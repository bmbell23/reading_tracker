"""CLI command for analyzing book cover quality."""
import argparse
import subprocess
from rich.console import Console
from rich.prompt import Confirm
from ..services.cover_analyzer import analyze_book_covers

console = Console()

def add_subparser(subparsers):
    """Add the analyze-covers command parser."""
    parser = subparsers.add_parser(
        "analyze-covers",
        help="Analyze book cover image quality",
        description="Analyze book cover images and identify low-quality covers"
    )
    return parser

def handle_command(args):
    """Handle the analyze-covers command."""
    low_quality_ids = analyze_book_covers()
    
    if low_quality_ids:
        if Confirm.ask("\nWould you like to fetch new covers for these books?"):
            # Convert IDs to strings and join with spaces
            id_str = " ".join(str(id) for id in low_quality_ids)
            # Run fetch-cover command
            result = subprocess.run(["reading-list", "fetch-cover"] + id_str.split())
            return result.returncode
    
    return 1 if low_quality_ids else 0