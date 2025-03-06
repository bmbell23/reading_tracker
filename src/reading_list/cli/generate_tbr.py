"""CLI command for generating TBR report."""
import argparse
from pathlib import Path
from rich.console import Console
from ..reports.tbr_report import generate_tbr_report
from ..utils.permissions import fix_report_permissions

console = Console()

def add_subparser(subparsers):
    """Add the generate-tbr command parser to the main parser."""
    parser = subparsers.add_parser(
        "generate-tbr",
        help="Generate TBR (To Be Read) report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate TBR report
  reading-list generate-tbr
        """
    )
    return parser

def handle_command(args):
    """Handle the generate-tbr command."""
    try:
        console.print("[blue]Generating TBR report...[/blue]")
        output_file = generate_tbr_report()
        
        if output_file:
            output_path = Path(output_file)
            console.print(f"[green]Report generated: {output_file}[/green]")
            fix_report_permissions(output_path)
        return 0
    except Exception as e:
        console.print(f"[red]Error generating TBR report: {str(e)}[/red]")
        return 1