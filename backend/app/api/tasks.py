
from fastapi import APIRouter
from app.agents.task_agent import generate

router = APIRouter(prefix="/tasks")

@router.post("/generate")
def generate_tasks(data: dict):
    return generate(data["concept"], data.get("complexity","MEDIUM"))
