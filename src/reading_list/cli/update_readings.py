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

from ..operations.chain_operations import ChainOperations

console = Console()

def display_section_header(title: str):
    console.print(f"\n[bold cyan]═══ {title} ═══[/bold cyan]")

def main():
    parser = argparse.ArgumentParser(description='Update reading calculations')
    parser.add_argument('--all', action='store_true', help='Update all calculated columns')
    parser.add_argument('--estimate', action='store_true', help='Update days_estimate column')
    parser.add_argument('--elapsed', action='store_true', help='Update days_elapsed_to_read column')
    parser.add_argument('--chain', action='store_true', help='Update chain dates')
    parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()

    # If no flags are specified, show usage
    if not any([args.all, args.estimate, args.elapsed, args.chain]):
        parser.print_help()
        return 1

    try:
        with ChainOperations() as chain_ops:
            changes_made = False
            
            # Days Estimate Updates
            if args.all or args.estimate:
                display_section_header("Days Estimate Updates")
                console.print("[dim]Calculating days estimates based on word count and media type[/dim]\n")
                updates, skipped = chain_ops.update_days_estimate()
                if updates > 0:
                    if args.no_confirm or Confirm.ask(f"\nUpdate {updates} estimates?"):
                        chain_ops.session.commit()
                        changes_made = True
                        console.print(f"[green]Successfully updated {updates} estimates![/green]")
                        if skipped > 0:
                            console.print(f"[yellow]Skipped {skipped} entries due to missing data[/yellow]")
                    else:
                        chain_ops.session.rollback()
                else:
                    console.print("[yellow]No estimate updates needed[/yellow]")

            # Days Elapsed Updates
            if args.all or args.elapsed:
                display_section_header("Days Elapsed Updates")
                console.print("[dim]Calculating actual days taken to read for completed books[/dim]\n")
                updates, skipped = chain_ops.update_days_elapsed()
                if updates > 0:
                    if args.no_confirm or Confirm.ask(f"\nUpdate {updates} elapsed times?"):
                        chain_ops.session.commit()
                        changes_made = True
                        console.print(f"[green]Successfully updated {updates} elapsed times![/green]")
                        if skipped > 0:
                            console.print(f"[yellow]Skipped {skipped} entries due to missing data[/yellow]")
                    else:
                        chain_ops.session.rollback()
                else:
                    console.print("[yellow]No elapsed time updates needed[/yellow]")

            # Reading Chain Updates
            if args.all or args.chain:
                display_section_header("Reading Chain Updates")
                console.print("[dim]Updating estimated start/end dates for books in reading chains[/dim]\n")
                updates, skipped = chain_ops.update_all_chain_dates()
                if updates > 0:
                    if args.no_confirm or Confirm.ask(f"\nUpdate {updates} chain dates?"):
                        chain_ops.session.commit()
                        changes_made = True
                        console.print(f"[green]Successfully updated {updates} chain dates![/green]")
                        if skipped > 0:
                            console.print(f"[yellow]Skipped {skipped} entries due to missing data[/yellow]")
                    else:
                        chain_ops.session.rollback()

    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())