# Database Migration & Deployment Guide

## Overview

This document explains how to set up the AI Academic Performance Analyzer database on any new system. The project uses **PostgreSQL** with **SQLAlchemy ORM** and a **migration system** for version control.

---

## Prerequisites

### System Requirements
- **Python 3.8+**
- **PostgreSQL 12+** (installed and running)
- **Git** (for cloning the repository)

### Installation

#### macOS
```bash
# Install PostgreSQL using Homebrew
brew install postgresql@15
brew services start postgresql@15

# Verify installation
psql --version
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Verify installation
psql --version
```

#### Windows
1. Download PostgreSQL installer from https://www.postgresql.org/download/windows/
2. Run installer and remember the superuser password
3. PostgreSQL should start automatically

---

## Project Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd ai-powered-academic-performance-analyser
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/academic_analyser

# Server Configuration
SECRET_KEY=your-secret-key-here-at-least-32-characters-long
GOOGLE_API_KEY=your-google-generative-ai-key

# Optional
DEBUG=False
LOG_LEVEL=INFO
```

**Important**: Replace `your_password` with your PostgreSQL superuser password.

### 5. Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# In psql terminal:
CREATE DATABASE academic_analyser;
CREATE USER academic_user WITH PASSWORD 'your_password';
ALTER ROLE academic_user SET client_encoding TO 'utf8';
ALTER ROLE academic_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE academic_user SET default_transaction_deferrable TO on;
ALTER ROLE academic_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE academic_analyser TO academic_user;
\q

# Verify database created
psql -U postgres -l | grep academic_analyser
```

---

## Database Migration

### Automatic Setup (Recommended for First Run)

```bash
# Run from project root directory
cd backend
python setup_db.py
```

This will:
- Create all required database tables
- Set up all indexes
- Initialize the schema

### Migration System (For Tracked Changes)

The project includes a comprehensive migration system for version control.

#### View Migration Status
```bash
cd ..  # Back to project root
python run_migrations.py status
```

Output:
```
============================================================
MIGRATION STATUS
============================================================

Total migrations: 4
Executed: 0
Pending: 4

Pending Migrations:
  ○ 001_add_task_table_and_date_tracking
  ○ 002_add_updated_at_to_tasks
  ○ 003_add_missing_task_columns
  ○ 004_initial_schema_complete
```

#### Run All Pending Migrations
```bash
python run_migrations.py
# or
python run_migrations.py up --verbose
```

#### Run Specific Migration
```bash
python run_migrations.py up 004_initial_schema_complete
```

#### Rollback Last Migration
```bash
python run_migrations.py rollback
```

#### Check Detailed Status
```bash
python run_migrations.py status
```

---

## Database Schema

### Tables Overview

#### 1. **staff** - User Authentication
- Stores user accounts (staff and students)
- Fields: id, name, email, password, department, user_type, roll_number, is_active, timestamps

#### 2. **syllabus** - Syllabus Documents
- Uploaded course syllabuses and analysis results
- Fields: id, staff_id, filename, file_type, course_name, hierarchy (JSON), analysis_summary, timestamps

#### 3. **unit_topic_concept** - Course Structure
- Hierarchical breakdown: Unit → Topic → Concept
- Fields: id, syllabus_id, unit_id, unit_name, topic_id, topic_name, concept_name, complexity_level, timestamps

#### 4. **concept_progress** - Student Progress
- Tracks student progress on each concept
- Fields: id, staff_id, unit_topic_concept_id, completion_percentage, status, start_date, end_date, timestamps

#### 5. **tasks** - Learning Tasks
- Generated tasks and assignments
- Fields: id, staff_id, concept_progress_id, title, description, task_type, status, effort_hours, timestamps, dates

#### 6. Legacy Tables (for compatibility)
- **department** - Course departments
- **subject** - Course subjects
- **unit** - Course units
- **concept** - Learning concepts

### Database Indexes

Automatically created for optimal query performance:
- Staff: email, created_at
- Syllabus: staff_id, file_hash, uploaded_at
- Unit Topic Concept: syllabus_id, unit_id, topic_id
- Concept Progress: staff_id, unit_topic_concept_id, created_at
- Tasks: staff_id, concept_progress_id, status, created_at

---

## Verification

### 1. Test PostgreSQL Connection
```bash
psql -U academic_user -d academic_analyser -c "SELECT version();"
```

Expected output: PostgreSQL version information

### 2. Check Database Tables
```bash
psql -U academic_user -d academic_analyser -c "\dt"
```

Expected output: List of all created tables

### 3. Test Backend Connection
```bash
cd backend
python -c "from app.database import init_db; init_db(); print('✓ Database connected successfully')"
```

### 4. Start Backend Server
```bash
cd backend
uvicorn app.main:app --reload
```

Open browser to: http://localhost:8000/docs
- Should show Swagger UI with all API endpoints
- Health check: GET /health

### 5. Start Frontend Development Server
```bash
cd frontend
npm install
npm run dev
```

Open browser to: http://localhost:5173
- Should load the React application

---

## Making Migrations

### When to Create a Migration

Create a new migration when you:
1. Add new database tables
2. Add columns to existing tables
3. Create or modify indexes
4. Rename tables or columns
5. Change column constraints

### How to Create a Migration

#### 1. Create Migration File

In `backend/migrations/`, create a new file with pattern: `NNN_description.py`

Example: `005_add_performance_metrics_table.py`

```python
"""
Migration: 005_add_performance_metrics_table.py
Adds a new performance_metrics table for tracking student performance
"""

from sqlalchemy import text
from app.database.session import engine
from app.core.logger import get_logger

logger = get_logger(__name__)

def upgrade():
    """Apply the migration"""
    with engine.connect() as conn:
        try:
            # Create new table
            create_sql = """
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id SERIAL PRIMARY KEY,
                staff_id INTEGER NOT NULL,
                unit_topic_concept_id INTEGER NOT NULL,
                score FLOAT,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE,
                FOREIGN KEY (unit_topic_concept_id) REFERENCES unit_topic_concept(id) ON DELETE CASCADE
            )
            """
            conn.execute(text(create_sql))
            logger.info("✓ Created 'performance_metrics' table")
            
            # Create indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_perf_staff_id 
                ON performance_metrics(staff_id)
            """))
            logger.info("✓ Created indexes for 'performance_metrics' table")
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"✗ Error: {str(e)}", exc_info=True)
            conn.rollback()
            raise

def downgrade():
    """Rollback the migration"""
    with engine.connect() as conn:
        try:
            conn.execute(text("DROP TABLE IF EXISTS performance_metrics CASCADE"))
            logger.info("✓ Dropped 'performance_metrics' table")
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"✗ Error: {str(e)}", exc_info=True)
            conn.rollback()
            raise
```

#### 2. Run Migration
```bash
python run_migrations.py up 005_add_performance_metrics_table
```

#### 3. Verify
```bash
python run_migrations.py status
```

---

## Backup & Restore

### Backup Database
```bash
# Full backup
pg_dump -U academic_user -d academic_analyser > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
pg_dump -U academic_user -d academic_analyser | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore Database
```bash
# Restore from SQL file
psql -U academic_user -d academic_analyser < backup_20260324_120000.sql

# Restore from compressed file
gunzip -c backup_20260324_120000.sql.gz | psql -U academic_user -d academic_analyser
```

---

## Troubleshooting

### Connection Refused
```bash
# Check if PostgreSQL is running
# macOS:
brew services list | grep postgresql

# Linux:
sudo systemctl status postgresql

# Start if not running:
# macOS:
brew services start postgresql@15

# Linux:
sudo systemctl start postgresql
```

### Permission Denied
```bash
# Check user permissions
psql -U postgres -d academic_analyser -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO academic_user;"
psql -U postgres -d academic_analyser -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO academic_user;"
```

### Migration Conflicts
```bash
# Check migration history
cat backend/migrations/migration_history.json

# Remove last migration from history (if failed)
# Edit backend/migrations/migration_history.json manually
```

### Database Already Exists
```bash
# Drop database and recreate
psql -U postgres -c "DROP DATABASE IF EXISTS academic_analyser;"
# Then follow setup steps again
```

---

## Environment-Specific Configurations

### Development
```bash
DATABASE_URL=postgresql://academic_user:password@localhost:5432/academic_analyser_dev
DEBUG=True
LOG_LEVEL=DEBUG
```

### Testing
```bash
DATABASE_URL=postgresql://academic_user:password@localhost:5432/academic_analyser_test
DEBUG=False
LOG_LEVEL=INFO
```

### Production
```bash
DATABASE_URL=postgresql://academic_user:secure_password@prod-db-host:5432/academic_analyser
DEBUG=False
LOG_LEVEL=WARNING
SECRET_KEY=<very-long-random-key>
```

---

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

---

## Getting Help

If you encounter issues:

1. Check the logs: `tail -f backend/logs/app.log`
2. Run health check: `curl http://localhost:8000/health`
3. Verify database: `python run_migrations.py status`
4. Check migration history: `cat backend/migrations/migration_history.json`

---

Last Updated: March 24, 2026
