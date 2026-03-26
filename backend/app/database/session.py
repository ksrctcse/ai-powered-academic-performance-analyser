
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database.config import (
    DATABASE_URL,
    SQLALCHEMY_ECHO,
    SQLALCHEMY_POOL_SIZE,
    SQLALCHEMY_MAX_OVERFLOW,
)

engine = create_engine(
    DATABASE_URL,
    echo=SQLALCHEMY_ECHO,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_MAX_OVERFLOW,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
