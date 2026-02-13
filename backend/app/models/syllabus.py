from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class Syllabus(Base):
    __tablename__ = "syllabus"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # 'pdf', 'csv', 'docx'
    course_name = Column(String, nullable=True)
    department = Column(String, nullable=False)
    
    # Content and Analysis
    raw_text = Column(Text, nullable=True)  # Store the extracted raw text
    
    # Hierarchical structure: units -> topics -> concepts
    # Structure: {"course_title": "...", "units": [...]}
    hierarchy = Column(JSON, nullable=True)  # Complete unit->topic->concept hierarchy
    
    # Legacy fields (kept for backward compatibility)
    units = Column(JSON, nullable=True)  # Extracted units from analysis
    concepts = Column(JSON, nullable=True)  # Extracted concepts from analysis
    analysis_result = Column(JSON, nullable=True)  # Complete analysis result from syllabus_agent
    
    # Vector Store References
    vector_store_id = Column(String, nullable=True)  # Reference to FAISS vector store
    vector_store_indices = Column(JSON, nullable=True)  # Indices of vectors added for each unit/topic
    
    # Metadata
    file_size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    staff = relationship("Staff", backref="syllabuses")
    
    def to_dict(self):
        return {
            "id": self.id,
            "staff_id": self.staff_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "course_name": self.course_name,
            "department": self.department,
            "hierarchy": self.hierarchy,
            "units": self.units,
            "concepts": self.concepts,
            "analysis_result": self.analysis_result,
            "vector_store_id": self.vector_store_id,
            "file_size_bytes": self.file_size_bytes,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
