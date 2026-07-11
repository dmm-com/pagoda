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
# usage:
#   tools/test_local.sh entity                       # one app
#   tools/test_local.sh entity.tests.test_api_v2     # one file
#   tools/test_local.sh --fresh entity               # recreate the test DB
#   tools/test_local.sh entity entry                 # multiple targets

set -ue

BASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "${BASE_DIR}"

KEEPDB="--keepdb"
if [ "${1:-}" = "--fresh" ]; then
  KEEPDB=""
  shift
fi

if [ $# -eq 0 ]; then
  echo "usage: $0 [--fresh] <test target>..."
  echo "  e.g. $0 entity entry.tests.test_api_v2"
  exit 1
fi

# The repository does not track migration files; generate them like CI does
# so that the test database can be (re)built when needed.
if ! ls entity/migrations/0*.py >/dev/null 2>&1; then
  echo ">>> generating migrations (first run)"
  uv run python manage.py makemigrations
fi

exec uv run python manage.py test "$@" ${KEEPDB}
