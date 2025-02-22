"""
Root Directory Organization Script

This script reorganizes the root directory structure to improve project organization.
It creates necessary directories and moves files to their appropriate locations.
"""
import shutil
from pathlib import Path

def organize_root():
    """Organize the root directory structure"""
    project_root = Path(__file__).parent.parent.parent

    # Create new directory structure
    directories = [
        'docs/images',
        'config',
        'data/csv',
        'data/examples',
        'data/backups',
        'data/db',
        'logs',
        'src/migrations',
        'templates/excel',
        'templates/email'
    ]

    for directory in directories:
        (project_root / directory).mkdir(parents=True, exist_ok=True)

    # Files that MUST stay in root directory
    root_files = {
        'README.md':        'Primary project documentation, must be in root for GitHub/GitLab visibility',
        'LICENSE':         'License information, standard to keep in root',
        '.gitignore':      'Git configuration, must be in root to work properly',
        'pyproject.toml':  'Project metadata and build configuration, used by pip and build tools',
        'requirements.txt': 'Python dependencies, standard location for pip and deployment tools',
        'setup.py':        'Installation script, needed in root for pip install',
        'setup.sh':        'Unix setup script',
        'setup.bat':       'Windows setup script',
        '.project-root':   'Project root marker file',
        'git_commit.sh':   'Git commit helper script'
    }

    # Files/directories to move
    moves = [
        # Data directories
        ('csv', 'data/csv'),
        ('csv_examples', 'data/examples'),
        ('db_backups', 'data/backups'),
        ('reading_list.db', 'data/db/reading_list.db'),

        # Configuration
        ('.env', 'config/.env'),
        ('.env.example', 'config/.env.example'),
        ('logging.yaml', 'config/logging.yaml'),

        # Migrations
        ('migrations', 'src/migrations'),

        # Documentation
        ('GETTING_STARTED.md', 'docs/getting_started.md'),
        ('DATABASE.md', 'docs/database.md'),
        ('API.md', 'docs/api.md'),
        ('project_structure.txt', 'docs/project_structure.txt'),

        # Templates
        ('reading_list_template.xlsx', 'templates/excel/reading_list_template.xlsx'),
        ('daily_report_template.html', 'templates/email/daily_report_template.html'),
    ]

    # Move files/directories to their new locations
    for source, dest in moves:
        source_path = project_root / source
        dest_path = project_root / dest
        if source_path.exists():
            print(f"Moving {source} to {dest}")
            if source_path.is_dir():
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                shutil.copytree(str(source_path), str(dest_path))
                shutil.rmtree(str(source_path))
            else:
                shutil.move(str(source_path), str(dest_path))

    # Remove build artifacts
    build_artifacts = [
        'reading_list.egg-info',
        'build',
        'dist',
        '__pycache__'
    ]

    for artifact in build_artifacts:
        artifact_path = project_root / artifact
        if artifact_path.exists():
            print(f"Removing build artifact: {artifact}")
            if artifact_path.is_dir():
                shutil.rmtree(artifact_path)
            else:
                artifact_path.unlink()

    # Update .gitignore
    gitignore_entries = [
        '# Build',
        'reading_list.egg-info/',
        'build/',
        'dist/',
        '__pycache__/',
        '',
        '# Data',
        'data/db/*.db',
        'data/backups/',
        'data/csv/*',
        '!data/csv/.gitkeep',
        '',
        '# Config',
        'config/.env',
        '',
        '# Logs',
        'logs/*',
        '!logs/.gitkeep',
    ]

    gitignore_path = project_root / '.gitignore'
    with open(gitignore_path, 'a') as f:
        f.write('\n# Added by organize_root.py\n')
        f.write('\n'.join(gitignore_entries))

    print("\nDirectory organization complete!")
    print("\nRemember to:")
    print("1. Update import paths in your code")
    print("2. Update documentation references")
    print("3. Review the updated .gitignore")
    print("4. Update database connection strings to use new data/db path")
    print("5. Commit changes with descriptive message")

if __name__ == "__main__":
    organize_root()
