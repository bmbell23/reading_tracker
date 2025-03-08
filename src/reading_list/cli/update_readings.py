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

def main(args=None):
    """Main entry point for updating reading calculations"""
    if args is None:
        parser = argparse.ArgumentParser(description='Update reading calculations')
        parser.add_argument('--all', action='store_true', help='Update all calculated columns')
        parser.add_argument('--estimate', action='store_true', help='Update days_estimate column')
        parser.add_argument('--elapsed', action='store_true', help='Update days_elapsed_to_read column')
        parser.add_argument('--chain', action='store_true', help='Update chain dates')
        parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation prompt')
        args = parser.parse_args()
    else:
        # Filter out None values from the args list
        args = [arg for arg in args if arg is not None]
        parser = argparse.ArgumentParser(description='Update reading calculations')
        parser.add_argument('--all', action='store_true', help='Update all calculated columns')
        parser.add_argument('--estimate', action='store_true', help='Update days_estimate column')
        parser.add_argument('--elapsed', action='store_true', help='Update days_elapsed_to_read column')
        parser.add_argument('--chain', action='store_true', help='Update chain dates')
        parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation prompt')
        args = parser.parse_args(args)

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
                
                # Preview days estimate changes
                estimate_changes = chain_ops.preview_days_estimate_updates()
                if estimate_changes:
                    chain_ops.display_days_estimate_preview(estimate_changes)
                    if args.no_confirm or Confirm.ask(f"\nUpdate {len(estimate_changes)} estimates?"):
                        updates = chain_ops.apply_days_estimate_updates(estimate_changes)
                        chain_ops.session.commit()
                        changes_made = True
                        console.print(f"[green]Successfully updated {updates} estimates![/green]")
                else:
                    console.print("[yellow]No estimate updates needed[/yellow]")

            # Reading Chain Updates
            if args.all or args.chain:
                display_section_header("Reading Chain Updates")
                console.print("[dim]Updating estimated start/end dates for books in reading chains[/dim]\n")
                
                # Preview chain date changes
                chain_changes = chain_ops.preview_chain_updates()
                if chain_changes:
                    chain_ops.display_chain_updates_preview(chain_changes)
                    if args.no_confirm or Confirm.ask(f"\nUpdate {len(chain_changes)} chain dates?"):
                        updates = chain_ops.apply_chain_updates(chain_changes)
                        chain_ops.session.commit()
                        changes_made = True
                        console.print(f"[green]Successfully updated {updates} chain dates![/green]")
                else:
                    console.print("[yellow]No chain date updates needed[/yellow]")

            if changes_made:
                console.print("\n[green]All updates completed successfully![/green]")
            else:
                console.print("\n[yellow]No updates were needed or applied[/yellow]")

    except Exception as e:
        console.print(f"\n[red]Error updating readings: {str(e)}[/red]")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
