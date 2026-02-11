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
from pagoda_plugin_sdk.decorators import entry_hook

class MyPlugin(Plugin):
    id = "my-plugin"
    name = "My Plugin"
    version = "1.0.0"
    django_apps = ["my_plugin"]
    api_v2_patterns = "my_plugin.api_v2.urls"

    @entry_hook("after_create")
    def log_entry_create(self, entity_name, user, entry, **kwargs):
        """Called after an entry is created"""
        logger.info(f"Entry created: {entry.name}")
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
# Install pagoda-plugin-sdk from Git repository (recommended)
pip install git+https://github.com/dmm-com/pagoda.git#subdirectory=plugin/sdk

# Or using uv (faster)
uv pip install git+https://github.com/dmm-com/pagoda.git#subdirectory=plugin/sdk

# Or from local source (for SDK development)
cd /path/to/pagoda/plugin/sdk
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
    "pagoda-plugin-sdk @ git+https://github.com/dmm-com/pagoda.git#subdirectory=plugin/sdk",
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
from pagoda_plugin_sdk.decorators import entry_hook
import logging

logger = logging.getLogger(__name__)

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

    # Hook handlers using decorators
    @entry_hook("after_create")
    def log_after_create(self, entity_name, user, entry, **kwargs):
        """Called after an entry is created"""
        logger.info(f"Entry created: {entry.name} in {entity_name}")

    @entry_hook("before_update")
    def log_before_update(self, entity_name, user, validated_data, entry, **kwargs):
        """Called before an entry is updated"""
        logger.info(f"Entry updating: {entry.name}")
        return validated_data

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

## Asynchronous Job Tasks

Plugins can define asynchronous Celery tasks that integrate with Airone's Job system for executing long-running operations in the background.

### Overview

The plugin job task system enables:

- **Background Execution**: Run time-consuming operations without blocking API responses
- **Job UI Integration**: Unified progress tracking through Airone's Job management interface
- **Operation Tracking**: Audit trail of who executed what and when
- **Status Management**: Automatic handling of job lifecycle states

### Operation ID Allocation

Each job task requires a unique operation ID for tracking and execution.

**ID Range Allocation:**

- **1-99**: Core operations (reserved for Airone core)
- **100-199**: custom_view operations (reserved for legacy custom views)
- **200-9999**: Plugin operations (available for plugin use)
- **10000+**: Reserved for future use

**Configuration:**

Operation ID ranges are configured in Airone settings or via environment variable:

```python
# In airone/settings_common.py or as environment variable
PLUGIN_OPERATION_ID_CONFIG = {
    "hello-world": (5000, 5099),      # Plugin ID: (range_start, range_end)
    "my-plugin": (6000, 6099),
}
```

Each plugin is allocated a range (e.g., 100 IDs from 5000 to 5099). Task operations use offsets within this range:

```python
# Actual operation_id = range_start + offset
# Example: hello-world plugin with offset 0 → operation_id = 5000
```

### Implementing Plugin Tasks

Plugin job tasks follow a four-step implementation pattern:

#### 1. Define Operation Offsets (config.py)

Create a configuration file defining task offsets and metadata:

```python
# my_plugin/config.py
import enum
from airone.lib.plugin_task import PluginTaskConfig

class MyPluginOperation(int, enum.Enum):
    """Operation offsets for my-plugin tasks"""
    TASK_A = 0  # offset within allocated range
    TASK_B = 1
    TASK_C = 2

PLUGIN_TASK_CONFIG = PluginTaskConfig(
    plugin_id="my-plugin",
    module_path="my_plugin.tasks",
    tasks={
        # "operation_name": (offset, "function_name")
        "task_a": (MyPluginOperation.TASK_A, "task_a"),
        "task_b": (MyPluginOperation.TASK_B, "task_b"),
    },
    # Optional: specify task behavior
    hidden_operations=["task_b"],      # Hide from UI
    cancelable_operations=["task_a"],  # Allow user cancellation
)
```

#### 2. Implement Celery Task (tasks.py)

Create the task implementation with proper decorators:

```python
# my_plugin/tasks.py
import logging
from airone.celery import app
from airone.lib.plugin_task import register_plugin_job_task
from job.models import Job, JobStatus
from my_plugin.config import MyPluginOperation

logger = logging.getLogger(__name__)

@register_plugin_job_task(MyPluginOperation.TASK_A)
@app.task(bind=True)
def task_a(self, job_id: int):
    """Example job task implementation"""
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found")
        return

    # Check if job was canceled by user
    if job.is_canceled():
        logger.info(f"Job {job_id} was canceled")
        return

    # Check if job is ready to proceed
    if not job.proceed_if_ready():
        logger.warning(f"Job {job_id} is not ready")
        return

    # Update status to processing
    job.update(JobStatus.PROCESSING)

    try:
        # Your long-running task logic here
        params = job.params  # Access job parameters
        logger.info(f"Processing job {job_id} with params: {params}")

        # Example: process data
        import time
        time.sleep(10)  # Simulate long operation

        # Update status to done
        job.update(JobStatus.DONE)
        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        job.update(JobStatus.ERROR)
```

**Key Implementation Points:**

- **Double Decorator**: Use both `@register_plugin_job_task(offset)` and `@app.task(bind=True)`
- **Status Checks**: Always check `is_canceled()` and `proceed_if_ready()`
- **Status Updates**: Update job status to PROCESSING, DONE, or ERROR
- **Error Handling**: Catch exceptions and update status to ERROR

#### 3. Register in AppConfig (apps.py)

Register the plugin's task configuration during Django initialization:

```python
# my_plugin/apps.py
import logging
from django.apps import AppConfig
from airone.lib.plugin_task import PluginTaskRegistry

logger = logging.getLogger(__name__)

class MyPluginConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "my_plugin"

    def ready(self):
        """Called when Django app is ready"""
        from my_plugin.config import PLUGIN_TASK_CONFIG

        # Register plugin tasks with global registry
        PluginTaskRegistry.register(PLUGIN_TASK_CONFIG)
        logger.info("Plugin tasks registered successfully")
```

#### 4. Trigger Job from API (api_v2/views.py)

Create an API endpoint to trigger the job:

```python
# my_plugin/api_v2/views.py
from rest_framework.response import Response
from rest_framework import status
from pagoda_plugin_sdk import PluginAPIViewMixin
from airone.lib.plugin_task import PluginTaskRegistry
from job.models import Job

class TaskView(PluginAPIViewMixin):
    def post(self, request):
        """Trigger a background job task"""
        try:
            # Get operation_id from registry
            operation_id = PluginTaskRegistry.get_operation_id(
                "my-plugin",
                "task_a"
            )

            # Create new job
            job = Job._create_new_job(
                user=request.user,
                target=None,  # Optional: ACL object for permission checks
                operation=operation_id,
                text="Task A Processing",
                params={
                    "input_data": request.data.get("input"),
                    "options": request.data.get("options", {}),
                },
            )

            # Queue job for execution
            job.run()

            return Response({
                "message": "Task queued successfully",
                "job_id": job.id,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

### Job Lifecycle

Jobs follow a standard lifecycle with automatic state transitions:

```
API Request
    ↓
Job._create_new_job()
    ↓ (status = PREPARING)
    ↓
job.run()
    ↓ (Celery task queued)
    ↓
Task Handler executes
    ↓ (status = PROCESSING)
    ↓
Business logic execution
    ↓
    ├─ Success → status = DONE
    └─ Failure → status = ERROR

User can cancel → status = CANCELED
```

**Job Status Values:**

- `PREPARING`: Job created, waiting to start
- `PROCESSING`: Task is currently executing
- `DONE`: Task completed successfully
- `ERROR`: Task failed with an error
- `CANCELED`: User canceled the job

### Best Practices

#### 1. Always Check Job Status

```python
@app.task(bind=True)
def my_task(self, job_id: int):
    job = Job.objects.get(id=job_id)

    # Check if user canceled
    if job.is_canceled():
        return

    # Check if dependencies are met
    if not job.proceed_if_ready():
        return

    # Proceed with task...
```

#### 2. Update Status Appropriately

```python
# When starting work
job.update(JobStatus.PROCESSING)

# When successful
job.update(JobStatus.DONE)

# When failed
job.update(JobStatus.ERROR)
```

#### 3. Handle Errors Gracefully

```python
try:
    # Task logic
    result = perform_operation()
    job.update(JobStatus.DONE)
except SpecificException as e:
    logger.error(f"Specific error: {e}")
    job.update(JobStatus.ERROR)
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    job.update(JobStatus.ERROR)
```

#### 4. Use Meaningful Job Text

```python
# Good: Descriptive job text
job = Job._create_new_job(
    user=request.user,
    operation=operation_id,
    text=f"Processing {entity_name} export ({len(entries)} entries)",
)

# Bad: Generic text
job = Job._create_new_job(
    user=request.user,
    operation=operation_id,
    text="Processing",
)
```

#### 5. Test with Celery Worker

Always test plugin tasks with a running Celery worker:

```bash
# Terminal 1: Start Celery worker
poetry run celery -A airone worker -l info

# Terminal 2: Start Django server
ENABLED_PLUGINS=my-plugin python manage.py runserver

# Terminal 3: Trigger task
curl -X POST http://localhost:8000/api/v2/plugins/my-plugin/task/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"input": "test data"}'
```

### Validation at Startup

Django automatically validates all plugin operation IDs during startup:

```python
# In airone/job/apps.py
class JobConfig(AppConfig):
    def ready(self):
        PluginTaskRegistry.validate_all()
```

**Validation Checks:**

1. **Range Conflicts**: Ensures no overlap between plugin ID ranges
2. **Offset Bounds**: Verifies all offsets are within allocated range
3. **Missing Registration**: Detects plugins without registry entries

**Example Validation Error:**

```
django.core.exceptions.ImproperlyConfigured: Plugin 'my-plugin' operation 'task_a'
with offset 150 exceeds allocated range (6000, 6099). Maximum offset is 99.
```

If validation fails, Django will not start, preventing deployment of misconfigured plugins.

### Checking Job Status

Users can check job status through the standard Job API:

```bash
# Get job details
curl http://localhost:8000/api/v2/jobs/<job_id>/ \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response:**

```json
{
  "id": 123,
  "user": {"id": 1, "username": "admin"},
  "text": "Task A Processing",
  "status": "DONE",
  "operation": 6000,
  "created_at": "2025-11-01T12:00:00Z",
  "updated_at": "2025-11-01T12:00:10Z"
}
```

### Complete Example

For a complete working example, see the hello-world-plugin implementation at:

```
plugin/examples/pagoda-hello-world-plugin/
├── pagoda_hello_world_plugin/
│   ├── config.py           # Operation offset definitions
│   ├── tasks.py            # Celery task implementations
│   ├── apps.py             # Task registry registration
│   └── api_v2/
│       └── views.py        # API endpoint for job creation
```

The example demonstrates:
- Operation offset enumeration
- Task implementation with proper decorators
- Registry registration in AppConfig
- API endpoint for triggering jobs
- Status checking and error handling

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

## Backend Plugin Entity Overrides

Plugins can override standard Entry API operations for specific entities. This allows custom handling of create, retrieve, update, delete, and list operations without modifying core code.

### Configuration

Configure backend overrides in `settings_common.py` or via environment variable:

```python
# airone/settings_common.py
AIRONE = {
    # ... other settings ...

    # Backend plugin entity override configuration
    # Format: { "entityId": { "plugin": "plugin-id", "operations": [...], "params": {...} } }
    "BACKEND_PLUGIN_ENTITY_OVERRIDES": json.loads(
        env.str(
            "BACKEND_PLUGIN_ENTITY_OVERRIDES",
            json.dumps({}),  # Default: no overrides
        )
    ),
}
```

### Configuration Format

```json
{
  "entityId": {
    "plugin": "plugin-id",
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
| `entityId` | string | The entity ID (as string) to override |
| `plugin` | string | The plugin ID that provides the override handlers |
| `operations` | string[] | List of operations to override: `create`, `retrieve`, `update`, `delete`, `list` |
| `params` | object | Optional plugin-specific parameters passed to handlers |

### Example Configurations

**Single Entity Override:**
```bash
export BACKEND_PLUGIN_ENTITY_OVERRIDES='{"42": {"plugin": "cross-entity-sample", "operations": ["create", "retrieve", "update", "delete"], "params": {"configuration_entity_id": 99}}}'
```

**Multiple Entity Overrides:**
```bash
export BACKEND_PLUGIN_ENTITY_OVERRIDES='{
  "42": {"plugin": "cross-entity-sample", "operations": ["create", "retrieve"], "params": {}},
  "100": {"plugin": "custom-handler", "operations": ["retrieve"], "params": {"enrichment": true}}
}'
```

### How It Works

1. When an Entry API request is received (e.g., `GET /entry/api/v2/{entry_id}/`), the system checks if an override is registered for that entity/operation combination.

2. If an override exists, the request is dispatched to the plugin's handler instead of the default implementation.

3. The handler receives an `OverrideContext` object containing:
   - `request`: The DRF Request object
   - `user`: The authenticated user
   - `entity`: The Entity instance
   - `entry`: The Entry instance (for retrieve/update/delete)
   - `data`: Request data (for create/update)
   - `params`: Plugin-specific parameters from configuration
   - `plugin_id`: The plugin's ID
   - `operation`: The operation type

4. The handler returns a DRF `Response` object.

### Implementing Override Handlers

Use the `@override_operation` decorator to mark methods as override handlers:

```python
from pagoda_plugin_sdk.override import (
    OverrideContext,
    override_operation,
    success_response,
    error_response,
)

class MyHandlers:
    @override_operation("retrieve")
    def handle_retrieve(self, context: OverrideContext) -> Response:
        """Handle entry retrieval with custom logic."""
        entry = context.entry
        if not entry:
            return error_response("Entry not found", status_code=404)

        # Use the standard serializer for compatibility
        from entry.api_v2.serializers import EntryRetrieveSerializer
        serializer = EntryRetrieveSerializer(entry, context={"request": context.request})
        response_data = serializer.data

        # Add plugin-specific enrichment
        response_data["_plugin_override"] = {
            "active": True,
            "plugin_id": context.plugin_id,
            "message": "Custom handling active",
        }

        return success_response(response_data)
```

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

### Important: Maintaining API Compatibility

When implementing override handlers, especially for `retrieve` operations, ensure the response format is compatible with the frontend:

```python
@override_operation("retrieve")
def handle_retrieve(self, context: OverrideContext) -> Response:
    entry = context.entry

    # Use the standard serializer to ensure correct format
    from entry.api_v2.serializers import EntryRetrieveSerializer
    serializer = EntryRetrieveSerializer(entry, context={"request": context.request})
    response_data = serializer.data

    # Then add your custom fields
    response_data["_custom_field"] = "value"

    return success_response(response_data)
```

This ensures the response includes required fields like `attrs` that the frontend expects.

### Verifying Override Configuration

```bash
# Check if override is active for an entry
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/entry/api/v2/{entry_id}/

# Response with override active:
{
  "id": 123,
  "name": "test-entry",
  "attrs": [...],
  "_plugin_override": {
    "active": true,
    "plugin_id": "cross-entity-sample",
    "message": "Custom handling active"
  }
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLED_PLUGINS` | `[]` | List of plugins to enable (comma-separated) |
| `BACKEND_PLUGIN_ENTITY_OVERRIDES` | `{}` | Backend entity override configuration (JSON) |
| `FRONTEND_PLUGIN_ENTITY_OVERRIDES` | `{}` | Frontend entity override configuration (JSON) |

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
[ERROR] Hook entry.after_create failed: missing required arguments
```

**Solution**: Implement correct hook handler signature with decorator
```python
# ❌ Wrong (missing decorator)
def log_after_create(self, entity_name, user, entry, **kwargs):
    pass

# ❌ Wrong (incorrect signature)
@entry_hook("after_create")
def log_after_create(user, entry):
    pass

# ✅ Correct
@entry_hook("after_create")
def log_after_create(self, entity_name, user, entry, **kwargs):
    """
    entity_name: Name of the entity
    user: User who created the entry
    entry: The created Entry instance
    **kwargs: Additional context
    """
    logger.info(f"New entry created: {entry.name} in {entity_name}")
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

The plugin system provides a comprehensive hook system with 17 standard hooks organized into four categories:

#### Available Hook Types

**1. Entry Lifecycle Hooks**
- `entry.before_create` - Called before an entry is created
- `entry.after_create` - Called after an entry is created
- `entry.before_update` - Called before an entry is updated
- `entry.after_update` - Called after an entry is updated
- `entry.before_delete` - Called before an entry is deleted
- `entry.before_restore` - Called before an entry is restored
- `entry.after_restore` - Called after an entry is restored

**2. Entity Lifecycle Hooks**
- `entity.before_create` - Called before an entity is created
- `entity.after_create` - Called after an entity is created
- `entity.before_update` - Called before an entity is updated
- `entity.after_update` - Called after an entity is updated

**3. Validation Hooks**
- `entry.validate` - Custom validation for entry creation/update

**4. Data Access Hooks**
- `entry.get_attrs` - Modify entry attributes before returning to client
- `entity.get_attrs` - Modify entity attributes before returning to client

#### Hook Decorators

The plugin SDK provides four decorators for registering hook handlers:

**1. `@entry_hook(hook_name, entity=None, priority=100)`**

For Entry lifecycle hooks. Supports entity-specific filtering.

```python
from pagoda_plugin_sdk.decorators import entry_hook

class MyPlugin(Plugin):
    # Apply to all entities
    @entry_hook("after_create")
    def log_all_entries(self, entity_name, user, entry, **kwargs):
        logger.info(f"Entry created: {entry.name}")

    # Apply only to specific entity
    @entry_hook("after_create", entity="customer")
    def log_customer_only(self, entity_name, user, entry, **kwargs):
        logger.info(f"Customer entry created: {entry.name}")
```

**2. `@entity_hook(hook_name, priority=100)`**

For Entity lifecycle hooks.

```python
from pagoda_plugin_sdk.decorators import entity_hook

class MyPlugin(Plugin):
    @entity_hook("after_create")
    def log_entity_create(self, user, entity, **kwargs):
        logger.info(f"Entity created: {entity.name}")
```

**3. `@validation_hook(priority=100)`**

For entry validation (entry.validate hook).

```python
from pagoda_plugin_sdk.decorators import validation_hook

class MyPlugin(Plugin):
    @validation_hook()
    def validate_entry(self, user, schema_name, name, attrs, instance, **kwargs):
        if "forbidden" in name.lower():
            raise ValueError("Name cannot contain 'forbidden'")
```

**4. `@get_attrs_hook(target, priority=100)`**

For data access hooks. Target must be either "entry" or "entity".

```python
from pagoda_plugin_sdk.decorators import get_attrs_hook

class MyPlugin(Plugin):
    @get_attrs_hook("entry")
    def modify_entry_attrs(self, entry, attrinfo, is_retrieve, **kwargs):
        # Add custom field
        for attr in attrinfo:
            attr["custom_flag"] = True
        return attrinfo

    @get_attrs_hook("entity")
    def modify_entity_attrs(self, entity, attrinfo, **kwargs):
        return attrinfo
```

#### Entity Filtering

Entry hooks support entity-specific filtering using the `entity` parameter:

```python
class MyPlugin(Plugin):
    # Runs only for "product" entity
    @entry_hook("after_create", entity="product")
    def handle_product_create(self, entity_name, user, entry, **kwargs):
        # Only called when a product entry is created
        pass

    # Runs for all entities
    @entry_hook("after_create")
    def handle_any_create(self, entity_name, user, entry, **kwargs):
        # Called for all entry creations
        pass
```

When both entity-specific and generic hooks are registered, both will be executed in priority order.

#### Hook Priority System

Hooks are executed in priority order (lower number = higher priority, default is 100):

```python
class MyPlugin(Plugin):
    # Runs first (priority 50)
    @entry_hook("after_create", priority=50)
    def first_handler(self, entity_name, user, entry, **kwargs):
        logger.info("Runs first")

    # Runs second (default priority 100)
    @entry_hook("after_create")
    def second_handler(self, entity_name, user, entry, **kwargs):
        logger.info("Runs second")

    # Runs last (priority 150)
    @entry_hook("after_create", priority=150)
    def third_handler(self, entity_name, user, entry, **kwargs):
        logger.info("Runs last")
```

This is useful for ensuring proper execution order when multiple plugins handle the same hook.

#### Hook Signatures

Each hook type has a specific signature:

**Entry Lifecycle Hooks:**
```python
def handler(self, entity_name: str, user: User, entry: Entry, **kwargs) -> None:
    # For after_create, after_update, after_delete, after_restore
    pass

def handler(self, entity_name: str, user: User, validated_data: dict, **kwargs) -> dict:
    # For before_create - can modify data
    return validated_data

def handler(self, entity_name: str, user: User, validated_data: dict, entry: Entry, **kwargs) -> dict:
    # For before_update - can modify data
    return validated_data

def handler(self, entity_name: str, user: User, entry: Entry, **kwargs) -> None:
    # For before_delete, before_restore
    pass
```

**Entity Lifecycle Hooks:**
```python
def handler(self, user: User, entity: Entity, **kwargs) -> None:
    # For after_create, after_update
    pass

def handler(self, user: User, validated_data: dict, **kwargs) -> dict:
    # For before_create - can modify data
    return validated_data

def handler(self, user: User, validated_data: dict, entity: Entity, **kwargs) -> dict:
    # For before_update - can modify data
    return validated_data
```

**Validation Hook:**
```python
def handler(self, user: User, schema_name: str, name: str,
            attrs: list, instance: Optional[Entry], **kwargs) -> None:
    # Raise ValueError or ValidationError to reject
    if invalid_condition:
        raise ValueError("Validation error message")
```

**Data Access Hooks:**
```python
def handler(self, entry: Entry, attrinfo: list, is_retrieve: bool, **kwargs) -> list:
    # For entry.get_attrs - must return modified attrinfo
    return attrinfo

def handler(self, entity: Entity, attrinfo: list, **kwargs) -> list:
    # For entity.get_attrs - must return modified attrinfo
    return attrinfo
```

#### Backward Compatibility

The hook system maintains backward compatibility with the legacy custom_view system through hook name aliases:

```python
# Legacy custom_view hook names are automatically mapped to standard names
HOOK_ALIASES = {
    "before_create_entry_v2": "entry.before_create",
    "after_create_entry_v2": "entry.after_create",
    "before_update_entry_v2": "entry.before_update",
    "after_update_entry_v2": "entry.after_update",
    "before_delete_entry_v2": "entry.before_delete",
    "validate_entry": "entry.validate",
    "get_entry_attr": "entry.get_attrs",
    "get_entity_attr": "entity.get_attrs",
    # ... and more
}
```

This allows existing custom_view implementations to work with the new plugin system without modification.

#### Hook Execution Implementation

```python
# Pagoda Hook Manager implementation
class HookManager:
    def execute_hook(self, hook_name, *args, entity_name=None, **kwargs):
        # 1. Normalize hook name (handle aliases)
        # 2. Get all registered handlers
        # 3. Filter by entity if specified
        # 4. Sort by priority
        # 5. Execute each handler with error isolation
        # 6. Collect and return results
```

Key features:
- **Error Isolation**: One plugin's failure doesn't affect others
- **Priority Ordering**: Handlers execute in priority order
- **Entity Filtering**: Entity-specific hooks run only for matching entities
- **Flexible Signatures**: Different hook types have different signatures

### Model Injection Implementation

The host application (Pagoda) injects concrete model implementations into the plugin SDK during initialization. This allows plugins to access Pagoda's data models without creating direct dependencies.

#### Injected Models

The following six models are automatically injected:

1. **Entity** - Schema definition (from `entity.models.Entity`)
2. **EntityAttr** - Entity attribute definition (from `entity.models.EntityAttr`)
3. **Entry** - Data entry (from `entry.models.Entry`)
4. **Attribute** - Entry attribute (from `entry.models.Attribute`)
5. **AttributeValue** - Attribute value (from `entry.models.AttributeValue`)
6. **User** - User account (from `user.models.User`)

#### Injection Process

```python
# airone/plugins/integration.py
class PluginIntegration:
    def _inject_models(self):
        """Inject real models into the plugin SDK"""
        try:
            # Import real models from Pagoda
            import pagoda_plugin_sdk.models as sdk_models
            from entity.models import Entity, EntityAttr
            from entry.models import Entry, Attribute, AttributeValue
            from user.models import User

            # Inject real models into SDK namespace
            sdk_models.Entity = Entity
            sdk_models.Entry = Entry
            sdk_models.User = User
            sdk_models.AttributeValue = AttributeValue
            sdk_models.EntityAttr = EntityAttr
            sdk_models.Attribute = Attribute

            logger.info("Successfully injected models into plugin SDK")
        except ImportError as e:
            logger.error(f"Failed to inject models into plugin SDK: {e}")
            raise
```

#### Initialization Sequence

```
1. Pagoda Application Startup
   └─ settings_common.py loads ENABLED_PLUGINS from environment

2. Plugin System Initialization
   ├─ PluginIntegration.initialize() is called
   ├─ discover_plugins() finds and registers plugins
   └─ _inject_models() injects real models into SDK

3. Plugin Access
   └─ Plugins can now safely import and use models
```

#### Using Injected Models in Plugins

```python
# In plugin code
from pagoda_plugin_sdk.models import Entity, Entry, User

class MyPlugin(Plugin):
    @entry_hook("after_create")
    def handle_entry_create(self, entity_name, user, entry, **kwargs):
        # Direct access to model methods
        entity = entry.schema  # Access related Entity
        creator = entry.created_user  # Access related User
        attrs = entry.get_attrs()  # Call Entry methods

        # Query operations
        all_entries = Entry.objects.filter(schema=entity)
        active_users = User.objects.filter(is_active=True)
```

#### Type Safety with Protocols

The SDK provides Protocol definitions for type checking without creating implementation dependencies:

```python
from pagoda_plugin_sdk.protocols import (
    EntityProtocol,
    EntryProtocol,
    UserProtocol,
    EntityAttrProtocol,
    AttributeProtocol,
    AttributeValueProtocol,
)

def process_entry(entry: EntryProtocol) -> dict:
    """Type-safe entry processing with IDE support"""
    return {
        "id": entry.id,
        "name": entry.name,
        "schema": entry.schema.name,  # Full IntelliSense support
    }
```

#### Checking Model Availability

Always check if models are available before using them:

```python
from pagoda_plugin_sdk import models
from pagoda_plugin_sdk.models import Entity

def safe_operation():
    # Check if plugin system is initialized
    if not models.is_initialized():
        raise RuntimeError("Plugin system not initialized")

    # Check specific model
    if Entity is None:
        raise RuntimeError("Entity model not available")

    # Safe to proceed
    entities = Entity.objects.all()
```

This injection mechanism ensures that plugins remain independent of Pagoda's implementation while still having full access to its data models.

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