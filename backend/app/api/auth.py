
from fastapi import APIRouter
from app.core.security import hash_password, create_token
from app.database.session import SessionLocal
from app.models.staff import Staff

router = APIRouter(prefix="/auth")

@router.post("/signup")
def signup(data: dict):
    db = SessionLocal()
    staff = Staff(**data, password=hash_password(data["password"]))
    db.add(staff)
    db.commit()
    return {"message": "Registered"}

@router.post("/login")
def login(data: dict):
    db = SessionLocal()
    staff = db.query(Staff).filter(Staff.email == data["email"]).first()
    return {"access_token": create_token({"id": staff.id})}
