"""Utilities for calculating reading progress."""
from datetime import date, timedelta
from typing import Any, Optional

def calculate_reading_progress(reading: Any, target_date: date) -> str:
    """
    Calculate reading progress as a percentage.
    
    Args:
        reading: Reading object with start_date, end_date, and current_page
        target_date: Date to calculate progress for
        
    Returns:
        String representation of progress (e.g., "45%")
    """
    if not reading.date_started or not reading.date_est_end:
        return "0%"

    total_days = (reading.date_est_end - reading.date_started).days + 1
    days_elapsed = (target_date - reading.date_started).days + 1
    
    # Handle edge cases
    if total_days <= 0:
        return "0%"
    if days_elapsed >= total_days:
        return "100%"
    if days_elapsed <= 0:
        return "0%"
    
    # Calculate progress percentage
    progress = (days_elapsed / total_days) * 100
    return f"{int(round(progress))}%"