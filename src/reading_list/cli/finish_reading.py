"""CLI command to mark a book as finished and transition to the next one."""
from datetime import date, timedelta
import subprocess
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from ..operations.chain_operations import ChainOperations
from ..models import Book, Reading
from ..repositories.reading_repository import ReadingRepository

console = Console()

def add_subparser(subparsers):
    """Add the finish-reading subparser to the main parser"""
    parser = subparsers.add_parser(
        "finish-reading",
        help="Mark a book as finished and transition to the next one"
    )
    return parser

def display_current_readings():
    """Display all current readings and return them."""
    repository = ReadingRepository()
    current_readings = repository.get_current_readings()

    if not current_readings:
        console.print("[yellow]No current readings found.[/yellow]")
        return []

    table = Table(title="Current Readings")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Author", style="blue")
    table.add_column("Media", style="magenta")
    table.add_column("Started", style="yellow")

    for reading in current_readings:
        table.add_row(
            str(reading.id),
            reading.book.title,
            f"{reading.book.author_name_first} {reading.book.author_name_second}".strip(),
            reading.media,
            str(reading.date_started) if reading.date_started else "Not started"
        )

    console.print(table)
    return current_readings

def find_next_readings(chain_ops, reading_id):
    """Find readings that have this reading as their previous reading."""
    next_readings = chain_ops.session.query(Reading).join(Book).filter(
        Reading.id_previous == reading_id,
        Reading.date_finished_actual.is_(None)
    ).all()

    return next_readings

def check_for_divergent_chain(next_readings):
    """Check if there are multiple next readings (divergent chain)."""
    return len(next_readings) > 1

def handle_command(args):
    """Handle the finish-reading command"""
    try:
        # Display current readings
        current_readings = display_current_readings()
        if not current_readings:
            return 1

        # Ask user to select a reading to finish
        reading_ids = [str(reading.id) for reading in current_readings]
        selected_id = Prompt.ask(
            "Enter the ID of the reading you want to mark as finished",
            choices=reading_ids
        )
        selected_id = int(selected_id)

        with ChainOperations() as chain_ops:
            # Get the selected reading
            reading = chain_ops.session.get(Reading, selected_id)
            if not reading:
                console.print(f"[red]Error: Reading ID {selected_id} not found[/red]")
                return 1

            # Confirm finishing the book
            console.print(f"\nYou selected: [green]{reading.book.title}[/green] by "
                         f"[blue]{reading.book.author_name_first} {reading.book.author_name_second}[/blue]")

            if not Confirm.ask("Do you want to mark this book as finished?"):
                console.print("[yellow]Operation cancelled.[/yellow]")
                return 0

            # Set the finish date to today
            today = date.today()
            reading.date_finished_actual = today
            chain_ops.session.commit()
            console.print(f"[green]Marked '{reading.book.title}' as finished on {today}[/green]")

            # Find the next reading(s) in the chain
            next_readings = find_next_readings(chain_ops, selected_id)

            # Check for divergent chain
            if check_for_divergent_chain(next_readings):
                console.print("[yellow]Warning: Divergent chain detected![/yellow]")
                console.print("Multiple books have this reading as their previous reading:")

                for i, next_reading in enumerate(next_readings, 1):
                    console.print(f"{i}. [cyan]{next_reading.book.title}[/cyan]")

                console.print("\nPlease run 'reading-list divergent-chains' to resolve this issue.")

                # Commit changes and update chain
                chain_ops.session.commit()
                console.print("\n[yellow]Running chain updates...[/yellow]")
                subprocess.run(["reading-list", "update-readings", "--chain", "--no-confirm"], check=True)
                return 0

            # If there's exactly one next reading, set its start date to tomorrow
            if next_readings:
                next_reading = next_readings[0]
                tomorrow = today + timedelta(days=1)

                console.print(f"\nNext book in chain: [green]{next_reading.book.title}[/green]")
                if Confirm.ask(f"Set start date to tomorrow ({tomorrow})?"):
                    next_reading.date_started = tomorrow
                    chain_ops.session.commit()
                    console.print(f"[green]Set start date for '{next_reading.book.title}' to {tomorrow}[/green]")
            else:
                console.print("[yellow]No next book found in the chain.[/yellow]")

            # Run chain updates
            console.print("\n[yellow]Running chain updates...[/yellow]")
            subprocess.run(["reading-list", "update-readings", "--chain", "--no-confirm"], check=True)

            # Run the update commands directly
            console.print("[yellow]Running full database update...[/yellow]")

            # Ask if the user wants to run the interactive update-entries command
            if Confirm.ask("Run interactive update-entries command?", default=False):
                subprocess.run(["reading-list", "update-entries"], check=True)

            # Run the automatic update-readings command
            subprocess.run(["reading-list", "update-readings", "--all", "--no-confirm"], check=True)

            console.print("[green]All updates completed successfully![/green]")
            return 0

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1
