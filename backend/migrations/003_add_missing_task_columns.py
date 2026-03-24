"""
Migration: 003_add_missing_task_columns.py
This migration:
1. Adds missing columns to the 'tasks' table that are defined in the Task model
2. Columns: concepts, effort_hours, average_complexity, covered_topics, start_date, end_date, updated_at
3. Makes concept_progress_id nullable (since tasks can be created without concept_progress)
"""

from sqlalchemy import text
from app.database.session import SessionLocal, engine

def upgrade():
    """Apply the migration"""
    with engine.connect() as conn:
        try:
            # Check current columns in tasks table
            check_columns = """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'tasks'
            """
            result = conn.execute(text(check_columns))
            existing_columns = [row[0] for row in result.fetchall()]
            
            # Add missing columns
            if 'concepts' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE tasks ADD COLUMN concepts JSONB NULL
                """))
                print("✓ Added 'concepts' column to tasks table")
            
            if 'covered_topics' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE tasks ADD COLUMN covered_topics JSONB NULL
                """))
                print("✓ Added 'covered_topics' column to tasks table")
            
            if 'effort_hours' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE tasks ADD COLUMN effort_hours FLOAT NULL
                """))
                print("✓ Added 'effort_hours' column to tasks table")
            
            if 'average_complexity' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE tasks ADD COLUMN average_complexity VARCHAR NULL
                """))
                print("✓ Added 'average_complexity' column to tasks table")
            
            if 'start_date' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE tasks ADD COLUMN start_date TIMESTAMP NULL
                """))
                print("✓ Added 'start_date' column to tasks table")
            
            if 'end_date' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE tasks ADD COLUMN end_date TIMESTAMP NULL
                """))
                print("✓ Added 'end_date' column to tasks table")
            
            if 'updated_at' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE tasks ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """))
                print("✓ Added 'updated_at' column to tasks table")
            
            # Make concept_progress_id nullable
            try:
                conn.execute(text("""
                    ALTER TABLE tasks ALTER COLUMN concept_progress_id DROP NOT NULL
                """))
                print("✓ Made 'concept_progress_id' nullable in tasks table")
            except:
                print("  (concept_progress_id already nullable)")
            
            conn.commit()
            print("\n✓ Migration 003 completed successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Migration 003 failed: {str(e)}")
            raise

def downgrade():
    """Revert the migration"""
    with engine.connect() as conn:
        try:
            columns_to_drop = [
                'concepts', 'covered_topics', 'effort_hours', 
                'average_complexity', 'start_date', 'end_date', 'updated_at'
            ]
            
            for column in columns_to_drop:
                try:
                    conn.execute(text(f"ALTER TABLE tasks DROP COLUMN {column}"))
                    print(f"✓ Dropped '{column}' column from tasks table")
                except:
                    pass
            
            conn.commit()
            print("\n✓ Migration 003 reverted successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Reverting migration 003 failed: {str(e)}")
            raise

if __name__ == "__main__":
    upgrade()
