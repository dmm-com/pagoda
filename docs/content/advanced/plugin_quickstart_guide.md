---
title: Plugin Development Quick Start Guide
weight: 2
---

## Plugin Development in 5 Minutes

This guide provides the shortest steps to create and verify your first plugin using the Pagoda plugin system.

### Step 1: Environment Setup (2 minutes)

#### 1.1 Setting up pagoda-plugin-sdk in Pagoda Environment

```bash
cd /path/to/pagoda

# Install development version of pagoda-plugin-sdk
cd plugin/sdk/
make install-dev

# Verify installation
python -c "import pagoda_plugin_sdk; print('✓ pagoda-plugin-sdk ready')"
```

#### 1.2 Verify Operation with Sample Plugin

```bash
# Enable plugin and start server
ENABLED_PLUGINS=hello-world python manage.py runserver 8080 &

# Verify operation in separate terminal
curl http://localhost:8080/api/v2/plugins/hello-world-plugin/test/
```

**Expected Response:**
```json
{
  "message": "External Hello World Plugin is working via pagoda-plugin-sdk!",
  "plugin": {
    "id": "hello-world-plugin",
    "name": "Hello World Plugin",
    "version": "1.0.0",
    "type": "external",
    "core": "pagoda-plugin-sdk"
  }
}
```

✅ **If everything works correctly up to this point, environment setup is complete!**

### Step 2: Creating Your First Plugin (3 minutes)

#### 2.1 Create Plugin Project

```bash
# Create working directory
mkdir my-first-plugin
cd my-first-plugin

# Copy from sample to start
cp -r ../plugin/examples/pagoda-hello-world-plugin/* .

# Customize plugin name
sed -i 's/hello-world-plugin/my-first-plugin/g' pyproject.toml
sed -i 's/pagoda_hello_world_plugin/my_first_plugin/g' pyproject.toml
```

#### 2.2 Rename Plugin Structure

```bash
# Change directory and file names
mv pagoda_hello_world_plugin my_first_plugin
```

#### 2.3 Customize Plugin Class

```python
# my_first_plugin/plugin.py
from pagoda_plugin_sdk import Plugin
from pagoda_plugin_sdk.decorators import entry_hook
import logging

logger = logging.getLogger(__name__)

class MyFirstPlugin(Plugin):
    id = "my-first-plugin"
    name = "My First Plugin"
    version = "1.0.0"
    description = "My very first Pagoda plugin"
    author = "Your Name"

    django_apps = ["my_first_plugin"]
    api_v2_patterns = "my_first_plugin.api_v2.urls"

    @entry_hook("after_create")
    def log_entry_create(self, entity_name, user, entry, **kwargs):
        """Hook executed after Entry creation"""
        logger.info(f"New entry created: {entry.name} in entity {entity_name} by {user.username}")
        print(f"My First Plugin detected new entry: {entry.name}")
```

#### 2.4 Customize API Endpoints

```python
# my_first_plugin/api_v2/views.py
from datetime import datetime
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from pagoda_plugin_sdk import PluginAPIViewMixin

class MyFirstView(PluginAPIViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "message": "Hello from My First Plugin!",
            "plugin": {
                "id": "my-first-plugin",
                "name": "My First Plugin",
                "version": "1.0.0"
            },
            "custom_data": {
                "greeting": "Welcome to plugin development!",
                "tips": "Check the documentation for advanced features"
            },
            "timestamp": datetime.now().isoformat()
        })
```

```python
# my_first_plugin/api_v2/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("test/", views.MyFirstView.as_view(), name="test"),
    path("hello/", views.MyFirstView.as_view(), name="hello"),
]
```

### Step 3: Plugin Testing & Installation

#### 3.1 Plugin Installation

```bash
# Development installation
pip install -e .

# Verify installation
python -c "
from my_first_plugin.plugin import MyFirstPlugin
plugin = MyFirstPlugin()
print(f'✓ Plugin ready: {plugin.name} v{plugin.version}')
"
```

#### 3.2 Testing with Pagoda

```bash
# Restart Pagoda server (to recognize new plugin)
pkill -f "manage.py runserver"
ENABLED_PLUGINS=my-first-plugin python manage.py runserver 8080 &

# Test plugin endpoint
curl http://localhost:8080/api/v2/plugins/my-first-plugin/test/
```

**Logs on Success:**
```
[INFO] Registered plugin: my-first-plugin v1.0.0
[INFO] Registered 1 hooks for plugin my-first-plugin
[INFO] Plugin discovery completed. Found 2 plugins.
```

## Practical Troubleshooting

### Issue 1: 404 Error - Plugin Not Found

**Symptoms:**
```bash
curl http://localhost:8080/api/v2/plugins/my-plugin/test/
# 404 Not Found
```

**Diagnostic Steps:**

```bash
# 1. Check if plugin system is enabled
python manage.py shell -c "
from django.conf import settings
print('Plugin system enabled:', bool(getattr(settings, 'ENABLED_PLUGINS', [])))
"

# 2. Check plugin registration status
ENABLED_PLUGINS=my-first-plugin python manage.py shell -c "
from airone.plugins.integration import plugin_integration
plugin_integration.initialize()
plugins = plugin_integration.get_enabled_plugins()
for p in plugins:
    print(f'Plugin: {p.id} - {p.name}')
"

# 3. Check entry points
python -c "
import pkg_resources
entries = list(pkg_resources.iter_entry_points('pagoda.plugins'))
print(f'Found {len(entries)} entry points:')
for ep in entries:
    print(f'  {ep.name} -> {ep.module_name}')
"
```

**Solutions:**
```bash
# Most common cause: Missing environment variable
❌ python manage.py runserver
✅ ENABLED_PLUGINS=my-first-plugin python manage.py runserver

# Second most common cause: Plugin not installed
pip install -e .

# Entry points path error
# Check pyproject.toml and fix the path specification
```

### Issue 2: Import Error - Module Not Found

**Symptoms:**
```
[ERROR] Failed to load external plugin: No module named 'my_plugin'
```

**Diagnostic & Resolution Steps:**

```bash
# 1. Check if plugin is installed correctly
pip list | grep my-plugin

# 2. Check module structure
tree my-plugin/
# Expected structure:
# my-plugin/
# ├── setup.py
# └── my_plugin/
#     ├── __init__.py
#     └── plugin.py

# 3. Check and fix entry points path
# In pyproject.toml:
[project.entry-points."pagoda.plugins"]
my-plugin = "my_plugin.plugin:MyPlugin"  # ← Exact path

# 4. Reinstall
pip uninstall -y my-plugin
rm -rf build/ dist/ *.egg-info/
pip install -e .
```

### Issue 3: Hook Execution Error

**Symptoms:**
```
[ERROR] Hook entry.after_create failed: missing required arguments
```

**Solutions:**
```python
# ❌ Incorrect signature (missing self and entity_name)
@entry_hook("after_create")
def log_entry_create(user, entry):
    pass

# ❌ Missing decorator
def log_entry_create(self, entity_name, user, entry, **kwargs):
    pass

# ✅ Correct signature with decorator
@entry_hook("after_create")
def log_entry_create(self, entity_name, user, entry, **kwargs):
    """
    entity_name: Name of the entity
    user: User who created the entry
    entry: The created Entry instance
    **kwargs: Additional context
    """
    logger.info(f"New entry: {entry.name} in entity {entity_name}")
```

## Accessing Host Application Models

### Overview

Plugins can access Pagoda's models (Entity, Entry, User, etc.) through the plugin SDK's model injection mechanism. This provides type-safe access to host application data.

### Basic Model Import

```python
# Import models from the plugin SDK
from pagoda_plugin_sdk.models import Entity, Entry, User

class MyPluginView(PluginAPIViewMixin):
    def get(self, request):
        # Access models directly
        entities = Entity.objects.filter(is_active=True)
        entries = Entry.objects.filter(schema__name="MyEntity")
```

### Entity Access Examples

**List All Entities:**

```python
from pagoda_plugin_sdk.models import Entity
from rest_framework.response import Response

class EntityListView(PluginAPIViewMixin):
    def get(self, request):
        # Get all active entities
        entities = Entity.objects.filter(is_active=True)

        # Convert to response format
        entity_list = []
        for entity in entities:
            entity_list.append({
                "id": entity.id,
                "name": entity.name,
                "note": entity.note,
                "created_user": entity.created_user.username if entity.created_user else None,
            })

        return Response({"entities": entity_list, "count": len(entity_list)})
```

**Get Entity Details:**

```python
from pagoda_plugin_sdk.models import Entity

class EntityDetailView(PluginAPIViewMixin):
    def get(self, request, entity_id):
        try:
            entity = Entity.objects.get(id=entity_id, is_active=True)

            return Response({
                "id": entity.id,
                "name": entity.name,
                "note": entity.note,
                "is_active": entity.is_active,
                "created_time": entity.created_time.isoformat() if entity.created_time else None,
            })
        except Entity.DoesNotExist:
            return Response(
                {"error": f"Entity {entity_id} not found"},
                status=404
            )
```

### Entry Access Examples

**List Entries with Filtering:**

```python
from pagoda_plugin_sdk.models import Entry

class EntryListView(PluginAPIViewMixin):
    def get(self, request):
        # Get query parameters
        entity_id = request.GET.get("entity_id")
        limit = request.GET.get("limit", 100)

        # Build query
        queryset = Entry.objects.filter(is_active=True)

        if entity_id:
            queryset = queryset.filter(schema_id=entity_id)

        # Limit results
        entries = queryset[:int(limit)]

        # Format response
        entry_list = []
        for entry in entries:
            entry_list.append({
                "id": entry.id,
                "name": entry.name,
                "entity": {
                    "id": entry.schema.id,
                    "name": entry.schema.name,
                } if entry.schema else None,
                "created_user": entry.created_user.username if entry.created_user else None,
            })

        return Response({
            "entries": entry_list,
            "count": len(entry_list),
            "filters": {"entity_id": entity_id, "limit": limit}
        })
```

**Get Entry with Attributes:**

```python
from pagoda_plugin_sdk.models import Entry

class EntryDetailView(PluginAPIViewMixin):
    def get(self, request, entry_id):
        try:
            entry = Entry.objects.get(id=entry_id, is_active=True)

            # Use Entry's custom method to get attributes
            attrs = entry.get_attrs()

            return Response({
                "id": entry.id,
                "name": entry.name,
                "entity": {
                    "id": entry.schema.id,
                    "name": entry.schema.name,
                },
                "attributes": attrs,  # All entry attributes
                "created_time": entry.created_time.isoformat() if entry.created_time else None,
            })
        except Entry.DoesNotExist:
            return Response(
                {"error": f"Entry {entry_id} not found"},
                status=404
            )
```

### Working with Relationships

```python
from pagoda_plugin_sdk.models import Entity, Entry

class EntityEntriesView(PluginAPIViewMixin):
    def get(self, request, entity_id):
        """Get an entity and all its entries"""
        try:
            # Get entity
            entity = Entity.objects.get(id=entity_id, is_active=True)

            # Get all entries for this entity
            entries = Entry.objects.filter(
                schema=entity,
                is_active=True
            ).select_related('created_user')

            # Format response
            return Response({
                "entity": {
                    "id": entity.id,
                    "name": entity.name,
                },
                "entries": [
                    {
                        "id": e.id,
                        "name": e.name,
                        "created_user": e.created_user.username,
                    }
                    for e in entries
                ],
                "total_entries": entries.count()
            })
        except Entity.DoesNotExist:
            return Response({"error": "Entity not found"}, status=404)
```

### Model Availability Check

Always check if models are available before using them:

```python
from pagoda_plugin_sdk.models import Entity
from pagoda_plugin_sdk import models

class SafeModelView(PluginAPIViewMixin):
    def get(self, request):
        # Check if plugin system is initialized
        if not models.is_initialized():
            return Response(
                {"error": "Plugin system not initialized"},
                status=503
            )

        # Check specific model
        if Entity is None:
            return Response(
                {"error": "Entity model not available"},
                status=503
            )

        # Safe to use models
        entities = Entity.objects.all()
        return Response({"count": entities.count()})
```

### Type-Safe Model Usage

Use Protocol types for better type safety:

```python
from typing import List
from pagoda_plugin_sdk.models import Entity, Entry
from pagoda_plugin_sdk.protocols import EntityProtocol, EntryProtocol

def process_entity(entity: EntityProtocol) -> dict:
    """Process entity with type safety

    Args:
        entity: Entity instance (type-safe)

    Returns:
        Processed entity data
    """
    return {
        "id": entity.id,
        "name": entity.name,
        "note": entity.note,
    }

def get_entity_entries(entity: EntityProtocol) -> List[EntryProtocol]:
    """Get entries for entity with type hints

    Args:
        entity: Entity to get entries for

    Returns:
        List of Entry instances
    """
    return Entry.objects.filter(schema=entity, is_active=True)
```

### Error Handling Best Practices

```python
from pagoda_plugin_sdk.models import Entity, Entry
from rest_framework.response import Response
from rest_framework import status

class RobustModelView(PluginAPIViewMixin):
    def get(self, request, entity_id):
        try:
            # Model availability check
            if Entity is None or Entry is None:
                return Response(
                    {"error": "Models not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Get entity
            entity = Entity.objects.get(id=entity_id, is_active=True)

            # Get entries
            entries = Entry.objects.filter(schema=entity, is_active=True)

            return Response({
                "entity": {"id": entity.id, "name": entity.name},
                "entry_count": entries.count()
            })

        except Entity.DoesNotExist:
            return Response(
                {"error": f"Entity {entity_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "Internal error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

## Advanced Development Techniques

### Inter-Plugin Communication

```python
# Plugin A: Data provider
class PluginA(Plugin):
    def get_shared_data(self):
        return {"key": "value"}

# Plugin B: Data consumer
class PluginB(Plugin):
    def use_shared_data(self):
        from airone.plugins.registry import plugin_registry
        plugin_a = plugin_registry.get_plugin("plugin-a")
        if plugin_a:
            data = plugin_a.get_shared_data()
            return data
```

### Data Access Using Model Injection

```python
# Access Pagoda data from plugin
from pagoda_plugin_sdk import PluginAPIViewMixin
from pagoda_plugin_sdk.models import Entity, Entry

class DataAccessView(PluginAPIViewMixin):
    def get(self, request, entity_id):
        # Type-safe model access
        try:
            if Entity is None:
                return Response(
                    {"error": "Entity model not available"},
                    status=503
                )

            entity = Entity.objects.get(id=entity_id, is_active=True)
            entries = Entry.objects.filter(schema=entity, is_active=True)

            return Response({
                "entity": {
                    "id": entity.id,
                    "name": entity.name,
                },
                "entry_count": entries.count()
            })
        except Entity.DoesNotExist:
            return Response({"error": "Entity not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
```

### Conditional Hook Execution

```python
@entry_hook("after_create")
def conditional_hook(self, entity_name, user, entry, **kwargs):
    # Execute only under specific conditions
    if entry.name.startswith("special_"):
        # Special processing
        logger.info(f"Special entry detected: {entry.name}")

        # Example of external API call
        import requests
        try:
            response = requests.post("https://api.example.com/notify", {
                "entry_name": entry.name,
                "entity_name": entity_name,
                "plugin": "my-first-plugin"
            }, timeout=5)
            logger.info(f"External API notified: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to notify external API: {e}")
```

## Performance Optimization

### Asynchronous Hook Execution

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

@entry_hook("after_create")
def async_hook_handler(self, entity_name, user, entry, **kwargs):
    """Execute heavy processing asynchronously"""
    def heavy_processing():
        # Heavy processing (external API, file processing, etc.)
        import time
        time.sleep(2)  # Example: Simulate heavy processing
        logger.info(f"Heavy processing completed for {entry.name}")

    # Execute in background
    executor = ThreadPoolExecutor(max_workers=2)
    executor.submit(heavy_processing)
```

### Conditional Hook Branching

```python
@entry_hook("after_create")
def optimized_hook(self, entity_name, user, entry, **kwargs):
    # Skip unnecessary processing
    if not self.should_process(entry):
        return

    # Execute heavy processing only when necessary
    if entry.name.endswith("_important"):
        self.heavy_processing(entry)
    else:
        self.light_processing(entry)

def should_process(self, entry):
    # Determine if processing is necessary
    return hasattr(entry, 'special_flag') and entry.special_flag
```

## Production Distribution Preparation

### PyPI Distribution Configuration

```toml
# pyproject.toml - Production version
[project]
name = "my-pagoda-plugin"
version = "1.0.0"
authors = [
    {name = "Your Name", email = "you@example.com"},
]
description = "A powerful Pagoda plugin"
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Framework :: Django",
]
dependencies = [
    "pagoda-plugin-sdk>=1.0.0,<2.0.0",
    "Django>=3.2",
    "djangorestframework>=3.12",
]

[project.urls]
Homepage = "https://github.com/youruser/my-pagoda-plugin"

[project.entry-points."pagoda.plugins"]
my-plugin = "my_plugin.plugin:MyPlugin"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Test Plugin

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", 3.11]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install pagoda-plugin-sdk
        pip install -e .
        pip install pytest

    - name: Run tests
      run: |
        pytest tests/

    - name: Test plugin loading
      run: |
        python -c "from my_plugin.plugin import MyPlugin; print('✓ Plugin loads successfully')"
```

By following this quick start guide, even beginners can start plugin development in 5 minutes and gain practical problem-solving skills. For more detailed information, refer to the main Plugin System documentation and architecture diagrams.