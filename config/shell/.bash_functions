
function sqlti()
{
        sqlite3 data/db/reading_list.db "pragma table_info($1)"
}

function sql()
{
        sqlite3 data/db/reading_list.db "$1"
}

# Shortcut function to Reorder Books within their
#    respective chains of the database
function rob()
{
        reading-list reorder $1 $2
}

function chain()
{
        reading-list chain $1
}

function book()
{
        python -c "from reading_list.queries.common_queries import CommonQueries; CommonQueries().print_readings_by_title('$1', exact_match=False)"
}

function show_table()
{
        sqlite3 -header -column data/db/reading_list.db "SELECT * FROM $1"
}


function cover()
{
        sudo curl -L "$1" -o "$WORKSPACE/assets/book_covers/$2.jpg"
        reading-list chain-report
        echo "Cover added for book ID $2"
        ls -alh "$WORKSPACE/assets/book_covers/$2.jpg"
}


function blank_cover()
{
        echo "Adding blank cover for book ID $1"
        cp assets/book_covers/0.jpg assets/book_covers/$1.jpg
}