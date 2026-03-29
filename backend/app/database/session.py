
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import (
    DATABASE_URL,
    SQLALCHEMY_ECHO,
    SQLALCHEMY_POOL_SIZE,
    SQLALCHEMY_MAX_OVERFLOW,
    SQLALCHEMY_POOL_TIMEOUT,
    SQLALCHEMY_POOL_RECYCLE,
)

engine = create_engine(
    DATABASE_URL,
    echo=SQLALCHEMY_ECHO,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_MAX_OVERFLOW,
    pool_timeout=SQLALCHEMY_POOL_TIMEOUT,
    pool_recycle=SQLALCHEMY_POOL_RECYCLE,
    connect_args={
        "connect_timeout": 30,
        "keepalives": 1,
        "keepalives_idle": 30,
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
