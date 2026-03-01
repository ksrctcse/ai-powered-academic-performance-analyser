"""
Migration: 002_add_updated_at_to_tasks.py
This migration adds the updated_at timestamp column to the tasks table
"""

from sqlalchemy import text
from app.database.session import SessionLocal, engine

def upgrade():
    """Apply the migration"""
    with engine.connect() as conn:
        try:
            # Check if updated_at column exists
            check_columns = """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'tasks' AND column_name = 'updated_at'
            """
            result = conn.execute(text(check_columns))
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                # Add updated_at column
                conn.execute(text("""
                    ALTER TABLE tasks ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """))
                print("✓ Added 'updated_at' column to tasks table")
            else:
                print("✓ 'updated_at' column already exists in tasks table")
            
            # Create index for updated_at
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at)"))
                print("✓ Created index for updated_at column")
            except Exception as e:
                print(f"⚠ Index already exists or creation failed: {str(e)}")
            
            conn.commit()
            print("✅ Migration 002 completed successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Migration 002 failed: {str(e)}")
            raise

def downgrade():
    """Rollback the migration"""
    with engine.connect() as conn:
        try:
            # Drop the index
            try:
                conn.execute(text("DROP INDEX IF EXISTS idx_tasks_updated_at"))
                print("✓ Dropped index idx_tasks_updated_at")
            except:
                pass
            
            # Drop the column
            conn.execute(text("""
                ALTER TABLE tasks DROP COLUMN IF EXISTS updated_at
            """))
            print("✓ Dropped 'updated_at' column from tasks table")
            
            conn.commit()
            print("✅ Downgrade from migration 002 completed successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Downgrade failed: {str(e)}")
            raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()
