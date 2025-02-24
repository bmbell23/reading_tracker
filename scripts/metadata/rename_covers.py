#!/usr/bin/env python3
from pathlib import Path
import re
from rich.console import Console
from rich.progress import Progress

def rename_covers():
    """Rename book cover files to remove 'book_' prefix"""
    console = Console()

    # Get the project root directory and construct path to covers
    project_root = Path(__file__).parent.parent.parent
    covers_path = project_root / 'assets' / 'book_covers'

    if not covers_path.exists():
        console.print(f"[red]Error: Cover directory not found at {covers_path}[/red]")
        return

    # Get all cover files
    cover_files = list(covers_path.glob('book_*.*'))

    with Progress() as progress:
        task = progress.add_task("[cyan]Renaming cover files...", total=len(cover_files))

        for file_path in cover_files:
            # Extract the number and extension
            match = re.match(r'book_(\d+)(\.(?:jpg|jpeg|png|webp))$', file_path.name)
            if match:
                number, ext = match.groups()
                new_name = covers_path / f"{number}{ext}"

                try:
                    file_path.rename(new_name)
                    progress.advance(task)
                except Exception as e:
                    console.print(f"[red]Error renaming {file_path}: {str(e)}[/red]")

    console.print("[green]Cover files renamed successfully![/green]")

if __name__ == "__main__":
    rename_covers()