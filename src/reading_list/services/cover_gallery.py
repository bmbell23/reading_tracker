"""Service for generating book cover gallery."""
from pathlib import Path
from datetime import datetime
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
        self.output_path = self.paths['reports'] / 'chain' / 'cover_gallery.html'
        
        # Create chain reports directory if it doesn't exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def generate(self, debug=False):
        """Generate an HTML gallery of all book covers."""
        try:
            self.console.print("[blue]Generating cover gallery...[/blue]")

            books = []
            with engine.connect() as conn:
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
                    cover_file = None
                    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        check_path = self.covers_path / f"{row.id}{ext}"
                        if check_path.exists():
                            cover_file = f"{row.id}{ext}"
                            break
                    
                    if cover_file:
                        books.append({
                            'id': row.id,
                            'title': row.title,
                            'author': row.author,
                            'cover_path': f"/assets/book_covers/{cover_file}"
                        })

            # Add timestamp for cache busting
            timestamp = int(datetime.now().timestamp())

            # Generate HTML
            html_content = self._get_template().render(
                books=books,
                timestamp=timestamp
            )

            # Write to file
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self.console.print(f"[green]Gallery generated with {len(books)} covers[/green]")

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
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .cover-img {
            width: 100%;
            height: auto;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .book-info {
            text-align: center;
        }
        .book-title {
            font-weight: bold;
            margin-bottom: 5px;
            color: #2c3e50;
        }
        .book-author {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .book-id {
            color: #95a5a6;
            font-size: 0.8em;
            margin-top: 5px;
        }
        .stats {
            text-align: center;
            margin-bottom: 20px;
            color: #7f8c8d;
        }
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Add cache buster to all cover images
            document.querySelectorAll('.cover-img').forEach(img => {
                const url = new URL(img.src, window.location.href);
                url.searchParams.set('v', '{{ timestamp }}');
                img.src = url.href;
            });
        });
    </script>
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
