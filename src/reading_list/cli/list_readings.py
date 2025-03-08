#!/usr/bin/env python3
"""
Simple CLI to list all readings ordered by start date
"""

import argparse
from rich.console import Console
from rich.table import Table
from ..queries.common_queries import CommonQueries

console = Console()

def display_readings():
    """Display all readings in a table format"""
    queries = CommonQueries()
    readings = queries.get_all_readings_ordered_by_start()
    
    table = Table(title="All Readings")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Start Date", style="yellow")
    table.add_column("Est. Start", style="yellow")
    table.add_column("Media", style="blue")
    
    for reading in readings:
        table.add_row(
            str(reading['id']),
            reading['title'],
            str(reading['date_started'] or ''),
            str(reading['date_est_start'] or ''),
            reading['media']
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
    try:
        display_readings()
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def main():
    """Main entry point for direct script execution"""
    parser = argparse.ArgumentParser(description="List all readings ordered by start date")
    args = parser.parse_args()
    return handle_command(args)

if __name__ == "__main__":
    main()
