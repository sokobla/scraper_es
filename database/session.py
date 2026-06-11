from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.base import Base

DATABASE_URL = "sqlite:///results.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def init_db():
    from models import Result
    Base.metadata.create_all(bind=engine)