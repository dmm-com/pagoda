# Advanced Search

Advanced Search is a powerful feature that allows you to search across multiple entities and their attributes with various search options and filters.

## Features

### Search Capabilities

- **Cross-Entity Search**
  - Search across multiple entity types simultaneously
  - Filter results by entity type
  - Combine search results from different entities

- **Attribute-Based Search**
  - Search by specific attribute values
  - Support for various data types:
    - Text (string, multi-line text)
    - Numbers
    - Dates and date ranges
    - Boolean values
    - Object references

- **Search Options**
  - Exact match or partial match
  - AND/OR conditions between multiple search criteria
  - Filter by attribute conditions:
    - Empty values
    - Non-empty values
    - Text contains/not contains
    - Date ranges

### Advanced Features

- **Search Chain**
  - Follow relationships between entries
  - Search through referenced objects
  - Chain multiple searches to traverse complex relationships
  - Results include both direct matches and related entries

- **Export Functionality**
  - Export search results to various formats
  - Asynchronous processing for large result sets
  - Progress tracking for export tasks
  - Download exported files when ready

## Access Methods

### Web UI (Legacy)

The legacy UI provides a full-featured search interface with:
- Interactive search form
- Real-time search results
- Advanced filtering options
- Export capabilities
- Search chain visualization

### REST API (APIv2)

Access Advanced Search programmatically through REST endpoints:
- `/api/v2/advanced_search/` - Main search endpoint
- `/api/v2/advanced_search_chain/` - Search chain operations
- `/api/v2/advanced_search_result/` - Export and result management

## Limitations and Considerations

### Search Limits

- Maximum results per query: Configurable, default is 100 entries
- Export size limits may apply for very large result sets
- Complex search chains may increase response time

### Performance Considerations

- Large result sets are processed asynchronously
- Complex search chains may require multiple API calls
- Export operations for large datasets run in the background

### Access Control

- Search results respect user permissions
- Attribute-level access control applies to search results
- Export operations require appropriate permissions

## Best Practices

- Use specific entity and attribute combinations when possible
- Leverage search chains for complex relationship queries
- Monitor export task progress for large result sets
- Consider pagination for large result sets in API usage

## For Developers

### Architecture Overview

#### Core Components

- **Service Layer**
  - `AdvancedSearchService`: Main service class handling search operations
  - Type-safe implementations using Python type hints and Pydantic models
  - Clear separation between data access and business logic

- **Search Engine**
  - Elasticsearch-based implementation
  - Custom index mapping for optimized search
  - Support for nested objects and complex queries
  - Configurable result window and timeout settings

- **Data Models**
  - Entity-Attribute-Value (EAV) pattern for flexible data modeling
  - Versioned attribute values
  - Type-safe attribute value storage

#### Implementation Details

- **Search Process Flow**
  1. Query Building: Create Elasticsearch query from search parameters
  2. Permission Checking: Apply ACL filters at entity and attribute levels
  3. Result Processing: Transform Elasticsearch results to typed models
  4. Chain Processing: Handle relationship traversal for search chains

- **Asynchronous Operations**
  - Celery tasks for background processing
  - Export task management and progress tracking
  - Configurable task queues and priorities

### API Integration

#### REST Endpoints

- **Advanced Search**
  - Endpoint: `/api/v2/advanced_search/`
  - Supports complex search parameters
  - Returns paginated, typed results
  - Handles ACL filtering

- **Search Chain**
  - Endpoint: `/api/v2/advanced_search_chain/`
  - Manages relationship traversal
  - Supports multiple chain steps
  - Combines results across relationships

- **Export Management**
  - Endpoint: `/api/v2/advanced_search_result/`
  - Handles asynchronous export requests
  - Provides task status monitoring
  - Manages file downloads

#### Response Types

- Strongly typed response models using Pydantic
- Consistent error handling
- Support for various result formats

### Development Guidelines

#### Adding New Features

- Extend search capabilities through service layer
- Maintain type safety with Pydantic models
- Follow existing patterns for ACL integration
- Add appropriate test coverage

#### Performance Optimization

- Use appropriate Elasticsearch index settings
- Implement efficient query patterns
- Consider bulk operations for large datasets
- Leverage caching where appropriate

#### Testing

- Unit tests for service layer
- Integration tests for API endpoints
- Performance tests for search operations
- ACL verification tests
