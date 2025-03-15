---
title: Tech Stack
weight: 30
---

# Tech Stack

Pagoda is a Single Source of Truth (SSoT) system that enables the definition of flexible data structures, relationships, and access control (ACL).

## Core Architecture

Pagoda comprises two UI systems:
1. **Legacy UI**: Django template-based full-stack application
2. **New UI**: A combination of DRF-based REST API and React SPA

### Backend

- **Django (4.x)** - Full-stack web application framework
  - Entity-Attribute-Value (EAV) pattern for flexible data modeling
    - Entity: Schema definitions
    - EntityAttr: Attribute definitions with type information
    - Entry: Data instances
    - Attribute: Attribute values with versioning
    - AttributeValue: Actual values with type safety

- **Django REST Framework (3.x)** - RESTful API implementation
  - Automatic OpenAPI spec generation (drf-spectacular)

- **Service Layer Architecture**
  - Clear separation between data access and business logic
  - Dedicated services for search and data manipulation
  - Type-safe implementations with Python type hints

### Frontend

- **Legacy UI**
  - Django template-based rendering
  - Server-side rendering with traditional request-response cycle

- **New UI (React SPA) (18.x)**
  - Written in TypeScript (5.x)
  - MUI (6.x) - UI component library
  - State management and forms
    - react-hook-form (7.x)
    - zod (3.x) validation
  - react-router (7.x) - Routing
  - Communicates with APIv2 through a generated client

## Extended Features

### Search and Indexing

- **Elasticsearch (7.x)** - Advanced search capabilities
  - Cross-entity and attribute search
  - Flexible search options (exact/partial match, AND/OR, date range)
  - Search chain for traversing entry relationships
  - Filter options (empty/non-empty, text contains/not contains)
  - Asynchronous result export

### Background Processing

- **Celery (5.x)** - Asynchronous task processing
  - Kombu (5.x) - Messaging library
  - Flower (1.x) - Task monitoring

### Data Management

- **History Management**
  - django-simple-history (3.x)

- **Data Type Support**
  - String, boolean, date, object references, etc.

## Development Tools

### Code Quality

- **Static Analysis**
  - ESLint (8.x) - TypeScript code analysis
  - Prettier (3.x) - Code formatter
  - Ruff (0.x) - Python linter and formatter
  - mypy (1.x) - Python type checking

- **Testing**
  - Jest (29.x) - JavaScript testing
  - Django standard test framework - Python testing

### Build Tools

- **Frontend**
  - Webpack (5.x) - Module bundler
  - TypeScript (5.x) - Type-safe JavaScript
  - openapi-generator - API type definition generation

- **Backend**
  - Poetry - Python dependency management

## Architecture Components

### Directory Structure

- **docs/** - End-user and developer documentation
- **frontend/** - React SPA
  - **src/apiclient/** - Wrapper for the generated API client
- **api_v2/** - DRF APIv2 code
- Other paths - Django application code

### API Architecture

- **APIv2** - REST API for the new UI
  - Shares core features with the legacy UI (models, Celery tasks, other utilities)
  - Schema as code, integration via OpenAPI spec auto-generation
  - Advanced search API
    - Complex search parameters
    - Chainable search capabilities
    - Export functionality

## Security and Permissions

- **Fine-grained ACL System**
  - Flexible permission settings for each attribute data
  - Dynamic schema definition for structured data
