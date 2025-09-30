#!/usr/bin/env python3
"""
Database Migration: Add days_estimate_override column
====================================================

This script adds the 'days_estimate_override' column to the 'read' table.
The column is a Boolean field that defaults to FALSE.

When days_estimate_override is TRUE, the update-readings command will skip
recalculating the days_estimate for that reading entry.

Usage:
    python scripts/database/add_days_estimate_override_column.py

The script will:
1. Create a backup of the current database
2. Add the new column with default value FALSE
3. Verify the column was added successfully
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from reading_list.utils.paths import get_project_paths

console = Console()

def create_backup(db_path: Path) -> Path:
    """Create a backup of the database before migration"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent.parent / "backups" / f"reading_list_before_days_estimate_override_{timestamp}.db"
    
    # Ensure backup directory exists
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy the database
    import shutil
    shutil.copy2(db_path, backup_path)
    console.print(f"[green]✓ Created backup at: {backup_path}[/green]")
    return backup_path

def check_column_exists(cursor: sqlite3.Cursor) -> bool:
    """Check if the days_estimate_override column already exists"""
    cursor.execute("PRAGMA table_info(read)")
    columns = [row[1] for row in cursor.fetchall()]
    return 'days_estimate_override' in columns

def add_column(cursor: sqlite3.Cursor) -> None:
    """Add the days_estimate_override column to the read table"""
    try:
        cursor.execute("""
            ALTER TABLE read 
            ADD COLUMN days_estimate_override BOOLEAN DEFAULT FALSE
        """)
        console.print("[green]✓ Successfully added days_estimate_override column[/green]")
    except sqlite3.Error as e:
        console.print(f"[red]✗ Error adding column: {e}[/red]")
        raise

def verify_migration(cursor: sqlite3.Cursor) -> None:
    """Verify the migration was successful"""
    # Check column exists
    if not check_column_exists(cursor):
        raise Exception("Column was not added successfully")
    
    # Check default value
    cursor.execute("SELECT COUNT(*) FROM read WHERE days_estimate_override IS NULL")
    null_count = cursor.fetchone()[0]
    
    if null_count > 0:
        console.print(f"[yellow]⚠ Warning: {null_count} rows have NULL values for days_estimate_override[/yellow]")
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM read")
    total_count = cursor.fetchone()[0]
    
    console.print(f"[green]✓ Migration verified: {total_count} total readings in table[/green]")

def main():
    """Main migration function"""
    console.print("[bold cyan]Database Migration: Adding days_estimate_override column[/bold cyan]")
    console.print()
    
    # Get database path
    paths = get_project_paths()
    db_path = paths['database']
    
    if not db_path.exists():
        console.print(f"[red]✗ Database not found at: {db_path}[/red]")
        return 1
    
    console.print(f"Database: {db_path}")
    console.print()
    
    # Connect to database and check current state
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        if check_column_exists(cursor):
            console.print("[yellow]⚠ Column 'days_estimate_override' already exists![/yellow]")
            return 0
        
        # Show current table info
        cursor.execute("PRAGMA table_info(read)")
        columns = cursor.fetchall()
        console.print(f"Current 'read' table has {len(columns)} columns")
        
        # Confirm migration
        if not Confirm.ask("\nProceed with migration?", default=True):
            console.print("[yellow]Migration cancelled[/yellow]")
            return 0
        
        # Create backup
        backup_path = create_backup(db_path)
        
        # Add the column
        console.print("\n[dim]Adding days_estimate_override column...[/dim]")
        add_column(cursor)
        
        # Commit changes
        conn.commit()
        
        # Verify migration
        console.print("\n[dim]Verifying migration...[/dim]")
        verify_migration(cursor)
        
        console.print("\n[bold green]✓ Migration completed successfully![/bold green]")
        console.print(f"[dim]Backup saved at: {backup_path}[/dim]")
        
        return 0
        
    except Exception as e:
        console.print(f"\n[red]✗ Migration failed: {e}[/red]")
        conn.rollback()
        return 1
        
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
