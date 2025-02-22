import sys
import os
from pathlib import Path
from datetime import date, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from rich.console import Console
from rich.text import Text
from io import StringIO
from scripts.utils.paths import find_project_root
from scripts.metrics.reading_status import ReadingStatus
from src.utils.progress_calculator import calculate_reading_progress
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add project root to Python path
project_root = find_project_root()
sys.path.insert(0, str(Path(project_root)))

class EmailReport:
    def __init__(self):
        self.sender_email = "bbell.primary@gmail.com"  # Updated to your email
        self.receiver_email = "bbell.primary@gmail.com"
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.app_password = None  # Will be loaded from environment variable

    def _get_app_password(self):
        """Get Gmail App Password from environment variable"""
        self.app_password = os.getenv('GMAIL_APP_PASSWORD')
        if not self.app_password:
            raise ValueError(
                "Gmail App Password not found. Please set the GMAIL_APP_PASSWORD environment variable. "
                "You can generate an App Password at: https://myaccount.google.com/apppasswords"
            )

    def _format_reading_to_html(self, reading, is_current=True):
        """Format a reading entry as HTML table row"""
        today = date.today()

        # Get color based on media type
        if reading.media.lower() == 'audio':
            color = '#FFA500'  # orange
        elif reading.media.lower() == 'hardcover':
            color = '#9370DB'  # purple
        elif reading.media.lower() == 'kindle':
            color = '#4169E1'  # blue
        else:
            color = '#333333'  # dark gray

        # Format dates and calculations differently for current vs upcoming
        if is_current:
            start_date = reading.date_started.strftime('%Y-%m-%d') if reading.date_started else 'Not started'
            days_elapsed_num = (today - reading.date_started).days if reading.date_started else 0
            days_elapsed = str(days_elapsed_num)

            if reading.date_est_end and reading.date_started:
                total_days = (reading.date_est_end - reading.date_started).days
                progress_pct = (days_elapsed_num / total_days * 100) if total_days > 0 else 0
                progress = f"{progress_pct:.1f}%"
                days_to_finish = str(total_days - days_elapsed_num)
            else:
                progress = "0%"
                days_to_finish = "Unknown"

            est_end_date = reading.date_est_end.strftime('%Y-%m-%d') if reading.date_est_end else 'Unknown'
        else:
            start_date = reading.date_est_start.strftime('%Y-%m-%d') if reading.date_est_start else 'Not scheduled'
            progress = "Not started"
            days_elapsed = "0"
            if reading.date_est_end and reading.date_est_start:
                days_to_finish = str((reading.date_est_end - reading.date_est_start).days)
            else:
                days_to_finish = "Unknown"
            est_end_date = reading.date_est_end.strftime('%Y-%m-%d') if reading.date_est_end else 'Unknown'

        # Create table row
        row = f"""
            <tr style="color: {color}">
                <td>{reading.media}</td>
                <td>{reading.book.title}</td>
                <td>{reading.book.author}</td>
                <td>{start_date}</td>
        """

        if is_current:
            row += f"""
                <td>{progress}</td>
                <td>{days_elapsed}</td>
            """

        row += f"""
                <td>{days_to_finish}</td>
                <td>{est_end_date}</td>
            </tr>
        """

        return row

    def _create_html_table(self, readings, title, is_current=True):
        """Create an HTML table for readings"""
        headers = ['Format', 'Title', 'Author', 'Start Date']
        if is_current:
            headers.extend(['Progress', 'Days Elapsed'])
        headers.extend(['Days to Finish', 'Est. End Date'])

        header_row = ''.join([f'<th>{h}</th>' for h in headers])

        table = f"""
        <div class="table-container">
            <h2>{title}</h2>
            <table>
                <thead>
                    <tr>{header_row}</tr>
                </thead>
                <tbody>
        """

        for reading in readings:
            table += self._format_reading_to_html(reading, is_current)

        table += """
                </tbody>
            </table>
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
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 20px;
                            color: #333333;
                        }}
                        h1 {{
                            color: #2c3e50;
                            font-size: 24px;
                            margin-bottom: 30px;
                        }}
                        h2 {{
                            color: #34495e;
                            font-size: 20px;
                            margin-bottom: 20px;
                        }}
                        table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin-bottom: 30px;
                        }}
                        th, td {{
                            border: 1px solid #ddd;
                            padding: 8px;
                            text-align: left;
                            font-weight: bold;
                        }}
                        th {{
                            background-color: #f5f5f5;
                        }}
                    </style>
                </head>
                <body>
                    <h1>Reading Status Report - {date.today().strftime("%Y-%m-%d")}</h1>
                    {current_table}
                    {upcoming_table}
                    {forecast_table}
                </body>
            </html>
            """

            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Reading Status Report - {date.today().strftime('%Y-%m-%d')}"
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email

            # Create plain text alternative
            text_content = """
            Reading Status Report

            Please view this email in an HTML-capable email client to see the formatted tables.
            """

            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.send_message(msg)

            print("Reading status report sent successfully!")

        except Exception as e:
            print(f"Error sending email: {str(e)}")

def main():
    email_report = EmailReport()
    email_report.send_reading_status()

if __name__ == "__main__":
    main()
