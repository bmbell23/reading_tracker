import pandas as pd
from datetime import datetime

def create_excel_template(output_path="reading_list_template.xlsx"):
    # Create a Pandas Excel writer
    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')

    # Books template
    books_columns = [
        'id_book',                  # required
        'title',                    # required
        'author',                   # required
        'word_count',               # optional
        'page_count',               # optional
        'date_published',           # optional (YYYY-MM-DD)
        'author_gender',            # optional
        'series',                   # optional
        'series_number',            # optional
        'genre'                     # optional
    ]

    # Readings template
    readings_columns = [
        'id_read',                  # required
        'id_read_previous',         # optional (ID of previous reading)
        'id_book',                  # required (must match id_book in books sheet)
        'media',                    # optional (was 'format')
        'date_started',             # optional (YYYY-MM-DD)
        'date_finished_actual',     # optional (YYYY-MM-DD)
        'rating_horror',            # optional (0-10)
        'rating_spice',             # optional (0-10)
        'rating_world_building',    # optional (0-10)
        'rating_writing',           # optional (0-10)
        'rating_characters',        # optional (0-10)
        'rating_readability',       # optional (0-10)
        'rating_enjoyment',         # optional (0-10)
        'rating_overall',           # optional (0-10)
        'rating_over_rank',         # optional
        'rank'                      # optional
    ]

    # Inventory template
    inventory_columns = [
        'id_inventory',             # required
        'id_book',                  # required (must match id_book in books sheet)
        'owned_audio',              # required (TRUE/FALSE)
        'owned_kindle',             # required (TRUE/FALSE)
        'owned_physical',           # required (TRUE/FALSE)
        'date_purchased',           # optional (YYYY-MM-DD)
        'location',                 # optional
        'isbn_10',                  # optional
        'isbn_13'                   # optional
    ]

    # Create empty DataFrames
    books_df = pd.DataFrame(columns=books_columns)
    readings_df = pd.DataFrame(columns=readings_columns)
    inventory_df = pd.DataFrame(columns=inventory_columns)

    # Add example rows
    books_df.loc[0] = [
        1,                          # id_book
        'The Hobbit',
        'J.R.R. Tolkien',
        95356,
        304,
        '1937-09-21',
        'M',
        'The Hobbit',
        1,
        'Fantasy'
    ]

    readings_df.loc[0] = [
        1,                          # id_read
        None,                       # id_previous
        1,                          # id_book
        'Physical',
        '2023-01-01',
        '2023-01-15',
        0,                         # rating_horror (0-10)
        0,                         # rating_spice (0-10)
        8,                         # rating_world_building (0-10)
        7,                         # rating_writing (0-10)
        9,                         # rating_characters (0-10)
        8,                         # rating_readability (0-10)
        9,                         # rating_enjoyment (0-10)
        8.2,                       # rating_overall (0-10)
        1,
        1
    ]

    inventory_df.loc[0] = [
        1,                          # id_inventory
        1,                          # id_book
        False,
        True,
        True,
        '2022-12-25',
        'Home Library',
        '0261103342',
        '9780261103344'
    ]

    # Write to Excel
    books_df.to_excel(writer, sheet_name='Books', index=False)
    readings_df.to_excel(writer, sheet_name='Readings', index=False)
    inventory_df.to_excel(writer, sheet_name='Inventory', index=False)

    # Get workbook and worksheet objects
    workbook = writer.book

    # Add instructions sheet
    worksheet = workbook.add_worksheet('Instructions')

    # Write instructions
    instructions = [
        "Instructions for Using This Template:",
        "",
        "1. General Guidelines:",
        "   - Fill out the Books sheet first",
        "   - Dates should be in YYYY-MM-DD format",
        "   - Required fields are marked in the column headers",
        "",
        "2. Books Sheet:",
        "   - Each book needs a unique id_book",
        "   - Title and Author combination must be unique",
        "",
        "3. Readings Sheet:",
        "   - id_book must match an id_book from the Books sheet",
        "   - id_previous refers to a previous reading's id_read (if applicable)",
        "   - Ratings should be between 0 and 10",
        "",
        "4. Inventory Sheet:",
        "   - id_book must match an id_book from the Books sheet",
        "   - owned_* fields should be TRUE or FALSE",
        "",
        "5. Important Notes:",
        "   - Don't modify column names",
        "   - Don't add or remove columns",
        "   - You can add as many rows as needed",
        "   - Book information is stored only in the Books sheet and referenced by id_book"
    ]

    for row, instruction in enumerate(instructions):
        worksheet.write(row, 0, instruction)

    # Save the file
    writer.close()

if __name__ == "__main__":
    create_excel_template()
