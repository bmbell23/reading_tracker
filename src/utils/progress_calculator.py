from datetime import date, timedelta

def calculate_reading_progress(reading, target_date, html_format=False):
    """
    Calculate reading progress for a given date

    Args:
        reading: Reading object
        target_date: date to calculate progress for
        html_format: whether to return HTML formatted string

    Returns:
        String representing progress (plain or HTML formatted)
    """
    if not reading.date_est_end:
        return "Unknown"

    # Always use actual start date if available
    start_date = reading.date_started or reading.date_est_start
    if not start_date:
        return "Unknown"

    if target_date < start_date:
        return f'<span style="color: #888888; font-weight: normal;">TBR</span>' if html_format else "TBR"

    # Show 100% only on the exact end date, "Done" after that
    if target_date > reading.date_est_end:
        return f'<span style="color: #888888; font-weight: normal;">Done</span>' if html_format else "Done"
    elif target_date == reading.date_est_end:
        return f'<span style="font-weight: bold;">100%</span>' if html_format else "100%"

    # Calculate progress percentage
    total_days = (reading.date_est_end - start_date).days + 1  # Add 1 to include start date
    if total_days <= 0:
        return "Unknown"

    days_elapsed = (target_date - start_date).days + 1  # Add 1 to include start date
    progress = (days_elapsed / total_days) * 100

    # Format progress with bold text
    return f'<span style="font-weight: bold;">{progress:.0f}%</span>' if html_format else f"{progress:.0f}%"
