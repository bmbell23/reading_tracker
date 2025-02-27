#!/usr/bin/env python3
"""
Excel Template CLI
================

Command-line interface for creating Excel templates and exporting database content.
"""

import argparse
from pathlib import Path
from reading_list.export.excel import ExcelExporter  # Changed from src.reading_list to reading_list

def main():
    parser = argparse.ArgumentParser(description='Create reading list Excel template or export current database')
    parser.add_argument('--export-current', '-e', action='store_true',
                       help='Export current database content instead of template')
    parser.add_argument('--output', '-o', type=str, default="reading_list_template.xlsx",
                       help='Output file path (default: reading_list_template.xlsx)')

    args = parser.parse_args()
    
    try:
        exporter = ExcelExporter()
        exporter.create_excel_file(args.output, args.export_current)
        print(f"{'Database exported' if args.export_current else 'Template created'} successfully: {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
