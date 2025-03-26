"""Service for generating reading statistics"""
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from ..queries.common_queries import CommonQueries

class ReadingStatsService:
    def __init__(self):
        self.console = Console()
        self.queries = CommonQueries()

    def display_author_stats(self):
        """Display statistics about books read by author"""
        stats = self.queries.get_books_by_author()
        
        if not stats:
            self.console.print("[yellow]No reading statistics found[/yellow]")
            return

        table = Table(title="Books Read by Author")
        
        table.add_column("Author", style="cyan", no_wrap=True)
        table.add_column("Total Books", justify="right", style="green")
        table.add_column("Total Readings", justify="right", style="blue")
        table.add_column("Completed", justify="right", style="purple")
        
        for stat in stats:
            table.add_row(
                stat['author'],
                str(stat['total_books']),
                str(stat['total_readings']),
                str(stat['completed_readings'])
            )
        
        self.console.print(table)