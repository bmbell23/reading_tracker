"""
Database Entry Editor
====================

Core functionality for editing and updating database entries across related tables:
- books: Main book information
- readings: Reading session records
- inventory: Book inventory tracking

Features:
- Search and select entries
- Update existing entries with validation
- Create new related entries
- Chain updates across related tables
"""
from typing import Optional, List, Dict, Any
from datetime import date
from sqlalchemy.orm import Session

from reading_list.models.book import Book
from reading_list.models.reading import Reading
from reading_list.models.inventory import Inventory
from reading_list.utils.validation import parse_date, parse_boolean

class EntryEditor:
    def __init__(self, session: Session):
        self.session = session

    def search_entries(self, model: type, search_term: str, search_by_id: bool = False) -> List[Any]:
        """Search for entries in specified model"""
        # Your existing search_entries logic

    def get_book_data(self, is_new: bool = True, existing_book: Optional[Book] = None) -> Dict[str, Any]:
        """Get validated book data without UI-specific logic"""
        # Your existing get_book_input logic, but without the prompts

    def get_reading_data(self, book_id: int, existing_reading: Optional[Reading] = None) -> Dict[str, Any]:
        """Get validated reading data without UI-specific logic"""
        # Your existing get_reading_input logic, but without the prompts

    def get_inventory_data(self, book_id: int, existing_inventory: Optional[Inventory] = None) -> Dict[str, Any]:
        """Get validated inventory data without UI-specific logic"""
        # Your existing get_inventory_input logic, but without the prompts

    def update_entry(self, model: type, entry_id: int, data: Dict[str, Any]) -> Any:
        """Update an existing entry with validated data"""
        entry = self.session.get(model, entry_id)
        if not entry:
            raise ValueError(f"No {model.__name__} entry found with ID {entry_id}")

        for key, value in data.items():
            if value is not None:
                setattr(entry, key, value)

        self.session.commit()
        return entry
