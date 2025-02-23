from sqlalchemy import text
from src.models.base import engine

def rename_readings_table():
    """Rename 'readings' table to 'read' if it exists"""
    with engine.connect() as conn:
        try:
            print("Starting migration...")
            trans = conn.begin()

            # Check if old table exists
            result = conn.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='readings';
            """))

            if result.fetchone():
                print("Found 'readings' table, renaming to 'read'...")
                conn.execute(text("""
                    ALTER TABLE readings RENAME TO read;
                """))
                print("Table renamed successfully!")
            else:
                print("No 'readings' table found, skipping migration.")

            trans.commit()

        except Exception as e:
            print(f"Error during migration: {str(e)}")
            if 'trans' in locals():
                trans.rollback()
            raise

if __name__ == "__main__":
    print("Starting table rename migration...")
    try:
        rename_readings_table()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {str(e)}")