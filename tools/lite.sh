#!/usr/bin/env bash
#
# Pagoda lite mode: run the app and its tests with no containers.
#
#   tools/lite.sh info      show this checkout's slot, port and state paths
#   tools/lite.sh init      create the SQLite DB and an admin user
#   tools/lite.sh run       start the dev server on this checkout's port
#   tools/lite.sh test ...  run the Django test suite (args passed through)
#   tools/lite.sh reindex   rebuild the search index from the database
#   tools/lite.sh reset     delete this checkout's DB, index and media
#   tools/lite.sh compose   docker compose, namespaced to this checkout
#
# Every path and port is derived from the checkout directory, so several git
# worktrees can run their own server and suite side by side without colliding.
# See docs/content/lite-mode.md.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
REPO_ROOT="$PWD"

export PAGODA_LITE="${PAGODA_LITE:-1}"

# Prefer an in-checkout virtualenv, then the repo root's, then uv.
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

case "${1:-info}" in
info)
    "${PY[@]}" airone/lib/devmode.py
    ;;

init)
    # Migrations are generated rather than committed in this project (see
    # .gitignore), so makemigrations has to run before migrate.
    "${PY[@]}" manage.py makemigrations
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
    eval "$(lite_env)"
    # Jobs need to actually complete without a Celery worker, so the dev
    # server (unlike the test suite) executes tasks inline.
    export AIRONE_CELERY_EAGER="${AIRONE_CELERY_EAGER:-1}"
    echo "Pagoda lite on http://127.0.0.1:${PAGODA_PORT}/ui/  (slot ${PAGODA_SLOT})"
    exec "${PY[@]}" manage.py runserver "127.0.0.1:${PAGODA_PORT}" "$@"
    ;;

test)
    shift || true
    if [ "$#" -gt 0 ]; then
        exec "${PY[@]}" manage.py test --no-input "$@"
    fi

    # No target given: run every app the way CI does -- one module per
    # process. CI's matrix gives each module its own job, and some modules
    # leave process-global state behind (plugin registries, URL gate keeper),
    # so a single combined process reports failures that CI never sees.
    # Separate processes also parallelise cleanly: each gets its own
    # in-memory SQLite database and its own in-process search index.
    modules=$(ls -d ./*/tests/ | sed 's|^\./||; s|/tests/||')
    concurrency="${PAGODA_TEST_JOBS:-4}"
    logdir="$REPO_ROOT/.pagoda-lite/testlogs"
    rm -rf "$logdir" && mkdir -p "$logdir/failed"

    running=0
    for module in $modules; do
        (
            log="$logdir/${module}.log"
            if "${PY[@]}" manage.py test --no-input "$module" >"$log" 2>&1; then
                printf '  ok    %-14s %s\n' "$module" \
                    "$(grep -oE 'Ran [0-9]+ tests? in [0-9.]+s' "$log" | tail -1)"
            else
                touch "$logdir/failed/$module"
                printf '  FAIL  %-14s %s  -> %s\n' "$module" \
                    "$(grep -oE 'Ran [0-9]+ tests? in [0-9.]+s' "$log" | tail -1)" "$log"
            fi
        ) &
        running=$((running + 1))
        if [ "$running" -ge "$concurrency" ]; then
            wait
            running=0
        fi
    done
    wait

    failed=$(ls -1 "$logdir/failed" | wc -l | tr -d ' ')
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
