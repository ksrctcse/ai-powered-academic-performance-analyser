
from fastapi import APIRouter
from app.agents.unit_progress_agent import calculate

router = APIRouter(prefix="/progress")

@router.post("/concept")
def update(data: dict):
    return {"unit_progress": calculate(data)}
