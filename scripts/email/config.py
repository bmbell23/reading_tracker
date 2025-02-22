"""
Email configuration settings.
Note: Sensitive information should be stored in environment variables.
"""
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent.parent / '.env')

EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': os.getenv('SENDER_EMAIL'),
    'receiver_email': os.getenv('RECEIVER_EMAIL')
}
