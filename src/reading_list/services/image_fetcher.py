"""Service for fetching images from Google."""
import aiohttp
import asyncio
from pathlib import Path
from typing import List
from urllib.parse import quote
from bs4 import BeautifulSoup
from rich.console import Console
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..utils.paths import get_project_paths
import random
import time

class GoogleImageFetcher:
    def __init__(self, session: Session):
        self.console = Console()
        self.session = session
        self.search_url = "https://www.google.com/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
        project_paths = get_project_paths()
        self.covers_path = project_paths['assets'] / 'book_covers'
        self.covers_path.mkdir(parents=True, exist_ok=True)
        self.min_aspect_ratio = 0.5
        self.max_aspect_ratio = 0.8
        self.retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff delays in seconds

    async def fetch_with_retry(self, session: aiohttp.ClientSession, url: str, params: dict) -> tuple[int, str]:
        """Fetch URL with retry logic and exponential backoff."""
        for attempt, delay in enumerate(self.retry_delays):
            try:
                # Add random delay between requests
                await asyncio.sleep(random.uniform(1.0, 3.0))
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return response.status, await response.text()
                    elif response.status == 429:
                        if attempt < len(self.retry_delays) - 1:
                            self.console.print(f"[yellow]Rate limited. Waiting {delay} seconds before retry...[/yellow]")
                            await asyncio.sleep(delay)
                            continue
                    return response.status, ""
            except Exception as e:
                if attempt < len(self.retry_delays) - 1:
                    self.console.print(f"[yellow]Request failed: {str(e)}. Retrying in {delay} seconds...[/yellow]")
                    await asyncio.sleep(delay)
                    continue
                raise

    async def fetch_book_cover(self, book_id: int) -> bool:
        """
        Fetch and save book cover for the given book ID.
        """
        try:
            # Get book details from database
            result = self.session.execute(
                text("""
                    SELECT 
                        title,
                        author_name_first,
                        author_name_second
                    FROM books 
                    WHERE id = :book_id
                """),
                {"book_id": book_id}
            )
            book = result.fetchone()
            
            if not book:
                self.console.print(f"[red]Book with ID {book_id} not found[/red]")
                return False
            
            # Construct search term
            author = f"{book.author_name_first or ''} {book.author_name_second or ''}".strip()
            search_term = f"{book.title} {author} book cover"
            output_path = self.covers_path / f"{book_id}.jpg"
            
            self.console.print(f"[cyan]Searching for: {search_term}[/cyan]")
            
            # Prepare search query
            params = {
                'q': search_term,
                'tbm': 'isch',
                'tbs': 'isz:l'  # Large images
            }
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                status, html = await self.fetch_with_retry(session, self.search_url, params)
                
                if status != 200:
                    self.console.print(f"[red]Search failed with status {status}[/red]")
                    return False
                
                # Look for high-quality retail images first (usually Amazon, etc.)
                import re
                matches = re.findall(r'https://[^"\']*?amazon[^"\']*?\.jpg', html)
                if not matches:
                    matches = re.findall(r'https://[^"\']*?\.jpg', html)
                
                if matches:
                    img_url = matches[0].replace('\\u003d', '=').replace('\\', '')
                    
                    async with session.get(img_url) as img_response:
                        if img_response.status == 200:
                            content = await img_response.read()
                            
                            # Basic validation
                            if len(content) < 5000:  # Skip very small files
                                return False
                                
                            # Save the image
                            output_path.write_bytes(content)
                            
                            # Update book's cover status
                            self.session.execute(
                                text("UPDATE books SET cover = TRUE WHERE id = :book_id"),
                                {"book_id": book_id}
                            )
                            self.session.commit()
                            
                            self.console.print(f"[green]Cover saved for book ID {book_id}[/green]")
                            return True
                
                self.console.print("[yellow]No suitable images found[/yellow]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error fetching cover for book {book_id}: {str(e)}[/red]")
            return False

def download_book_cover(session: Session, book_id: int) -> bool:
    """
    Synchronous wrapper for fetching book cover from Google Images.
    
    Args:
        session: SQLAlchemy database session
        book_id: ID of the book to fetch cover for
        
    Returns:
        bool: True if successful, False otherwise
    """
    fetcher = GoogleImageFetcher(session)
    return asyncio.run(fetcher.fetch_book_cover(book_id))
