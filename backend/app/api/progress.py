from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional
import jwt
from jwt import exceptions as jwt_exceptions
from datetime import datetime
from pydantic import BaseModel
from app.core.logger import get_logger
from app.core.security import SECRET_KEY
from app.database.session import SessionLocal
from app.models.staff import Staff
from app.models.unit_topic_concept import UnitTopicConcept
from app.models import ConceptProgress
from app.models.task import Task, TaskStatus, TaskType
from app.agents.unit_progress_agent import calculate
from app.agents.task_agent import generate_tasks

logger = get_logger(__name__)

router = APIRouter(
    prefix="/progress",
    tags=["Progress Tracking"],
    responses={404: {"description": "Not found"}}
)


class ConceptProgressRequest(BaseModel):
    """Request model for concept progress"""
    unit_topic_concept_id: int
    staff_id: int
    start_date: Optional[str] = None  # ISO format date
    completion_percentage: int = 0
    status: str = "In Progress"
    

class ConceptProgressCompleteRequest(BaseModel):
    """Request model for completing concept progress"""
    unit_topic_concept_id: int
    staff_id: int
    end_date: Optional[str] = None  # ISO format date
    completion_percentage: int = 100
    generate_tasks: bool = True


def get_current_user_id(authorization: Optional[str]) -> int:
    """Extract and validate user ID from JWT token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme"
            )
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return user_id
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    except jwt_exceptions.PyJWTError:
        logger.warning("JWT validation failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


@router.post(
    "/concept",
    summary="Update Concept Progress",
    description="Update student progress on a specific concept and calculate overall unit progress",
    responses={
        200: {"description": "Progress updated successfully"},
        400: {"description": "Invalid input data"}
    }
)
def update(data: dict):
    return {"unit_progress": calculate(data)}


@router.post(
    "/concept/start",
    summary="Start Concept Progress",
    description="Mark the start of learning a specific concept with start date",
    responses={
        200: {"description": "Concept progress started"},
        400: {"description": "Invalid input"},
        401: {"description": "Unauthorized"},
        404: {"description": "Concept not found"}
    }
)
async def start_concept_progress(
    request: ConceptProgressRequest,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Start tracking progress on a concept with a start date.
    Creates or updates ConceptProgress record.
    """
    db = SessionLocal()
    
    try:
        staff_id = get_current_user_id(authorization)
        
        # Verify staff exists
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff not found"
            )
        
        # Verify concept exists
        utc = db.query(UnitTopicConcept).filter(
            UnitTopicConcept.id == request.unit_topic_concept_id
        ).first()
        
        if not utc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Concept not found"
            )
        
        # Check if progress already exists for this concept
        concept_progress = db.query(ConceptProgress).filter(
            ConceptProgress.staff_id == staff_id,
            ConceptProgress.unit_topic_concept_id == request.unit_topic_concept_id
        ).first()
        
        start_date = datetime.fromisoformat(request.start_date) if request.start_date else datetime.utcnow()
        
        if concept_progress:
            # Update existing progress
            concept_progress.start_date = start_date
            concept_progress.status = request.status
            concept_progress.completion_percentage = request.completion_percentage
            concept_progress.updated_at = datetime.utcnow()
            logger.info(f"Updated progress for staff {staff_id} on concept {request.unit_topic_concept_id}")
        else:
            # Create new progress
            concept_progress = ConceptProgress(
                staff_id=staff_id,
                concept_id=utc.id if hasattr(utc, 'id') else None,
                unit_topic_concept_id=request.unit_topic_concept_id,
                start_date=start_date,
                status=request.status,
                completion_percentage=request.completion_percentage,
                created_at=datetime.utcnow()
            )
            db.add(concept_progress)
            logger.info(f"Created progress for staff {staff_id} on concept {request.unit_topic_concept_id}")
        
        db.commit()
        db.refresh(concept_progress)
        
        return {
            "success": True,
            "message": "Concept progress started successfully",
            "data": {
                "id": concept_progress.id,
                "unit_topic_concept_id": concept_progress.unit_topic_concept_id,
                "staff_id": concept_progress.staff_id,
                "status": concept_progress.status,
                "start_date": concept_progress.start_date.isoformat() if concept_progress.start_date else None,
                "completion_percentage": concept_progress.completion_percentage
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting concept progress: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start concept progress"
        )
    finally:
        db.close()


@router.post(
    "/concept/complete",
    summary="Complete Concept Progress",
    description="Mark concept as completed with end date and optionally generate tasks",
    responses={
        200: {"description": "Concept progress completed"},
        400: {"description": "Invalid input"},
        401: {"description": "Unauthorized"},
        404: {"description": "Concept not found"}
    }
)
async def complete_concept_progress(
    request: ConceptProgressCompleteRequest,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Mark a concept as completed with an end date.
    Optionally generates tasks for reinforcement.
    """
    db = SessionLocal()
    
    try:
        staff_id = get_current_user_id(authorization)
        
        # Verify staff exists
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff not found"
            )
        
        # Get concept progress
        concept_progress = db.query(ConceptProgress).filter(
            ConceptProgress.staff_id == staff_id,
            ConceptProgress.unit_topic_concept_id == request.unit_topic_concept_id
        ).first()
        
        if not concept_progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Concept progress not found"
            )
        
        # Update progress
        end_date = datetime.fromisoformat(request.end_date) if request.end_date else datetime.utcnow()
        concept_progress.end_date = end_date
        concept_progress.status = "Completed"
        concept_progress.completion_percentage = 100
        concept_progress.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(concept_progress)
        
        logger.info(f"Completed progress for staff {staff_id} on concept {request.unit_topic_concept_id}")
        
        response_data = {
            "id": concept_progress.id,
            "unit_topic_concept_id": concept_progress.unit_topic_concept_id,
            "staff_id": concept_progress.staff_id,
            "status": concept_progress.status,
            "start_date": concept_progress.start_date.isoformat() if concept_progress.start_date else None,
            "end_date": concept_progress.end_date.isoformat() if concept_progress.end_date else None,
            "completion_percentage": concept_progress.completion_percentage
        }
        
        # Generate tasks if requested
        tasks_generated = []
        if request.generate_tasks:
            try:
                # Get concept details for task generation
                utc = db.query(UnitTopicConcept).filter(
                    UnitTopicConcept.id == request.unit_topic_concept_id
                ).first()
                
                if utc:
                    # Generate tasks using task agent
                    task_descriptions = generate_tasks(
                        concept_name=utc.concept_name,
                        topic_name=utc.topic_name,
                        unit_name=utc.unit_name
                    )
                    
                    # Store tasks in database
                    for task_desc in task_descriptions:
                        task = Task(
                            staff_id=staff_id,
                            concept_progress_id=concept_progress.id,
                            title=task_desc.get("title", f"Task for {utc.concept_name}"),
                            description=task_desc.get("description", ""),
                            task_type=TaskType.LEARNING_ACTIVITY,
                            content=task_desc,
                            status=TaskStatus.PENDING,
                            created_at=datetime.utcnow()
                        )
                        db.add(task)
                        tasks_generated.append(task_desc)
                    
                    db.commit()
                    logger.info(f"Generated {len(tasks_generated)} tasks for concept progress {concept_progress.id}")
                    
            except Exception as e:
                logger.error(f"Error generating tasks: {str(e)}", exc_info=True)
                # Don't fail the whole request if task generation fails
        
        response_data["tasks_generated"] = len(tasks_generated)
        
        return {
            "success": True,
            "message": "Concept progress completed successfully",
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing concept progress: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete concept progress"
        )
    finally:
        db.close()


@router.get(
    "/concept/{concept_progress_id}/tasks",
    summary="Get Tasks for Concept Progress",
    description="Get all tasks associated with a concept progress record",
    responses={
        200: {"description": "Tasks retrieved"},
        401: {"description": "Unauthorized"},
        404: {"description": "Concept progress not found"}
    }
)
async def get_concept_tasks(
    concept_progress_id: int,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Get all tasks for a concept progress."""
    db = SessionLocal()
    
    try:
        staff_id = get_current_user_id(authorization)
        
        # Get concept progress and verify ownership
        concept_progress = db.query(ConceptProgress).filter(
            ConceptProgress.id == concept_progress_id,
            ConceptProgress.staff_id == staff_id
        ).first()
        
        if not concept_progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Concept progress not found"
            )
        
        # Get tasks
        tasks = db.query(Task).filter(
            Task.concept_progress_id == concept_progress_id
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
