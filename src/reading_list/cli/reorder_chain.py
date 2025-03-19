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
from ..models.reading import Reading
from .display_utils import display_chain_changes

console = Console()

def update_chain_data(chain_ops: ChainOperations, reading_id: int):
    """Update all reading calculations and generate new chain report"""
    try:
        # Ensure the session is committed and cleared
        chain_ops.session.commit()
        chain_ops.session.expire_all()

        # First update the chain dates directly using our ChainOperations instance
        media_type = chain_ops.session.get(Reading, reading_id).media.lower()
        chain_changes = chain_ops.preview_chain_updates(media_type=media_type)
        if chain_changes:
            updates = chain_ops.apply_chain_updates(chain_changes)
            chain_ops.session.commit()
            console.print(f"[green]Successfully updated {updates} chain dates![/green]")

        # Then run the full update command with better error handling
        try:
            result = subprocess.run(
                ["reading-list", "update-readings", "--chain", "--no-confirm"],
                check=False,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                console.print("[red]Error during reading calculations update:[/red]")
                if result.stderr and result.stderr.strip():
                    console.print(f"[red]Error output:[/red]\n{result.stderr}")
                if result.stdout and result.stdout.strip():
                    console.print(f"[yellow]Standard output:[/yellow]\n{result.stdout}")
                console.print(f"[yellow]Return code: {result.returncode}[/yellow]")
            else:
                console.print("[green]Reading calculations updated successfully[/green]")

                # Generate new chain report
                report_result = subprocess.run(
                    ["reading-list", "chain-report"],
                    check=False,
                    capture_output=True,
                    text=True
                )

                if report_result.returncode != 0:
                    console.print("[red]Error generating chain report:[/red]")
                    if report_result.stderr:
                        console.print(f"[red]Error output:[/red]\n{report_result.stderr}")
                    return

                console.print("[green]Chain report generated successfully[/green]")

        except subprocess.SubprocessError as e:
            console.print(f"[red]Error executing update command: {str(e)}[/red]")
            return

    except Exception as e:
        console.print(f"[red]Error updating chain data: {str(e)}[/red]")
        if hasattr(e, 'stderr'):
            console.print(f"[dim]{e.stderr}[/dim]")
        if hasattr(e, 'stdout'):
            console.print(f"[dim]{e.stdout}[/dim]")

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
            update_chain_data(chain_ops, reading_id)  # Pass chain_ops instance
        else:
            chain_ops.session.rollback()
            console.print("[yellow]Changes discarded[/yellow]")

    except Exception as e:
        console.print(f"[red]Error during chain reorder: {str(e)}[/red]")
        if chain_ops and chain_ops.session:
            chain_ops.session.rollback()
    finally:
        if chain_ops and chain_ops.session:
            chain_ops.session.close()

if __name__ == "__main__":
    main()
