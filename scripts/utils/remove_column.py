import argparse
from src.models.base import engine
from sqlalchemy import text, inspect

def get_existing_tables():
    """Get list of existing tables in the database"""
    inspector = inspect(engine)
    return inspector.get_table_names()

def get_existing_columns(table_name):
    """Get list of existing columns in a table"""
    inspector = inspect(engine)
    return [col['name'] for col in inspector.get_columns(table_name)]

def remove_column(table_name, column_name):
    """Remove a single column from a table"""
    with engine.connect() as conn:
        try:
            # Begin transaction
            trans = conn.begin()

            # Get all columns except the one to be removed
            result = conn.execute(text(f"pragma table_info({table_name})"))
            columns = [row[1] for row in result.fetchall() if row[1] != column_name]

            if not columns:
                print(f"\nError: Cannot remove all columns from table {table_name}")
                return

            # Create new table without the specified column
            columns_str = ', '.join(columns)
            conn.execute(text(f"""
                CREATE TABLE {table_name}_new AS
                SELECT {columns_str}
                FROM {table_name}
            """))

            # Drop the old table
            conn.execute(text(f"DROP TABLE {table_name}"))

            # Rename the new table to the original name
            conn.execute(text(f"ALTER TABLE {table_name}_new RENAME TO {table_name}"))

            # Recreate any indexes (except for the removed column)
            result = conn.execute(text(f"""
                SELECT sql FROM sqlite_master
                WHERE type='index' AND tbl_name='{table_name}'
                AND sql IS NOT NULL
                AND sql NOT LIKE '%{column_name}%'
            """))

            for row in result:
                if row[0]:
                    conn.execute(text(row[0]))

            trans.commit()
            print(f"\nSuccessfully removed {column_name} column from {table_name} table")

        except Exception as e:
            print(f"\nError removing column {column_name}: {str(e)}")
            if 'trans' in locals():
                trans.rollback()

def main():
    # Get list of existing tables
    tables = get_existing_tables()

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Remove a column from an existing database table')
    parser.add_argument('table', choices=tables, help='Name of the table to modify')
    args = parser.parse_args()

    # Get existing columns
    existing_columns = get_existing_columns(args.table)

    # Print available columns
    print("\nAvailable columns:")
    for i, col in enumerate(existing_columns, 1):
        print(f"{i}: {col}")

    # Get column selection
    while True:
        try:
            choice = input("\nSelect column to remove (enter number): ")
            idx = int(choice) - 1
            if 0 <= idx < len(existing_columns):
                column_name = existing_columns[idx]
                break
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

    # Confirm action
    print(f"\nAbout to remove column with following specifications:")
    print(f"Table: {args.table}")
    print(f"Column: {column_name}")

    if input("\nProceed? (y/N): ").lower() == 'y':
        remove_column(args.table, column_name)
    else:
        print("\nOperation cancelled")

if __name__ == "__main__":
    main()