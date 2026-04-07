---
name: pagoda-backend-core
description: |
  Development guide for Pagoda/AirOne backend (Django + DRF) core. Use when developing or modifying Django app models, views, serializers, tests, and API endpoints. Covers all backend Python code changes, Django migrations, REST API development, Celery tasks, and Elasticsearch integration outside of plugin/. Trigger on requests like "fix the backend", "add an API", "change the model", "fix the test", "modify the serializer", or any backend development task.
---

# Pagoda Backend Core Development Guide

The Pagoda backend is built with Django 5.2 + Django REST Framework. This skill defines conventions for core (non-plugin) backend development.

## Development Workflow

### 1. Write Code

**Django app structure (common pattern across apps):**
```
<app>/
  ├── models.py           # Model definitions (inherit from ACLBase)
  ├── admin.py            # Django admin + import/export
  ├── tasks.py            # Celery tasks
  ├── api_v2/             # Current API (use this for new development)
  │   ├── views.py        # ViewSet + @extend_schema
  │   ├── serializers.py  # DRF serializers + Pydantic models
  │   ├── urls.py         # Path-based routing
  │   └── pagination.py   # Custom pagination
  ├── api_v1/             # Legacy API
  └── tests/
```

**Writing API views:**
- Apply `PluginOverrideMixin` to ViewSets (plugin support)
- Use `@extend_schema()` for OpenAPI documentation
- Permissions are based on `ACLType` (Nothing/Readable/Writable/Full)
- Parsers: `JSONParser` + `YAMLParser`

**Writing serializers:**
- Use Pydantic `BaseModel` + `@model_validator` for validation
- Use DRF `ModelSerializer` to define response format
- Use nested serializers to include related data

**Shared libraries (`airone/lib/`):**
- `acl.py` — ACL permission checks (`get_permission_level`, `get_permitted_objects`)
- `drf.py` — Custom exceptions (error codes AE-XXXXXX), YAMLParser
- `types.py` — `AttrType` IntEnum (STRING, OBJECT, BOOLEAN, etc.)
- `elasticsearch.py` — ES search and index operations
- `test.py` — Test base classes (`AironeTestCase`, `AironeViewTest`)

### 2. Run Static Analysis

After code changes, run static analysis and confirm everything passes before moving to tests.

```bash
# Ruff (linter + isort) — target changed files
uv run ruff check <changed-files>

# Auto-fix if possible
uv run ruff check --fix <changed-files>

# Mypy (type checking) — target changed modules
uv run mypy <changed-modules> --config-file=pyproject.toml
```

**Ruff rules:**
- Applies `E`, `F`, `I`, `W` (pyflakes, pycodestyle, isort)
- Max line length: 100 characters
- Excludes migrations/ and manage.py

**Mypy rules:**
- `check_untyped_defs = true` — checks functions even without type annotations
- Tests and migrations have `ignore_errors = true`
- `webhook`, `category`, `job`, `acl`, `user` etc. have `disallow_untyped_defs = true` (strict mode)
- Type annotations are encouraged for new code

### 3. Run Tests

**Backend tests take a very long time to run in full, so unless explicitly instructed, run only tests related to the changes.**

```bash
# Specific test method
uv run python manage.py test entity.tests.test_api_v2.ViewTest.test_retrieve_entity

# Specific test class
uv run python manage.py test entity.tests.test_model.ModelTest

# Specific test file
uv run python manage.py test entity.tests.test_api_v2

# Entire app (only when changes are extensive)
uv run python manage.py test entity
```

**Writing tests:**
- API tests inherit from `AironeViewTest` and use `self.client` for HTTP requests
- Model tests inherit from `AironeTestCase`
- Helpers: `self.create_entity()`, `self.add_entry()`, `self.make_attr()`, `self.guest_login()`, `self.admin_login()`
- Elasticsearch tests create indexes with `test-` prefix + PID suffix during setup

**Choosing which tests to run:**
- Model changes → `<app>/tests/test_model.py`
- API v2 changes → `<app>/tests/test_api_v2.py`
- API v1 changes → `<app>/tests/test_api_v1.py`
- Serializer changes → related test files broadly
- `airone/lib/` changes → `airone/tests/` + tests from apps that use the changed code

### 4. Quality Checklist

Before completing changes:
1. `uv run ruff check <changed-files>` — lint and import order OK
2. `uv run mypy <changed-modules>` — type checking OK
3. `uv run python manage.py test <related-tests>` — tests pass
4. Comments and docstrings are written in English

## Important Notes

- All imports go at the top of the file (in-function imports only allowed to prevent circular dependencies)
- Do not manually edit migration files (generate with `makemigrations`)
- Models inheriting from ACLBase require permission checks
- Celery tasks use the JobOperation enum registered in the `job/` app
- `airone/settings_common.py` is the main settings file; `airone/settings.py` switches between Dev/Prd
