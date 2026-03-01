"""
Migration: 001_add_task_table_and_date_tracking.py
This migration:
1. Creates the 'tasks' table with task management fields
2. Adds start_date and end_date columns to concept_progress table
3. Adds unit_topic_concept_id foreign key to concept_progress
"""

from sqlalchemy import text
from app.database.session import SessionLocal, engine

def upgrade():
    """Apply the migration"""
    with engine.connect() as conn:
        try:
            # Create tasks table (PostgreSQL)
            create_tasks_sql = """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                staff_id INTEGER NOT NULL,
                concept_progress_id INTEGER NOT NULL,
                title VARCHAR NOT NULL,
                description TEXT,
                task_type VARCHAR DEFAULT 'ASSIGNMENT' NOT NULL,
                content JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                due_date TIMESTAMP,
                completed_at TIMESTAMP,
                status VARCHAR DEFAULT 'PENDING' NOT NULL,
                completion_percentage INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE,
                FOREIGN KEY (concept_progress_id) REFERENCES concept_progress(id) ON DELETE CASCADE
            )
            """
            conn.execute(text(create_tasks_sql))
            print("✓ Created 'tasks' table")
            
            # Create indexes for tasks table
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_staff_id ON tasks(staff_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_concept_progress_id ON tasks(concept_progress_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)"))
                print("✓ Created indexes for tasks table")
            except Exception as e:
                logger.warning(f"Failed to create indexes (might already exist): {str(e)}")
            
            # Check if start_date column exists in concept_progress
            check_columns = """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'concept_progress'
            """
            result = conn.execute(text(check_columns))
            columns = [row[0] for row in result.fetchall()]
            
            # Add start_date if not exists
            if 'start_date' not in columns:
                conn.execute(text("""
                    ALTER TABLE concept_progress ADD COLUMN start_date TIMESTAMP NULL
                """))
                print("✓ Added 'start_date' column to concept_progress table")
            
            # Add end_date if not exists
            if 'end_date' not in columns:
                conn.execute(text("""
                    ALTER TABLE concept_progress ADD COLUMN end_date TIMESTAMP NULL
                """))
                print("✓ Added 'end_date' column to concept_progress table")
            
            # Add created_at if not exists
            if 'created_at' not in columns:
                conn.execute(text("""
                    ALTER TABLE concept_progress ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """))
                print("✓ Added 'created_at' column to concept_progress table")
            
            # Add unit_topic_concept_id if not exists
            if 'unit_topic_concept_id' not in columns:
                conn.execute(text("""
                    ALTER TABLE concept_progress ADD COLUMN unit_topic_concept_id INTEGER NULL
                """))
                
                try:
                    conn.execute(text("""
                        ALTER TABLE concept_progress 
                        ADD CONSTRAINT fk_concept_progress_utc 
                        FOREIGN KEY (unit_topic_concept_id) REFERENCES unit_topic_concept(id) ON DELETE CASCADE
                    """))
                except:
                    # Foreign key might already exist
                    pass
                
                print("✓ Added 'unit_topic_concept_id' column to concept_progress table")
            
            # Add indexes for better query performance
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cp_staff_id ON concept_progress(staff_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cp_concept_id ON concept_progress(concept_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cp_unit_topic_concept_id ON concept_progress(unit_topic_concept_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cp_start_date ON concept_progress(start_date)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cp_end_date ON concept_progress(end_date)"))
                print("✓ Created indexes for concept_progress table")
            except Exception as e:
                print(f"⚠ Some indexes may already exist: {str(e)}")
            
            conn.commit()
            print("\n✅ Migration 001 completed successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Error during migration: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


def downgrade():
    """Revert the migration"""
    with engine.connect() as conn:
        try:
            conn.execute(text("DROP TABLE IF EXISTS tasks CASCADE"))
            print("✓ Dropped 'tasks' table")
            
            # Note: PostgreSQL doesn't easily allow dropping columns
            # To completely revert, you would need to recreate the table
            print("⚠ Note: To completely revert, you may need to manually remove start_date, end_date, and unit_topic_concept_id columns from concept_progress")
            
            conn.commit()
            print("✓ Migration 001 downgrade completed!")
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Error during downgrade: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()
