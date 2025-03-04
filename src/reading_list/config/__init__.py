"""Configuration settings for the reading list application."""
import os
from dotenv import load_dotenv
from ..utils.paths import find_project_root

# Load environment variables
load_dotenv(find_project_root() / 'config' / '.env')

EMAIL_CONFIG = {
    'sender_email': os.getenv('SENDER_EMAIL'),
    'receiver_email': os.getenv('RECEIVER_EMAIL'),
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
}

__all__ = ['EMAIL_CONFIG']