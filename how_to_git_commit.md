
# 0. Change to your project directory
cd /home/bbell/sandbox/projects/personal/reading_tracker/reading_list

# 1. See what files have been changed
git status

# 2. Add files to staging
git add .                    # Add all changes
# OR
git add specific_file.py     # Add specific file
# OR
git add src/*               # Add all files in specific directory

# 3. Commit the changes
git commit -m "$1"

# 4. Push changes to remote repository (if you have one set up)
git push
```

## Best Practices for Commits

1. **Check Status First**
   ```bash
   git status
   ```
   This shows you:
   - Modified files (red)
   - Staged files (green)
   - Untracked files

2. **Review Your Changes**
   ```bash
   git diff
   ```
   Shows exact changes in unstaged files

3. **Write Good Commit Messages**
   - Keep messages clear and concise
   - Start with a verb (Add, Update, Fix, Remove, etc.)
   - Example good messages:
     - "Add database models for books table"
     - "Fix bug in rating calculation"
     - "Update README with setup instructions"

4. **Commit Related Changes Together**
   - Group related changes in single commits
   - Split unrelated changes into separate commits

## Example Workflow
```bash
# Check status
git status

# Add specific files
git add src/models/book.py
git add README.md

# Check what's staged
git status

# Commit with message
git commit -m "Add book model and update README"

# Push to remote (if set up)
git push
```

## Useful Additional Commands
```bash
# Undo staging of files
git reset HEAD file.py

# Discard changes in working directory
git checkout -- file.py

# See commit history
git log

# See shortened commit history
git log --oneline
```