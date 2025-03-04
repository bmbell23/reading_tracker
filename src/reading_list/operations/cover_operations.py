"""Operations for managing book cover status."""
from pathlib import Path
from typing import List, Tuple
from sqlalchemy import text
from ..models.base import engine
from ..utils.paths import get_project_paths

def get_books_missing_covers() -> List[Tuple[int, str, str]]:
    """Get list of books missing covers."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                b.id,
                b.title,
                CASE
                    WHEN b.author_name_second IS NOT NULL
                    THEN b.author_name_first || ' ' || b.author_name_second
                    ELSE b.author_name_first
                END as author
            FROM books b
            WHERE b.cover = FALSE
            ORDER BY b.id
        """))
        return [(row[0], row[1], row[2]) for row in result]

def update_cover_status() -> Tuple[int, int]:
    """Update books.cover based on existing cover files.
    
    Returns:
        Tuple containing (total_books, books_with_covers)
    """
    paths = get_project_paths()
    covers_path = paths['assets'] / 'book_covers'  # Changed from paths['book_covers']

    if not covers_path.exists():
        raise FileNotFoundError(f"Cover directory not found at {covers_path}")

    with engine.connect() as conn:
        try:
            # First, set all cover values to FALSE
            conn.execute(text("UPDATE books SET cover = FALSE"))

            # Get list of all book IDs
            result = conn.execute(text("SELECT id FROM books"))
            book_ids = [row[0] for row in result]

            updates = 0
            for book_id in book_ids:
                has_cover = False
                for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    if (covers_path / f"{book_id}{ext}").exists():
                        has_cover = True
                        break

                if has_cover:
                    conn.execute(
                        text("UPDATE books SET cover = TRUE WHERE id = :book_id"),
                        {"book_id": book_id}
                    )
                    updates += 1

            conn.commit()
            return len(book_ids), updates

        except Exception as e:
            conn.rollback()
            raise e
