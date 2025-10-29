#!/usr/bin/env python3
"""
Reading Updates CLI
=================

Command-line interface for updating reading calculations and chain dates.
"""

import sys
import argparse
from rich.console import Console
from rich.prompt import Confirm
from sqlalchemy import text
from datetime import datetime

from ..operations.chain_operations import ChainOperations

console = Console()

def display_section_header(title: str):
    console.print(f"\n[bold cyan]═══ {title} ═══[/bold cyan]")

def main(args=None):
    """Main entry point for updating reading calculations"""
    if args is None:
        parser = argparse.ArgumentParser(description='Update reading calculations')
        parser.add_argument('--all', action='store_true', help='Update all calculated columns')
        parser.add_argument('--estimate', action='store_true', help='Update days_estimate column')
        parser.add_argument('--elapsed', action='store_true', help='Update days_elapsed_to_read column')
        parser.add_argument('--chain', action='store_true', help='Update chain dates')
        parser.add_argument('--reread', action='store_true', help='Update reread flags')
        parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation prompt')
        args = parser.parse_args()
    else:
        args = [arg for arg in args if arg is not None]
        parser = argparse.ArgumentParser(description='Update reading calculations')
        parser.add_argument('--all', action='store_true', help='Update all calculated columns')
        parser.add_argument('--estimate', action='store_true', help='Update days_estimate column')
        parser.add_argument('--elapsed', action='store_true', help='Update days_elapsed_to_read column')
        parser.add_argument('--chain', action='store_true', help='Update chain dates')
        parser.add_argument('--reread', action='store_true', help='Update reread flags')
        parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation prompt')
        args = parser.parse_args(args)

    # If no flags are specified, show usage
    if not any([args.all, args.estimate, args.elapsed, args.chain, args.reread]):
        parser.print_help()
        return 1

    try:
        with ChainOperations() as chain_ops:

            # Process reread detection if requested
            if args.all or args.reread:
                display_section_header("REREAD DETECTION")
                console.print("\n[dim]Checking for rereads...[/dim]\n")
                reread_changes = preview_reread_updates(chain_ops)

                if reread_changes:
                    display_reread_preview(reread_changes)
                    if args.no_confirm or Confirm.ask(f"\nUpdate {len(reread_changes)} reread flags?"):
                        updates = apply_reread_updates(chain_ops, reread_changes)
                        chain_ops.session.commit()
                        console.print(f"[green]Successfully updated {updates} reread flags![/green]")
                else:
                    console.print("[yellow]No reread updates needed[/yellow]")

            # Process each media type separately
            for media_type in ['kindle', 'hardcover', 'audio']:
                display_section_header(f"{media_type.upper()} Updates")

                # Days Estimate Updates
                if args.all or args.estimate:
                    console.print(f"\n[dim]Calculating days estimates for {media_type}[/dim]\n")
                    estimate_changes = chain_ops.preview_days_estimate_updates(media_type=media_type)
                    if estimate_changes:
                        chain_ops.display_days_estimate_preview(estimate_changes)
                        approved_changes = []

                        for change in estimate_changes:
                            if args.no_confirm or Confirm.ask(
                                f"Update estimate for '{change['title']}' from {change['current_estimate']} to {change['new_estimate']}?",
                                default=True
                            ):
                                approved_changes.append(change)

                        if approved_changes:
                            updates = chain_ops.apply_days_estimate_updates(approved_changes)
                            chain_ops.session.commit()
                            console.print(f"[green]Successfully updated {updates} estimates for {media_type}![/green]")
                        else:
                            console.print(f"[yellow]No estimates were updated for {media_type}[/yellow]")
                    else:
                        console.print(f"[yellow]No estimate updates needed for {media_type}[/yellow]")

            # Process chain updates if requested
            if args.all or args.chain:
                display_section_header("CHAIN UPDATES")

                # Process each media type separately
                for media_type in ['kindle', 'hardcover', 'audio']:
                    console.print(f"\n[dim]Updating chain dates for {media_type}...[/dim]\n")
                    chain_changes = chain_ops.preview_chain_updates(media_type=media_type)

                    if chain_changes:
                        # Display enhanced preview of changes
                        chain_ops.display_chain_updates_preview(chain_changes)

                        if args.no_confirm or Confirm.ask(f"\nUpdate {len(chain_changes)} chain dates for {media_type}?"):
                            updates = chain_ops.apply_chain_updates(chain_changes)
                            chain_ops.session.commit()
                            console.print(f"[green]Successfully updated {updates} chain dates for {media_type}![/green]")
                    else:
                        console.print(f"[yellow]No chain updates needed for {media_type}[/yellow]")

            # Always return 0 (success) even if no changes were made
            # This prevents the command from being interpreted as an error
            # when called from other commands like finish-reading
            return 0

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def preview_reread_updates(chain_ops):
    """Preview which readings should be marked as rereads"""
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
            b.author_name_first,
            b.author_name_second,
            COALESCE(r.date_started, r.date_est_start) as read_date,
            fr.first_read_date,
            fr.first_read_id,
            r.reread as current_reread_status
        FROM read r
        JOIN books b ON r.book_id = b.id
        JOIN FirstReads fr ON r.book_id = fr.book_id
        WHERE
            COALESCE(r.date_started, r.date_est_start) > fr.first_read_date
            AND r.id != fr.first_read_id
            AND (r.reread IS NULL OR r.reread = false)
            AND r.id != fr.first_read_id
        ORDER BY r.book_id, read_date
    """)

    results = chain_ops.session.execute(query).mappings().all()
    if results:
        console.print(f"\n[dim]Found {len(results)} potential rereads to update[/dim]")
    return [dict(r) for r in results]

def display_reread_preview(changes):
    """Display preview of reread updates in a formatted table"""
    from rich.table import Table

    table = Table(
        title="[bold]Readings to be Marked as Rereads[/bold]",
        show_header=True,
        header_style="bold cyan"
    )

    # Add columns
    table.add_column("RID", justify="right", style="cyan")
    table.add_column("BID", justify="right", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Author", style="white")
    table.add_column("First Read", justify="center", style="green")
    table.add_column("This Read", justify="center", style="yellow")

    for change in changes:
        # Convert string dates to datetime objects if they're strings
        first_read_date = change['first_read_date']
        if isinstance(first_read_date, str):
            first_read_date = datetime.strptime(first_read_date, '%Y-%m-%d')

        read_date = change['read_date']
        if isinstance(read_date, str):
            read_date = datetime.strptime(read_date, '%Y-%m-%d')

        # Add row to table
        table.add_row(
            str(change['id']),                                    # RID
            str(change['book_id']),                              # BID
            change['title'],                                      # Title
            f"{change.get('author_name_first', '')} {change.get('author_name_second', '')}".strip(),  # Author
            first_read_date.strftime('%Y-%m-%d'),                # First Read
            read_date.strftime('%Y-%m-%d')                       # This Read
        )

    console.print("\n")
    console.print(table)
    console.print("\n")

def apply_reread_updates(chain_ops, changes):
    """Apply reread updates to the database"""
    update_query = text("""
        UPDATE read
        SET reread = TRUE
        WHERE id = :read_id
    """)

    for change in changes:
        chain_ops.session.execute(update_query, {"read_id": change['id']})

    return len(changes)

if __name__ == "__main__":
    sys.exit(main())
