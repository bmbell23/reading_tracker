#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, date

from ..utils.paths import get_project_paths
from ..analytics.core import ReadingAnalytics
from rich.console import Console
from rich.table import Table
from jinja2 import Environment, FileSystemLoader

console = Console()

def generate_report(year: int, output_format: str = 'both'):
    """Generate projected readings report in specified format (console, html, or both)"""
    analytics = ReadingAnalytics()
    readings = analytics.get_projected_readings(year)

    if not readings:
        console.print(f"[red]No projected books found for year {year}[/red]")
        return

    # Remove the yearly stats section since it's not needed for projections
    months_data = analytics.process_readings_data(readings)
    
    # Get statistics
    monthly_books_data = [months_data[m]['total_books'] for m in range(1, 13)]
    monthly_words_data = [months_data[m]['total_words'] for m in range(1, 13)]
    monthly_pages_data = [months_data[m]['total_pages'] for m in range(1, 13)]
    
    cumulative_books, cumulative_words, cumulative_pages = analytics.calculate_cumulative_stats(months_data)

    if output_format in ['console', 'both']:
        print_console_report(months_data, monthly_books_data, monthly_words_data, monthly_pages_data)

    if output_format in ['html', 'both']:
        return generate_html_report(year, months_data, monthly_books_data, monthly_words_data, 
                           monthly_pages_data, cumulative_books, cumulative_words, cumulative_pages)

def print_console_report(months_data: dict, monthly_books: list, 
                        monthly_words: list, monthly_pages: list):
    """Print report to console using Rich tables"""
    console.print(f"\n[bold cyan]Projected Reading Report[/bold cyan]")
    
    # Create summary table
    summary_table = Table(title="Monthly Summary")
    summary_table.add_column("Month")
    summary_table.add_column("Books", justify="right")
    summary_table.add_column("Pages", justify="right")
    summary_table.add_column("Words", justify="right")

    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']

    for idx, month in enumerate(month_names):
        summary_table.add_row(
            month,
            str(monthly_books[idx]),
            f"{monthly_pages[idx]:,}",
            f"{monthly_words[idx]:,}"
        )

    console.print(summary_table)

    # Print detailed monthly breakdowns
    for month_num in range(1, 13):
        if months_data[month_num]['books']:
            console.print(f"\n[bold]{month_names[month_num-1]}[/bold]")
            month_table = Table(show_header=True, header_style="bold")
            month_table.add_column("Title")
            month_table.add_column("Author")
            month_table.add_column("Pages", justify="right")
            month_table.add_column("Est. Finish")

            for book in months_data[month_num]['books']:
                est_end_date = book['est_end'].strftime('%Y-%m-%d') if book['est_end'] else 'TBD'
                month_table.add_row(
                    book['title'],
                    book['author'],
                    str(book['pages']),
                    est_end_date
                )

            console.print(month_table)

def generate_html_report(year: int, months_data: dict, monthly_books: list,
                        monthly_words: list, monthly_pages: list,
                        cumulative_books: list, cumulative_words: list,
                        cumulative_pages: list):
    """Generate HTML report using template"""
    project_paths = get_project_paths()
    
    # Use the correct template directory from project_paths
    template_dir = project_paths['projected_templates']
    output_dir = project_paths['workspace'] / 'reports' / 'projected'
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template('projected_readings.html')

    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']

    html_content = template.render(
        year=year,
        months_data=months_data,
        month_names=month_names,
        monthly_books=monthly_books,
        monthly_words=monthly_words,
        monthly_pages=monthly_pages,
        cumulative_books=cumulative_books,
        cumulative_words=cumulative_words,
        cumulative_pages=cumulative_pages,
        generation_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    output_file = output_dir / 'projected_readings.html'
    output_file.write_text(html_content)
    console.print(f"\n[green]HTML report generated: {output_file}[/green]")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate projected readings report")
    parser.add_argument("year", type=int, help="Year to generate report for")
    parser.add_argument("--format", choices=['console', 'html', 'both'], 
                        default='both', help="Output format")
    args = parser.parse_args()

    generate_report(args.year, args.format)
