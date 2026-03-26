"""
Database initialization and utilities
"""
from app.database.session import engine
from app.database.base import Base


def init_db():
    """Create all database tables"""
    # Import all models to register them with Base
    # Import order matters: models with foreign keys should be imported after their dependencies
    from app.models.staff import Staff
    from app.models.syllabus import Syllabus
    from app.models.unit_topic_concept import UnitTopicConcept
    from app.models.task import Task
    from app.models import Department, Subject, Unit, Concept, ConceptProgress
    
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all database tables (use with caution)"""
    Base.metadata.drop_all(bind=engine)
