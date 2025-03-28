"""CLI command to create a new reading entry."""
from datetime import date
from rich.console import Console
from sqlalchemy import text
from ..core.database.entry_editor import EntryEditor
from ..operations.chain_operations import ChainOperations
from ..models import Book, Reading

console = Console()

def add_subparser(subparsers):
    """Add the new-reading subparser to the main parser"""
    parser = subparsers.add_parser(
        "new-reading",
        help="Create a new reading entry"
    )
    parser.add_argument("book_id", type=int, help="Book ID")
    parser.add_argument("media", choices=["kindle", "hardcover", "audio"], help="Media type")
    return parser

def check_reread_status(chain_ops, reading_id):
    """Check if the new reading should be marked as a reread"""
    query = text("""
        WITH FirstReads AS (
            SELECT 
                book_id,
                MIN(COALESCE(date_started, date_est_start)) as first_read_date,
                id as first_read_id
            FROM read
            WHERE COALESCE(date_started, date_est_start) IS NOT NULL
            GROUP BY book_id
        )
        SELECT DISTINCT
            r.id,
            r.book_id,
            b.title,
            COALESCE(r.date_started, r.date_est_start) as read_date,
            fr.first_read_date
        FROM read r
        JOIN books b ON r.book_id = b.id
        JOIN FirstReads fr ON r.book_id = fr.book_id
        WHERE 
            r.id = :reading_id
            AND COALESCE(r.date_started, r.date_est_start) > fr.first_read_date
            AND r.id != fr.first_read_id
    """)
    
    result = chain_ops.session.execute(query, {"reading_id": reading_id}).first()
    
    if result:
        # This is a reread - update the flag
        update_query = text("UPDATE read SET reread = TRUE WHERE id = :read_id")
        chain_ops.session.execute(update_query, {"read_id": reading_id})
        chain_ops.session.commit()
        console.print(f"[yellow]Marked as reread: Previous read found for '{result.title}'[/yellow]")
        return True
    return False

def handle_command(args):
    """Handle the new-reading command"""
    try:
        with ChainOperations() as chain_ops:
            # Verify book exists
            book = chain_ops.session.get(Book, args.book_id)
            if not book:
                console.print(f"[red]Error: Book ID {args.book_id} not found[/red]")
                return 1

            # Get the next available read ID
            next_id = chain_ops.session.execute(text("SELECT MAX(id) FROM read")).scalar()
            next_id = (next_id or 0) + 1

            # Get the latest chain ID for this media type
            prev_id = chain_ops.session.execute(
                text("""
                    SELECT id
                    FROM read
                    WHERE LOWER(media) = LOWER(:media)
                    AND date_finished_actual IS NULL
                    ORDER BY date_est_end DESC, id DESC
                    LIMIT 1
                """),
                {"media": args.media}
            ).scalar()

            # Create new reading entry
            new_reading = Reading(
                id=next_id,
                book_id=args.book_id,
                media=args.media,
                id_previous=prev_id
            )

            chain_ops.session.add(new_reading)
            chain_ops.session.commit()

            console.print(f"[green]Created new reading entry for '{book.title}'[/green]")
            console.print(f"Reading ID: {next_id}")
            console.print(f"Previous ID in chain: {prev_id or 'None'}")

            # Calculate days estimate for just this reading
            estimate_changes = chain_ops.preview_days_estimate_updates(media_type=args.media)
            estimate_changes = [change for change in estimate_changes if change['id'] == next_id]
            if estimate_changes:
                chain_ops.apply_days_estimate_updates(estimate_changes)
                chain_ops.session.commit()

            # Update chain dates for just this reading and its subsequent readings
            chain_changes = chain_ops.preview_chain_updates(media_type=args.media)
            if chain_changes:
                chain_ops.apply_chain_updates(chain_changes)
                chain_ops.session.commit()

            # Check and update reread status
            check_reread_status(chain_ops, next_id)

            # Generate chain report
            import subprocess
            subprocess.run(["reading-list", "chain-report"], check=True)

            return 0

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1
