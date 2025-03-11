#SQL Commands

alias sqlt="sqlite3 data/db/reading_list.db '.tables'"

alias SQL='DB="data/db/reading_list.db"; \
    echo -e "\nBOOKS TABLE:"; \
    sqlite3 $DB "pragma table_info(books);" && \
    echo -e "\nREAD TABLE:"; \
    sqlite3 $DB "pragma table_info(read);" && \
    echo -e "\nINV TABLE:"; \
    sqlite3 $DB "pragma table_info(inv);" && \
    echo -e "\nISBN TABLE:"; \
    sqlite3 $DB "pragma table_info(isbn);"'

# Cleanup Commands

alias pycache='find . -type d \( -name "__pycache__" -o -name ".pytest_cache" \) -exec rm -rf {} +'

# Tree Commans

alias tsrl='clear && tree src/reading_list/'

alias ts='clear && tree scripts/'


# CLI Commands

alias update_book='reading-list update-entries && reading-list update-readings --all'

alias chain_report='reading-list chain-report'

alias status='reading-list status'

alias media_stats='clear && reading-list media-stats --finished-only'

alias series_stats='clear && reading-list series-stats --finished-only'

alias email='reading-list email-report'

alias update_db='reading-list update-readings --all'

alias ver='reading-list version --check'

alias tbr='reading-list chain-report'

alias shelves='reading-list shelf && reading-list shelf --shelve'

