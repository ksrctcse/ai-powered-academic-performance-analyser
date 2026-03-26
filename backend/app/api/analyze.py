from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional
from app.agents.syllabus_agent import analyze
from app.utils.file_processor import process_file, FileProcessingError
from app.core.logger import get_logger
from app.core.security import SECRET_KEY
from jose import jwt, JWTError
import json

logger = get_logger(__name__)

router = APIRouter(
    prefix="/analyze",
    tags=["Syllabus Analysis"],
    responses={404: {"description": "Not found"}}
)

def get_current_user_id(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
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
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed"
        )

@router.post("/syllabus", summary="Analyze syllabus text", description="Analyze syllabus text and return hierarchy.")
async def analyze_syllabus(
    text: str,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    user_id = get_current_user_id(authorization)
    try:
        result = analyze(text)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception:
                result = {"raw_analysis": result}
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Syllabus analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze syllabus: {str(e)}"
        )
