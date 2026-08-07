---
title: Lite mode (containerless development)
weight: 25
---

# Lite mode

Pagoda normally runs against MySQL, Elasticsearch and RabbitMQ. That is the
right shape for production and CI, and the wrong shape for the ten-second edit
/ run / edit loop -- especially when several `git worktree` checkouts are being
worked on at once and all of them want port 3306.

`tools/test_local.sh --sqlite` already removes the MySQL container for test
runs. Lite mode goes further in three ways: it removes the Elasticsearch and
RabbitMQ containers too, it covers the dev server rather than only tests, and
it closes the MySQL-vs-SQLite behavioural gaps that `--sqlite` documents as
caveats. The two share the same SQLite backend, so those fixes apply to
`--sqlite` as well.

Lite mode replaces the three services with in-process equivalents:

| Service       | Production        | Lite mode                                     |
| ------------- | ----------------- | --------------------------------------------- |
| Database      | MySQL             | SQLite, one file per checkout                 |
| Search        | Elasticsearch     | in-process index (`airone/lib/es_inmemory.py`)|
| Task broker   | RabbitMQ + worker | kombu `memory://`, or inline execution        |

Nothing needs to be installed or started. `docker` is not involved.

## What it costs and what it buys

1383 tests, same tree, same per-app split, run back to back on a 12-core
macOS laptop at load ~7. Serial unless noted. The failures were identical in
every configuration, so none of these substitutions changed behaviour.

| configuration | containers | total |
| --- | ---: | ---: |
| MySQL + Elasticsearch + RabbitMQ | 3 | 1175s |
| `test_local.sh --sqlite` (SQLite + real ES) | 2 | 222s |
| SQLite + in-process search | 1 | 165s |
| lite | 0 | 169s |
| lite, `tools/lite.sh test` | 0 | 82s |

Read that as four separate effects, because they are not equally interesting:

| step | saved | share |
| --- | ---: | ---: |
| MySQL → SQLite | 953s | 81% |
| real ES → in-process | 57s | 5% |
| RabbitMQ → `memory://` | 0s | 0% |
| serial → parallel apps | 87s | 7% |

Three things follow. **The big win is SQLite, and `test_local.sh --sqlite`
already had it** -- lite mode's marginal gain over that is 222s → 82s (2.7x),
from dropping the search container and from being able to parallelise at all.
**Dropping RabbitMQ buys no time whatsoever**; the suite queues tasks nobody
consumes, so the broker was never on the critical path. Its removal is about
one less thing to run, not speed.

**These ratios are near their upper bound here.** The dominant cost is
per-query round-trip latency, and macOS reaches its containers through a VM
(~2.4ms/query, per `tools/test_local.sh`'s own notes). On Linux with a native
MySQL -- CI, most servers -- the same substitution saves proportionally less.
The container-free and per-worktree properties do not depend on the platform;
the multipliers do.

Finally, `entry` alone accounts for 56% of the container-mode total, and its
cost is dominated by search writes: `register_es()` issues an `es.refresh()`
after every single document (~35ms each). That is worth looking at
independently of lite mode, since it also runs in production.

## Quick start

```
$ tools/lite.sh init          # create the SQLite DB and an admin/admin user
$ tools/lite.sh run           # dev server on this checkout's own port
$ tools/lite.sh test          # whole suite, one process per app, no containers
```

`tools/lite.sh info` prints everything this checkout derives from its path:

```
workspace        /path/to/worktrees/my-feature
slot             43
port             8043
state_dir        /path/to/worktrees/my-feature/.pagoda-lite
compose_project  pagoda-my-feature-43
container_ports  {'MYSQL': 3349, 'ES': 9243, 'RABBITMQ': 5715, ...}
```

Lite mode is opt-in and driven entirely by `PAGODA_LITE=1`, which `tools/lite.sh`
sets for you. Any `manage.py` command works with it directly:

```
$ PAGODA_LITE=1 uv run python manage.py test entry
```

## Parallel worktrees

Every path and port above is derived by hashing the checkout directory
(`airone/lib/devmode.py`), so two worktrees never collide:

* **HTTP port** -- `8000 + slot`, so both dev servers can run at once.
* **Database** -- `<checkout>/.pagoda-lite/pagoda.sqlite3`. Deleting a worktree
  deletes its data; no shared test database to corrupt.
* **Search index** -- named `airone-<checkout>-<slot>`, and in-process anyway.
* **Media files** -- `<checkout>/.pagoda-lite/media`.
* **Container names and ports** -- if you *do* start the full stack, do it via
  `tools/lite.sh compose up -d`, which sets `COMPOSE_PROJECT_NAME` and the
  per-slot host ports so several checkouts can each run their own stack.

Pin a specific value with `PAGODA_SLOT=7` when you want a memorable port.

## Running tests

`tools/lite.sh test` with no arguments runs **one process per Django app**.
This mirrors CI, which gives every app its own matrix job. It is not only
faster: a few apps leave process-global state behind (plugin registries, the
URL gate keeper), so running everything in a single process reports failures
that neither CI nor a real deployment would ever see.

Pass a target to run it directly in the foreground:

```
$ tools/lite.sh test entry.tests.test_service
```

**The concurrency budget is shared by every worktree of the repository**, via
lock directories under the common `.git`. This matters once more than one
agent or terminal is working in parallel: without it each run helps itself to
half the cores, and three of them together drive a 12-core laptop past load 40,
at which point everything -- including the runs themselves -- gets slower.
`PAGODA_TEST_JOBS` sets the budget; it defaults to cores minus two. A slot
whose owning process died is reclaimed automatically, so a killed run does not
strand capacity.

Per-app logs land in `.pagoda-lite/testlogs/`, alongside a `results.json`
summarising every app, its test count, duration and the names of any failing
tests -- so tooling does not have to scrape stdout.

Two footguns are handled rather than documented: migrations (which this project
generates rather than commits) are created when missing and regenerated when
the models have moved on, and if `custom_view` is not set up the runner says
up front which two apps are expected to fail for that reason alone.

## Fidelity: what lite mode reproduces, and what it does not

Lite mode is for iteration. CI remains the source of truth, and anything
touching search semantics, migrations or transaction behaviour deserves a run
against the real stack before it ships.

Three MySQL behaviours that code silently depends on **are** reproduced, by a
thin SQLite backend at `airone/db/backends/sqlite_pagoda/`:

* **Integer ranges.** Django derives `max_value` validators from the backend's
  declared ranges. Stock SQLite declares 64-bit, so an over-range value that
  MySQL rejects would be accepted, and the API would return a different error.
* **Case-insensitive text.** Pagoda's MySQL uses a `_ci` collation, so
  `name="lb"` finds `"LB"` and unique constraints fold case. Text columns are
  declared `COLLATE NOCASE` to match. Note that `NOCASE` only folds ASCII.
  This matters well beyond `__iexact`: plain `filter(name=...)` duplicate-name
  checks are scattered through the models and would silently stop catching
  `"Foo"` vs `"foo"` on a case-sensitive backend.
* **`__regex` case sensitivity.** MySQL's `REGEXP` follows the same collation,
  so `name__regex="^entity-"` matches `"Entity-1"` in production. Stock SQLite
  would not match it.

The SQLite connection runs in WAL mode with a 20-second busy timeout and
`IMMEDIATE` transactions, which is what keeps the threaded dev server and
inline job execution from tripping over `database is locked`. SQLite's
single-writer model is still a real constraint -- it is fine for dev-scale
work and is not a production configuration.

The search engine is faithful for a specific reason: every analysed field in
Pagoda's mapping uses the `keyword` analyzer, so there is no tokenizer or
stemmer to emulate -- `match` and `term` are whole-value equality. What it does
*not* reproduce:

* `_score` counts matching clauses rather than computing BM25. The orderings
  Pagoda relies on (an entry matched by name outranks one matched by attribute
  value) hold; a true relevance ranking does not.
* Field paths resolve structurally, so a query against a doubly-nested field
  matches from its parent scope where a real cluster would require an explicit
  inner `nested` clause. The engine is the more permissive of the two.
* Index settings and mappings are accepted and ignored.

Unsupported query clauses raise immediately rather than returning wrong
results, so a new query shape fails loudly instead of quietly.

## Mixing and matching

The three substitutions are independent, so you can escalate one at a time:

```
# in-process search, but the real MySQL from docker compose
$ PAGODA_LITE=1 AIRONE_MYSQL_MASTER_URL=mysql://airone:password@127.0.0.1:3349/airone \
      uv run python manage.py test entry

# SQLite, but a real Elasticsearch shared between worktrees
# (the index name already carries the checkout name, so they will not collide)
$ PAGODA_LITE=1 AIRONE_ES_BACKEND=http uv run python manage.py test entry
```

Relevant environment variables:

| Variable                     | Default in lite mode        | Purpose                                  |
| ---------------------------- | --------------------------- | ---------------------------------------- |
| `PAGODA_LITE`                | unset (off)                 | master switch                            |
| `PAGODA_SLOT`                | hash of checkout path       | pin the port/namespace                   |
| `PAGODA_PORT_BASE`           | `8000`                      | base for the dev-server port             |
| `PAGODA_STATE_DIR`           | `<checkout>/.pagoda-lite`   | where the DB, index and media live       |
| `AIRONE_MYSQL_MASTER_URL`    | the per-checkout SQLite file| point at a real database instead         |
| `AIRONE_ES_BACKEND`          | `inmemory`                  | `http` to use a real cluster             |
| `AIRONE_CELERY_EAGER`        | `0` (`1` under `lite.sh run`)| run tasks inline instead of queueing    |
| `PAGODA_TEST_JOBS`           | `4`                         | app-level test concurrency               |

## Jobs and Celery

The test suite is written against an environment where tasks are *queued and
never consumed* -- CI runs RabbitMQ but no worker. Lite mode reproduces that
with kombu's `memory://` transport, so `.delay()` neither blocks on a
connection nor runs inline, and job-status assertions behave as they do in CI.

The dev server wants the opposite: jobs should actually complete. So
`tools/lite.sh run` sets `AIRONE_CELERY_EAGER=1`, which executes tasks inline
in the request process. Creating a model or an item returns `202` and the work
has already happened by the time you look.

## Housekeeping

```
$ tools/lite.sh reindex   # rebuild the search index from the database
$ tools/lite.sh reset     # delete this checkout's DB, index, media and logs
```

The in-process index is mirrored to `.pagoda-lite/es/*.json` so it survives a
dev-server restart. Tests never persist it.
