# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pagoda (formerly AirOne) is an entity/metadata management platform with flexible data-structure, relations, and ACL. Backend is Django + DRF, frontend is React + TypeScript + Material-UI.

## Build, Lint, and Test Commands

### Lite mode (no containers at all) — prefer this while iterating
`tools/test_local.sh --sqlite` (below) removes the MySQL container. Lite mode
removes the other two as well: an in-process search index replaces
Elasticsearch and kombu's `memory://` replaces RabbitMQ, so nothing has to be
started, and it covers the dev server rather than only tests.

- **Whole suite, one process per app (mirrors CI's matrix):** `tools/lite.sh test`
  — writes `.pagoda-lite/testlogs/results.json` (per-app counts, durations,
  failing test names) so you do not have to parse stdout. Its concurrency
  budget is shared across all worktrees, so parallel agents throttle each
  other instead of thrashing the machine; override with `PAGODA_TEST_JOBS`.
- **One target:** `tools/lite.sh test entry.tests.test_service`
- **Dev server on this checkout's own port:** `tools/lite.sh init` then `tools/lite.sh run`
- **Show this checkout's slot/port/paths:** `tools/lite.sh info`
- **Is my dev server up?** `tools/lite.sh status`
- **Any manage.py command:** prefix with `PAGODA_LITE=1`

Migrations are generated, not committed; `lite.sh` creates them when missing
and regenerates them when models have changed, so a fresh or freshly-rebased
worktree needs no extra step.

The pieces compose, so `AIRONE_ES_BACKEND=inmemory tools/test_local.sh --sqlite
<target>` also runs container-free.

Do NOT run every app in a single `manage.py test` process — some apps leave
process-global state behind and the combined run reports failures CI never
sees. See `docs/content/getting_started/lite_mode.md` for the fidelity limits
(search scoring is approximate; escalate to the real stack before shipping
search-semantics changes).

### Backend (Python/Django)
- **Run all tests for an app:** `uv run python manage.py test <app_name>`
- **Run a specific test:** `uv run python manage.py test <app_name>.tests.<test_file>.<TestClass>.<test_method>`
- **Fast local test runs:** `tools/test_local.sh <target>...` — serial + `--keepdb`
  (skips ~28s of test-DB creation per run; local Docker MySQL/ES is I/O-bound so
  `--parallel` is slower here, while CI keeps using `--parallel`). The test DB is
  isolated per checkout, so parallel worktrees/sessions don't corrupt each other.
  Use `tools/test_local.sh --fresh <target>` after changing models/migrations.
- **Fastest (development iteration):** `tools/test_local.sh --sqlite <target>...`
  runs against in-memory SQLite. SQL round-trips dominate local test time, so
  this cuts the whole backend suite from ~19min to ~3min (entity: 99s → 14s).
  Migrations run in-memory each time; `--keepdb`/DB isolation are unnecessary.
  SQLite runs go through `airone/db/backends/sqlite_pagoda`, which restores the
  MySQL behaviour Django's stock SQLite backend drops — integer-range
  validators, case-insensitive text comparison and `__regex` case folding — so
  those no longer diverge. Elasticsearch semantics still can, so keep running
  the final pre-push check against the real stack or rely on CI.
- **Lint (ruff):** `uv run ruff check .`
- **Type check:** `PAGODA_LITE=1 uv run mypy .` shows all current diagnostics.
  CI runs `uv run python tools/mypy_ratchet.py --base-ref <git-ref>` and fails
  only when the diagnostic multiset grows relative to that revision. It uses
  the current checkout's mypy configuration and dependencies for both runs.
  This is a source-regression gate: configuration or toolchain changes can
  alter both measurements and may cancel out diagnostic changes. Git-detected
  file renames are normalized before comparison.
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

### API Client Release Workflow (auto-publish on merge to master)

The TypeScript client at `apiclient/typescript-fetch/` is published to GitHub
Packages as `@dmm-com/airone-apiclient-typescript-fetch`. CI installs the
*published* version via `npm ci`; `npm run link:client` is local-development
only and does not affect CI. Therefore any FE change that depends on a new
API field/endpoint requires a release-and-bump cycle, and **CI will fail
between steps 1 and 2 — this is expected, not a regression.**

Publishing is automated by `.github/workflows/release-apiv2-client.yml`,
which runs **on push to `master`** (no `pull_request_target`, no label). It
fires when a merge touches files that can change the generated OpenAPI spec
(`**/api_v2/**/*.py`) or the client `package.json`. The workflow regenerates
the spec/client from the merged code and publishes only when the version in
`apiclient/typescript-fetch/package.json` is not already on the registry —
so API changes merged without a version bump are a no-op (skipped), not a
failure.

1. In your PR, bump the version in `apiclient/typescript-fetch/package.json`
   (e.g. `0.28.1` → `0.28.2`) whenever you change the APIv2 schema. On merge
   to `master`, the workflow publishes the new version to GitHub Packages.
2. After the publish completes, open a follow-up PR that bumps the same
   version in the root `package.json` `optionalDependencies` and
   `package-lock.json` (e.g. `npm install
   @dmm-com/airone-apiclient-typescript-fetch@<new>` or manual edit). Once
   merged, CI resolves to the new version and FE build/test/lint pass.

Past examples: commits `696e8d1e` (root + lock bump after release) and
`1401e969` (apiclient-only bump on a separate PR).

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
