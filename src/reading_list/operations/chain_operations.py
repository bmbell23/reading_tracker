"""
Chain Operations
===============

Core functionality for manipulating reading chains and managing chain-related operations.
"""

from typing import List, Tuple, Optional, Dict, Any
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
        Get segments of the chain before and after a position.

        Args:
            chain: List of readings
            position: Position in chain to center on
            window: Number of items to include before and after (default 2)

        Returns:
            Tuple of (before_segment, after_segment)
        """
        if not chain:
            return [], []

        # Ensure position is within bounds
        if position < 0 or position >= len(chain):
            return [], []

        # Get before segment
        start = max(0, position - window)
        before = chain[start:position]

        # Get after segment
        after = chain[position + 1:position + window + 1]

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

    def reorder_reading_chain(self, reading_id: int, target_id: int) -> Tuple[bool, str, Dict]:
        """Reorder a reading chain by moving a reading after a target reading"""
        try:
            console.print("[dim]Debug: Starting chain reorder[/dim]")
            console.print(f"[dim]Debug: Moving reading {reading_id} after {target_id}[/dim]")

            # Get the readings
            reading_to_move = self.session.get(Reading, reading_id)
            if not reading_to_move:
                return False, f"Reading {reading_id} not found", None

            target_reading = self.session.get(Reading, target_id)
            if not target_reading:
                return False, f"Target reading {target_id} not found", None

            # Check if we're trying to move a book to where it already is
            if reading_to_move.id_previous == target_reading.id:
                return False, "Book is already in the requested position", None

            # Get chain states before changes
            chain_state = self._get_chain_state(reading_to_move, target_reading)

            # Store original media type for chain state display
            original_media = reading_to_move.media

            # Update media type if moving between different media chains
            if target_reading.media != reading_to_move.media:
                reading_to_move.media = target_reading.media

            # Perform the actual reorder
            # 1. Update the reading that previously pointed to our moving reading
            if reading_to_move.id_previous:
                previous_reading = self.session.get(Reading, reading_to_move.id_previous)
                next_after_moving = self.session.query(Reading).filter(Reading.id_previous == reading_to_move.id).first()
                if previous_reading and next_after_moving:
                    next_after_moving.id_previous = previous_reading.id

            # 2. Update the reading that was pointing to our target's next reading
            next_after_target = self.session.query(Reading).filter(Reading.id_previous == target_reading.id).first()
            if next_after_target and next_after_target.id != reading_to_move.id:
                next_after_target.id_previous = reading_to_move.id

            # 3. Update our moving reading to point to target's previous next reading
            reading_to_move.id_previous = target_reading.id

            # Get chain states after changes, but use original media for the "before" state
            new_chain_state = self._get_chain_state(reading_to_move, target_reading)
            chain_state['original']['source']['segment'] = [
                {**book, 'media': original_media if book['id'] == reading_id else book['media']}
                for book in chain_state['original']['source']['segment']
            ]
            chain_state['original']['target']['segment'] = [
                {**book, 'media': original_media if book['id'] == reading_id else book['media']}
                for book in chain_state['original']['target']['segment']
            ]
            
            chain_info = {
                'original': chain_state['original'],
                'new': new_chain_state['new']
            }

            return True, "Chain reorder prepared", chain_info

        except Exception as e:
            console.print(f"[red]Debug: Error in reorder_reading_chain: {str(e)}[/red]")
            return False, f"Error during chain reorder: {str(e)}", None

    def update_chain_dates(self, reading: Reading) -> Tuple[int, int]:
        """Update dates for a single reading in the chain"""
        updates = 0
        skipped = 0
        
        try:
            # Get current dates for logging
            old_start = reading.date_est_start
            old_end = reading.date_est_end
            
            if reading.id_previous:
                # Get fresh data for previous reading
                prev_reading = (
                    self.session.query(Reading)
                    .filter(Reading.id == reading.id_previous)
                    .first()
                )

                # Determine the end date to use: actual finish date takes priority over estimated end date
                prev_end_date = None
                if prev_reading:
                    if prev_reading.date_finished_actual:
                        prev_end_date = prev_reading.date_finished_actual
                    elif prev_reading.date_est_end:
                        prev_end_date = prev_reading.date_est_end

                if not prev_end_date:
                    print("  SKIP: Previous reading missing end date (actual or estimated)")
                    return 0, 1

                new_start = prev_end_date + timedelta(days=1)
                
                if reading.date_est_start != new_start:
                    reading.date_est_start = new_start
                    updates += 1
                    
            if reading.date_est_start and reading.days_estimate:
                new_end = reading.date_est_start + timedelta(days=reading.days_estimate - 1)
                
                if reading.date_est_end != new_end:
                    reading.date_est_end = new_end
                    updates += 1
            else:
                print(f"  SKIP: Missing start date or days estimate")
                skipped += 1
            
            if updates > 0:
                print(f"  UPDATED: {reading.book.title[:40]}")
                print(f"    Start: {old_start} -> {reading.date_est_start}")
                print(f"    End:   {old_end} -> {reading.date_est_end}")
            
        except Exception as e:
            print(f"ERROR updating reading {reading.id}: {str(e)}")
            skipped += 1
        
        return updates, skipped

    def update_all_chain_dates(self) -> Tuple[int, int]:
        """Update estimated dates for all reading chains"""
        total_updates = 0
        total_skipped = 0
        
        # Update each media type separately and allow user to confirm each
        for media_type in ['kindle', 'hardcover', 'audio']:
            print(f"\n{'='*50}")
            print(f"Processing {media_type.upper()} chain")
            print(f"{'='*50}")
            
            updates, skipped = self.update_single_media_chain(media_type)
            
            print(f"\nCompleted {media_type.upper()} chain:")
            print(f"Total updates: {updates}")
            print(f"Total skipped: {skipped}")
            
            total_updates += updates
            total_skipped += skipped
            
            # Commit changes for this media type
            self.session.commit()
            
            input(f"\nPress Enter to continue to next media type...")

        return total_updates, total_skipped

    def update_single_media_chain(self, media_type: str) -> Tuple[int, int]:
        """Update chain dates for a single media type"""
        iteration = 0
        total_updates = 0
        total_skipped = 0
        max_iterations = 50
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\nIteration {iteration}:")
            print("-" * 20)
            
            # Clear SQLAlchemy session to avoid stale data
            self.session.expire_all()
            
            # Get chain in order
            chain = self._get_ordered_chain(media_type)
            if not chain:
                print(f"No active chain found for {media_type}")
                break
                
            # Track changes in this iteration
            iteration_updates = 0
            iteration_skipped = 0
            
            # Process each reading in the chain
            for i, reading in enumerate(chain):
                print(f"\nProcessing book {i+1}/{len(chain)}: {reading.book.title[:40]}")
                
                updates, skipped = self.update_chain_dates(reading)
                iteration_updates += updates
                iteration_skipped += skipped
                
                # Commit after each book to ensure changes propagate
                if updates > 0:
                    self.session.commit()
            
            # Add to totals
            total_updates += iteration_updates
            total_skipped += iteration_skipped
            
            print(f"\nIteration {iteration} results:")
            print(f"  Updates: {iteration_updates}")
            print(f"  Skipped: {iteration_skipped}")
            
            # If no updates were made in this iteration, we're done
            if iteration_updates == 0:
                print(f"\nNo more changes needed for {media_type} chain")
                break
                
            # Commit changes for this iteration
            self.session.commit()
        
        if iteration >= max_iterations:
            print(f"WARNING: Reached maximum iterations ({max_iterations})")
        
        return total_updates, total_skipped

    def _get_ordered_chain(self, media_type: str) -> List[Reading]:
        """Get readings in correct chain order for a media type"""
        # First get the chain start
        chain_start = (
            self.session.query(Reading)
            .filter(
                Reading.id_previous.is_(None),
                Reading.media.ilike(media_type),
                Reading.date_finished_actual.is_(None)  # Only include unfinished readings
            )
            .first()
        )
        
        if not chain_start:
            return []
            
        # Build the ordered chain
        ordered_chain = [chain_start]
        current = chain_start
        
        # Follow the chain using subsequent_readings
        while True:
            next_reading = (
                self.session.query(Reading)
                .filter(
                    Reading.id_previous == current.id,
                    Reading.date_finished_actual.is_(None)  # Only include unfinished readings
                )
                .first()
            )
            
            if not next_reading:
                break
                
            ordered_chain.append(next_reading)
            current = next_reading
        
        return ordered_chain

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

    def preview_chain_updates(self, media_type: str = None) -> List[Dict]:
        """Preview ALL possible changes that would be made to chain dates"""
        all_changes = {}  # Use dict to track unique changes by reading ID
        iteration = 0
        max_iterations = 50
        
        while iteration < max_iterations:
            iteration += 1
            new_changes_found = False

            query = self.session.query(Reading).filter(Reading.date_finished_actual.is_(None))
            if media_type:
                query = query.filter(Reading.media.ilike(media_type))
            readings = query.order_by(Reading.id).all()

            for reading in readings:
                if not reading.days_estimate:
                    continue

                reading_id = reading.id
                current_change = {
                    'id': reading_id,
                    'title': reading.book.title,
                    'media': reading.media,
                    'word_count': reading.book.word_count,
                    'days_estimate': reading.days_estimate,
                    'current_start': reading.date_est_start,
                    'current_end': reading.date_est_end,
                }

                new_start = None
                new_end = None

                if reading.date_started:
                    new_start = reading.date_started
                    new_end = reading.date_started + timedelta(days=reading.days_estimate - 1)
                elif reading.id_previous:
                    prev_reading = self.session.get(Reading, reading.id_previous)
                    if prev_reading:
                        # Determine the end date to use: actual finish date takes priority
                        prev_end = None
                        if prev_reading.date_finished_actual:
                            prev_end = prev_reading.date_finished_actual
                        elif prev_reading.date_est_end:
                            # Use either actual end date from previous changes or current end date
                            prev_end = all_changes.get(prev_reading.id, {}).get(
                                'new_end', prev_reading.date_est_end)

                        if prev_end:
                            new_start = prev_end + timedelta(days=1)
                            new_end = new_start + timedelta(days=reading.days_estimate - 1)

                if new_start and new_end:
                    if (new_start != reading.date_est_start or new_end != reading.date_est_end):
                        current_change.update({
                            'new_start': new_start,
                            'new_end': new_end,
                            'has_actual_start': bool(reading.date_started)
                        })
                        
                        # Check if this is a new change or different from previous iteration
                        prev_change = all_changes.get(reading_id)
                        if not prev_change or (
                            prev_change['new_start'] != new_start or 
                            prev_change['new_end'] != new_end
                        ):
                            all_changes[reading_id] = current_change
                            new_changes_found = True

            if not new_changes_found:
                break

        # Convert dict to sorted list
        changes_list = list(all_changes.values())
        changes_list.sort(key=lambda x: x['new_start'] or date.max)
        return changes_list

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

    def preview_days_estimate_updates(self, media_type: str = None) -> List[Dict]:
        """Preview changes that would be made to days_estimate values"""
        preview_changes = []
        readings = self.get_all_readings()

        for reading in readings:
            # Skip if no word count or wrong media type
            if not reading.book.word_count or not reading.media:
                continue
            if media_type and reading.media.lower() != media_type.lower():
                continue

            media_lower = reading.media.lower()
            words_per_day = READING_SPEEDS.get(media_lower, DEFAULT_WPD)
            old_estimate = reading.days_estimate
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

    def get_chain_window(self, reading: Reading, window: int = 2) -> List[Dict]:
        """Get a window of readings around the given reading"""
        try:
            # Get books before
            before = []
            current = reading
            for _ in range(window):
                if current.id_previous:
                    prev = self.session.get(Reading, current.id_previous)
                    if prev:
                        before.insert(0, {
                            'read_id': prev.id,
                            'media': prev.media,
                            'title': prev.book.title,
                            'chain': {'previous_id': prev.id_previous}
                        })
                        current = prev
                    else:
                        break
                else:
                    break

            # Current reading
            current_dict = {
                'read_id': reading.id,
                'media': reading.media,
                'title': reading.book.title,
                'chain': {'previous_id': reading.id_previous}
            }

            # Get books after
            after = []
            current = reading
            for _ in range(window):
                next_reading = (self.session.query(Reading)
                              .filter(Reading.id_previous == current.id)
                              .first())
                if next_reading:
                    after.append({
                        'read_id': next_reading.id,
                        'media': next_reading.media,
                        'title': next_reading.book.title,
                        'chain': {'previous_id': next_reading.id_previous}
                    })
                    current = next_reading
                else:
                    break

            return before + [current_dict] + after

        except Exception as e:
            console.print(f"[red]Error getting chain window: {str(e)}[/red]")
            raise

    def _get_chain_state(self, reading: Reading, target: Reading) -> Dict:
        """Get the state of chains before and after reordering"""
        CONTEXT_SIZE = 2  # Number of books to show before/after the focus point
        
        try:
            # Helper function to get N previous readings
            def get_previous_n(start_reading: Reading, n: int) -> List[Reading]:
                result = []
                current = start_reading
                for _ in range(n):
                    if current.id_previous:
                        prev = self.session.get(Reading, current.id_previous)
                        if prev:
                            result.append(prev)
                            current = prev
                return list(reversed(result))  # Return in chronological order

            # Helper function to get N next readings
            def get_next_n(start_reading: Reading, n: int, exclude_id: int = None) -> List[Reading]:
                result = []
                current = start_reading
                seen_ids = set()  # Track seen reading IDs
                for _ in range(n):
                    next_reading = self.session.query(Reading).filter(
                        Reading.id_previous == current.id
                    ).first()
                    if next_reading and next_reading.id not in seen_ids and next_reading.id != exclude_id:
                        result.append(next_reading)
                        current = next_reading
                        seen_ids.add(next_reading.id)
                    else:
                        break
                return result

            # Format reading into dictionary
            def format_reading(r: Reading) -> Dict:
                next_reading = self.session.query(Reading).filter(
                    Reading.id_previous == r.id
                ).first()
                return {
                    'id': r.id,
                    'media': r.media,
                    'title': r.book.title,
                    'chain': {
                        'previous_id': r.id_previous,
                        'next_id': next_reading.id if next_reading else None
                    }
                }

            # Build original chain segments
            original_source = (
                get_previous_n(reading, CONTEXT_SIZE) +  # 2 books before
                [reading] +                              # The book being moved
                get_next_n(reading, CONTEXT_SIZE)        # 2 books after
            )
            
            original_target = (
                get_previous_n(target, CONTEXT_SIZE) +   # 2 books before
                [target] +                               # The target book
                get_next_n(target, CONTEXT_SIZE)         # 2 books after
            )

            # Build new source chain segment (with reading removed)
            prev_readings = get_previous_n(reading, CONTEXT_SIZE)
            next_readings = get_next_n(reading, CONTEXT_SIZE, exclude_id=reading.id)
            new_source = prev_readings + next_readings

            # Build new target chain segment (with reading inserted)
            new_target = (
                get_previous_n(target, CONTEXT_SIZE) +   # 2 books before
                [target] +                               # Target book
                [reading] +                              # Inserted book
                get_next_n(target, CONTEXT_SIZE, exclude_id=reading.id)  # 2 books after, excluding the moved book
            )

            return {
                'original': {
                    'source': {'segment': [format_reading(r) for r in original_source]},
                    'target': {'segment': [format_reading(r) for r in original_target]}
                },
                'new': {
                    'source': {'segment': [format_reading(r) for r in new_source]},
                    'target': {'segment': [format_reading(r) for r in new_target]}
                }
            }

        except Exception as e:
            console.print(f"[red]Error getting chain state: {str(e)}[/red]")
            raise

    def _format_reading(self, reading_dict: Dict) -> Dict:
        """Format a reading dictionary for display"""
        return {
            'id': reading_dict['read_id'],
            'title': reading_dict['title'],
            'media': reading_dict['media'],
            'chain': reading_dict['chain']
        }

    def update_reading(self, reading_id: int, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update a reading entry with new data

        Args:
            reading_id: ID of the reading to update
            update_data: Dictionary of fields to update

        Returns:
            Tuple of (success, message)
        """
        try:
            reading = self.session.get(Reading, reading_id)
            if not reading:
                return False, f"Reading {reading_id} not found"

            print(f"Debug - Update data received: {update_data}")

            # Convert date strings to date objects
            date_fields = ['date_started', 'date_finished_actual', 'date_est_start', 'date_est_end']
            for field in date_fields:
                if field in update_data and update_data[field]:
                    if isinstance(update_data[field], str):
                        try:
                            update_data[field] = datetime.strptime(update_data[field], '%Y-%m-%d').date()
                            print(f"Debug - Converted {field} to date object: {update_data[field]}")
                        except ValueError as e:
                            return False, f"Invalid date format for {field}: {str(e)}"

            # Update the reading object
            for key, value in update_data.items():
                print(f"Debug - Setting {key}={value}")
                setattr(reading, key, value)

            print("Debug - Committing changes...")
            self.session.commit()
            return True, "Reading updated successfully"

        except Exception as e:
            self.session.rollback()
            return False, f"Failed to update reading: {str(e)}"
