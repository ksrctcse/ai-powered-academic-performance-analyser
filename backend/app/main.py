from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import auth, syllabus, progress, tasks
from app.database import init_db
from app.core.logger import get_logger
import traceback

logger = get_logger(__name__)

app = FastAPI(
    title="AI Academic Performance Analyzer API",
    description="A comprehensive API for analyzing academic performance using AI-powered insights",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

# Initialize database tables on startup
@app.on_event("startup")
def startup_event():
    logger.info("Starting up application...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down application...")

app.include_router(auth.router)
app.include_router(syllabus.router)
app.include_router(progress.router)
app.include_router(tasks.router)

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "AI Academic Performance Analyzer API"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        from app.database.session import engine
        with engine.connect() as conn:
            logger.info("Health check: Database connection OK")
            return {
                "status": "healthy",
                "message": "API is running and database is connected"
            }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
