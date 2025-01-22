# Frontend Architecture

Pagoda provides two distinct user interfaces: a modern React-based SPA (New UI) and a traditional Django template-based interface (Legacy UI). This document explains both interfaces, their features, and how to work with them.

## For Users

### Overview

#### New UI (React SPA)
- Modern, responsive single-page application
- Fast, client-side navigation
- Real-time updates and validations
- Consistent look and feel using Material-UI
- Internationalization support

#### Legacy UI (Django Templates)
- Traditional server-side rendered pages
- Direct database operations
- Stable and proven interface
- Simpler architecture for basic operations

### Key Features

#### Common Features
- Entity and attribute management
- User and group administration
- Access control management
- Advanced search capabilities
- History tracking
- Webhook management

#### New UI Specific Features
- Improved response times through API-based operations
- Modern form handling with real-time validation
- Enhanced user experience with instant feedback
- Consistent styling across all pages
- Mobile-friendly responsive design

#### Legacy UI Specific Features
- Direct database operations
- Server-side validation
- Traditional navigation pattern
- Simpler debugging process

### When to Use Which UI

#### Use New UI When
- Working with modern browsers
- Requiring real-time feedback
- Needing mobile-friendly interface
- Performing complex data operations
- Integrating with other modern web applications

#### Use Legacy UI When
- Requiring simpler, proven interface
- Working in environments with limited JavaScript support
- Needing direct database operations
- Performing basic CRUD operations

## For Developers

### Architecture Overview

#### New UI Architecture

##### Core Technologies
- React 18
- TypeScript
- Material-UI (MUI)
- react-router for routing
- react-hook-form for form management
- zod for schema validation
- i18next for internationalization

##### Directory Structure
```
frontend/src/
├── apiclient/      # API client wrapper
├── components/     # Reusable UI components
├── hooks/          # Custom React hooks
├── i18n/          # Internationalization
├── pages/         # Page components
├── repository/    # Data access layer
├── routes/        # Routing configuration
└── services/      # Business logic
```

##### Key Components
- API Client: Auto-generated from OpenAPI specs
- Form Management: react-hook-form with zod validation
- State Management: React hooks and context
- Routing: react-router with type-safe routes
- UI Components: Material-UI based components

#### Legacy UI Architecture

##### Core Technologies
- Django Templates
- jQuery (where needed)
- Bootstrap for styling

##### Template Structure
```
templates/
├── advanced_search/   # Search interface
├── edit_entry/       # Entry management
├── list_entry/       # Entry listing
├── registration/     # User registration
├── role/            # Role management
└── show_entry/      # Entry display
```

### Development Guidelines

#### Setting Up Development Environment

```bash
# Install dependencies
npm install

# Start development server
npm run watch

# Build for production
npm run build:production
```

#### Adding New Features

1. **New UI Development**
   - Follow React component patterns
   - Use TypeScript for type safety
   - Implement responsive design
   - Add appropriate test coverage
   - Update API client when needed

2. **Legacy UI Development**
   - Follow Django template patterns
   - Maintain backwards compatibility
   - Keep JavaScript usage minimal
   - Test across different browsers

#### Testing

1. **New UI Testing**
   - Unit tests with Jest
   - Component testing with React Testing Library
   - E2E testing when needed
   - i18n testing

2. **Legacy UI Testing**
   - Django template testing
   - Integration testing
   - Browser compatibility testing

### Performance Considerations

#### New UI
- Use React.memo for expensive components
- Implement proper code splitting
- Optimize bundle size
- Use appropriate caching strategies

#### Legacy UI
- Minimize server-side processing
- Optimize template rendering
- Use appropriate caching
- Minimize database queries
