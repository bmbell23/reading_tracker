"""Display utilities for reading list CLI tools."""
from rich.console import Console
from rich.panel import Panel

console = Console()

def display_reading_group(readings: list, title: str = None) -> None:
    """
    Display a group of readings in a formatted panel.
    
    Args:
        readings: List of Reading objects to display
        title: Optional title for the panel
    """
    if not readings:
        console.print("[italic]No readings in this segment[/italic]")
        return

    content = []
    for reading in readings:
        reading_info = f"ID: {reading.id} - {reading.book.title}"
        if reading.id_previous:
            reading_info += f" (Previous: {reading.id_previous})"
        content.append(reading_info)

    panel_content = "\n".join(content)
    console.print(Panel(
        panel_content,
        title=title if title else "Reading Group",
        border_style="cyan"
    ))