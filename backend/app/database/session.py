
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:password@localhost/ai_phase1"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
