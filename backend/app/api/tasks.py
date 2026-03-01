
from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional, List
import jwt
from jwt import exceptions as jwt_exceptions
from datetime import datetime
from pydantic import BaseModel
from app.agents.task_agent import generate
from app.agents.effort_agent import calculate_effort, calculate_end_date
from app.core.logger import get_logger
from app.core.security import SECRET_KEY
from app.database.session import SessionLocal
from app.models.task import Task, TaskStatus, TaskType
from app.models import ConceptProgress

logger = get_logger(__name__)

router = APIRouter(
    prefix="/tasks",
    tags=["Task Management"],
    responses={404: {"description": "Not found"}}
)


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
        user_id = payload.get("sub")
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
def create_task_from_concepts(
    request: TaskFromConceptsRequest,
    authorization: Optional[str] = Header(None)
):
    """Create a task from selected concepts"""
    db = SessionLocal()
    try:
        # Verify user
        user_id = get_current_user_id(authorization)
        
        # Calculate effort using effort agent
        concepts_data = [
            {
                "name": concept.get("name"),
                "complexity": concept.get("complexity", "MEDIUM")
            }
            for concept in request.concepts
        ]
        
        effort_result = calculate_effort(concepts_data)
        
        if "error" in effort_result and effort_result["error"]:
            logger.warning(f"Effort calculation had error: {effort_result.get('error')}")
        
        total_hours = effort_result.get("total_hours", 0)
        average_complexity = effort_result.get("average_complexity", "MEDIUM")
        
        # Calculate end date (4 hours per day)
        start_date = request.start_date or datetime.utcnow().isoformat()
        end_date = calculate_end_date(start_date, total_hours)
        
        # Create task title
        task_title = f"{request.topic_name} - {', '.join([c.get('name', '') for c in request.concepts[:3]])}"
        if len(request.concepts) > 3:
            task_title += f" (+{len(request.concepts) - 3} more)"
        
        # Create task
        task = Task(
            staff_id=user_id,
            title=task_title,
            description=request.description or f"Learning task for {request.topic_name}",
            task_type=TaskType.ASSIGNMENT,
            status=TaskStatus.PENDING,
            concepts=concepts_data,
            effort_hours=total_hours,
            average_complexity=average_complexity,
            start_date=datetime.fromisoformat(start_date.replace('Z', '+00:00')),
            end_date=datetime.fromisoformat(end_date.replace('Z', '+00:00')),
            content={
                "syllabus_id": request.syllabus_id,
                "unit_id": request.unit_id,
                "unit_name": request.unit_name,
                "topic_id": request.topic_id,
                "topic_name": request.topic_name,
                "concepts_count": len(request.concepts)
            }
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(f"Task created from concepts: {task.id}, effort: {total_hours}h")
        
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
            detail="Failed to create task"
        )
    finally:
        db.close()


@router.put(
    "/{task_id}/progress",
    summary="Update Task Progress",
    description="Update task progress with dates, status, and covered topics",
    responses={
        200: {"description": "Progress updated successfully"},
        404: {"description": "Task not found"}
    }
)
def update_task_progress(
    task_id: int,
    request: TaskProgressRequest,
    authorization: Optional[str] = Header(None)
):
    """Update task progress"""
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
        
        # Update fields
        if request.status:
            task.status = TaskStatus[request.status.upper()]
        
        if request.completion_percentage is not None:
            task.completion_percentage = request.completion_percentage
            if request.completion_percentage == 100:
                task.completed_at = datetime.utcnow()
        
        if request.start_date:
            task.start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        
        if request.end_date:
            task.end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
        
        if request.covered_topics:
            task.covered_topics = request.covered_topics
        
        if request.notes:
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
            detail="Failed to update task progress"
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
def assign_task(request: TaskAssignRequest, authorization: Optional[str] = Header(None)):
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
    description="Get all tasks for a specific staff member"
)
def get_tasks(staff_id: int, authorization: Optional[str] = Header(None)):
    """Get all tasks for a staff member"""
    db = SessionLocal()
    try:
        # Verify user
        user_id = get_current_user_id(authorization)
        
        if staff_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view other users' tasks"
            )
        
        # Get all tasks
        tasks = db.query(Task).filter(
            Task.staff_id == staff_id
        ).order_by(Task.created_at.desc()).all()
        
        return {
            "success": True,
            "message": "Tasks retrieved successfully",
            "data": [task.to_dict() for task in tasks]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tasks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks"
        )
    finally:
        db.close()
