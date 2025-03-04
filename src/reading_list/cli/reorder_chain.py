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

from reading_list.operations.chain_operations import ChainOperations
from reading_list.utils.display import display_reading_group
from reading_list.utils.chain_report import run_chain_report

console = Console()

def display_chain_changes(chain_info: dict) -> None:
    """Display the before and after state of chains"""
    # Show original state
    console.print("\n[bold]Current chain orders:[/bold]")
    
    console.print("\n[bold cyan]Source Chain (before move):[/bold cyan]")
    display_reading_group(chain_info['original']['source']['segment'], "Source Chain Segment")
    
    console.print("\n[bold cyan]Target Chain (before move):[/bold cyan]")
    display_reading_group(chain_info['original']['target']['segment'], "Target Chain Segment")

    # Show new state
    console.print("\n[bold]Proposed new chain orders:[/bold]")
    
    if chain_info['new']['source']['segment']:
        console.print("\n[bold green]Source Chain (after move):[/bold green]")
        display_reading_group(chain_info['new']['source']['segment'], "Updated Source Chain Segment")

    console.print("\n[bold green]Target Chain (after move):[/bold green]")
    display_reading_group(chain_info['new']['target']['segment'], "Updated Target Chain Segment")

def main(args=None):
    """Main CLI entry point.
    
    Args:
        args: Optional list of arguments [reading_id, target_id]. If None, uses sys.argv.
    """
    if args is None:
        if len(sys.argv) != 3:
            console.print(Panel(
                "[red]Usage: python -m reading_list.cli.reorder_chain <reading_id_to_move> <reading_id_to_place_after>[/red]\n" +
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

    try:
        chain_ops = ChainOperations()
        success, message, chain_info = chain_ops.reorder_reading_chain(reading_id, target_id)
        
        if not success:
            console.print(f"[red]{message}[/red]")
            return

        display_chain_changes(chain_info)

        # Confirm changes
        if Confirm.ask("\nDo you want to save these changes?"):
            chain_info['session'].commit()
            console.print("[green]Chains updated successfully![/green]")
            run_chain_report()
        else:
            chain_info['session'].rollback()
            console.print("[yellow]Changes cancelled[/yellow]")
            
    except ValueError:
        console.print("[red]Reading IDs must be numbers[/red]")
    finally:
        if chain_info and 'session' in chain_info:
            chain_info['session'].close()

if __name__ == "__main__":
    main()
