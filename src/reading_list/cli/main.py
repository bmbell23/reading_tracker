"""Main CLI entry point for reading-list commands."""
import argparse
from . import covers
from . import yearly
from . import status
from . import media_stats
from . import series_stats
from . import metadata
from . import gallery
from . import sync_covers
from . import email_report
from . import update_version
from . import inspect_chain
from . import reorder_chain
from . import update_entries
from . import update_readings
from . import chain_report
from . import generate_dashboard
from . import list_readings
from . import excel_template_cli
from . import shelf
from . import search
from . import unread_inventory
from . import owned
from . import owned_report  # Add this import

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Reading List Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Register all subparsers
    excel_template_cli.add_excel_subcommand(subparsers)  # Make sure this is registered

    # Register all subparsers
    dashboard_parser = subparsers.add_parser(
        "generate-dashboard",
        help="Generate the reading dashboard and chain report"
    )

    # Add chain-report command
    chain_report_parser = subparsers.add_parser(
        "chain-report",
        help="Generate reading chain report"
    )

    # Add update-entries command
    update_entries_parser = subparsers.add_parser(
        "update-entries",
        help="Update database entries interactively"
    )

    # Add update-readings command
    update_readings_parser = subparsers.add_parser(
        "update-readings",
        help="Update reading calculations"
    )
    update_readings_parser.add_argument('--all', action='store_true',
                                      help='Update all calculated columns')
    update_readings_parser.add_argument('--estimate', action='store_true',
                                      help='Update days_estimate column')
    update_readings_parser.add_argument('--elapsed', action='store_true',
                                      help='Update days_elapsed_to_read column')
    update_readings_parser.add_argument('--chain', action='store_true',
                                      help='Update chain dates')
    update_readings_parser.add_argument('--reread', action='store_true',
                                      help='Update reread flags')
    update_readings_parser.add_argument('--no-confirm', action='store_true',
                                      help='Skip confirmation prompt')

    # Add reorder command
    reorder_parser = subparsers.add_parser("reorder", help="Reorder readings in chains")
    reorder_parser.add_argument("reading_id", type=int, help="ID of the reading to move")
    reorder_parser.add_argument("target_id", type=int, help="ID of the reading to place after")

    # Register commands
    covers_parser = subparsers.add_parser("covers", help="Manage book covers")
    covers_subparsers = covers_parser.add_subparsers(dest="covers_command")
    update_parser = covers_subparsers.add_parser("update", help="Update cover status for all books")

    # Chain inspection parser
    chain_parser = subparsers.add_parser("chain", help="Inspect reading chains")
    chain_parser.add_argument("title_fragment", help="Part of the book title to search for")

    # Version management parser
    version_parser = subparsers.add_parser("version", help="Version management")
    version_group = version_parser.add_mutually_exclusive_group(required=True)
    version_group.add_argument('--check', action='store_true', help='Check current version')
    version_group.add_argument('--update', help='Update to specified version')

    yearly_parser = yearly.add_subparser(subparsers)
    status_parser = status.add_subparser(subparsers)
    media_stats_parser = media_stats.add_subparser(subparsers)
    series_stats_parser = series_stats.add_subparser(subparsers)
    metadata_parser = metadata.add_subparser(subparsers)
    gallery_parser = gallery.add_subparser(subparsers)
    sync_covers_parser = sync_covers.add_subparser(subparsers)
    email_report_parser = email_report.add_subparser(subparsers)

    # Register list-readings command
    list_readings_parser = list_readings.add_subparser(subparsers)

    shelf_parser = shelf.add_subparser(subparsers)
    search_parser = search.add_subparser(subparsers)

    # Add the new unread-inventory command
    unread_inventory.add_subparser(subparsers)

    # Add the owned command
    owned_parser = owned.add_subparser(subparsers)

    # Add the owned-report command
    owned_report_parser = owned_report.add_subparser(subparsers)

    args = parser.parse_args()

    if args.command == "excel":
        return excel_template_cli.handle_excel_command(args)
    elif args.command == "list-readings":
        return list_readings.handle_command(args)
    elif args.command == "generate-dashboard":
        return generate_dashboard.main()
    elif args.command == "chain-report":
        return chain_report.handle_command(args)
    elif args.command == "update-entries":
        return update_entries.main()
    elif args.command == "update-readings":
        return update_readings.main([
            '--all' if args.all else None,
            '--estimate' if args.estimate else None,
            '--elapsed' if args.elapsed else None,
            '--chain' if args.chain else None,
            '--reread' if args.reread else None,
            '--no-confirm' if args.no_confirm else None
        ])
    elif args.command == "reorder":
        return reorder_chain.main([args.reading_id, args.target_id])
    elif args.command == "covers" and args.covers_command == "update":
        return covers.update_covers()
    elif args.command == "chain":
        return inspect_chain.inspect_chain_around_book(args.title_fragment)
    elif args.command == "version":
        if hasattr(args, 'check') and args.check:
            return update_version.main(['--check'])
        elif hasattr(args, 'update') and args.update:
            return update_version.main(['--update', args.update])
    elif args.command == "yearly":
        return yearly.handle_command(args)
    elif args.command == "status":
        return status.handle_command(args)
    elif args.command == "media-stats":
        return media_stats.handle_command(args)
    elif args.command == "series-stats":
        return series_stats.handle_command(args)
    elif args.command == "metadata":
        return metadata.handle_command(args)
    elif args.command == "gallery":
        return gallery.handle_command(args)
    elif args.command == "sync-covers":
        return sync_covers.handle_command(args)
    elif args.command == "email-report":
        return email_report.handle_command(args)
    elif args.command == "shelf":
        return shelf.handle_command(args)
    elif args.command == "search":
        return search.handle_command(args)
    elif args.command == "unread-inventory":
        return unread_inventory.handle_command(args)
    elif args.command == "owned":
        return owned.handle_command(args)
    elif args.command == "owned-report":  # Add this handler
        return owned_report.handle_command(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    exit(main())
