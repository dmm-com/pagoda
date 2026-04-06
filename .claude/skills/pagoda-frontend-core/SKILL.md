---
name: pagoda-frontend-core
description: |
  Development guide for Pagoda/AirOne frontend (React + TypeScript + MUI) core. Use when developing or modifying page components, shared components, hooks, services, routing, and API clients under frontend/src/ (excluding plugins/). Trigger on requests like "fix the component", "add a page", "create a hook", "fix the frontend", "change the UI", "modify the screen", or any frontend development task. Also use when frontend changes are needed due to backend API modifications.
---

# Pagoda Frontend Core Development Guide

The Pagoda frontend is built with React 19 + TypeScript 5.x + Material-UI 6.x. Data fetching uses SWR, and form validation uses React Hook Form + Zod.

## Development Workflow

### 1. Write Code

**Directory structure:**
```
frontend/src/
  ├── pages/          # Page components (mapped to routes)
  ├── components/     # Reusable components (feature-based subdirectories)
  │   ├── common/     # Shared UI (Header, SearchBox, Table, Modal)
  │   ├── entity/     # Entity-related
  │   ├── entry/      # Entry-related (entryForm/ for form widgets)
  │   └── ...         # acl, category, group, job, role, trigger, user
  ├── hooks/          # Custom hooks
  ├── services/       # Business logic and utilities
  ├── repository/     # API client (AironeApiClient)
  ├── routes/         # Routing (Routes.ts, AppRouter.tsx)
  ├── i18n/           # Internationalization
  └── plugins/        # Plugin system (covered by separate skill)
```

**Writing components:**
- Use functional components + hooks (class components are discouraged)
- Style with Material-UI `styled()` (no CSS modules or Tailwind)
- File names in PascalCase (`EntityListPage.tsx`)
- Use barrel exports (`index.ts`) for module directories
- Do not use default exports

**Data fetching patterns:**
```typescript
// SWR pattern (recommended)
const { data, error } = usePagodaSWR(
  ["key", page, keyword],
  async () => await aironeApiClient.getEntities(page, keyword),
);

// Simple async pattern
const data = useAsync(async () => {
  return await aironeApiClient.getSearchEntries(query);
}, [query]);
```

**Form patterns:**
```typescript
// Zod schema definition
const schema = z.object({
  name: z.string().min(1, { message: "Required" }),
  // ...
});
type Schema = z.infer<typeof schema>;

// React Hook Form
const { control, setValue } = useForm<Schema>({
  resolver: zodResolver(schema),
  mode: "onBlur",
  defaultValues,
});
```

**Routing:**
- Base path: `/ui/`
- Use path builder functions from `Routes.ts` (e.g., `entryDetailsPath(entityId, entryId)`)
- Entity-dependent routes use the `EntityAwareRoute` wrapper
- React Router v7 (v6 compatible)

**API client:**
- Import and use the `aironeApiClient` singleton
- Wraps the auto-generated OpenAPI client (`@dmm-com/airone-apiclient-typescript-fetch`)
- CSRF token retrieved from cookies via `getCsrfToken()`

### 2. Run Static Analysis

After code changes, all static analysis must pass.

```bash
# ESLint — TypeScript rules + import order + unused imports
npx eslint frontend/src/<changed-files>

# Auto-fix
npx eslint --fix frontend/src/<changed-files>

# Biome — formatter (2-space indent, 80-char width, double quotes, semicolons)
npx biome format frontend/src/<changed-files>

# Auto-fix
npx biome format --write frontend/src/<changed-files>

# Knip — unused export and dependency detection
npx knip

# Run all at once
npm run lint
```

**Key ESLint rules:**
- `no-explicit-any: "error"` — `any` type is forbidden
- `no-unused-imports: "error"` — unused imports must be removed immediately
- Import order: builtin → external → parent → sibling → index → object → type (alphabetical)
- MUI icons must use specific imports (import from subpaths)

**Biome formatting rules:**
- Indent: 2 spaces
- Line width: 80 characters
- Quotes: double (`"`)
- Semicolons: always
- Trailing commas: always
- Arrow function parentheses: always

### 3. Run Tests

**Frontend tests are run in full by default.** Unlike the backend, execution time is short enough for full runs.

```bash
# Full run (default)
npm run test

# Filter to specific test pattern
npm run test -- -t "test name pattern"

# Update snapshots
npm run test:update
```

**Writing tests:**
- Jest + `@testing-library/react`
- Wrap with `TestWrapper` for providers (SWRConfig, ThemeProvider, SnackbarProvider, MemoryRouter)
- API mocking: `jest.spyOn(aironeApiClient, "methodName").mockResolvedValue(...)`
- Test custom hooks with `renderHook()`
- Wrap async operations with `act()`
- Timezone: fixed at `TZ=UTC` (configured in package.json)

### 4. Verify Backend Integration

Frontend development also involves ensuring consistency with backend APIs.

**When API changes are involved:**
- Backend serializer changes → may require regenerating the API client
- Run `npm run generate:client` to regenerate the OpenAPI client
- Verify no type mismatches with TypeScript compilation

**Points to verify:**
- API request/response types match frontend type definitions
- UI display controls correspond to backend permission checks (ACL)
- Celery job integration (polling, etc.) works correctly

### 5. Quality Checklist

Before completing changes:
1. `npm run lint` — ESLint + Biome + Knip all pass
2. `npm run test` — all tests pass
3. `npm run build` — build succeeds
4. Comments are written in English
5. No `any` types used

## Important Notes

- State management uses React hooks + SWR only (no Redux or Context API)
- Styling uses MUI `styled()` only (no CSS modules or Tailwind)
- Forms follow the React Hook Form + Zod pattern
- Route paths use builder functions from `Routes.ts` (no hardcoding)
- Use `aironeApiClient` methods directly; do not write raw `fetch` calls
