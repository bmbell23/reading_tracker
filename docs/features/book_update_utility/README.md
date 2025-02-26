# Book Update Utility

## Overview
The Book Update Utility is a command-line interface tool for managing and updating book-related data across the reading list database. It provides an interactive way to modify entries in the books, reading sessions, and inventory tables.

## Key Features

### 1. Multi-Table Management
- Books table: Core book information
- Reading sessions table: Reading progress tracking
- Inventory table: Book ownership and location tracking

### 2. Interactive Search
- Search by ID or title
- Combined results from ID and title searches
- Clear tabulated display of search results
- Support for partial matches

### 3. Smart Data Entry
- Field-specific validation
- Current value display
- Optional field skipping
- Type conversion handling
  - Dates (YYYY-MM-DD format)
  - Booleans (y/n inputs)
  - Numbers
  - Text

### 4. Related Entry Management
- Chain updates across related tables
- Automatic relationship maintenance
- Creation of related entries when needed

### 5. Visual Feedback
- Rich text formatting
- Success/error messages
- Entry cards showing updated information
- Progress indicators

## Usage

### Basic Operations

1. **Table Selection**
   ```bash
   Which table would you like to modify? [books/read/inv]
   ```

2. **Search**
   - By ID: Enter numeric ID
   - By Title: Enter full or partial title
   - Results show relevant information based on table

3. **Entry Updates**
   - Current values shown for each field
   - Press Enter to skip/keep current value
   - Validation feedback for invalid inputs

4. **Related Updates**
   - Option to update related entries
   - Example: Update inventory after adding new book

## Technical Details

### Database Tables

1. **Books Table**
   - Core book information
   - Title, author, word count, etc.
   - Primary source for book data

2. **Reading Table**
   - Reading session tracking
   - Start/end dates
   - Progress metrics

3. **Inventory Table**
   - Ownership tracking
   - Multiple format support (physical/kindle/audio)
   - Location tracking

### Data Validation

1. **Date Validation**
   - YYYY-MM-DD format
   - Future date checks where appropriate
   - Optional date fields

2. **Boolean Input**
   - y/n input format
   - Case insensitive
   - Default values

3. **Numeric Validation**
   - Type checking
   - Range validation where appropriate
   - Optional fields handling

## Error Handling

### Common Errors

1. **Input Errors**
   - Invalid date formats
   - Invalid boolean inputs
   - Missing required fields

2. **Database Errors**
   - Constraint violations
   - Transaction failures
   - Connection issues

### Recovery Procedures

1. **Transaction Management**
   - Automatic rollback on failure
   - Session cleanup
   - State preservation

2. **User Feedback**
   - Clear error messages
   - Retry options
   - Recovery suggestions

## Best Practices

### When Using the Utility

1. **Search Best Practices**
   - Use IDs for precise matches
   - Use partial titles for broader searches
   - Review all results before selecting

2. **Data Entry**
   - Verify information before confirming
   - Use standardized formats
   - Check related entries

3. **Batch Updates**
   - Plan related updates
   - Verify relationships
   - Check consistency after updates

## Future Improvements

### Planned Features

1. **Enhanced Search**
   - [ ] Advanced filtering
   - [ ] Multiple criteria search
   - [ ] Search history

2. **Batch Operations**
   - [ ] Multi-entry updates
   - [ ] Bulk imports
   - [ ] Mass changes

3. **User Experience**
   - [ ] Command history
   - [ ] Configurable defaults
   - [ ] Custom field templates

### Technical Debt

1. **Code Structure**
   - [ ] Modularize large functions
   - [ ] Improve error handling
   - [ ] Add comprehensive logging

2. **Testing**
   - [ ] Add unit tests
   - [ ] Add integration tests
   - [ ] Add validation tests

## Related Documentation

- [Database Schema](../../DATABASE.md)
- [Getting Started Guide](../../GETTING_STARTED.md)
- [Technical Documentation](../../TECHNICAL.md)