import os
from pathlib import Path

def remove_empty_init_files(project_root: Path):
    """Remove empty __init__.py files"""
    empty_inits = []
    for init_file in project_root.rglob('__init__.py'):
        if init_file.stat().st_size == 0:
            print(f"Found empty __init__.py: {init_file}")
            empty_inits.append(init_file)
    
    if empty_inits:
        confirm = input("\nRemove these empty __init__.py files? (yes/no): ")
        if confirm.lower() == 'yes':
            for file in empty_inits:
                os.remove(file)
                print(f"Removed: {file}")

def remove_migration_artifacts(project_root: Path):
    """Remove old migration scripts and artifacts"""
    migration_files = [
        'migrate_author_names.py',
        'how_to_git_commit.md'
    ]
    
    found_files = []
    for file in migration_files:
        file_path = project_root / 'scripts' / file
        if file_path.exists():
            print(f"Found migration file: {file}")
            found_files.append(file_path)
    
    if found_files:
        confirm = input("\nRemove these migration files? (yes/no): ")
        if confirm.lower() == 'yes':
            for file in found_files:
                os.remove(file)
                print(f"Removed: {file}")

def consolidate_query_scripts(project_root: Path):
    """Print information about query scripts that could be consolidated"""
    query_scripts = [
        'query_db.py',
        'show_current_readings.py'
    ]
    
    found_scripts = []
    for script in query_scripts:
        script_path = project_root / 'scripts' / script
        if script_path.exists():
            found_scripts.append(script)
    
    if found_scripts:
        print("\nConsider consolidating these query scripts:")
        for script in found_scripts:
            print(f"- {script}")
        print("\nSuggestion: Create a unified CLI tool for database queries")

def main():
    project_root = Path(__file__).parent.parent
    
    print("Reading List Project Cleanup Utility")
    print("=" * 40)
    
    # 1. Remove empty __init__.py files
    remove_empty_init_files(project_root)
    
    # 2. Remove migration artifacts
    remove_migration_artifacts(project_root)
    
    # 3. Suggest query script consolidation
    consolidate_query_scripts(project_root)
    
    print("\nCleanup complete!")
    print("\nAdditional manual tasks:")
    print("1. Review and update database schema to remove redundant columns")
    print("2. Consider consolidating database query scripts into a single CLI tool")
    print("3. Update documentation to reflect any changes made")

if __name__ == "__main__":
    main()