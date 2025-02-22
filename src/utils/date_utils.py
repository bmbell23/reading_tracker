from datetime import datetime

def parse_date(date_str: str) -> datetime:
    """Parse a date string into a datetime object."""
    if not date_str:
        return None
    return datetime.strptime(date_str, '%Y-%m-%d')

def format_date(date_obj: datetime) -> str:
    """Format a datetime object into a string."""
    if not date_obj:
        return None
    return date_obj.strftime('%Y-%m-%d')