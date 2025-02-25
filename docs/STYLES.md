# Styles Documentation

## TBR Manager Styles

Located in `static/css/tbr_manager.css`, these styles define the visual language for the reading list management interface.

### Color System

```css
:root {
    /* Core colors */
    --color-bg: #f5f5f5;
    --color-text: #333;
    --color-primary: #2c3e50;
    --color-secondary: #34495e;
    --color-accent: #3498db;
    --color-warning: #e74c3c;
    --color-success: #2ecc71;

    /* Media-specific colors */
    --kindle-color: #427AA1;
    --kindle-bg: #EFF6FF;
    --hardcover-color: #7A4242;
    --hardcover-bg: #FAF5FF;
    --audio-color: #427A42;
    --audio-bg: #FFF7ED;
}
```

### Component Architecture

1. **Toolbar**
   - Three-section layout (left, center, right)
   - Search bar with real-time filtering
   - Theme toggle and refresh controls
   - Export functionality
   - Sort dropdown

2. **Stats Dashboard**
   - Reading streak with visual indicators
   - Monthly goal progress
   - Reading pace with trend indicators
   - Responsive grid layout

3. **Filters**
   - Primary filter buttons with counts
   - Advanced filters panel
   - Date range selection
   - Priority and status filters

4. **Reading Chain**
   - Chain header with statistics
   - Draggable book cards
   - Progress indicators
   - Action buttons
   - Media-specific styling

5. **Book Card**
   - Title section with series information
   - Status badges
   - Detail groups
   - Progress bar
   - Action buttons

### Accessibility Features

1. **Navigation**
   - Skip to main content link
   - Proper heading hierarchy
   - ARIA labels and roles
   - Keyboard navigation support

2. **Interactive Elements**
   - Button states and focus indicators
   - Progress bar announcements
   - Status updates
   - Tooltip information

3. **Visual Hierarchy**
   - Clear content structure
   - Status indicators
   - Progress visualization
   - Action button clarity

### Responsive Design

- Fluid grid system
- Flexible component layouts
- Mobile-first approach
- Breakpoint-based adaptations

### Spacing System

```css
:root {
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
}
```

### Typography

- Font: 'Plus Jakarta Sans'
- Fallbacks: -apple-system, BlinkMacSystemFont, sans-serif
- Size scale: 0.9rem to 2.5rem
- Weights: 400, 500, 600, 700

[Rest of the document remains unchanged...]
