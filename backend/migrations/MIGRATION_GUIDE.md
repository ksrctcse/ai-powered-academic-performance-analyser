# Database Migration System

## Overview

This database migration system provides a robust way to manage all database schema changes for the AI Academic Performance Analyzer application.

## Features

✅ **Automatic Migration Detection** - Discovers all migration files automatically
✅ **Migration Status Tracking** - Tracks which migrations have been applied
✅ **Rollback Support** - Ability to rollback migrations
✅ **Schema Validation** - Validates database schema after migrations
✅ **Detailed Reporting** - Comprehensive status and schema reports
✅ **Error Handling** - Graceful error handling with detailed error messages
✅ **Dependency Management** - Runs migrations in order

## Usage

### 1. List All Migrations
```bash
cd backend
python run_migrations.py list
```

Shows all available migrations with their status (APPLIED or PENDING).

### 2. Apply All Pending Migrations
```bash
cd backend
python run_migrations.py up
```

Applies all migrations that haven't been applied yet.

### 3. Apply Migrations Up to a Specific Version
```bash
cd backend
python run_migrations.py up 005_add_department_selection_support
```

Applies all migrations up to (and including) the specified migration.

### 4. Rollback the Last Migration
```bash
cd backend
python run_migrations.py down
```

Rolls back the most recently applied migration.

### 5. Reset All Migrations
```bash
cd backend
python run_migrations.py reset
```

Rolls back ALL migrations and then re-applies them all. Use with caution!

### 6. Show Detailed Schema Information
```bash
cd backend
python run_migrations.py schema
```

Displays all tables and their columns with data types.

### 7. Validate Database Schema
```bash
cd backend
python run_migrations.py validate
```

Validates that:
- Database connection works
- All required tables exist
- All required columns exist
- Recommended indexes are present

### 8. View Complete Status Report
```bash
cd backend
python run_migrations.py status
```

Shows migration status + full schema validation report.

## Current Database Schema

### Tables Created by Migrations

| Table | Description | Key Columns |
|-------|-------------|------------|
| `staff` | User accounts (teachers/students) | id, email, password, user_type |
| `syllabus` | Course syllabuses | id, staff_id, hierarchy, raw_text |
| `unit_topic_concept` | Hierarchical course structure | id, unit_id, topic_id, concept_id |
| `concept_progress` | Student progress on concepts | id, staff_id, concept_id, progress_percentage |
| `tasks` | Learning tasks/assignments | id, staff_id, unit_id, topic_id, concept_ids, status |

### Key Columns Added by Recent Migrations

**Tasks Table:**
- `unit_id` - Direct reference to unit (indexed)
- `unit_name` - Unit name for display
- `topic_id` - Direct reference to topic (indexed)
- `topic_name` - Topic name for display
- `concept_ids` - Comma-separated concept IDs
- `learning_task_progress` - JSON array tracking individual task progress
- `effort_hours` - Estimated learning hours
- `average_complexity` - Complexity level (LOW/MEDIUM/HIGH)

## Migration Files

### Existing Migrations

1. **001_add_task_table_and_date_tracking**
   - Creates tasks table
   - Adds date tracking to concept_progress

2. **002_add_updated_at_to_tasks**
   - Adds updated_at timestamp to tasks

3. **003_add_missing_task_columns**
   - Adds various task-related columns

4. **004_initial_schema_complete**
   - Completes initial schema setup

5. **005_add_department_selection_support**
   - Adds department field to tasks

6. **006_update_existing_syllabus_department**
   - Updates existing data for department field

7. **007_add_department_to_tasks**
   - Ensures department column in tasks

8. **008_add_cascade_delete_to_unit_topic_concept**
   - Adds cascade delete on foreign keys

9. **009_add_syllabus_id_to_tasks**
   - Links tasks to syllabuses

10. **010_add_learning_task_progress**
    - Adds JSON column for fine-grained task progress

### Creating New Migrations

To create a new migration:

1. Create a file: `migrations/01X_description.py`
2. Include `upgrade()` function for applying changes
3. Include `downgrade()` function for rollback (optional)
4. Use SQLAlchemy's `text()` for SQL operations

**Template:**
```python
"""
Migration: 01X_your_migration_description.py
Description: What this migration does
"""

from sqlalchemy import text
from app.database.session import SessionLocal, engine
import logging

logger = logging.getLogger(__name__)

def upgrade():
    """Apply the migration"""
    db = SessionLocal()
    try:
        with engine.connect() as conn:
            # Your migration code here
            conn.execute(text("ALTER TABLE tasks ADD COLUMN new_column VARCHAR"))
            conn.commit()
            logger.info("✓ Migration applied successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise
    finally:
        db.close()

def downgrade():
    """Rollback the migration (optional)"""
    db = SessionLocal()
    try:
        with engine.connect() as conn:
            # Rollback code here
            conn.execute(text("ALTER TABLE tasks DROP COLUMN new_column"))
            conn.commit()
            logger.info("✓ Migration rolled back")
    except Exception as e:
        logger.error(f"Rollback failed: {e}", exc_info=True)
        raise
    finally:
        db.close()
```

## Migration Status File

The system tracks applied migrations in `.migrations_applied.json`:

```json
[
  "001_add_task_table_and_date_tracking",
  "002_add_updated_at_to_tasks",
  "003_add_missing_task_columns",
  ...
]
```

**WARNING:** Don't edit this file manually! Use the migration runner.

## Best Practices

### Before Running Migrations

1. **Backup Database**
   ```bash
   pg_dump academic_analyser > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Verify Connection**
   ```bash
   python run_migrations.py validate
   ```

3. **Check Pending Migrations**
   ```bash
   python run_migrations.py list
   ```

### During Development

1. Always test migrations locally first
2. Keep downgrade() functions up-to-date
3. Document schema changes in docstrings

### Before Deployment

1. Run migrations on staging environment
2. Verify with `python run_migrations.py validate`
3. Take production database backup
4. Run migrations with `python run_migrations.py up`

## Troubleshooting

### Connection Issues
```bash
# Verify database connection
python run_migrations.py validate
```

**Check:**
- DATABASE_URL in .env is correct
- PostgreSQL service is running
- Credentials are correct

### Migration Failed
```bash
# Rollback last migration
python run_migrations.py down

# Then investigate the error in logs
tail -f logs/app.log
```

### Schema Validation Errors
```bash
# Check current schema
python run_migrations.py schema

# Validate against required schema
python run_migrations.py validate

# Get detailed status
python run_migrations.py status
```

### Missing Migrations

If you see "PENDING" migrations that should be applied:

```bash
# Apply all pending migrations
python run_migrations.py up

# Verify they were applied
python run_migrations.py list
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run database migrations
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: |
    cd backend
    python run_migrations.py up
    python run_migrations.py validate
```

### GitLab CI Example

```yaml
migrations:
  script:
    - cd backend
    - python run_migrations.py up
    - python run_migrations.py validate
  variables:
    DATABASE_URL: $DATABASE_URL
```

## Environment Variables

Required for migrations to work:

```
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/academic_analyser
```

## Common Commands

```bash
# Fresh setup (create all tables)
cd backend
python setup_db.py

# Apply pending migrations
python run_migrations.py up

# Validate everything is correct
python run_migrations.py validate

# View detailed schema
python run_migrations.py schema

# Get complete status report
python run_migrations.py status

# Rollback and reapply (careful!)
python run_migrations.py reset
```

## Summary

The migration system provides:
✅ Automatic management of database schema changes
✅ Version control for database changes
✅ Rollback capabilities
✅ Schema validation and reporting
✅ Integration with CI/CD pipelines
✅ Clear documentation of all changes

Use `python run_migrations.py` to start!
