"""Service for analyzing book cover image quality."""
from pathlib import Path
from typing import List, Dict, NamedTuple
from PIL import Image
from rich.console import Console
from rich.table import Table
from ..utils.paths import get_project_paths

class CoverQuality(NamedTuple):
    book_id: int
    filename: str
    width: int
    height: int
    file_size_kb: float
    is_high_quality: bool
    reason: str

class CoverAnalyzer:
    def __init__(self, 
                 min_width: int = 250,  # Previously reduced from 400
                 min_height: int = 400,  # Previously reduced from 600
                 min_file_size_kb: float = 20.0):  # Reduced from 50.0
        self.console = Console()
        self.project_paths = get_project_paths()
        self.covers_path = self.project_paths['assets'] / 'book_covers'
        self.min_width = min_width
        self.min_height = min_height
        self.min_file_size_kb = min_file_size_kb

    def analyze_covers(self) -> List[CoverQuality]:
        """
        Analyze all book covers and return quality information.
        """
        results = []
        
        for cover_file in self.covers_path.glob('*.jp*g'):
            try:
                # Extract book ID from filename
                book_id = int(cover_file.stem)
                
                # Skip fallback image (cover 0)
                if book_id == 0:
                    continue
                
                # Get file size in KB
                file_size_kb = cover_file.stat().st_size / 1024
                
                # Get image dimensions
                with Image.open(cover_file) as img:
                    width, height = img.size
                
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
                
                reason = " and ".join(reasons) if reasons else "meets quality standards"
                
                results.append(CoverQuality(
                    book_id=book_id,
                    filename=cover_file.name,
                    width=width,
                    height=height,
                    file_size_kb=file_size_kb,
                    is_high_quality=is_high_quality,
                    reason=reason
                ))
                
            except Exception as e:
                self.console.print(f"[red]Error analyzing {cover_file}: {str(e)}[/red]")
        
        return sorted(results, key=lambda x: (x.is_high_quality, x.book_id))

    def print_analysis(self, results: List[CoverQuality]):
        """Print analysis results in a formatted table."""
        table = Table(title="Book Cover Quality Analysis")
        
        table.add_column("Book ID", justify="right", style="cyan")
        table.add_column("Dimensions", justify="right")
        table.add_column("Size (KB)", justify="right")
        table.add_column("Quality", justify="center")
        table.add_column("Reason", justify="left")
        
        for result in results:
            quality_style = "green" if result.is_high_quality else "red"
            quality_text = "HIGH" if result.is_high_quality else "LOW"
            
            table.add_row(
                str(result.book_id),
                f"{result.width}x{result.height}",
                f"{result.file_size_kb:.1f}",
                f"[{quality_style}]{quality_text}[/{quality_style}]",
                result.reason
            )
        
        self.console.print(table)
        
        # Print summary
        low_quality = [r for r in results if not r.is_high_quality]
        self.console.print(f"\nFound {len(low_quality)} low-quality covers out of {len(results)} total.")
        if low_quality:
            self.console.print("\nLow-quality book IDs:")
            self.console.print(" ".join(str(r.book_id) for r in low_quality))

def analyze_book_covers():
    """CLI entry point for cover analysis."""
    analyzer = CoverAnalyzer()
    results = analyzer.analyze_covers()
    analyzer.print_analysis(results)
    return [r.book_id for r in results if not r.is_high_quality]