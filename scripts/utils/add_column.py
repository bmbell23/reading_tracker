import sys
import os
import argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.base import engine
from sqlalchemy import text

def add_columns(table_name, columns):
    """
    Add multiple columns to a specified table

    Args:
        table_name (str): Name of the table to modify
        columns (list): List of tuples containing (column_name, column_type)
    """
    with engine.connect() as conn:
        for column_name, column_type in columns:
            try:
                # Create ALTER TABLE statement
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                conn.execute(text(sql))
                conn.commit()
                print(f"Successfully added {column_name} column to {table_name} table")
            except Exception as e:
                print(f"Error adding column {column_name}: {str(e)}")
                conn.rollback()

def main():
    parser = argparse.ArgumentParser(description='Add columns to a database table')
    parser.add_argument('table', help='Name of the table to modify')
    parser.add_argument('columns', nargs='+', help='Columns to add in format: name:type')

    args = parser.parse_args()

    # Parse column definitions
    columns = []
    for col in args.columns:
        try:
            name, type_ = col.split(':')
            columns.append((name, type_))
        except ValueError:
            print(f"Error: Invalid column format '{col}'. Use name:type")
            sys.exit(1)

    add_columns(args.table, columns)

if __name__ == "__main__":
    main()