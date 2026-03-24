"""
Migration: Add learning_task_progress column to tasks table for per-task progress tracking
Stores individual progress for each generated learning task: [{task_title, completion_percentage, status, notes}, ...]
"""

from sqlalchemy import text
from app.database.session import SessionLocal, engine
import logging

logger = logging.getLogger(__name__)


def upgrade():
    """Add learning_task_progress column to tasks table"""
    db = SessionLocal()
    try:
        # Check if column already exists
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='tasks' AND column_name='learning_task_progress'
                """)
            )
            if result.fetchone():
                logger.info("learning_task_progress column already exists in tasks table")
                return
            
            # Add the column with default empty array
            conn.execute(
                text("""
                    ALTER TABLE tasks 
                    ADD COLUMN learning_task_progress JSON DEFAULT '[]'
                """)
            )
            conn.commit()
            logger.info("Successfully added learning_task_progress column to tasks table")
        
    except Exception as e:
        logger.error(f"Error during upgrade: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


def downgrade():
    """Remove learning_task_progress column from tasks table"""
    db = SessionLocal()
    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    ALTER TABLE tasks 
                    DROP COLUMN IF EXISTS learning_task_progress
                """)
            )
            conn.commit()
            logger.info("Successfully removed learning_task_progress column from tasks table")
        
    except Exception as e:
        logger.error(f"Error during downgrade: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


