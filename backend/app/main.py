
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, syllabus, progress, tasks

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(syllabus.router)
app.include_router(progress.router)
app.include_router(tasks.router)
