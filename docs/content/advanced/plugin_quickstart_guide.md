---
title: Plugin Development Quick Start Guide
weight: 2
---

## Plugin Development in 5 Minutes

This guide provides the shortest steps to create and verify your first plugin using the Pagoda plugin system.

### Step 1: Environment Setup (2 minutes)

#### 1.1 Install pagoda-plugin-sdk

Install the plugin SDK from the Git repository:

**Option A: From Git repository (recommended)**
```bash
# Using pip
pip install git+https://github.com/dmm-com/pagoda.git#subdirectory=plugin/sdk

# Or using uv (faster)
uv pip install git+https://github.com/dmm-com/pagoda.git#subdirectory=plugin/sdk

# Verify installation
python -c "import pagoda_plugin_sdk; print('✓ pagoda-plugin-sdk ready')"
```

**Option B: From local source (for SDK development)**
```bash
cd /path/to/pagoda/plugin/sdk
pip install -e .

# Or using uv
uv pip install -e .

# Verify installation
python -c "import pagoda_plugin_sdk; print('✓ pagoda-plugin-sdk ready')"
```

#### 1.2 Install and Test Sample Plugin

Install the hello-world sample plugin to verify your environment:

```bash
# Navigate to sample plugin directory
cd ../examples/pagoda-hello-world-plugin

# Install sample plugin (choose one)
pip install -e .          # Using pip
# OR
uv pip install -e .       # Using uv

# Verify plugin installation
python -c "from pagoda_hello_world_plugin.plugin import HelloWorldPlugin; print('✓ Sample plugin ready')"
```

#### 1.3 Test Plugin with Pagoda

Start the Pagoda server with the sample plugin enabled:

```bash
# Navigate back to Pagoda root
cd ../../..

# Start server with plugin enabled
ENABLED_PLUGINS=hello-world python manage.py runserver 8080

# In another terminal, test the plugin endpoint
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
  },
  "test": "no-auth",
  "user": {
    "username": "anonymous",
    "is_authenticated": false
  }
}
```

✅ **If everything works correctly up to this point, environment setup is complete!**

**Common Issues:**
- If `ENABLED_PLUGINS` is not set, plugins won't be loaded
- Plugin entry point name must match: `hello-world` in environment variable maps to entry point in `pyproject.toml`
- Both SDK and plugin must be installed in the same Python environment

### Step 2: Creating Your First Plugin (3 minutes)

#### 2.1 Create Plugin Project Structure

Create a new directory for your plugin outside the Pagoda repository:

```bash
# Create plugin project directory
mkdir my-first-plugin
cd my-first-plugin

# Create package directory structure
mkdir -p my_first_plugin/api_v2
touch my_first_plugin/__init__.py
touch my_first_plugin/plugin.py
touch my_first_plugin/apps.py
touch my_first_plugin/api_v2/__init__.py
touch my_first_plugin/api_v2/urls.py
touch my_first_plugin/api_v2/views.py
touch README.md
```

Your plugin structure should look like:
```
my-first-plugin/
├── README.md
├── pyproject.toml           (create in next step)
└── my_first_plugin/
    ├── __init__.py
    ├── plugin.py
    ├── apps.py
    └── api_v2/
        ├── __init__.py
        ├── urls.py
        └── views.py
```

#### 2.2 Configure pyproject.toml

Create `pyproject.toml` with the following content:

```toml
[project]
name = "my-first-plugin"
version = "1.0.0"
description = "My First Pagoda Plugin"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
dependencies = [
    "pagoda-plugin-sdk @ git+https://github.com/dmm-com/pagoda.git#subdirectory=plugin/sdk",
    "Django>=3.2",
    "djangorestframework>=3.12",
]
requires-python = ">=3.8"

[project.entry-points."pagoda.plugins"]
my-first = "my_first_plugin.plugin:MyFirstPlugin"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["my_first_plugin"]
```

**Important Notes:**
- Entry point name (`my-first`) is what you'll use in `ENABLED_PLUGINS`
- Entry point value must point to your plugin class: `package.module:ClassName`
- Build backend is `hatchling` (modern, fast Python packager)

#### 2.3 Customize Plugin Class

```python
# my_first_plugin/plugin.py
from pagoda_plugin_sdk import Plugin
from pagoda_plugin_sdk.decorators import (
    entry_hook,
    entity_hook,
    validation_hook,
    get_attrs_hook
)
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

    # Entry Lifecycle Hooks
    @entry_hook("after_create")
    def log_entry_create(self, entity_name, user, entry, **kwargs):
        """Hook executed after Entry creation (all entities)"""
        logger.info(f"New entry created: {entry.name} in entity {entity_name} by {user.username}")
        print(f"My First Plugin detected new entry: {entry.name}")

    @entry_hook("after_create", entity="customer", priority=50)
    def log_customer_create(self, entity_name, user, entry, **kwargs):
        """Hook executed only for 'customer' entity with high priority"""
        logger.info(f"Customer entry created: {entry.name}")
        # Perform customer-specific processing

    @entry_hook("before_update")
    def modify_entry_before_update(self, entity_name, user, validated_data, entry, **kwargs):
        """Hook executed before Entry update - can modify data"""
        logger.info(f"Entry updating: {entry.name}")
        # You can modify validated_data before update
        # validated_data["name"] = validated_data["name"].upper()
        return validated_data

    # Entity Lifecycle Hooks
    @entity_hook("after_create")
    def log_entity_create(self, user, entity, **kwargs):
        """Hook executed after Entity creation"""
        logger.info(f"New entity created: {entity.name} by {user.username}")

    @entity_hook("before_update")
    def modify_entity_before_update(self, user, validated_data, entity, **kwargs):
        """Hook executed before Entity update - can modify data"""
        logger.info(f"Entity updating: {entity.name}")
        return validated_data

    # Validation Hook
    @validation_hook()
    def validate_entry_name(self, user, schema_name, name, attrs, instance, **kwargs):
        """Custom validation for entry creation/update

        Raises ValueError to reject invalid entries
        """
        # Example: Reject entries with forbidden words
        forbidden_words = ["forbidden", "banned", "illegal"]
        if any(word in name.lower() for word in forbidden_words):
            raise ValueError(f"Entry name cannot contain forbidden words")

        # Example: Validate minimum name length
        if len(name) < 3:
            raise ValueError("Entry name must be at least 3 characters")

    # Data Access Hooks
    @get_attrs_hook("entry")
    def add_custom_entry_metadata(self, entry, attrinfo, is_retrieve, **kwargs):
        """Add custom metadata to entry attributes"""
        logger.info(f"Getting entry attrs for: {entry.name}")

        # Add custom metadata to each attribute
        for attr in attrinfo:
            attr["plugin_processed"] = True
            attr["processed_by"] = "my-first-plugin"

        return attrinfo

    @get_attrs_hook("entity")
    def add_custom_entity_metadata(self, entity, attrinfo, **kwargs):
        """Add custom metadata to entity attributes"""
        logger.info(f"Getting entity attrs for: {entity.name}")

        # Add plugin-specific information
        for attr in attrinfo:
            attr["plugin_version"] = self.version

        return attrinfo
```

**Decorator Types and Usage:**

1. **`@entry_hook(hook_name, entity=None, priority=100)`**
   - For Entry lifecycle events
   - Supports entity-specific filtering
   - Can modify data in "before" hooks

2. **`@entity_hook(hook_name, priority=100)`**
   - For Entity lifecycle events
   - Can modify data in "before" hooks

3. **`@validation_hook(priority=100)`**
   - For entry validation
   - Raise `ValueError` to reject invalid data

4. **`@get_attrs_hook(target, priority=100)`**
   - For modifying data before returning to client
   - Target must be "entry" or "entity"
   - Must return modified attrinfo list

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

#### 3.1 Install Your Plugin in Development Mode

Navigate to your plugin directory and install it:

**Option A: Using pip**
```bash
cd /path/to/my-first-plugin
pip install -e .
```

**Option B: Using uv (recommended)**
```bash
cd /path/to/my-first-plugin
uv pip install -e .
```

#### 3.2 Verify Plugin Installation

Check that your plugin can be imported and instantiated:

```bash
python -c "
from my_first_plugin.plugin import MyFirstPlugin
plugin = MyFirstPlugin()
print(f'✓ Plugin ready: {plugin.name} v{plugin.version}')
print(f'  ID: {plugin.id}')
print(f'  Django apps: {plugin.django_apps}')
print(f'  API patterns: {plugin.api_v2_patterns}')
"
```

**Expected Output:**
```
✓ Plugin ready: My First Plugin v1.0.0
  ID: my-first-plugin
  Django apps: ['my_first_plugin']
  API patterns: my_first_plugin.api_v2.urls
```

#### 3.3 Test with Pagoda Application

Start Pagoda with your plugin enabled:

```bash
# Navigate to Pagoda repository
cd /path/to/pagoda

# Start server with plugin enabled
ENABLED_PLUGINS=my-first python manage.py runserver 8080
```

**Expected Logs on Success:**
```
[INFO] Initializing plugin system...
[INFO] Starting plugin discovery...
[INFO] Loaded external plugin: my-first
[INFO] Registered plugin: my-first-plugin v1.0.0
[INFO] Successfully injected models into plugin SDK
[INFO] Registered 6 hook(s) for plugin 'my-first-plugin'
[INFO] Plugin discovery completed. Found 1 plugins.
[INFO] Plugin system initialized successfully
```

#### 3.4 Test Plugin API Endpoints

In another terminal, test your plugin's endpoints:

```bash
# Test the no-auth endpoint
curl http://localhost:8080/api/v2/plugins/my-first/test/

# Test authenticated endpoint (requires valid token)
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8080/api/v2/plugins/my-first/hello/
```

**Expected Response:**
```json
{
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
  "timestamp": "2025-10-12T12:34:56.789012"
}
```

#### 3.5 Test Hook Execution

Create a test entity and entry to see your hooks in action:

```bash
# Watch server logs for hook messages
# You should see log messages like:
# [INFO] [My First Plugin] Entry created: 'test-entry' in entity 'TestEntity' by admin
# [INFO] [My First Plugin] Getting entry attrs for: 'test-entry'
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

### Issue 4: Entity Filtering Not Working

**Symptoms:**
Hook decorated with `entity="customer"` is being called for all entities.

**Diagnostic Steps:**
```python
# Check if entity parameter is specified correctly
@entry_hook("after_create", entity="customer")  # ✅ Correct
def handle_customer(self, entity_name, user, entry, **kwargs):
    pass

# Common mistakes:
@entry_hook("after_create", entity_name="customer")  # ❌ Wrong parameter name
@entry_hook("after_create", entity=["customer"])     # ❌ Should be string, not list
```

**Solution:**
```python
# Verify entity name matches exactly (case-sensitive)
@entry_hook("after_create", entity="Customer")  # Won't match "customer"
@entry_hook("after_create", entity="customer")  # ✅ Correct

# Check entity name in hook handler for debugging
@entry_hook("after_create")
def debug_entity_name(self, entity_name, user, entry, **kwargs):
    logger.info(f"Entity name received: '{entity_name}'")
    # Use this to verify the actual entity name
```

### Issue 5: Wrong Decorator for Hook Type

**Symptoms:**
```
[ERROR] Hook validation failed: unexpected arguments
```

**Solutions:**

Each decorator is designed for specific hook types:

```python
# ❌ Wrong decorator for validation hook
@entry_hook("validate")
def validate_entry(self, user, schema_name, name, attrs, instance, **kwargs):
    pass

# ✅ Correct decorator
@validation_hook()
def validate_entry(self, user, schema_name, name, attrs, instance, **kwargs):
    pass

# ❌ Wrong decorator for data access hook
@entry_hook("get_attrs")
def modify_attrs(self, entry, attrinfo, is_retrieve, **kwargs):
    pass

# ✅ Correct decorator
@get_attrs_hook("entry")
def modify_attrs(self, entry, attrinfo, is_retrieve, **kwargs):
    return attrinfo
```

**Correct Decorator Usage:**
- `@entry_hook()` - For entry lifecycle (create, update, delete, restore)
- `@entity_hook()` - For entity lifecycle (create, update)
- `@validation_hook()` - For entry validation only
- `@get_attrs_hook()` - For data access hooks (entry/entity get_attrs)

### Issue 6: Hook Priority Not Working as Expected

**Symptoms:**
Hooks are executing in unexpected order despite setting priority values.

**Solution:**
```python
# Remember: Lower priority number = Higher priority (executes first)
class MyPlugin(Plugin):
    @entry_hook("after_create", priority=50)   # Executes FIRST
    def first_handler(self, entity_name, user, entry, **kwargs):
        pass

    @entry_hook("after_create", priority=100)  # Executes SECOND (default)
    def second_handler(self, entity_name, user, entry, **kwargs):
        pass

    @entry_hook("after_create", priority=150)  # Executes LAST
    def third_handler(self, entity_name, user, entry, **kwargs):
        pass
```

**Debugging Priority Issues:**
```python
# Add logging to verify execution order
@entry_hook("after_create", priority=50)
def handler_a(self, entity_name, user, entry, **kwargs):
    logger.info(f"Handler A executing (priority 50)")

@entry_hook("after_create", priority=100)
def handler_b(self, entity_name, user, entry, **kwargs):
    logger.info(f"Handler B executing (priority 100)")

# Check logs to verify execution order:
# [INFO] Handler A executing (priority 50)
# [INFO] Handler B executing (priority 100)
```

### Issue 7: Data Access Hook Not Returning Modified Data

**Symptoms:**
```
[ERROR] get_attrs_hook must return attrinfo list
```

**Solution:**
```python
# ❌ Forgot to return modified attrinfo
@get_attrs_hook("entry")
def modify_attrs(self, entry, attrinfo, is_retrieve, **kwargs):
    for attr in attrinfo:
        attr["custom_field"] = "value"
    # Missing return statement!

# ✅ Correct: Always return the modified attrinfo
@get_attrs_hook("entry")
def modify_attrs(self, entry, attrinfo, is_retrieve, **kwargs):
    for attr in attrinfo:
        attr["custom_field"] = "value"
    return attrinfo  # Must return!

# ✅ Even if no modifications, return the original
@get_attrs_hook("entry")
def no_modification(self, entry, attrinfo, is_retrieve, **kwargs):
    logger.info("Hook called but no changes needed")
    return attrinfo  # Still must return!
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

### Building Your Plugin

Before distributing your plugin, you need to build it into a distributable package.

#### Option A: Using build tool (standard)

```bash
# Install build tool if not already installed
pip install build

# Build distribution packages
python -m build

# This creates:
# dist/my_first_plugin-1.0.0-py3-none-any.whl  (wheel package)
# dist/my_first_plugin-1.0.0.tar.gz            (source distribution)
```

#### Option B: Using uv (recommended - faster)

```bash
# Build with uv
uv build

# Creates the same dist/ files
```

### Publishing Your Plugin

#### To PyPI (Public)

```bash
# Install twine if needed
pip install twine

# Upload to PyPI
python -m twine upload dist/*

# Or using uv
uv publish
```

#### To TestPyPI (For Testing)

```bash
# Upload to TestPyPI first to test
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ my-first-plugin
```

#### To GitHub Releases

```bash
# Create a git tag
git tag v1.0.0
git push origin v1.0.0

# Upload wheel file to GitHub release
# Users can install with:
# pip install https://github.com/you/my-plugin/releases/download/v1.0.0/my_first_plugin-1.0.0-py3-none-any.whl
```

### Production-Ready pyproject.toml

Update your `pyproject.toml` with complete metadata for production:

```toml
[project]
name = "my-first-plugin"
version = "1.0.0"
description = "A production-ready Pagoda plugin"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
keywords = ["pagoda", "plugin", "yourfeature"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Web Environment",
    "Framework :: Django",
    "Framework :: Django :: 3.2",
    "Framework :: Django :: 4.0",
    "Framework :: Django :: 4.1",
    "Framework :: Django :: 4.2",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Internet :: WWW/HTTP",
]
dependencies = [
    "pagoda-plugin-sdk @ git+https://github.com/dmm-com/pagoda.git#subdirectory=plugin/sdk",
    "Django>=3.2",
    "djangorestframework>=3.12",
]
requires-python = ">=3.8"

[project.urls]
Homepage = "https://github.com/youruser/my-first-plugin"
Documentation = "https://my-plugin-docs.example.com"
Repository = "https://github.com/youruser/my-first-plugin.git"
Issues = "https://github.com/youruser/my-first-plugin/issues"
Changelog = "https://github.com/youruser/my-first-plugin/blob/main/CHANGELOG.md"

[project.entry-points."pagoda.plugins"]
my-first = "my_first_plugin.plugin:MyFirstPlugin"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["my_first_plugin"]
```

### Continuous Integration with GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Test and Build Plugin

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v4
      with:
        version: "latest"

    - name: Set up Python
      run: uv python install ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        uv pip install git+https://github.com/dmm-com/pagoda.git#subdirectory=plugin/sdk
        uv pip install -e .
        uv pip install pytest

    - name: Run tests
      run: |
        uv run pytest tests/

    - name: Test plugin loading
      run: |
        uv run python -c "from my_first_plugin.plugin import MyFirstPlugin; print('✓ Plugin loads successfully')"

  build:
    needs: test
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v4

    - name: Build package
      run: uv build

    - name: Upload artifacts
      uses: actions/upload-artifact@v4
      with:
        name: dist
        path: dist/

    - name: Publish to PyPI
      if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags')
      env:
        UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
      run: uv publish
```

### Version Management Best Practices

1. **Update version in pyproject.toml**
   ```toml
   version = "1.0.1"  # Semantic versioning
   ```

2. **Create git tag**
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

3. **Maintain CHANGELOG.md**
   ```markdown
   # Changelog

   ## [1.0.1] - 2025-10-12
   ### Fixed
   - Bug fix description

   ## [1.0.0] - 2025-10-01
   ### Added
   - Initial release
   ```

### Installation Instructions for Users

Once published, users can install your plugin:

```bash
# From PyPI
pip install my-first-plugin

# From Git repository
pip install git+https://github.com/youruser/my-first-plugin.git

# From Git tag
pip install git+https://github.com/youruser/my-first-plugin.git@v1.0.0

# Using uv (faster)
uv pip install my-first-plugin
```

Then enable it in their Pagoda installation:
```bash
export ENABLED_PLUGINS=my-first
python manage.py runserver
```

## Summary

By following this quick start guide, you can create a working Pagoda plugin in 5 minutes:

1. ✅ Install pagoda-plugin-sdk
2. ✅ Create plugin structure with pyproject.toml
3. ✅ Implement plugin with decorators (@entry_hook, @entity_hook, etc.)
4. ✅ Test with development installation
5. ✅ Build and distribute with uv or pip

For more detailed information, refer to:
- [Plugin System Documentation](plugin_system.md) - Complete reference
- [Plugin Architecture Diagrams](plugin_architecture_diagrams.md) - Visual architecture