"""
Reading Inspector CLI
===================

Command-line interface for inspecting details of specific reading sessions.
"""

import argparse
from rich.console import Console

from ..queries.common_queries import CommonQueries
from .display import display_reading_details

console = Console()

def main() -> int:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Inspect details of a specific reading session"
    )
    parser.add_argument(
        "reading_id",
        type=int,
        help="ID of the reading session to inspect"
    )

    args = parser.parse_args()
    
    queries = CommonQueries()
    reading_details = queries.get_reading_details(args.reading_id)
    display_reading_details(reading_details)
    
    return 0 if reading_details else 1

if __name__ == "__main__":
    raise SystemExit(main())
