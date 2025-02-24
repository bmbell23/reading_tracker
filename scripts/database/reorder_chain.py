#!/usr/bin/env python3
from pathlib import Path
import sys
import subprocess
from datetime import date, timedelta
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

# Add project root to Python path
from scripts.utils.paths import find_project_root
project_root = find_project_root()
sys.path.insert(0, str(project_root))

from src.models.base import SessionLocal
from src.models.reading import Reading
from src.models.book import Book

console = Console()

def display_reading_group(readings, title, style="cyan"):
    """Display a group of readings in a table format"""
    table = Table(title=title, style=style)
    table.add_column("Reading ID", justify="right", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Start Date", style="blue")
    table.add_column("End Date", style="blue")
    table.add_column("Status", style="yellow")

    for reading in readings:
        # Determine dates and status
        start_date = reading.date_started or reading.date_est_start
        end_date = reading.date_finished_actual or reading.date_est_end
        status = "Completed" if reading.date_finished_actual else "Current" if reading.date_started else "Upcoming"

        table.add_row(
            str(reading.id),
            reading.book.title,
            str(start_date) if start_date else "TBD",
            str(end_date) if end_date else "TBD",
            status
        )

    console.print(table)

def get_chain(session, reading_id):
    """Get the complete reading chain containing the specified reading"""
    # First find the reading
    reading = session.get(Reading, reading_id)
    if not reading:
        return None

    # Build chain by going backwards to start
    chain = []
    current = reading
    while current:
        chain.insert(0, current)  # Add to start of list
        if not current.id_previous:
            break
        current = session.get(Reading, current.id_previous)

    # Now go forwards to get any subsequent readings
    current = reading
    while True:
        # Find the next reading that points to current
        next_reading = session.query(Reading).filter(Reading.id_previous == current.id).first()
        if not next_reading:
            break
        chain.append(next_reading)
        current = next_reading

    return chain

def get_chain_segment(session, reading_id, target_id):
    """Get the relevant segment of the reading chain"""
    # Get the full chain first
    chain = get_chain(session, reading_id)
    if not chain:
        return None, None, None, None

    # Find positions of both readings
    reading_pos = None
    target_pos = None
    for i, r in enumerate(chain):
        if r.id == reading_id:
            reading_pos = i
        if r.id == target_id:
            target_pos = i
        if reading_pos is not None and target_pos is not None:
            break

    if reading_pos is None or target_pos is None:
        return None, None, None, None

    # Calculate the range to show the full span between positions
    earliest_pos = min(reading_pos, target_pos)
    latest_pos = max(reading_pos, target_pos)

    # Show 3 books before earliest position and 3 books after latest position
    start_idx = max(0, earliest_pos - 3)
    end_idx = min(len(chain), latest_pos + 4)

    # Return the full span segment
    return chain[start_idx:end_idx], reading_pos, target_pos, chain

def update_chain_dates(session, chain, start_pos):
    """Update estimated dates for all readings from start_pos onwards"""
    for i in range(start_pos, len(chain)):
        reading = chain[i]
        prev_reading = chain[i-1] if i > 0 else None

        # If this is the first book or has an actual start date, use that
        if reading.date_started:
            reading.date_est_start = reading.date_started
        elif prev_reading and prev_reading.date_est_end:
            reading.date_est_start = prev_reading.date_est_end + timedelta(days=1)

        # Calculate estimated end date if we have start date and days estimate
        if reading.date_est_start and reading._days_estimate:
            reading.date_est_end = reading.date_est_start + timedelta(days=reading._days_estimate)

def run_chain_report():
    """Run the reading chain report generation"""
    report_script = project_root / "scripts" / "reports" / "reading_chain_report.py"
    try:
        console.print("\n[bold]Regenerating reading chain report...[/bold]")
        subprocess.run([sys.executable, str(report_script)], check=True)
        console.print("[green]Reading chain report updated successfully![/green]")
    except subprocess.CalledProcessError as e:
        console.print("[red]Error regenerating reading chain report[/red]")
        console.print(f"[red]Error: {str(e)}[/red]")

def get_chain_segment_between(session, start_id, end_id, chain=None):
    """Get a segment of the chain from start_id to end_id inclusive"""
    if chain is None:
        # If no chain provided, get the full chain starting from start_id
        chain = get_chain(session, start_id)
        if not chain:
            return None, None, None

    # Find positions of both readings in the chain
    start_pos = None
    end_pos = None
    for i, r in enumerate(chain):
        if r.id == start_id:
            start_pos = i
        if r.id == end_id:
            end_pos = i
        if start_pos is not None and end_pos is not None:
            break

    if start_pos is None or end_pos is None:
        return None, None, None

    # Return the segment and positions
    return chain[start_pos:end_pos + 1], start_pos, end_pos

def reorder_chain(reading_id, target_id):
    """Reorder a reading in the chain to be after the target reading"""
    session = SessionLocal()
    try:
        # Get the full chain first
        full_chain = get_chain(session, reading_id)
        if not full_chain:
            console.print("[red]Could not find reading in the chain[/red]")
            return

        # Find positions for the move
        reading_pos = next(i for i, r in enumerate(full_chain) if r.id == reading_id)
        target_pos = next(i for i, r in enumerate(full_chain) if r.id == target_id)

        # Get book before the one we're moving (A)
        book_before_moving = full_chain[reading_pos - 1] if reading_pos > 0 else None

        # Get book after our target (B)
        book_after_target = full_chain[target_pos + 1] if target_pos + 1 < len(full_chain) else None

        # Get the original chain segment from A to B
        if book_before_moving and book_after_target:
            segment, _, _ = get_chain_segment_between(session, book_before_moving.id, book_after_target.id, full_chain)
            if segment:
                console.print("\n[bold]Current chain order:[/bold]")
                display_reading_group(segment, "Current Reading Chain")

        # Remove reading from current position
        reading_to_move = full_chain.pop(reading_pos)

        # Insert immediately after target position
        # If we removed an item before the target, adjust the target position
        adjusted_target_pos = target_pos if reading_pos > target_pos else target_pos - 1
        new_pos = adjusted_target_pos + 1
        full_chain.insert(new_pos, reading_to_move)

        # Update chain references
        for i, reading in enumerate(full_chain):
            if i == 0:
                reading.id_previous = None
            else:
                reading.id_previous = full_chain[i-1].id

        # Update estimated dates
        start_pos = min(reading_pos, new_pos)
        update_chain_dates(session, full_chain, start_pos)

        # Show the proposed new chain using the same A to B segment
        if book_before_moving and book_after_target:
            segment, _, _ = get_chain_segment_between(session, book_before_moving.id, book_after_target.id, full_chain)
            if segment:
                console.print("\n[bold]Proposed new chain order:[/bold]")
                display_reading_group(segment, "Updated Reading Chain")

        # Confirm changes
        if Confirm.ask("\nDo you want to save these changes?"):
            session.commit()
            console.print("[green]Chain updated successfully![/green]")
            run_chain_report()
        else:
            session.rollback()
            console.print("[yellow]Changes cancelled[/yellow]")

    except Exception as e:
        session.rollback()
        console.print(f"[red]Error: {str(e)}[/red]")
    finally:
        session.close()

def main():
    if len(sys.argv) != 3:
        console.print(Panel(
            "[red]Usage: python reorder_chain.py <reading_id_to_move> <reading_id_to_place_after>[/red]\n" +
            "Example: python reorder_chain.py 178 143  # Moves reading 178 to be after reading 143",
            title="Reading Chain Reorder",
            border_style="red"
        ))
        return

    try:
        reading_id = int(sys.argv[1])
        target_id = int(sys.argv[2])
        reorder_chain(reading_id, target_id)
    except ValueError:
        console.print("[red]Reading IDs must be numbers[/red]")

if __name__ == "__main__":
    main()
