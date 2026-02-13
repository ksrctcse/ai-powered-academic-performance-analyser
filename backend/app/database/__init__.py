"""
Database initialization and utilities
"""
from app.database.session import engine
from app.database.base import Base
# Import all models to register them with Base
from app.models.staff import Staff
from app.models.syllabus import Syllabus
from app.models import Department, Subject, Unit, Concept, ConceptProgress


def init_db():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all database tables (use with caution)"""
    Base.metadata.drop_all(bind=engine)
