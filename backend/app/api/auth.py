
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from app.core.security import hash_password, create_token, verify_password
from app.core.logger import get_logger
from app.database.session import SessionLocal
from app.models.staff import Staff
import traceback

logger = get_logger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}}
)

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    department: str
    userType: str = 'staff'  # 'staff' or 'student'
    rollNumber: Optional[str] = None  # Optional, only for students

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "staff@example.com",
                "password": "password123",
                "name": "John Doe",
                "department": "CSE",
                "userType": "staff"
            }
        }

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    user: dict

@router.post(
    "/signup",
    summary="Staff Registration",
    description="Register a new staff member with email and password",
    responses={
        200: {"description": "Successfully registered"},
        400: {"description": "Invalid input or user already exists"}
    }
)
def signup(data: SignupRequest):
    db = SessionLocal()
    logger.info(f"Signup attempt for email: {data.email}")
    try:
        # Check if email already exists
        existing_staff = db.query(Staff).filter(Staff.email == data.email).first()
        if existing_staff:
            logger.warning(f"Signup failed: Email already exists - {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new staff record
        staff = Staff(
            email=data.email,
            password=hash_password(data.password),
            name=data.name,
            department=data.department,
            user_type=data.userType,
            roll_number=data.rollNumber if data.userType == 'student' else None
        )
        db.add(staff)
        db.commit()
        db.refresh(staff)
        
        logger.info(f"User registered successfully: {staff.email} (ID: {staff.id}, Type: {staff.user_type})")
        return {
            "message": "Successfully registered",
            "user": {
                "id": staff.id,
                "email": staff.email,
                "name": staff.name,
                "userType": staff.user_type
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Signup error for {data.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )
    finally:
        db.close()

@router.post(
    "/login",
    summary="Staff Login",
    description="Authenticate staff member and receive JWT token",
    response_model=AuthResponse,
    responses={
        200: {"description": "Login successful, returns access token"},
        401: {"description": "Invalid credentials"}
    }
)
def login(data: LoginRequest):
    db = SessionLocal()
    logger.info(f"Login attempt for email: {data.email}")
    try:
        staff = db.query(Staff).filter(Staff.email == data.email).first()
        
        if not staff:
            logger.warning(f"Login failed: User not found - {data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not verify_password(data.password, staff.password):
            logger.warning(f"Login failed: Invalid password for - {data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        access_token = create_token({"id": staff.id, "email": staff.email})
        logger.info(f"User logged in successfully: {staff.email} (ID: {staff.id}, Type: {staff.user_type})")
        
        return {
            "access_token": access_token,
            "user": {
                "id": staff.id,
                "email": staff.email,
                "name": staff.name,
                "userType": staff.user_type
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {data.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )
    finally:
        db.close()

