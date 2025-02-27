#!/usr/bin/env python3
"""
Database Transfer CLI
===================

Command-line interface for database transfer operations.
"""

import argparse
from pathlib import Path
from rich.prompt import Confirm

from reading_list.database.transfer import DatabaseTransfer

def main():
    parser = argparse.ArgumentParser(description="Database transfer utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Export parser
    export_parser = subparsers.add_parser("export", help="Export the database")
    export_parser.add_argument("--format", choices=["sqlite", "sql", "csv"], 
                             default="sqlite", help="Export format")
    export_parser.add_argument("--output", type=Path, help="Output path")

    # Import parser
    import_parser = subparsers.add_parser("import", help="Import the database")
    import_parser.add_argument("input", type=Path, help="Input file path")
    import_parser.add_argument("--no-backup", action="store_true", 
                             help="Skip backup before import")

    args = parser.parse_args()
    db_transfer = DatabaseTransfer()

    try:
        if args.command == "export":
            db_transfer.export_database(args.output, args.format)
        elif args.command == "import":
            if not args.no_backup:
                if not Confirm.ask("Create backup before import?"):
                    return
            db_transfer.import_database(args.input, not args.no_backup)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
