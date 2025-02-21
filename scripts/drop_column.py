import sys
import os
import argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.base import engine
from sqlalchemy import text

def drop_column(table_name, column_name):
    """
    Drop a column from a specified table

    Args:
        table_name (str): Name of the table to modify
        column_name (str): Name of the column to drop
    """
    with engine.connect() as conn:
        try:
            sql = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
            conn.execute(text(sql))
            conn.commit()
            print(f"Successfully dropped {column_name} column from {table_name} table")
        except Exception as e:
            print(f"Error dropping column {column_name}: {str(e)}")
            conn.rollback()

def main():
    parser = argparse.ArgumentParser(description='Drop a column from a table')
    parser.add_argument('table_name', help='Name of the table')
    parser.add_argument('column_name', help='Name of the column to drop')

    args = parser.parse_args()
    drop_column(args.table_name, args.column_name)

if __name__ == "__main__":
    main()