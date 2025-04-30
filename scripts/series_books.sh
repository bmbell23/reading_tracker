#!/bin/bash

# Check if a series name was provided
if [ -z "$1" ]; then
    echo "Usage: $0 \"series name\""
    exit 1
fi

# Escape the series name for SQL
SERIES_NAME="$1"

# Execute the query
sqlite3 -header -column data/db/reading_list.db "
SELECT
    b.title,
    b.series_number,
    b.date_published,
    CASE
        WHEN EXISTS (SELECT 1 FROM read r WHERE r.book_id = b.id AND r.date_finished_actual IS NOT NULL)
        THEN 'Yes'
        ELSE 'No'
    END as 'Read',
    CASE
        WHEN EXISTS (SELECT 1 FROM inv i WHERE i.book_id = b.id AND (i.owned_physical = 1 OR i.owned_kindle = 1 OR i.owned_audio = 1))
        THEN 'Yes'
        ELSE 'No'
    END as 'Owned',
    CASE
        WHEN b.date_published IS NULL OR b.date_published > date('now')
        THEN 'Yes'
        ELSE 'No'
    END as 'Future/Unpublished'
FROM books b
WHERE b.series = '$SERIES_NAME'
ORDER BY b.series_number"
