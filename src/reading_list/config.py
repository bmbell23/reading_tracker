"""Configuration settings for the reading list application."""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / 'config' / '.env')

EMAIL_CONFIG = {
    'sender_email': os.getenv('SENDER_EMAIL'),
    'receiver_email': os.getenv('RECEIVER_EMAIL'),
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

# Add other configuration settings as needed