
from fastapi import APIRouter
from app.agents.unit_progress_agent import calculate

router = APIRouter(
    prefix="/progress",
    tags=["Progress Tracking"],
    responses={404: {"description": "Not found"}}
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
