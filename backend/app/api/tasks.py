
from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional, List
import jwt
from jwt import exceptions as jwt_exceptions
from datetime import datetime
from pydantic import BaseModel
from ..agents.task_agent import generate, generate_batch, generate_tasks_for_concepts
from ..agents.effort_time_agent import calculate_effort_time
from ..core.logger import get_logger
from ..core.security import SECRET_KEY
from ..database.session import SessionLocal
from ..models.task import Task, TaskStatus, TaskType
from ..models import ConceptProgress
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = get_logger(__name__)

router = APIRouter(
    prefix="/tasks",
    tags=["Task Management"],
    responses={404: {"description": "Not found"}}
)


def _calculate_average_complexity(concepts: list) -> str:
    """
    Calculate average complexity from concept list.
    
    Args:
        concepts: List of {name, complexity} dicts
    
    Returns:
        "LOW", "MEDIUM", or "HIGH"
    """
    if not concepts:
        return "MEDIUM"
    
    complexity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    complexities = [c.get("complexity", "MEDIUM").upper() for c in concepts]
    
    avg_value = sum(complexity_map.get(c, 2) for c in complexities) / len(complexities) if complexities else 2
    
    if avg_value < 1.5:
        return "LOW"
    elif avg_value < 2.5:
        return "MEDIUM"
    else:
        return "HIGH"


class TaskAssignRequest(BaseModel):
    """Request model for assigning tasks"""
    unit_topic_concept_id: int
    staff_id: int
    title: str
    description: Optional[str] = None
    task_type: str = "READING"
    status: str = "PENDING"
    content: Optional[dict] = None


class TaskFromConceptsRequest(BaseModel):
    """Request model for creating task from selected concepts"""
    syllabus_id: int
    unit_id: str
    unit_name: str
    topic_id: str
    topic_name: str
    concepts: List[dict]  # [{id, name, complexity}, ...]
    start_date: Optional[str] = None  # ISO format date
    description: Optional[str] = None


class TaskProgressRequest(BaseModel):
    """Request model for updating task progress"""
    status: Optional[str] = None  # PENDING, IN_PROGRESS, COMPLETED
    completion_percentage: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    covered_topics: Optional[List[str]] = None
    notes: Optional[str] = None
    learning_task_progress: Optional[List[dict]] = None  # [{task_title, completion_percentage, status, notes}, ...]


class LearningTaskProgressRequest(BaseModel):
    """Request model for updating individual learning task progress"""
    task_title: str  # Title of the learning task
    completion_percentage: int  # 0-100
    status: Optional[str] = None  # PENDING, IN_PROGRESS, COMPLETED
    notes: Optional[str] = None  # Notes on the specific learning task


def get_current_user_id(authorization: Optional[str]) -> int:
    """Extract and validate user ID from JWT token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return int(user_id)
    except jwt_exceptions.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.post(
    "/from-concepts",
    summary="Create Task from Selected Concepts",
    description="Create a new task from selected concepts with effort calculation",
    responses={
        200: {"description": "Task created successfully"},
        400: {"description": "Invalid input"}
    }
)
async def create_task_from_concepts(
    request: TaskFromConceptsRequest,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Create a task from selected concepts"""
    db = SessionLocal()
    try:
        # Verify user
        user_id = get_current_user_id(authorization)
        
        # Fetch syllabus to get department
        from app.models.syllabus import Syllabus
        syllabus = db.query(Syllabus).filter(
            Syllabus.id == request.syllabus_id,
            Syllabus.staff_id == user_id
        ).first()
        
        if not syllabus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Syllabus not found"
            )
        
        department = syllabus.department or "CSE"
        
        # Prepare concepts data
        concepts_data = [
            {
                "name": concept.get("name"),
                "complexity": concept.get("complexity", "MEDIUM")
            }
            for concept in request.concepts
        ]
        
        # Calculate average complexity from concepts
        average_complexity = _calculate_average_complexity(concepts_data)
        
        # Create task title
        task_title = f"{request.topic_name} - {', '.join([c.get('name', '') for c in request.concepts[:3]])}"
        if len(request.concepts) > 3:
            task_title += f" (+{len(request.concepts) - 3} more)"
        
        # Parse start date
        start_date = request.start_date or datetime.utcnow().isoformat()
        try:
            parsed_start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to parse start_date '{start_date}': {str(e)}")
            parsed_start_date = datetime.utcnow()
        
        # Generate learning tasks for all selected concepts (run in thread pool to avoid blocking)
        logger.info(f"Generating tasks for {len(request.concepts)} concepts using enhanced task agent")
        loop = asyncio.get_event_loop()
        generated_tasks = await loop.run_in_executor(
            None,
            generate_batch,
            request.concepts,
            request.topic_name,
            request.unit_name,
            average_complexity
        )
        
        # Extract task list (handling both dict and list returns)
        task_list = []
        if isinstance(generated_tasks, dict):
            task_list = generated_tasks.get("tasks", [])
            logger.info(f"Generated {len(task_list)} tasks from batch generator")
        elif isinstance(generated_tasks, list):
            task_list = generated_tasks
        
        # Initialize learning task progress for each generated task (without time allocation yet)
        learning_task_progress = []
        for generated_task in task_list:
            learning_task_progress.append({
                "task_title": generated_task.get("title", "Unknown Task"),
                "task_type": generated_task.get("type", "learning_activity"),
                "difficulty": generated_task.get("difficulty", "MEDIUM").upper(),
                "estimated_time_minutes": 0,  # Will be calculated by effort time agent
                "completion_percentage": 0,
                "status": "PENDING",
                "notes": ""
            })
        
        # Use langchain agent to intelligently allocate time based on complexity
        effort_result = calculate_effort_time(
            learning_tasks=learning_task_progress,
            overall_complexity=average_complexity,
            start_date=parsed_start_date
        )
        
        # Update learning task progress with allocated times and calculated end_date
        learning_task_progress = effort_result.get("updated_tasks", learning_task_progress)
        total_minutes = effort_result.get("total_minutes", 0)
        total_hours = round(total_minutes / 60, 2) if total_minutes else 0
        calculated_end_date = effort_result.get("end_date")
        
        if calculated_end_date:
            try:
                parsed_end_date = datetime.fromisoformat(calculated_end_date.replace('Z', '+00:00'))
            except:
                pass  # Keep original end_date if parsing fails
        
        logger.info(f"Allocated effort times: {total_minutes} total minutes ({total_hours} hours) across {len(learning_task_progress)} tasks")
        
        # Create task with department and generated subtasks
        # Prepare concept IDs as comma-separated string
        concept_ids_str = ",".join([str(c.get("id")) for c in request.concepts if c.get("id")])
        
        task = Task(
            staff_id=user_id,
            syllabus_id=request.syllabus_id,
            department=department,
            unit_id=int(request.unit_id) if request.unit_id else None,  # Store unit_id directly
            unit_name=request.unit_name,  # Store unit_name directly
            topic_id=int(request.topic_id) if request.topic_id else None,  # Store topic_id directly
            topic_name=request.topic_name,  # Store topic_name directly
            concept_ids=concept_ids_str,  # Store concept IDs as comma-separated string
            title=task_title,
            description=request.description or f"Learning task for {request.topic_name}",
            task_type=TaskType.LEARNING_ACTIVITY,
            status=TaskStatus.PENDING,
            concepts=concepts_data,
            effort_hours=total_hours,
            average_complexity=average_complexity,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            learning_task_progress=learning_task_progress,
            content={
                "syllabus_id": request.syllabus_id,
                "unit_id": request.unit_id,
                "unit_name": request.unit_name,
                "topic_id": request.topic_id,
                "topic_name": request.topic_name,
                "concepts_count": len(request.concepts),
                "department": department,
                "generated_tasks": task_list,  # Store all generated tasks for this concept combination
                "task_generation_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(f"Task created from concepts: {task.id}, effort: {total_hours}h, department: {department}")
        
        return {
            "success": True,
            "message": "Task created successfully",
            "data": task.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating task from concepts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )
    finally:
        db.close()


@router.put(
    "/{task_id}/progress",
    summary="Update Task Progress",
    description="Update task progress with dates, status, and covered topics. Can update individual learning task progress.",
    responses={
        200: {"description": "Progress updated successfully"},
        404: {"description": "Task not found"}
    }
)
def update_task_progress(
    task_id: int,
    request: TaskProgressRequest,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Update task progress including individual learning task progress"""
    db = SessionLocal()
    try:
        # Verify user
        user_id = get_current_user_id(authorization)
        
        # Get task
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Verify ownership
        if task.staff_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update other users' tasks"
            )
        
        # Update individual learning task progress if provided
        if request.learning_task_progress:
            task.learning_task_progress = request.learning_task_progress
            logger.info(f"Updated {len(request.learning_task_progress)} learning task progress entries for task {task_id}")
            
            # Calculate overall progress using progress agent
            from app.agents.progress_agent import evaluate_task_progress, calculate_aggregate_progress
            
            # Get evaluation from progress agent
            evaluation = evaluate_task_progress(
                task_title=task.title,
                learning_tasks_progress=request.learning_task_progress,
                complexity_level=task.average_complexity or "MEDIUM",
                end_date=task.end_date.isoformat() if task.end_date else None
            )
            
            # Update task with evaluated progress
            task.completion_percentage = evaluation.get("overall_completion_percentage", 0)
            task.status = TaskStatus[evaluation.get("status", "PENDING").upper()]
            
            # Add evaluation notes to task notes
            if evaluation.get("evaluation_notes"):
                existing_notes = task.notes or ""
                task.notes = f"{existing_notes}\n\n[Progress Evaluation] {evaluation['evaluation_notes']}" if existing_notes else f"[Progress Evaluation] {evaluation['evaluation_notes']}"
        
        # Update other fields
        if request.status and not request.learning_task_progress:  # Only update if not using learning task progress
            task.status = TaskStatus[request.status.upper()]
        
        if request.completion_percentage is not None and not request.learning_task_progress:
            task.completion_percentage = request.completion_percentage
            if request.completion_percentage == 100:
                task.completed_at = datetime.utcnow()
        
        if request.start_date:
            task.start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        
        if request.end_date:
            task.end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
        
        if request.covered_topics:
            task.covered_topics = request.covered_topics
        
        if request.notes and not request.learning_task_progress:
            task.notes = request.notes
        
        task.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(task)
        
        logger.info(f"Task progress updated: {task.id}")
        
        return {
            "success": True,
            "message": "Task progress updated successfully",
            "data": task.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating task progress: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task progress: {str(e)}"
        )
    finally:
        db.close()


@router.post(
    "/generate",
    summary="Generate Learning Tasks",
    description="Generate AI-powered learning tasks for a specific concept with configurable difficulty level",
    responses={
        200: {"description": "Tasks generated successfully"},
        400: {"description": "Invalid concept or complexity level"}
    }
)
def generate_tasks(data: dict):
    return generate(data["concept"], data.get("complexity","MEDIUM"))


@router.post(
    "/assign",
    summary="Assign Task to Staff",
    description="Assign a learning task to staff for tracking concept progress"
)
def assign_task(request: TaskAssignRequest, authorization: Optional[str] = Header(None, alias="Authorization")):
    """Assign a task for concept progress tracking"""
    db = SessionLocal()
    try:
        # Verify user
        user_id = get_current_user_id(authorization)
        
        if request.staff_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign tasks to other users"
            )
        
        # Check if concept progress exists
        concept_progress = db.query(ConceptProgress).filter(
            ConceptProgress.unit_topic_concept_id == request.unit_topic_concept_id,
            ConceptProgress.staff_id == request.staff_id
        ).first()
        
        # If not, create it
        if not concept_progress:
            concept_progress = ConceptProgress(
                unit_topic_concept_id=request.unit_topic_concept_id,
                staff_id=request.staff_id,
                status='Pending',
                completion_percentage=0,
                created_at=datetime.utcnow(),
                start_date=datetime.utcnow()
            )
            db.add(concept_progress)
            db.commit()
            db.refresh(concept_progress)
            logger.info(f"Created new concept progress: {concept_progress.id}")
        
        # Create task
        task = Task(
            concept_progress_id=concept_progress.id,
            staff_id=request.staff_id,
            title=request.title,
            description=request.description,
            task_type=request.task_type,
            status=request.status or 'PENDING',
            content=request.content,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(f"Task assigned successfully: {task.id}")
        
        return {
            "success": True,
            "message": "Task assigned successfully",
            "data": task.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign task"
        )
    finally:
        db.close()


@router.get(
    "",
    summary="Get All Tasks",
    description="Get all tasks for a specific staff member, optionally filtered by department and/or syllabus"
)
def get_tasks(
    staff_id: int, 
    department: Optional[str] = None,
    syllabus_id: Optional[int] = None,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Get all tasks for a staff member, optionally filtered by department and/or syllabus"""
    db = SessionLocal()
    try:
        # Verify user
        user_id = get_current_user_id(authorization)
        
        if staff_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view other users' tasks"
            )
        
        # Get tasks, optionally filtered by department and/or syllabus
        query = db.query(Task).filter(Task.staff_id == staff_id)
        
        if department:
            query = query.filter(Task.department == department)
            logger.info(f"Filtering tasks for department: {department}")
        
        if syllabus_id:
            query = query.filter(Task.syllabus_id == syllabus_id)
            logger.info(f"Filtering tasks for syllabus: {syllabus_id}")
        
        tasks = query.order_by(Task.created_at.desc()).all()
        
        return {
            "success": True,
            "message": "Tasks retrieved successfully",
            "data": [task.to_dict() for task in tasks],
            "total": len(tasks),
            "department_filter": department or "All",
            "syllabus_filter": syllabus_id or "All"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error retrieving tasks for staff_id={staff_id}, department={department}, syllabus_id={syllabus_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tasks: {str(e)}"
        )
    finally:
        db.close()


@router.get(
    "/check-existing",
    summary="Check if tasks exist for unit-topic-concepts",
    description="Check if tasks already exist for a given unit, topic, and concepts combination"
)
def check_existing_tasks(
    unit_id: int,
    topic_id: int,
    concept_ids: str,  # Comma-separated list of concept IDs
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Check if tasks already exist for a specific unit, topic, and concepts combination.
    
    Args:
        unit_id: The unit ID
        topic_id: The topic ID
        concept_ids: Comma-separated concept IDs (e.g., "1,2,3")
        
    Returns:
        Dict with exists flag
    """
    db = SessionLocal()
    try:
        # Verify user
        user_id = get_current_user_id(authorization)
        
        # Parse concept IDs
        try:
            concept_id_list = [int(cid.strip()) for cid in concept_ids.split(',')]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid concept_ids format"
            )
        
        # Query tasks by unit_id and topic_id directly from DB columns
        existing_tasks = db.query(Task).filter(
            Task.staff_id == user_id,
            Task.unit_id == unit_id,
            Task.topic_id == topic_id
        ).all()
        
        # Check if any existing task has overlapping concepts
        tasks_exist = False
        for task in existing_tasks:
            if task.concept_ids:  # If concept_ids is set
                try:
                    task_concept_ids = [int(cid.strip()) for cid in task.concept_ids.split(',')]
                    # Check if there's any overlap
                    if any(cid in task_concept_ids for cid in concept_id_list):
                        tasks_exist = True
                        logger.info(
                            f"Found existing task {task.id} for unit_id={unit_id}, "
                            f"topic_id={topic_id} with overlapping concepts"
                        )
                        break
                except (ValueError, AttributeError):
                    continue
        
        logger.info(
            f"Checked existing tasks for staff_id={user_id}, unit_id={unit_id}, "
            f"topic_id={topic_id}: exists={tasks_exist}"
        )
        
        return {
            "success": True,
            "data": {
                "exists": tasks_exist,
                "unit_id": unit_id,
                "topic_id": topic_id,
                "concept_ids": concept_id_list
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error checking existing tasks: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check existing tasks"
        )
    finally:
        db.close()


@router.delete(
    "/{task_id}",
    summary="Delete Task",
    description="Delete a specific task by ID. Only the task owner can delete it."
)
def delete_task(
    task_id: int,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Delete a task by ID. Only the task owner can delete it."""
    db = SessionLocal()
    try:
        # Verify user
        user_id = get_current_user_id(authorization)
        
        # Get the task
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Verify ownership
        if task.staff_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete other users' tasks"
            )
        
        # Delete the task
        db.delete(task)
        db.commit()
        
        logger.info(f"Task {task_id} deleted by user {user_id}")
        
        return {
            "success": True,
            "message": "Task deleted successfully",
            "data": {"task_id": task_id}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_msg = f"Error deleting task {task_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )
    finally:
        db.close()
