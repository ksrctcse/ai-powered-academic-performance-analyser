
from sqlalchemy import Column, Integer, String
from app.database.base import Base

class Staff(Base):
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    department = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
