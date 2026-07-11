#!/bin/bash
#
# Fast local test runner. CI is not affected by this script; it keeps using
# `manage.py test <target> --parallel` (see .github/workflows/build-core.yml).
#
# Local measurements (entity module, macOS + Docker MySQL/ES, 2026-07):
#   - Test DB creation costs ~28s per run; --keepdb removes it after the
#     first run. Pass --fresh when migrations or models have changed.
#   - Tests here are I/O-bound against MySQL/ES; running with --parallel is
#     SLOWER than serial on local Docker setups, so this script runs serially.
#
# The test database is isolated per checkout (airone_<hash of checkout path>)
# unless AIRONE_MYSQL_MASTER_URL is already set. Without this, multiple
# worktrees or agent sessions share "test_airone" and a --keepdb schema from
# another branch fails with errors like "Field 'x' doesn't have a default
# value".
#
# usage:
#   tools/test_local.sh entity                       # one app
#   tools/test_local.sh entity.tests.test_api_v2     # one file
#   tools/test_local.sh --fresh entity               # recreate the test DB
#   tools/test_local.sh entity entry                 # multiple targets

set -ue

BASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "${BASE_DIR}"

FRESH=0
if [ "${1:-}" = "--fresh" ]; then
  FRESH=1
  shift
fi

if [ $# -eq 0 ]; then
  echo "usage: $0 [--fresh] <test target>..."
  echo "  e.g. $0 entity entry.tests.test_api_v2"
  exit 1
fi

if [ -z "${AIRONE_MYSQL_MASTER_URL:-}" ]; then
  DB_SUFFIX=$(echo "${BASE_DIR}" | shasum | cut -c1-8)
  export AIRONE_MYSQL_MASTER_URL="mysql://airone:password@127.0.0.1:3306/airone_${DB_SUFFIX}?charset=utf8mb4"
  echo ">>> test database: test_airone_${DB_SUFFIX} (isolated per checkout)"
fi

# The repository does not track migration files; generate them like CI does
# so that the test database can be (re)built when needed.
if ! ls entity/migrations/0*.py >/dev/null 2>&1; then
  echo ">>> generating migrations (first run)"
  uv run python manage.py makemigrations
fi

if [ "${FRESH}" = "1" ]; then
  # Recreate the test DB from current migrations, then drop it as usual
  exec uv run python manage.py test "$@" --noinput
fi

exec uv run python manage.py test "$@" --keepdb
