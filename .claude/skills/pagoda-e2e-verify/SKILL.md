---
name: pagoda-e2e-verify
description: |
  Browser-driven integration testing of Pagoda/AirOne (FE+BE combined). Use when asked to "verify in the browser", "test the UI", "check if it works", "do a smoke test", "manual test", "e2e test", "integration test", "run through the UI", or when finishing a feature and wanting to confirm it works end-to-end. Also trigger on Japanese phrases like "動作確認", "ブラウザで確認", "画面で試して", or any variation of manual/visual verification. Determines what to test from the current git diff context and drives browser automation to navigate pages, fill forms, click buttons, and verify results.
---

# Pagoda E2E Verification

Browser-driven manual testing of Pagoda/AirOne. Analyzes current changes, selects relevant test scenarios, and drives the UI via browser automation to verify everything works.

## Phase 1: Pre-checks

Run all checks before testing. Stop and guide the user if any fail.

### 1.1 Browser Tool

Check in priority order. Use the first available:

```bash
# Priority 1: agent-browser (preferred — session-based, configured in this project)
agent-browser --version

# Priority 2: playwright CLI
npx playwright --version

# Priority 3: playwright-mcp (available as MCP tool if configured)
```

All instructions below assume `agent-browser`. Adapt if falling back to another tool.

### 1.2 Backend Health

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v2/
```

If not 200/301/302:
1. Ask the user whether they want you to start the backend, or if they will start it themselves
2. If the user agrees, run `uv run python manage.py runserver 0.0.0.0:8000` in the background and wait a few seconds for it to be ready
3. Do NOT stop the entire verification — proceed with Phase 2 (change analysis) while waiting, then retry the health check before Phase 3

### 1.3 Frontend Build Freshness

Check if `static/js/ui.js` exists and is reasonably recent relative to frontend source changes:

```bash
ls -la static/js/ui.js
```

If the file is missing or you suspect it is stale (e.g., the user just changed frontend code), warn:
> Frontend bundle may be stale. Run `npm run build` or start `npm run watch`.

### 1.4 Docker Services

```bash
docker compose ps --format json 2>/dev/null | head -20
```

Verify mysql, elasticsearch, and rabbitmq are running. If not:
> Docker services are not all running. Start them with: `docker compose up -d mysql elasticsearch rabbitmq`

### 1.5 Test User

Attempt login with the default test credentials (`admin` / `password`). If login fails, tell the user:
> Test user does not exist. Create it with: `tools/register_user.sh admin -p password -s`

## Critical Features (Priority Order)

Some features are more important than others due to their impact on data integrity, security, and daily usage. When time is limited or when deciding test depth, prioritize accordingly:

1. **Entity schema definition (3.1)** — Adding/changing/deleting attributes affects the entire data structure downstream. A broken entity schema can corrupt all entries. Test thoroughly: create with multiple attribute types, edit existing attributes, verify attribute type constraints.
2. **Entry CRUD (3.2)** — The most frequently used operation in daily workflows. Test the full lifecycle: create, edit, copy, delete, restore. Pay special attention to attribute value rendering and form submission for each attribute type.
3. **Advanced search (3.3)** — Relies on Elasticsearch indexing and is a primary information access path. Fragile due to ES sync timing. Always verify that newly created/edited entries appear in search results.
4. **ACL / Permissions (3.4)** — Security-critical. A broken ACL can expose restricted data or block legitimate access. When ACL-related code changes, verify both grant and deny paths.

For full smoke tests, always run these four areas with deeper coverage (including negative tests and edge cases) before moving to lower-priority sections like User/Group/Role management, Jobs, Triggers, and Categories.

## Phase 2: Determine What to Test

### 2.1 Gather Changes

```bash
# Uncommitted changes
git diff HEAD --name-only

# Branch changes (if no uncommitted changes)
git diff main...HEAD --name-only 2>/dev/null || git diff master...HEAD --name-only 2>/dev/null
```

### 2.2 Change-to-Test Mapping

Map changed file paths to test scenarios. Run all matching sections. Always include Login (3.0).

| Changed files match | Test scenarios |
|---|---|
| `entity/**`, `frontend/src/**/entity/**`, `frontend/src/pages/Entity*` | Entity CRUD (3.1) |
| `entry/**`, `frontend/src/**/entry/**`, `frontend/src/pages/Entry*` | Entry CRUD (3.2) |
| `acl/**`, `frontend/src/**/acl/**` | ACL (3.4) |
| `user/**`, `frontend/src/**/user/**` | User management (3.5) |
| `group/**`, `frontend/src/**/group/**` | Group management (3.5) |
| `role/**`, `frontend/src/**/role/**` | Role management (3.5) |
| `frontend/src/pages/AdvancedSearch*`, `airone/lib/elasticsearch*` | Search (3.3) |
| `job/**`, `frontend/src/**/job/**` | Job list (3.6) |
| `trigger/**`, `frontend/src/**/trigger/**` | Trigger management (3.7) |
| `category/**`, `frontend/src/**/category/**` | Category management (3.8) |
| `frontend/src/components/common/**`, `frontend/src/routes/**` | Smoke: Login + Entity list + Entry list |
| `webhook/**` | Entity edit (webhook section in 3.1) |
| `api_v1/**`, `api_v2/**` | Smoke test of affected domain |
| No changes detected | Full smoke test (all sections, happy path only) |

## Phase 3: Test Scenarios

### Browser Interaction Pattern

For every page interaction, follow this cycle:
1. **Act** — navigate, click, or fill
2. **Wait** — `wait --load networkidle` after navigation, or `wait <selector>` for dynamic content
3. **Snapshot** — `snapshot -i` to see interactive elements (use `-C` to include clickable elements when exploring)
4. **Verify** — check expected content in the snapshot or via `get text <selector>`

Always use a named session to preserve login cookies:
```bash
agent-browser --session e2e open <url>
agent-browser --session e2e wait --load networkidle
agent-browser --session e2e snapshot -i
```

On failure, take a screenshot for debugging:
```bash
agent-browser --session e2e screenshot /tmp/pagoda_e2e_error.png
```

### MUI Component Interaction

Pagoda uses Material-UI. Key patterns:

- **TextField**: `fill "#field-id" "value"` or `fill "input[name='fieldname']" "value"`
- **Select**: `click "#selectId"` then `click` the desired menu item from the snapshot
- **Autocomplete**: `fill ".MuiAutocomplete-input" "search"`, wait, then click the option
- **Checkbox**: `click "[data-testid='checkboxId']"` or click by snapshot ref
- **Button**: `click "button[type='submit']"` or find by text "保存" in snapshot
- **Snackbar** (success/error): `wait ".notistack-SnackbarContainer"` then `get text ".notistack-SnackbarContainer"`

### 3.0 Login

```bash
agent-browser --session e2e open http://localhost:8000/auth/login/
agent-browser --session e2e wait --load networkidle
agent-browser --session e2e snapshot -i
agent-browser --session e2e fill "#username" "admin"
agent-browser --session e2e fill "#password" "password"
agent-browser --session e2e click "button[type='submit']"
agent-browser --session e2e wait --load networkidle
agent-browser --session e2e get url
```

Verify: URL is `http://localhost:8000/ui/` (dashboard). If login fails, stop and report.

**Negative test** (optional, run if auth-related changes detected):
- Fill wrong password, submit, verify error message appears.

### 3.1 Entity CRUD

**Create:**
1. Navigate to `http://localhost:8000/ui/entities/new`
2. Snapshot to identify form fields
3. Fill `#entity-name` with `"E2E_TestEntity"`
4. Add at least one attribute — find the add-attribute button in the snapshot, click it, fill attribute name (e.g., "test_attr"), verify type defaults to string
5. Click submit ("保存")
6. Verify: redirected to entry list or success snackbar

**Verify in list:**
1. Navigate to `http://localhost:8000/ui/entities`
2. Verify "E2E_TestEntity" appears

**Edit:**
1. Click the entity to open edit page
2. Add another attribute or change the entity note
3. Save and verify

**Delete:**
1. From entity list, find the more-actions menu for E2E_TestEntity
2. Click delete, confirm in dialog
3. Verify entity is removed from list

### 3.2 Entry CRUD

Prerequisite: An entity exists. Note its ID from the URL after creating it in 3.1.

**Create:**
1. Navigate to `http://localhost:8000/ui/entities/<entityId>/entries/new`
2. Snapshot to identify form fields
3. Fill entry name (look for name input field) with `"E2E_TestEntry"`
4. Fill attribute values as appropriate for the attribute types
5. Submit and verify

**View details:**
1. Navigate to `http://localhost:8000/ui/entities/<entityId>/entries`
2. Verify "E2E_TestEntry" appears in the list
3. Click to view details

**Edit:**
1. Open entry edit page
2. Change the entry name or an attribute value
3. Save, verify changes persist on reload

**Copy:**
1. From entry list, find copy action for the entry
2. Confirm the copy
3. Verify both original and copy exist

**Delete & Restore:**
1. Delete the entry from the list (more-actions menu → delete → confirm)
2. Verify entry is removed
3. Navigate to `http://localhost:8000/ui/entities/<entityId>/restore`
4. Find and restore the deleted entry
5. Verify it reappears in the entry list

### 3.3 Search

**Simple search:**
1. From dashboard or header, find the search input
2. Type "E2E_TestEntry"
3. Submit and verify results appear

**Advanced search:**
1. Navigate to `http://localhost:8000/ui/advanced_search`
2. Select entity from autocomplete
3. Configure attribute filters if applicable
4. Execute search
5. Verify results page shows matching entries

### 3.4 ACL/Permission Management

1. Navigate to ACL page for a test entity: `http://localhost:8000/ui/acl/<objectId>`
2. Snapshot the permission form
3. Modify a permission setting (e.g., change default permission level)
4. Save and verify changes persist

### 3.5 User/Group/Role Management

**User:**
1. Navigate to `http://localhost:8000/ui/users`
2. Verify user list loads
3. Optionally create a test user via `http://localhost:8000/ui/users/new`

**Group:**
1. Navigate to `http://localhost:8000/ui/groups`
2. Verify group tree loads
3. Optionally create a test group

**Role:**
1. Navigate to `http://localhost:8000/ui/roles`
2. Verify role list loads
3. Optionally create a test role

### 3.6 Job List

```bash
agent-browser --session e2e open http://localhost:8000/ui/jobs
agent-browser --session e2e wait --load networkidle
agent-browser --session e2e snapshot
```

Verify: Job list page loads without errors.

### 3.7 Trigger Management

1. Navigate to `http://localhost:8000/ui/triggers`
2. Verify list loads
3. Navigate to `http://localhost:8000/ui/triggers/new`
4. Snapshot to understand the form structure
5. Fill trigger conditions and actions if testing this area
6. Save and verify

### 3.8 Category Management

1. Navigate to `http://localhost:8000/ui/categories/list`
2. Verify list loads
3. Navigate to `http://localhost:8000/ui/categories/new`
4. Fill category name, select entities
5. Save and verify

## Phase 4: Cleanup & Report

### Cleanup

Delete test data created during the session (entities, entries, users) to avoid polluting the dev environment. Navigate to each item and delete through the UI, or use the API:

```bash
curl -X DELETE http://localhost:8000/entity/api/v2/<id>/ \
  -H "Content-Type: application/json" \
  -H "Cookie: <session-cookie>"
```

### Close Session

```bash
agent-browser --session e2e close
```

### Report

Summarize results in this format:

```
## E2E Verification Results

**Changes tested:** <what changed and what was tested>
**Browser tool:** agent-browser
**Base URL:** http://localhost:8000

| Scenario | Status | Notes |
|----------|--------|-------|
| Login | PASS/FAIL | ... |
| Entity create | PASS/FAIL | ... |
| Entry create | PASS/FAIL | ... |
| ... | ... | ... |

**Issues found:**
- <description of any bugs or unexpected behavior>

**Screenshots:** (on failure)
- /tmp/pagoda_e2e_error.png
```

## Tips for Effective Manual Testing

These are the things a QA engineer would pay attention to:

- **Form validation**: Try submitting empty required fields. Verify inline error messages appear.
- **Data persistence**: After creating/editing, reload the page and verify data is still there.
- **Navigation consistency**: Use the browser back button, breadcrumbs, and direct URL access to verify routing works.
- **Permission boundaries**: If ACL is set, verify that restricted users cannot see/edit restricted items.
- **Edge cases for attribute types**: Test with special characters in string fields, boundary values for numbers, various date formats.
- **Concurrent state**: If Celery jobs are involved (import/export), verify the job list updates and completes.
- **Error recovery**: After a failed operation (e.g., duplicate entity name), verify the form remains usable and shows a clear error.
- **Responsive feedback**: Verify snackbar notifications appear for success/error, and loading states are shown during API calls.
