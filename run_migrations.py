#!/usr/bin/env python
"""
Database Migration Runner
Manages execution of migrations in order and tracks migration history

Usage:
    # Run all pending migrations
    python run_migrations.py

    # Run migrations with verbose output
    python run_migrations.py --verbose

    # Show pending migrations
    python run_migrations.py status

    # Rollback last migration
    python run_migrations.py rollback

    # Manually run specific migration
    python run_migrations.py up 004_initial_schema_complete
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import text
import importlib.util

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database.session import engine
from app.core.logger import get_logger

logger = get_logger(__name__)

# Migration history file
MIGRATIONS_DIR = Path(__file__).parent / 'backend' / 'migrations'
HISTORY_FILE = MIGRATIONS_DIR / 'migration_history.json'


class MigrationRunner:
    """Manages database migrations"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.ensure_history_file()

    def ensure_history_file(self):
        """Create migration history file if it doesn't exist"""
        if not HISTORY_FILE.exists():
            self._save_history([])
            logger.info(f"✓ Created migration history file: {HISTORY_FILE}")

    def _save_history(self, history):
        """Save migration history to file"""
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)

    def _load_history(self):
        """Load migration history from file"""
        if not HISTORY_FILE.exists():
            return []
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)

    def _get_migration_files(self):
        """Get all migration files sorted by name"""
        migration_files = sorted([f for f in MIGRATIONS_DIR.glob('*.py') if not f.name.startswith('_')])
        return [f.name.replace('.py', '') for f in migration_files if f.name != 'migration_history.json']

    def _load_migration_module(self, migration_name):
        """Dynamically load a migration module"""
        migration_path = MIGRATIONS_DIR / f'{migration_name}.py'
        
        if not migration_path.exists():
            raise FileNotFoundError(f"Migration not found: {migration_name}")

        spec = importlib.util.spec_from_file_location(migration_name, migration_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module

    def get_pending_migrations(self):
        """Get list of migrations that haven't been run yet"""
        all_migrations = self._get_migration_files()
        history = self._load_history()
        executed = [m['name'] for m in history]
        
        return [m for m in all_migrations if m not in executed]

    def get_executed_migrations(self):
        """Get list of migrations that have been executed"""
        history = self._load_history()
        return [m['name'] for m in history]

    def run_migration(self, migration_name, direction='up'):
        """Run a specific migration"""
        try:
            if self.verbose:
                logger.info(f"Loading migration: {migration_name}")
            
            module = self._load_migration_module(migration_name)
            
            if direction == 'up':
                if not hasattr(module, 'upgrade'):
                    raise AttributeError(f"Migration {migration_name} doesn't have 'upgrade' function")
                
                logger.info(f"Running migration: {migration_name}")
                module.upgrade()
                
                # Record in history
                history = self._load_history()
                history.append({
                    'name': migration_name,
                    'executed_at': datetime.utcnow().isoformat(),
                    'direction': 'up'
                })
                self._save_history(history)
                logger.info(f"✓ Migration '{migration_name}' executed successfully")
                
            elif direction == 'down':
                if not hasattr(module, 'downgrade'):
                    raise AttributeError(f"Migration {migration_name} doesn't have 'downgrade' function")
                
                logger.info(f"Rolling back migration: {migration_name}")
                module.downgrade()
                
                # Remove from history
                history = self._load_history()
                history = [m for m in history if m['name'] != migration_name]
                self._save_history(history)
                logger.info(f"✓ Migration '{migration_name}' rolled back successfully")
            
            return True

        except Exception as e:
            logger.error(f"✗ Error running migration {migration_name}: {str(e)}", exc_info=True)
            return False

    def run_all_pending(self):
        """Run all pending migrations"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("✓ No pending migrations")
            return True

        logger.info(f"Found {len(pending)} pending migration(s)")
        logger.info("=" * 60)
        
        success_count = 0
        for migration in pending:
            if self.run_migration(migration, 'up'):
                success_count += 1
            else:
                logger.error(f"✗ Failed to run migration: {migration}")
                logger.error("Stopping migration run due to error")
                return False

        logger.info("=" * 60)
        logger.info(f"✓ Successfully executed {success_count}/{len(pending)} migrations")
        return True

    def show_status(self):
        """Show migration status"""
        all_migrations = self._get_migration_files()
        executed = self.get_executed_migrations()
        pending = self.get_pending_migrations()
        
        print("\n" + "=" * 60)
        print("MIGRATION STATUS")
        print("=" * 60)
        
        if not all_migrations:
            print("No migrations found")
            return

        print(f"\nTotal migrations: {len(all_migrations)}")
        print(f"Executed: {len(executed)}")
        print(f"Pending: {len(pending)}")
        
        print("\nExecuted Migrations:")
        if executed:
            for migration in executed:
                print(f"  ✓ {migration}")
        else:
            print("  (none)")

        print("\nPending Migrations:")
        if pending:
            for migration in pending:
                print(f"  ○ {migration}")
        else:
            print("  (none)")
        
        print("\n" + "=" * 60)

    def rollback_last(self):
        """Rollback the last executed migration"""
        history = self._load_history()
        
        if not history:
            logger.info("✓ No migrations to rollback")
            return True

        last_migration = history[-1]['name']
        logger.info(f"Rolling back last migration: {last_migration}")
        
        return self.run_migration(last_migration, 'down')


def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Database Migration Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_migrations.py              # Run all pending migrations
  python run_migrations.py status       # Show migration status
  python run_migrations.py rollback     # Rollback last migration
  python run_migrations.py up 004_...   # Run specific migration
        """
    )
    
    parser.add_argument('command', nargs='?', default='up', 
                        choices=['up', 'status', 'rollback', 'down'],
                        help='Migration command')
    parser.add_argument('migration', nargs='?', 
                        help='Specific migration name (for up/down commands)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    
    args = parser.parse_args()
    
    runner = MigrationRunner(verbose=args.verbose)
    
    try:
        if args.command == 'up':
            if args.migration:
                # Run specific migration
                success = runner.run_migration(args.migration, 'up')
            else:
                # Run all pending
                success = runner.run_all_pending()
        
        elif args.command == 'down':
            if not args.migration:
                logger.error("migration name required for 'down' command")
                return 1
            success = runner.run_migration(args.migration, 'down')
        
        elif args.command == 'status':
            runner.show_status()
            success = True
        
        elif args.command == 'rollback':
            success = runner.rollback_last()
        
        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("\nMigration cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"✗ Fatal error: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
