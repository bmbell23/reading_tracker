from pathlib import Path
from scripts.utils.paths import find_project_root
import sys

# Add project root to Python path
project_root = find_project_root()
sys.path.insert(0, str(project_root))

from src.models.base import engine
from sqlalchemy import text

def reorder_books_columns():
    with engine.connect() as conn:
        # Create new table with desired column order
        conn.execute(text("""
            CREATE TABLE books_new (
                id INTEGER PRIMARY KEY,
                title VARCHAR NOT NULL,
                author_name_first VARCHAR,
                author_name_second VARCHAR,
                author_gender VARCHAR,
                word_count INTEGER,
                page_count INTEGER,
                date_published DATE,
                series VARCHAR,
                series_number INTEGER,
                genre VARCHAR
            )
        """))

        # Copy data from old table to new table
        conn.execute(text("""
            INSERT INTO books_new (
                id,
                title,
                author_name_first,
                author_name_second,
                author_gender,
                word_count,
                page_count,
                date_published,
                series,
                series_number,
                genre
            )
            SELECT
                id,
                title,
                author_name_first,
                author_name_second,
                author_gender,
                word_count,
                page_count,
                date_published,
                series,
                series_number,
                genre
            FROM books
        """))

        # Drop old table
        conn.execute(text("DROP TABLE books"))

        # Rename new table to old name
        conn.execute(text("ALTER TABLE books_new RENAME TO books"))

        conn.commit()

        print("Table columns reordered successfully!")

if __name__ == "__main__":
    reorder_books_columns()
