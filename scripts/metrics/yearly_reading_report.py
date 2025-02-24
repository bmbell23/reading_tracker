#!/usr/bin/env python3
import sys
from pathlib import Path
import argparse
from datetime import datetime
from rich.console import Console
from sqlalchemy import text
from scripts.utils.paths import get_project_paths, find_project_root
from src.models.base import engine

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

def generate_html_report(year: int):
    """Generate HTML report for the specified year"""
    # Get standardized project paths
    project_paths = get_project_paths()
    workspace = project_paths['workspace']

    # Define paths relative to workspace
    covers_path = workspace / 'assets' / 'book_covers'
    reports_path = workspace / 'reports' / 'yearly'
    styles_path = workspace / 'assets' / 'styles' / 'reading_report.css'

    # Debug: Print paths
    console.print(f"Workspace: {workspace}")
    console.print(f"Covers directory: {covers_path}")
    console.print(f"Reports directory: {reports_path}")
    console.print(f"Styles path: {styles_path}")

    with engine.connect() as conn:
        readings = get_monthly_readings(year, conn)

        if not readings:
            console.print(f"[red]No books found for year {year}[/red]")
            return

        months_data = {}
        for reading in readings:
            month = int(reading.month)
            if month not in months_data:
                months_data[month] = {
                    'books': [],
                    'total_pages': 0,
                    'total_words': 0
                }

            book_id = reading.id

            # Check for book cover with multiple extensions
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                cover_file = covers_path / f"{book_id}{ext}"
                if cover_file.exists():
                    console.print(f"[green]Found cover for book {book_id}: {cover_file}[/green]")
                    # Calculate relative path from reports to covers
                    cover_path = f"../../assets/book_covers/{book_id}{ext}"
                    break
            else:
                console.print(f"[yellow]No cover found for book {book_id}[/yellow]")
                cover_path = "../../assets/book_covers/default-cover.jpg"

            months_data[month]['books'].append({
                'id': book_id,
                'title': reading.title,
                'author': format_author_name(reading.author_name_first, reading.author_name_second),
                'pages': reading.page_count or 0,
                'words': reading.word_count or 0,
                'cover_path': cover_path
            })
            months_data[month]['total_pages'] += reading.page_count or 0
            months_data[month]['total_words'] += reading.word_count or 0

        # Create reports directory if it doesn't exist
        reports_path.mkdir(parents=True, exist_ok=True)

        # Generate HTML
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reading Report {year}</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="../../assets/styles/reading_report.css">
            <script>
                window.addEventListener('load', function() {{
                    document.querySelectorAll('.book-cover').forEach(function(img) {{
                        console.log('Cover path:', img.src, 'Status:', img.complete ? 'Loaded' : 'Failed');
                    }});
                }});
            </script>
        </head>
        <body>
            <h1>Reading Report {year}</h1>
        """

        # Add month sections
        for month in range(1, 13):
            if month not in months_data:
                continue

            month_name = datetime(year, month, 1).strftime('%B')
            month_data = months_data[month]

            html_content += f"""
            <section class="month-section">
                <div class="month-header">
                    <h2 class="month-title">{month_name}</h2>
                    <div class="month-stats">
                        <div class="stat-pill books">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                            </svg>
                            <span class="stat-number">{len(month_data['books'])}</span> books
                        </div>
                        <div class="stat-pill pages">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                                <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
                            </svg>
                            <span class="stat-number">{month_data['total_pages']:,}</span> pages
                        </div>
                        <div class="stat-pill words">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M4 7V4h16v3"></path>
                                <path d="M9 20h6"></path>
                                <path d="M12 4v16"></path>
                            </svg>
                            <span class="stat-number">{month_data['total_words']:,}</span> words
                        </div>
                    </div>
                </div>
                <div class="books-grid">
            """

            for book in month_data['books']:
                html_content += f"""
                    <div class="book-card">
                        <div class="book-cover-container">
                            <img class="book-cover"
                                 src="{book['cover_path']}"
                                 alt="Cover of {book['title']}"
                                 onerror="this.src='../../assets/book_covers/default-cover.jpg';">
                        </div>
                        <div class="book-title">{book['title']}</div>
                        <div class="book-author">{book['author']}</div>
                    </div>
                """

            html_content += """
                </div>
            </section>
            """

        # Add year summary section
        html_content += f"""
            <div class="year-summary">
                <h2>{year} Reading Journey</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{sum(len(m['books']) for m in months_data.values())}</div>
                        <div class="stat-label">Books Completed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{sum(m['total_pages'] for m in months_data.values()):,}</div>
                        <div class="stat-label">Pages Read</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{sum(m['total_words'] for m in months_data.values()):,}</div>
                        <div class="stat-label">Words Read</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # Write the report
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
