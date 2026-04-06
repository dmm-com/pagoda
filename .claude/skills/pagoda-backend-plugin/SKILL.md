---
name: pagoda-backend-plugin
description: |
  Development guide for Pagoda/AirOne backend plugins. Use when developing plugins under plugin/sdk/ (pagoda-plugin-sdk), plugin/examples/, or modifying the plugin integration layer at airone/plugins/. Covers plugin hooks, overrides, task registration, SDK feature extensions, and plugin integration. Trigger on requests like "create a plugin", "add a hook", "implement an override", "modify the SDK", "plugin/ code", or any backend plugin development task.
---

# Pagoda Backend Plugin Development Guide

The Pagoda backend plugin system extends the host application (AirOne) without forking. It has a two-layer architecture: the SDK (`plugin/sdk/`) and the host integration layer (`airone/plugins/`).

## Architecture

### SDK (plugin/sdk/pagoda_plugin_sdk/)
- **Host-independent** — runs without Django, can be tested independently
- `Plugin` base class: metadata (id, name, version) + Django integration (django_apps, url_patterns)
- Decorators: `@entry_hook`, `@entity_hook`, `@validation_hook`, `@get_attrs_hook`, `@override_operation`
- `__init_subclass__` auto-detects decorated methods
- Django-dependent components use lazy loading via `__getattr__`

### Host Integration Layer (airone/plugins/)
- `discovery.py` — auto-discovers plugins from entry points (`pagoda.plugins` group)
- `registry.py` — registers plugin instances, extracts hooks
- `hook_manager.py` — executes hooks (priority-ordered, entity filtering)
- `override_manager.py` — manages entry operation overrides
- `integration.py` — Django integration orchestrator (model injection, URL registration)

### Request Flow (Override)
```
Request → EntryAPI(PluginOverrideMixin)
  → _dispatch_override()
  → OverrideRegistry.get_registration()
  → handler(OverrideContext)  ← plugin handler
  OR fall back to default processing
```

## Development Workflow

### 1. Create a Plugin

**Minimal structure:**
```python
from pagoda_plugin_sdk import Plugin
from pagoda_plugin_sdk.decorators import entry_hook

class MyPlugin(Plugin):
    id = "my-plugin"
    name = "My Plugin"
    version = "0.1.0"

    @entry_hook("after_create", entity="TargetEntity")
    def on_entry_created(self, user, entry, entity_name):
        # Post-creation processing
        pass
```

**Available decorators:**
- `@entry_hook(hook_type, entity=None, priority=100)` — Entry lifecycle (before_create, after_create, before_update, after_update, before_delete, before_restore, after_restore)
- `@entity_hook(hook_type, entity=None, priority=100)` — Entity lifecycle
- `@validation_hook(entity=None, priority=100)` — Entry validation
- `@get_attrs_hook(target, entity=None, priority=100)` — Attribute data transformation
- `@override_operation(operation)` — CRUD operation override ("create", "retrieve", "update", "delete", "list")

**Writing overrides:**
```python
from pagoda_plugin_sdk.override import override_operation, OverrideContext

class MyPlugin(Plugin):
    @override_operation("create")
    def custom_create(self, context: OverrideContext):
        # context.request, context.user, context.entity, context.data, context.params
        # Response helpers: success_response(), created_response(), error_response()
        return self.created_response({"id": new_entry.id})
```

**Packaging:**
- Define `[project.entry-points."pagoda.plugins"]` in `pyproject.toml`
- Enable via `ENABLED_PLUGINS` setting
- Configure overrides via `BACKEND_PLUGIN_ENTITY_OVERRIDES`

### 2. Run Static Analysis

**SDK code:**
```bash
# Run from SDK directory
cd plugin/sdk
uv run ruff check pagoda_plugin_sdk/
uv run mypy pagoda_plugin_sdk/
```

**Example plugin code:**
```bash
# From project root
uv run ruff check plugin/examples/<plugin-name>/
```

**Host integration layer:**
```bash
uv run ruff check airone/plugins/
uv run mypy airone/plugins/
```

Ruff and Mypy follow the project root `pyproject.toml` configuration (100-char line length, isort enabled).

### 3. Run Tests

**Plugin tests are split into three layers. Run the appropriate layer based on what was changed.**

#### SDK Tests (no Django required)
Functional tests for the SDK itself. Run in an independent environment without Django.

```bash
cd plugin/sdk
python -m unittest tests.<test_module> -v

# Examples
python -m unittest tests.test_plugin -v
python -m unittest tests.test_decorators -v
python -m unittest tests.test_override -v
```

- Tests requiring Django setup are automatically skipped
- Use mocks for isolated testing (`@patch` decorator)

#### Example Plugin Tests
Individual tests for each plugin.

```bash
# hello-world plugin
cd plugin/examples/pagoda-hello-world-plugin
python -m unittest tests -v

# cross-entity plugin
cd plugin/examples/pagoda-cross-entity-plugin
python -m unittest tests -v
```

#### Host Integration Tests (Django required)
Tests for the `airone/plugins/` integration layer.

```bash
# From project root
uv run python manage.py test airone.tests.test_plugins
```

**Choosing which tests to run:**
- SDK decorator / base class changes → SDK tests
- Plugin hook / override implementation → individual plugin tests
- Plugin integration (discovery, registry, hook_manager, override_manager) → host integration tests
- Entry/Entity API used by plugins → core tests (`entry.tests`, `entity.tests`) as well

### 4. Plugin-Specific Notes

**Avoiding circular imports:**
- The SDK does not directly depend on host Django models
- `integration.py`'s `_inject_models()` injects models at runtime
- When using Entity/Entry within plugins, reference the injected models

**Operation ID management:**
- Celery tasks use `PluginTaskRegistry` for operation ID allocation
- Range: 200-9999 (core: 1-99, custom_view: 100-199)
- Configure ranges via `PLUGIN_OPERATION_ID_CONFIG`

**Override constraints:**
- Multiple plugins cannot override the same entity/operation (`OverrideConflictError`)
- During an override, normal Job creation and hook execution are skipped
- If needed, explicitly create Jobs within the plugin

**Configuration:**
```python
# Must be enabled in settings
ENABLED_PLUGINS = ["my-plugin"]

AIRONE = {
    "BACKEND_PLUGIN_ENTITY_OVERRIDES": {
        "<entity_id>": {
            "plugin": "my-plugin",
            "operations": ["create", "update"],
            "params": {"key": "value"}
        }
    }
}
```

### 5. Quality Checklist

Before completing changes:
1. `uv run ruff check <changed-files>` — lint OK
2. `uv run mypy <changed-modules>` — type checking OK (run independently for SDK)
3. Appropriate layer tests pass (SDK / plugin / host integration)
4. Comments and docstrings are in English
5. Verify SDK changes do not break the host side

## Reference: Example Plugins

- `plugin/examples/pagoda-hello-world-plugin/` — demos all hook types
- `plugin/examples/pagoda-cross-entity-plugin/` — demos overrides (cross-entity linking, cascade delete)
