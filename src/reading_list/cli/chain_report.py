"""
Reading Chain Report CLI
======================

Command-line interface for generating reading chain reports.
"""

from ..reports.chain_report import generate_chain_report
from rich.console import Console

console = Console()

def main():
    """Main CLI entry point"""
    try:
        generate_chain_report()
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
