from sqlalchemy import text
from src.models.base import engine

def add_date_est_end_column():
    """Add date_est_end column to read table"""
    with engine.connect() as conn:
        try:
            print("Starting migration...")

            # Begin transaction
            trans = conn.begin()

            print("Adding new column...")
            # Add the new column
            conn.execute(
                text("ALTER TABLE read ADD COLUMN date_est_end DATE")
            )

            print("Updating existing records...")
            # Update existing records with calculated end dates
            result = conn.execute(
                text("""
                    UPDATE read
                    SET date_est_end = date(date_started, '+' || days_estimate || ' days')
                    WHERE date_started IS NOT NULL
                    AND days_estimate IS NOT NULL
                    AND date_finished_actual IS NULL
                """)
            )

            # Commit the transaction
            trans.commit()
            print(f"Migration completed successfully! Updated {result.rowcount} rows.")

        except Exception as e:
            print(f"Error occurred during migration: {str(e)}")
            print("Rolling back changes...")
            if 'trans' in locals():
                trans.rollback()
            raise

if __name__ == "__main__":
    print("Starting database migration to add date_est_end column...")
    try:
        add_date_est_end_column()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {str(e)}")
