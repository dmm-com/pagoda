# Cross-Entity Sample Plugin

A sample plugin demonstrating cross-entity operations using the ID-based endpoint override pattern.

## Overview

This plugin shows how to override standard Entry API operations for specific entities using ID-based configuration. Instead of hardcoding entity names, the plugin receives entity IDs from the `BACKEND_PLUGIN_ENTITY_OVERRIDES` configuration, allowing flexible deployment.

**Version**: 3.0.0
**Pattern**: ID-Based Endpoint Override

## Features

- Override Entry operations (create, retrieve, update, delete) for any configured entity
- ID-based configuration via environment variable
- Automatic creation of related entries
- Atomic cross-entity transactions with rollback support
- Permission pre-checking for all affected entries
- Cascade delete for related entries
- Full API compatibility with standard Entry serializers

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     Entry API v2                               │
│  (existing endpoints: /api/v2/entries/, /api/v2/entities/)    │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                 PluginOverrideMixin                            │
│    (checks OverrideRegistry using entity ID from config)       │
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

3. Enable the plugin in environment:
   ```bash
   export ENABLED_PLUGINS=cross-entity-sample
   ```

4. Configure entity overrides:
   ```bash
   export BACKEND_PLUGIN_ENTITY_OVERRIDES='{
     "42": {
       "plugin": "cross-entity-sample",
       "operations": ["create", "retrieve", "update", "delete"],
       "params": {
         "configuration_entity_id": 99,
         "cascade_delete": true
       }
     }
   }'
   ```

## Configuration

### BACKEND_PLUGIN_ENTITY_OVERRIDES Format

```json
{
  "entityId": {
    "plugin": "cross-entity-sample",
    "operations": ["create", "retrieve", "update", "delete"],
    "params": {
      "configuration_entity_id": 99,
      "cascade_delete": true
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `entityId` | string | The entity ID to override (as string key) |
| `plugin` | string | Must be `"cross-entity-sample"` for this plugin |
| `operations` | string[] | Operations to override: `create`, `retrieve`, `update`, `delete`, `list` |
| `params.configuration_entity_id` | number | Entity ID for related Configuration entries |
| `params.cascade_delete` | boolean | Whether to cascade delete related entries |

## Plugin Structure

```
pagoda_cross_entity_sample_plugin/
├── __init__.py          # Package exports
├── apps.py              # Django app configuration
├── plugin.py            # Plugin class with override registration
├── handlers.py          # Override handler implementations (using OverrideContext)
└── relationships.py     # Entity relationship definitions
```

## Handler Implementation

### OverrideContext

All handlers receive an `OverrideContext` object:

```python
@dataclass
class OverrideContext:
    request: Request      # DRF Request object
    user: User            # Authenticated user
    entity: Entity        # Entity instance
    entry: Entry          # Entry instance (for retrieve/update/delete)
    data: dict            # Request data (for create/update)
    params: dict          # Plugin params from configuration
    plugin_id: str        # Plugin ID
    operation: str        # Operation type
```

### Using the @override_operation Decorator

```python
from pagoda_plugin_sdk.override import (
    OverrideContext,
    override_operation,
    success_response,
    error_response,
)

class ServiceHandlers:
    @override_operation("retrieve")
    def handle_retrieve(self, context: OverrideContext) -> Response:
        """Handle entry retrieval with custom enrichment."""
        entry = context.entry
        if not entry:
            return error_response("Entry not found", status_code=404)

        # Use standard serializer for API compatibility
        from entry.api_v2.serializers import EntryRetrieveSerializer
        serializer = EntryRetrieveSerializer(
            entry,
            context={"request": context.request}
        )
        response_data = serializer.data

        # Add plugin-specific fields
        response_data["_plugin_override"] = {
            "active": True,
            "plugin_id": context.plugin_id,
            "message": "Handled by cross-entity-sample plugin",
            "params": context.params,
        }

        return success_response(response_data)
```

### Important: API Compatibility

When implementing `retrieve` handlers, always use the standard `EntryRetrieveSerializer` to ensure the response includes all required fields (`attrs`, `schema`, `permission`, etc.) that the frontend expects:

```python
# Good: Use standard serializer
from entry.api_v2.serializers import EntryRetrieveSerializer
serializer = EntryRetrieveSerializer(entry, context={"request": context.request})
response_data = serializer.data
response_data["_custom_field"] = "value"  # Add custom fields after

# Bad: Manual response construction (may break frontend)
response_data = {
    "id": entry.id,
    "name": entry.name,
    # Missing: attrs, schema.permission, etc.
}
```

### Supported Operations

| Operation | Handler Signature | Description |
|-----------|-------------------|-------------|
| `create` | `handle_create(self, context: OverrideContext)` | Create entry with related entries |
| `retrieve` | `handle_retrieve(self, context: OverrideContext)` | Get entry with enrichment |
| `update` | `handle_update(self, context: OverrideContext)` | Update entry and related entries |
| `delete` | `handle_delete(self, context: OverrideContext)` | Delete with optional cascade |
| `list` | `handle_list(self, context: OverrideContext)` | Custom list with filtering |

### Response Helpers

The SDK provides response helper functions:

```python
from pagoda_plugin_sdk.override import (
    success_response,            # 200 OK with data
    created_response,            # 201 Created
    accepted_response,           # 202 Accepted
    no_content_response,         # 204 No Content
    error_response,              # 400 Bad Request (customizable)
    not_found_response,          # 404 Not Found
    permission_denied_response,  # 403 Forbidden
    validation_error_response,   # 400 with validation errors
)
```

## API Behavior

When this plugin is enabled and configured, the standard Entry API behaves differently for configured entities:

### Retrieve Entry

**Endpoint**: `GET /entry/api/v2/{entry_id}/`

**Response** (with plugin override):
```json
{
  "id": 123,
  "name": "my-service",
  "schema": {
    "id": 42,
    "name": "TestService",
    "is_public": true,
    "permission": 8
  },
  "is_active": true,
  "attrs": [
    {"id": 124, "type": 2, "schema": {"id": 45, "name": "description"}, ...}
  ],
  "is_public": true,
  "permission": 8,
  "_plugin_override": {
    "active": true,
    "plugin_id": "cross-entity-sample",
    "plugin_version": "3.0.0",
    "message": "This response was handled by cross-entity-sample plugin!",
    "params": {
      "configuration_entity_id": 99,
      "cascade_delete": true
    }
  },
  "_retrieved_at": "2026-02-01T12:00:00.000000"
}
```

### Create Entry

**Endpoint**: `POST /entity/api/v2/{entity_id}/entries/`

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
  "message": "Entry 'my-service' creation accepted",
  "entity_id": 42,
  "_plugin_override": {
    "active": true,
    "plugin_id": "cross-entity-sample",
    "message": "Entry created via cross-entity-sample plugin!",
    "configurations_created": 1
  }
}
```

### Delete Entry

**Endpoint**: `DELETE /entry/api/v2/{entry_id}/?cascade=true`

The `cascade=true` query parameter (or `cascade_delete: true` in params) triggers cascade deletion of related entries.

## Testing

Run the plugin tests:

```bash
# Run with Django test runner
ENABLED_PLUGINS=cross-entity-sample \
BACKEND_PLUGIN_ENTITY_OVERRIDES='{"42":{"plugin":"cross-entity-sample","operations":["retrieve"],"params":{}}}' \
python manage.py test airone.plugins.tests.test_override
```

Verify override is working:

```bash
# Get an entry with override configured
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/entry/api/v2/{entry_id}/

# Check for _plugin_override field in response
```

## Migration from Name-Based System

If you were using the legacy name-based override system (`@override_entry_operation`), migrate to the ID-based system:

### Before (Deprecated)
```python
@override_entry_operation(entity="Service", operation="retrieve")
def handle_retrieve(self, request, entry, **kwargs):
    ...
```

### After (Current)
```python
@override_operation("retrieve")
def handle_retrieve(self, context: OverrideContext) -> Response:
    entry = context.entry
    params = context.params  # Get config from BACKEND_PLUGIN_ENTITY_OVERRIDES
    ...
```

Entity binding is now done via configuration:
```bash
export BACKEND_PLUGIN_ENTITY_OVERRIDES='{"42": {"plugin": "cross-entity-sample", "operations": ["retrieve"], "params": {}}}'
```

## Development Notes

- Handlers are registered during plugin initialization via the override registry
- Only one plugin can override a specific entity/operation combination
- Conflict detection prevents accidental override collisions
- The original Entry API behavior is used when no override is registered
- Use standard serializers (`EntryRetrieveSerializer`) to ensure API compatibility with the frontend
