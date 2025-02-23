# Getting Started with Reading List Tracker

This guide will walk you through setting up the Reading List Tracker from scratch.

## Initial Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/reading-list.git
cd reading-list

# Create a new branch for your setup
git checkout -b setup/initial
```

### 2. Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv

# On Linux/MacOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install core dependencies
pip install -e .

# For development, install additional dependencies
pip install -e ".[dev]"
```

Note: The development installation includes additional tools for testing, linting, and code formatting.

Core Dependencies:
- SQLAlchemy (≥1.4.0) - Database ORM
- Alembic (≥1.7.0) - Database migrations
- Pandas (≥1.3.0) - Data manipulation
- XlsxWriter (≥3.0.0) - Excel file creation
- OpenPyXL (≥3.0.0) - Excel file reading
- Rich (≥10.0.0) - Terminal formatting
- Python-dotenv (≥0.19.0) - Environment configuration

Development Dependencies:
- Black - Code formatting
- isort - Import sorting
- MyPy - Type checking
- Pylint - Code linting
- Pytest - Testing framework

### 3. Configure Environment Variables

Create a `.env` file in the project root:
```env
# Gmail settings (required for email reports)
GMAIL_APP_PASSWORD="your_app_password"
SENDER_EMAIL="your.email@gmail.com"
RECEIVER_EMAIL="your.email@gmail.com"
```

To get your Gmail App Password:
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification if not already enabled
3. Go to App Passwords
4. Select "Mail" and your device
5. Copy the generated password

### 4. Database Setup

```bash
# Initialize the database
python scripts/setup/create_db.py
```

### 5. Create and Import Data

```bash
# Generate Excel template
python scripts/setup/excel_template.py

# This creates reading_list_template.xlsx in your current directory
```

Fill out the template with your reading data:

1. Books Sheet:
   - Add your books with unique `id_book`
   - Required: title, author
   - Optional but recommended: word_count, page_count

2. Read Sheet:
   - Add reading sessions
   - Required: id_read, id_book
   - Link to books using `id_book`

3. Inventory Sheet:
   - Track your book ownership
   - Required: id_inventory, id_book
   - Mark owned_audio, owned_kindle, owned_physical as TRUE/FALSE

Then import your data:
```bash
python scripts/setup/excel_import.py reading_list_template.xlsx
```

### 6. Verify Setup

```bash
# Check current readings
python scripts/database/db_cli.py --current

# Check inventory
python scripts/database/db_cli.py --inventory all
```

### 7. Email Reports Setup (Optional)

1. Test email reports:
```bash
./scripts/email/run_daily_report.sh
```

2. Set up daily reports (Linux/MacOS):
```bash
# Open crontab editor
crontab -e

# Add this line to run report at 9 AM daily
0 9 * * * /full/path/to/reading_list/scripts/email/run_daily_report.sh
```

## Common Tasks

### Adding New Books

1. Option 1: Add via Excel
   - Update your Excel template
   - Run `python scripts/setup/excel_import.py reading_list_template.xlsx`

2. Option 2: Use CLI (if implemented)
   - `python scripts/database/db_cli.py --add-book`

### Starting a New Reading Session

1. Add to Readings sheet in Excel template:
   - Generate new `id_read`
   - Reference existing `id_book`
   - Set `date_started`
   - Import using excel_import.py

### Updating Reading Progress

Use the database CLI:
```bash
python scripts/database/db_cli.py --update-progress <id_read> --pages <pages_read>
```

### Database Maintenance

Regular cleanup:
```bash
# Remove invalid entries
python scripts/database/db_cli.py --cleanup-books

# Remove empty entries
python scripts/database/db_cli.py --cleanup-empty
```

## Troubleshooting

### Database Issues

If your database becomes corrupted:
1. Backup your data:
   ```bash
   cp reading_list.sqlite reading_list.sqlite.backup
   ```
2. Recreate database:
   ```bash
   rm reading_list.sqlite
   python scripts/setup/create_db.py
   ```
3. Re-import your data:
   ```bash
   python scripts/setup/excel_import.py reading_list_template.xlsx
   ```

### Email Report Issues

1. Check .env configuration
2. Verify Gmail App Password
3. Enable "Less secure app access" in Gmail
4. Test email manually:
   ```bash
   python scripts/email/test_email.py
   ```

## Project Structure

Key directories:
```
reading_list/
├── src/               # Core code
│   ├── models/        # Database models
│   ├── services/      # Business logic
│   └── utils/         # Helper functions
├── scripts/
│   ├── database/      # Database management
│   ├── email/         # Email reports
│   └── cleanup/       # Maintenance tools
└── tests/             # Test suite
```

## Next Steps

1. Customize your Excel template
2. Set up regular backups
3. Configure email reports
4. Review the main README.md for advanced features

## Support

If you encounter issues:
1. Check the issues on GitHub
2. Review the troubleshooting guide
3. Open a new issue with:
   - Error message
   - Steps to reproduce
   - Your environment details
