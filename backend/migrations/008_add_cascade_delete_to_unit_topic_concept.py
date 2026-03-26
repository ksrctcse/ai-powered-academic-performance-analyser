"""
Migration: 008_add_cascade_delete_to_unit_topic_concept.py
Adds ON DELETE CASCADE to the foreign key constraint between 
unit_topic_concept and syllabus to allow proper deletion
"""

from sqlalchemy import text
from app.database.session import engine
from app.core.logger import get_logger

logger = get_logger(__name__)

def upgrade():
    """Apply the migration"""
    with engine.connect() as conn:
        try:
            # Drop existing foreign key constraint
            # First, we need to find the constraint name
            conn.execute(text("""
                ALTER TABLE IF EXISTS unit_topic_concept 
                DROP CONSTRAINT IF EXISTS unit_topic_concept_syllabus_id_fkey
            """))
            logger.info("✓ Dropped old foreign key constraint from unit_topic_concept")
            
            # Add new foreign key with cascade delete
            conn.execute(text("""
                ALTER TABLE unit_topic_concept
                ADD CONSTRAINT unit_topic_concept_syllabus_id_fkey
                FOREIGN KEY (syllabus_id) REFERENCES syllabus(id) ON DELETE CASCADE
            """))
            logger.info("✓ Added new foreign key constraint with ON DELETE CASCADE")
            
            conn.commit()
            logger.info("✓ Migration 008 completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error applying migration 008: {str(e)}", exc_info=True)
            conn.rollback()
            raise


def downgrade():
    """Rollback the migration"""
    with engine.connect() as conn:
        try:
            # Drop the cascade foreign key
            conn.execute(text("""
                ALTER TABLE IF EXISTS unit_topic_concept 
                DROP CONSTRAINT IF EXISTS unit_topic_concept_syllabus_id_fkey
            """))
            logger.info("✓ Dropped foreign key constraint")
            
            # Add back without cascade
            conn.execute(text("""
                ALTER TABLE unit_topic_concept
                ADD CONSTRAINT unit_topic_concept_syllabus_id_fkey
                FOREIGN KEY (syllabus_id) REFERENCES syllabus(id)
            """))
            logger.info("✓ Restored foreign key constraint without cascade")
            
            conn.commit()
            logger.info("✓ Migration 008 rolled back successfully!")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error rolling back migration 008: {str(e)}", exc_info=True)
            conn.rollback()
            raise


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()
