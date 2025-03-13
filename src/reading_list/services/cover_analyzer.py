"""Service for analyzing book cover image quality."""
from pathlib import Path
from typing import List, Dict, NamedTuple
from PIL import Image
from rich.console import Console
from rich.table import Table
from sqlalchemy import text
from ..models.base import engine
from ..utils.paths import get_project_paths

class CoverQuality(NamedTuple):
    book_id: int
    filename: str
    width: int
    height: int
    file_size_kb: float
    aspect_ratio: float
    is_high_quality: bool
    reason: str

class MissingCover(NamedTuple):
    book_id: int
    title: str
    author: str

class CoverAnalyzer:
    def __init__(self, 
                 min_width: int = 250,
                 min_height: int = 400,
                 min_file_size_kb: float = 20.0,
                 min_aspect_ratio: float = 0.5,
                 max_aspect_ratio: float = 0.8):
        self.console = Console()
        self.project_paths = get_project_paths()
        self.covers_path = self.project_paths['assets'] / 'book_covers'
        self.min_width = min_width
        self.min_height = min_height
        self.min_file_size_kb = min_file_size_kb
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
        
        # Load placeholder image hash
        placeholder_path = self.covers_path / "0.jpg"
        if placeholder_path.exists():
            with open(placeholder_path, 'rb') as f:
                self.placeholder_hash = hash(f.read())
        else:
            self.placeholder_hash = None

    def is_placeholder_image(self, file_path: Path) -> bool:
        """Check if the given file is identical to the placeholder image."""
        if self.placeholder_hash is None:
            return False
            
        with open(file_path, 'rb') as f:
            return hash(f.read()) == self.placeholder_hash

    def get_missing_covers(self) -> List[MissingCover]:
        """Get list of books that are missing covers."""
        # Update cover status using existing command
        from ..operations.cover_operations import update_cover_status
        update_cover_status()
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    b.id,
                    b.title,
                    CASE
                        WHEN b.author_name_second IS NOT NULL
                        THEN b.author_name_first || ' ' || b.author_name_second
                        ELSE b.author_name_first
                    END as author
                FROM books b
                WHERE b.cover = FALSE
                ORDER BY b.id
            """))
            return [MissingCover(row[0], row[1], row[2]) for row in result]

    def analyze_covers(self) -> List[CoverQuality]:
        """Analyze all book covers and return quality information."""
        results = []
        placeholder_covers = []
        
        for cover_file in self.covers_path.glob('*.jp*g'):
            try:
                # Extract book ID from filename
                book_id = int(cover_file.stem)
                
                # Skip fallback image (cover 0)
                if book_id == 0:
                    continue
                
                # Check if it's a placeholder image
                if self.is_placeholder_image(cover_file):
                    placeholder_covers.append(book_id)
                    results.append(CoverQuality(
                        book_id=book_id,
                        filename=cover_file.name,
                        width=265,  # Known placeholder dimensions
                        height=400,
                        aspect_ratio=0.66,
                        file_size_kb=18.5,
                        is_high_quality=True,  # Don't mark as low quality
                        reason="placeholder cover image"
                    ))
                    continue
                
                # Get file size in KB
                file_size_kb = cover_file.stat().st_size / 1024
                
                # Get image dimensions
                with Image.open(cover_file) as img:
                    width, height = img.size
                
                # Calculate aspect ratio (width/height)
                aspect_ratio = width / height
                
                # Determine quality and reason
                is_high_quality = True
                reasons = []
                
                if width < self.min_width:
                    is_high_quality = False
                    reasons.append(f"width ({width}px < {self.min_width}px)")
                
                if height < self.min_height:
                    is_high_quality = False
                    reasons.append(f"height ({height}px < {self.min_height}px)")
                
                if file_size_kb < self.min_file_size_kb:
                    is_high_quality = False
                    reasons.append(f"file size ({file_size_kb:.1f}KB < {self.min_file_size_kb}KB)")
                
                if aspect_ratio > self.max_aspect_ratio:
                    is_high_quality = False
                    reasons.append(f"too wide ({aspect_ratio:.2f} > {self.max_aspect_ratio})")
                elif aspect_ratio < self.min_aspect_ratio:
                    is_high_quality = False
                    reasons.append(f"too narrow ({aspect_ratio:.2f} < {self.min_aspect_ratio})")
                elif abs(aspect_ratio - 1.0) < 0.1:  # Check if close to square
                    is_high_quality = False
                    reasons.append(f"too square (ratio {aspect_ratio:.2f})")
                
                reason = " and ".join(reasons) if reasons else "meets quality standards"
                
                results.append(CoverQuality(
                    book_id=book_id,
                    filename=cover_file.name,
                    width=width,
                    height=height,
                    aspect_ratio=aspect_ratio,
                    file_size_kb=file_size_kb,
                    is_high_quality=is_high_quality,
                    reason=reason
                ))
                
            except Exception as e:
                self.console.print(f"[red]Error analyzing {cover_file}: {str(e)}[/red]")
        
        if placeholder_covers:
            self.console.print(f"\n[yellow]Warning: Found {len(placeholder_covers)} placeholder covers: {', '.join(map(str, sorted(placeholder_covers)))}[/yellow]")
        
        return sorted(results, key=lambda x: (x.is_high_quality, x.book_id))

    def print_analysis(self, results: List[CoverQuality]):
        """Print analysis results in a formatted table."""
        # First print existing covers analysis
        if results:
            table = Table(title="Book Cover Quality Analysis")
            
            table.add_column("Book ID", justify="right", style="cyan")
            table.add_column("Dimensions", justify="right")
            table.add_column("Ratio", justify="right")
            table.add_column("Size (KB)", justify="right")
            table.add_column("Quality", justify="center")
            table.add_column("Reason", justify="left")
            
            for result in results:
                quality_style = "green" if result.is_high_quality else "red"
                quality_text = "HIGH" if result.is_high_quality else "LOW"
                
                table.add_row(
                    str(result.book_id),
                    f"{result.width}x{result.height}",
                    f"{result.aspect_ratio:.2f}",
                    f"{result.file_size_kb:.1f}",
                    f"[{quality_style}]{quality_text}[/{quality_style}]",
                    result.reason
                )
            
            self.console.print(table)
            
            # Print summary of existing covers
            low_quality = [r for r in results if not r.is_high_quality]
            self.console.print(f"\nFound {len(low_quality)} low-quality covers out of {len(results)} total.")
        
        # Get and print missing covers
        missing_covers = self.get_missing_covers()
        if missing_covers:
            missing_table = Table(title="\nMissing Covers", style="red")
            
            missing_table.add_column("Book ID", justify="right", style="cyan")
            missing_table.add_column("Title", style="white")
            missing_table.add_column("Author", style="white")
            
            for missing in missing_covers:
                missing_table.add_row(
                    str(missing.book_id),
                    missing.title,
                    missing.author
                )
            
            self.console.print(missing_table)
            self.console.print(f"\n[red]Found {len(missing_covers)} books missing covers.[/red]")
        
        return [r.book_id for r in results if not r.is_high_quality] + [m.book_id for m in missing_covers]

def analyze_book_covers():
    """CLI entry point for cover analysis."""
    analyzer = CoverAnalyzer()
    results = analyzer.analyze_covers()
    return analyzer.print_analysis(results)
