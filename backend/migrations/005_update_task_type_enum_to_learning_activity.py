"""
Migration: 005_update_task_type_enum_to_learning_activity.py
This migration:
1. Updates the tasktype enum in PostgreSQL to include LEARNING_ACTIVITY
2. Handles enum migration by converting to text and back
3. Updates existing ASSIGNMENT values to LEARNING_ACTIVITY
"""

from sqlalchemy import text
from app.database.session import SessionLocal, engine
import logging

logger = logging.getLogger(__name__)

def upgrade():
    """Apply the migration"""
    with engine.connect() as conn:
        try:
            # Step 0: Remove default constraint first
            conn.execute(text("""
                ALTER TABLE tasks 
                ALTER COLUMN task_type DROP DEFAULT;
            """))
            logger.info("✓ Dropped default constraint")
            
            # Step 1: Create new enum type with all required values
            conn.execute(text("""
                DO $$ BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tasktype_new') THEN
                        CREATE TYPE tasktype_new AS ENUM (
                            'PENDING',
                            'IN_PROGRESS', 
                            'COMPLETED',
                            'OVERDUE',
                            'READING',
                            'PROBLEM_SOLVING',
                            'QUIZ',
                            'PROJECT',
                            'DISCUSSION',
                            'LEARNING_ACTIVITY'
                        );
                    END IF;
                END $$;
            """))
            logger.info("✓ Created new enum type")
            
            # Step 2: Alter column to TEXT temporarily
            conn.execute(text("""
                ALTER TABLE tasks 
                ALTER COLUMN task_type TYPE VARCHAR;
            """))
            logger.info("✓ Converted column to VARCHAR")
            
            # Step 3: Update ASSIGNMENT to LEARNING_ACTIVITY and handle NULL
            conn.execute(text("""
                UPDATE tasks SET task_type = 'LEARNING_ACTIVITY' 
                WHERE task_type = 'ASSIGNMENT' OR task_type IS NULL;
            """))
            logger.info("✓ Updated ASSIGNMENT values to LEARNING_ACTIVITY")
            
            # Step 4: Cast column to new enum type
            conn.execute(text("""
                ALTER TABLE tasks 
                ALTER COLUMN task_type TYPE tasktype_new USING task_type::tasktype_new;
            """))
            logger.info("✓ Converted column to new enum type")
            
            # Step 5: Drop old enum type if it exists
            conn.execute(text("""
                DROP TYPE IF EXISTS tasktype CASCADE;
            """))
            logger.info("✓ Dropped old enum type")
            
            # Step 6: Rename new enum to original name
            conn.execute(text("""
                ALTER TYPE tasktype_new RENAME TO tasktype;
            """))
            logger.info("✓ Renamed enum type to original name")
            
            # Step 7: Set default to LEARNING_ACTIVITY
            conn.execute(text("""
                ALTER TABLE tasks 
                ALTER COLUMN task_type SET DEFAULT 'LEARNING_ACTIVITY';
            """))
            logger.info("✓ Set default value to LEARNING_ACTIVITY")
            
            conn.commit()
            print("✓ Migration 005: TaskType enum updated successfully!")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"✗ Error in migration 005: {e}", exc_info=True)
            print(f"✗ Error in migration 005: {e}")
            raise


def downgrade():
    """Revert the migration"""
    with engine.connect() as conn:
        try:
            # Revert back to VARCHAR if needed
            conn.execute(text("""
                ALTER TABLE tasks 
                ALTER COLUMN task_type TYPE VARCHAR;
            """))
            conn.commit()
            logger.info("✓ Migration 005 rolled back successfully!")
            print("✓ Migration 005 rolled back successfully!")
        except Exception as e:
            conn.rollback()
            logger.error(f"✗ Error reverting migration 005: {e}", exc_info=True)
            print(f"✗ Error reverting migration 005: {e}")
            raise

