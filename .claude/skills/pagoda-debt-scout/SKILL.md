---
name: pagoda-debt-scout
description: Inspect Pagoda technical-debt candidates on demand using cognitive complexity and duplicate-code signals. Use after a feature change, before modifying a complex area, or when asked to find safe refactoring opportunities. Do not use as a routine CI or completion gate.
---

# Pagoda Debt Scout

Use the scanners as evidence for investigation, not as an instruction to reduce scores blindly. The desired outcome is at most three concrete maintenance tasks, or a reasoned conclusion that no change is worthwhile.

## Choose the scope

- For a repository inventory, run `npm run debt:report`.
- For machine-readable Python findings, run `npm run debt:complexity:python:json`; read `.cache/debt/complexipy` and apply the threshold during triage because this inventory contains all functions.
- For a feature or branch, resolve the actual base revision first. Prefer the PR base or its merge base over a fixed branch name.
- For an already merged feature, record the feature base, merge commit, and current revision. Check later commits before treating the historical file location as a current candidate.
- For new duplicate blocks, run `npx jscpd --config .jscpd.json --baseline-from-ref <base-ref> --reporters json --output .cache/debt/jscpd-diff .`.
- For changed frontend files, run `npx biome lint --javascript-linter-enabled=true --only=complexity/noExcessiveCognitiveComplexity --changed --since=<base-ref> --max-diagnostics=none --no-errors-on-unmatched frontend/src e2e`.

Biome's changed mode selects files, not newly introduced diagnostics. Complexipy's CLI diff output includes low-value entries and is not a ready-made task list. Compare the relevant functions before and after the base revision when an exact regression claim matters.

Record the base revision, current revision, tool versions, and scan time with the findings. If an existing report's provenance is unknown or its configuration differs, use it only as a hint and rerun before making a regression claim. A jscpd `isNew` value is meaningful only for the baseline used by that scan.

## Triage findings

Prioritize signals in this order:

1. The same recent feature increases complexity and creates duplicate logic.
2. A new function exceeds cognitive complexity 15.
3. An existing function ends above 15 and increases by at least 5.
4. A duplicate block represents a business rule that future changes would otherwise require editing in multiple places.
5. A complex function is about to be changed for another reason and has a separable responsibility.

Group overlapping clone pairs into one maintenance task. Separate production code from tests. Treat imports, type declarations, UI boilerplate, fixtures, and parallel API contract tests as low-priority until their maintenance cost is demonstrated.

For each proposed task, inspect callers, semantic differences, and relevant tests. Never infer that a duplicate was AI-generated from the duplicate alone.

## Decide whether to change code

Scanning must not change tracked source. The commands above write ignored reports under `.cache`; if the task prohibits all filesystem writes, inspect existing reports and source instead. Refactor only when the user requested optimization or the active implementation task clearly includes it.

When refactoring:

- Keep the change to one responsibility and one reviewable patch.
- Preserve caller-specific behavior instead of forcing superficially similar code into one abstraction.
- Add or strengthen characterization tests before changing poorly covered behavior.
- Run the smallest relevant tests and static checks, then report the before/after complexity or duplication evidence.
- Prefer no change when the abstraction would be harder to explain than the duplication.

Do not change CI, hooks, public APIs, ACL behavior, persistence semantics, or test coverage policy without explicit authorization. Do not commit, push, or merge unless the user requests it.

## Report

Return no more than three candidates. For each candidate include:

- location and detected signal;
- why it creates maintenance cost;
- semantic differences that must remain;
- available regression tests;
- estimated impact, risk, and effort;
- recommendation: refactor, investigate, intentionally retain, or delete after reference analysis.

Record intentional or deferred findings by stable function or normalized-fragment identity when the surrounding workflow provides a decision log. Do not repeatedly propose an unchanged rejected candidate.
