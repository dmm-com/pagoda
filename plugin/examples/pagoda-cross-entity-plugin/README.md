# Cross-Entity Sample Plugin

A sample plugin demonstrating cross-entity operations using the endpoint override pattern.

## Overview

This plugin shows how to override standard Entry API operations to implement custom cross-entity behavior. Instead of creating new API endpoints, the plugin intercepts existing Entry API calls for specific entities and provides custom handling.

**Version**: 2.0.0
**Pattern**: Endpoint Override

## Features

- Override Service entity CRUD operations (create, retrieve, update, delete)
- Automatic creation of related Configuration entries
- Atomic cross-entity transactions with rollback support
- Permission pre-checking for all affected entries
- Cascade delete for related entries

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     Entry API v2                               │
│  (existing endpoints: /api/v2/entries/, /api/v2/entities/)    │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                   Override Dispatcher                          │
│         (checks OverrideRegistry for entity/operation)        │
└────────────────────────┬───────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
┌──────────────────┐          ┌──────────────────┐
│  Plugin Handler  │          │ Default Handler  │
│  (if registered) │          │ (if no override) │
└──────────────────┘          └──────────────────┘
```

## Installation

1. Install the plugin SDK:
   ```bash
   cd plugin/sdk && pip install -e .
   ```

2. Install this plugin:
   ```bash
   cd plugin/examples/pagoda-cross-entity-plugin && pip install -e .
   ```

3. Enable the plugin in AirOne settings:
   ```python
   # airone/settings.py
   ENABLED_PLUGINS = [
       "cross-entity-sample",
   ]
   ```

## Plugin Structure

```
pagoda_cross_entity_plugin/
├── __init__.py          # Package exports
├── plugin.py            # Plugin class with override registration
├── handlers.py          # Override handler implementations
└── relationships.py     # Entity relationship definitions
```

## Usage

### Defining Override Handlers

Use the `@override_entry_operation` decorator to mark methods as override handlers:

```python
from pagoda_plugin_sdk.override import (
    override_entry_operation,
    accepted_response,
    error_response,
)

class ServiceHandlers:
    @override_entry_operation(entity="Service", operation="create")
    def handle_create(self, request, entity, data, **kwargs):
        """Handle Service entry creation with related entries."""
        # Custom creation logic
        return accepted_response({"id": entry.id, "name": entry.name})
```

### Supported Operations

| Operation | Handler Signature |
|-----------|-------------------|
| `create`  | `handle_create(self, request, entity, data, **kwargs)` |
| `retrieve`| `handle_retrieve(self, request, entry, **kwargs)` |
| `update`  | `handle_update(self, request, entry, validated_data, **kwargs)` |
| `delete`  | `handle_delete(self, request, entry, **kwargs)` |
| `list`    | `handle_list(self, request, entity, **kwargs)` |

### Response Helpers

The SDK provides response helper functions:

```python
from pagoda_plugin_sdk.override import (
    success_response,        # 200 OK with data
    created_response,        # 201 Created
    accepted_response,       # 202 Accepted
    no_content_response,     # 204 No Content
    error_response,          # 400 Bad Request (customizable)
    not_found_response,      # 404 Not Found
    permission_denied_response,  # 403 Forbidden
    validation_error_response,   # 400 with validation errors
)
```

### Cross-Entity Utilities

Use the cross_entity SDK modules for complex operations:

```python
from pagoda_plugin_sdk.cross_entity import (
    atomic_operation,         # Transaction context manager
    CompositeEntry,           # Entry with related data
    BatchPermissionChecker,   # Check permissions for multiple entries
)

# Atomic transaction
with atomic_operation(user) as op:
    service = op.create_entry(entity_name="Service", name="my-service", attrs={})
    config = op.create_entry(entity_name="Configuration", name="config-1", attrs={})
    # Both entries created atomically, or both rolled back on error

# Composite entry with relationships
composite = CompositeEntry.from_entry(
    entry=service_entry,
    relationships=self.relationships,
    fetch_related=True,
)
response_data = composite.to_dict()

# Batch permission check
checker = BatchPermissionChecker(user)
result = checker.check_entries(entries_list, "write")
if not result.all_granted:
    return permission_denied_response(denied_entries=result.denied_ids)
```

## Entity Relationships

Define relationships in `relationships.py`:

```python
from pagoda_plugin_sdk.cross_entity import EntityRelationship, RelationType

SERVICE_RELATIONSHIPS = [
    EntityRelationship(
        source_entity="Service",
        target_entity="Configuration",
        relation_type=RelationType.COMPOSITION,
        attribute_name="configurations",
        cascade_delete=True,
        required=False,
    ),
]
```

## API Behavior

When this plugin is enabled, the standard Entry API behaves differently for Service entries:

### Create Service Entry

**Endpoint**: `POST /api/v2/entities/{entity_id}/entries/`

**Request** (with related entries):
```json
{
  "name": "my-service",
  "attrs": {
    "description": "A test service"
  },
  "configurations": [
    {"name": "config-1", "attrs": {"key": "value"}}
  ]
}
```

**Response** (202 Accepted):
```json
{
  "id": 123,
  "name": "my-service",
  "configurations": [
    {"id": 456, "name": "config-1"}
  ],
  "message": "Service creation accepted"
}
```

### Retrieve Service Entry

**Endpoint**: `GET /api/v2/entries/{entry_id}/`

Returns composite data including all related entries.

### Delete Service Entry

**Endpoint**: `DELETE /api/v2/entries/{entry_id}/?cascade=true`

The `cascade=true` query parameter triggers cascade deletion of related entries.

## Testing

Run the plugin tests:

```bash
# SDK-side tests
cd plugin/sdk && python -m pytest tests/test_override.py -v

# AirOne-side tests
poetry run python manage.py test airone.plugins.tests.test_override
```

## Development Notes

- Handlers are registered during plugin initialization via the plugin registry
- Only one plugin can override a specific entity/operation combination
- Conflict detection prevents accidental override collisions
- The original Entry API behavior is used when no override is registered
