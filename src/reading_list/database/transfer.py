"""
Database Transfer Module
=======================

Provides functionality for exporting and importing the reading list database.
Supports SQLite file transfer, SQL dump, and CSV formats.
"""

import shutil
import sqlite3
import csv
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from reading_list.utils.paths import get_project_paths

console = Console()
paths = get_project_paths()

class DatabaseTransfer:
    def __init__(self):
        self.db_path = paths['database']
        self.backup_dir = paths['backups']
        self.engine = create_engine(f"sqlite:///{self.db_path}")

    def create_backup(self) -> Path:
        """Create a backup of the current database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"reading_list_{timestamp}_backup.db"
        
        shutil.copy2(self.db_path, backup_path)
        console.print(f"[green]Created backup at: {backup_path}[/green]")
        return backup_path

    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database"""
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def export_database(self, output_path: Optional[Path] = None, format: str = "sqlite") -> None:
        """
        Export the database to the specified path
        
        Args:
            output_path: Path to export to. If None, generates a timestamped name
            format: Format to export as ('sqlite', 'sql', or 'csv')
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "sqlite":
            if output_path is None:
                output_path = Path(f"reading_list_export_{timestamp}.db")
            shutil.copy2(self.db_path, output_path)
            console.print(f"[green]Database exported to: {output_path}[/green]")
        
        elif format == "sql":
            if output_path is None:
                output_path = Path(f"reading_list_export_{timestamp}.sql")
            try:
                conn = sqlite3.connect(self.db_path)
                with open(output_path, 'w') as f:
                    for line in conn.iterdump():
                        f.write(f'{line}\n')
                console.print(f"[green]Database exported as SQL to: {output_path}[/green]")
            finally:
                conn.close()

        elif format == "csv":
            if output_path is None:
                output_path = Path(f"reading_list_export_{timestamp}")
            output_path.mkdir(parents=True, exist_ok=True)
            
            tables = self.get_all_tables()
            for table in tables:
                df = pd.read_sql_table(table, self.engine)
                csv_path = output_path / f"{table}.csv"
                df.to_csv(csv_path, index=False)
            console.print(f"[green]Database exported as CSV files to: {output_path}[/green]")

    def import_database(self, input_path: Path, create_backup: bool = True) -> None:
        """
        Import the database from the specified path
        
        Args:
            input_path: Path to import from
            create_backup: Whether to create a backup before import
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Import file not found at {input_path}")

        if create_backup:
            self.create_backup()

        if input_path.is_dir():  # CSV import
            try:
                for csv_file in input_path.glob("*.csv"):
                    table_name = csv_file.stem
                    df = pd.read_csv(csv_file)
                    df.to_sql(table_name, self.engine, if_exists='replace', index=False)
                console.print("[green]Database imported successfully from CSV files[/green]")
            except Exception as e:
                raise ImportError(f"Failed to import CSV files: {str(e)}")

        elif input_path.suffix == '.sql':
            try:
                conn = sqlite3.connect(self.db_path)
                with open(input_path) as f:
                    conn.executescript(f.read())
                console.print("[green]Database imported successfully from SQL dump[/green]")
            finally:
                conn.close()
        else:
            shutil.copy2(input_path, self.db_path)
            console.print("[green]Database imported successfully[/green]")
