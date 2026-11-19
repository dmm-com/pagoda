---
title: Mutation testing
weight: 35
---

Mutation testing checks whether the existing test suite detects a small, controlled change in behavior. Pagoda's local runner uses `@mizchi/mutator` with Vitest. It is useful for boundary values, state transitions, data transformations, and compatibility with stored settings.

## Run it locally

Install frontend dependencies with `npm ci` as usual. Then switch to Node 24 or later on macOS or Linux and install the pinned mutation tool once per checkout.

```sh
npm ci --prefix tools/mutation --ignore-scripts
npm run test:mutation -- --since HEAD
```

`HEAD` covers local uncommitted changes. Set `--since` to the target branch or a base commit to cover changes already committed on your branch. For a test-only edit, the runner also considers mutants covered by or imported from changed tests. Its Git input is limited to frontend sources, tests, and Vitest configuration. See the effective scope printed by the command.

The default source scope is the job status notice, import preview aggregation and polling, and advanced search column order. To check a different feature or a test for that feature, give the production source path. Repeat `--include` for multiple files. Keep the same set when rechecking so the runner can reuse the snapshot.

```sh
npm run test:mutation -- --since HEAD --include frontend/src/services/JobUtil.ts
npm run test:mutation -- --only "$MUTANT_ID" --include frontend/src/services/JobUtil.ts
```

Use `--all` instead of `--since` to examine the whole selected scope or seed a snapshot before editing tests. For a baseline comparison, seed the snapshot at the baseline revision with the same toolchain and source scope. The default time budget is 120 seconds. A separate deadline stops the runner and its worker processes after the budget plus 60 seconds. Reports are written to a new directory under `.mutator/pagoda/runs/` on each run. The command prints the directory, status counts, and up to three gaps. Use `agent.json` for relevant test names and `run.log` for baseline, timeout, or setup failures.

## Use the feedback in an agent task

1. State the expected behavior before implementing it. Use an issue, an API contract, a persisted fixture, or a user-visible outcome as the source of the expectation. Run the ordinary tests first.
2. Run the mutation check and pick up to three gaps that matter to the change. For `notReached`, add a scenario that reaches the code. For `notInfected`, choose an input that separates the two versions. For `notDetected`, check both the input and what the test observes. A 301-second fixture, for example, cannot distinguish `>= 300` from `> 300`.
3. Edit the test to observe that behavior, rerun the ordinary test, and recheck with `--only`. Report the observed failure and the mutant ID. Check the reported test name or reproduce a failure on a temporary copy when the reason for detection is unclear. Review any proposed equivalent mutant with an explanation of the observable behavior.

A baseline failure exits with code `4` and requires fixing the test run first. A hard deadline exits with code `124`. The tool reports survivors and detection regressions as review findings. A run with no selected mutants, `Pending` entries, timeouts, or runner warnings represents limited evidence. Hold off on interpreting missing coverage until you check the source scope and the runner warnings. The standard frontend build, tests, and coverage checks run through their existing commands.

## Where to run it

| Where | When to use it |
| --- | --- |
| Local coding agent | Default for an affected behavior. Feedback arrives while the author can still change the fixture or expectation. |
| PR review | A second reader can validate the behavior and reject tests that mirror the implementation. Once local use has stabilized, consider publishing a few actionable findings from a Node 24 job for the same scope. |
| Periodic run | Use a larger budget to discover gaps in stable legacy code or warm a baseline before test refactors. Scope the runs to a feature and track the unresolved findings. |

Start with review feedback. Evaluate usefulness, runtime, reproducibility, and detection of known regressions held out from the agent before using a result as a merge criterion. A single global score encourages tests for easy mutants and combines results from very different behaviors. For repository-specific cost data, record whether a run used a warm snapshot and how many mutants remained pending.

The frontend runner covers in-process Vitest tests. Use browser tests for layout and interaction that depends on a real browser. For Django, `tools/lite.sh test <target>` can verify a deliberately changed behavior in an isolated checkout. Use the real services when behavior depends on the database, search engine, or task worker.

[Mutation-guided LLM test generation](https://arxiv.org/abs/2506.02954)

[Incremental mutation testing in code review](https://arxiv.org/abs/2102.11378)
