#!/usr/bin/env python3
"""
Simple CLI to list all readings ordered by start date
"""

import argparse
from typing import List, Dict
from rich.table import Table
from rich.console import Console
from sqlalchemy import text
from ..operations.chain_operations import ChainOperations
from ..models.base import SessionLocal
from ..models.reading import Reading
from datetime import datetime
from rich.prompt import Confirm

console = Console()

def get_readings() -> List[Dict]:
    """Get all readings with their associated book data"""
    with SessionLocal() as session:
        chain_ops = ChainOperations(session)
        readings = session.execute(text("""
            SELECT 
                r.id as read_id,
                r.media,
                b.title,
                r.date_started,
                r.date_finished_actual,
                r.date_est_start,
                r.date_est_end,
                b.word_count,
                b.page_count,
                r.days_estimate
            FROM read r
            JOIN books b ON r.book_id = b.id
            ORDER BY 
                COALESCE(r.date_started, r.date_est_start) ASC NULLS LAST,
                b.title ASC
        """)).mappings().all()
        return [dict(r) for r in readings]

def display_readings(readings: List[Dict]) -> None:
    """Display readings in a formatted table."""
    table = Table(title="Reading List")
    
    # Define media colors
    MEDIA_COLORS = {
        'hardcover': 'purple',
        'kindle': 'blue',
        'audio': '#FF6600'  # Specific orange for audio
    }

    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Media", style="bold")
    table.add_column("Title", style="bold")
    table.add_column("Start Date", justify="center")
    table.add_column("End Date", justify="center")
    table.add_column("Pages", justify="right")
    table.add_column("Words", justify="right")
    table.add_column("Days", justify="right")

    for reading in readings:
        # Determine start date (actual or estimated)
        start_date = reading.get('date_started') or reading.get('date_est_start')
        start_style = "green" if reading.get('date_started') else "yellow"
        formatted_start = f"[{start_style}]{start_date}[/{start_style}]" if start_date else ""

        # Determine end date (actual or estimated)
        end_date = reading.get('date_finished_actual') or reading.get('date_est_end')
        end_style = "green" if reading.get('date_finished_actual') else "yellow"
        formatted_end = f"[{end_style}]{end_date}[/{end_style}]" if end_date else ""

        # Format media with color
        media = reading.get('media', '').lower()
        media_color = MEDIA_COLORS.get(media, 'white')
        formatted_media = f"[{media_color}]{media.title()}[/{media_color}]"

        # Format word count and page count with commas
        word_count = reading.get('word_count')
        page_count = reading.get('page_count')
        formatted_words = f"{word_count:,}" if word_count else ""
        formatted_pages = f"{page_count:,}" if page_count else ""

        table.add_row(
            str(reading.get('read_id', '')),
            formatted_media,
            reading.get('title', '')[:50],
            formatted_start,
            formatted_end,
            formatted_pages,
            formatted_words,
            str(reading.get('days_estimate', ''))
        )

    console.print(table)

def add_subparser(subparsers):
    """Add the list-readings subparser to the main parser"""
    parser = subparsers.add_parser(
        "list-readings",
        help="List all readings ordered by start date"
    )
    return parser

def handle_command(args):
    """Handle the list-readings command"""
    readings = get_readings()
    display_readings(readings)
    return 0

def main():
    """Main entry point for direct script execution"""
    parser = argparse.ArgumentParser(description="List all readings ordered by start date")
    args = parser.parse_args()
    return handle_command(args)

if __name__ == "__main__":
    main()

def update_reading_entry(reading_id: int, chain_ops: ChainOperations) -> None:
    """Update a reading entry"""
    update_data = {}
    
    # Get current reading
    reading = chain_ops.session.get(Reading, reading_id)
    if not reading:
        console.print(f"[red]Reading {reading_id} not found[/red]")
        return

    # Handle id_previous
    if Confirm.ask(f"Update Id Previous? (current: {reading.id_previous})", default=False):
        update_data['id_previous'] = input("Id Previous: ").strip() or None

    # Handle media
    if Confirm.ask(f"Update Media? (current: {reading.media})", default=False):
        update_data['media'] = input("Media: ").strip()

    # Handle dates with proper conversion
    if Confirm.ask(f"Update Start Date (YYYY-MM-DD)? (current: {reading.date_started})", default=False):
        date_str = input("Start Date: ").strip()
        if date_str:
            update_data['date_started'] = datetime.strptime(date_str, '%Y-%m-%d').date()

    if Confirm.ask(f"Update Date Finished Actual? (current: None) [y/n]", default=False):
        date_str = input("Date Finished Actual: ").strip()
        if date_str:
            try:
                # Convert string to date object before adding to update_data
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                update_data['date_finished_actual'] = date_obj
                print(f"Debug: Added date_finished_actual = {date_obj} (type: {type(date_obj)})")
            except ValueError as e:
                console.print(f"[red]Invalid date format. Please use YYYY-MM-DD: {e}[/red]")
                return

    # Handle ratings
    rating_fields = ['rating_horror', 'rating_spice', 'rating_world_building', 
                    'rating_writing', 'rating_characters', 'rating_readability', 
                    'rating_enjoyment']
    
    for field in rating_fields:
        current_value = getattr(reading, field)
        if Confirm.ask(f"Update {field.replace('_', ' ').title()}? (current: {current_value})", default=False):
            update_data[field] = input(f"{field.replace('_', ' ').title()}: ").strip() or None

    # Handle rank
    if Confirm.ask(f"Update Rank? (current: {reading.rank})", default=False):
        update_data['rank'] = input("Rank: ").strip() or None

    # Handle estimates and calculations
    if Confirm.ask(f"Update Days Estimate? (current: {reading.days_estimate})", default=False):
        update_data['days_estimate'] = input("Days Estimate: ").strip() or None

    if Confirm.ask(f"Update Days Elapsed To Read? (current: {reading.days_elapsed_to_read})", default=False):
        update_data['days_elapsed_to_read'] = input("Days Elapsed To Read: ").strip() or None

    if Confirm.ask(f"Update Days To Read Delta From Estimate? (current: {reading.days_to_read_delta_from_estimate})", default=False):
        update_data['days_to_read_delta_from_estimate'] = input("Days To Read Delta From Estimate: ").strip() or None

    # Handle estimated dates
    if Confirm.ask(f"Update Date Est Start? (current: {reading.date_est_start})", default=False):
        date_str = input("Date Est Start: ").strip()
        if date_str:
            update_data['date_est_start'] = datetime.strptime(date_str, '%Y-%m-%d').date()

    if Confirm.ask(f"Update Date Est End? (current: {reading.date_est_end})", default=False):
        date_str = input("Date Est End: ").strip()
        if date_str:
            update_data['date_est_end'] = datetime.strptime(date_str, '%Y-%m-%d').date()

    print(f"\nDebug - New data received: {update_data}")

    if update_data:
        success, message = chain_ops.update_reading(reading_id, update_data)
        if success:
            console.print(f"[green]{message}[/green]")
        else:
            console.print(f"[red]Error updating entry: {message}[/red]")
