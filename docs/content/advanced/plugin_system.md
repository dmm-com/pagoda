---
title: Plugin System
weight: 0
---

## Overview

Pagoda's plugin system enables extension through completely independent external plugins using a **3-layer architecture**. This system separates plugins from core functionality and provides stable extension points.

### 3-Layer Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Core Layer    │    │   Plugin Layer   │    │Extended App Layer│
│                 │    │                  │    │                  │
│pagoda-plugin-sdk│◄───│  External Plugin │◄───│     Pagoda       │
│                 │    │                  │    │                  │
│ • Interfaces    │    │ • Plugin Logic   │    │ • Bridge Impl.   │
│ • Base Classes  │    │ • API Endpoints  │    │ • URL Integration│
│ • Common Hooks  │    │ • Hook Handlers  │    │ • Django Setup   │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

### Core Capabilities

Plugins enable the following extensions:

- **API v2 Endpoints**: RESTful API extensions
- **Hook-Based Extensions**: Intervention and extension of core operations
- **Custom Business Logic**: Unique processing and data manipulation
- **Authentication & Authorization Integration**: Utilizing Pagoda's permission system

## Architecture Deep Dive

### Layer 1: pagoda-plugin-sdk (Core Framework)

Foundation layer provided as an independent PyPI package:

```python
# pagoda_plugin_sdk provides:
from pagoda_plugin_sdk import Plugin, PluginAPIViewMixin
from pagoda_plugin_sdk.models import Entity, Entry, User
from pagoda_plugin_sdk.protocols import EntityProtocol, EntryProtocol, UserProtocol
```

**Features:**
- Distributable via PyPI
- Depends on Django/DRF but not on Pagoda application
- Type-safe Protocol definitions for host models
- Model injection mechanism for accessing host application data

### Layer 2: External Plugin (Independent Extension)

Completely independent plugin that depends only on pagoda-plugin-sdk:

```python
from pagoda_plugin_sdk import Plugin

class MyPlugin(Plugin):
    id = "my-plugin"
    name = "My Plugin"
    version = "1.0.0"
    django_apps = ["my_plugin"]
    api_v2_patterns = "my_plugin.api_v2.urls"
    hooks = {
        "entry.after_create": "my_plugin.hooks.after_create",
    }
```

### Layer 3: Pagoda Application (Host Application)

Injects concrete model implementations into the plugin SDK:

```python
# Pagoda injects actual models into the plugin SDK
from airone.plugins.integration import plugin_integration

# During initialization, real models are injected
plugin_integration.initialize()  # Injects Entity, Entry, User, etc.

# Plugins can then access models through the SDK
from pagoda_plugin_sdk.models import Entity, Entry, User
```

## Model Access through Protocols

### Overview

Plugins access host application models through a safe injection mechanism. The SDK provides Protocol-based type definitions that ensure type safety without creating implementation dependencies.

### Protocol Definitions

The SDK defines type-safe protocols for all major models:

```python
from pagoda_plugin_sdk.protocols import (
    EntityProtocol,
    EntryProtocol,
    UserProtocol,
    EntityAttrProtocol,
    AttributeProtocol,
    AttributeValueProtocol,
)
```

**Available Protocols:**

- `EntityProtocol` - Schema definition (Entity model)
- `EntryProtocol` - Data entry (Entry model)
- `UserProtocol` - User account
- `EntityAttrProtocol` - Entity attribute definition
- `AttributeProtocol` - Entry attribute
- `AttributeValueProtocol` - Attribute value

### Model Injection Mechanism

Models are injected by the host application during initialization:

```python
# In Pagoda application startup
from airone.plugins.integration import plugin_integration

# Initialize plugin system and inject models
plugin_integration.initialize()  # Automatically injects real models
```

The injection process:

1. Pagoda application starts
2. Plugin system initializes
3. Real Django models are injected into `pagoda_plugin_sdk.models`
4. Plugins can safely access models through the SDK

### Accessing Models in Plugins

**Basic Model Access:**

```python
from pagoda_plugin_sdk.models import Entity, Entry, User

def my_plugin_view(request):
    # Type-safe Entity access
    entities = Entity.objects.filter(is_active=True)

    # Type-safe Entry access
    entries = Entry.objects.filter(schema__name="MyEntity")

    # Access with relationships
    for entry in entries:
        entity_name = entry.schema.name  # Type-safe attribute access
        creator = entry.created_user.username
```

**Checking Model Availability:**

```python
from pagoda_plugin_sdk import models

# Check if models are initialized
if models.is_initialized():
    from pagoda_plugin_sdk.models import Entity
    entities = Entity.objects.all()
else:
    # Handle case where plugin system is not initialized
    raise RuntimeError("Plugin system not initialized")

# Get list of available models
available = models.get_available_models()  # ['Entity', 'Entry', 'User', ...]
```

**Model CRUD Operations:**

```python
from pagoda_plugin_sdk.models import Entity, Entry

# Create
entity = Entity.objects.create(
    name="New Entity",
    note="Created by plugin",
    created_user=request.user
)

# Read
entity = Entity.objects.get(id=123)
entries = Entry.objects.filter(schema=entity, is_active=True)

# Update
entity.note = "Updated by plugin"
entity.save()

# Delete (soft delete)
entity.is_active = False
entity.save()
```

**Using Entry-Specific Methods:**

```python
from pagoda_plugin_sdk.models import Entry

# Get entry with attributes
entry = Entry.objects.get(id=456)

# Use Entry's custom methods (defined in EntryProtocol)
attrs = entry.get_attrs()  # Get all attributes as dict
entry.set_attrs(user=request.user, name="value", age=30)

# Permission checking
if entry.may_permitted(request.user, some_permission):
    # Perform operation
    pass
```

### Type Safety Benefits

Using Protocols provides several advantages:

1. **IDE Autocomplete**: Full IntelliSense support in modern IDEs
2. **Type Checking**: Static type checkers (mypy) can verify correctness
3. **No Import Errors**: No circular dependency issues
4. **Documentation**: Protocol definitions serve as API documentation

**Example with Type Hints:**

```python
from typing import List
from pagoda_plugin_sdk.models import Entity, Entry
from pagoda_plugin_sdk.protocols import EntityProtocol, EntryProtocol

def get_entries_for_entity(entity: EntityProtocol) -> List[EntryProtocol]:
    """Get all active entries for a given entity

    Args:
        entity: Entity to query entries for

    Returns:
        List of active Entry instances
    """
    return Entry.objects.filter(schema=entity, is_active=True)
```

### Error Handling

Always handle cases where models might not be available:

```python
from pagoda_plugin_sdk.models import Entity
from rest_framework.response import Response
from rest_framework import status

def my_view(request):
    try:
        if Entity is None:
            return Response(
                {"error": "Entity model not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        entities = Entity.objects.filter(is_active=True)
        # Process entities...

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

## Getting Started

### Prerequisites

```bash
# Install pagoda-plugin-sdk (for plugin development)
pip install pagoda-plugin-sdk

# Or development version (for local development)
cd plugin/sdk/
pip install -e .
```

### Plugin Enablement

The plugin system loads only manually specified plugins:

```bash
# Enable a single plugin
export ENABLED_PLUGINS=my-plugin

# Enable multiple plugins (comma-separated)
export ENABLED_PLUGINS=my-plugin,another-plugin
```

### Starting Server with Plugins

```bash
# Start with uv environment (recommended)
ENABLED_PLUGINS=my-plugin uv run python manage.py runserver

# Start with pip environment
ENABLED_PLUGINS=my-plugin python manage.py runserver

# Start after setting environment variable
export ENABLED_PLUGINS=my-plugin
python manage.py runserver
```

**Important**: Only plugins explicitly specified in `ENABLED_PLUGINS` are loaded. If none are specified, the plugin system is disabled.

## Verifying Plugin Operation

### Startup Logs

Logs when the plugin system is operating normally:

```
[INFO] Initializing plugin system...
[INFO] Starting plugin discovery...
[INFO] Loaded external plugin: hello-world
[INFO] Registered plugin: hello-world-plugin v1.0.0
[INFO] Connected Entry model signals to hook system
[INFO] Pagoda bridge manager initialized successfully
[INFO] Registered 2 hooks for plugin hello-world-plugin
[INFO] Plugin discovery completed. Found 1 plugins.
[INFO] Plugin system initialized successfully
```

### Testing Plugin APIs

Sample plugin API endpoints:

```bash
# Authentication-free test endpoint (for verification)
curl http://localhost:8000/api/v2/plugins/hello-world-plugin/test/

# Authentication-required endpoints
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v2/plugins/hello-world-plugin/hello/

curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v2/plugins/hello-world-plugin/greet/John/

curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v2/plugins/hello-world-plugin/status/
```

### Expected Response

```json
{
  "message": "External Hello World Plugin is working via pagoda-core!",
  "plugin": {
    "id": "hello-world-plugin",
    "name": "Hello World Plugin",
    "version": "1.0.0",
    "type": "external",
    "core": "pagoda-core"
  },
  "test": "no-auth",
  "user": {
    "username": "anonymous",
    "is_authenticated": false
  },
  "pagoda_core_version": "1.0.0",
  "timestamp": "2025-09-15T02:09:45.658756"
}
```

## Plugin Development

### Development Workflow

#### 1. Create Plugin Structure

```bash
mkdir my-pagoda-plugin
cd my-pagoda-plugin

# Copy from example
cp -r ../plugin/examples/pagoda-hello-world-plugin/* .
```

#### 2. Plugin Package Structure

```
my-pagoda-plugin/
├── pyproject.toml              # Modern package configuration
├── Makefile                    # Development commands
├── README.md                   # Plugin documentation
└── my_plugin_package/          # Main package
    ├── __init__.py
    ├── plugin.py               # Plugin class definition
    ├── hooks.py                # Hook handlers
    ├── apps.py                 # Django app configuration
    └── api_v2/                 # API endpoints
        ├── __init__.py
        ├── urls.py             # URL configuration
        └── views.py            # API view implementation
```

#### 3. pyproject.toml Configuration

```toml
[project]
name = "my-pagoda-plugin"
version = "1.0.0"
description = "My Pagoda Plugin"
dependencies = [
    "pagoda-plugin-sdk>=1.0.0",  # Core dependency only
    "Django>=3.2",
    "djangorestframework>=3.12",
]
requires-python = ">=3.8"

[project.entry-points."pagoda.plugins"]
my-plugin = "my_plugin_package.plugin:MyPlugin"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### 4. Plugin Class Implementation

```python
from pagoda_plugin_sdk import Plugin

class MyPlugin(Plugin):
    # Required metadata
    id = "my-plugin"
    name = "My Plugin"
    version = "1.0.0"
    description = "My custom Pagoda plugin"
    author = "Your Name"

    # Django integration
    django_apps = ["my_plugin_package"]
    api_v2_patterns = "my_plugin_package.api_v2.urls"

    # Hook registrations
    hooks = {
        "entry.after_create": "my_plugin_package.hooks.after_create",
        "entry.before_update": "my_plugin_package.hooks.before_update",
    }

```

#### 5. API View Implementation

```python
from datetime import datetime
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from pagoda_plugin_sdk import PluginAPIViewMixin

class MyAPIView(PluginAPIViewMixin):
    permission_classes = [AllowAny]  # For testing

    def get(self, request):
        return Response({
            "message": "Hello from my plugin!",
            "plugin": {
                "id": self.plugin_id,
                "name": "My Plugin",
                "version": "1.0.0"
            },
            "timestamp": datetime.now().isoformat()
        })
```

### Development Commands

Development Make commands in plugin directory:

```bash
make help              # Show available commands
make dev-setup         # Set up development environment
make install-dev       # Install in development mode
make test              # Run plugin tests
make test-integration  # Run Pagoda integration tests
make build             # Build distribution packages
make publish-test      # Publish to TestPyPI
make publish           # Publish to PyPI
```

### Distribution Strategies

#### 1. PyPI Distribution

```bash
# Build and publish
make build
make publish

# Users install the plugin
pip install my-pagoda-plugin
```

#### 2. GitHub Releases

```bash
# Create tag and release
git tag v1.0.0
git push origin v1.0.0

# Users install from GitHub release
pip install https://github.com/user/my-plugin/releases/download/v1.0.0/my_plugin-1.0.0-py3-none-any.whl
```

#### 3. Development Installation

```bash
# Development editable install
pip install -e .

# Development install in Poetry environment
pip install -e .
```

## Sample Plugin Reference

### Available Example

A complete sample plugin is available at `plugin/examples/pagoda-hello-world-plugin/`:

**Endpoints:**
- `GET /api/v2/plugins/hello-world-plugin/test/` - Authentication-free test
- `GET /api/v2/plugins/hello-world-plugin/hello/` - Basic Hello API
- `POST /api/v2/plugins/hello-world-plugin/hello/` - Custom message API
- `GET /api/v2/plugins/hello-world-plugin/greet/<name>/` - Personalized greeting
- `GET /api/v2/plugins/hello-world-plugin/status/` - Plugin status
- `GET /api/v2/plugins/hello-world-plugin/entities/` - List all entities (demonstrates model access)
- `GET /api/v2/plugins/hello-world-plugin/entities/<id>/` - Get entity details
- `GET /api/v2/plugins/hello-world-plugin/entries/` - List entries with filtering
- `GET /api/v2/plugins/hello-world-plugin/entries/<id>/` - Get entry with attributes

**Model Access Examples:**

The sample plugin demonstrates how to access host application models:

```python
from pagoda_plugin_sdk import PluginAPIViewMixin
from pagoda_plugin_sdk.models import Entity, Entry

class EntityListView(PluginAPIViewMixin):
    def get(self, request):
        # Type-safe entity access
        entities = Entity.objects.filter(is_active=True)

        entity_list = [
            {
                "id": entity.id,
                "name": entity.name,
                "note": entity.note,
            }
            for entity in entities
        ]

        return Response({"entities": entity_list})
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLED_PLUGINS` | `[]` | List of plugins to enable (comma-separated) |

### Django Settings Integration

```python
# airone/settings_common.py
ENABLED_PLUGINS = env.list("ENABLED_PLUGINS", default=[])

# Plugin system is automatically enabled if any plugins are specified
PLUGINS_ENABLED = bool(ENABLED_PLUGINS)

# Plugin apps are dynamically added to INSTALLED_APPS
if PLUGINS_ENABLED:
    INSTALLED_APPS.extend(plugin_integration.get_installed_apps())
```

### Manual Plugin Control

The plugin system adopts explicit control:

- **No Automatic Discovery**: Does not automatically load available plugins
- **Explicit Specification**: Only loads plugins specified in `ENABLED_PLUGINS`
- **Security**: Prevents loading of unintended plugins
- **Controllability**: Easy plugin control in development and production environments

## Troubleshooting

### Common Issues and Solutions

#### 1. 404 Error on Plugin Endpoints

**Symptoms**: `curl http://localhost:8000/api/v2/plugins/my-plugin/test/` returns 404

**Causes and Solutions**:

```bash
# Cause 1: Plugin not specified
❌ python manage.py runserver
✅ ENABLED_PLUGINS=my-plugin python manage.py runserver

# Cause 2: Plugin not installed
❌ pip install -e plugin_examples/my-plugin/
✅ cd plugin_examples/my-plugin/ && pip install -e .

# Cause 3: Incorrect Entry points path
❌ 'my-plugin = my_plugin:MyPlugin'
✅ 'my-plugin = my_plugin.plugin:MyPlugin'

# Cause 4: Incorrect Entry points group name
❌ [project.entry-points."airone.plugins"]
✅ [project.entry-points."pagoda.plugins"]
```

#### 2. Plugin Discovery Failures

**Log Example**:
```
[ERROR] Failed to load external plugin my-plugin: No module named 'my_plugin'
[INFO] Plugin discovery completed. Found 0 plugins.
```

**Resolution Steps**:

1. **Check Entry points**:
```bash
python -c "
import pkg_resources
for ep in pkg_resources.iter_entry_points('pagoda.plugins'):
    print(f'{ep.name} -> {ep.module_name}:{ep.attrs[0]}')
    try:
        plugin_class = ep.load()
        print(f'✓ Load successful: {plugin_class}')
    except Exception as e:
        print(f'✗ Load failed: {e}')
"
```

2. **Reinstall Plugin**:
```bash
cd my-plugin/
pip uninstall -y my-plugin
rm -rf build/ dist/ *.egg-info/
pip install -e .
```

3. **Check Path and Module**:
```bash
python -c "
import sys
sys.path.insert(0, 'plugin_examples/my-plugin')
from my_plugin.plugin import MyPlugin
print(f'✓ Direct import works: {MyPlugin().name}')
"
```

#### 3. Hook Execution Errors

**Log Example**:
```
[ERROR] Hook entry.after_create failed: after_entry_create() missing required arguments
```

**Solution**: Implement correct hook handler signature
```python
# ❌ Wrong
def after_entry_create():
    pass

# ✅ Correct
def after_entry_create(sender, instance, created, **kwargs):
    # sender is Django model class
    # instance is the created Entry instance
    # created is a boolean flag for new creation
    print(f"New entry created: {instance.name}")
```

#### 4. Plugin Development Environment Issues

**Development with Poetry**:
```bash
# If pagoda-core is not found
cd pagoda-core/
make install-dev

# Install plugin for development
cd ../plugin_examples/my-plugin/
pip install -e .

# Run integration tests
make test-integration
```

### Debug Commands

```bash
# Check plugin status
ENABLED_PLUGINS=hello-world python manage.py shell -c "
from airone.plugins.integration import plugin_integration
plugin_integration.initialize()
print(f'Plugins: {plugin_integration.get_enabled_plugin_count()}')
for plugin in plugin_integration.get_enabled_plugins():
    print(f'  - {plugin.name} ({plugin.id}) v{plugin.version}')
"

# Test URL resolution
python -c "
import django
django.setup()
from django.urls import get_resolver
resolver = get_resolver()
match = resolver.resolve('/api/v2/plugins/hello-world-plugin/test/')
print(f'✓ URL resolved: {match.func}')
"

# Get hook statistics
python -c "
from airone.plugins.bridge_manager import bridge_manager
bridge_manager.initialize()
stats = bridge_manager.hooks.get_hook_statistics()
print(f'Total hooks: {stats[\"total_hooks\"]}')
print(f'Registered hooks: {stats[\"registered_hooks\"]}')
"
```

## Architecture Details

### Plugin Discovery Process

```
1. External Plugin Discovery (Entry Points)
   ├─ pkg_resources.iter_entry_points('pagoda.plugins')
   ├─ Load plugin class from entry point
   └─ Register with plugin_registry

2. Example Plugin Discovery (Directory Scan)
   ├─ Scan plugin_examples/ directory
   ├─ Import plugin.py from each plugin directory
   └─ Register discovered plugin classes

3. Plugin Integration
   ├─ Django Apps → INSTALLED_APPS integration
   ├─ URL Patterns → api_v2/urls.py integration
   ├─ Hook Registration → bridge_manager.hooks
   └─ Bridge System Initialization
```

### Hook System Architecture

```python
# Core Layer: 27 common hooks + Pagoda specific hooks (42 total)
COMMON_HOOKS = [
    "entity.before_create", "entity.after_create",
    "entry.before_create", "entry.after_create",
    # ... 23 more
]

# Pagoda Layer: Concrete implementation
class PagodaHookBridge(HookInterface):
    def __init__(self):
        self._hooks = {}
        self._available_hooks = COMMON_HOOKS + PAGODA_SPECIFIC_HOOKS

    def execute_hook(self, hook_name, *args, **kwargs):
        # Execute all registered callbacks with error handling
```

### Model Injection Implementation

```python
# Host application injects models during initialization
# airone/plugins/integration.py
def _inject_models(self):
    import pagoda_plugin_sdk.models as sdk_models
    from entity.models import Entity, EntityAttr
    from entry.models import Entry, Attribute, AttributeValue
    from user.models import User

    # Inject real models into SDK
    sdk_models.Entity = Entity
    sdk_models.Entry = Entry
    sdk_models.User = User
    # ... other models

# Plugin accesses models safely
from pagoda_plugin_sdk.models import Entity
entities = Entity.objects.all()  # → Pagoda Entity instances
```

## Best Practices

### 1. Plugin Development

- **Version Pinning**: Ensure compatibility with `pagoda-core>=1.0.0,<2.0.0`
- **Testing**: Implement both unit tests and Pagoda integration tests
- **Documentation**: Include README and API specifications
- **Error Handling**: Implement proper exception handling in hooks and APIs
- **Security**: Implement proper authentication and authorization

### 2. Distribution

- **Semantic Versioning**: Use appropriate `major.minor.patch` versioning
- **Changelog**: Maintain release notes and change history
- **Compatibility**: Clearly specify supported Pagoda/pagoda-plugin-sdk versions
- **Dependencies**: Keep dependencies to a minimum

### 3. Production Deployment

- **Environment Isolation**: Isolate virtual environments per plugin
- **Monitoring**: Monitor plugin error logs
- **Rollback Strategy**: Prepare procedures for disabling plugins
- **Performance**: Evaluate performance impact of hook processing

This 3-layer architecture realizes a plugin system completely independent from Pagoda. Plugin developers can create safe and reusable plugins depending only on `pagoda-plugin-sdk`.