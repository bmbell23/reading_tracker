#!/usr/bin/env python3
"""CLI command for Excel template operations."""
from pathlib import Path
from rich.console import Console
from argparse import RawDescriptionHelpFormatter
from ..exports.excel import ExcelExporter
from ..imports.excel import import_excel_data

console = Console()

def add_excel_subcommand(subparsers):
    """Add the Excel subcommand to the main parser."""
    parser = subparsers.add_parser(
        "excel",
        help="Create, export, or import reading list Excel files",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using flags:
  reading-list excel --export-current --file data.xlsx
  reading-list excel --create-template --file template.xlsx
  reading-list excel --import --file data.xlsx

  # Using subcommands:
  reading-list excel export data.xlsx
  reading-list excel create template.xlsx
  reading-list excel import data.xlsx
        """
    )

    # Add flag-style arguments
    parser.add_argument(
        "--export-current",
        action="store_true",
        help="Export current database to Excel"
    )
    parser.add_argument(
        "--create-template",
        action="store_true",
        help="Create a new Excel template"
    )
    parser.add_argument(
        "--import",
        dest="import_file",
        action="store_true",
        help="Import data from Excel file"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Excel file path"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompts"
    )

    # Add subcommand-style arguments
    subparsers_excel = parser.add_subparsers(dest="excel_command")

    create_parser = subparsers_excel.add_parser(
        "create",
        help="Create a new Excel template"
    )
    create_parser.add_argument(
        "file",
        type=Path,
        help="Output Excel file path"
    )

    export_parser = subparsers_excel.add_parser(
        "export",
        help="Export current data to Excel"
    )
    export_parser.add_argument(
        "file",
        type=Path,
        help="Output Excel file path"
    )

    import_parser = subparsers_excel.add_parser(
        "import",
        help="Import data from Excel file"
    )
    import_parser.add_argument(
        "file",
        type=Path,
        help="Input Excel file path"
    )
    import_parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompts"
    )

    return parser

def handle_excel_command(args):
    """Handle the excel command."""
    try:
        # Handle flag-style commands
        if hasattr(args, 'file') and args.file:
            if args.export_current:
                exporter = ExcelExporter()
                exporter.create_excel_file(args.file, export_current=True)
                console.print(f"[green]Database exported successfully: {args.file}[/green]")
                return 0
            elif args.create_template:
                exporter = ExcelExporter()
                exporter.create_excel_file(args.file, export_current=False)
                console.print(f"[green]Template created successfully: {args.file}[/green]")
                return 0
            elif args.import_file:
                import_excel_data(args.file, skip_confirmation=args.no_confirm)
                console.print(f"[green]Data imported successfully from: {args.file}[/green]")
                return 0

        # Handle subcommand-style commands
        if args.excel_command == "import":
            import_excel_data(args.file, skip_confirmation=args.no_confirm)
            console.print(f"[green]Data imported successfully from: {args.file}[/green]")
        elif args.excel_command in ["create", "export"]:
            exporter = ExcelExporter()
            exporter.create_excel_file(
                args.file,
                export_current=(args.excel_command == "export")
            )
            action = "Database exported" if args.excel_command == "export" else "Template created"
            console.print(f"[green]{action} successfully: {args.file}[/green]")
        else:
            console.print("[yellow]Please specify an action (--export-current, --create-template, --import) with --file, or use subcommands (create, export, import)[/yellow]")
            return 1
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def main():
    """Main entry point when run directly."""
    import argparse
    parser = argparse.ArgumentParser(
        description='Create, export, or import reading list Excel files'
    )
    subparsers = parser.add_subparsers(dest="command")
    add_excel_subcommand(subparsers)
    args = parser.parse_args()
    return handle_excel_command(args)

if __name__ == "__main__":
    exit(main())
