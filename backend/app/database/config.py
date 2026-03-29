import os
from dotenv import load_dotenv

# Load .env from backend directory
import sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent.parent  # Go up to backend/
env_path = backend_dir / ".env"
load_dotenv(env_path)

# Get raw DATABASE_URL from environment
raw_database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/academic_analyser"
)

# Format DATABASE_URL for SQLAlchemy
# Railway connections work best with default SSL handling
if raw_database_url.startswith("postgresql://"):
    # Check if SSL mode is already specified
    if "sslmode" in raw_database_url:
        DATABASE_URL = raw_database_url
    # For Railway: use sslmode=allow to work with proxy transparently
    elif "hopper.proxy.rlwy.net" in raw_database_url or ".railway" in raw_database_url:
        DATABASE_URL = raw_database_url + "?sslmode=allow"
    else:
        # Local PostgreSQL doesn't need SSL
        DATABASE_URL = raw_database_url
else:
    DATABASE_URL = raw_database_url

# Database configuration options - optimized for Railway
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False") == "True"
# Reduced pool size for Railway's connection limits
SQLALCHEMY_POOL_SIZE = int(os.getenv("SQLALCHEMY_POOL_SIZE", "3"))
SQLALCHEMY_MAX_OVERFLOW = int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", "5"))
# Connection timeout settings
SQLALCHEMY_POOL_TIMEOUT = int(os.getenv("SQLALCHEMY_POOL_TIMEOUT", "30"))
SQLALCHEMY_POOL_RECYCLE = int(os.getenv("SQLALCHEMY_POOL_RECYCLE", "3600"))
