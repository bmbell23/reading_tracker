#!/usr/bin/env python3
"""
Reading Chain Reorder CLI
========================

Command-line interface for reordering readings within chains.
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
import subprocess
from ..operations.chain_operations import ChainOperations
from .display_utils import display_chain_changes

console = Console()

def update_chain_data():
    """Update all reading calculations and generate new chain report"""
    try:
        # Update all reading calculations
        subprocess.run(["reading-list", "update-readings", "--all"], check=True)
        # Generate new chain report
        subprocess.run(["reading-list", "chain-report"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error updating chain data: {str(e)}[/red]")

def main(args=None):
    """Main function for reordering reading chains."""
    if args is None:
        if len(sys.argv) != 3:
            console.print(Panel(
                "Usage: python -m reading_list.cli.reorder_chain <reading_id> <target_id>\n\n"
                "Example: python -m reading_list.cli.reorder_chain 178 143  # Moves reading 178 to be after reading 143",
                title="Reading Chain Reorder",
                border_style="red"
            ))
            return
        reading_id = int(sys.argv[1])
        target_id = int(sys.argv[2])
    else:
        reading_id = args[0]
        target_id = args[1]

    chain_ops = None
    try:
        chain_ops = ChainOperations()
        success, message, chain_info = chain_ops.reorder_reading_chain(reading_id, target_id)
        
        if not success:
            console.print(f"[red]{message}[/red]")
            return

        display_chain_changes(chain_info)

        # Confirm changes
        if Confirm.ask("\nDo you want to save these changes?"):
            chain_ops.session.commit()
            console.print("[green]Chains updated successfully![/green]")
            update_chain_data()  # Replace old TBR generator with new chain updates
        else:
            chain_ops.session.rollback()
            console.print("[yellow]Changes discarded[/yellow]")

    except Exception as e:
        console.print(f"[red]Error during chain reorder: {str(e)}[/red]")
        if chain_ops and chain_ops.session:
            chain_ops.session.rollback()
    finally:
        if chain_ops:
            chain_ops.session.close()

if __name__ == "__main__":
    main()
