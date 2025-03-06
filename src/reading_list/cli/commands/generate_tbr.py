import click
from ...reports.tbr_report import generate_tbr_report
from rich.console import Console

console = Console()

@click.command()
def tbr():
    """Generate TBR (To Be Read) report."""
    try:
        output_file = generate_tbr_report()
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1
    return 0

if __name__ == '__main__':
    tbr()