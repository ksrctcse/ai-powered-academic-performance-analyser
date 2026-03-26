"""
Migration 003: Add unit_id, topic_id, and concept_ids columns to tasks table

This migration adds direct columns for unit_id, unit_name, topic_id, topic_name, 
and concept_ids to the tasks table for efficient querying without JSON parsing.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from app.database.session import engine


def upgrade():
    """Add new columns to tasks table"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('tasks')]
        
        with engine.begin() as connection:
            if 'unit_id' not in columns:
                connection.execute(text(
                    'ALTER TABLE tasks ADD COLUMN unit_id INTEGER'
                ))
                connection.execute(text(
                    'CREATE INDEX ix_tasks_unit_id ON tasks(unit_id)'
                ))
                print("✓ Added unit_id column to tasks table")
            
            if 'unit_name' not in columns:
                connection.execute(text(
                    'ALTER TABLE tasks ADD COLUMN unit_name VARCHAR'
                ))
                print("✓ Added unit_name column to tasks table")
            
            if 'topic_id' not in columns:
                connection.execute(text(
                    'ALTER TABLE tasks ADD COLUMN topic_id INTEGER'
                ))
                connection.execute(text(
                    'CREATE INDEX ix_tasks_topic_id ON tasks(topic_id)'
                ))
                print("✓ Added topic_id column to tasks table")
            
            if 'topic_name' not in columns:
                connection.execute(text(
                    'ALTER TABLE tasks ADD COLUMN topic_name VARCHAR'
                ))
                print("✓ Added topic_name column to tasks table")
            
            if 'concept_ids' not in columns:
                connection.execute(text(
                    'ALTER TABLE tasks ADD COLUMN concept_ids VARCHAR'
                ))
                print("✓ Added concept_ids column to tasks table")
        
        print("Migration 003 complete!")
        return True
        
    except Exception as e:
        print(f"Error running migration: {str(e)}")
        return False


def downgrade():
    """Remove the added columns from tasks table"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('tasks')]
        
        with engine.begin() as connection:
            # Drop columns if they exist (order matters for dependencies)
            if 'concept_ids' in columns:
                connection.execute(text('ALTER TABLE tasks DROP COLUMN concept_ids'))
            if 'topic_name' in columns:
                connection.execute(text('ALTER TABLE tasks DROP COLUMN topic_name'))
            if 'topic_id' in columns:
                connection.execute(text('ALTER TABLE tasks DROP COLUMN topic_id'))
            if 'unit_name' in columns:
                connection.execute(text('ALTER TABLE tasks DROP COLUMN unit_name'))
            if 'unit_id' in columns:
                connection.execute(text('ALTER TABLE tasks DROP COLUMN unit_id'))
        
        print("Migration 003 downgraded successfully!")
        return True
        
    except Exception as e:
        print(f"Error downgrading migration: {str(e)}")
        return False


if __name__ == "__main__":
    print("Running migration 003...")
    success = upgrade()
    sys.exit(0 if success else 1)
