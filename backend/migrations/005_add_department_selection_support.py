"""
Migration: 005_add_department_selection_support.py
Adds proper support for department selection:
1. Ensure department column exists and is indexed in syllabus table
2. Add index for efficient department filtering
3. Set default department for existing syllabuses
"""

from sqlalchemy import text
from app.database.session import engine
from app.core.logger import get_logger

logger = get_logger(__name__)

# Define valid departments
VALID_DEPARTMENTS = ["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL"]

def upgrade():
    """Apply the migration"""
    with engine.connect() as conn:
        try:
            # Check if department column exists
            check_column = """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'syllabus' AND column_name = 'department'
            """
            result = conn.execute(text(check_column))
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                # Add department column if it doesn't exist
                conn.execute(text("""
                    ALTER TABLE syllabus ADD COLUMN department VARCHAR DEFAULT 'CSE'
                """))
                logger.info("✓ Added 'department' column to syllabus table")
            else:
                logger.info("✓ 'department' column already exists in syllabus table")
            
            # Create index for department filtering
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_syllabus_department ON syllabus(department)
            """))
            logger.info("✓ Created index on department column")
            
            # Ensure all existing syllabuses have a valid department
            conn.execute(text("""
                UPDATE syllabus SET department = 'CSE' WHERE department IS NULL OR department = ''
            """))
            logger.info("✓ Set default department 'CSE' for syllabuses with null/empty department")
            
            conn.commit()
            logger.info("✓ Migration 005 completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error applying migration 005: {str(e)}", exc_info=True)
            conn.rollback()
            raise

def downgrade():
    """Rollback the migration"""
    with engine.connect() as conn:
        try:
            # Drop index
            conn.execute(text("DROP INDEX IF EXISTS idx_syllabus_department"))
            logger.info("✓ Dropped department index")
            
            # Drop column
            conn.execute(text("ALTER TABLE syllabus DROP COLUMN IF EXISTS department"))
            logger.info("✓ Dropped 'department' column from syllabus table")
            
            conn.commit()
            logger.info("✓ Migration 005 rolled back successfully!")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error rolling back migration 005: {str(e)}", exc_info=True)
            conn.rollback()
            raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()
