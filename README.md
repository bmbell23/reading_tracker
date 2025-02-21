# Reading List Tracker v1.0.1

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
   - Reading speed metrics
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

[Usage instructions will be added as features are implemented]

## Project Structure

```
reading_list/
├── src/
│   ├── models/          # Database models
│   ├── services/        # Business logic, calculations
│   ├── utils/           # Helper functions
│   └── api/            # Future API endpoints
├── scripts/
│   └── excel_import.py  # Script to import Excel data
├── tests/
├── requirements.txt
└── config.py
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
