# Reading List Tracker v2.3.18

A Python-based application to track reading habits, book inventory, and reading statistics.

## Quick Start

👉 **New users:** See our detailed [Getting Started Guide](docs/GETTING_STARTED.md) for step-by-step setup instructions.

## Features

- Track current and completed reading sessions
- Manage book inventory across multiple formats (physical, Kindle, audio)
- Generate daily reading progress reports via email
- Calculate reading statistics and progress
- Command-line interface for database operations

## Project Structure

```
reading_list/
├── docs/              # Documentation
├── config/            # Configuration files
├── src/              # Core application code
├── scripts/          # Utility scripts
├── tests/            # Test suite
├── templates/        # Excel and email templates
└── [Configuration]   # Project configuration files
```

For detailed structure information, see [Project Structure](docs/project_structure.txt)

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Gmail account for email reports
- SQLite (default) or other supported database

## Installation

For detailed setup instructions, please refer to our [Getting Started Guide](docs/GETTING_STARTED.md).

Quick setup:

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd reading_list
   ```

2. Run the setup script:
   ```bash
   python setup.py
   ```

This will:
- Create and configure the virtual environment
- Install all dependencies
- Set up necessary directories
- Run initial tests

## Environment Setup

Create a `.env` file in the project root:

```env
GMAIL_APP_PASSWORD="your_app_password"
SENDER_EMAIL="your.email@gmail.com"
RECEIVER_EMAIL="your.email@gmail.com"
```

Notes:
- Gmail App Password: Generate at https://myaccount.google.com/apppasswords
- Required for daily reading report emails
- Sender and receiver can be the same email address

## Database Management

Initialize and manage the database:

```bash
# Initialize database
python scripts/setup/create_db.py

# Import data from Excel template
python scripts/setup/excel_import.py

# Database operations
python scripts/database/db_cli.py --help
```

Common database operations:
- Show current readings: `--current`
- Show inventory: `--inventory [all|physical|kindle|audio]`
- Clean up invalid books: `--cleanup-books`
- Clean up empty entries: `--cleanup-empty`

## Reports

Generate various reading reports:

```bash
# Generate yearly reading report
python scripts/metrics/yearly_reading_report.py 2024

# Generate projected readings report
python scripts/metrics/projected_readings.py 2024
```

## Email Reports

Generate daily reading progress reports:

```bash
# Test the email report
reading-list email-report

# Set up cron job for daily reports
crontab -e
# Add: 0 9 * * * /path/to/reading_tracker/src/reading_list/cli/commands/daily_report.sh
```

## Project Maintenance

Keep the project clean and up-to-date:

```bash
# Update version numbers
python scripts/version.py --update <version>

# Clean up codebase
python scripts/cleanup/run_cleanup.py

# Commit changes
version-commit <version> "<commit message>"
```

## Documentation

- [Getting Started Guide](docs/GETTING_STARTED.md) - Detailed setup instructions
- [Project Structure](project_structure.txt) - Detailed codebase organization
- [Database Schema](docs/DATABASE.md) - Database structure and relationships

## Development

Key technologies:
- SQLAlchemy: Database ORM
- Alembic: Database migrations
- Pandas: Data manipulation
- Rich: Terminal formatting

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Open Pull Request

## License

[Add your chosen license here]

## Support

For issues and feature requests, please use the GitHub issue tracker.
