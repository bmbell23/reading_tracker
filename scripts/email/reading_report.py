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
            cover_path = os.path.join(self.assets_path, f"book_{book_id}{ext}")
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
            '<td class="cover-cell" style="width: 60px; padding: 8px;">'
            f'<img src="{cover_url}" '
            f'alt="Cover of {reading.book.title}" '
            'style="width: 60px; height: auto; border-radius: 4px; '
            'box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: block;" />'
            '</td>'
        )

        print(f"DEBUG - Final cover HTML: {cover_html}")

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
                        {int(round(progress_pct))}%
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
        """Create HTML table for 10-day reading progress forecast"""
        today = date.today()
        dates = [today + timedelta(days=i) for i in range(10)]

        # Sort readings by start date and media type
        readings = sorted(readings, key=lambda r: (
            r.date_started or r.date_est_start or date.max,
            r.media.lower()
        ))

        table = """
        <div class="table-container">
            <h2>10-Day Reading Progress Forecast</h2>
            <table>
                <thead>
                    <tr>
                        <th>Format</th>
                        <th>Title</th>
                        <th>Author</th>
        """

        # Add date columns
        for forecast_date in dates:
            table += f"<th>{forecast_date.strftime('%m/%d')}</th>"

        table += """
                    </tr>
                </thead>
                <tbody>
        """

        for reading in readings:
            # Get color based on media type
            if reading.media.lower() == 'audio':
                color = '#FFA500'
            elif reading.media.lower() == 'hardcover':
                color = '#9370DB'
            elif reading.media.lower() == 'kindle':
                color = '#4169E1'
            else:
                color = '#333333'

            row = f"""
                <tr style="color: {color}">
                    <td>{reading.media}</td>
                    <td>{reading.book.title}</td>
                    <td>{reading.book.author}</td>
            """

            # Add progress forecasts for each date
            for forecast_date in dates:
                progress = self._calculate_future_progress(reading, forecast_date)
                row += f"<td>{progress}</td>"

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

    def send_reading_status(self):
        """Send reading status report via email"""
        try:
            self._get_app_password()

            # Get reading data
            status = ReadingStatus()
            current_readings = status.queries.get_current_unfinished_readings()
            upcoming_readings = status.queries.get_upcoming_readings()

            # Filter upcoming readings for forecast (next 10 days only)
            ten_days_future = date.today() + timedelta(days=10)
            forecast_upcoming = [r for r in upcoming_readings
                               if r.date_est_start and r.date_est_start <= ten_days_future]

            # Create HTML tables
            current_table = self._create_html_table(
                current_readings,
                "Current Reading Sessions",
                is_current=True
            )
            upcoming_table = self._create_html_table(
                upcoming_readings,
                "Upcoming Reading Sessions",
                is_current=False
            )
            forecast_table = self._create_forecast_table(current_readings + forecast_upcoming)

            # Create email HTML content
            html_content = f"""
            <html>
                <head>
                    <style>
                        body {{
                            font-family: 'Segoe UI', Arial, sans-serif;
                            margin: 0;
                            padding: 40px;
                            color: #2c3e50;
                            background-color: #f5f7fa;
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
                        .header {{
                            text-align: center;
                            padding-bottom: 30px;
                            margin-bottom: 30px;
                            border-bottom: 2px solid #edf2f7;
                        }}
                        h1 {{
                            color: #1a202c;
                            font-size: 28px;
                            font-weight: 600;
                            margin: 0;
                        }}
                        .date {{
                            color: #718096;
                            font-size: 16px;
                            margin-top: 8px;
                        }}
                        h2 {{
                            color: #2d3748;
                            font-size: 22px;
                            font-weight: 600;
                            margin: 30px 0 20px 0;
                            padding-bottom: 10px;
                            /* border-bottom: 2px solid #edf2f7; */
                        }}
                        .table-section {{
                            margin-bottom: 40px;
                        }}

                        .table-wrapper {{
                            border-radius: 8px;
                            overflow: hidden;
                            /* Removing this line:
                            border: 1px solid #e2e8f0;
                            */
                        }}

                        table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin-bottom: 0;
                            background-color: white;
                        }}

                        .table-header {{
                            font-size: 14px;
                            font-weight: 600;  /* changed from 500 to 600 for bold */
                            text-transform: none;
                            letter-spacing: 0.3px;
                            background-color: #f8fafc;
                            border-bottom: 2px solid #e2e8f0;
                            padding: 16px 12px;
                            text-align: left;
                            color: #64748b;
                            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        }}

                        .cover-header {{
                            width: 96px;
                            border: none !important;
                            background: none !important;
                            padding: 8px 16px 8px 0;
                        }}

                        th {{
                            background-color: #f8fafc;
                            border: none;
                            border-bottom: 2px solid #e2e8f0;
                        }}

                        td {{
                            padding: 16px 12px;
                            border: none;
                            border-bottom: 1px solid #e2e8f0;
                        }}

                        tr:last-child td {{
                            border-bottom: none;
                        }}

                        tr:hover {{
                            background-color: #f8fafc;
                            transition: background-color 0.2s ease;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Your Daily Reading Update for {date.today().strftime('%B %d')}!</h1>
                            <div class="intro-text">
                                Here's your personalized reading dashboard for today. Below you'll find your current reading progress,
                                upcoming books in your queue, and a forecast of your reading journey for the next 10 days.
                                Keep turning those pages! 📚
                            </div>
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
