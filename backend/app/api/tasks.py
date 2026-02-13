
from fastapi import APIRouter
from app.agents.task_agent import generate

router = APIRouter(
    prefix="/tasks",
    tags=["Task Generation"],
    responses={404: {"description": "Not found"}}
)

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
