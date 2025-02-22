# Technical Documentation

## Project Structure
The project follows a standardized directory structure:

```
reading_list/
├── config/               # Configuration files
│   ├── .env             # Environment variables (not in git)
│   ├── .env.example     # Example environment file
│   └── logging.yaml     # Logging configuration
├── data/                # All data files
│   ├── db/             # Database files
│   ├── csv/            # CSV exports/imports
│   ├── backups/        # Database backups
│   └── examples/       # Example data files
├── docs/               # Documentation
├── logs/              # Application logs
├── src/               # Source code
├── scripts/           # Utility scripts
├── templates/         # Templates
└── tests/            # Test suite
```

## Environment Variables
Required environment variables in `config/.env`:

```env
WORKSPACE="/path/to/project"          # Project root path
GMAIL_APP_PASSWORD="your_password"    # Gmail API password
SENDER_EMAIL="email@example.com"      # Sender email
RECEIVER_EMAIL="email@example.com"    # Receiver email
DATABASE_PATH="data/db/reading_list.db"  # Optional: Custom DB path
```

## Database
- Location: `data/db/reading_list.db`
- Backup Location: `data/backups/`
- Schema: See [DATABASE.md](DATABASE.md)

### Database Operations
Common operations:
```bash
# Backup database
python scripts/database/backup_db.py

# Restore from backup
python scripts/database/restore_db.py --backup-file YYYY-MM-DD_backup.db

# Export to CSV
python scripts/database/export_csv.py
```

## Logging
- Configuration: `config/logging.yaml`
- Log files: `logs/`
- Log rotation: Daily with 30-day retention

## Development Setup

### Prerequisites
- Python 3.8+
- pip
- virtualenv or venv
- Git

### First-time Setup
```bash
# Clone repository
git clone [repository-url]
cd reading_list

# Windows
setup.bat

# Linux/MacOS
./setup.sh
```

### Development Environment
```bash
# Activate virtual environment
# Windows
venv\Scripts\activate

# Linux/MacOS
source venv/bin/activate

# Install core dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Version Information
Current version: 1.5.0

Major changes in this version:
- Significant documentation overhaul
- Added automated email reports via cron
- Streamlined dependency management
- Separated core and development dependencies

### Dependency Management
- Core dependencies are defined in `pyproject.toml`
- Development tools are available as optional dependencies
- Use `pip install -e ".[dev]"` for development setup
- Requirements are locked in `requirements.txt`

## Testing
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_database.py

# Run with coverage
python -m pytest --cov=src tests/
```

## Common Issues & Solutions

### Database Errors
If you encounter database errors:
1. Check file permissions in `data/db/`
2. Verify SQLite version compatibility
3. Try restoring from backup:
   ```bash
   python scripts/database/restore_db.py --latest
   ```

### Email Configuration
If email reports fail:
1. Verify Gmail App Password is correct
2. Check sender email permissions
3. Test email configuration:
   ```bash
   python scripts/email/test_email.py
   ```

### Path Issues
If you encounter path-related errors:
1. Verify `WORKSPACE` in `config/.env`
2. Check directory permissions
3. Run path verification:
   ```bash
   python scripts/utils/verify_paths.py
   ```

## Maintenance Tasks

### Regular Maintenance
```bash
# Update dependencies
pip install -U -r requirements.txt

# Clean up database
python scripts/cleanup/run_cleanup.py

# Backup database
python scripts/database/backup_db.py
```

### Version Updates
```bash
# Update version
python scripts/version.py --update X.Y.Z

# Commit changes
./git_commit.sh "X.Y.Z" "Version bump to X.Y.Z"
```

## Contributing
1. Create feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```
2. Run tests before commit:
   ```bash
   python scripts/pre_commit.py
   ```
3. Update documentation if needed
4. Submit pull request

## Build & Distribution
```bash
# Create distribution
python -m build

# Upload to PyPI (if applicable)
python -m twine upload dist/*
```

## Security Considerations
- Store sensitive data in `config/.env`
- Regular database backups
- Sanitize user inputs
- Keep dependencies updated
- Follow GDPR guidelines for user data

## Performance Tips
- Use batch operations for database updates
- Enable SQLite optimizations
- Cache frequently accessed data
- Use appropriate indexes

## Additional Resources
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Python Testing Guide](https://docs.pytest.org/)
- [Project Wiki](https://github.com/your-repo/wiki)

## Architecture

### Core Components
- **Database Layer**: SQLAlchemy ORM with SQLite backend
- **Service Layer**: Business logic and data processing
- **CLI Interface**: Command-line tools for database operations
- **Report Generator**: Email report generation system
- **Data Import/Export**: Excel and CSV data handling

### Data Flow
1. Data Input:
   - Excel template import
   - Direct CLI input
   - Database migrations
2. Processing:
   - Data validation
   - Statistics calculation
   - Progress tracking
3. Output:
   - Daily email reports
   - CSV exports
   - CLI displays

## Database Schema Details

### Books Table
```sql
CREATE TABLE books (
    id_book INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    word_count INTEGER,
    page_count INTEGER,
    words_per_page INTEGER,
    date_published DATE,
    year_published INTEGER,
    author_gender TEXT,
    series TEXT,
    series_number INTEGER,
    series_word_count INTEGER,
    genre TEXT
);
```

### Readings Table
```sql
CREATE TABLE readings (
    id_read INTEGER PRIMARY KEY,
    id_previous INTEGER,
    id_book INTEGER NOT NULL,
    format TEXT,
    date_started DATE,
    date_finished_actual DATE,
    date_finished_estimate DATE,
    words_per_day_actual INTEGER,
    words_per_day_goal INTEGER,
    FOREIGN KEY (id_book) REFERENCES books(id_book)
);
```

### Inventory Table
```sql
CREATE TABLE inventory (
    id_inventory INTEGER PRIMARY KEY,
    id_book INTEGER NOT NULL,
    owned_audio BOOLEAN,
    owned_kindle BOOLEAN,
    owned_physical BOOLEAN,
    FOREIGN KEY (id_book) REFERENCES books(id_book)
);
```

## API Documentation

### Database Operations
```python
from src.services.database import DatabaseService

# Create new book
db.add_book(title="Example", author="Author Name")

# Update reading progress
db.update_reading_progress(id_read=1, pages_read=50)

# Get reading statistics
stats = db.get_reading_stats(user_id=1)
```

### Report Generation
```python
from src.services.reports import ReportGenerator

# Generate daily report
report = ReportGenerator.create_daily_report()

# Generate custom date range report
report = ReportGenerator.create_range_report(
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

## Configuration Details

### Logging Configuration
```yaml
# config/logging.yaml
version: 1
formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers:
  file:
    class: logging.handlers.RotatingFileHandler
    filename: logs/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 30
root:
  level: INFO
  handlers: [file]
```

### Database Configuration
```python
# src/config/database.py
DATABASE_CONFIG = {
    'pool_size': 5,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 1800,
}
```

## Error Handling

### Database Errors
```python
from src.exceptions import DatabaseError

try:
    db.execute_operation()
except DatabaseError as e:
    logger.error(f"Database operation failed: {e}")
    # Implement recovery strategy
```

### Data Validation
```python
from src.validators import BookValidator

def validate_book_data(data: dict):
    validator = BookValidator(data)
    if not validator.is_valid():
        raise ValidationError(validator.errors)
```

## Performance Optimization

### Database Indexing
```sql
-- Recommended indexes
CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_readings_date ON readings(date_started, date_finished_actual);
CREATE INDEX idx_inventory_book ON inventory(id_book);
```

### Batch Operations
```python
def bulk_import_books(books: List[Dict]):
    with db.batch_operations():
        for book in books:
            db.add_book(**book)
```

## Backup and Recovery

### Backup Strategy
1. Daily automated backups
2. Pre-migration backups
3. Manual backups before major operations

### Recovery Procedures
1. Verify backup integrity
2. Stop application services
3. Restore from backup
4. Validate data consistency
5. Restart services

## Monitoring

### Key Metrics
- Database size and growth rate
- Query performance
- API response times
- Error rates
- Report generation time

### Health Checks
```python
def check_system_health():
    checks = {
        'database': check_db_connection(),
        'email': check_email_service(),
        'disk_space': check_storage_space(),
        'backup_status': check_latest_backup()
    }
    return checks
```

## Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints
- Document all public functions
- Write unit tests for new features

### Git Workflow
1. Feature branches from `develop`
2. Pull request review required
3. CI/CD checks must pass
4. Squash merge to `develop`
5. Release branches from `develop` to `main`

### Version Control
```bash
# Create release
./scripts/release.sh <version>

# Hot fixes
git checkout -b hotfix/issue-description main
```

## Deployment

### Requirements
- Python 3.8+
- SQLite 3.30+
- 1GB RAM minimum
- 500MB disk space

### Production Setup
```bash
# Production deployment
python scripts/deploy.py --env production

# Health check
python scripts/monitor.py --check-health
```

## Support and Maintenance

### Regular Tasks
- Daily: Check error logs
- Weekly: Review performance metrics
- Monthly: Update dependencies
- Quarterly: Full system audit

### Troubleshooting Guide
1. Check logs in `logs/app.log`
2. Verify database consistency
3. Test email connectivity
4. Validate file permissions
5. Review recent changes

## Future Improvements
- Migration to PostgreSQL
- REST API implementation
- Web interface
- Mobile app integration
- Cloud backup integration
