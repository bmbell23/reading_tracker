"""Display utilities for reading list CLI tools."""
from typing import List, Union
from rich.console import Console
from rich.panel import Panel
from ..models.reading import Reading

console = Console()

def display_reading_group(readings: List[Union[Reading, str]], title: str) -> None:
    """
    Display a group of readings in a panel.
    
    Args:
        readings: List of readings or formatted reading strings
        title: Title for the panel
    """
    if not readings:
        return
        
    panel_content = ""
    for reading in readings:
        if isinstance(reading, str):
            panel_content += reading + "\n"
        else:
            reading_info = f"ID: {reading.id} - {reading.book.title}"
            panel_content += reading_info + "\n"
            
    console.print(Panel(panel_content.rstrip(), title=title))
