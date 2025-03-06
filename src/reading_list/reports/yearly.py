"""Generate yearly reading reports."""
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from ..utils.paths import get_project_paths
from ..analytics.core import ReportAnalytics

console = Console()

def _get_template_env() -> Environment:
    """Get the Jinja2 template environment."""
    project_paths = get_project_paths()
    workspace = project_paths['workspace']
    template_dir = workspace / 'src' / 'reading_list' / 'templates' / 'reports'
    return Environment(loader=FileSystemLoader(str(template_dir)))

def _prepare_monthly_data(readings: List[Dict]) -> tuple:
    """Prepare monthly data for the report."""
    months = []
    monthly_books_data = [0] * 12  # Initialize with zeros
    monthly_pages_data = [0] * 12
    monthly_words_data = [0] * 12
    
    # Create a dict to store month data
    month_data_dict = {}
    
    for reading in readings:
        # Get month number (1-based) and subtract 1 for 0-based array indexing
        month_num = reading['month']
        month_idx = int(month_num) - 1
        month_name = datetime(2024, int(month_num), 1).strftime('%B')
        
        # Initialize month data if not exists
        if month_num not in month_data_dict:
            month_data_dict[month_num] = {
                'name': month_name,
                'number': month_num,  # Add this for reference
                'books': [],
                'total_books': 0,
                'total_pages': 0,
                'total_words': 0
            }
        
        # Add book to month data
        month_data_dict[month_num]['books'].append({
            'id': reading.get('book_id', ''),  # Add ID for book cover
            'title': reading['title'],
            'author': reading['author'],
            'status': reading.get('status', '')
        })
        
        # Update monthly totals
        month_data_dict[month_num]['total_books'] += 1
        month_data_dict[month_num]['total_pages'] += reading['pages']
        month_data_dict[month_num]['total_words'] += reading['words']
        
        # Update the monthly data arrays
        monthly_books_data[month_idx] += 1
        monthly_pages_data[month_idx] += reading['pages']
        monthly_words_data[month_idx] += reading['words']
    
    # Convert dict to sorted list for the template
    months = [month_data_dict[month_num] for month_num in sorted(month_data_dict.keys())]
    
    return months, monthly_books_data, monthly_pages_data, monthly_words_data

def generate_report(year: int, format: str = 'both', actual_only: bool = False, estimated_only: bool = False) -> Optional[str]:
    """Generate yearly reading report.
    
    Args:
        year: Year to generate report for
        format: Output format ('console', 'html', or 'both')
        actual_only: Show only readings with actual dates
        estimated_only: Show only readings with estimated dates
    
    Returns:
        Path to generated HTML report if format includes HTML, None otherwise
    """
    try:
        analytics = ReportAnalytics()
        readings = analytics.get_yearly_readings(
            year,
            actual_only=actual_only,
            estimated_only=estimated_only
        )

        if not readings:
            console.print(f"[yellow]No readings found for year {year}[/yellow]")
            return None

        # Add debug prints
        env = _get_template_env()
        console.print(f"[blue]Loading template from: {env.loader.searchpath}[/blue]")
        
        # Change this line to use the correct template path
        template = env.get_template('yearly/yearly_reading_report.html')
        
        # Calculate totals
        total_books = len(readings)
        total_pages = sum(reading.get('pages', 0) for reading in readings)
        total_words = sum(reading.get('words', 0) for reading in readings)

        # Prepare monthly data with the new structure
        months, monthly_books_data, monthly_pages_data, monthly_words_data = _prepare_monthly_data(readings)

        # Console output if requested
        if format in ['console', 'both']:
            console.print(f"\n[bold]Reading Report {year}[/bold]")
            console.print(f"Total Books: {total_books}")
            console.print(f"Total Pages: {total_pages:,}")
            console.print(f"Total Words: {total_words:,}")
            
            for month in months:
                console.print(f"\n[bold]{month['name']}[/bold]")
                console.print(f"Books: {month['total_books']}")
                console.print(f"Pages: {month['total_pages']:,}")
                console.print(f"Words: {month['total_words']:,}")
                
                for book in month['books']:
                    console.print(f"- {book['title']} by {book['author']}")

        # HTML output if requested
        if format in ['html', 'both']:
            output = template.render(
                year=year,
                intro_text=f"A summary of your literary adventures in {year}",
                total_books=total_books,
                total_pages=total_pages,
                total_words=total_words,
                months=months,
                # Add the new monthly data arrays for the charts
                monthly_books_data=monthly_books_data,
                monthly_pages_data=monthly_pages_data,
                monthly_words_data=monthly_words_data
            )
            
            # Save the report
            project_paths = get_project_paths()
            reports_dir = project_paths['workspace'] / 'reports' / 'yearly'
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = reports_dir / f'reading_report_{year}.html'
            output_file.write_text(output)
            
            return str(output_file)

        return None

    except Exception as e:
        console.print(f"[red]Error generating report: {str(e)}[/red]")
        raise
