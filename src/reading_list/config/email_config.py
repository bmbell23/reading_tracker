"""Email configuration settings."""
from pathlib import Path
import os
from dotenv import load_dotenv

from ..utils.paths import get_project_paths

# Load environment variables
load_dotenv(get_project_paths()['root'] / '.env')

EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': os.getenv('SENDER_EMAIL'),
    'receiver_email': os.getenv('RECEIVER_EMAIL'),
    'templates_dir': get_project_paths()['root'] / 'templates' / 'email'
}