from sqlalchemy import text
from src.models.base import engine

def add_est_date_columns():
    """Add estimated date columns if they don't exist"""
    with engine.connect() as conn:
        try:
            print("Starting migration...")
            trans = conn.begin()

            # Check if columns exist
            result = conn.execute(text("""
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='read';
            """))
            table_def = result.scalar()

            # Add date_est_start if missing
            if 'date_est_start' not in table_def:
                print("Adding date_est_start column...")
                conn.execute(text("""
                    ALTER TABLE read
                    ADD COLUMN date_est_start DATE;
                """))

            # Add date_est_end if missing
            if 'date_est_end' not in table_def:
                print("Adding date_est_end column...")
                conn.execute(text("""
                    ALTER TABLE read
                    ADD COLUMN date_est_end DATE;
                """))

            trans.commit()
            print("Migration completed successfully!")

        except Exception as e:
            print(f"Error during migration: {str(e)}")
            if 'trans' in locals():
                trans.rollback()
            raise

if __name__ == "__main__":
    add_est_date_columns()