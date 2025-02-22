#!/bin/bash

# Check if both arguments are provided
if [ $# -ne 2 ]; then
    echo "Error: Missing required arguments"
    echo "Usage: ./git_commit.sh <version> <commit_message>"
    echo "Example: ./git_commit.sh \"1.1.0\" \"Updated version to 1.1.0\""
    exit 1
fi

# Update the read table
python scripts/updates/update_read_db.py --all

# Run cleanup all scripts
python scripts/cleanup/run_cleanup.py

# Run framework tests first
echo -e "\nRunning framework tests..."
if python tests/framework/test_scripts.py; then
    echo "Framework tests passed"
else
    echo "Framework tests failed"
    exit 1
fi

# Run all other tests
echo -e "\nRunning main test suite..."
if python tests/run_tests.py; then
    echo "All tests passed"
else
    echo "Some tests failed"
    exit 1
fi

# Run version update script and capture its exit status
python scripts/updates/update_version.py --update "$1"
UPDATE_STATUS=$?

# Check if update_version.py succeeded
if [ $UPDATE_STATUS -ne 0 ]; then
    echo "Error: Version update failed"
    exit 1
fi
echo "Version updated to $1"

# 1. See what files have been changed
git status

# 2. Add files to staging
git add .

# 3. Commit the changes
git commit -m "$2"

# 4. Push changes to remote repository
git push

# 5. Check status again to show everything is clean
git status

echo "Done! Version $1 has been committed and pushed"
```
