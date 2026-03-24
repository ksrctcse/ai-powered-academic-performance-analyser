# Database Migrations

This directory contains all database migrations for the AI Academic Performance Analyzer project.

## Overview

Migrations are versioned database schema changes that can be applied and rolled back in sequence. They track the evolution of your database structure over time.

## Migration Files

### Current Migrations

| Migration | Description | Tables Affected |
|-----------|-------------|-----------------|
| `001_add_task_table_and_date_tracking.py` | Added tasks table and date tracking columns | tasks, concept_progress |
| `002_add_updated_at_to_tasks.py` | Added updated_at column to tasks table | tasks |
| `003_add_missing_task_columns.py` | Added concepts, effort_hours, complexity, dates | tasks |
| `004_initial_schema_complete.py` | **Complete initial schema for fresh deployments** | All tables |

### Migration History

The `migration_history.json` file tracks which migrations have been executed:

```json
[
  {
    "name": "001_add_task_table_and_date_tracking",
    "executed_at": "2026-03-24T10:30:00.000000",
    "direction": "up"
  }
]
```

## How to Use

### View Status
```bash
python run_migrations.py status
```

### Run All Pending Migrations
```bash
python run_migrations.py
```

### Run Specific Migration
```bash
python run_migrations.py up 004_initial_schema_complete
```

### Rollback Last Migration
```bash
python run_migrations.py rollback
```

### View Detailed Output
```bash
python run_migrations.py --verbose
```

## Migration File Structure

Each migration file should follow this pattern:

```python
"""
Migration: NNN_description.py
Description of what this migration does
"""

from sqlalchemy import text
from app.database.session import engine
from app.core.logger import get_logger

logger = get_logger(__name__)

def upgrade():
    """Apply the migration"""
    with engine.connect() as conn:
        try:
            # Upgrade code here
            conn.execute(text("SQL HERE"))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            conn.rollback()
            raise

def downgrade():
    """Rollback the migration"""
    with engine.connect() as conn:
        try:
            # Rollback code here
            conn.execute(text("SQL HERE"))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            conn.rollback()
            raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()
```

## Creating a New Migration

### Step 1: Create File
Create a new file with pattern: `NNN_brief_description.py`

Example: `005_add_student_performance_table.py`

Use the next sequential number (check existing files first).

### Step 2: Implement upgrade() and downgrade()

```python
def upgrade():
    # Write SQL to apply the change
    # - Create tables
    # - Add columns
    # - Create indexes
    # - Migrate data
    
def downgrade():
    # Write SQL to reverse the change
    # - Drop tables
    # - Remove columns
    # - Drop indexes
    # - Restore data (if needed)
```

### Step 3: Test

```bash
# Run your migration
python run_migrations.py up 005_add_student_performance_table

# Check status
python run_migrations.py status

# Test query
psql -U academic_user -d academic_analyser -c "SELECT * FROM new_table LIMIT 1;"

# Rollback if needed
python run_migrations.py rollback
```

### Step 4: Commit to Git

```bash
git add migrations/005_add_student_performance_table.py
git commit -m "Add student performance table migration"
```

## Best Practices

### DO
- ✓ Create migrations for all schema changes
- ✓ Make migrations reversible (implement downgrade)
- ✓ Add meaningful logging for debugging
- ✓ Use descriptive file names
- ✓ Test migrations before committing
- ✓ Keep migrations focused and small
- ✓ Add indexes for foreign keys and frequently queried columns
- ✓ Use transactions (wrap in conn.connect())

### DON'T
- ✗ Don't modify migrations that have already been run
- ✗ Don't skip sequential numbering
- ✗ Don't delete migration history entries
- ✗ Don't make data migrations without backups
- ✗ Don't ignore error handling
- ✗ Don't forget rollback functionality

## Common Issues

### Migration Conflicts
If two developers create conflicting migrations while offline:

1. Identify conflicting migrations
2. Rename one to use the next available number
3. Test both in sequence
4. Update git history if necessary

### Failed Migration
If a migration fails mid-execution:

1. Check the error in logs
2. Manually fix the database if needed
3. Remove failed migration from `migration_history.json`
4. Fix the migration file
5. Rerun

### Locked Tables
If a migration hangs (table locked):

1. In another terminal: `psql -U academic_user -d academic_analyser`
2. Find blocker: `SELECT * FROM pg_stat_activity WHERE state = 'active';`
3. Kill if needed: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE query LIKE '%migration%';`

## Advanced Usage

### Migrate to Specific Version
```bash
# Run only up to migration 002
python run_migrations.py up 002_add_updated_at_to_tasks
```

### Dry Run (Show SQL without executing)
Edit migration file temporarily to print SQL, run it, then revert.

### Batch Operations
```bash
# Run all AND check status
python run_migrations.py && python run_migrations.py status
```

### Database Backup Before Migration
```bash
# Always backup before major changes
pg_dump -U academic_user -d academic_analyser > /tmp/backup_pre_migration.sql

# Run migration
python run_migrations.py

# Restore if needed
psql -U academic_user -d academic_analyser < /tmp/backup_pre_migration.sql
```

## Database Schema

After all migrations run, you should have:

### Core Tables
- `staff` - User accounts
- `syllabus` - Course syllabuses
- `unit_topic_concept` - Course structure
- `concept_progress` - Student progress
- `tasks` - Learning tasks

### Legacy Tables (Compatibility)
- `department` - Departments
- `subject` - Subjects  
- `unit` - Units
- `concept` - Concepts

### All Tables Have
- Primary key (id)
- Timestamps (created_at, updated_at)
- Proper indexes for performance
- Foreign key constraints

## Troubleshooting

```bash
# Check if PostgreSQL is running
psql -U academic_user -d academic_analyser -c "SELECT 1;"

# View migration history
cat migration_history.json

# Reset migrations (DANGEROUS - deletes history)
rm migration_history.json

# Check database for locked tables
psql -U academic_user -d academic_analyser -c "SELECT * FROM pg_stat_user_tables WHERE n_live_tup > 0;"

# View active connections
psql -U academic_user -d academic_analyser -c "SELECT pid, usename, state, query FROM pg_stat_activity;"
```

## Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html)
- [Database Migration Best Practices](https://www.liquibase.org/get-started/best-practices)

## Support

For migration issues:
1. Check `backend/logs/app.log` for error messages
2. Review the migration file and SQL syntax
3. Test SQL directly in PostgreSQL
4. Check database state with `\dt` command
5. Review migration_history.json for execution order

---

**Last Updated**: March 24, 2026  
**Version**: 1.0
