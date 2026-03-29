"""
Migration: Replace roll_number column with staff_user_id in staff table
This migration removes the optional roll_number column and replaces it with 
a more general staff_user_id column for unique staff/student identification.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.session import SessionLocal, engine
import logging

logger = logging.getLogger(__name__)


def upgrade():
    """Replace roll_number column with staff_user_id in staff table"""
    db = SessionLocal()
    try:
        with engine.connect() as conn:
            # Check if roll_number exists
            check_roll_col = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='staff' AND column_name='roll_number'
            """)
            result = conn.execute(check_roll_col)
            roll_exists = result.fetchone() is not None
            
            # Check if staff_user_id already exists
            check_staff_col = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='staff' AND column_name='staff_user_id'
            """)
            result = conn.execute(check_staff_col)
            staff_user_id_exists = result.fetchone() is not None
            
            if not staff_user_id_exists:
                # Add staff_user_id column first
                conn.execute(text("""
                    ALTER TABLE staff 
                    ADD COLUMN staff_user_id VARCHAR UNIQUE
                """))
                logger.info("✓ Added 'staff_user_id' column to staff table")
                
                # Create index on staff_user_id
                try:
                    conn.execute(text("CREATE INDEX idx_staff_user_id ON staff(staff_user_id)"))
                    logger.info("✓ Created index on 'staff_user_id' column")
                except Exception as e:
                    logger.warning(f"Index creation skipped: {str(e)}")
            
            if roll_exists:
                # Drop roll_number column
                conn.execute(text("""
                    ALTER TABLE staff 
                    DROP COLUMN roll_number
                """))
                logger.info("✓ Dropped 'roll_number' column from staff table")
            
            conn.commit()
            logger.info("✅ Migration 011 completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Error during upgrade: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


def downgrade():
    """Revert changes: restore roll_number and remove staff_user_id"""
    db = SessionLocal()
    try:
        with engine.connect() as conn:
            # Check if staff_user_id exists
            check_staff_col = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='staff' AND column_name='staff_user_id'
            """)
            result = conn.execute(check_staff_col)
            staff_user_id_exists = result.fetchone() is not None
            
            # Check if roll_number exists
            check_roll_col = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='staff' AND column_name='roll_number'
            """)
            result = conn.execute(check_roll_col)
            roll_exists = result.fetchone() is not None
            
            if staff_user_id_exists:
                # Drop the index first
                try:
                    conn.execute(text("DROP INDEX IF EXISTS idx_staff_user_id"))
                except:
                    pass
                
                # Drop staff_user_id column
                conn.execute(text("""
                    ALTER TABLE staff 
                    DROP COLUMN staff_user_id
                """))
                logger.info("✓ Dropped 'staff_user_id' column from staff table")
            
            if not roll_exists:
                # Restore roll_number column
                conn.execute(text("""
                    ALTER TABLE staff 
                    ADD COLUMN roll_number VARCHAR
                """))
                logger.info("✓ Restored 'roll_number' column to staff table")
            
            conn.commit()
            logger.info("✅ Downgrade from migration 011 completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Error during downgrade: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    upgrade()
    logger.info("Migration completed successfully")
