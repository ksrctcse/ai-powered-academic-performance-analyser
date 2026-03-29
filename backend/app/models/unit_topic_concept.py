from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.base import Base
import enum


class ComplexityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class UnitTopicConcept(Base):
    """
    Stores the hierarchical mapping of Unit -> Topic -> Concepts with complexity analysis.
    This model captures the analyzed structure from syllabus documents.
    """
    __tablename__ = "unit_topic_concept"
    
    id = Column(Integer, primary_key=True, index=True)
    syllabus_id = Column(Integer, ForeignKey("syllabus.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Hierarchical structure
    unit_id = Column(String, nullable=False)  # Unit identifier/index
    unit_name = Column(String, nullable=False)  # Unit name/title
    
    topic_id = Column(String, nullable=False)  # Topic identifier/index
    topic_name = Column(String, nullable=False)  # Topic name/title
    
    concept_name = Column(String, nullable=False)  # Concept name
    complexity_level = Column(Enum(ComplexityLevel), default=ComplexityLevel.MEDIUM, nullable=False)
    
    # Additional metadata for future use
    description = Column(String, nullable=True)  # Optional concept description
    learning_objectives = Column(JSON, nullable=True)  # List of learning objectives
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    syllabus = relationship("Syllabus", foreign_keys=[syllabus_id])
    
    def to_dict(self):
        return {
            "id": self.id,
            "syllabus_id": self.syllabus_id,
            "unit_id": self.unit_id,
            "unit_name": self.unit_name,
            "topic_id": self.topic_id,
            "topic_name": self.topic_name,
            "concept_name": self.concept_name,
            "complexity_level": self.complexity_level.value if self.complexity_level else None,
            "description": self.description,
            "learning_objectives": self.learning_objectives,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
