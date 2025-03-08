"""
Chain Operations
===============

Core functionality for manipulating reading chains and managing chain-related operations.
"""

from typing import List, Tuple, Optional, Dict
from datetime import date, datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from jinja2 import Environment, FileSystemLoader
from rich.table import Table
from rich.console import Console
import math

console = Console()

from reading_list.models.reading import Reading
from reading_list.models.book import Book
from reading_list.models.base import SessionLocal
from ..queries.common_queries import CommonQueries
from reading_list.utils.paths import get_project_paths
from utils.constants import READING_SPEEDS, DEFAULT_WPD

class ChainOperations:
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize chain operations with optional session.
        
        Args:
            session: SQLAlchemy session. If None, creates new session
        """
        self.session = session or SessionLocal()
        self.queries = CommonQueries(self.session)  # Initialize queries with same session

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is not None:
            self.session.rollback()
        self.session.close()

    @staticmethod
    def get_chain_segment(chain: List[Reading], position: int, window: int = 2) -> Tuple[List[Reading], List[Reading]]:
        """
        Get segments of readings before and after a position in a chain.
        
        Args:
            chain: List of readings
            position: Position in chain to center the window around
            window: Number of readings to include before and after position
            
        Returns:
            Tuple of (readings_before, readings_after)
        """
        start = max(0, position - window)
        before = chain[start:position]
        after = chain[position + 1:position + window + 1] if position + 1 < len(chain) else []
        return before, after

    @staticmethod
    def update_chain_references(chain: List[Reading]) -> None:
        """
        Update id_previous references for all readings in a chain.
        
        Args:
            chain: List of readings to update
        """
        for i, reading in enumerate(chain):
            if i == 0:
                reading.id_previous = None
            else:
                reading.id_previous = chain[i-1].id

    def reorder_reading_chain(self, reading_id: int, target_id: int) -> Tuple[bool, str, Optional[dict]]:
        """
        Reorder a reading in the chain by moving it after the target reading.
        
        Args:
            reading_id: ID of the reading to move
            target_id: ID of the reading to place it after
            
        Returns:
            Tuple of (success, message, chain_info)
            where chain_info contains segments of affected chains for display
        """
        try:
            # Get both chains
            chain_1 = self.queries.get_reading_chain(reading_id)
            chain_2 = self.queries.get_reading_chain(target_id)

            if not chain_1 or not chain_2:
                return False, "Could not find one or both chains", None

            # Find positions
            pos_A = next(i for i, r in enumerate(chain_1) if r.id == reading_id)
            pos_B = next(i for i, r in enumerate(chain_2) if r.id == target_id)

            # Get the books we need to track
            book_A = chain_1[pos_A]
            book_B = chain_2[pos_B]

            # Get segments before and after each position
            chain_A_2_before, chain_A_2_after = self.get_chain_segment(chain_1, pos_A)
            chain_B_2_before, chain_B_2_after = self.get_chain_segment(chain_2, pos_B)

            # Store original state for display
            original_state = {
                'source': {
                    'segment': chain_A_2_before + [book_A] + chain_A_2_after,
                    'book': book_A
                },
                'target': {
                    'segment': chain_B_2_before + [book_B] + chain_B_2_after,
                    'book': book_B
                }
            }

            # Remove reading from source chain
            chain_1.pop(pos_A)
            self.update_chain_references(chain_1)

            # Insert into target chain
            chain_2.insert(pos_B + 1, book_A)
            self.update_chain_references(chain_2)

            # Update dates in both chains
            self.update_chain_dates(chain_1, max(0, pos_A - 1))
            self.update_chain_dates(chain_2, pos_B)

            # Store new state for display
            new_state = {
                'source': {
                    'segment': chain_A_2_before + chain_A_2_after if chain_1 else []
                },
                'target': {
                    'segment': chain_B_2_before + [book_B, book_A] + chain_B_2_after
                }
            }

            return True, "Chain reorder prepared successfully", {
                'original': original_state,
                'new': new_state,
                'session': self.session
            }

        except Exception as e:
            self.session.rollback()
            return False, f"Error: {str(e)}", None

    def update_chain_dates(self, reading: Reading) -> Tuple[int, int]:
        """Update estimated dates for a reading chain starting from the given reading"""
        updates_count = 0
        skipped_count = 0

        # If this reading has a previous reading, we need its end date
        if reading.id_previous:
            prev_reading = self.session.get(Reading, reading.id_previous)
            if prev_reading and prev_reading.date_est_end:
                # Set estimated start date to day after previous reading's estimated end
                reading.date_est_start = prev_reading.date_est_end + timedelta(days=1)
                
                # Calculate estimated end date based on days_estimate
                if reading.days_estimate:
                    reading.date_est_end = reading.date_est_start + timedelta(days=reading.days_estimate - 1)
                    updates_count += 1
                    print(f"Updated chain dates for: {reading.book.title[:30]:30} "
                          f"Start: {reading.date_est_start} End: {reading.date_est_end}")
                else:
                    skipped_count += 1
                    print(f"Skipped {reading.book.title[:30]:30} - missing days_estimate")
            else:
                skipped_count += 1
                print(f"Skipped {reading.book.title[:30]:30} - previous reading missing end date")

        return updates_count, skipped_count

    def update_all_chain_dates(self) -> Tuple[int, int]:
        """Update estimated dates for all reading chains"""
        total_updates = 0
        total_skipped = 0

        # First, ensure all days_estimate values are up to date
        self.update_days_estimate()
        
        # Get all readings that are part of chains (have a previous reading)
        chain_readings = self.session.query(Reading).filter(Reading.id_previous.isnot(None)).all()
        
        for reading in chain_readings:
            updates, skipped = self.update_chain_dates(reading)
            total_updates += updates
            total_skipped += skipped

        if total_updates > 0:
            self.session.commit()

        return total_updates, total_skipped

    def get_all_readings(self) -> List[Reading]:
        """Get all readings joined with their books"""
        return self.session.query(Reading).join(Book).all()

    def update_days_estimate(self) -> Tuple[int, int]:
        """Calculate and update days_estimate for all reading entries"""
        readings = self.get_all_readings()
        updates_count = 0
        skipped_count = 0

        for reading in readings:
            if not reading.book.word_count or not reading.media:
                skipped_count += 1
                continue

            media_lower = reading.media.lower()
            words_per_day = READING_SPEEDS.get(media_lower, DEFAULT_WPD)
            old_estimate = reading.days_estimate
            # Changed from int() to math.ceil()
            new_estimate = math.ceil(reading.book.word_count / words_per_day)

            if old_estimate != new_estimate:
                old_str = str(old_estimate) if old_estimate is not None else "None"
                print(f"Estimate: {reading.book.title[:30]:30} {old_str:>4} → {new_estimate:>3} days")
                reading.days_estimate = new_estimate
                updates_count += 1

        return updates_count, skipped_count

    def update_days_elapsed(self) -> Tuple[int, int]:
        """Calculate and update days_elapsed_to_read for all reading entries"""
        readings = self.get_all_readings()
        updates_count = 0
        skipped_count = 0

        for reading in readings:
            if not reading.date_started or not reading.date_finished_actual:
                skipped_count += 1
                continue

            old_elapsed = reading.days_elapsed_to_read
            # Add 1 to account for the day the book was started
            new_elapsed = (reading.date_finished_actual - reading.date_started).days + 1

            if old_elapsed != new_elapsed:
                old_str = str(old_elapsed) if old_elapsed is not None else "None"
                print(f"Elapsed: {reading.book.title[:30]:30} {old_str:>4} → {new_elapsed:>3} days")
                reading.days_elapsed_to_read = new_elapsed
                updates_count += 1

        return updates_count, skipped_count

    def update_reading_calculations(self, update_all: bool = False,
                                  update_estimate: bool = False,
                                  update_elapsed: bool = False,
                                  update_chain: bool = False) -> Dict[str, Tuple[int, int]]:
        """
        Update various reading calculations based on specified flags.
        
        Args:
            update_all: Update all calculated columns
            update_estimate: Update days_estimate column
            update_elapsed: Update days_elapsed_to_read column
            update_chain: Update chain dates
            
        Returns:
            Dictionary of operation results with updates and skips counts
        """
        results = {}

        if update_all or update_estimate:
            results['estimate'] = self.update_days_estimate()

        if update_all or update_elapsed:
            results['elapsed'] = self.update_days_elapsed()

        if update_all or update_chain:
            results['chain'] = self.update_all_chain_dates()

        return results

    def get_current_readings(self) -> List[Dict]:
        """
        Get all current (in-progress) readings.
        
        Returns:
            List of dictionaries containing reading information
        """
        current_readings = []
        
        # Query for readings that are started but not finished
        readings = (self.session.query(Reading)
                   .join(Book)
                   .filter(and_(
                       Reading.date_started <= date.today(),
                       Reading.date_finished_actual.is_(None)
                   ))
                   .all())
        
        for reading in readings:
            current_readings.append({
                'read_id': reading.id,
                'media': reading.media,
                'title': reading.book.title
            })
        
        return current_readings

    def get_reading_chain(self, reading_id: int, direction: str = 'both', limit: int = 10) -> List[dict]:
        """Get the reading chain around a specific reading"""
        # ... existing SQL query from reading_chain_report.py ...
        pass

    @staticmethod
    def format_author_name(first: str, second: str) -> str:
        """Format author name from first and second parts"""
        if first and second:
            return f"{first} {second}"
        return first or second or "Unknown Author"

    def get_book_cover_path(self, book_id: int) -> Optional[str]:
        """Get the path to a book's cover image"""
        project_paths = get_project_paths()
        covers_dir = project_paths['workspace'] / 'data' / 'covers'
        
        # Check for cover file with different extensions
        for ext in ['.jpg', '.jpeg', '.png']:
            cover_path = covers_dir / f"{book_id}{ext}"
            if cover_path.exists():
                return str(cover_path.relative_to(project_paths['workspace']))
        return None

    def format_book_card(self, book: dict) -> dict:
        """Format book information for template display"""
        cover_path = self.get_book_cover_path(book['book_id'])
        
        return {
            'read_id': book['read_id'],
            'book_id': book['book_id'],
            'title': book['title'],
            'author': self.format_author_name(book.get('author_name_first'), book.get('author_name_second')),
            'cover_url': f"/{cover_path}" if cover_path else None,
            'media': book['media'],
            'date_started': book.get('date_started'),
            'date_finished_actual': book.get('date_finished_actual'),
            'date_est_start': book.get('date_est_start'),
            'date_est_end': book.get('date_est_end'),
            'is_current': book.get('is_current', False),
            'is_future': book.get('is_future', False)
        }

    def generate_chain_report(self) -> Tuple[str, bool]:
        """
        Generate an HTML report of all reading chains.
        
        Returns:
            Tuple of (output_file_path, success)
        """
        try:
            paths = get_project_paths()
            
            # Ensure reports directory exists
            reports_dir = paths['root'] / 'reports'
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Get template directory
            template_dir = paths['templates'] / 'reports' / 'chain'
            
            # Setup Jinja environment
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template('reading_chain.html')
            
            # Generate report data
            chains = {
                'kindle': {'chain': self.queries.get_reading_chain_by_media('kindle')},
                'hardcover': {'chain': self.queries.get_reading_chain_by_media('hardcover')},
                'audio': {'chain': self.queries.get_reading_chain_by_media('audio')}
            }
            
            # Media type colors
            media_colors = {
                'kindle': {'text_color': '#37A0E8'},    # Kindle blue
                'hardcover': {'text_color': '#6B4BA3'}, # Space purple
                'audio': {'text_color': '#F6911E'}      # Audible orange
            }
            
            # Render template
            output = template.render(
                title="Reading Chains",
                description="Current and upcoming books in each reading chain",
                chains=chains,
                media_colors=media_colors,
                generated_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            # Write output
            output_file = reports_dir / 'reading_chains.html'
            output_file.write_text(output)
            
            return str(output_file), True
        
        except Exception as e:
            return f"Error generating report: {str(e)}", False

    def preview_chain_updates(self) -> List[Dict]:
        """Preview changes that would be made to chain dates"""
        preview_changes = []
        
        readings = (self.session.query(Reading)
                   .filter(Reading.date_finished_actual.is_(None))
                   .order_by(Reading.id)
                   .all())
        
        for reading in readings:
            if not reading.days_estimate:
                continue

            # Gather additional verification data
            base_data = {
                'id': reading.id,
                'title': reading.book.title,
                'media': reading.media,
                'word_count': reading.book.word_count,
                'days_estimate': reading.days_estimate,
                'current_start': reading.date_est_start,
                'current_end': reading.date_est_end,
            }

            if reading.date_started:
                estimated_end = reading.date_started + timedelta(days=reading.days_estimate - 1)
                
                if estimated_end != reading.date_est_end:
                    preview_changes.append({
                        **base_data,
                        'new_start': reading.date_started,
                        'new_end': estimated_end,
                        'has_actual_start': True
                    })
            
            elif reading.id_previous:
                prev_reading = self.session.get(Reading, reading.id_previous)
                if prev_reading and prev_reading.date_est_end:
                    estimated_start = prev_reading.date_est_end + timedelta(days=1)
                    estimated_end = estimated_start + timedelta(days=reading.days_estimate - 1)
                    
                    if (estimated_start != reading.date_est_start or 
                        estimated_end != reading.date_est_end):
                        preview_changes.append({
                            **base_data,
                            'new_start': estimated_start,
                            'new_end': estimated_end,
                            'has_actual_start': False
                        })
        
        preview_changes.sort(key=lambda x: x['new_start'] or date.max)
        return preview_changes

    def display_chain_updates_preview(self, changes: List[Dict]) -> None:
        """Display preview of chain date changes"""
        if not changes:
            console.print("[yellow]No chain date updates needed[/yellow]")
            return

        table = Table(title="Proposed Chain Date Updates")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Media", style="magenta", width=12)
        table.add_column("Book Title", style="blue")
        table.add_column("Words", justify="right", style="green")
        table.add_column("Est. Days", justify="right", style="yellow")
        table.add_column("Current Est. Start", justify="center")
        table.add_column("New Est. Start", justify="center")
        table.add_column("Current Est. End", justify="center")
        table.add_column("New Est. End", justify="center")

        for change in changes:
            # Format word count with commas
            word_count = f"{change['word_count']:,}" if change['word_count'] else "N/A"
            
            current_start = str(change['current_start'] or '')
            new_start = str(change['new_start'] or '')
            if change.get('has_actual_start'):
                current_start = new_start = str(change['new_start'])

            table.add_row(
                str(change['id']),
                change['media'],
                change['title'][:50],
                word_count,
                str(change['days_estimate']),
                current_start,
                new_start,
                str(change['current_end'] or ''),
                str(change['new_end'] or '')
            )

        console.print(table)
        console.print(f"\nTotal changes: {len(changes)}")

    def preview_days_estimate_updates(self) -> List[Dict]:
        """Preview changes that would be made to days_estimate values"""
        preview_changes = []
        readings = self.get_all_readings()

        for reading in readings:
            if not reading.book.word_count or not reading.media:
                continue

            media_lower = reading.media.lower()
            words_per_day = READING_SPEEDS.get(media_lower, DEFAULT_WPD)
            old_estimate = reading.days_estimate
            # Changed from int() to math.ceil()
            new_estimate = math.ceil(reading.book.word_count / words_per_day)

            if old_estimate != new_estimate:
                preview_changes.append({
                    'id': reading.id,
                    'title': reading.book.title,
                    'current_estimate': old_estimate,
                    'new_estimate': new_estimate,
                    'word_count': reading.book.word_count,
                    'media': reading.media
                })

        return preview_changes

    def display_days_estimate_preview(self, changes: List[Dict]) -> None:
        """Display preview of days estimate changes"""
        if not changes:
            console.print("[yellow]No days estimate updates needed[/yellow]")
            return

        table = Table(title="Proposed Days Estimate Updates")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Book Title", style="blue")
        table.add_column("Media", style="magenta")
        table.add_column("Word Count", justify="right", style="yellow")
        table.add_column("Current Est.", justify="right", style="red")
        table.add_column("New Est.", justify="right", style="green")

        for change in changes:
            table.add_row(
                str(change['id']),
                change['title'][:50],
                change['media'],
                f"{change['word_count']:,}",
                str(change['current_estimate'] or 'None'),
                str(change['new_estimate'])
            )

        console.print(table)
        console.print(f"\nTotal changes: {len(changes)}")

    def apply_days_estimate_updates(self, changes: List[Dict]) -> int:
        """Apply the previewed days estimate updates"""
        updates_count = 0
        
        for change in changes:
            reading = self.session.get(Reading, change['id'])
            if reading:
                reading.days_estimate = change['new_estimate']
                updates_count += 1

        return updates_count

    def apply_chain_updates(self, changes: List[Dict]) -> int:
        """Apply the previewed chain date updates"""
        updates_count = 0
        
        for change in changes:
            reading = self.session.get(Reading, change['id'])
            if reading:
                reading.date_est_start = change['new_start']
                reading.date_est_end = change['new_end']
                updates_count += 1

        return updates_count
