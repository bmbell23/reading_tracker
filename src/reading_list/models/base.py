from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

# Configure database path
project_root = Path(__file__).parents[3]  # Go up 3 levels from models/base.py
DATABASE_URL = f"sqlite:///{project_root}/data/db/reading_list.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
