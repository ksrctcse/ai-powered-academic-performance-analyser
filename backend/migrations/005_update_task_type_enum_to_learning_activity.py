"""
Migration: 005_update_task_type_enum_to_learning_activity.py
This migration:
1. Updates the tasktype enum in PostgreSQL to replace ASSIGNMENT with LEARNING_ACTIVITY
2. Handles enum migration in PostgreSQL by creating new type and migrating column
"""

from sqlalchemy import text
from app.database.session import SessionLocal, engine

def upgrade():
    """Apply the migration"""
    with engine.connect() as conn:
        try:
            # Step 1: Create new enum type with all values including LEARNING_ACTIVITY
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
                            'ASSIGNMENT',
                            'LEARNING_ACTIVITY'
                        );
                    END IF;
                END $$;
            """))
            
            # Step 2: Alter the tasks.task_type column to use new enum
            conn.execute(text("""
                ALTER TABLE tasks 
                ALTER COLUMN task_type TYPE tasktype_new USING task_type::text::tasktype_new;
            """))
            
            # Step 3: Update existing ASSIGNMENT values to LEARNING_ACTIVITY
            conn.execute(text("""
                UPDATE tasks SET task_type = 'LEARNING_ACTIVITY' WHERE task_type = 'ASSIGNMENT';
            """))
            
            # Step 4: Drop old enum type if it exists
            conn.execute(text("""
                DROP TYPE IF EXISTS tasktype CASCADE;
            """))
            
            # Step 5: Rename new enum to original name
            conn.execute(text("""
                ALTER TYPE tasktype_new RENAME TO tasktype;
            """))
            
            # Step 6: Update column default to LEARNING_ACTIVITY
            conn.execute(text("""
                ALTER TABLE tasks 
                ALTER COLUMN task_type SET DEFAULT 'LEARNING_ACTIVITY';
            """))
            
            conn.commit()
            print("✓ Migration 005: TaskType enum updated successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Error in migration 005: {e}")
            raise


def downgrade():
    """Revert the migration"""
    with engine.connect() as conn:
        try:
            # Revert back to using VARCHAR if needed
            conn.execute(text("""
                ALTER TABLE tasks 
                ALTER COLUMN task_type TYPE VARCHAR;
            """))
            conn.commit()
            print("✓ Migration 005 rolled back successfully!")
        except Exception as e:
            conn.rollback()
            print(f"✗ Error reverting migration 005: {e}")
            raise


if __name__ == "__main__":
    upgrade()
