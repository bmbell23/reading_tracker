"""Generate the reading dashboard and chain report."""
from rich.console import Console
from ...reports.chain_report import generate_chain_report

console = Console()

def main():
    """Generate the dashboard and chain report."""
    try:
        # Generate chain report
        console.print("[blue]Generating chain report...[/blue]")
        generate_chain_report()
        
        console.print("[green]Dashboard generation complete![/green]")
        return 0
    except Exception as e:
        console.print(f"[red]Error generating dashboard: {str(e)}[/red]")
        return 1

if __name__ == '__main__':
    main()