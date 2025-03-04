#!/usr/bin/env python3
"""
Reading Chain Inspector
=====================

CLI tool for inspecting the chain of readings around a specific book.
Shows previous and upcoming books in the reading sequence.
"""

import sys
import argparse
from rich.console import Console
from rich.rule import Rule

from ..models.base import SessionLocal
from ..models.book import Book
from ..models.reading import Reading
from ..queries.common_queries import CommonQueries

console = Console()

def create_section_header(title: str, style: str = "bold cyan") -> None:
    """Create a visually distinct section header"""
    console.print("\n")  # Add extra space before section
    console.print(Rule(style=style))
    console.print(f"[{style}]{title}[/{style}]", justify="center")
    console.print(Rule(style=style))

def inspect_chain_around_book(title_fragment: str) -> None:
    """Display the reading chain around a book"""
    queries = CommonQueries()
    session = SessionLocal()

    try:
        # Find all readings of matching books
        readings = (session.query(Reading)
                  .join(Book)
                  .filter(Book.title.ilike(f"%{title_fragment}%"))
                  .all())

        if not readings:
            console.print(f"[red]No reading found with title containing '{title_fragment}'[/red]")
            return

        # If multiple readings found, let user select one
        target = readings[0]  # Default to first reading
        if len(readings) > 1:
            console.print("\n[yellow]Multiple readings found:[/yellow]")
            for idx, reading in enumerate(readings, 1):
                console.print(f"{idx}. Reading ID: {reading.id}")
                queries.print_reading(reading)
                console.print()  # Add blank line between entries
            
            while True:
                choice = console.input("\nSelect reading number (or press Enter for first): ")
                if not choice:  # User pressed Enter
                    break
                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(readings):
                        target = readings[choice_idx]
                        break
                    else:
                        console.print("[red]Invalid selection. Please try again.[/red]")
                except ValueError:
                    console.print("[red]Please enter a valid number.[/red]")

        # Get chain of books
        before_chain = []
        after_chain = []
        
        # Build chain backwards
        current = target
        while current and current.id_previous:
            previous = session.query(Reading).get(current.id_previous)
            if previous:
                before_chain.append(previous)
                current = previous
            else:
                break

        # Build chain forwards
        current = target
        while current:
            next_reading = (session.query(Reading)
                          .filter(Reading.id_previous == current.id)
                          .first())
            if next_reading:
                after_chain.append(next_reading)
                current = next_reading
            else:
                break

        # Print previous books
        if before_chain:
            create_section_header("📚 PREVIOUS BOOKS", "blue")
            for reading in reversed(before_chain):  # Show in chronological order
                queries.print_reading(reading, show_actual_dates=True)
                console.print()  # Add blank line between entries

        # Print target book
        create_section_header("🎯 TARGET BOOK", "yellow")
        queries.print_reading(target, show_actual_dates=False)
        console.print()  # Add blank line after target

        # Print next books
        if after_chain:
            create_section_header("📚 NEXT BOOKS", "green")
            for reading in after_chain:
                queries.print_reading(reading)
                console.print()  # Add blank line between entries

        # Print summary
        total_books = len(before_chain) + 1 + len(after_chain)
        console.print(Rule(style="cyan"))
        console.print(
            f"[bold white]Chain Summary[/bold white]\n"
            f"Previous Books: [blue]{len(before_chain)}[/blue]\n"
            f"Next Books: [green]{len(after_chain)}[/green]\n"
            f"Total in Chain: [yellow]{total_books}[/yellow]"
        )
        console.print(Rule(style="cyan"))

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
    finally:
        session.close()

def main() -> None:
    """Main entry point for the chain inspector CLI"""
    parser = argparse.ArgumentParser(
        description="Inspect the chain of readings around a specific book"
    )
    parser.add_argument(
        "title_fragment",
        help="Part of the book title to search for"
    )

    args = parser.parse_args()
    inspect_chain_around_book(args.title_fragment)

if __name__ == "__main__":
    main()
