
from fastapi import APIRouter, UploadFile
from app.agents.syllabus_agent import analyze
from app.vectorstore.store import add

router = APIRouter(prefix="/syllabus")

@router.post("/upload")
async def upload(file: UploadFile):
    text = (await file.read()).decode()
    add(text)
    return analyze(text)
