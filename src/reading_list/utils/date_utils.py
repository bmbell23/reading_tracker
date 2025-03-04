"""Date-related utility functions."""
from datetime import datetime

def get_month_name(month_number: int) -> str:
    """
    Convert month number to month name.
    
    Args:
        month_number: Integer representing the month (1-12)
        
    Returns:
        Full name of the month (e.g., "January" for 1)
    """
    return datetime(2000, month_number, 1).strftime('%B')