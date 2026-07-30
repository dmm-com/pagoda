---
name: pagoda-n-plus-one
description: Detect, diagnose, repair, and verify Django N+1 queries in Pagoda/AirOne. Use when asked to find N+1 queries, reduce query growth, investigate repeated SQL, optimize Django or DRF relation loading, add query-count regression coverage, or produce a performance-remediation report.
---

# Pagoda N+1 Autofix

Turn a suspected N+1 into a reproduced query-growth regression, a bounded fix, and a reviewable
before/after report. Treat detector output as a candidate signal, not proof by itself.

## Run the detector

Choose the smallest API test module that exercises a list or nested serializer. Run without
parallelism so each request remains attributable:

```bash
AIRONE_NPLUSONE_REPORT=.artifacts/nplusone-before.json \
uv run python manage.py test <test-label> --parallel=1 \
  --testrunner=airone.lib.nplusone.NPlusOneDiscoverRunner
```

The runner inspects each HTTP request, groups repeated SELECT shapes, and records source locations
and repair hints. Default threshold is 5 identical shapes. Set `AIRONE_NPLUSONE_MIN_REPEATS` only
when a smaller fixture cannot expose query growth. Never lower it below 2.

If the selected test has too few parent rows, add a focused regression test that requests a small
fixture and a larger fixture. Compare query counts or candidate occurrences and prove growth before
editing production code.

## Diagnose before editing

For every candidate:

1. Open the reported source and the queryset that supplies its objects.
2. Confirm query count grows with parent or child rows. Ignore constant repeated queries unless they
   are still materially expensive.
3. Identify the exact relation, filtering, ordering, permission, and active-row semantics.
4. Record the before counts from both fixture sizes and preserve the detector JSON.

Prefer one proven candidate per fix. Do not refactor unrelated query code merely because it appears
near the reported line.

## Repair the query shape

- Use `select_related` for one-valued foreign-key or one-to-one relations.
- Use `prefetch_related` for many-valued relations when the unfiltered related manager is correct.
- Use `Prefetch` with a filtered/ordered queryset and `to_attr` when serializer semantics differ
  from the default manager. Consume `to_attr` directly; calling the related manager again discards
  the prefetch benefit.
- Replace per-row `.get()`, `.exists()`, or `.count()` with bulk queries, annotations, or id-keyed
  maps when relation prefetching does not model the lookup.
- Keep ACL and active-row filters unchanged. Avoid loading an unbounded relation solely to save a
  small number of queries.

Add a regression test whose larger fixture would fail with the original implementation. Prefer a
growth assertion over one brittle absolute query count, allowing only a small constant delta for
authentication and permission work.

## Verify and self-review

Run the focused test in hard-gate mode, then the affected app tests and static checks:

```bash
AIRONE_NPLUSONE_MODE=fail AIRONE_NPLUSONE_REPORT=.artifacts/nplusone-after.json \
uv run python manage.py test <test-label> --parallel=1 \
  --testrunner=airone.lib.nplusone.NPlusOneDiscoverRunner
uv run python manage.py test <affected-app>
uv run ruff check <changed-python-files>
uv run mypy <changed-modules> --config-file=pyproject.toml
```

Review the diff for preserved ordering, filters, ACL behavior, pagination, response shape, database
alias behavior, and memory amplification. Re-run the before/after fixture comparison after the fix;
a green detector alone is insufficient if the request is no longer exercising the relation.

## Produce the remediation report

Render the machine-readable evidence and then add the diff summary, regression test, self-review
result, and any residual candidates:

```bash
python .claude/skills/pagoda-n-plus-one/scripts/render_report.py \
  --before .artifacts/nplusone-before.json \
  --after .artifacts/nplusone-after.json \
  --output .artifacts/nplusone-remediation.md
```

Report exact commands and counts. Mark uncertain candidates as unverified rather than claiming they
were fixed.
