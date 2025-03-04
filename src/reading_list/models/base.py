"""Base SQLAlchemy models and database configuration."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..utils.paths import get_project_paths

Base = declarative_base()

# Configure database using paths utility
paths = get_project_paths()
DATABASE_URL = f"sqlite:///{paths['database']}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
