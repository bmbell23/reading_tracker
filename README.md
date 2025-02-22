# Reading List Tracker v1.4.0

A Python-based application to track reading habits, book inventory, and reading statistics.

## Project Structure

```
reading_list/
├── src/               # Core application code
│   ├── models/        # Database models
│   ├── services/      # Business logic
│   ├── utils/         # Helper functions
│   └── api/           # Future API endpoints
├── scripts/
│   ├── database/      # Database management scripts
│   │   └── db_cli.py  # Database operations CLI
│   ├── utils/         # Utility scripts
│   │   ├── inspect_chain.py
│   │   ├── search_book.py
│   │   └── verify_dates.py
│   ├── cleanup/       # Cleanup utilities
│   └── [Other scripts]
└── [Configuration files]
```

## Database Management
- Initialize database: `python scripts/create_db.py`
- Import data: `python scripts/excel_import.py`
- Database operations:
  - Show current readings: `python scripts/database/db_cli.py --current`
  - Show inventory: `python scripts/database/db_cli.py --inventory [all|physical|kindle|audio]`
  - Clean up invalid books: `python scripts/database/db_cli.py --cleanup-books`
  - Clean up empty entries: `python scripts/database/db_cli.py --cleanup-empty`

## Project Maintenance
- Update version numbers: `python scripts/version.py --update <version>`
- Commit changes: `./git_commit.sh <version> "<commit message>"`
- Clean up codebase: `python scripts/cleanup/run_cleanup.py`

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
