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
    table.add_column("Days Est.", justify="right")

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
