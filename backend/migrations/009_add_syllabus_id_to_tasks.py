"""
Migration: Add syllabus_id to tasks table
This migration adds a foreign key column to link tasks back to syllabuses
for better organization and filtering capabilities.
"""

from sqlalchemy import Column, Integer, ForeignKey, text
from app.database.session import SessionLocal, engine
from app.models.task import Task
from app.models import Base
import logging

logger = logging.getLogger(__name__)


def upgrade():
    """Add syllabus_id column to tasks table"""
    db = SessionLocal()
    try:
        # Check if column already exists
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='tasks' AND column_name='syllabus_id'
                """)
            )
            if result.fetchone():
                logger.info("syllabus_id column already exists in tasks table")
                return
            
            # Add the column
            conn.execute(
                text("""
                    ALTER TABLE tasks 
                    ADD COLUMN syllabus_id INTEGER,
                    ADD CONSTRAINT fk_tasks_syllabus_id 
                    FOREIGN KEY (syllabus_id) 
                    REFERENCES syllabus(id)
                """)
            )
            conn.execute(text("CREATE INDEX idx_tasks_syllabus_id ON tasks(syllabus_id)"))
            conn.commit()
            logger.info("Successfully added syllabus_id column to tasks table")
        
    except Exception as e:
        logger.error(f"Error during upgrade: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


def downgrade():
    """Remove syllabus_id column from tasks table"""
    db = SessionLocal()
    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    ALTER TABLE tasks 
                    DROP CONSTRAINT IF EXISTS fk_tasks_syllabus_id,
                    DROP COLUMN IF EXISTS syllabus_id
                """)
            )
            conn.commit()
            logger.info("Successfully removed syllabus_id column from tasks table")
        
    except Exception as e:
        logger.error(f"Error during downgrade: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    upgrade()
    logger.info("Migration completed successfully")
