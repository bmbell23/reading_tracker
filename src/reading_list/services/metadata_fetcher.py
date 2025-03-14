import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Any
from urllib.parse import quote
from PIL import Image
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn  # Added progress components, SpinnerColumn, TextColumn, BarColumn  # Added progress components
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from rich.style import Style
from rich import box

from ..models.base import SessionLocal
from ..models.book import Book
from ..models.isbn import ISBN
from ..utils.paths import get_project_paths

class MetadataFetcher:
    def __init__(self, force_update: bool = False, missing_only: bool = False):
        self.session = SessionLocal()
        self.console = Console()
        self.force_update = force_update
        self.missing_only = missing_only
        self.max_concurrent_requests = 10
        self.max_workers = 4
        self.min_aspect_ratio = 0.6
        self.max_aspect_ratio = 0.7

        # Set up paths
        project_paths = get_project_paths()
        self.assets_path = project_paths['assets'] / 'book_covers'  # Fix: use dictionary access
        self.assets_path.mkdir(parents=True, exist_ok=True)

        # API endpoints
        self.google_books_url = "https://www.googleapis.com/books/v1/volumes"
        self.openlibrary_url = "https://openlibrary.org/search.json"

        # Track results
        self.results = {
            'covers': {'success': 0, 'updated': 0, 'skipped': 0, 'failed': []},
            'isbn': {'success': 0, 'skipped': 0, 'failed': []},  # Added 'skipped'
            'dates': {'success': 0, 'failed': []},
            'pages': {'success': 0, 'failed': []},
            'words': {'success': 0, 'failed': []},
            'series': {'success': 0, 'failed': []},
            'author': {'success': 0, 'failed': []}
        }

        # Track proposed changes
        self.proposed_changes = {
            'covers': [],
            'isbn': [],
            'dates': [],
            'pages': [],
            'words': [],
            'series': [],
            'author': []
        }

        # Initial scan to update has_cover status
        self.update_cover_status()

    def update_cover_status(self):
        """Scan assets directory and update cover status in database"""
        books = self.session.query(Book).all()
        for book in books:
            has_cover = False
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                if (self.assets_path / f"book_{book.id}{ext}").exists():
                    has_cover = True
                    break
            if book.cover != has_cover:  # Changed from has_cover to cover
                book.cover = has_cover  # Changed from has_cover to cover
        self.session.commit()

    def get_books_needing_metadata(self, metadata_type: str) -> List[Book]:
        """Get books that need metadata updates"""
        query = self.session.query(Book)
        
        if metadata_type == 'pages':
            if self.missing_only:
                query = query.filter(Book.page_count.is_(None))
            elif not self.force_update:
                query = query.filter(Book.page_count.is_(None))
        
        return query.all()

    def is_cover_rectangular(self, image_path: Path) -> bool:
        """Check if image has proper book cover dimensions"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                aspect_ratio = width / height
                return self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio
        except Exception as e:
            self.console.print(f"[red]Error checking image dimensions for {image_path}: {str(e)}[/red]")
            return False

    async def try_google_books(self, session: aiohttp.ClientSession,
                             title: str, author: str) -> Optional[str]:
        """Try to fetch cover from Google Books API"""
        try:
            query = quote(f"intitle:\"{title}\" inauthor:\"{author}\"")
            async with session.get(
                f"{self.google_books_url}?q={query}&maxResults=10"
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                if 'items' not in data:
                    return None

                for item in data['items']:
                    book_info = item['volumeInfo']
                    if (title.lower() in book_info.get('title', '').lower() and
                        author.lower() in book_info.get('authors', [''])[0].lower()):

                        image_links = book_info.get('imageLinks', {})
                        for img_type in ['extraLarge', 'large', 'medium', 'thumbnail', 'smallThumbnail']:
                            if cover_url := image_links.get(img_type):
                                return cover_url.replace('http://', 'https://')

                for item in data['items']:
                    image_links = item['volumeInfo'].get('imageLinks', {})
                    if cover_url := (image_links.get('thumbnail') or image_links.get('smallThumbnail')):
                        return cover_url.replace('http://', 'https://')

        except Exception as e:
            self.console.print(f"[red]Google Books API error: {str(e)}[/red]")
        return None

    async def try_openlibrary(self, session: aiohttp.ClientSession,
                             title: str, author: str) -> Optional[str]:
        """Try to fetch cover from OpenLibrary API"""
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

                for doc in data['docs']:
                    if cover_id := doc.get('cover_i'):
                        for size in ['L', 'M', 'S']:
                            return f"https://covers.openlibrary.org/b/id/{cover_id}-{size}.jpg"

        except Exception as e:
            self.console.print(f"[red]OpenLibrary API error: {str(e)}[/red]")
        return None

    async def analyze_cover_changes(self, books: List[Book], progress, task) -> List[Tuple]:
        """Analyze what cover changes would be made"""
        changes = []
        async with aiohttp.ClientSession() as session:
            for book in books:
                progress.update(task, advance=1)
                current_status = "Has cover" if book.cover else "No cover"  # Changed from has_cover to cover
                
                # Check if we can get a new cover
                cover_url = None
                for source in [self.try_google_books, self.try_openlibrary]:
                    author = f"{book.author_name_first or ''} {book.author_name_second or ''}".strip()
                    cover_url = await source(session, book.title, author)
                    if cover_url:
                        break
                
                if cover_url:
                    proposed = "Update cover" if book.cover else "Add new cover"  # Changed from has_cover to cover
                    changes.append((book.id, book.title, current_status, proposed))
                elif not book.cover:  # Changed from has_cover to cover
                    changes.append((book.id, book.title, current_status, "No cover found"))

        return changes

    def show_proposed_changes(self, change_type: str) -> bool:
        """Show proposed changes and ask for confirmation"""
        if not self.proposed_changes[change_type]:
            self.console.print(Panel(
                "[yellow]No changes to apply[/yellow]",
                title=f"[bold blue]{change_type.title()} Changes[/bold blue]",
                border_style="blue"
            ))
            return False

        table = Table(
            title=f"Proposed {change_type.title()} Changes",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            box=box.ROUNDED,
            title_style="bold blue",
            padding=(0, 1)
        )
        
        if change_type == 'covers':
            table.add_column("Book ID", justify="right", style="dim cyan")
            table.add_column("Title", style="bold white")
            table.add_column("Current Status", style="yellow")
            table.add_column("Proposed Change", style="green")
            
            for book_id, title, current, proposed in self.proposed_changes[change_type]:
                status_style = "red" if current == "No cover" else "yellow"
                proposed_style = {
                    "Add new cover": "bold green",
                    "Update cover": "bold yellow",
                    "No cover found": "bold red"
                }.get(proposed, "white")
                
                table.add_row(
                    str(book_id),
                    title,
                    f"[{status_style}]{current}[/{status_style}]",
                    f"[{proposed_style}]{proposed}[/{proposed_style}]"
                )
        else:
            table.add_column("Book ID", justify="right", style="dim cyan")
            table.add_column("Title", style="bold white")
            table.add_column("Current Value", style="yellow")
            table.add_column("New Value", style="green")
            
            for book_id, title, current, proposed in self.proposed_changes[change_type]:
                current_display = str(current) if current else "[italic red]None[/italic red]"
                table.add_row(
                    str(book_id),
                    title,
                    current_display,
                    f"[bold green]{proposed}[/bold green]"
                )

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

        # Show summary
        changes_count = len(self.proposed_changes[change_type])
        summary = Table.grid(padding=1)
        summary.add_column(style="cyan")
        summary.add_column(style="bold white")
        summary.add_row("Total changes:", str(changes_count))
        
        self.console.print(Panel(
            summary,
            title="[bold blue]Summary[/bold blue]",
            border_style="blue",
            box=box.ROUNDED
        ))
        self.console.print("\n")

        return Confirm.ask(
            "[bold cyan]Do you want to apply these changes?[/bold cyan]",
            default=False
        )

    async def fetch_covers_async(self):
        """Fetch book covers asynchronously"""
        with Progress() as progress:
            task1 = progress.add_task(
                "[cyan]Analyzing current covers...", 
                total=None
            )
            books = self.get_books_needing_covers()
            progress.update(task1, completed=True)

            task2 = progress.add_task(
                "[cyan]Checking available covers...", 
                total=len(books)
            )
            
            # Analyze proposed changes
            self.proposed_changes['covers'] = await self.analyze_cover_changes(
                books, 
                progress,
                task2
            )

        if not self.show_proposed_changes('covers'):
            self.console.print("[yellow]No changes were made.[/yellow]")
            return

        # Proceed with actual fetching
        self.console.print("\n[bold cyan]Applying changes...[/bold cyan]")
        async with aiohttp.ClientSession() as session:
            with Progress() as progress:
                task = progress.add_task(
                    "[cyan]Downloading covers...", 
                    total=len(books)
                )
                for book in books:
                    progress.update(task, advance=1)
                    
                    # Try Google Books first
                    if cover_url := await self.try_google_books(session, book.title, book.author_name_first):
                        # Save cover logic here
                        self.results['covers']['success'] += 1
                        continue
                        
                    # Try OpenLibrary as fallback
                    if cover_url := await self.try_openlibrary(session, book.title, book.author_name_first):
                        # Save cover logic here
                        self.results['covers']['success'] += 1
                        continue
                        
                    self.results['covers']['failed'].append(f"{book.title} by {book.author_name_first}")

    def fetch_all_metadata(self):
        """Fetch all available metadata"""
        self.console.print(Panel(
            "[bold white]Starting comprehensive metadata analysis...[/bold white]",
            title="[bold blue]Metadata Update[/bold blue]",
            border_style="blue",
            box=box.ROUNDED
        ))
        
        # Analyze all types of changes first
        for metadata_type in self.proposed_changes.keys():
            # Add analysis logic for each type
            pass
        
        # Show all proposed changes at once
        for metadata_type in self.proposed_changes.keys():
            if not self.show_proposed_changes(metadata_type):
                self.console.print(f"\nSkipping {metadata_type} updates.")
                continue
                
            # Proceed with the actual fetching for this type
            if metadata_type == 'covers':
                self.fetch_covers()
            elif metadata_type == 'isbn':
                self.fetch_isbns()
            # ... (other metadata types) ...

    def fetch_covers(self):
        """Fetch book covers"""
        self.console.print("[bold blue]Fetching book covers...[/bold blue]")
        asyncio.run(self.fetch_covers_async())
        self.print_cover_report()

    def print_cover_report(self):
        """Print report of cover fetching results"""
        self.console.print("\n[bold green]Cover Fetching Report:[/bold green]")
        self.console.print(f"Successfully fetched: {self.results['covers']['success']}")
        self.console.print(f"Updated: {self.results['covers']['updated']}")
        self.console.print(f"Skipped: {self.results['covers']['skipped']}")
        if self.results['covers']['failed']:
            self.console.print("\n[bold red]Failed to fetch covers for:[/bold red]")
            for book in self.results['covers']['failed']:
                self.console.print(f"- {book}")

    def fetch_isbns(self):
        """Fetch ISBN numbers"""
        self.console.print("[bold blue]Fetching ISBN numbers...[/bold blue]")
        asyncio.run(self.fetch_isbns_async())

    async def try_fetch_isbn(self, session: aiohttp.ClientSession, title: str, author: str) -> Dict[str, str]:
        """Try to fetch ISBNs from various sources"""
        try:
            # Try Google Books first
            query = quote(f"intitle:\"{title}\" inauthor:\"{author}\"")
            async with session.get(f"{self.google_books_url}?q={query}&maxResults=1") as response:
                if response.status == 200:
                    data = await response.json()
                    if 'items' in data:
                        volume_info = data['items'][0]['volumeInfo']
                        identifiers = volume_info.get('industryIdentifiers', [])
                        result = {
                            'isbn_10': None,
                            'isbn_13': None,
                            'asin': None,
                            'source': 'google_books'
                        }
                        for identifier in identifiers:
                            if identifier['type'] == 'ISBN_10':
                                result['isbn_10'] = identifier['identifier']
                            elif identifier['type'] == 'ISBN_13':
                                result['isbn_13'] = identifier['identifier']
                        return result

            # Try OpenLibrary as fallback
            clean_title = quote(title.lower().replace(' ', '+'))
            clean_author = quote(author.lower().replace(' ', '+'))
            async with session.get(f"{self.openlibrary_url}?title={clean_title}&author={clean_author}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('docs'):
                        doc = data['docs'][0]
                        return {
                            'isbn_10': doc.get('isbn', [None])[0],
                            'isbn_13': doc.get('isbn13', [None])[0],
                            'asin': None,
                            'source': 'openlibrary'
                        }

        except Exception as e:
            self.console.print(f"[red]Error fetching ISBN: {str(e)}[/red]")
        
        return {}

    async def fetch_isbns_async(self):
        """Fetch ISBNs for books and store them in the isbn table without modifying books"""
        query = self.session.query(Book)
        books = query.all()
        
        if not books:
            self.console.print("[green]No books found![/green]")
            return

        async with aiohttp.ClientSession() as session:
            with Progress() as progress:
                task = progress.add_task("[cyan]Fetching ISBNs...", total=len(books))

                for book in books:
                    author = f"{book.author_name_first or ''} {book.author_name_second or ''}".strip()
                    isbns = await self.try_fetch_isbn(session, book.title, author)
                    
                    if isbns.get('isbn_10') or isbns.get('isbn_13') or isbns.get('asin'):
                        # Check if any of these ISBNs already exist
                        existing_isbn = None
                        if isbns.get('isbn_10'):
                            existing_isbn = self.session.query(ISBN).filter_by(isbn_10=isbns['isbn_10']).first()
                        if not existing_isbn and isbns.get('isbn_13'):
                            existing_isbn = self.session.query(ISBN).filter_by(isbn_13=isbns['isbn_13']).first()
                        if not existing_isbn and isbns.get('asin'):
                            existing_isbn = self.session.query(ISBN).filter_by(asin=isbns['asin']).first()

                        if existing_isbn:
                            self.results['isbn']['skipped'] += 1
                        else:
                            # Create new ISBN record
                            isbn_record = ISBN(
                                title=book.title,
                                author_name_first=book.author_name_first,
                                author_name_second=book.author_name_second,
                                author_gender=book.author_gender,
                                page_count=book.page_count,
                                date_published=book.date_published,
                                has_cover=book.has_cover,
                                isbn_10=isbns.get('isbn_10'),
                                isbn_13=isbns.get('isbn_13'),
                                asin=isbns.get('asin'),
                                source=isbns.get('source')
                            )
                            self.session.add(isbn_record)
                            self.results['isbn']['success'] += 1
                    else:
                        self.results['isbn']['failed'].append((book.id, book.title, author))
                    
                    progress.advance(task)
                    
                self.session.commit()

        # Print results
        stats_table = Table(
            title="ISBN Fetch Results",
            box=box.ROUNDED,
            show_header=False,
            title_style="bold blue"
        )
        
        stats_table.add_column(style="cyan")
        stats_table.add_column(style="white")
        
        total = self.results['isbn']['success'] + len(self.results['isbn']['failed'])
        
        stats_table.add_row("Total processed:", str(total))
        stats_table.add_row("Successfully fetched:", f"[green]{self.results['isbn']['success']}[/green]")
        stats_table.add_row("Failed:", f"[red]{len(self.results['isbn']['failed'])}[/red]")
        
        self.console.print("\n")
        self.console.print(stats_table)

        if self.results['isbn']['failed']:
            failed_table = Table(
                title="Failed ISBN Fetches",
                show_header=True,
                header_style="bold red",
                box=box.ROUNDED
            )
            
            failed_table.add_column("ID", justify="right", style="cyan")
            failed_table.add_column("Title", style="white")
            failed_table.add_column("Author", style="white")
            
            for book_id, title, author in self.results['isbn']['failed']:
                failed_table.add_row(str(book_id), title, author)
            
            self.console.print("\n")
            self.console.print(failed_table)

    async def try_fetch_page_count(self, session: aiohttp.ClientSession, title: str, author: str) -> Optional[int]:
        """Try to fetch page count from Google Books API"""
        try:
            query = quote(f"intitle:\"{title}\" inauthor:\"{author}\"")
            async with session.get(f"{self.google_books_url}?q={query}&maxResults=1") as response:
                if response.status != 200:
                    return None

                data = await response.json()
                if 'items' not in data:
                    return None

                volume_info = data['items'][0]['volumeInfo']
                return volume_info.get('pageCount')

        except Exception as e:
            self.console.print(f"[red]Error fetching page count: {str(e)}[/red]")
            return None

    async def fetch_page_counts_async(self):
        """Fetch page counts asynchronously"""
        books = self.get_books_needing_metadata('pages')
        
        if not books:
            self.console.print("[yellow]No books found needing page count updates.[/yellow]")
            return

        async with aiohttp.ClientSession() as session:
            with Progress() as progress:
                task = progress.add_task("[cyan]Fetching page counts...", total=len(books))

                for book in books:
                    author = f"{book.author_name_first or ''} {book.author_name_second or ''}".strip()
                    if page_count := await self.try_fetch_page_count(session, book.title, author):
                        book.page_count = page_count
                        self.results['pages']['success'] += 1
                    else:
                        self.results['pages']['failed'].append(f"{book.title} by {author}")
                    
                    progress.advance(task)

            self.session.commit()

        # Print results
        self.console.print("\n[bold green]Page Count Fetching Report:[/bold green]")
        self.console.print(f"Successfully fetched: {self.results['pages']['success']}")
        if self.results['pages']['failed']:
            self.console.print("\n[bold red]Failed to fetch page counts for:[/bold red]")
            for book in self.results['pages']['failed']:
                self.console.print(f"- {book}")

    def fetch_page_counts(self):
        """Fetch page counts for books"""
        self.console.print("[bold blue]Fetching page counts...[/bold blue]")
        asyncio.run(self.fetch_page_counts_async())
