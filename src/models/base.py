from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///reading_list.db')  # Can switch to PostgreSQL later
SessionLocal = sessionmaker(bind=engine)