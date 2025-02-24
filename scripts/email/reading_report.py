"""
Daily Reading Report Generator

This script generates and sends daily reading progress reports via email.
It includes:
- Current reading progress
- Estimated completion dates
- Upcoming reading sessions
- Reading forecast for the next 10 days

Configuration:
- Requires .env file with email settings
- Uses Gmail SMTP server
- Supports HTML-formatted emails with progress bars

Usage:
    Direct: python reading_report.py
    Cron: Set up using run_daily_report.sh

Environment Variables Required:
    GMAIL_APP_PASSWORD: Gmail application-specific password
    SENDER_EMAIL: Gmail address to send from
    RECEIVER_EMAIL: Email address to receive reports
"""

import sys
import os
from pathlib import Path
from datetime import date, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from rich.console import Console
from rich.text import Text
from io import StringIO
from scripts.utils.paths import get_project_paths
from scripts.metrics.reading_status import ReadingStatus
from src.utils.progress_calculator import calculate_reading_progress
from dotenv import load_dotenv
from scripts.email.config import EMAIL_CONFIG
import requests
from urllib.parse import quote
import base64  # Add this import at the top of the file

# Load environment variables
load_dotenv()

# Get project paths
paths = get_project_paths()

class EmailReport:
    def __init__(self):
        """Initialize the reading report generator"""
        self.sender_email = EMAIL_CONFIG['sender_email']
        self.receiver_email = EMAIL_CONFIG['receiver_email']
        self.smtp_server = EMAIL_CONFIG['smtp_server']
        self.smtp_port = EMAIL_CONFIG['smtp_port']
        self.template_dir = paths['email_templates']
        self.app_password = None  # Will be loaded from environment variable
        self.google_books_url = "https://www.googleapis.com/books/v1/volumes"
        self.cover_cache = {}  # Cache cover URLs to avoid repeated API calls
        self.image_cids = {}  # Add this to store Content-IDs for images

        # Define assets path for book covers
        self.assets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'book_covers')

        # Create the book covers directory if it doesn't exist
        os.makedirs(self.assets_path, exist_ok=True)

        # Default cover as fallback
        self.default_cover_url = (
            "https://raw.githubusercontent.com/your-repo/reading-list/main/assets/generic-book-cover.png"
        )

    def _get_app_password(self):
        """Get Gmail App Password from environment variable"""
        self.app_password = os.getenv('GMAIL_APP_PASSWORD')
        if not self.app_password:
            raise ValueError(
                "Gmail App Password not found. Please set the GMAIL_APP_PASSWORD environment variable. "
                "You can generate an App Password at: https://myaccount.google.com/apppasswords"
            )

    def _get_local_cover_path(self, book_id):
        """Get image data and type for a book cover"""
        if book_id is None:
            return None, None

        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            cover_path = os.path.join(self.assets_path, f"{book_id}{ext}")  # Removed book_ prefix
            if os.path.exists(cover_path):
                with open(cover_path, 'rb') as img_file:
                    img_data = img_file.read()
                    mime_type = f"image/{ext.lstrip('.')}"
                    if mime_type == 'image/jpg':
                        mime_type = 'image/jpeg'
                    return img_data, mime_type
        return None, None

    def _get_book_cover_url(self, title, author, book_id=None):
        """Get book cover CID for email"""
        cache_key = f"{title}-{author}"
        if cache_key in self.image_cids:
            return f"cid:{self.image_cids[cache_key]}"

        # First try local storage
        if book_id:
            img_data, mime_type = self._get_local_cover_path(book_id)
            if img_data:
                cid = f"cover_{book_id}@reading.list"
                self.image_cids[cache_key] = (cid, img_data, mime_type)
                return f"cid:{cid}"

        # If not in local storage, try to fetch from APIs and save locally
        cover_url = None
        for source in [
            self._try_google_books,
            self._try_openlibrary,
            self._try_librarything,
            self._try_isbndb,
            self._try_goodreads
        ]:
            cover_url = source(title, author)
            if cover_url:
                break

        if cover_url:
            try:
                # Download and save the cover
                response = requests.get(cover_url, timeout=10)
                if response.status_code == 200:
                    img_data = response.content
                    mime_type = response.headers.get('content-type', 'image/jpeg')

                    # Save locally for future use if we have a book_id
                    if book_id:
                        ext = '.jpg' if 'jpeg' in mime_type else '.' + mime_type.split('/')[-1]
                        cover_path = os.path.join(self.assets_path, f"book_{book_id}{ext}")
                        with open(cover_path, 'wb') as f:
                            f.write(img_data)

                    # Use in current email
                    cid = f"cover_{book_id or cache_key}@reading.list"
                    self.image_cids[cache_key] = (cid, img_data, mime_type)
                    return f"cid:{cid}"
            except Exception as e:
                print(f"Error downloading cover for {title}: {str(e)}")

        # If all else fails, use default cover
        if self.default_cover_url:
            try:
                response = requests.get(self.default_cover_url, timeout=10)
                if response.status_code == 200:
                    img_data = response.content
                    mime_type = response.headers.get('content-type', 'image/png')
                    cid = f"default_cover@reading.list"
                    self.image_cids[cache_key] = (cid, img_data, mime_type)
                    return f"cid:{cid}"
            except Exception as e:
                print(f"Error loading default cover: {str(e)}")

        return ""  # Return empty string if no cover is available

    def _try_google_books(self, title, author):
        """Try to get cover from Google Books API"""
        try:
            query = quote(f"intitle:\"{title}\" inauthor:\"{author}\"")
            response = requests.get(
                f"{self.google_books_url}?q={query}&maxResults=5",
                timeout=5
            )
            data = response.json()

            if 'items' in data:
                # Try exact match first
                for item in data['items']:
                    book_info = item['volumeInfo']
                    if (book_info.get('title', '').lower() == title.lower() and
                        author.lower() in book_info.get('authors', [''])[0].lower()):
                        image_links = book_info.get('imageLinks', {})
                        cover_url = image_links.get('thumbnail') or image_links.get('smallThumbnail')
                        if cover_url:
                            return cover_url.replace('http://', 'https://')

                # Fallback to first result
                image_links = data['items'][0]['volumeInfo'].get('imageLinks', {})
                cover_url = image_links.get('thumbnail') or image_links.get('smallThumbnail')
                if cover_url:
                    return cover_url.replace('http://', 'https://')

        except Exception:
            pass
        return None

    def _try_openlibrary(self, title, author):
        """Try to get cover from OpenLibrary API"""
        try:
            clean_title = quote(title.lower().replace(' ', '+'))
            clean_author = quote(author.lower().replace(' ', '+'))

            response = requests.get(
                f"https://openlibrary.org/search.json?title={clean_title}&author={clean_author}",
                timeout=5
            )
            data = response.json()

            if data.get('docs') and len(data['docs']) > 0:
                cover_id = data['docs'][0].get('cover_i')
                if cover_id:
                    return f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"

        except Exception:
            pass
        return None

    def _try_librarything(self, title, author):
        """Try to get cover from LibraryThing"""
        # Requires API key - implement if you have one
        try:
            api_key = os.getenv('LIBRARYTHING_API_KEY')
            if not api_key:
                return None

            # Basic implementation - expand based on their API docs
            clean_title = quote(title.lower())
            response = requests.get(
                f"http://covers.librarything.com/services/rest/1.1/?method=librarything.ck.getwork"
                f"&apikey={api_key}&title={clean_title}",
                timeout=5
            )
            # Parse response and extract cover URL
            # Implementation depends on API response format

        except Exception:
            pass
        return None

    def _try_isbndb(self, title, author):
        """Try to get cover from ISBNdb"""
        try:
            api_key = os.getenv('ISBNDB_API_KEY')
            if not api_key:
                return None

            headers = {'Authorization': api_key}
            response = requests.get(
                f"https://api2.isbndb.com/book/{quote(title)}",
                headers=headers,
                timeout=5
            )
            data = response.json()

            if 'book' in data and 'image' in data['book']:
                return data['book']['image']

        except Exception:
            pass
        return None

    def _try_goodreads(self, title, author):
        """Try to get cover from Goodreads"""
        try:
            api_key = os.getenv('GOODREADS_API_KEY')
            if not api_key:
                return None

            # Note: Goodreads API is being deprecated, but still works for now
            response = requests.get(
                "https://www.goodreads.com/search/index.xml",
                params={
                    'key': api_key,
                    'q': f"{title} {author}"
                },
                timeout=5
            )

            # Parse XML response and extract cover URL
            # Implementation depends on API response format

        except Exception:
            pass
        return None

    def _format_reading_to_html(self, reading, is_current=True):
        """Format a reading entry as HTML table row"""
        today = date.today()

        # Get color based on media type
        if reading.media.lower() == 'audio':
            color = '#FB923C'  # warm orange
            bg_color = '#FFF7ED'
        elif reading.media.lower() == 'hardcover':
            color = '#A855F7'  # purple
            bg_color = '#FAF5FF'
        elif reading.media.lower() == 'kindle':
            color = '#3B82F6'  # blue
            bg_color = '#EFF6FF'
        else:
            color = '#64748B'  # slate
            bg_color = '#F8FAFC'

        # Get book cover with improved styling
        cover_url = self._get_book_cover_url(
            reading.book.title,
            reading.book.author,
            book_id=reading.book.id
        )
        print(f"DEBUG - Cover URL length: {len(cover_url) if cover_url else 0}")
        print(f"DEBUG - Cover URL start: {cover_url[:100] if cover_url else 'None'}")

        # Simplified and more robust cover HTML
        cover_html = (
            '<td class="cover-cell" style="width: 60px; padding: 8px; background: transparent; border: none;">'
            f'<img src="{cover_url}" '
            f'alt="Cover of {reading.book.title}" '
            'style="width: 60px; height: auto; border-radius: 4px; '
            'box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: block;" />'
            '</td>'
        )

        print(f"DEBUG - Final cover HTML: {cover_html}")

        # Format media badge
        media_badge = self._format_media_badge(reading.media)

        # Format title and author
        title_author = f"""
            <div style="font-weight: 600; color: #1a202c; margin-bottom: 4px;">
                {reading.book.title}
            </div>
            <div style="color: #64748b; font-size: 14px;">
                {reading.book.author}
            </div>
        """

        # Format dates and calculations
        if is_current:
            start_date = reading.date_started.strftime('%b %d, %Y') if reading.date_started else 'Not started'
            days_elapsed_num = (today - reading.date_started).days if reading.date_started else 0

            if reading.date_est_end and reading.date_started:
                # Use the same calculation as the 10-day forecast
                progress = calculate_reading_progress(reading, today)
                progress_pct = float(progress.rstrip('%')) if progress.endswith('%') else 0

                # Progress bar HTML
                progress_bar = f"""
                    <div style="width: 100%; background-color: #e2e8f0; border-radius: 9999px; height: 6px; margin-top: 8px;">
                        <div style="width: {min(100, progress_pct)}%; background-color: {color}; height: 6px; border-radius: 9999px;"></div>
                    </div>
                    <div style="color: {color}; font-weight: 600; font-size: 14px; margin-top: 4px;">
                        {int(round(progress_pct))}%<br>
                        p. {int(round((progress_pct/100) * reading.book.page_count))}
                    </div>
                """
                total_days = (reading.date_est_end - reading.date_started).days + 1
                days_elapsed = days_elapsed_num + 1
                days_to_finish = str(total_days - days_elapsed)
            else:
                progress_bar = """
                    <div style="color: #64748b; font-size: 14px;">No progress data</div>
                """
                days_to_finish = "Unknown"

            est_end_date = reading.date_est_end.strftime('%b %d, %Y') if reading.date_est_end else 'Unknown'
        else:
            start_date = reading.date_est_start.strftime('%b %d, %Y') if reading.date_est_start else 'Not scheduled'
            est_end_date = reading.date_est_end.strftime('%b %d, %Y') if reading.date_est_end else 'Unknown'
            progress_bar = ""
            days_elapsed = "0"
            days_to_finish = str((reading.date_est_end - reading.date_est_start).days) if (reading.date_est_end and reading.date_est_start) else "Unknown"

        # Create table row
        row = f"""
            <tr>
                {cover_html}
                <td>{media_badge}</td>
                <td>{title_author}</td>
                <td style="color: #64748b; font-size: 14px;">{start_date}</td>
        """

        if is_current:
            row += f"""
                <td>{progress_bar}</td>
                <td style="text-align: center; color: #64748b; font-size: 14px;">{days_elapsed}</td>
            """

        row += f"""
                <td style="text-align: center; color: #64748b; font-size: 14px;">{days_to_finish}</td>
                <td style="color: #64748b; font-size: 14px;">{est_end_date}</td>
            </tr>
        """

        return row

    def _create_html_table(self, readings, title, is_current=True):
        """Create an HTML table for readings"""
        table = f"""
        <div class="table-section">
            <h2>{title}</h2>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th class="cover-header"></th>
                            <th class="table-header">Format</th>
                            <th class="table-header">Title</th>
                            <th class="table-header">Start Date</th>
        """

        if is_current:
            table += """
                            <th class="table-header">Progress</th>
                            <th class="table-header">Days Elapsed</th>
            """

        table += """
                            <th class="table-header">Days to Finish</th>
                            <th class="table-header">Est. End Date</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for reading in readings:
            table += self._format_reading_to_html(reading, is_current)

        table += """
                    </tbody>
                </table>
            </div>
        </div>
        """

        return table

    def _create_forecast_table(self, readings):
        """Create HTML table for weekly progress forecast"""
        today = date.today()
        dates = [today + timedelta(days=i) for i in range(7)]  # Changed from 10 to 7

        # Sort readings by start date and media type
        readings = sorted(readings, key=lambda r: (
            r.date_started or r.date_est_start or date.max,
            r.media.lower()
        ))

        table = """
        <div class="table-section">
            <h2>Weekly Progress Forecast</h2>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th class="table-header">Format</th>
                            <th class="table-header">Title</th>
        """

        # Add date columns with matching header style
        for forecast_date in dates:
            day_of_week = forecast_date.strftime('%a')  # Gets abbreviated day name (Mon, Tue, etc)
            date_str = forecast_date.strftime('%m/%d')
            table += f"""
                <th class="table-header">
                    <div style="color: #64748b;">{day_of_week}</div>
                    {date_str}
                </th>"""

        table += """
                        </tr>
                    </thead>
                    <tbody>
        """

        for reading in readings:
            # Get color based on media type
            if reading.media.lower() == 'audio':
                color = '#FB923C'  # warm orange
                bg_color = '#FFF7ED'
            elif reading.media.lower() == 'hardcover':
                color = '#A855F7'  # purple
                bg_color = '#FAF5FF'
            elif reading.media.lower() == 'kindle':
                color = '#3B82F6'  # blue
                bg_color = '#EFF6FF'
            else:
                color = '#64748B'  # slate
                bg_color = '#F8FAFC'

            # Format media badge
            media_badge = f"""
                <span style="
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    background-color: {bg_color};
                    color: {color};
                    font-size: 12px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                ">{reading.media}</span>
            """

            # Format title and author in the same style as other tables
            title_author = f"""
                <div style="font-weight: 600; color: #1a202c; margin-bottom: 4px;">
                    {reading.book.title}
                </div>
                <div style="color: #64748b; font-size: 14px;">
                    {reading.book.author}
                </div>
            """

            row = f"""
                <tr>
                    <td>{media_badge}</td>
                    <td>{title_author}</td>
            """

            # Add progress forecasts for each date
            for forecast_date in dates:
                progress = self._calculate_future_progress(reading, forecast_date)
                row += f'<td style="color: {color}; font-weight: 600;">{progress}</td>'

            row += "</tr>"
            table += row

        table += """
                </tbody>
            </table>
        </div>
        """

        return table

    def _calculate_future_progress(self, reading, target_date):
        """Calculate estimated progress for a book on a future date"""
        return calculate_reading_progress(reading, target_date, html_format=True)

    def _format_media_badge(self, media: str) -> str:
        """Format media type with enhanced styling"""
        # Media type styling
        styles = {
            'audio': ('#FB923C', '#FFF7ED'),
            'hardcover': ('#A855F7', '#FAF5FF'),
            'kindle': ('#3B82F6', '#EFF6FF'),
            'default': ('#64748B', '#F8FAFC')
        }

        color, bg_color = styles.get(media.lower(), styles['default'])

        return f"""
            <span style="
                display: inline-block;
                padding: 8px 16px;
                border-radius: 8px;
                background-color: {bg_color};
                color: {color};
                font-size: 18px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.075em;
                margin: 6px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: all 0.2s ease;
            ">
                {media}
            </span>
        """

    def _get_media_styles(self):
        """Get enhanced CSS styles for media badges"""
        return """
            .media-badge {
                display: inline-block;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.075em;
                margin: 6px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: all 0.2s ease;
            }
            .kindle {
                background-color: #EFF6FF;
                color: #3B82F6;
            }
            .hardcover {
                background-color: #FAF5FF;
                color: #A855F7;
            }
            .audio {
                background-color: #FFF7ED;
                color: #FB923C;
            }
        """

    def send_reading_status(self):
        """Send reading status report via email"""
        try:
            self._get_app_password()

            # Get reading data
            status = ReadingStatus()
            current_readings = status.queries.get_current_unfinished_readings()
            upcoming_readings = status.queries.get_upcoming_readings()

            # Filter upcoming readings for forecast (next 7 days only)
            seven_days_future = date.today() + timedelta(days=7)
            forecast_upcoming = [r for r in upcoming_readings
                               if r.date_est_start and r.date_est_start <= seven_days_future]

            # Create HTML tables
            current_table = self._create_html_table(
                current_readings,
                "Currently Reading",
                is_current=True
            )
            upcoming_table = self._create_html_table(
                upcoming_readings,
                "Coming Soon",
                is_current=False
            )
            forecast_table = self._create_forecast_table(current_readings + forecast_upcoming)

            # Create email HTML content
            html_content = f"""
            <html>
                <head>
                    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
                    <style>
                        body {{
                            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            margin: 0;
                            padding: 40px;
                            color: #1e293b;
                            background-color: #f8fafc;
                            line-height: 1.6;
                        }}
                        .container {{
                            max-width: 1200px;
                            margin: 0 auto;
                            background-color: #ffffff;
                            border-radius: 12px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                            padding: 30px;
                        }}
                        .title-section {{
                            text-align: center;
                            margin: 60px auto 80px;
                            max-width: 800px;
                        }}
                        h1 {{
                            text-align: center;
                            font-size: 3.5rem;
                            font-weight: 800;
                            letter-spacing: -0.025em;
                            background: linear-gradient(135deg, #3b82f6, #10b981);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            background-clip: text;  /* Added for broader compatibility */
                            color: transparent;  /* Fallback for non-webkit browsers */
                            margin: 0;
                        }}
                        h2 {{
                            text-align: center;
                            font-size: 2.25rem;
                            font-weight: 800;
                            letter-spacing: -0.025em;
                            background: linear-gradient(135deg, #3b82f6, #10b981);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            background-clip: text;
                            color: transparent;
                            margin-top: 1.5rem;
                            margin-bottom: 1.5rem;
                        }}
                        .intro-text {{
                            color: #475569;
                            font-size: 1.25rem;
                            line-height: 1.6;
                            margin: 1.5rem auto;
                            font-weight: 400;
                        }}
                        .title-decoration {{
                            margin: 2rem auto;
                            width: 120px;  /* Increased width for a more prominent line */
                            height: 2px;
                            background: linear-gradient(to right, #3b82f6, #10b981);
                        }}
                        /* Original email report styles */
                        table {{
                            width: 100%;
                            border-collapse: separate;
                            border-spacing: 0;
                            margin: 20px 0;
                            background: white;
                            border-radius: 8px;
                            overflow: hidden;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                        }}
                        /* Target the Format column (second column) */
                        th:nth-child(2) {{
                            border-top-left-radius: 8px;
                        }}
                        th:last-child {{
                            border-top-right-radius: 8px;
                        }}
                        th {{
                            background: linear-gradient(to bottom, #f8fafc, #f1f5f9);
                            padding: 14px 16px;
                            text-align: left;
                            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            font-weight: 800;  /* Changed to 800 to match titles */
                            font-size: 0.9rem;
                            text-transform: uppercase;
                            letter-spacing: -0.025em;  /* Matched with titles */
                            color: #64748b;
                            border-bottom: 1px solid #e2e8f0;
                            position: relative;
                        }}
                        td {{
                            padding: 12px;
                            border-bottom: 1px solid #e2e8f0;
                            color: #334155;
                        }}
                        .cover-cell {{
                            background: transparent !important;
                            border: none !important;
                            padding: 8px !important;
                        }}
                        th.cover-header {{
                            background: transparent !important;
                            border: none !important;
                        }}/* Add styles for cover column */
                        .book-title {{
                            font-weight: 600;
                            color: #1e293b;
                        }}
                        .author {{
                            color: #64748b;
                            font-size: 0.9em;
                        }}
                        .progress-bar {{
                            background: #e2e8f0;
                            height: 8px;
                            border-radius: 4px;
                            overflow: hidden;
                        }}
                        .progress-fill {{
                            height: 100%;
                            background: linear-gradient(to right, #3b82f6, #10b981);
                            transition: width 0.3s ease;
                        }}
                        .media-badge {{
                            display: inline-block;
                            padding: 2px 8px;
                            border-radius: 12px;
                            font-size: 0.8em;
                            font-weight: 500;
                            margin-left: 8px;
                        }}
                        .kindle {{
                            background: #e0f2fe;
                            color: #0369a1;
                        }}
                        .hardcover {{
                            background: #fef3c7;
                            color: #92400e;
                        }}
                        .audio {{
                            background: #f3e8ff;
                            color: #7e22ce;
                        }}
                        .section-header {{
                            margin-top: 40px;
                            margin-bottom: 20px;
                            color: #1e293b;
                            font-weight: 600;
                            font-size: 1.5em;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="title-section">
                            <h1>Your Daily Reading Update</h1>
                            <p class="intro-text">
                                Here's your personalized reading dashboard for {date.today().strftime('%B %d')}.
                                Below you'll find your current reading progress, upcoming books in your queue,
                                and a forecast of your reading journey for the next 7 days.
                                Keep turning those pages!
                            </p>
                            <div class="title-decoration"></div>
                        </div>
                        {current_table}
                        {upcoming_table}
                        {forecast_table}
                    </div>
                </body>
            </html>
            """

            # Create email message
            msg = MIMEMultipart('related')  # Change to 'related' instead of 'alternative'
            msg['Subject'] = f"Your Daily Reading Update for {date.today().strftime('%B %d')}!"
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email

            # Create message container
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)

            # Create plain text alternative
            text_content = """
            Reading Status Report

            Please view this email in an HTML-capable email client to see the formatted tables.
            """

            msg_alternative.attach(MIMEText(text_content, 'plain'))
            msg_alternative.attach(MIMEText(html_content, 'html'))

            # Attach all images
            for cid, (content_id, img_data, mime_type) in self.image_cids.items():
                img = MIMEImage(img_data)
                img.add_header('Content-ID', f'<{content_id}>')
                img.add_header('Content-Disposition', 'inline')
                msg.attach(img)

            # Enhanced SMTP connection and authentication
            try:
                print("Connecting to SMTP server...")
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    print("Starting TLS...")
                    server.starttls()

                    print(f"Attempting login for {self.sender_email}...")
                    server.login(self.sender_email, self.app_password)

                    print("Sending email...")
                    server.send_message(msg)
                    print("Email sent successfully!")

            except smtplib.SMTPAuthenticationError as auth_error:
                print(f"Authentication failed: {auth_error}")
                print("Please verify your Gmail App Password and sender email address")
                print("Generate a new App Password at: https://myaccount.google.com/apppasswords")
                raise

            except smtplib.SMTPException as smtp_error:
                print(f"SMTP error occurred: {smtp_error}")
                raise

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            print("\nTroubleshooting steps:")
            print("1. Check that GMAIL_APP_PASSWORD is set in your .env file")
            print("2. Verify SENDER_EMAIL matches the Gmail account used to generate the App Password")
            print("3. Ensure 2-Step Verification is enabled on your Gmail account")
            print("4. Try generating a new App Password")
            raise

def main():
    email_report = EmailReport()
    email_report.send_reading_status()

if __name__ == "__main__":
    main()
