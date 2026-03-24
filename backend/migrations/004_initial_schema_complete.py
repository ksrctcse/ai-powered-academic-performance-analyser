"""
Migration: 004_initial_schema_complete.py
Comprehensive initial database schema setup for fresh deployments

This migration creates all required tables for the AI Academic Performance Analyzer:
1. staff - User authentication and information
2. syllabus - Uploaded syllabus documents and analysis
3. unit_topic_concept - Hierarchical structure of course content
4. concept_progress - Student progress tracking per concept
5. tasks - Learning tasks and assignments
6. All required indexes for optimal query performance

Run this migration when setting up the project on a new system.
"""

from sqlalchemy import text
from app.database.session import engine
from app.core.logger import get_logger

logger = get_logger(__name__)


def upgrade():
    """Apply the migration - create all tables and indexes"""
    with engine.connect() as conn:
        try:
            # ========================================
            # 1. CREATE STAFF TABLE
            # ========================================
            create_staff_sql = """
            CREATE TABLE IF NOT EXISTS staff (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                email VARCHAR NOT NULL UNIQUE,
                password VARCHAR NOT NULL,
                department VARCHAR NOT NULL,
                user_type VARCHAR DEFAULT 'staff' NOT NULL,
                roll_number VARCHAR,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            conn.execute(text(create_staff_sql))
            logger.info("✓ Created 'staff' table")
            
            # Create indexes for staff table
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_staff_email ON staff(email)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_staff_created_at ON staff(created_at)"))
            logger.info("✓ Created indexes for 'staff' table")


            # ========================================
            # 2. CREATE SYLLABUS TABLE
            # ========================================
            create_syllabus_sql = """
            CREATE TABLE IF NOT EXISTS syllabus (
                id SERIAL PRIMARY KEY,
                staff_id INTEGER NOT NULL,
                filename VARCHAR NOT NULL,
                file_type VARCHAR NOT NULL,
                course_name VARCHAR,
                department VARCHAR NOT NULL,
                raw_text TEXT,
                hierarchy JSONB,
                units JSONB,
                concepts JSONB,
                analysis_result JSONB,
                analysis_summary JSONB,
                vector_store_id VARCHAR,
                vector_store_indices JSONB,
                file_size_bytes INTEGER,
                file_hash VARCHAR,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
            )
            """
            conn.execute(text(create_syllabus_sql))
            logger.info("✓ Created 'syllabus' table")
            
            # Create indexes for syllabus table
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_syllabus_staff_id ON syllabus(staff_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_syllabus_file_hash ON syllabus(file_hash)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_syllabus_uploaded_at ON syllabus(uploaded_at)"))
            logger.info("✓ Created indexes for 'syllabus' table")


            # ========================================
            # 3. CREATE UNIT_TOPIC_CONCEPT TABLE
            # ========================================
            create_utc_sql = """
            CREATE TABLE IF NOT EXISTS unit_topic_concept (
                id SERIAL PRIMARY KEY,
                syllabus_id INTEGER NOT NULL,
                unit_id VARCHAR NOT NULL,
                unit_name VARCHAR NOT NULL,
                topic_id VARCHAR NOT NULL,
                topic_name VARCHAR NOT NULL,
                concept_name VARCHAR NOT NULL,
                complexity_level VARCHAR DEFAULT 'MEDIUM',
                description VARCHAR,
                learning_objectives JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (syllabus_id) REFERENCES syllabus(id) ON DELETE CASCADE
            )
            """
            conn.execute(text(create_utc_sql))
            logger.info("✓ Created 'unit_topic_concept' table")
            
            # Create indexes for unit_topic_concept table
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_utc_syllabus_id ON unit_topic_concept(syllabus_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_utc_unit_id ON unit_topic_concept(unit_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_utc_topic_id ON unit_topic_concept(topic_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_utc_created_at ON unit_topic_concept(created_at)"))
            logger.info("✓ Created indexes for 'unit_topic_concept' table")


            # ========================================
            # 4. CREATE CONCEPT_PROGRESS TABLE
            # ========================================
            create_concept_progress_sql = """
            CREATE TABLE IF NOT EXISTS concept_progress (
                id SERIAL PRIMARY KEY,
                staff_id INTEGER NOT NULL,
                concept_id INTEGER,
                unit_topic_concept_id INTEGER,
                completion_percentage INTEGER DEFAULT 0,
                status VARCHAR DEFAULT 'Not Started',
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE,
                FOREIGN KEY (unit_topic_concept_id) REFERENCES unit_topic_concept(id) ON DELETE CASCADE
            )
            """
            conn.execute(text(create_concept_progress_sql))
            logger.info("✓ Created 'concept_progress' table")
            
            # Create indexes for concept_progress table
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_concept_progress_staff_id ON concept_progress(staff_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_concept_progress_unit_topic_concept_id ON concept_progress(unit_topic_concept_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_concept_progress_created_at ON concept_progress(created_at)"))
            logger.info("✓ Created indexes for 'concept_progress' table")


            # ========================================
            # 5. CREATE TASKS TABLE
            # ========================================
            create_tasks_sql = """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                staff_id INTEGER NOT NULL,
                concept_progress_id INTEGER,
                title VARCHAR NOT NULL,
                description TEXT,
                task_type VARCHAR DEFAULT 'ASSIGNMENT',
                content JSONB,
                concepts JSONB,
                covered_topics JSONB,
                effort_hours FLOAT,
                average_complexity VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                due_date TIMESTAMP,
                completed_at TIMESTAMP,
                status VARCHAR DEFAULT 'PENDING',
                completion_percentage INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE,
                FOREIGN KEY (concept_progress_id) REFERENCES concept_progress(id) ON DELETE CASCADE
            )
            """
            conn.execute(text(create_tasks_sql))
            logger.info("✓ Created 'tasks' table")
            
            # Create indexes for tasks table
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_staff_id ON tasks(staff_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_concept_progress_id ON tasks(concept_progress_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)"))
            logger.info("✓ Created indexes for 'tasks' table")


            # ========================================
            # 6. CREATE LEGACY TABLES (if needed)
            # ========================================
            # Department table (legacy, but kept for compatibility)
            create_department_sql = """
            CREATE TABLE IF NOT EXISTS department (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            conn.execute(text(create_department_sql))
            logger.info("✓ Created 'department' table")


            # Subject table (legacy, but kept for compatibility)
            create_subject_sql = """
            CREATE TABLE IF NOT EXISTS subject (
                id SERIAL PRIMARY KEY,
                department_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                code VARCHAR,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE CASCADE
            )
            """
            conn.execute(text(create_subject_sql))
            logger.info("✓ Created 'subject' table")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_subject_department_id ON subject(department_id)"))


            # Unit table (legacy, but kept for compatibility)
            create_unit_sql = """
            CREATE TABLE IF NOT EXISTS unit (
                id SERIAL PRIMARY KEY,
                subject_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                description TEXT,
                unit_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE
            )
            """
            conn.execute(text(create_unit_sql))
            logger.info("✓ Created 'unit' table")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_unit_subject_id ON unit(subject_id)"))


            # Concept table (legacy, but kept for compatibility)
            create_concept_sql = """
            CREATE TABLE IF NOT EXISTS concept (
                id SERIAL PRIMARY KEY,
                unit_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                description TEXT,
                difficulty_level VARCHAR,
                resources JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (unit_id) REFERENCES unit(id) ON DELETE CASCADE
            )
            """
            conn.execute(text(create_concept_sql))
            logger.info("✓ Created 'concept' table")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_concept_unit_id ON concept(unit_id)"))


            # ========================================
            # 7. ENABLE REQUIRED EXTENSIONS
            # ========================================
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
                logger.info("✓ Enabled 'uuid-ossp' extension")
            except Exception as e:
                logger.warning(f"Could not enable uuid-ossp extension: {str(e)}")

            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\""))
                logger.info("✓ Enabled 'pg_trgm' extension (for full-text search)")
            except Exception as e:
                logger.warning(f"Could not enable pg_trgm extension: {str(e)}")


            # Commit all changes
            conn.commit()
            logger.info("\n✓ Migration 004 completed successfully!")
            logger.info("✓ All tables and indexes created")
            return True

        except Exception as e:
            logger.error(f"✗ Error applying migration 004: {str(e)}", exc_info=True)
            conn.rollback()
            raise


def downgrade():
    """Rollback the migration - drop all tables (use with caution)"""
    with engine.connect() as conn:
        try:
            # Drop in reverse order of creation (respecting foreign keys)
            tables_to_drop = [
                'tasks',
                'concept_progress',
                'unit_topic_concept',
                'syllabus',
                'concept',
                'unit',
                'subject',
                'department',
                'staff'
            ]
            
            for table in tables_to_drop:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                logger.info(f"✓ Dropped '{table}' table")
            
            conn.commit()
            logger.info("\n✓ Migration 004 rolled back successfully!")
            return True

        except Exception as e:
            logger.error(f"✗ Error rolling back migration 004: {str(e)}", exc_info=True)
            conn.rollback()
            raise


if __name__ == "__main__":
    """Allow running migration directly: python migrations/004_initial_schema_complete.py"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        print("Rolling back migration 004...")
        downgrade()
    else:
        print("Applying migration 004...")
        upgrade()
