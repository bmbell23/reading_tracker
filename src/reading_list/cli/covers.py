"""CLI command for managing book cover status."""
import argparse
from rich.console import Console
from rich.table import Table
from ..operations.cover_operations import update_cover_status, get_books_missing_covers

console = Console()

def update_covers():
    """Update cover status for all books."""
    try:
        total_books, books_with_covers = update_cover_status()
        console.print("\n[green]Cover status update completed successfully![/green]")
        console.print(f"Found covers for [blue]{books_with_covers}[/blue] out of [blue]{total_books}[/blue] books")

        # Show books missing covers if any
        if books_with_covers < total_books:
            missing_books = get_books_missing_covers()
            
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

            # Add rows to table
            for book_id, title, author in missing_books:
                table.add_row(
                    str(book_id),
                    title or "N/A",
                    author or "Unknown"
                )

            # Print the table
            console.print(table)

    except FileNotFoundError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1
    except Exception as e:
        console.print(f"[red]Error during update: {str(e)}[/red]")
        return 1

    return 0

def main():
    """CLI entry point for cover management."""
    parser = argparse.ArgumentParser(
        description="Manage book cover status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update cover status for all books
  reading-list covers update

  # More commands coming soon...
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update cover status for all books")

    args = parser.parse_args()

    if args.command == "update":
        return update_covers()
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    exit(main())
