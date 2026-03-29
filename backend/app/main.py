from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from .api import auth, syllabus, progress, tasks
from .database import init_db
from .core.logger import get_logger
import asyncio
import time
import json

import os
from dotenv import load_dotenv
load_dotenv()
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

# Add CORS middleware FIRST before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Catch-all middleware for CORS headers on all responses
@app.middleware("http")
async def cors_headers_middleware(request: Request, call_next):
    """Add CORS headers to all responses"""
    try:
        # Handle OPTIONS requests
        if request.method == "OPTIONS":
            origin = request.headers.get("origin", "*")
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": request.headers.get("access-control-request-headers", "Content-Type, Authorization"),
                    "Access-Control-Max-Age": "86400",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Get the response from the next middleware/handler
        response = await call_next(request)
        
        # Add CORS headers to all responses
        origin = request.headers.get("origin", "*")
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    except Exception as e:
        logger.error(f"CORS middleware error: {str(e)}", exc_info=True)
        # Even on error, return 200 for OPTIONS with CORS headers
        if request.method == "OPTIONS":
            origin = request.headers.get("origin", "*")
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        raise

# Timeout middleware for long-running requests
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Add timeout to all requests"""
    # Skip timeout for OPTIONS requests
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # Determine timeout based on endpoint
    if request.url.path.endswith("/upload"):
        timeout_seconds = 300  # Syllabus upload: 5 minutes
    elif "/tasks" in request.url.path and request.method == "POST":
        timeout_seconds = 120  # Task generation: 2 minutes (LLM calls can be slow)
    else:
        timeout_seconds = 30  # Default: 30 seconds
    
    try:
        start = time.time()
        response = await asyncio.wait_for(call_next(request), timeout=timeout_seconds)
        elapsed = time.time() - start
        if elapsed > timeout_seconds * 0.8:  # Log if close to timeout
            logger.warning(f"{request.method} {request.url.path} took {elapsed:.1f}s (timeout: {timeout_seconds}s)")
        return response
    except asyncio.TimeoutError:
        logger.error(f"Request timeout for {request.method} {request.url.path} after {timeout_seconds}s")
        return JSONResponse(
            status_code=504,
            content={"detail": f"Request timeout after {timeout_seconds} seconds"}
        )

# Exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
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


from .api.analyze import router as analyze_router
app.include_router(auth.router)
app.include_router(syllabus.router)
app.include_router(progress.router)
app.include_router(tasks.router)
app.include_router(analyze_router)

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "AI Academic Performance Analyzer API"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        from .database.session import engine
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
