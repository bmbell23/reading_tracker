"""Utility functions for displaying CLI output"""
from rich.console import Console
from rich.table import Table
from typing import Dict, Any

console = Console()

def display_chain_changes(chain_info: Dict[str, Any]) -> None:
    """
    Display the changes that will be made to the reading chain
    
    Args:
        chain_info: Dictionary containing original and new chain states
    """
    if not chain_info:
        return

    console.print("\n[bold cyan]Chain Changes Preview:[/bold cyan]")

    # Display original chain state
    console.print("\n[yellow]Original Chain:[/yellow]")
    for entry in chain_info['original']:
        console.print(entry)

    # Display new chain state
    console.print("\n[green]New Chain:[/green]")
    for entry in chain_info['new']:
        console.print(entry)