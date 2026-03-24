from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base
import enum


class TaskStatus(str, enum.Enum):
    """Task status enumeration"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"


class TaskType(str, enum.Enum):
    """Task type enumeration"""
    READING = "READING"
    PROBLEM_SOLVING = "PROBLEM_SOLVING"
    QUIZ = "QUIZ"
    PROJECT = "PROJECT"
    DISCUSSION = "DISCUSSION"
    ASSIGNMENT = "ASSIGNMENT"


class Task(Base):
    """
    Represents a learning task/assignment generated for concept progress tracking.
    Each task is associated with one or more concepts and a staff member.
    """
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)
    syllabus_id = Column(Integer, ForeignKey("syllabus.id"), nullable=True, index=True)
    concept_progress_id = Column(Integer, ForeignKey("concept_progress.id"), nullable=True, index=True)
    
    # Department tracking (for filtering tasks by department)
    department = Column(String, default="CSE", nullable=False, index=True)
    
    # Task information
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(Enum(TaskType), default=TaskType.ASSIGNMENT, nullable=False)
    content = Column(JSON, nullable=True)  # Flexible storage for task details
    
    # Concepts and effort information
    concepts = Column(JSON, nullable=True)  # Array of {name, complexity, id}
    covered_topics = Column(JSON, nullable=True)  # Array of covered topics/content
    effort_hours = Column(Float, nullable=True)  # Estimated effort in hours
    average_complexity = Column(String, nullable=True)  # LOW, MEDIUM, HIGH
    
    # Individual learning task progress tracking
    # Each entry: {task_title, completion_percentage, status, notes}
    learning_task_progress = Column(JSON, default=list, nullable=True)  # Array of learning task progress
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_date = Column(DateTime, nullable=True)  # When task started
    end_date = Column(DateTime, nullable=True)  # Calculated end date (start_date + effort)
    due_date = Column(DateTime, nullable=True)  # Manual due date if different
    completed_at = Column(DateTime, nullable=True)
    
    # Status tracking
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    completion_percentage = Column(Integer, default=0)  # 0-100
    notes = Column(Text, nullable=True)  # Staff notes on task completion
    
    # Relationships
    staff = relationship("Staff", foreign_keys=[staff_id])
    syllabus = relationship("Syllabus", back_populates="tasks", foreign_keys=[syllabus_id])
    concept_progress = relationship("ConceptProgress", back_populates="tasks")
    
    def to_dict(self):
        return {
            "id": self.id,
            "staff_id": self.staff_id,
            "syllabus_id": self.syllabus_id,
            "concept_progress_id": self.concept_progress_id,
            "department": self.department,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type.value if self.task_type else None,
            "status": self.status.value if self.status else None,
            "completion_percentage": self.completion_percentage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
            "content": self.content,
            "concepts": self.concepts,
            "covered_topics": self.covered_topics,
            "effort_hours": self.effort_hours,
            "average_complexity": self.average_complexity,
            "learning_task_progress": self.learning_task_progress,
        }
