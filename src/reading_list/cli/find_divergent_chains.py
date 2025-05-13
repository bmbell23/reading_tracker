#!/usr/bin/env python3
"""
Find Divergent Reading Chains
=============================

CLI tool for finding divergent reading chains - cases where multiple unfinished books
have the same previous reading ID.
"""

import argparse
from typing import Dict, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule
from sqlalchemy import func

from ..models.base import SessionLocal
from ..models.book import Book
from ..models.reading import Reading
from ..queries.common_queries import CommonQueries

console = Console()

def find_divergent_chains(include_finished: bool = False) -> None:
    """
    Find and display divergent reading chains.
    
    Args:
        include_finished: If True, include finished books in the analysis.
                         If False, only show divergent chains for unfinished books.
    """
    session = SessionLocal()
    queries = CommonQueries()
    
    try:
        # Build a query to find duplicate previous_id values
        # Only consider unfinished books unless include_finished is True
        subquery = (
            session.query(
                Reading.id_previous,
                func.count(Reading.id).label('count')
            )
            .filter(
                Reading.id_previous.isnot(None)
            )
        )
        
        if not include_finished:
            subquery = subquery.filter(
                Reading.date_finished_actual.is_(None)
            )
            
        subquery = subquery.group_by(
            Reading.id_previous
        ).having(
            func.count(Reading.id) > 1
        ).subquery()
        
        # Get the previous readings that have multiple next readings
        divergent_points = (
            session.query(Reading)
            .join(subquery, Reading.id == subquery.c.id_previous)
            .order_by(Reading.date_est_start)
            .all()
        )
        
        if not divergent_points:
            console.print("[green]No divergent chains found for unfinished books![/green]")
            return
        
        # For each divergent point, get all the next readings
        for i, prev_reading in enumerate(divergent_points):
            # Get all next readings for this previous reading
            next_readings = (
                session.query(Reading)
                .join(Book, Reading.book_id == Book.id)
                .filter(Reading.id_previous == prev_reading.id)
            )
            
            if not include_finished:
                next_readings = next_readings.filter(
                    Reading.date_finished_actual.is_(None)
                )
                
            next_readings = next_readings.order_by(
                Reading.date_est_start.asc().nullslast(),
                Reading.id.asc()
            ).all()
            
            if not next_readings:
                continue
                
            # Create a table for this divergent point
            if i > 0:
                console.print()  # Add space between sections
                
            console.print(Rule(style="cyan"))
            console.print(f"[bold cyan]Divergent Point #{i+1}:[/bold cyan]")
            
            # Print the previous reading
            console.print(Panel(
                f"[yellow]Previous Reading (ID: {prev_reading.id})[/yellow]\n"
                f"[bold]{prev_reading.book.title}[/bold] by {prev_reading.book.author_name_first} {prev_reading.book.author_name_second}\n"
                f"Media: {prev_reading.media} | "
                f"Status: {'Finished' if prev_reading.date_finished_actual else 'Unfinished'}"
            ))
            
            # Create a table for the next readings
            table = Table(title=f"Multiple Next Readings ({len(next_readings)})")
            
            table.add_column("ID", justify="right", style="dim")
            table.add_column("Title", style="green")
            table.add_column("Media", style="blue")
            table.add_column("Est. Start", style="yellow")
            table.add_column("Est. End", style="yellow")
            table.add_column("Status", style="cyan")
            
            for reading in next_readings:
                status = "Current" if reading.date_started and not reading.date_finished_actual else \
                         "Finished" if reading.date_finished_actual else "Upcoming"
                
                table.add_row(
                    str(reading.id),
                    reading.book.title,
                    reading.media,
                    str(reading.date_est_start) if reading.date_est_start else "",
                    str(reading.date_est_end) if reading.date_est_end else "",
                    status
                )
            
            console.print(table)
            
            # Print a suggestion for fixing
            console.print(Panel(
                "[bold white]Suggestion to Fix:[/bold white]\n"
                f"To fix this divergent chain, you can set id_previous = NULL for all but one of these books.\n"
                f"Example SQL: UPDATE read SET id_previous = NULL WHERE id = <reading_id>"
            ))
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
    finally:
        session.close()

def main() -> None:
    """Main entry point for the divergent chain finder CLI"""
    parser = argparse.ArgumentParser(
        description="Find divergent reading chains (multiple books with same previous ID)"
    )
    parser.add_argument(
        "--include-finished",
        action="store_true",
        help="Include finished books in the analysis (default: only unfinished)"
    )

    args = parser.parse_args()
    find_divergent_chains(include_finished=args.include_finished)

if __name__ == "__main__":
    main()
