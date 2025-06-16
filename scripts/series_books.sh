#!/bin/bash

# Check if a series name was provided
if [ -z "$1" ]; then
    echo "Usage: $0 \"series name\""
    exit 1
fi

# Store the series name
SERIES_NAME="$1"

# Print a fancy header
echo ""
echo "📚 Series: $SERIES_NAME"
echo ""

# Properly escape the series name for SQL
SERIES_NAME_ESCAPED=$(echo "$SERIES_NAME" | sed "s/'/''/g")

# Execute the query with custom formatting
sqlite3 -header data/db/reading_list.db << EOF
.mode column
.headers on
.width 50 13 14 12 6 7 10 5 5
SELECT
    b.title,
    b.series_number,
    b.date_published,
    printf('%,12d', COALESCE(b.word_count, 0)) as 'Word Count',
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
        THEN 'No'
        ELSE 'Yes'
    END as 'Published',
    b.id as 'BID',
    (SELECT r.id FROM read r WHERE r.book_id = b.id ORDER BY COALESCE(r.date_finished_actual, '9999-12-31') DESC, r.id DESC LIMIT 1) as 'RID'
FROM books b
WHERE b.series = '$SERIES_NAME_ESCAPED'
ORDER BY b.series_number;
EOF

# Now add summary information
echo ""
echo "Summary for series: $SERIES_NAME"
echo "----------------------------------------"

# Get total word count
TOTAL_WORDS=$(sqlite3 data/db/reading_list.db "
    SELECT printf('%,d', SUM(COALESCE(word_count, 0)))
    FROM books
    WHERE series = '$SERIES_NAME_ESCAPED'
")
echo "Total Word Count: $TOTAL_WORDS"

# Get novel and novella counts
NOVEL_COUNT=$(sqlite3 data/db/reading_list.db "
    SELECT COUNT(*)
    FROM books
    WHERE series = '$SERIES_NAME_ESCAPED'
    AND word_count >= 45000
")

NOVELLA_COUNT=$(sqlite3 data/db/reading_list.db "
    SELECT COUNT(*)
    FROM books
    WHERE series = '$SERIES_NAME_ESCAPED'
    AND word_count < 45000
")

TOTAL_COUNT=$((NOVEL_COUNT + NOVELLA_COUNT))

echo "Book Count: $NOVEL_COUNT novels, $NOVELLA_COUNT novellas ($TOTAL_COUNT total)"

# Add a note about novel/novella classification
echo ""
echo "Note: Books are classified as novels if they are ≥45,000 words, otherwise they are considered novellas."
