"""Utility functions for generating chain reports."""
from rich.console import Console
from ..operations.chain_operations import ChainOperations

console = Console()

def run_chain_report() -> None:
    """Generate and save a chain report after changes."""
    try:
        chain_ops = ChainOperations()
        output_file, success = chain_ops.generate_chain_report()
        if success:
            console.print(f"[green]Chain report updated: {output_file}[/green]")
        else:
            console.print(f"[yellow]Warning: {output_file}[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not generate chain report: {str(e)}[/yellow]")