"""
Migration: 006_update_existing_syllabus_department.py
Updates existing syllabus ID 3 (if it exists) to set department as CSE
"""

from sqlalchemy import text
from app.database.session import engine
from app.core.logger import get_logger

logger = get_logger(__name__)

def upgrade():
    """Apply the migration"""
    with engine.connect() as conn:
        try:
            # Check if syllabus with id 3 exists
            check_sql = "SELECT id FROM syllabus WHERE id = 3"
            result = conn.execute(text(check_sql))
            exists = result.fetchone() is not None
            
            if exists:
                # Update syllabus id 3 with CSE department
                conn.execute(text("""
                    UPDATE syllabus SET department = 'CSE' WHERE id = 3
                """))
                logger.info("✓ Updated syllabus ID 3 to department CSE")
            else:
                logger.info("⚠ Syllabus ID 3 does not exist, skipping update")
            
            conn.commit()
            logger.info("✓ Migration 006 completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error applying migration 006: {str(e)}", exc_info=True)
            conn.rollback()
            raise

def downgrade():
    """Rollback the migration"""
    with engine.connect() as conn:
        try:
            # Reset syllabus id 3 department to CSE (or leave as is)
            # For this migration, downgrade doesn't change anything
            logger.info("✓ Migration 006 rolled back (no changes made)")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error rolling back migration 006: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()
