"""Generate yearly reading reports.

This module handles the generation of yearly reading reports in both console and HTML formats.
It processes reading data for a specific year and creates visualizations and statistics.

Key Components:
- Template handling using Jinja2
- Monthly data aggregation and processing
- Report generation in console and/or HTML format
- File permission management for generated reports

Dependencies:
- Jinja2 for HTML templating
- Rich for console output
- ReportAnalytics for data retrieval
"""

from datetime import datetime
import os
from pathlib import Path
from typing import Optional, Dict, List
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from ..utils.paths import get_project_paths, ensure_directory
from ..utils.permissions import fix_report_permissions
from ..analytics.core import ReportAnalytics

console = Console()

def _get_template_env() -> Environment:
    """Get the Jinja2 template environment.
    
    Sets up the template environment by locating the templates directory
    and initializing Jinja2's FileSystemLoader.
    
    Returns:
        Environment: Configured Jinja2 environment
    """
    project_paths = get_project_paths()
    workspace = project_paths['workspace']
    template_dir = workspace / 'src' / 'reading_list' / 'templates' / 'reports'
    return Environment(loader=FileSystemLoader(str(template_dir)))

def _prepare_monthly_data(readings: List[Dict]) -> tuple:
    """Prepare monthly data for the report.
    
    Processes raw reading data into monthly aggregates and statistics.
    
    Args:
        readings: List of reading records, each containing book details
                 and temporal information
    
    Returns:
        tuple: Contains:
            - months: List of monthly data with books and statistics
            - monthly_books_data: Array of book counts per month
            - monthly_pages_data: Array of page counts per month
            - monthly_words_data: Array of word counts per month
    """
    months = []
    monthly_books_data = [0] * 12
    monthly_pages_data = [0] * 12
    monthly_words_data = [0] * 12
    month_data_dict = {}

    for reading in readings:
        month_num = reading['month']
        month_idx = int(month_num) - 1
        month_name = datetime(2024, int(month_num), 1).strftime('%B')

        if month_num not in month_data_dict:
            month_data_dict[month_num] = {
                'name': month_name,
                'number': month_num,
                'books': [],
                'total_books': 0,
                'total_pages': 0,
                'total_words': 0
            }

        book_data = {
            'id': reading.get('book_id', ''),
            'title': reading['title'],
            'author': reading['author'],
            'status': reading.get('status', ''),
            'pages': reading['pages'],
            'words': reading['words'],
            'pages_display': f"{reading['pages']:,} pages",
            'words_display': f"{reading['words']:,} words",
            'cover_url': f"/assets/book_covers/{reading.get('book_id', '0')}.jpg"
        }
        month_data_dict[month_num]['books'].append(book_data)
        
        month_data_dict[month_num]['total_books'] += 1
        month_data_dict[month_num]['total_pages'] += reading['pages']
        month_data_dict[month_num]['total_words'] += reading['words']
        
        monthly_books_data[month_idx] += 1
        monthly_pages_data[month_idx] += reading['pages']
        monthly_words_data[month_idx] += reading['words']
    
    months = [month_data_dict[month_num] for month_num in sorted(month_data_dict.keys())]
    return months, monthly_books_data, monthly_pages_data, monthly_words_data

def generate_report(year: int, format: str = 'both', actual_only: bool = False, estimated_only: bool = False) -> Optional[str]:
    """Generate yearly reading report.
    
    Creates a comprehensive report of reading activity for the specified year.
    Can output to console, HTML, or both formats.
    
    Args:
        year: Target year for the report
        format: Output format ('console', 'html', or 'both')
        actual_only: Filter for only completed readings
        estimated_only: Filter for only planned/estimated readings
    
    Returns:
        Optional[str]: Path to generated HTML report if format includes HTML,
                      None for console-only output or if no readings found
    
    Raises:
        Exception: Propagates any errors during report generation
    """
    try:
        analytics = ReportAnalytics()
        readings = analytics.get_yearly_readings(
            year,
            actual_only=actual_only,
            estimated_only=estimated_only
        )

        if not readings:
            return None

        env = _get_template_env()
        template = env.get_template('yearly/yearly_reading_report.html')
        
        months, monthly_books_data, monthly_pages_data, monthly_words_data = _prepare_monthly_data(readings)

        total_books = sum(month['total_books'] for month in months)
        total_pages = sum(month['total_pages'] for month in months)
        total_words = sum(month['total_words'] for month in months)

        if format in ['html', 'both']:
            output = template.render(
                year=year,
                intro_text=f"A summary of your literary adventures in {year}",
                total_books=total_books,
                total_pages=total_pages,
                total_words=total_words,
                months=months,
                monthly_books_data=monthly_books_data,
                monthly_pages_data=monthly_pages_data,
                monthly_words_data=monthly_words_data
            )
            
            project_paths = get_project_paths()
            reports_dir = project_paths['workspace'] / 'reports' / 'yearly'
            
            ensure_directory(reports_dir)
            reports_dir.chmod(0o755)
            
            filename = f'{year}_reading_journey.html' if actual_only else f'{year}_reading_goals.html'
            output_file = reports_dir / filename
            
            if output_file.exists():
                try:
                    output_file.unlink()
                except PermissionError:
                    fix_report_permissions(output_file)
                    output_file.unlink()
            
            output_file.write_text(output)
            fix_report_permissions(output_file)
            
            return str(output_file)

        return None

    except Exception as e:
        raise
