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
            'intro_text': (
                f"A visual journey through my reading adventures in {year}. "
                "Each book, word, and page contributing to a year of discovery and growth."
            ),
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

def generate_report(year: int, format: str = 'both'):
    """Generate report in the specified format(s)"""
    if format in ['html', 'both']:
        generate_html_report(year)

    if format in ['pdf', 'both']:
        # First generate HTML, then convert to PDF
        project_paths = get_project_paths()
        workspace = project_paths['workspace']
        html_file = workspace / 'reports' / 'yearly' / f'reading_report_{year}.html'
        pdf_file = workspace / 'reports' / 'yearly' / f'reading_report_{year}.pdf'

        if html_file.exists():
            try:
                from weasyprint import HTML, CSS
                HTML(filename=str(html_file)).write_pdf(str(pdf_file))
                console.print(f"[green]PDF report generated: {pdf_file}[/green]")
            except ImportError:
                console.print("[yellow]WeasyPrint not installed. Skipping PDF generation.[/yellow]")
                console.print("To enable PDF support, install WeasyPrint: pip install weasyprint")
        else:
            console.print("[red]HTML report not found. Generate HTML report first.[/red]")

def main():
    parser = argparse.ArgumentParser(description='Generate yearly reading report with statistics and book covers')
    parser.add_argument('year', type=int, nargs='?', default=datetime.now().year,
                       help='Year to generate report for (default: current year)')
    parser.add_argument('--format', '-f', choices=['html', 'pdf', 'both'], default='both',
                       help='Output format (default: both)')

    args = parser.parse_args()
    generate_report(args.year, args.format)

if __name__ == "__main__":
    main()
