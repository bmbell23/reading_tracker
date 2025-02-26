#!/usr/bin/env python3
import os
from datetime import date, datetime
from pathlib import Path
from sqlalchemy import text
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from scripts.utils.paths import get_project_paths, find_project_root
from src.models.base import engine

console = Console()

def get_current_readings(conn):
    """Get all all curnngs"""
    query = """
        SELECT
            r.id as read_id,
            r.media,
            r.date_started,
            r.date_finished_actual,
            b.id as book_id,
            b.id as book_id,
            b.title
        FROM read r
        JOIN books b ON r.book_id = b.id
        WHERE r.date_started IS NOT NULL
        AND r.date_finished_actual IS NULL
        ORDER BY r.media;
    """
    results = conn.execute(text(query)).fetchall()

    # Debug output
    console.print("\n[bold]Current Readings Found:[/bold]")
    for r in results:
        console.print(f"ID: {r.read_id}, Title: {r.title}, Media: {r.media}")
        console.print(f"Started: {r.date_started}, Finished: {r.date_finished_actual}")

    return results

def get_reading_chain(conn, reading_id, direction='both', limit=10):
    """Get the reading chain around a specific reading"""
    query = """
        WITH RECURSIVE backward AS (
            -- Initial reading
            SELECT
                r.id as read_id,
                r.id_previous,
                r.book_id,
                r.media,
                r.date_started,
                r.date_finished_actual,
                r.date_est_start,
                r.date_est_end,
                b.title,
                b.author_name_first,
                b.author_name_second,
                0 as position
            FROM read r
            JOIN books b ON r.book_id = b.id
            WHERE r.id = :reading_id

            UNION ALL

            -- Previous books (limit to 1)
            SELECT
                r.id,
                r.id_previous,
                r.book_id,
                r.media,
                r.date_started,
                r.date_finished_actual,
                r.date_est_start,
                r.date_est_end,
                b.title,
                b.author_name_first,
                b.author_name_second,
                bw.position - 1
            FROM read r
            JOIN books b ON r.book_id = b.id
            JOIN backward bw ON bw.id_previous = r.id
            WHERE bw.position > -1
        ),
        forward AS (
            -- Initial reading (already included in backward)
            SELECT
                r.id as read_id,
                r.id_previous,
                r.book_id,
                r.media,
                r.date_started,
                r.date_finished_actual,
                r.date_est_start,
                r.date_est_end,
                b.title,
                b.author_name_first,
                b.author_name_second,
                0 as position
            FROM read r
            JOIN books b ON r.book_id = b.id
            WHERE r.id = :reading_id

            UNION ALL

            -- Next books (no limit)
            SELECT
                r.id,
                r.id_previous,
                r.book_id,
                r.media,
                r.date_started,
                r.date_finished_actual,
                r.date_est_start,
                r.date_est_end,
                b.title,
                b.author_name_first,
                b.author_name_second,
                fw.position + 1
            FROM read r
            JOIN books b ON r.book_id = b.id
            JOIN forward fw ON r.id_previous = fw.read_id
            WHERE fw.position < 100  -- Large number to get all upcoming books
        )
        SELECT DISTINCT
            read_id,
            id_previous,
            book_id,
            media,
            date_started,
            date_finished_actual,
            date_est_start,
            date_est_end,
            title,
            author_name_first,
            author_name_second,
            position,
            (SELECT r2.id FROM read r2 WHERE r2.id_previous = read_id) as next_id
        FROM (
            SELECT * FROM backward
            UNION ALL
            SELECT * FROM forward WHERE position > 0
        )
        ORDER BY position;
    """

    return conn.execute(text(query), {
        'reading_id': reading_id
    }).fetchall()

def format_author_name(first, second):
    """Format author's full name"""
    return f"{first or ''} {second or ''}".strip() or "Unknown Author"

def get_book_data(reading, is_current=False, is_future=False):
    """Get formatted book data including cover URL"""
    book = reading.book
    cover_url = _get_book_cover_url(book.title, book.author, book_id=book.id)

    return {
        'title': book.title,
        'author': book.author,
        'date_started': reading.date_started,
        'date_est_start': reading.date_est_start,
        'is_current': is_current,
        'is_future': is_future,
        'cover_url': cover_url,
        'read_id': reading.read_id,
        'book_id': book.id
    }

def _get_book_cover_url(title, author, book_id=None):
    """Get book cover URL"""
    project_paths = get_project_paths()

    # First try local storage
    if book_id:
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            cover_path = f"../../assets/book_covers/{book_id}{ext}"
            absolute_path = project_paths['workspace'] / 'assets' / 'book_covers' / f"{book_id}{ext}"
            if absolute_path.exists():
                return cover_path

    # If no cover found, use book cover 0
    return "../../assets/book_covers/0.jpg"

def generate_report(limit=10):
    """Generate the reading chain report for current books"""
    project_paths = get_project_paths()

    template_dir = project_paths['workspace'] / 'templates' / 'reports'
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('reading_chain_report.html')

    with engine.connect() as conn:
        current_readings = get_current_readings(conn)

        if not current_readings:
            console.print("[red]No current readings found[/red]")
            return

        # Initialize chains for all media types
        reading_chains = {
            'kindle': {'current_title': None, 'chain': []},
            'hardcover': {'current_title': None, 'chain': []},
            'audio': {'current_title': None, 'chain': []}
        }

        today = date.today()

        # Process chains for each current reading
        for reading in current_readings:
            chain = get_reading_chain(conn, reading.read_id, 'both', limit)
            media = reading.media.lower()  # Normalize media type

            # Process chain into template-friendly format
            processed_chain = []
            for book in chain:
                is_current = book.title == reading.title
                # Convert date_est_start to date object if it's not None
                est_start_date = (datetime.strptime(book.date_est_start, '%Y-%m-%d').date()
                                if book.date_est_start else None)

                is_future = (not book.date_started and est_start_date and
                           est_start_date > today)

                processed_chain.append({
                    'read_id': book.read_id,
                    'book_id': book.book_id,  # Make sure book_id is included
                    'title': book.title,
                    'author': format_author_name(book.author_name_first, book.author_name_second),
                    'previous_id': book.id_previous,
                    'next_id': book.next_id,
                    'position': book.position,
                    'media': book.media,
                    'is_current': is_current,
                    'is_future': is_future,
                    'date_started': (datetime.strptime(book.date_started, '%Y-%m-%d').date()
                                   if book.date_started else None),
                    'date_finished_actual': (datetime.strptime(book.date_finished_actual, '%Y-%m-%d').date()
                                          if book.date_finished_actual else None),
                    'date_est_start': est_start_date,
                    'date_est_end': (datetime.strptime(book.date_est_end, '%Y-%m-%d').date()
                                   if book.date_est_end else None),
                    'cover_url': _get_book_cover_url(
                        book.title,
                        format_author_name(book.author_name_first, book.author_name_second),
                        book.book_id
                    )
                })

            if media in reading_chains:
                reading_chains[media] = {
                    'current_title': reading.title,
                    'chain': processed_chain
                }

        # Get current year for the description
        current_year = datetime.now().year

        # Render the template
        html_content = template.render(
            title=f"Your {current_year} TBR and beyond by Format",
            description="Your upcoming reading adventures. Each book by format, contributing to more worlds to get lost in.",
            chains=reading_chains,
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            media_colors={
                'kindle': {'color': '#3B82F6', 'font_size': '48px', 'text_color': '#3B82F6'},  # blue
                'hardcover': {'color': '#A855F7', 'font_size': '48px', 'text_color': '#A855F7'},  # purple
                'audio': {'color': '#FB923C', 'font_size': '48px', 'text_color': '#FB923C'}  # orange
            }
        )

        # Write the report
        output_dir = project_paths['workspace'] / 'reports' / 'tbr'
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / 'tbr.html'
        output_file.write_text(html_content)

        console.print(f"[green]Report generated: {output_file}[/green]")
        console.print(f"[green]Found chains for {len([c for c in reading_chains.values() if c['current_title']])} current readings[/green]")

if __name__ == "__main__":
    generate_report()
