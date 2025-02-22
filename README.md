# Reading List Tracker v1.3.1

A Python-based application to track reading habits, book inventory, and reading statistics.

## Database Structure

The application uses three main database tables:

1. **Book Database** - Stores book information
   - Basic info (title, author, publication date)
   - Book metrics (word count, page count)
   - Series information
   - Genre and author demographics

2. **Reading Database** - Tracks reading sessions
   - Reading progress (start/finish dates)
   - Reading speed metrics (actual vs. estimated days)
   - Reading time calculations:
     - Days estimate (based on word count and media type)
     - Days elapsed (including start and end dates)
     - Delta from estimate
   - Ratings (0-10 scale):
     - Horror
     - Spice
     - World Building
     - Writing
     - Characters
     - Readability
     - Enjoyment
     - Overall

3. **Inventory Database** - Manages book collection
   - Ownership status (physical, Kindle, audio)
   - Purchase information
   - Location and read status
   - ISBN information

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/reading_list.git
   cd reading_list
   ```

2. **Set up Python environment**
   ```bash
   python setup.py
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Create database**
   ```bash
   python scripts/create_db.py
   ```

## Usage

### Database Management
- Initialize database: `python scripts/create_db.py`
- Import data: `python scripts/excel_import.py`
- Query database: `python scripts/query_db.py`

### Reading Progress
- Update reading calculations: `python scripts/update_read_db.py`
  - Update all calculations: `--all`
  - Update specific calculations:
    - `--estimate` - Calculate estimated reading days
    - `--elapsed` - Calculate actual reading days
    - `--delta` - Calculate difference between estimated and actual
- View current readings: `python scripts/show_current_readings.py`

### Project Maintenance
- Update version numbers: `python scripts/version.py --update <version>`
- Commit changes: `./git_commit.sh <version> "<commit message>"`
- Clean up codebase: `python scripts/cleanup_codebase.py`

## Project Structure

```
reading_list/
├── src/
│   ├── models/          # Database models
│   ├── services/        # Business logic, calculations
│   ├── utils/           # Helper functions
│   ├── queries/         # Database queries
│   └── api/             # Future API endpoints
├── scripts/
│   ├── create_db.py           # Database initialization
│   ├── excel_import.py        # Data import from Excel
│   ├── query_db.py           # Database queries
│   ├── show_current_readings.py # Display active readings
│   ├── updates/              # Update operations
│   │   ├── update_book.py     # Book updates
│   │   ├── update_read_db.py  # Reading calculations
│   │   └── update_version.py  # Version management
│   ├── metrics/              # Statistics and metrics scripts
│   │   ├── series_stats.py
│   │   └── media_stats.py
│   └── util/                 # Utility scripts
        ├── fix_hardcover_chain.py
        └── fix_missing_data.py
├── tests/
└── [Configuration files]
```

## Development

- Python 3.8+
- SQLAlchemy for database operations
- Alembic for database migrations
- Pandas for data manipulation

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

[Add your chosen license here]
