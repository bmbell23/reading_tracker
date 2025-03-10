"""Utility functions for displaying CLI output"""
from rich.console import Console
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
    console.print("\n[yellow]Original Chain State:[/yellow]")
    
    # Source chain segment
    console.print("\nSource chain segment:")
    for entry in chain_info['original']['source']['segment']:
        console.print(f"  {entry}")
    
    # Target chain segment
    console.print("\nTarget chain segment:")
    for entry in chain_info['original']['target']['segment']:
        console.print(f"  {entry}")

    # Display media change message if present
    if media_msg := chain_info['original'].get('media_change_msg'):
        console.print(media_msg)

    # Display new chain state
    console.print("\n[green]New Chain State:[/green]")
    
    # Source chain segment
    console.print("\nSource chain segment:")
    for entry in chain_info['new']['source']['segment']:
        console.print(f"  {entry}")
    
    # Target chain segment
    console.print("\nTarget chain segment:")
    for entry in chain_info['new']['target']['segment']:
        console.print(f"  {entry}")
