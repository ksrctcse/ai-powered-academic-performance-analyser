from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subjects = relationship("Subject", back_populates="department")


class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    code = Column(String, unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    department = relationship("Department", back_populates="subjects")
    units = relationship("Unit", back_populates="subject")


class Unit(Base):
    __tablename__ = "units"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    order = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subject = relationship("Subject", back_populates="units")
    concepts = relationship("Concept", back_populates="unit")


class Concept(Base):
    __tablename__ = "concepts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    complexity_level = Column(String, nullable=True)  # e.g., "Easy", "Medium", "Hard"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    unit = relationship("Unit", back_populates="concepts")
    progress = relationship("ConceptProgress", back_populates="concept")


class ConceptProgress(Base):
    __tablename__ = "concept_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False, index=True)
    unit_topic_concept_id = Column(Integer, ForeignKey("unit_topic_concept.id"), nullable=True, index=True)
    
    # Progress tracking
    completion_percentage = Column(Integer, default=0)
    status = Column(String, default="Not Started")  # Not Started, In Progress, Completed
    
    # Dates
    start_date = Column(DateTime, nullable=True)  # When staff started learning this concept
    end_date = Column(DateTime, nullable=True)    # When staff completed this concept
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    staff = relationship("Staff", back_populates="concept_progress")
    concept = relationship("Concept", back_populates="progress")
    tasks = relationship("Task", back_populates="concept_progress", cascade="all, delete-orphan")


# Import Staff here to avoid circular imports
from app.models.staff import Staff
