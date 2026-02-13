
import json
from fastapi import APIRouter, UploadFile, Depends, HTTPException, status, Header
from typing import Optional
from app.agents.syllabus_agent import analyze
from app.vectorstore.store import add
from app.database.session import SessionLocal
from app.models.syllabus import Syllabus
from app.models.staff import Staff
from app.utils.file_processor import process_file, extract_course_name_from_text, FileProcessingError
from app.core.logger import get_logger
from app.core.security import SECRET_KEY
from jose import jwt, JWTError
import traceback

logger = get_logger(__name__)

router = APIRouter(
    prefix="/syllabus",
    tags=["Syllabus Management"],
    responses={404: {"description": "Not found"}}
)


def get_current_user_id(authorization: Optional[str] = Header(None)):
    """
    Extract and validate user ID from JWT token in Authorization header.
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        User ID from the token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme"
            )
        
        # Decode JWT token
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
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed"
        )


@router.post(
    "/upload",
    summary="Upload and Analyze Syllabus",
    description="Upload a syllabus document (PDF, DOCX, or CSV) for AI-powered analysis and concept extraction",
    responses={
        200: {"description": "Syllabus processed and analyzed successfully"},
        400: {"description": "Invalid file format or file processing error"},
        401: {"description": "Unauthorized - missing or invalid token"},
        500: {"description": "Processing error"}
    }
)
async def upload_syllabus(
    file: UploadFile,
    authorization: Optional[str] = Header(None)
):
    """
    Upload and analyze a syllabus document.
    
    The endpoint:
    1. Validates the JWT token to identify the staff member
    2. Processes the uploaded file (PDF, DOCX, or CSV)
    3. Extracts text from the file
    4. Analyzes content using syllabus_agent to extract units and concepts
    5. Stores metadata in the Syllabus database model
    6. Adds analyzed text to FAISS vector store
    7. Returns analysis results
    """
    db = SessionLocal()
    
    try:
        # Get user ID from token
        staff_id = get_current_user_id(authorization)
        
        # Verify staff exists
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        if not staff:
            logger.warning(f"Staff member not found for ID: {staff_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Staff member not found"
            )
        
        logger.info(f"Syllabus upload initiated by staff: {staff.email} (ID: {staff_id})")
        
        # Validate file was provided
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Read file content
        file_content = await file.read()
        
        try:
            # Process file and extract text
            extracted_text, file_type = process_file(file.filename, file_content)
            
            logger.info(f"File processed successfully: {file.filename} (type: {file_type})")
            
        except FileProcessingError as e:
            logger.warning(f"File processing error for {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File processing failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error processing file {file.filename}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process file"
            )
        
        # Analyze using syllabus_agent to extract hierarchical structure
        try:
            analysis_result = analyze(extracted_text)
            
            # Ensure we have a dict
            if isinstance(analysis_result, str):
                try:
                    analysis_json = json.loads(analysis_result)
                except json.JSONDecodeError:
                    analysis_json = {"raw_analysis": analysis_result}
            else:
                analysis_json = analysis_result if analysis_result else {}
            
            logger.info(f"Syllabus analysis completed for file: {file.filename}")
            
        except Exception as e:
            logger.error(f"Error analyzing syllabus: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze syllabus: {str(e)}"
            )
        
        # Extract course name from analysis or file
        course_name = analysis_json.get("course_title") or extract_course_name_from_text(extracted_text, file.filename)
        
        # Extract hierarchical structure: units -> topics -> concepts
        hierarchy = analysis_json if "units" in analysis_json else None
        
        # For backward compatibility, extract flat lists
        units = analysis_json.get("units", None)
        concepts = analysis_json.get("concepts", None)
        
        # Add analyzed content to vector store
        try:
            # Store course title + content for better semantic search
            vector_text = f"Course: {course_name}\n\n{extracted_text}"
            vector_store_result = add(vector_text)
            vector_store_id = str(vector_store_result) if vector_store_result else None
            logger.info(f"Added to vector store: {file.filename}")
            
        except Exception as e:
            logger.error(f"Error adding to vector store: {str(e)}", exc_info=True)
            vector_store_id = None
            # Don't fail the upload if vector store fails, but log it
        
        # Create syllabus record in database
        try:
            syllabus = Syllabus(
                staff_id=staff_id,
                filename=file.filename,
                file_type=file_type,
                course_name=course_name,
                department=staff.department,
                raw_text=extracted_text[:10000],  # Store first 10000 chars for preview
                hierarchy=hierarchy,  # Store complete hierarchical structure
                units=units,
                concepts=concepts,
                analysis_result=analysis_json,
                vector_store_id=vector_store_id,
                file_size_bytes=len(file_content)
            )
            
            db.add(syllabus)
            db.commit()
            db.refresh(syllabus)
            
            logger.info(f"Syllabus record created: ID {syllabus.id} with hierarchical structure for staff {staff_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving syllabus to database: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save syllabus metadata: {str(e)}"
            )
        
        # Calculate summary from hierarchy
        total_units = 0
        total_topics = 0
        total_concepts = 0
        
        if hierarchy and "units" in hierarchy:
            units_list = hierarchy["units"]
            total_units = len(units_list) if isinstance(units_list, list) else 0
            
            for unit in units_list if isinstance(units_list, list) else []:
                if isinstance(unit, dict) and "topics" in unit:
                    topics_list = unit["topics"]
                    total_topics += len(topics_list) if isinstance(topics_list, list) else 0
                    
                    for topic in topics_list if isinstance(topics_list, list) else []:
                        if isinstance(topic, dict) and "concepts" in topic:
                            concepts_list = topic["concepts"]
                            total_concepts += len(concepts_list) if isinstance(concepts_list, list) else 0
        
        # Return success response
        response = {
            "success": True,
            "message": "Syllabus uploaded and analyzed successfully",
            "data": {
                "syllabus_id": syllabus.id,
                "filename": syllabus.filename,
                "file_type": syllabus.file_type,
                "course_name": syllabus.course_name,
                "department": syllabus.department,
                "file_size_bytes": syllabus.file_size_bytes,
                "uploaded_at": syllabus.uploaded_at.isoformat() if syllabus.uploaded_at else None,
                "hierarchy": hierarchy,
                "analysis_summary": {
                    "total_units": total_units,
                    "total_topics": total_topics,
                    "total_concepts": total_concepts,
                }
            }
        }
        
        logger.info(f"Syllabus upload completed: {file.filename} (ID: {syllabus.id}, Units: {total_units}, Topics: {total_topics}, Concepts: {total_concepts})")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during upload"
        )
    finally:
        db.close()


@router.get(
    "/list",
    summary="List User's Syllabuses",
    description="Get all syllabuses uploaded by the current user",
    responses={
        200: {"description": "List of syllabuses retrieved successfully"},
        401: {"description": "Unauthorized - missing or invalid token"}
    }
)
async def list_syllabuses(authorization: Optional[str] = Header(None)):
    """
    Get all syllabuses uploaded by the current staff member.
    """
    db = SessionLocal()
    
    try:
        staff_id = get_current_user_id(authorization)
        
        syllabuses = db.query(Syllabus).filter(
            Syllabus.staff_id == staff_id
        ).order_by(Syllabus.uploaded_at.desc()).all()
        
        return {
            "success": True,
            "data": [syllabus.to_dict() for syllabus in syllabuses],
            "count": len(syllabuses)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing syllabuses: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve syllabuses"
        )
    finally:
        db.close()


@router.get(
    "/{syllabus_id}",
    summary="Get Syllabus Details",
    description="Get detailed information about a specific syllabus",
    responses={
        200: {"description": "Syllabus details retrieved successfully"},
        401: {"description": "Unauthorized - missing or invalid token"},
        404: {"description": "Syllabus not found"}
    }
)
async def get_syllabus(
    syllabus_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Get detailed information about a specific syllabus.
    """
    db = SessionLocal()
    
    try:
        staff_id = get_current_user_id(authorization)
        
        syllabus = db.query(Syllabus).filter(
            Syllabus.id == syllabus_id,
            Syllabus.staff_id == staff_id
        ).first()
        
        if not syllabus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Syllabus not found"
            )
        
        return {
            "success": True,
            "data": syllabus.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving syllabus: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve syllabus"
        )
    finally:
        db.close()


@router.delete(
    "/{syllabus_id}",
    summary="Delete Syllabus",
    description="Delete a syllabus and its vector store references",
    responses={
        200: {"description": "Syllabus deleted successfully"},
        401: {"description": "Unauthorized - missing or invalid token"},
        404: {"description": "Syllabus not found"}
    }
)
async def delete_syllabus(
    syllabus_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Delete a syllabus record and its vector store references.
    """
    db = SessionLocal()
    
    try:
        staff_id = get_current_user_id(authorization)
        
        syllabus = db.query(Syllabus).filter(
            Syllabus.id == syllabus_id,
            Syllabus.staff_id == staff_id
        ).first()
        
        if not syllabus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Syllabus not found"
            )
        
        filename = syllabus.filename
        db.delete(syllabus)
        db.commit()
        
        logger.info(f"Syllabus deleted: ID {syllabus_id} ({filename})")
        
        return {
            "success": True,
            "message": f"Syllabus '{filename}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting syllabus: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete syllabus"
        )
    finally:
        db.close()
