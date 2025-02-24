#!/usr/bin/env python3
import sys
from pathlib import Path
import argparse
from datetime import datetime
from rich.console import Console
from sqlalchemy import text
from scripts.utils.paths import get_project_paths, find_project_root
from src.models.base import engine
from jinja2 import Environment, FileSystemLoader

console = Console()

def get_monthly_readings(year: int, conn):
    """Get all books read in the specified year, grouped by month"""
    query = """
        SELECT
            strftime('%m', r.date_finished_actual) as month,
            b.id,
            b.title,
            b.author_name_first,
            b.author_name_second,
            b.page_count,
            b.word_count
        FROM read r
        JOIN books b ON r.book_id = b.id
        WHERE strftime('%Y', r.date_finished_actual) = :year
        AND r.date_finished_actual IS NOT NULL
        ORDER BY r.date_finished_actual
    """
    return conn.execute(text(query), {"year": str(year)}).fetchall()

def format_author_name(first, second):
    """Format author's full name"""
    return f"{first or ''} {second or ''}".strip() or "Unknown Author"

def process_readings_data(readings):
    """Process raw readings data into a format suitable for the template"""
    months_data = {}

    # Initialize all months with zero values
    for month in range(1, 13):
        months_data[month] = {
            'books': [],
            'total_books': 0,
            'total_pages': 0,
            'total_words': 0
        }

    for reading in readings:
        month = int(reading.month)
        book_data = {
            'id': reading.id,
            'title': reading.title,
            'author': format_author_name(reading.author_name_first, reading.author_name_second),
            'pages': reading.page_count or 0,
            'words': reading.word_count or 0
        }

        months_data[month]['books'].append(book_data)
        months_data[month]['total_books'] += 1
        months_data[month]['total_pages'] += book_data['pages']
        months_data[month]['total_words'] += book_data['words']

    return months_data

def generate_html_report(year: int):
    """Generate HTML report for the specified year"""
    # Get standardized project paths
    project_paths = get_project_paths()
    workspace = project_paths['workspace']

    # Set up Jinja2 environment
    template_dir = workspace / 'templates' / 'reports'
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('yearly_reading_report.html')

    with engine.connect() as conn:
        readings = get_monthly_readings(year, conn)

        if not readings:
            console.print(f"[red]No books found for year {year}[/red]")
            return

        # Process the data into the format expected by the template
        months_data = process_readings_data(readings)

        # Prepare monthly data for charts
        monthly_books_data = [months_data[m]['total_books'] for m in range(1, 13)]
        monthly_words_data = [months_data[m]['total_words'] for m in range(1, 13)]
        monthly_pages_data = [months_data[m]['total_pages'] for m in range(1, 13)]

        # Prepare template context
        context = {
            'year': year,
            'total_books': sum(m['total_books'] for m in months_data.values()),
            'total_pages': sum(m['total_pages'] for m in months_data.values()),
            'total_words': sum(m['total_words'] for m in months_data.values()),
            'monthly_books_data': monthly_books_data,
            'monthly_words_data': monthly_words_data,
            'monthly_pages_data': monthly_pages_data,
            'months': [
                {
                    'number': month,
                    'name': datetime(year, month, 1).strftime('%B'),
                    'books': months_data[month]['books'],
                    'total_books': months_data[month]['total_books'],
                    'total_pages': months_data[month]['total_pages'],
                    'total_words': months_data[month]['total_words']
                }
                for month in range(1, 13)
                if month in months_data
            ]
        }

        # Render the template
        html_content = template.render(**context)

        # Write the report
        reports_path = workspace / 'reports' / 'yearly'
        reports_path.mkdir(parents=True, exist_ok=True)
        report_file = reports_path / f'reading_report_{year}.html'
        report_file.write_text(html_content)
        console.print(f"[green]Report generated: {report_file}[/green]")

def main():
    parser = argparse.ArgumentParser(description='Generate yearly reading report with statistics and book covers')
    parser.add_argument('--year', '-y', type=int, default=datetime.now().year,
                       help='Year to generate report for (default: current year)')

    args = parser.parse_args()
    generate_html_report(args.year)

if __name__ == "__main__":
    main()
