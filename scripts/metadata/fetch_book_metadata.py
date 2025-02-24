#!/usr/bin/env python3
import os
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import requests
from urllib.parse import quote
from rich.console import Console
from rich.table import Table
from rich.progress import track, Progress
import argparse
from PIL import Image
import math

from src.models.base import SessionLocal
from src.models.book import Book

class FetchBookMetadata:
    def __init__(self, force_update: bool = False):
        self.session = SessionLocal()
        self.console = Console()
        self.force_update = force_update
        self.max_concurrent_requests = 10
        self.max_workers = 4
        self.min_aspect_ratio = 0.6
        self.max_aspect_ratio = 0.7

        # Set up paths
        self.assets_path = Path(__file__).parent.parent.parent / 'assets' / 'book_covers'
        self.assets_path.mkdir(parents=True, exist_ok=True)

        # API endpoints
        self.google_books_url = "https://www.googleapis.com/books/v1/volumes"
        self.openlibrary_url = "https://openlibrary.org/search.json"

        # Track results
        self.results = {
            'covers': {
                'success': 0,
                'updated': 0,
                'skipped': 0,
                'failed': []
            },
            'isbn': {'success': 0, 'failed': []},
            'dates': {'success': 0, 'failed': []},
            'pages': {'success': 0, 'failed': []},
            'words': {'success': 0, 'failed': []},
            'series': {'success': 0, 'failed': []},
            'author': {'success': 0, 'failed': []}
        }

        # Initial scan to update has_cover status
        self.update_cover_status()

    def update_cover_status(self):
        """Scan assets directory and update has_cover status in database"""
        books = self.session.query(Book).all()
        for book in books:
            has_cover = False
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                if (self.assets_path / f"book_{book.id}{ext}").exists():
                    has_cover = True
                    break
            if book.has_cover != has_cover:
                book.has_cover = has_cover
        self.session.commit()

    def get_books_needing_covers(self) -> List[Book]:
        """Get list of books that need covers"""
        query = self.session.query(Book)

        if not self.force_update:
            query = query.filter(Book.has_cover == False)

        return query.all()

    def is_cover_rectangular(self, image_path: Path) -> bool:
        """Check if image has proper book cover dimensions"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                aspect_ratio = width / height
                return self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio
        except Exception as e:
            print(f"Error checking image dimensions for {image_path}: {str(e)}")
            return False

    def check_existing_cover(self, book_id: int) -> tuple[bool, bool]:
        """
        Check if a cover exists and if it's properly rectangular
        Returns: (exists: bool, is_rectangular: bool)
        """
        if self.force_update:
            return False, False

        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            path = self.assets_path / f"{book_id}{ext}"  # Removed book_ prefix
            if path.exists():
                is_rect = self.is_cover_rectangular(path)
                return True, is_rect

        return False, False

    async def try_google_books(self, session: aiohttp.ClientSession,
                             title: str, author: str) -> str | None:
        """Async version of Google Books API check"""
        try:
            # Simplified query - just search by title and author
            query = quote(f"intitle:\"{title}\" inauthor:\"{author}\"")
            async with session.get(
                f"{self.google_books_url}?q={query}&maxResults=10"
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                if 'items' not in data:
                    return None

                # Look for best match without strict requirements
                for item in data['items']:
                    book_info = item['volumeInfo']
                    # Relaxed title matching - allow partial matches
                    if (title.lower() in book_info.get('title', '').lower() and
                        author.lower() in book_info.get('authors', [''])[0].lower()):

                        image_links = book_info.get('imageLinks', {})
                        # Try to get the best quality image available
                        for img_type in ['extraLarge', 'large', 'medium', 'thumbnail', 'smallThumbnail']:
                            if cover_url := image_links.get(img_type):
                                return cover_url.replace('http://', 'https://')

                # Fallback to first result with an image if no good match found
                for item in data['items']:
                    image_links = item['volumeInfo'].get('imageLinks', {})
                    if cover_url := (image_links.get('thumbnail') or image_links.get('smallThumbnail')):
                        return cover_url.replace('http://', 'https://')

        except Exception as e:
            print(f"Google Books API error: {str(e)}")
        return None

    async def try_openlibrary(self, session: aiohttp.ClientSession,
                             title: str, author: str) -> str | None:
        """Async version of OpenLibrary API check"""
        try:
            clean_title = quote(title.lower().replace(' ', '+'))
            clean_author = quote(author.lower().replace(' ', '+'))

            async with session.get(
                f"{self.openlibrary_url}?title={clean_title}&author={clean_author}"
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                if not data.get('docs'):
                    return None

                # Look for any result with a cover
                for doc in data['docs']:
                    if cover_id := doc.get('cover_i'):
                        # Try to get the largest available image
                        for size in ['L', 'M', 'S']:
                            return f"https://covers.openlibrary.org/b/id/{cover_id}-{size}.jpg"

        except Exception as e:
            print(f"OpenLibrary API error: {str(e)}")
        return None

    def save_cover(self, book_id: int, cover_url: str) -> bool:
        """Download and save book cover - runs in thread pool"""
        try:
            response = requests.get(cover_url, timeout=10)
            if response.status_code == 200:
                # Save to temporary file first to check dimensions
                temp_path = self.assets_path / f"temp_{book_id}.jpg"
                temp_path.write_bytes(response.content)

                # Check if the image has proper dimensions
                if not self.is_cover_rectangular(temp_path):
                    temp_path.unlink()
                    return False

                mime_type = response.headers.get('content-type', 'image/jpeg')
                ext = '.jpg' if 'jpeg' in mime_type else '.' + mime_type.split('/')[-1]
                cover_path = self.assets_path / f"{book_id}{ext}"  # Removed book_ prefix

                # Remove any existing covers
                if self.force_update:
                    for existing_ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        existing_path = self.assets_path / f"{book_id}{existing_ext}"  # Removed book_ prefix
                        if existing_path.exists():
                            existing_path.unlink()

                # Move temporary file to final location
                temp_path.rename(cover_path)
                return True

            return False
        except Exception as e:
            print(f"Error saving cover: {str(e)}")
            return False

    async def process_book(self, session: aiohttp.ClientSession,
                         book: Book, progress: Progress) -> None:
        """Process a single book asynchronously"""
        # First check if we can skip this book
        if book.has_cover and not self.force_update:
            self.results['covers']['skipped'] += 1
            progress.advance(self.task_id)
            return

        # Get cover status
        cover_exists, is_rectangular = self.check_existing_cover(book.id)

        # If we have a cover but it's not rectangular, or if we're forcing an update,
        # we'll try to get a better one
        if cover_exists and not is_rectangular:
            self.force_update = True

        # Only proceed with API calls if we need a new cover
        if self.force_update or not cover_exists:
            author = f"{book.author_name_first or ''} {book.author_name_second or ''}".strip()
            cover_url = None

            # Try different sources
            for source in [self.try_google_books, self.try_openlibrary]:
                cover_url = await source(session, book.title, author)
                if cover_url:
                    break

            if cover_url:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    success = await asyncio.get_event_loop().run_in_executor(
                        executor, self.save_cover, book.id, cover_url
                    )
                    if success:
                        if self.force_update:
                            self.results['covers']['updated'] += 1
                        else:
                            self.results['covers']['success'] += 1
                        book.has_cover = True
                        self.session.commit()
                    else:
                        self.results['covers']['failed'].append((
                            book.id, book.title, author,
                            "Failed to save cover (incorrect dimensions)" if cover_url else "Failed to save cover"
                        ))
            else:
                self.results['covers']['failed'].append((
                    book.id, book.title, author, "No suitable cover found"
                ))

        progress.advance(self.task_id)

    async def fetch_covers_async(self):
        """Main async function to fetch covers"""
        books = self.get_books_needing_covers()

        self.console.print("\n[bold blue]Checking for book covers...[/bold blue]")
        if self.force_update:
            self.console.print("[yellow]Force update enabled - checking all books[/yellow]")
        elif not books:
            self.console.print("[green]All books have covers - nothing to do![/green]")
            return

        # Show table of books we'll be processing
        table = Table(
            title="\nBooks To Process",
            show_header=True,
            header_style="bold magenta",
            border_style="bright_black"
        )

        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Author", style="white")
        table.add_column("Status", style="yellow")

        for book in books:
            author = f"{book.author_name_first or ''} {book.author_name_second or ''}".strip()
            status = "Update" if book.has_cover else "Missing"
            table.add_row(
                str(book.id),
                book.title or "N/A",
                author or "Unknown",
                status
            )

        self.console.print(table)
        self.console.print(f"\nProcessing [blue]{len(books)}[/blue] books...")

        async with aiohttp.ClientSession() as session:
            with Progress() as progress:
                self.task_id = progress.add_task(
                    "[cyan]Processing books...", total=len(books)
                )

                # Process books in chunks to avoid overwhelming APIs
                chunks = [books[i:i + self.max_concurrent_requests]
                         for i in range(0, len(books), self.max_concurrent_requests)]

                for chunk in chunks:
                    tasks = [self.process_book(session, book, progress)
                            for book in chunk]
                    await asyncio.gather(*tasks)

    def fetch_all_metadata(self):
        """Fetch all types of metadata"""
        self.console.print("[bold blue]Fetching all metadata...[/bold blue]")
        self.fetch_covers()
        self.fetch_isbns()
        self.fetch_publication_dates()
        self.fetch_page_counts()
        self.fetch_word_counts()
        self.fetch_series_info()
        self.fetch_author_info()

    def fetch_covers(self):
        """Fetch book covers"""
        self.console.print("[bold blue]Fetching book covers...[/bold blue]")
        asyncio.run(self.fetch_covers_async())
        self.print_cover_report()

    def fetch_isbns(self):
        """Fetch ISBN numbers"""
        self.console.print("[bold blue]Fetching ISBN numbers...[/bold blue]")
        # Implementation needed

    def fetch_publication_dates(self):
        """Fetch publication dates"""
        self.console.print("[bold blue]Fetching publication dates...[/bold blue]")
        # Implementation needed

    def fetch_page_counts(self):
        """Fetch page counts"""
        self.console.print("[bold blue]Fetching page counts...[/bold blue]")
        # Implementation needed

    def fetch_word_counts(self):
        """Fetch word counts"""
        self.console.print("[bold blue]Fetching word counts...[/bold blue]")
        # Implementation needed

    def fetch_series_info(self):
        """Fetch series information"""
        self.console.print("[bold blue]Fetching series information...[/bold blue]")
        # Implementation needed

    def fetch_author_info(self):
        """Fetch author information"""
        self.console.print("[bold blue]Fetching author information...[/bold blue]")
        # Implementation needed

    def print_cover_report(self):
        """Print final report"""
        self.console.print("\n[bold green]Cover Download Report[/bold green]")

        stats_table = Table(show_header=False, box=None)
        total = (self.results['covers']['success'] +
                self.results['covers']['updated'] +
                len(self.results['covers']['failed']) +
                self.results['covers']['skipped'])

        stats_table.add_row("Total processed:", str(total))
        if self.force_update:
            stats_table.add_row("Updated:", str(self.results['covers']['updated']))
        stats_table.add_row("Successfully downloaded:", str(self.results['covers']['success']))
        stats_table.add_row("Already existed:", str(self.results['covers']['skipped']))

        # Only include books that have no cover file or have an invalid cover
        truly_missing = []
        for book_id, title, author, reason in self.results['covers']['failed']:
            exists, is_rectangular = self.check_existing_cover(book_id)
            if not exists:  # No cover file exists
                truly_missing.append((book_id, title, author, "No cover found"))
            elif not is_rectangular:  # Cover exists but has wrong dimensions
                truly_missing.append((book_id, title, author, "Square cover needs replacement"))

        stats_table.add_row("Failed:", str(len(truly_missing)))
        self.console.print(stats_table)

        if truly_missing:
            self.console.print("\n[bold red]Books Missing Proper Covers:[/bold red]")
            table = Table(show_header=True)
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Author", style="white")
            table.add_column("Reason", style="red")

            for book_id, title, author, reason in truly_missing:
                table.add_row(str(book_id), title, author, reason)

            self.console.print(table)

def main():
    parser = argparse.ArgumentParser(
        description='Fetch book metadata from various online sources'
    )

    # Metadata type arguments
    metadata_group = parser.add_mutually_exclusive_group(required=True)
    metadata_group.add_argument('--all', action='store_true',
                              help='Fetch all available metadata')
    metadata_group.add_argument('--covers', action='store_true',
                              help='Fetch book covers')
    metadata_group.add_argument('--isbn', action='store_true',
                              help='Fetch ISBN numbers')
    metadata_group.add_argument('--dates', action='store_true',
                              help='Fetch publication dates')
    metadata_group.add_argument('--pages', action='store_true',
                              help='Fetch page counts')
    metadata_group.add_argument('--words', action='store_true',
                              help='Fetch word counts')
    metadata_group.add_argument('--series', action='store_true',
                              help='Fetch series information')
    metadata_group.add_argument('--author', action='store_true',
                              help='Fetch author information')

    # Optional arguments
    parser.add_argument('--force-update', action='store_true',
                       help='Force update of metadata, even if it already exists')
    parser.add_argument('--concurrent-requests', type=int, default=10,
                       help='Maximum number of concurrent API requests')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of worker threads for file operations')

    args = parser.parse_args()

    fetcher = FetchBookMetadata(force_update=args.force_update)
    fetcher.max_concurrent_requests = args.concurrent_requests
    fetcher.max_workers = args.workers

    if args.all:
        fetcher.fetch_all_metadata()
    elif args.covers:
        fetcher.fetch_covers()
    elif args.isbn:
        fetcher.fetch_isbns()
    elif args.dates:
        fetcher.fetch_publication_dates()
    elif args.pages:
        fetcher.fetch_page_counts()
    elif args.words:
        fetcher.fetch_word_counts()
    elif args.series:
        fetcher.fetch_series_info()
    elif args.author:
        fetcher.fetch_author_info()

if __name__ == "__main__":
    main()
