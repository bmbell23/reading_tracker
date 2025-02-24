from pathlib import Path
from src.models.base import engine
from sqlalchemy import text
from rich.console import Console
from rich.table import Table

def update_cover_status():
    """Update books.cover based on existing cover files in assets/book_covers"""
    console = Console()

    # Get the project root directory and construct path to covers
    project_root = Path(__file__).parent.parent.parent
    covers_path = project_root / 'assets' / 'book_covers'

    if not covers_path.exists():
        console.print(f"[red]Error: Cover directory not found at {covers_path}[/red]")
        return

    # Get all book IDs from the database
    with engine.connect() as conn:
        try:
            console.print("[blue]Starting cover status update...[/blue]")

            # First, set all cover values to FALSE
            conn.execute(text("UPDATE books SET cover = FALSE"))

            # Get list of all book IDs
            result = conn.execute(text("SELECT id FROM books"))
            book_ids = [row[0] for row in result]

            updates = 0
            for book_id in book_ids:
                has_cover = False
                # Check for any image file with matching book ID
                for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    if (covers_path / f"book_{book_id}{ext}").exists():
                        has_cover = True
                        break

                if has_cover:
                    conn.execute(
                        text("UPDATE books SET cover = TRUE WHERE id = :book_id"),
                        {"book_id": book_id}
                    )
                    updates += 1

            conn.commit()
            console.print(f"\n[green]Update completed successfully![/green]")
            console.print(f"Found covers for [blue]{updates}[/blue] out of [blue]{len(book_ids)}[/blue] books")

            # Show books missing covers
            if updates < len(book_ids):
                # Create Rich table
                table = Table(
                    title="\nBooks Missing Covers",
                    show_header=True,
                    header_style="bold magenta",
                    border_style="bright_black"
                )

                # Add columns
                table.add_column("ID", justify="right", style="cyan")
                table.add_column("Title", style="white")
                table.add_column("Author", style="white")

                # Get missing books with author information
                missing = conn.execute(text("""
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

                # Add rows to table
                for book_id, title, author in missing:
                    table.add_row(
                        str(book_id),
                        title or "N/A",
                        author or "Unknown"
                    )

                # Print the table
                console.print(table)

        except Exception as e:
            console.print(f"[red]Error during update: {str(e)}[/red]")
            conn.rollback()

if __name__ == "__main__":
    update_cover_status()
