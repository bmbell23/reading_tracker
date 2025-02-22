import pandas as pd
from datetime import datetime
import sys
from pathlib import Path
from scripts.utils.paths import find_project_root

# Add project root to Python path
project_root = find_project_root()
sys.path.insert(0, str(project_root))

from src.models.base import SessionLocal
from src.models.book import Book
from src.models.reading import Reading
from src.models.inventory import Inventory

def parse_date(date_str):
    if pd.isna(date_str):
        return None
    if isinstance(date_str, str):
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    if isinstance(date_str, (int, float)):
        return pd.to_datetime(date_str).date()
    if isinstance(date_str, pd.Timestamp):
        return date_str.date()
    return date_str.date()

def import_excel_data(file_path):
    # Read Excel sheets
    books_df = pd.read_excel(file_path, sheet_name='Books')
    readings_df = pd.read_excel(file_path, sheet_name='Readings')
    inventory_df = pd.read_excel(file_path, sheet_name='Inventory')

    session = SessionLocal()

    try:
        # Import Books
        print("Importing books...")
        for _, row in books_df.iterrows():
            # Skip rows where required fields are missing
            if pd.isna(row['title']) or pd.isna(row['author']):
                print(f"Skipping book with missing required fields: {row['id_book'] if not pd.isna(row['id_book']) else 'Unknown ID'}")
                continue

            book = Book(
                id=row['id_book'],
                title=row['title'],
                author=row['author'],
                word_count=row['word_count'] if not pd.isna(row['word_count']) else None,
                page_count=row['page_count'] if not pd.isna(row['page_count']) else None,
                date_published=parse_date(row['date_published']),
                author_gender=row['author_gender'] if not pd.isna(row['author_gender']) else None,
                series=row['series'] if not pd.isna(row['series']) else None,
                series_number=row['series_number'] if not pd.isna(row['series_number']) else None,
                genre=row['genre'] if not pd.isna(row['genre']) else None
            )
            session.add(book)

        # Import Readings
        print("Importing readings...")
        for _, row in readings_df.iterrows():
            # Skip rows where required fields are missing
            if pd.isna(row['id_read']) or pd.isna(row['id_book']):
                print(f"Skipping reading with missing required fields: {row['id_read'] if not pd.isna(row['id_read']) else 'Unknown ID'}")
                continue

            reading = Reading(
                id=row['id_read'],
                id_previous=row['id_read_previous'] if not pd.isna(row['id_read_previous']) else None,
                book_id=row['id_book'],
                media=row['media'] if not pd.isna(row['media']) else None,  # Changed from 'format' to 'media'
                date_started=parse_date(row['date_started']),
                date_finished_actual=parse_date(row['date_finished_actual']),
                rating_horror=row['rating_horror'] if not pd.isna(row['rating_horror']) else None,
                rating_spice=row['rating_spice'] if not pd.isna(row['rating_spice']) else None,
                rating_world_building=row['rating_world_building'] if not pd.isna(row['rating_world_building']) else None,
                rating_writing=row['rating_writing'] if not pd.isna(row['rating_writing']) else None,
                rating_characters=row['rating_characters'] if not pd.isna(row['rating_characters']) else None,
                rating_readability=row['rating_readability'] if not pd.isna(row['rating_readability']) else None,
                rating_enjoyment=row['rating_enjoyment'] if not pd.isna(row['rating_enjoyment']) else None,
                rank=row['rank'] if not pd.isna(row['rank']) else None
            )
            session.add(reading)

        # Import Inventory
        print("Importing inventory...")
        for _, row in inventory_df.iterrows():
            # Skip rows where required fields are missing
            if pd.isna(row['id_inventory']) or pd.isna(row['id_book']):
                print(f"Skipping inventory with missing required fields: {row['id_inventory'] if not pd.isna(row['id_inventory']) else 'Unknown ID'}")
                continue

            inventory = Inventory(
                id=row['id_inventory'],
                book_id=row['id_book'],
                owned_audio=bool(row['owned_audio']),
                owned_kindle=bool(row['owned_kindle']),
                owned_physical=bool(row['owned_physical']),
                date_purchased=parse_date(row['date_purchased']),
                location=row['location'] if not pd.isna(row['location']) else None,
                isbn_10=row['isbn_10'] if not pd.isna(row['isbn_10']) else None,
                isbn_13=row['isbn_13'] if not pd.isna(row['isbn_13']) else None
            )
            session.add(inventory)

        # Commit all changes
        session.commit()
        print("Import completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"Error during import: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python excel_import.py <path_to_excel_file>")
        sys.exit(1)

    excel_file = sys.argv[1]
    if not os.path.exists(excel_file):
        print(f"Error: File {excel_file} not found")
        sys.exit(1)

    import_excel_data(excel_file)
