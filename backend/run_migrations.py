#!/usr/bin/env python
"""
Migration Runner Script - Enhanced Version
Runs database migrations in order to update the database schema

Features:
  - Run all pending migrations
  - List migration status and descriptions
  - Rollback migrations
  - Schema validation and reporting
  - Detailed table and column information
  
Usage:
    python run_migrations.py                 # List all migrations and their status
    python run_migrations.py up              # Run all pending migrations
    python run_migrations.py down            # Rollback the last migration
    python run_migrations.py up <version>    # Run migrations up to a specific version
    python run_migrations.py reset           # Rollback all and re-apply all migrations
    python run_migrations.py validate        # Validate database schema
    python run_migrations.py schema          # Show detailed schema information
    python run_migrations.py status          # Display detailed migration status report
"""

import sys
import os
import json
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import engine
from app.core.logger import get_logger
from sqlalchemy import text, inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
MIGRATIONS_STATUS_FILE = MIGRATIONS_DIR / ".migrations_applied.json"


def get_applied_migrations():
    """Load the list of applied migrations from file"""
    if MIGRATIONS_STATUS_FILE.exists():
        try:
            with open(MIGRATIONS_STATUS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read migrations status file: {e}")
            return []
    return []


def save_applied_migrations(migrations):
    """Save the list of applied migrations to file"""
    try:
        with open(MIGRATIONS_STATUS_FILE, 'w') as f:
            json.dump(migrations, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save migrations status: {e}")
        raise


def get_migration_files():
    """Get all migration files, sorted by number"""
    migration_files = sorted([
        f for f in MIGRATIONS_DIR.glob("*.py")
        if f.name not in ["__init__.py", "README.md"]
        and f.name[0].isdigit()
    ])
    return migration_files


def validate_database_connection():
    """Validate that the database connection works"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True, "Database connection successful"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"


def get_database_tables() -> Dict[str, List[str]]:
    """Get all tables and their columns from the database"""
    try:
        inspector = inspect(engine)
        tables_info = {}
        
        for table_name in inspector.get_table_names():
            columns = []
            for column in inspector.get_columns(table_name):
                col_type = str(column['type'])
                nullable = "NULL" if column['nullable'] else "NOT NULL"
                columns.append(f"{column['name']} ({col_type}, {nullable})")
            
            tables_info[table_name] = columns
        
        return tables_info
    except Exception as e:
        logger.error(f"Error retrieving database schema: {e}")
        return {}


def validate_required_tables() -> Tuple[bool, List[str]]:
    """Validate that all required tables exist"""
    required_tables = [
        "staff", "syllabus", "unit_topic_concept", 
        "concept_progress", "tasks"
    ]
    
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        missing = [t for t in required_tables if t not in existing_tables]
        present = [t for t in required_tables if t in existing_tables]
        
        if missing:
            return False, missing
        return True, present
    except Exception as e:
        logger.error(f"Error validating tables: {e}")
        return False, []


def validate_required_columns() -> Tuple[bool, Dict[str, List[str]]]:
    """Validate that required columns exist in tasks table"""
    required_columns = {
        "tasks": [
            "id", "staff_id", "unit_id", "unit_name", "topic_id", 
            "topic_name", "concept_ids", "title", "description", 
            "status", "completion_percentage", "created_at", "updated_at"
        ]
    }
    
    try:
        inspector = inspect(engine)
        missing_columns = {}
        
        for table_name, required_cols in required_columns.items():
            if table_name not in inspector.get_table_names():
                missing_columns[table_name] = required_cols
                continue
            
            existing_cols = [col['name'] for col in inspector.get_columns(table_name)]
            missing = [col for col in required_cols if col not in existing_cols]
            
            if missing:
                missing_columns[table_name] = missing
        
        return len(missing_columns) == 0, missing_columns
    except Exception as e:
        logger.error(f"Error validating columns: {e}")
        return False, {}


def validate_indexes() -> Tuple[bool, List[str]]:
    """Validate that required indexes exist"""
    required_indexes = {
        "tasks": ["unit_id", "topic_id", "staff_id", "status"]
    }
    
    try:
        inspector = inspect(engine)
        missing_indexes = []
        
        for table_name, index_cols in required_indexes.items():
            if table_name not in inspector.get_table_names():
                continue
            
            # Get existing indexes
            existing_indexes = []
            for idx in inspector.get_indexes(table_name):
                for col in idx['column_names']:
                    existing_indexes.append(col)
            
            for col in index_cols:
                if col not in existing_indexes:
                    missing_indexes.append(f"{table_name}.{col}")
        
        return len(missing_indexes) == 0, missing_indexes
    except Exception as e:
        logger.warning(f"Could not validate indexes: {e}")
        return True, []  # Don't fail on index validation


def print_schema_report():
    """Print detailed schema information"""
    print("\n" + "=" * 80)
    print("DATABASE SCHEMA REPORT".center(80))
    print("=" * 80 + "\n")
    
    # Connection status
    is_connected, msg = validate_database_connection()
    status_icon = "✓" if is_connected else "✗"
    print(f"{status_icon} Database Connection: {msg}\n")
    
    if not is_connected:
        return
    
    # Tables and columns
    tables_info = get_database_tables()
    print(f"Found {len(tables_info)} table(s):\n")
    for i, (table_name, columns) in enumerate(sorted(tables_info.items()), 1):
        print(f"{i}. {table_name} ({len(columns)} columns)")
        for col in columns:
            print(f"   ├─ {col}")
        print()
    
    print("=" * 80 + "\n")


def print_schema_validation_report():
    """Print schema validation report"""
    print("\n" + "=" * 80)
    print("SCHEMA VALIDATION REPORT".center(80))
    print("=" * 80 + "\n")
    
    # Connection status
    is_connected, msg = validate_database_connection()
    status_icon = "✓" if is_connected else "✗"
    print(f"[{status_icon}] Database Connection: {msg}\n")
    
    if not is_connected:
        return
    
    # Required tables
    all_tables_present, tables_list = validate_required_tables()
    status_icon = "✓" if all_tables_present else "✗"
    print(f"[{status_icon}] Required Tables: {len(tables_list)} present")
    for table in tables_list:
        print(f"     ├─ {table}")
    print()
    
    # Required columns
    all_cols_present, missing_cols = validate_required_columns()
    status_icon = "✓" if all_cols_present else "✗"
    print(f"[{status_icon}] Required Columns:")
    if all_cols_present:
        print("     └─ All required columns present ✓")
    else:
        for table, cols in missing_cols.items():
            print(f"     ├─ {table}:")
            for col in cols:
                print(f"     │  ├─ MISSING: {col}")
    print()
    
    # Indexes
    indexes_valid, missing_indexes = validate_indexes()
    status_icon = "✓" if indexes_valid else "⚠"
    print(f"[{status_icon}] Indexed Columns:")
    if not missing_indexes:
        print("     └─ All recommended indexes present ✓")
    else:
        for idx in missing_indexes:
            print(f"     ├─ MISSING INDEX: {idx}")
    print()
    
    # Overall status
    overall_ok = is_connected and all_tables_present and all_cols_present
    status_icon = "✓" if overall_ok else "✗"
    print("=" * 80)
    overall_msg = "Database schema is valid and ready!" if overall_ok else "Database schema validation failed!"
    print(f"[{status_icon}] {overall_msg}".center(80))
    print("=" * 80 + "\n")
    
    return overall_ok



def load_migration(file_path):
    """Dynamically load a migration module"""
    spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def list_migrations():
    """List all migrations and their status"""
    migration_files = get_migration_files()
    applied = get_applied_migrations()
    
    print("\n" + "=" * 70)
    print("MIGRATION STATUS".center(70))
    print("=" * 70)
    
    if not migration_files:
        print("No migrations found")
        return
    
    for i, migration_file in enumerate(migration_files, 1):
        migration_name = migration_file.stem
        is_applied = migration_name in applied
        status = "✓ APPLIED" if is_applied else "○ PENDING"
        
        # Try to get the migration description from docstring
        try:
            module = load_migration(migration_file)
            doc = module.__doc__ or ""
            description = doc.split('\n')[0].strip() if doc else migration_name
        except Exception:
            description = migration_name
        
        print(f"{i}. [{status}] {migration_name}")
        print(f"   └─ {description}")
    
    print("=" * 70 + "\n")
    print(f"Total: {len(migration_files)} migrations | Applied: {len(applied)}")
    print()


def run_migration(migration_file, applied_migrations):
    """Run a single migration"""
    migration_name = migration_file.stem
    
    try:
        module = load_migration(migration_file)
        
        if not hasattr(module, 'upgrade'):
            logger.error(f"Migration {migration_name} has no 'upgrade' function")
            return False
        
        print(f"Running migration: {migration_name}...")
        module.upgrade()
        
        applied_migrations.append(migration_name)
        save_applied_migrations(applied_migrations)
        
        print(f"✓ Migration {migration_name} applied successfully\n")
        return True
    except Exception as e:
        logger.error(f"Error running migration {migration_name}: {e}", exc_info=True)
        print(f"✗ Migration {migration_name} failed: {e}\n")
        return False


def rollback_migration(migration_name):
    """Rollback a single migration"""
    migration_file = MIGRATIONS_DIR / f"{migration_name}.py"
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_name}")
        return False
    
    try:
        module = load_migration(migration_file)
        
        if not hasattr(module, 'downgrade'):
            logger.warning(f"Migration {migration_name} has no 'downgrade' function, skipping rollback")
            return True
        
        print(f"Rolling back migration: {migration_name}...")
        module.downgrade()
        
        print(f"✓ Migration {migration_name} rolled back successfully\n")
        return True
    except Exception as e:
        logger.error(f"Error rolling back migration {migration_name}: {e}", exc_info=True)
        print(f"✗ Rollback of {migration_name} failed: {e}\n")
        return False


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        list_migrations()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_migrations()
    
    elif command == "schema":
        print_schema_report()
    
    elif command == "validate":
        is_valid = print_schema_validation_report()
        sys.exit(0 if is_valid else 1)
    
    elif command == "status":
        print("\n" + "=" * 80)
        print("MIGRATION STATUS & SCHEMA VALIDATION".center(80))
        print("=" * 80 + "\n")
        list_migrations()
        print_schema_validation_report()
    
    elif command == "up":
        # Validate connection first
        is_connected, msg = validate_database_connection()
        if not is_connected:
            print(f"✗ {msg}")
            sys.exit(1)
        
        migration_files = get_migration_files()
        applied = get_applied_migrations()
        
        # Determine which migrations to run
        if len(sys.argv) > 2:
            # Run up to a specific migration
            target = sys.argv[2]
            migrations_to_run = [
                f for f in migration_files
                if f.stem not in applied and f.stem <= target
            ]
        else:
            # Run all pending migrations
            migrations_to_run = [
                f for f in migration_files
                if f.stem not in applied
            ]
        
        if not migrations_to_run:
            print("✓ All migrations are already applied\n")
            print_schema_validation_report()
            return
        
        print(f"\nApplying {len(migrations_to_run)} migration(s)...\n")
        failed = False
        
        for migration_file in migrations_to_run:
            if not run_migration(migration_file, applied):
                failed = True
                break
        
        if failed:
            print("❌ One or more migrations failed")
            sys.exit(1)
        else:
            print("✅ All migrations applied successfully!")
            print("\nValidating schema...\n")
            is_valid = print_schema_validation_report()
            if not is_valid:
                logger.warning("Schema validation found issues - please review")
    
    elif command == "down":
        applied = get_applied_migrations()
        
        if not applied:
            print("✓ No migrations to rollback\n")
            return
        
        # Rollback the last applied migration
        last_migration = applied[-1]
        print(f"\nRolling back last migration...\n")
        
        if rollback_migration(last_migration):
            applied.pop()
            save_applied_migrations(applied)
            print("✅ Migration rolled back successfully!")
            print("\nValidating schema...\n")
            print_schema_validation_report()
        else:
            print("❌ Failed to rollback migration")
            sys.exit(1)
    
    elif command == "reset":
        migration_files = get_migration_files()
        applied = get_applied_migrations()
        
        print(f"\nThis will rollback and re-apply {len(migration_files)} migration(s)")
        confirm = input("Are you sure? (yes/no): ").lower().strip()
        
        if confirm != "yes":
            print("Cancelled.\n")
            return
        
        # Rollback all in reverse order
        print("\nRolling back migrations...\n")
        for migration_name in reversed(applied):
            if not rollback_migration(migration_name):
                print("❌ Rollback failed, aborting")
                sys.exit(1)
        
        # Apply all again
        print("\nApplying migrations...\n")
        applied = []
        for migration_file in migration_files:
            if not run_migration(migration_file, applied):
                print("❌ Migration failed, aborting")
                sys.exit(1)
        
        print("✅ All migrations reset successfully!")
        print("\nValidating schema...\n")
        print_schema_validation_report()
    
    else:
        print(f"Unknown command: {command}")
        print("\nAvailable commands:")
        print("  - list       Show all migrations and their status")
        print("  - up         Run all pending migrations")
        print("  - down       Rollback the last migration")
        print("  - reset      Rollback and re-apply all migrations")
        print("  - validate   Validate database schema")
        print("  - schema     Show detailed schema information")
        print("  - status     Show migration status and schema validation")
        sys.exit(1)


if __name__ == "__main__":
    main()
