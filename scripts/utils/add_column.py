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

def get_column_type():
    """Prompt user for column type"""
    valid_types = {
        '1': 'INTEGER',
        '2': 'TEXT',
        '3': 'VARCHAR',
        '4': 'BOOLEAN',
        '5': 'DATE',
        '6': 'FLOAT'
    }

    while True:
        print("\nAvailable column types:")
        for key, value in valid_types.items():
            print(f"{key}: {value}")

        choice = input("\nSelect column type (enter number): ")
        if choice in valid_types:
            col_type = valid_types[choice]

            # Handle VARCHAR length
            if col_type == 'VARCHAR':
                while True:
                    length = input("Enter VARCHAR length (e.g., 255): ")
                    if length.isdigit() and int(length) > 0:
                        col_type = f"VARCHAR({length})"
                        break
                    print("Please enter a valid positive number")

            return col_type
        print("Invalid choice. Please try again.")

def get_column_constraints():
    """Get column constraints from user input"""
    constraints = []

    # Nullable
    if input("Can this column be NULL? (y/N): ").lower() != 'y':
        constraints.append("NOT NULL")

    # Unique
    if input("Should this column be UNIQUE? (y/N): ").lower() == 'y':
        constraints.append("UNIQUE")

    # Default value
    if input("Do you want to set a DEFAULT value? (y/N): ").lower() == 'y':
        default_value = input("Enter default value: ")
        constraints.append(f"DEFAULT {default_value}")

    return " ".join(constraints)

def add_column(table_name, column_name, column_type, constraints):
    """Add a single column to a table"""
    with engine.connect() as conn:
        try:
            # First add the column without UNIQUE constraint
            base_constraints = constraints.replace('UNIQUE', '').strip()
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {base_constraints}"
            conn.execute(text(sql))

            # If UNIQUE was specified, add it as a separate command
            if 'UNIQUE' in constraints:
                sql = f"CREATE UNIQUE INDEX idx_{table_name}_{column_name}_unique ON {table_name}({column_name})"
                conn.execute(text(sql))

            conn.commit()
            print(f"\nSuccessfully added {column_name} column to {table_name} table")
        except Exception as e:
            print(f"\nError adding column {column_name}: {str(e)}")
            conn.rollback()

def main():
    # Get list of existing tables
    tables = get_existing_tables()

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Add a column to an existing database table')
    parser.add_argument('table', choices=tables, help='Name of the table to modify')
    args = parser.parse_args()

    # Get existing columns
    existing_columns = get_existing_columns(args.table)

    # Get column name
    while True:
        column_name = input("\nEnter new column name: ").strip()
        if not column_name:
            print("Column name cannot be empty")
        elif column_name in existing_columns:
            print(f"Column '{column_name}' already exists in table '{args.table}'")
        elif column_name.isidentifier():
            break
        else:
            print("Invalid column name. Use only letters, numbers, and underscores")

    # Get column type
    column_type = get_column_type()

    # Get constraints
    constraints = get_column_constraints()

    # Confirm action
    print(f"\nAbout to add column with following specifications:")
    print(f"Table: {args.table}")
    print(f"Column: {column_name}")
    print(f"Type: {column_type}")
    print(f"Constraints: {constraints}")

    if input("\nProceed? (y/N): ").lower() == 'y':
        add_column(args.table, column_name, column_type, constraints)
    else:
        print("\nOperation cancelled")

if __name__ == "__main__":
    main()
