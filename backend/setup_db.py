#!/usr/bin/env python
"""
Database setup script - Run this to initialize the database
Usage: python setup_db.py
"""
import sys
import os

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, drop_db
from app.database.session import engine


def setup_database():
    """Create all tables in the database"""
    print("Creating database tables...")
    try:
        init_db()
        print("✓ Database tables created successfully!")
        print(f"✓ Connected to: {os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/academic_analyser')}")
    except Exception as e:
        print(f"✗ Error creating database tables: {e}")
        sys.exit(1)


def reset_database():
    """Drop and recreate all tables"""
    print("Warning: This will delete all data in the database!")
    confirm = input("Are you sure? (yes/no): ").lower().strip()
    if confirm == "yes":
        print("Dropping all tables...")
        drop_db()
        print("✓ All tables dropped")
        setup_database()
    else:
        print("Cancelled.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_database()
    else:
        setup_database()
