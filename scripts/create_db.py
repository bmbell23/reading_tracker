from src.models.base import Base, engine

def create_database():
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    create_database()