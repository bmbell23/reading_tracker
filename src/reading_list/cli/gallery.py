"""CLI command for generating book cover gallery."""
import argparse
from rich.console import Console
from ..services.cover_gallery import CoverGalleryGenerator

console = Console()

def add_subparser(subparsers):
    """Add the gallery command parser to the main parser."""
    parser = subparsers.add_parser(
        "gallery",
        help="Generate book cover gallery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate cover gallery
  reading-list gallery
        """
    )
    return parser

def handle_command(args):
    """Handle the gallery command."""
    try:
        generator = CoverGalleryGenerator()
        generator.generate(debug=True)  # Added debug flag
        return 0
    except Exception as e:
        console.print(f"[red]Error generating gallery: {str(e)}[/red]")
        return 1
