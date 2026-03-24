#!/usr/bin/env python
import sys
sys.path.insert(0, '/Users/arunkumaraswamy/Documents/Study/ai-powered-academic-performance-analyser/backend')

from sqlalchemy import text
from app.database.session import engine

def add_missing_task_columns():
    """Add missing columns to the tasks table"""
    with engine.connect() as conn:
        try:
            # Check current columns in tasks table
            check_columns = """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'tasks'
            """
            result = conn.execute(text(check_columns))
            existing_columns = [row[0] for row in result.fetchall()]
            
            print(f"Existing columns in tasks table: {existing_columns}\n")
            
            # Add missing columns
            columns_to_add = {
                'concepts': "JSONB NULL",
                'covered_topics': "JSONB NULL",
                'effort_hours': "FLOAT NULL",
                'average_complexity': "VARCHAR NULL",
                'start_date': "TIMESTAMP NULL",
                'end_date': "TIMESTAMP NULL",
                'updated_at': "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
            
            for column_name, column_type in columns_to_add.items():
                if column_name not in existing_columns:
                    sql = f"ALTER TABLE tasks ADD COLUMN {column_name} {column_type}"
                    conn.execute(text(sql))
                    print(f"✓ Added '{column_name}' column to tasks table")
                else:
                    print(f"  '{column_name}' already exists")
            
            # Make concept_progress_id nullable
            try:
                conn.execute(text("""
                    ALTER TABLE tasks ALTER COLUMN concept_progress_id DROP NOT NULL
                """))
                print("\n✓ Made 'concept_progress_id' nullable in tasks table")
            except Exception as e:
                print(f"\n  'concept_progress_id' nullable update: {str(e)}")
            
            conn.commit()
            print("\n✓ Migration completed successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    add_missing_task_columns()
