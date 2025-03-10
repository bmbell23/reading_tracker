"""Utility functions for displaying CLI output"""
from rich.console import Console
from typing import Dict, Any

console = Console()

def display_chain_changes(chain_info: Dict[str, Any]) -> None:
    """Display the changes that will be made to the reading chain"""
    if not chain_info or 'original' not in chain_info or 'new' not in chain_info:
        console.print("[yellow]No chain information available[/yellow]")
        return

    console.print("\n[bold cyan]Chain Changes Preview:[/bold cyan]")

    def print_chain_segment(segment, indent="  "):
        if not segment:
            console.print(f"{indent}[yellow]No books in segment[/yellow]")
            return
        for entry in segment:
            id_str = f"[cyan]{entry['id']}[/cyan]"
            media_str = f"[magenta]{entry['media']}[/magenta]"
            title_str = f"[blue]{entry['title']}[/blue]"
            console.print(f"{indent}{id_str} {media_str}: {title_str}")

    try:
        # Original state
        console.print("\n[yellow]Original Chain State:[/yellow]")
        
        console.print("\n[blue]Source chain segment (where book is being moved from):[/blue]")
        print_chain_segment(chain_info['original']['source']['segment'])
        
        console.print("\n[blue]Target chain segment (where book will be moved to):[/blue]")
        print_chain_segment(chain_info['original']['target']['segment'])

        # New state
        console.print("\n[green]New Chain State:[/green]")
        
        console.print("\n[blue]Source chain segment (after book is removed):[/blue]")
        print_chain_segment(chain_info['new']['source']['segment'])
        
        console.print("\n[blue]Target chain segment (after book is inserted):[/blue]")
        print_chain_segment(chain_info['new']['target']['segment'])

    except Exception as e:
        console.print(f"[red]Error displaying chain changes: {str(e)}[/red]")
        if isinstance(e, KeyError):
            console.print("\n[dim]Chain info structure:[/dim]")
            console.print(chain_info)
