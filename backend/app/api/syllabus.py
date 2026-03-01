from fastapi import APIRouter, Header, HTTPException, status, UploadFile, File
from typing import Optional
import json
import hashlib
import jwt
from jwt import exceptions as jwt_exceptions
from app.core.logger import get_logger
from app.core.security import SECRET_KEY
from app.database.session import SessionLocal
from app.models.syllabus import Syllabus
from app.models.staff import Staff
from app.models.unit_topic_concept import UnitTopicConcept, ComplexityLevel
from app.agents.syllabus_agent import analyze
from app.agents.complexity_agent import analyze_hierarchy_complexity
from app.utils.file_processor import process_file
from app.vectorstore.store import add

logger = get_logger(__name__)

router = APIRouter(
    prefix="/syllabus",
    tags=["Syllabus Management"],
    responses={404: {"description": "Not found"}}
)


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
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed"
        )


def extract_course_name_from_text(text: str, filename: str) -> str:
    """Extract course name from text or filename."""
    if not text or len(text) < 10:
        return filename.replace(".pdf", "").replace(".docx", "").replace(".csv", "").replace(".txt", "")
    
    # Try to find a course title in first few lines
    lines = text.split('\n')[:10]
    for line in lines:
        if line.strip() and len(line.strip()) > 3 and len(line.strip()) < 100:
            return line.strip()
    
    return filename.replace(".pdf", "").replace(".docx", "").replace(".csv", "").replace(".txt", "")


def calculate_analysis_summary(analysis_json: dict) -> dict:
    """Calculate total units, topics, and concepts from hierarchy."""
    summary = {
        "total_units": 0,
        "total_topics": 0,
        "total_concepts": 0
    }
    
    if not analysis_json or "units" not in analysis_json:
        return summary
    
    units_list = analysis_json.get("units", [])
    if not isinstance(units_list, list):
        return summary
    
    summary["total_units"] = len(units_list)
    
    for unit in units_list:
        if isinstance(unit, dict) and "topics" in unit:
            topics_list = unit["topics"]
            if isinstance(topics_list, list):
                summary["total_topics"] += len(topics_list)
                
                for topic in topics_list:
                    if isinstance(topic, dict) and "concepts" in topic:
                        concepts_list = topic["concepts"]
                        if isinstance(concepts_list, list):
                            summary["total_concepts"] += len(concepts_list)
    
    return summary


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
    file: UploadFile = File(...),
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
        
        # Get staff information
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff not found"
            )

        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        file_hash = hashlib.sha256(file_content).hexdigest()
        logger.info(f"File hash calculated: {file_hash} for file: {file.filename}")

        # Check for duplicate file content for this staff (same content, different or same name)
        existing_syllabus = db.query(Syllabus).filter(
            Syllabus.staff_id == staff_id,
            Syllabus.file_hash == file_hash
        ).first()
        
        if existing_syllabus:
            # File with same content already exists
            logger.info(f"Duplicate file detected (same content). Original: {existing_syllabus.filename}, New: {file.filename}")
            
            # Return cached analysis without re-analyzing
            hierarchy = existing_syllabus.hierarchy
            analysis_summary = calculate_analysis_summary(hierarchy if hierarchy else {})
            
            return {
                "success": True,
                "message": f"File with same content already exists as '{existing_syllabus.filename}'. Using previous analysis.",
                "data": {
                    "syllabus_id": existing_syllabus.id,
                    "filename": existing_syllabus.filename,
                    "file_type": existing_syllabus.file_type,
                    "course_name": existing_syllabus.course_name,
                    "department": existing_syllabus.department,
                    "file_size_bytes": existing_syllabus.file_size_bytes,
                    "uploaded_at": existing_syllabus.uploaded_at.isoformat() if existing_syllabus.uploaded_at else None,
                    "hierarchy": hierarchy,
                    "analysis_summary": analysis_summary,
                }
            }
        
        # Process file and extract text
        extracted_text, file_type = process_file(file.filename, file_content)
        logger.info(f"File processed successfully: {file.filename} (type: {file_type})")

        # Analyze using syllabus_agent to extract hierarchical structure
        analysis_result = analyze(extracted_text)
        if isinstance(analysis_result, str):
            try:
                analysis_json = json.loads(analysis_result)
            except json.JSONDecodeError:
                analysis_json = {"raw_analysis": analysis_result}
        else:
            analysis_json = analysis_result if analysis_result else {}
        logger.info(f"Syllabus analysis completed for file: {file.filename}")

        # Extract course name from analysis or file
        course_name = analysis_json.get("course_title") or extract_course_name_from_text(extracted_text, file.filename)

        # Extract hierarchical structure: units -> topics -> concepts
        hierarchy = analysis_json if "units" in analysis_json else None

        # Analyze complexity for all concepts in hierarchy
        if hierarchy:
            logger.info("Starting complexity analysis for concepts...")
            hierarchy = analyze_hierarchy_complexity(hierarchy)
            logger.info("Complexity analysis completed")

        # For backward compatibility, extract flat lists
        units = analysis_json.get("units", None)
        concepts = analysis_json.get("concepts", None)

        # Calculate analysis summary
        analysis_summary = calculate_analysis_summary(analysis_json)

        # Add analyzed content to vector store
        vector_text = f"Course: {course_name}\n\n{extracted_text}"
        vector_store_result = add(vector_text)
        vector_store_id = str(vector_store_result) if vector_store_result else None
        logger.info(f"Added to vector store: {file.filename}")

        # Create syllabus record in database
        syllabus = Syllabus(
            staff_id=staff_id,
            filename=file.filename,
            file_type=file_type,
            course_name=course_name,
            department=staff.department,
            raw_text=extracted_text[:10000],  # Store first 10000 chars for preview
            hierarchy=hierarchy,  # Store complete hierarchical structure with complexity
            units=units,
            concepts=concepts,
            analysis_result=analysis_json,
            vector_store_id=vector_store_id,
            file_size_bytes=len(file_content),
            file_hash=file_hash,
            analysis_summary=analysis_summary,
        )
        db.add(syllabus)
        db.commit()
        db.refresh(syllabus)
        logger.info(f"Syllabus record created: ID {syllabus.id} with hierarchical structure for staff {staff_id}")
        
        # Store individual unit->topic->concept mappings with complexity in database
        if hierarchy and "units" in hierarchy:
            logger.info("Storing unit->topic->concept mappings with complexity levels...")
            for unit in hierarchy.get("units", []):
                unit_id = unit.get("unit_id", "")
                unit_name = unit.get("unit_name", "")
                
                for topic in unit.get("topics", []):
                    topic_id = topic.get("topic_id", "")
                    topic_name = topic.get("topic_name", "")
                    
                    for concept in topic.get("concepts", []):
                        # Handle both dict and string concept formats
                        if isinstance(concept, dict):
                            concept_name = concept.get("name", "")
                            complexity_str = concept.get("complexity_level", "MEDIUM")
                        else:
                            concept_name = str(concept)
                            complexity_str = "MEDIUM"
                        
                        # Ensure complexity_str is a valid enum value
                        if complexity_str not in ["LOW", "MEDIUM", "HIGH"]:
                            complexity_str = "MEDIUM"
                        
                        complexity_level = ComplexityLevel(complexity_str)
                        
                        # Create unit->topic->concept mapping record
                        utc_record = UnitTopicConcept(
                            syllabus_id=syllabus.id,
                            unit_id=unit_id,
                            unit_name=unit_name,
                            topic_id=topic_id,
                            topic_name=topic_name,
                            concept_name=concept_name,
                            complexity_level=complexity_level
                        )
                        db.add(utc_record)
            
            db.commit()
            logger.info(f"Stored unit->topic->concept mappings for syllabus ID {syllabus.id}")
        
        return {
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
                "analysis_summary": analysis_summary,
            }
        }
        
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
    Returns only essential fields for better performance.
    """
    db = SessionLocal()
    
    try:
        staff_id = get_current_user_id(authorization)
        
        syllabuses = db.query(Syllabus).filter(
            Syllabus.staff_id == staff_id
        ).order_by(Syllabus.uploaded_at.desc()).all()
        
        # Only return necessary fields for listing
        return {
            "success": True,
            "data": [
                {
                    "id": s.id,
                    "filename": s.filename,
                    "file_type": s.file_type,
                    "course_name": s.course_name,
                    "department": s.department,
                    "file_size_bytes": s.file_size_bytes,
                    "uploaded_at": s.uploaded_at.isoformat() if s.uploaded_at else None,
                    "analysis_summary": s.analysis_summary,
                    "hierarchy": s.hierarchy,
                } for s in syllabuses
            ],
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

@router.post(
    "/{syllabus_id}/analyze",
    summary="Analyze Syllabus",
    description="Analyze a syllabus or return existing analysis",
    responses={
        200: {"description": "Syllabus analyzed successfully"},
        401: {"description": "Unauthorized - missing or invalid token"},
        404: {"description": "Syllabus not found"}
    }
)
async def analyze_syllabus(
    syllabus_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Analyze a syllabus to extract hierarchical structure.
    If analysis already exists, returns the cached result.
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
        
        # If analysis already exists, return cached result
        if syllabus.hierarchy and syllabus.analysis_summary:
            logger.info(f"Returning cached analysis for syllabus {syllabus_id}")
            return {
                "success": True,
                "message": "Analysis retrieved successfully",
                "data": {
                    "hierarchy": syllabus.hierarchy,
                    "analysis_summary": syllabus.analysis_summary,
                    "course_name": syllabus.course_name,
                    "filename": syllabus.filename,
                }
            }
        
        # If no analysis exists, perform new analysis
        logger.info(f"Performing new analysis for syllabus {syllabus_id}")
        
        if not syllabus.raw_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No raw text available for analysis"
            )
        
        # Run analysis
        analysis_result = analyze(syllabus.raw_text)
        if isinstance(analysis_result, str):
            try:
                analysis_json = json.loads(analysis_result)
            except json.JSONDecodeError:
                analysis_json = {"raw_analysis": analysis_result}
        else:
            analysis_json = analysis_result if analysis_result else {}
        
        # Extract hierarchical structure
        hierarchy = analysis_json if "units" in analysis_json else None
        analysis_summary = calculate_analysis_summary(analysis_json)
        
        # Update database with analysis results
        syllabus.hierarchy = hierarchy
        syllabus.analysis_result = analysis_json
        syllabus.analysis_summary = analysis_summary
        db.commit()
        
        logger.info(f"Analysis completed for syllabus {syllabus_id}")
        
        return {
            "success": True,
            "message": "Analysis completed successfully",
            "data": {
                "hierarchy": hierarchy,
                "analysis_summary": analysis_summary,
                "course_name": syllabus.course_name,
                "filename": syllabus.filename,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing syllabus: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze syllabus"
        )
    finally:
        db.close()


@router.get(
    "/{syllabus_id}/units-topics-concepts",
    summary="Get Unit->Topic->Concepts Mapping",
    description="Get the hierarchical unit->topic->concepts mapping with complexity levels",
    responses={
        200: {"description": "Mapping retrieved successfully"},
        401: {"description": "Unauthorized - missing or invalid token"},
        404: {"description": "Syllabus not found"}
    }
)
async def get_units_topics_concepts(
    syllabus_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Get the unit->topic->concepts hierarchical mapping for a syllabus with complexity levels.
    This endpoint returns data organized as units, with each unit containing topics, 
    and each topic containing concepts with complexity levels.
    """
    db = SessionLocal()
    
    try:
        staff_id = get_current_user_id(authorization)
        
        # Verify syllabus belongs to user
        syllabus = db.query(Syllabus).filter(
            Syllabus.id == syllabus_id,
            Syllabus.staff_id == staff_id
        ).first()
        
        if not syllabus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Syllabus not found"
            )
        
        # Fetch all unit->topic->concept mappings
        utc_records = db.query(UnitTopicConcept).filter(
            UnitTopicConcept.syllabus_id == syllabus_id
        ).order_by(
            UnitTopicConcept.unit_id,
            UnitTopicConcept.topic_id,
            UnitTopicConcept.concept_name
        ).all()
        
        # Build hierarchical structure
        units_dict = {}
        
        for record in utc_records:
            unit_key = record.unit_id
            
            if unit_key not in units_dict:
                units_dict[unit_key] = {
                    "unit_id": record.unit_id,
                    "unit_name": record.unit_name,
                    "topics": {}
                }
            
            topic_key = record.topic_id
            if topic_key not in units_dict[unit_key]["topics"]:
                units_dict[unit_key]["topics"][topic_key] = {
                    "topic_id": record.topic_id,
                    "topic_name": record.topic_name,
                    "concepts": []
                }
            
            units_dict[unit_key]["topics"][topic_key]["concepts"].append({
                "concept_name": record.concept_name,
                "complexity_level": record.complexity_level.value if record.complexity_level else "MEDIUM",
                "id": record.id
            })
        
        # Convert nested dict to list structure
        units = []
        for unit in units_dict.values():
            topics = list(unit["topics"].values())
            units.append({
                "unit_id": unit["unit_id"],
                "unit_name": unit["unit_name"],
                "topics": topics
            })
        
        logger.info(f"Retrieved unit->topic->concepts mapping for syllabus {syllabus_id}")
        
        return {
            "success": True,
            "message": "Unit->Topic->Concepts mapping retrieved successfully",
            "data": {
                "syllabus_id": syllabus_id,
                "course_name": syllabus.course_name,
                "units": units,
                "total_units": len(units),
                "total_topics": sum(len(u["topics"]) for u in units),
                "total_concepts": sum(
                    len(t["concepts"]) for u in units for t in u["topics"]
                )
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving unit->topic->concepts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve unit->topic->concepts mapping"
        )
    finally:
        db.close()