from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# Create engine
engine = create_engine('sqlite:///data/db/reading_list.db')

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def get_db():
    """Get database session"""
    return Session()

Base = declarative_base()