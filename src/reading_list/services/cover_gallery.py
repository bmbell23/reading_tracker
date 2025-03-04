"""Service for generating book cover gallery."""
from pathlib import Path
from jinja2 import Template
from rich.console import Console
from sqlalchemy import text

from ..models.base import engine
from ..utils.paths import get_project_paths

class CoverGalleryGenerator:
    def __init__(self):
        self.console = Console()
        self.paths = get_project_paths()
        self.covers_path = self.paths['assets'] / 'book_covers'
        self.output_path = self.paths['reports'] / 'cover_gallery.html'
        
        # Create reports directory if it doesn't exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def generate(self, debug=False):
        """Generate an HTML gallery of all book covers."""
        try:
            self.console.print("[blue]Generating cover gallery...[/blue]")

            if debug:
                self.console.print(f"Looking for covers in: {self.covers_path}")
                self.console.print(f"Covers directory exists: {self.covers_path.exists()}")
                
                if self.covers_path.exists():
                    self.console.print("Files in covers directory:")
                    for file in self.covers_path.iterdir():
                        self.console.print(f"  - {file.name}")

            books = []
            with engine.connect() as conn:
                if debug:
                    result = conn.execute(text("SELECT COUNT(*) FROM books WHERE cover = TRUE"))
                    count = result.scalar()
                    self.console.print(f"Books with cover=True in database: {count}")

                result = conn.execute(text("""
                    SELECT
                        b.id,
                        b.title,
                        CASE
                            WHEN b.author_name_first IS NOT NULL AND b.author_name_second IS NOT NULL 
                            THEN b.author_name_first || ' ' || b.author_name_second
                            ELSE COALESCE(b.author_name_first, b.author_name_second, 'Unknown Author')
                        END as author
                    FROM books b
                    WHERE b.cover = TRUE
                    ORDER BY b.title
                """))
                
                for row in result:
                    if debug:
                        self.console.print(f"\nChecking book ID {row.id}: {row.title}")
                    
                    cover_file = None
                    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        check_path = self.covers_path / f"{row.id}{ext}"
                        if debug:
                            self.console.print(f"  Checking for {check_path}")
                        if check_path.exists():
                            cover_file = f"{row.id}{ext}"
                            if debug:
                                self.console.print(f"  Found cover: {cover_file}")
                            break
                    
                    if cover_file:
                        books.append({
                            'id': row.id,
                            'title': row.title,
                            'author': row.author,
                            'cover_path': f"/assets/book_covers/{cover_file}"
                        })
                    elif debug:
                        self.console.print(f"  No cover found for book ID {row.id}")

            # Generate HTML
            html_content = self._get_template().render(books=books)

            # Write to file
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self.console.print(f"[green]Gallery generated successfully at {self.output_path}[/green]")
            self.console.print(f"Found covers for [blue]{len(books)}[/blue] books")

        except Exception as e:
            self.console.print(f"[red]Error generating gallery: {str(e)}[/red]")
            raise

    def _get_template(self) -> Template:
        """Return the Jinja2 template for the gallery."""
        return Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Book Cover Gallery</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            padding: 20px;
        }
        .book-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .book-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .cover-img {
            width: 100%;
            height: 280px;
            object-fit: cover;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .book-info {
            text-align: center;
        }
        .book-title {
            font-weight: 600;
            margin: 5px 0;
            color: #2c3e50;
        }
        .book-author {
            color: #7f8c8d;
            margin: 5px 0;
        }
        .book-id {
            color: #95a5a6;
            font-size: 0.8em;
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
        }
        .stats {
            text-align: center;
            margin-bottom: 20px;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <h1>Book Cover Gallery</h1>
    <div class="stats">
        Total Books with Covers: {{ books|length }}
    </div>
    <div class="gallery">
        {% for book in books %}
        <div class="book-card">
            <img src="{{ book.cover_path }}" alt="Cover of {{ book.title }}" class="cover-img">
            <div class="book-info">
                <div class="book-title">{{ book.title }}</div>
                <div class="book-author">{{ book.author }}</div>
                <div class="book-id">ID: {{ book.id }}</div>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
""")
