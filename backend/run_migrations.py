#!/usr/bin/env python
"""
Migration Runner Script
Runs database migrations in order to update the database schema

Usage:
    python run_migrations.py               # List all migrations and their status
    python run_migrations.py up            # Run all pending migrations
    python run_migrations.py down          # Rollback the last migration
    python run_migrations.py up <version>  # Run migrations up to a specific version
    python run_migrations.py reset         # Rollback all and re-apply all migrations
"""

import sys
import os
import json
import importlib.util
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import engine
from app.core.logger import get_logger
from sqlalchemy import text

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
    
    elif command == "up":
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
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: list, up, down, reset")
        sys.exit(1)


if __name__ == "__main__":
    main()
