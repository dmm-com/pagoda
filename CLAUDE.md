# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pagoda (formerly AirOne) is an entity/metadata management platform with flexible data-structure, relations, and ACL. Backend is Django + DRF, frontend is React + TypeScript + Material-UI.

## Build, Lint, and Test Commands

### Backend (Python/Django)
- **Run all tests for an app:** `uv run python manage.py test <app_name>`
- **Run a specific test:** `uv run python manage.py test <app_name>.tests.<test_file>.<TestClass>.<test_method>`
- **Lint (ruff):** `uv run ruff check .`
- **Type check:** `uv run mypy .`
- **Generate test data:** `uv run python tools/generate_testdata.py`

### Frontend (TypeScript/React)
- **Build:** `npm run build`
- **Build production:** `npm run build:production`
- **Lint:** `npm run lint` (eslint + biome + knip)
- **Fix lint:** `npm run fix`
- **Run tests:** `npm run test`
- **Run specific test:** `npm run test -- -t "test name pattern"`
- **Watch mode:** `npm run watch`

### API Client Generation
- **Generate client:** `npm run generate:client`
- **Generate custom client:** `npm run generate:custom_client`

## Architecture

### Django Apps
All models with access control inherit from `acl.models.ACLBase`. Core domain apps:
- **entity/** - Entity/schema definitions (EntityAttr, Entity)
- **entry/** - Data records (Entry, AttributeValue, AliasEntry)
- **acl/** - Access control layer (ACLBase permission system)
- **user/** - Custom User model (extends AbstractUser)
- **group/**, **role/** - User grouping and RBAC
- **job/** - Async job tracking with Celery (JobOperation enum defines 22+ operation types)
- **trigger/** - Conditional triggers on entry operations
- **webhook/** - Event notifications to external systems
- **category/** - Categorization system
- **dashboard/** - Dashboard views

### API Versions
- **api_v1/** - Primary REST API at `/api/v1/` (entity, entry, job, user endpoints)
- **api_v2/** - Plugin-focused API at `/api/v2/` (custom_view and plugin handlers)

### Frontend (`frontend/src/`)
- **pages/** - Page components (routes under `/ui/`)
- **components/** - Reusable React components
- **hooks/** - Custom hooks (usePage, usePagodaSWR, etc.)
- **routes/** - Route configuration (entity-scoped: `/ui/entities/{entityId}/entries/*`)
- **repository/** - API client (AironeApiClient)
- **plugins/** - Frontend plugin integration

### Plugin System
- **plugin/sdk/** - Independent plugin SDK (`pagoda_plugin_sdk`, separate from Django)
- **plugin/examples/** - Sample plugins (hello-world, cross-entity)
- **airone/plugins/override_manager.py** - Registry for operation overrides (CREATE/RETRIEVE/UPDATE/DELETE/LIST)
- **airone/lib/plugin_dispatch.py** - `PluginOverrideMixin` intercepts ViewSet actions and routes to plugin handlers
- **Request flow:** Request → PluginOverrideMixin._dispatch_override → override_registry → handler(OverrideContext)

### Custom View System
- **custom_view/** - Optional app for extending without forking
- Registered at `/api/v1/advanced/` and `/api/v2/custom/`
- Custom views take precedence over default views
- `custom_view/lib/task.py` defines CUSTOM_TASKS for job system integration

### Key Infrastructure
- **Elasticsearch** (`airone/lib/elasticsearch.py`) - Advanced search, auto-indexing on entry changes
- **Celery** - Heavy operations (import/export/indexing) are async via job/ app
- **MySQL** with read-replica routing via `django-replicated` (5s write pin)
- **Authentication** - LDAP (`airone/auth/ldap.py`), SAML, social auth, token auth
- **Settings** - `airone/settings_common.py` (base), `airone/settings.py` (Dev/Prd configurations via django-configurations)

### Operational Scripts (`tools/`)
- `clear_and_initdb.sh` - Database initialization
- `register_user.sh` - User creation
- `generate_client.sh` - API client codegen (OpenAPI → TypeScript)
- `initialize_es_document.py`, `sync_es_index.sh` - Elasticsearch management

## Code Style Guidelines
- **Python:** PEP 8, max 100 chars (ruff), type annotations encouraged
- **TypeScript:** Strict typing, ESLint + Biome rules
- **Comments and documentation:** Write in English only
- **Imports:** All imports at file top. No mid-function imports except for circular dependency prevention (e.g., Entity model import inside plugin mixin methods)
- **Frontend naming:** PascalCase for components, camelCase for variables/functions
- **Frontend imports:** Group by external/internal, sort alphabetically
