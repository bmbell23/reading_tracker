from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
import os

# Get database path from environment or use default
database_path = os.getenv('DATABASE_PATH', 'data/db/reading_list.db')
database_url = f"sqlite:///{database_path}"

# Create engine
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()
