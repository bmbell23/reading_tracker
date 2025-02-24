from src.models.base import engine
from sqlalchemy import text

def cleanup_tables():
    """Remove deprecated and unnecessary tables"""
    with engine.connect() as conn:
        try:
            print("Starting table cleanup...")
            trans = conn.begin()

            # Check if tables exist before trying to drop them
            for table in ['readings', 'alembic_version']:
                result = conn.execute(text(f"""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='{table}'
                """))

                if result.fetchone():
                    print(f"Dropping {table} table...")
                    conn.execute(text(f"DROP TABLE {table}"))
                    print(f"Successfully dropped {table} table")
                else:
                    print(f"Table {table} not found - skipping")

            trans.commit()
            print("\nCleanup completed successfully!")

        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            if 'trans' in locals():
                trans.rollback()

if __name__ == "__main__":
    cleanup_tables()