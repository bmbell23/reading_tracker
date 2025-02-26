"""
Validation utilities for parsing and validating input data.
"""
from typing import Optional
from datetime import datetime, date

def parse_date(date_str: str) -> Optional[date]:
    """
    Parse date string in YYYY-MM-DD format.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Parsed date object or None if invalid/empty
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

def parse_boolean(value: str) -> bool:
    """
    Convert string input to boolean value.

    Args:
        value: String input ('yes', 'true', 't', 'y', '1' for True)

    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('yes', 'true', 't', 'y', '1')