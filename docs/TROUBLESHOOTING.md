### Database Issues

If your database becomes corrupted:
1. Backup your data:
   ```bash
   cp data/db/reading_list.db data/db/reading_list.db.backup
   ```
2. Recreate database:
   ```bash
   rm data/db/reading_list.db
   python scripts/setup/create_db.py
   ```