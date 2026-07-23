# Frontend testing strategy

The frontend test gate is designed to support large refactors without relying
on snapshot-only confidence or happy-path rendering checks.

## Required layers

1. Pure services and schemas: boundaries, invalid input, and error mapping.
2. Hooks: loading, success, failure, revalidation, and cleanup behavior.
3. Components: rendering, user interaction, disabled and validation states,
   request success and failure, and stable form values.
4. Pages: route parameters, permissions, loading and error boundaries, and the
   integration between API responses and child components.
5. Browser tests: critical workflows, accessibility, browser errors, and live
   API contracts where mocks cannot provide sufficient evidence.

Snapshot assertions may supplement behavioral assertions, but a snapshot alone
does not prove component behavior.

## Coverage gate

`npm run test` collects coverage from all production TypeScript and TSX files
under `frontend/src`, including files that no test imports. Test files, barrel
exports, and `TestWrapper.tsx` are excluded from the production denominator.

The global thresholds are the current ratchet, not the final target. Raise them
as uncovered areas are addressed; never lower them to make a change pass.
Components that receive focused hardening should get their own thresholds in
`tools/frontendCoverageReporter.cjs`, so a high global average cannot hide a
local regression. These checks are kept outside Jest's `coverageThreshold`
file entries because Jest removes matched files from its global denominator.

Current staged targets are:

- Stage 1: lines/statements 75%, branches 55%, functions 60%.
- Stage 2: lines/statements 80%, branches 65%, functions 70%.
- Stage 3: critical forms, API-backed pickers, ACL, and routing at 90% lines and
  80% branches, with explicit request-failure tests.

## Test quality checklist

- Assert user-visible behavior and form or navigation outcomes.
- Cover empty, invalid, disabled, loading, failure, and recovery states where
  the component supports them.
- Verify API call arguments and prevent duplicate or stale requests.
- Await asynchronous UI updates; React `act` warnings are test defects.
- Keep tests deterministic under `TZ=UTC` and avoid timing-based sleeps.
- Use role, label, placeholder, or visible text queries before DOM structure.
- Treat unexpected `console.error` and `console.warn` output as cleanup work;
  expected error-boundary logs should be scoped and asserted explicitly.
