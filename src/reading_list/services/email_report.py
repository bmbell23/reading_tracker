"""Service for generating and sending email reading reports."""
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
import smtplib
import requests
from typing import Dict, Tuple, List
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
        today = date.today()

        # Use StatusDisplay's media badge formatting
        media_badge = self.status_display._format_media_badge(reading.media)

        # Get text color for progress bar from the badge
        text_color = '#3B82F6'  # Default to blue
        if reading.media.lower() == 'hardcover':
            text_color = '#A855F7'
        elif reading.media.lower() in ['audio', 'audiobook']:
            text_color = '#FB923C'

        # Calculate progress if current reading
        progress = ""
        if is_current:
            progress = calculate_reading_progress(reading, today)
            if progress.endswith('%'):
                progress_pct = float(progress.rstrip('%'))
                progress = f"""
                    <div style="width: 100%; background-color: #e2e8f0; border-radius: 9999px; height: 6px;">
                        <div style="width: {progress_pct}%; background-color: {text_color}; height: 6px; border-radius: 9999px;"></div>
                    </div>
                    <div style="color: {text_color}; font-weight: 600; font-size: 14px; margin-top: 4px;">
                        {int(progress_pct)}%
                    </div>
                """

        return f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px;">{media_badge}</td>
                <td style="padding: 12px;">
                    <div style="font-weight: 600;">{reading.book.title}</div>
                    <div style="color: #64748b; font-size: 14px;">{reading.book.author_name_first} {reading.book.author_name_second}</div>
                </td>
                <td style="padding: 12px;">{reading.date_started.strftime('%b %d, %Y') if reading.date_started else 'Not started'}</td>
                {f'<td style="padding: 12px;">{progress}</td>' if is_current else ''}
                <td style="padding: 12px;">{reading.date_est_end.strftime('%b %d, %Y') if reading.date_est_end else 'TBD'}</td>
            </tr>
        """

    def _generate_html_table(self, readings: List[Reading], title: str, is_current: bool = True) -> str:
        """Generate HTML table for readings."""
        if not readings:
            return f"<h2>{title}</h2><p>No readings found.</p>"

        headers = ['Format', 'Book', 'Started']
        if is_current:
            headers.append('Progress')
        headers.append('Est. Completion')

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
        current_table = self._generate_html_table(current_readings, "Currently Reading", True)
        upcoming_table = self._generate_html_table(upcoming_readings, "Coming Soon", False)

        # Use the model's get_forecast_readings() instead of custom sorting
        model = ReadingStatus()
        all_readings = model.get_forecast_readings()  # This already has the correct sorting

        forecast_table = self._generate_forecast_table(all_readings)

        return f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
                    <h1 style="color: #1e293b; margin-bottom: 24px;">Reading Update - {date.today().strftime('%B %d, %Y')}</h1>
                    {current_table}
                    {upcoming_table}
                    {forecast_table}
                </div>
            </body>
        </html>
        """

    def _generate_forecast_table(self, readings: List[Reading]) -> str:
        """Generate HTML table for weekly progress forecast."""
        if not readings:
            return "<p>No current or upcoming readings found for the next 7 days.</p>"

        dates = [date.today() + timedelta(days=i) for i in range(8)]

        table = """
        <div style="margin-bottom: 32px;">
            <h2 style="color: #1e293b; margin-bottom: 16px;">Weekly Reading Progress Forecast</h2>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
                <thead>
                    <tr>
                        <th style="text-align: left; padding: 12px; background-color: #f8fafc;">Format</th>
                        <th style="text-align: left; padding: 12px; background-color: #f8fafc;">Title</th>
                        <th style="text-align: left; padding: 12px; background-color: #f8fafc;">Author</th>
        """

        # Add date columns
        for d in dates:
            day_name = d.strftime('%a')
            date_str = d.strftime('%m/%d')
            table += f"""
                <th style="text-align: center; padding: 12px; background-color: #f8fafc;">
                    {day_name}<br>{date_str}
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
                    <td style="padding: 12px;">{self.status_display._format_author(reading.book)}</td>
            """

            # Add progress forecasts for each date
            for forecast_date in dates:
                progress = self.status_display._format_forecast_progress(reading, forecast_date)
                row += f'<td style="text-align: center; padding: 12px; color: {color}; font-weight: 600;">{progress}</td>'

            row += "</tr>"
            table += row

        table += "</tbody></table></div>"
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
            cover_path = get_project_paths()['assets'] / 'book_covers' / f'cover_{book_id}.jpg'
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

            # Create email HTML content using StatusDisplay
            status = self.status_display
            current_readings = status.model.get_current_readings()
            upcoming_readings = status.model.get_upcoming_readings()

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
