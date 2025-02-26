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
from typing import Optional, List, Dict, Any, Type
from datetime import date
from sqlalchemy import or_
from sqlalchemy.orm import Session

from reading_list.models.book import Book
from reading_list.models.reading import Reading
from reading_list.models.inventory import Inventory
from reading_list.utils.validation import parse_date, parse_boolean

class EntryEditor:
    def __init__(self, session: Session):
        self.session = session

    def search_entries(self, model: Type, search_term: str, search_by_id: bool = False) -> List[Any]:
        """Search for entries in specified model"""
        query = self.session.query(model)

        # Debug: Print total count of entries in table
        total_count = query.count()
        print(f"Total entries in {model.__name__} table: {total_count}")

        # First try to search by ID if the search term is numeric
        try:
            entry_id = int(search_term)
            print(f"Searching for ID: {entry_id}")
            id_entry = query.filter(model.id == entry_id).first()
            if id_entry:
                print(f"Found entry with ID {entry_id}")
                return [id_entry]
        except ValueError:
            pass

        # If ID search fails or search term isn't numeric, search by text
        print(f"Searching for term: {search_term}")
        if model == Book:
            results = query.filter(
                or_(
                    Book.title.ilike(f"%{search_term}%"),
                    Book.author_name_first.ilike(f"%{search_term}%"),
                    Book.author_name_second.ilike(f"%{search_term}%")
                )
            ).all()
            print(f"Found {len(results)} matching books")
            return results
        elif model == Reading:
            results = query.join(Book).filter(Book.title.ilike(f"%{search_term}%")).all()
            print(f"Found {len(results)} matching readings")
            return results
        elif model == Inventory:
            results = query.join(Book).filter(Book.title.ilike(f"%{search_term}%")).all()
            print(f"Found {len(results)} matching inventory entries")
            return results

        return []

    def get_book_data(self, data: Dict[str, Any], existing_book: Optional[Book] = None) -> Dict[str, Any]:
        """Validate and process book data"""
        validated = {}

        if 'title' in data:
            validated['title'] = str(data['title']).strip()
        if 'author_name_first' in data:
            validated['author_name_first'] = str(data['author_name_first']).strip()
        if 'author_name_second' in data:
            validated['author_name_second'] = str(data['author_name_second']).strip()
        if 'date_published' in data and data['date_published']:
            validated['date_published'] = parse_date(data['date_published'])
        if 'series' in data:
            validated['series'] = data['series'].strip() if data['series'] else None
        if 'series_number' in data:
            validated['series_number'] = int(data['series_number']) if data['series_number'] else None
        if 'genre' in data:
            validated['genre'] = data['genre'].strip() if data['genre'] else None
        if 'has_cover' in data:
            validated['has_cover'] = parse_boolean(data['has_cover'])
        if 'isbn_id' in data:
            validated['isbn_id'] = int(data['isbn_id']) if data['isbn_id'] else None

        return validated

    def get_reading_data(self, data: Dict[str, Any], book_id: int, existing_reading: Optional[Reading] = None) -> Dict[str, Any]:
        """Validate and process reading data"""
        validated = {'book_id': book_id}

        if 'date_started' in data and data['date_started']:
            validated['date_started'] = parse_date(data['date_started'])
        if 'date_finished' in data and data['date_finished']:
            validated['date_finished'] = parse_date(data['date_finished'])
        if 'pages_read' in data:
            validated['pages_read'] = int(data['pages_read']) if data['pages_read'] else 0
        if 'completed' in data:
            validated['completed'] = parse_boolean(data['completed'])

        return validated

    def get_inventory_data(self, data: Dict[str, Any], book_id: int, existing_inventory: Optional[Inventory] = None) -> Dict[str, Any]:
        """Validate and process inventory data"""
        validated = {'book_id': book_id}

        if 'owned_physical' in data:
            validated['owned_physical'] = parse_boolean(data['owned_physical'])
        if 'owned_kindle' in data:
            validated['owned_kindle'] = parse_boolean(data['owned_kindle'])
        if 'owned_audio' in data:
            validated['owned_audio'] = parse_boolean(data['owned_audio'])
        if 'location' in data:
            validated['location'] = data['location'].strip() if data['location'] else None

        return validated

    def update_entry(self, model: Type, entry_id: int, data: Dict[str, Any]) -> Any:
        """Update an existing entry with validated data"""
        entry = self.session.get(model, entry_id)
        if not entry:
            raise ValueError(f"No {model.__name__} entry found with ID {entry_id}")

        for key, value in data.items():
            if value is not None:
                setattr(entry, key, value)

        self.session.commit()
        return entry

    def get_related_entries(self, book_id: int) -> Dict[str, List[Any]]:
        """Get all related entries for a book"""
        return {
            'readings': self.session.query(Reading).filter(Reading.book_id == book_id).all(),
            'inventory': self.session.query(Inventory).filter(Inventory.book_id == book_id).all()
        }
