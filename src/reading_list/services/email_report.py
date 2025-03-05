"""Service for generating and sending email reading reports."""
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
import smtplib
import requests
from typing import Dict, Tuple, List, Optional
from dotenv import load_dotenv

from .status_display import StatusDisplay
from ..utils.paths import get_project_paths
from ..config.email_config import EMAIL_CONFIG
from ..models.reading import Reading
from ..models.reading_status import ReadingStatus
from ..utils.progress_calculator import calculate_reading_progress

class EmailReport:
    """Service for sending email reading reports."""

    def __init__(self):
        load_dotenv()
        self.status_display = StatusDisplay()
        self.sender_email = EMAIL_CONFIG['sender_email']
        self.receiver_email = EMAIL_CONFIG['receiver_email']
        self.smtp_server = EMAIL_CONFIG['smtp_server']
        self.smtp_port = EMAIL_CONFIG['smtp_port']
        self.templates_dir = EMAIL_CONFIG['templates_dir']
        self.image_cids: Dict[str, Tuple[str, bytes, str]] = {}

    def _generate_reading_row(self, reading: Reading, is_current: bool = True) -> str:
        """Generate HTML table row for a reading."""
        def format_date(d: Optional[date]) -> str:
            """Format date as 'MMM DD' with ordinal suffix."""
            if not d:
                return 'Not scheduled'
            day = d.day
            suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
            return d.strftime(f'%b {day}{suffix}')

        # Get cover image
        cover_url = self._get_book_cover_url(reading.book.title, reading.book.author_name_first, reading.book.id)
        cover_cell = f'<td style="padding: 12px;"><img src="{cover_url}" style="width: 60px; border-radius: 4px;" alt="Book cover"/></td>' if cover_url else '<td></td>'
        
        # Format dates and progress
        formatted = {
            'author': f"{reading.book.author_name_first} {reading.book.author_name_second}",
            'start_date': (format_date(reading.date_started) if reading.date_started else 
                          format_date(reading.date_est_start) if reading.date_est_start else 
                          'Not scheduled'),
            'end_date': format_date(reading.date_est_end)
        }

        # Get formatted media badge
        media_badge = self.status_display._format_media_badge(reading.media)

        # Calculate progress for current readings
        progress = ''
        if is_current:
            today = date.today()
            progress = calculate_reading_progress(reading, today)
            if progress and progress.endswith('%'):
                pct = float(progress.rstrip('%'))
                total_pages = reading.book.page_count
                pages_read = int(round((pct / 100) * total_pages)) if total_pages else 0
                progress = f"p. {pages_read}<br>{pct}%" if total_pages else progress

        return f"""
            <tr>
                {cover_cell}
                <td style="padding: 12px;">{media_badge}</td>
                <td style="padding: 12px;">
                    <div style="font-weight: 600;">{reading.book.title}</div>
                    <div style="color: #64748b; font-size: 14px;">{formatted['author']}</div>
                </td>
                {f'<td style="padding: 12px;">{progress}</td>' if is_current else ''}
                <td style="padding: 12px;">{formatted['start_date']}</td>
                <td style="padding: 12px;">{formatted['end_date']}</td>
            </tr>
        """

    def _generate_html_table(self, readings: List[Reading], title: str, is_current: bool = True) -> str:
        """Generate HTML table for readings."""
        if not readings:
            return f"<h2>{title}</h2><p>No readings found.</p>"

        headers = ['Cover', 'Format', 'Book']
        if is_current:
            headers.append('Progress')
        headers.extend(['Start Date', 'End Date'])

        header_row = "".join([f'<th style="text-align: left; padding: 12px; background-color: #f8fafc;">{h}</th>' for h in headers])

        rows = [self._generate_reading_row(reading, is_current) for reading in readings]

        return f"""
            <div style="margin-bottom: 32px;">
                <h2 style="color: #1e293b; margin-bottom: 16px;">{title}</h2>
                <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
                    <thead>
                        <tr>{header_row}</tr>
                    </thead>
                    <tbody>
                        {"".join(rows)}
                    </tbody>
                </table>
            </div>
        """

    def _generate_html_content(self, current_readings: List[Reading], upcoming_readings: List[Reading]) -> str:
        """Generate complete HTML email content."""
        # Use the model's standardized sorted lists
        model = ReadingStatus()
        current_readings = model.get_current_readings()
        upcoming_readings = model.get_upcoming_readings()
        all_readings = model.get_forecast_readings()

        current_table = self._generate_html_table(current_readings, "Currently Reading", True)
        upcoming_table = self._generate_html_table(upcoming_readings, "Coming Soon", False)
        forecast_table = self._generate_forecast_table(all_readings)

        today_date = date.today().strftime('%B %-d')  # Format like "March 5"

        return f"""
        <html>
            <head>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');
                    body {{
                        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        margin: 0;
                        padding: 24px;
                        background-color: #f1f5f9;
                        color: #1e293b;
                        line-height: 1.5;
                    }}
                </style>
            </head>
            <body>
                <div style="max-width: 800px; margin: 0 auto;">
                    <div style="text-align: center; margin-bottom: 40px;">
                        <h1 style="
                            font-family: 'Outfit', sans-serif;
                            font-size: 42px;
                            font-weight: 800;
                            margin: 0;
                            background: linear-gradient(135deg, #94A3B8 0%, #818CF8 33%, #38BDF8 66%, #2DD4BF 100%);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            -moz-background-clip: text;
                            -moz-text-fill-color: transparent;
                            background-clip: text;
                            text-fill-color: transparent;
                            color: transparent;
                            display: inline-block;
                            letter-spacing: -0.02em;
                            padding: 4px 0;
                        ">Your Daily Reading Update</h1>
                        
                        <div style="
                            width: 80px;
                            height: 4px;
                            background: linear-gradient(135deg, #94A3B8 0%, #818CF8 33%, #38BDF8 66%, #2DD4BF 100%);
                            margin: 28px auto;
                            border-radius: 4px;
                        "></div>
                        
                        <p style="
                            font-family: 'Outfit', sans-serif;
                            font-size: 17px;
                            color: #64748b;
                            margin: 0;
                            line-height: 1.7;
                            max-width: 600px;
                            margin: 0 auto;
                            font-weight: 500;
                        ">
                            Here's your personalized reading dashboard for {today_date}!<br>
                            Below you'll find your current reading progress, upcoming books in your queue,
                            and a forecast of your reading journey for the next 7 days. Keep turning those pages! 📚
                        </p>
                    </div>

                    {current_table}
                    {upcoming_table}
                    {forecast_table}
                </div>
            </body>
        </html>
        """

    def _format_forecast_cell(self, progress: str) -> str:
        """Format forecast cell content for email HTML."""
        if progress in ["TBR", "Done"]:
            return f'<span style="color: #94A3B8;">{progress}</span>'  # Soft slate gray
        
        # Extract the percentage value from the Rich-formatted string
        if "%" in progress:
            try:
                value = int(progress.split("%")[0])
                # Smooth gradient from soft pink to soft teal
                if value < 20:
                    color = "#F472B6"  # Soft pink
                elif value < 40:
                    color = "#818CF8"  # Soft purple
                elif value < 60:
                    color = "#38BDF8"  # Light blue
                elif value < 80:
                    color = "#22D3EE"  # Cyan
                else:
                    color = "#2DD4BF"  # Soft teal
                return f'<span style="color: {color}; font-weight: 600;">{value}%</span>'
            except ValueError:
                return progress
        
        return progress

    def _generate_forecast_table(self, readings: List[Reading]) -> str:
        """Generate HTML table for weekly progress forecast."""
        if not readings:
            return "<p>No current or upcoming readings found for the next 7 days.</p>"

        dates = [date.today() + timedelta(days=i) for i in range(7)]  # Changed from 8 to 7

        table = """
        <div style="margin-bottom: 32px;">
            <h2 style="color: #1e293b; margin-bottom: 16px;">Weekly Reading Progress Forecast</h2>
            <div style="overflow-x: auto; -webkit-overflow-scrolling: touch;">
                <table style="width: 100%; min-width: 800px; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
                    <thead>
                        <tr>
                            <th style="text-align: left; padding: 12px; background-color: #f8fafc; min-width: 70px; width: 70px;">Format</th>
                            <th style="text-align: left; padding: 12px; background-color: #f8fafc; min-width: 300px;">Title</th>
        """

        # Add date columns
        for d in dates:
            day_name = d.strftime('%a')
            table += f"""
                <th style="text-align: center; padding: 12px; background-color: #f8fafc; min-width: 55px; width: 55px;">
                    {day_name}
                </th>"""

        table += "</tr></thead><tbody>"

        # Use readings directly without any additional sorting
        for reading in readings:
            media_badge = self.status_display._format_media_badge(reading.media)
            color = '#1e293b'  # Default text color

            row = f"""
                <tr>
                    <td style="padding: 12px;">{media_badge}</td>
                    <td style="padding: 12px;">
                        <div style="font-weight: 600;">{reading.book.title}</div>
                        <div style="color: #64748b; font-size: 14px;">{reading.book.author_name_first} {reading.book.author_name_second}</div>
                    </td>
            """

            # Add progress forecasts for each date
            for forecast_date in dates:
                progress = self.status_display._format_forecast_progress(reading, forecast_date, raw_value=True)
                formatted_progress = self._format_forecast_cell(progress)
                row += f'<td style="text-align: center; padding: 12px;">{formatted_progress}</td>'

            row += "</tr>"
            table += row

        table += "</tbody></table></div></div>"
        return table

    def _get_app_password(self):
        """Get Gmail app password from environment."""
        password = os.getenv('GMAIL_APP_PASSWORD')
        if not password:
            raise ValueError(
                "Gmail App Password not found. Please set the GMAIL_APP_PASSWORD environment variable. "
                "You can generate an App Password at: https://myaccount.google.com/apppasswords"
            )
        return password

    def _get_book_cover_url(self, title: str, author: str, book_id: int = None) -> str:
        """Get book cover URL, first checking local storage then external APIs."""
        cache_key = f"{title}-{author}"
        if cache_key in self.image_cids:
            return f"cid:{self.image_cids[cache_key][0]}"

        # Check local storage first
        if book_id:
            cover_path = get_project_paths()['assets'] / 'book_covers' / f'{book_id}.jpg'
            if cover_path.exists():
                with open(cover_path, 'rb') as f:
                    img_data = f.read()
                cid = f"cover_{book_id}@reading.list"
                self.image_cids[cache_key] = (cid, img_data, 'image/jpeg')
                return f"cid:{cid}"

        return None

    def send_reading_status(self):
        """Send reading status report via email."""
        try:
            password = self._get_app_password()

            # Use ReadingStatus for consistent data access
            status_model = ReadingStatus()
            current_readings = status_model.get_current_readings()
            upcoming_readings = status_model.get_upcoming_readings()

            # Generate HTML content
            html_content = self._generate_html_content(current_readings, upcoming_readings)

            # Create email message
            msg = MIMEMultipart('related')
            msg['Subject'] = f"Your Daily Reading Update for {date.today().strftime('%B %d')}!"
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email

            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)

            # Add plain text and HTML versions
            msg_alternative.attach(MIMEText("Please view this email in an HTML-capable email client.", 'plain'))
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
                    server.login(self.sender_email, password)

                    print("Sending email...")
                    server.send_message(msg)
                    print("Email sent successfully!")
                    return True

            except smtplib.SMTPAuthenticationError as auth_error:
                print(f"Authentication failed: {auth_error}")
                print("Please verify your Gmail App Password and sender email address")
                print("Generate a new App Password at: https://myaccount.google.com/apppasswords")
                return False

            except smtplib.SMTPException as smtp_error:
                print(f"SMTP error occurred: {smtp_error}")
                return False

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            print("\nTroubleshooting steps:")
            print("1. Check that GMAIL_APP_PASSWORD is set in your .env file")
            print("2. Verify SENDER_EMAIL matches the Gmail account")
            print("3. Ensure 2-Step Verification is enabled")
            print("4. Try generating a new App Password")
            return False
