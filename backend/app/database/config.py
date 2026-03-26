import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/academic_analyser"
)

# Database configuration options
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False") == "True"
SQLALCHEMY_POOL_SIZE = int(os.getenv("SQLALCHEMY_POOL_SIZE", "5"))
SQLALCHEMY_MAX_OVERFLOW = int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", "10"))
