# Book Update Utility Styles Guide

## Console Output Styles

### 1. Headers
- Bold cyan for section headers
- White background for main titles
- Green for success messages

### 2. Input Prompts
- Cyan for current values
- Yellow for optional fields
- Red for required fields

### 3. Results Display
- Tabulated format
- Alternating row colors
- Bold for key fields

### 4. Error Messages
- Red background for critical errors
- Yellow for warnings
- White text for error details

### 5. Success Messages
- Green background
- White text
- Bold for important details

## Visual Components

### 1. Entry Cards
- Bordered panels
- Title in header
- Field-value pairs
- Color-coded sections

### 2. Search Results
- Compact table format
- Truncated long values
- Highlighted matches

### 3. Progress Indicators
- Spinner for operations
- Progress bars for batch operations
- Status messages

## Style Constants

```python
# Color Schemes
header_style = "bold cyan"
error_style = "bold red"
success_style = "bold green"
warning_style = "yellow"

# Panel Styles
panel_border_style = "green"
panel_title_style = "bold white"

# Table Styles
table_header_style = "bold cyan"
table_border_style = "blue"
```

## Usage Guidelines

### 1. Message Types
- Use error_style for exceptions
- Use warning_style for validation issues
- Use success_style for confirmations

### 2. Data Display
- Use panels for detailed views
- Use tables for lists
- Use progress bars for operations

### 3. User Input
- Show current values in cyan
- Show options in brackets
- Show required fields with asterisk