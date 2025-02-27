"""Excel export functionality for reading list data"""

import pandas as pd
from datetime import datetime
from reading_list.models.base import SessionLocal

class ExcelExporter:
    def __init__(self):
        pass
        
    def create_excel_file(self, output_path, export_current=False):
        """
        Create an Excel file - either a template or export of current data.
        
        Args:
            output_path (str): Path where Excel file should be saved
            export_current (bool): If True, export current database content.
                                 If False, create empty template.
        """
        if export_current:
            self._export_database(output_path)
        else:
            self._create_template(output_path)
            
    def _export_database(self, output_path):
        """Export current database content"""
        session = SessionLocal()
        try:
            books_df = pd.read_sql_query(
                """
                SELECT 
                    id as id_book,
                    title,
                    COALESCE(author_name_first || ' ' || author_name_second, 
                            author_name_first, 
                            author_name_second) as author,
                    word_count,
                    page_count,
                    date_published,
                    author_gender,
                    series,
                    series_number,
                    genre
                FROM books
                """,
                session.bind
            )

            readings_df = pd.read_sql_query(
                """
                SELECT 
                    id as id_read,
                    id_previous as id_read_previous,
                    book_id as id_book,
                    media,
                    date_started,
                    date_finished_actual,
                    rating_horror,
                    rating_spice,
                    rating_world_building,
                    rating_writing,
                    rating_characters,
                    rating_readability,
                    rating_enjoyment,
                    (rating_horror + rating_spice + rating_world_building + 
                     rating_writing + rating_characters + rating_readability + 
                     rating_enjoyment) / 7.0 as rating_overall,
                    NULL as rating_over_rank,
                    rank
                FROM "read"
                """,
                session.bind
            )

            inventory_df = pd.read_sql_query(
                """
                SELECT 
                    id as id_inventory,
                    book_id as id_book,
                    owned_audio,
                    owned_kindle,
                    owned_physical,
                    date_purchased,
                    location,
                    isbn_10,
                    isbn_13
                FROM inv
                """,
                session.bind
            )

            writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
            books_df.to_excel(writer, sheet_name='Books', index=False)
            readings_df.to_excel(writer, sheet_name='Readings', index=False)
            inventory_df.to_excel(writer, sheet_name='Inventory', index=False)
            self._write_instructions(writer.book.add_worksheet('Instructions'))
            writer.close()

        finally:
            session.close()
            
    def _create_template(self, output_path):
        """Create template with example data"""
        books_df = pd.DataFrame([{
            'id_book': 1,
            'title': 'Project Hail Mary',
            'author': 'Andy Weir',
            'word_count': 110000,
            'page_count': 496,
            'date_published': '2021-05-04',
            'author_gender': 'M',
            'series': None,
            'series_number': None,
            'genre': 'Science Fiction'
        }])

        readings_df = pd.DataFrame([{
            'id_read': 1,
            'id_read_previous': None,
            'id_book': 1,
            'media': 'audio',
            'date_started': '2024-01-01',
            'date_finished_actual': '2024-01-15',
            'rating_horror': 0,
            'rating_spice': 0,
            'rating_world_building': 9,
            'rating_writing': 8,
            'rating_characters': 9,
            'rating_readability': 10,
            'rating_enjoyment': 9,
            'rating_overall': 9,
            'rating_over_rank': None,
            'rank': None
        }])

        inventory_df = pd.DataFrame([{
            'id_inventory': 1,
            'id_book': 1,
            'owned_audio': True,
            'owned_kindle': True,
            'owned_physical': False,
            'date_purchased': '2024-01-01',
            'location': 'Audible',
            'isbn_10': '0593135202',
            'isbn_13': '9780593135204'
        }])

        writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
        books_df.to_excel(writer, sheet_name='Books', index=False)
        readings_df.to_excel(writer, sheet_name='Readings', index=False)
        inventory_df.to_excel(writer, sheet_name='Inventory', index=False)
        self._write_instructions(writer.book.add_worksheet('Instructions'))
        writer.close()

    def _write_instructions(self, worksheet):
        """Write instructions to worksheet"""
        instructions = [
            "Instructions for Using This Template:",
            "",
            "1. General Guidelines:",
            "   - Fill out the Books sheet first",
            "   - Dates should be in YYYY-MM-DD format",
            "   - Required fields are marked in the column headers (*)",
            "",
            "2. Books Sheet:",
            "   - Each book needs a unique id_book*",
            "   - Title* and Author* combination must be unique",
            "   - word_count and page_count are optional but recommended",
            "",
            "3. Readings Sheet:",
            "   - id_read* must be unique",
            "   - id_book* must match an id_book from the Books sheet",
            "   - id_previous refers to a previous reading's id_read (if applicable)",
            "   - Ratings should be between 0 and 10",
            "",
            "4. Inventory Sheet:",
            "   - id_inventory* must be unique",
            "   - id_book* must match an id_book from the Books sheet",
            "   - owned_* fields should be TRUE or FALSE",
            "",
            "5. Important Notes:",
            "   - Don't modify column names",
            "   - Don't add or remove columns",
            "   - You can add as many rows as needed",
            "   - Book information is stored only in the Books sheet and referenced by id_book",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]

        for row, instruction in enumerate(instructions):
            worksheet.write(row, 0, instruction)
