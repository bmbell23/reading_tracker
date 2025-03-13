"""CLI command for analyzing book cover quality."""
import argparse
from ..services.cover_analyzer import analyze_book_covers

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
    return 1 if low_quality_ids else 0