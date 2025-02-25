# TBR Manager Styles Documentation

## Overview
This document describes the styling system used in the TBR Manager template. The system is designed to be modular, responsive, and easily maintainable.

## File Structure
```
templates/reports/
├── tbr_manager.html    # Main HTML template
├── styles/
│   └── tbr_manager.css # Main stylesheet
└── STYLES.md          # This documentation
```

## Design System

### Colors
The color system uses CSS variables for easy theming:
- `--color-bg`: Background color (#f5f5f5)
- `--color-text`: Main text color (#333)
- `--color-primary`: Primary color (#2c3e50)
- `--color-secondary`: Secondary color (#34495e)
- `--color-accent`: Accent color (#3498db)
- `--color-warning`: Warning color (#e74c3c)
- `--color-success`: Success color (#2ecc71)

Media-specific colors:
- `--kindle-color`: Kindle section color (#427AA1)
- `--hardcover-color`: Hardcover section color (#7A4242)
- `--audio-color`: Audio section color (#427A42)

### Typography
- Font Family: 'Plus Jakarta Sans'
- Base font size: 16px
- Scale:
  - h1: 2.5rem
  - h2: 1.5rem
  - h3: 1.1rem
  - Body: 1rem
  - Small text: 0.9rem

### Components

#### Book Card
```html
<div class="book-card kindle">
    <div class="book-header">
        <h3>Book Title</h3>
        <span class="author">Author Name</span>
    </div>
    <div class="book-details">
        <div class="detail">
            <span class="label">Started:</span>
            <span class="value">2023-01-01</span>
        </div>
    </div>
</div>
```

#### Reading Chain Section
```html
<section class="reading-chain kindle">
    <h2>Kindle Reading Chain</h2>
    <div class="chain-stats">
        <span>Books: 10</span>
        <span>Pages: 3000</span>
    </div>
    <!-- Book cards go here -->
</section>
```

### Grid System
The layout uses CSS Grid with responsive breakpoints:
- Desktop: 3 columns
- Tablet: 2 columns
- Mobile: 1 column

## Customization

### Adding New Media Types
1. Add a new color variable in `:root`
2. Create a new chain class in CSS:
```css
.reading-chain.new-media {
    border-top: 4px solid var(--new-media-color);
}
```

### Modifying Styles
All major components use CSS variables that can be modified in the `:root` section:
```css
:root {
    --color-primary: #your-color;
    --card-shadow: your-shadow-value;
}
```

## Best Practices

1. Always use the provided CSS variables for colors and transitions
2. Maintain the semantic HTML structure
3. Use the provided class names for consistency
4. Test responsive layouts when making changes

## Browser Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Requires CSS Grid support
- Flexbox fallbacks provided for older browsers
