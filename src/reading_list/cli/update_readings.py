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
            
            # Process each media type separately
            for media_type in ['kindle', 'hardcover', 'audio']:
                display_section_header(f"{media_type.upper()} Updates")
                
                # Days Estimate Updates
                if args.all or args.estimate:
                    console.print(f"\n[dim]Calculating days estimates for {media_type}[/dim]\n")
                    estimate_changes = chain_ops.preview_days_estimate_updates(media_type=media_type)
                    if estimate_changes:
                        chain_ops.display_days_estimate_preview(estimate_changes)
                        if args.no_confirm or Confirm.ask(f"\nUpdate {len(estimate_changes)} estimates for {media_type}?"):
                            updates = chain_ops.apply_days_estimate_updates(estimate_changes)
                            chain_ops.session.commit()
                            changes_made = True
                            console.print(f"[green]Successfully updated {updates} estimates for {media_type}![/green]")
                    else:
                        console.print(f"[yellow]No estimate updates needed for {media_type}[/yellow]")

                # Reading Chain Updates
                if args.all or args.chain:
                    console.print(f"\n[dim]Updating chain dates for {media_type}[/dim]\n")
                    chain_changes = chain_ops.preview_chain_updates(media_type=media_type)
                    if chain_changes:
                        chain_ops.display_chain_updates_preview(chain_changes)
                        if args.no_confirm or Confirm.ask(f"\nUpdate {len(chain_changes)} chain dates for {media_type}?"):
                            updates = chain_ops.apply_chain_updates(chain_changes)
                            chain_ops.session.commit()
                            changes_made = True
                            console.print(f"[green]Successfully updated {updates} chain dates for {media_type}![/green]")
                    else:
                        console.print(f"[yellow]No chain updates needed for {media_type}[/yellow]")

            return 0 if changes_made else 1

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
