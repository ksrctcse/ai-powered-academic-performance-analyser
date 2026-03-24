"""
Migration: 007_add_department_to_tasks.py
Adds department tracking to tasks table for efficient filtering
"""

from sqlalchemy import text
from app.database.session import engine
from app.core.logger import get_logger

logger = get_logger(__name__)

def upgrade():
    """Apply the migration"""
    with engine.connect() as conn:
        try:
            # Check if department column exists in tasks table
            check_column = """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'tasks' AND column_name = 'department'
            """
            result = conn.execute(text(check_column))
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                # Add department column if it doesn't exist
                conn.execute(text("""
                    ALTER TABLE tasks ADD COLUMN department VARCHAR DEFAULT 'CSE'
                """))
                logger.info("✓ Added 'department' column to tasks table")
            else:
                logger.info("✓ 'department' column already exists in tasks table")
            
            # Create index for department filtering in tasks
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tasks_department ON tasks(department)
            """))
            logger.info("✓ Created index on tasks.department column")
            
            # Create composite index for staff + department filtering
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tasks_staff_department ON tasks(staff_id, department)
            """))
            logger.info("✓ Created composite index on tasks(staff_id, department)")
            
            conn.commit()
            logger.info("✓ Migration 007 completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error applying migration 007: {str(e)}", exc_info=True)
            conn.rollback()
            raise


def downgrade():
    """Rollback the migration"""
    with engine.connect() as conn:
        try:
            # Drop indexes
            conn.execute(text("DROP INDEX IF EXISTS idx_tasks_department"))
            logger.info("✓ Dropped idx_tasks_department index")
            
            conn.execute(text("DROP INDEX IF EXISTS idx_tasks_staff_department"))
            logger.info("✓ Dropped idx_tasks_staff_department index")
            
            # Drop column
            conn.execute(text("ALTER TABLE tasks DROP COLUMN IF EXISTS department"))
            logger.info("✓ Dropped 'department' column from tasks table")
            
            conn.commit()
            logger.info("✓ Migration 007 rolled back successfully!")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error rolling back migration 007: {str(e)}", exc_info=True)
            conn.rollback()
            raise


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()
