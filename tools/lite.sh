#!/usr/bin/env bash
#
# Pagoda lite mode: run the app and its tests with no containers.
#
#   tools/lite.sh info      show this checkout's slot, port and state paths
#   tools/lite.sh status    show whether this checkout's dev server is up
#   tools/lite.sh init      create the SQLite DB and an admin user
#   tools/lite.sh run       start the dev server on this checkout's port
#   tools/lite.sh test ...  run the Django test suite (args passed through)
#   tools/lite.sh reindex   rebuild the search index from the database
#   tools/lite.sh reset     delete this checkout's DB, index and media
#   tools/lite.sh compose   docker compose, namespaced to this checkout
#
# Every path and port is derived from the checkout directory, so several git
# worktrees can run their own server and suite side by side without colliding.
# Test processes additionally share a repository-wide concurrency budget, so
# several agents running suites at once do not oversubscribe the machine.
# See docs/content/getting_started/lite_mode.md.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
REPO_ROOT="$PWD"

export PAGODA_LITE="${PAGODA_LITE:-1}"

# Prefer an in-checkout virtualenv, then the main checkout's, then uv.
if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
    PY=("$REPO_ROOT/.venv/bin/python")
elif [ -x "$(git rev-parse --git-common-dir 2>/dev/null)/../.venv/bin/python" ]; then
    PY=("$(git rev-parse --git-common-dir)/../.venv/bin/python")
else
    PY=(uv run python)
fi

lite_env() {
    "${PY[@]}" airone/lib/devmode.py --env
}

# Migration files are generated rather than committed (see .gitignore), so a
# fresh checkout has none and a rebased one may have stale ones. Both fail in
# ways that read as product bugs, so handle them here rather than in a comment.
ensure_migrations() {
    if ! ls entity/migrations/0*.py >/dev/null 2>&1; then
        echo ">>> generating migrations (none in this checkout)"
        "${PY[@]}" manage.py makemigrations >/dev/null
    fi
}

regenerate_migrations_if_stale() {
    if ! "${PY[@]}" manage.py makemigrations --check --dry-run >/dev/null 2>&1; then
        echo ">>> models changed since migrations were generated; regenerating"
        rm -f ./*/migrations/0*.py
        "${PY[@]}" manage.py makemigrations >/dev/null
    fi
}

# CI renames custom_view_sample to custom_view before running. Without that,
# two modules fail for reasons that have nothing to do with your change; say so
# rather than letting the next reader investigate it again.
note_custom_view() {
    if [ ! -d custom_view ] && [ -d custom_view_sample ]; then
        echo "note: custom_view is not set up (CI does 'mv custom_view_sample custom_view')."
        echo "      job.test_method_table and custom_view_sample failures are expected here."
    fi
}

case "${1:-info}" in
info)
    "${PY[@]}" airone/lib/devmode.py
    ;;

status)
    eval "$(lite_env)"
    "${PY[@]}" - "$PAGODA_PORT" "$PAGODA_STATE_DIR" <<'EOF'
import os
import socket
import sys

port, state = int(sys.argv[1]), sys.argv[2]
with socket.socket() as probe:
    probe.settimeout(0.3)
    up = probe.connect_ex(("127.0.0.1", port)) == 0
print("dev server   %s  http://127.0.0.1:%d/ui/" % ("UP  " if up else "down", port))


def size(path):
    if not os.path.exists(path):
        return "-"
    if os.path.isfile(path):
        return "%.1f MB" % (os.path.getsize(path) / 1e6)
    total = sum(
        os.path.getsize(os.path.join(root, f))
        for root, _, files in os.walk(path)
        for f in files
    )
    return "%.1f MB" % (total / 1e6)


print("database     %s" % size(os.path.join(state, "pagoda.sqlite3")))
print("search index %s" % size(os.path.join(state, "es")))
EOF
    ;;

init)
    ensure_migrations
    regenerate_migrations_if_stale
    "${PY[@]}" manage.py migrate --no-input
    # Pagoda overrides UserManager.create_user with its own signature, so the
    # stock create_superuser helper is not available here.
    "${PY[@]}" manage.py shell -c '
from user.models import User
if User.objects.filter(username="admin").exists():
    print("superuser admin already exists")
else:
    user = User(username="admin", email="admin@example.com", is_superuser=True, is_staff=True)
    user.set_password("admin")
    user.save()
    print("created superuser admin / admin")
'
    ;;

run)
    shift || true
    ensure_migrations
    eval "$(lite_env)"
    # Jobs need to actually complete without a Celery worker, so the dev
    # server (unlike the test suite) executes tasks inline.
    export AIRONE_CELERY_EAGER="${AIRONE_CELERY_EAGER:-1}"
    echo "Pagoda lite on http://127.0.0.1:${PAGODA_PORT}/ui/  (slot ${PAGODA_SLOT})"
    exec "${PY[@]}" manage.py runserver "127.0.0.1:${PAGODA_PORT}" "$@"
    ;;

test)
    shift || true
    ensure_migrations

    if [ "$#" -gt 0 ]; then
        exec "${PY[@]}" manage.py test --no-input "$@"
    fi

    regenerate_migrations_if_stale
    note_custom_view

    # No target given: run every app the way CI does -- one module per
    # process. CI's matrix gives each module its own job, and some modules
    # leave process-global state behind (plugin registries, URL gate keeper),
    # so a single combined process reports failures that CI never sees.
    # Separate processes also parallelise cleanly: each gets its own in-memory
    # SQLite database and its own in-process search index.
    #
    # The concurrency budget is shared with every other worktree of this
    # repository. Without that, N agents each running a suite at "half the
    # cores" is how a 12-core laptop reaches load 40 and every measurement
    # becomes noise.
    cores=$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)
    budget="${PAGODA_TEST_JOBS:-$(( cores > 3 ? cores - 2 : 2 ))}"
    lockdir="$(git rev-parse --git-common-dir)/pagoda-lite-jobs"
    mkdir -p "$lockdir"

    logdir="$REPO_ROOT/.pagoda-lite/testlogs"
    rm -rf "$logdir" && mkdir -p "$logdir/failed"

    # $1 is the PID that will own the slot. It has to be passed in: this runs
    # inside a command substitution, so $BASHPID here would be the short-lived
    # substitution subshell, and the reclaim check below would free the slot
    # again the instant it was taken.
    acquire_slot() {
        owner_pid="$1"
        while :; do
            for i in $(seq 1 "$budget"); do
                slot="$lockdir/$i"
                if mkdir "$slot" 2>/dev/null; then
                    echo "$owner_pid" >"$slot/pid"
                    echo "$slot"
                    return 0
                fi
                # Reclaim a slot whose owner died (killed run, crashed shell).
                owner=$(cat "$slot/pid" 2>/dev/null || echo "")
                if [ -n "$owner" ] && ! kill -0 "$owner" 2>/dev/null; then
                    rm -rf "$slot"
                fi
            done
            sleep 1
        done
    }

    modules=$(ls -d ./*/tests/ | sed 's|^\./||; s|/tests/||')
    for module in $modules; do
        (
            me=$BASHPID
            slot=$(acquire_slot "$me")
            trap 'rm -rf "$slot"' EXIT
            log="$logdir/${module}.log"
            if "${PY[@]}" manage.py test --no-input "$module" >"$log" 2>&1; then
                printf '  ok    %-18s %s\n' "$module" \
                    "$(grep -oE 'Ran [0-9]+ tests? in [0-9.]+s' "$log" | tail -1)"
            else
                touch "$logdir/failed/$module"
                printf '  FAIL  %-18s %s  -> %s\n' "$module" \
                    "$(grep -oE 'Ran [0-9]+ tests? in [0-9.]+s' "$log" | tail -1)" "$log"
            fi
        ) &
    done
    wait

    # A machine-readable summary, so an agent does not have to scrape stdout.
    "${PY[@]}" - "$logdir" >"$logdir/results.json" <<'EOF'
import json
import os
import re
import sys

logdir = sys.argv[1]
failed = set(os.listdir(os.path.join(logdir, "failed")))
modules = []
for name in sorted(os.listdir(logdir)):
    if not name.endswith(".log"):
        continue
    module = name[: -len(".log")]
    text = open(os.path.join(logdir, name), encoding="utf-8", errors="replace").read()
    ran = re.findall(r"Ran (\d+) tests? in ([\d.]+)s", text)
    modules.append(
        {
            "module": module,
            "ok": module not in failed,
            "tests": int(ran[-1][0]) if ran else None,
            "seconds": float(ran[-1][1]) if ran else None,
            "failures": re.findall(r"^(?:FAIL|ERROR): (\S+)", text, re.M),
            "log": os.path.join(logdir, name),
        }
    )
print(
    json.dumps(
        {
            "ok": not failed,
            "modules": modules,
            "tests": sum(m["tests"] or 0 for m in modules),
        },
        indent=2,
    )
)
EOF

    failed=$(ls -1 "$logdir/failed" | wc -l | tr -d ' ')
    echo "summary: $logdir/results.json"
    if [ "$failed" != "0" ]; then
        echo "$failed module(s) failed; logs in $logdir"
        exit 1
    fi
    echo "all modules passed"
    ;;

reindex)
    exec "${PY[@]}" tools/initialize_es_document.py
    ;;

reset)
    eval "$(lite_env)"
    echo "removing ${PAGODA_STATE_DIR}"
    rm -rf "${PAGODA_STATE_DIR}"
    ;;

compose)
    shift || true
    eval "$(lite_env)"
    # A per-checkout project name and port offset let several worktrees run
    # containers at once; see docker-compose.yml.
    export PAGODA_SLOT PAGODA_PORT COMPOSE_PROJECT_NAME
    exec docker compose "$@"
    ;;

*)
    sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
