"""Database configuration and session management."""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Get project root directory
project_root = Path(__file__).resolve().parents[2]

# Configure database path
DATABASE_URL = f"sqlite:///{project_root}/data/db/reading_list.db"

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

def get_session():
    """Get a new database session."""
    return SessionLocal()