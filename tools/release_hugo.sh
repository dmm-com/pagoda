#!/bin/bash

set -euo pipefail

HUGO_VERSION=${HUGO_VERSION:-0.110.0}
HUGO_BIN=${HUGO_BIN:-hugo}
REMOTE=${REMOTE:-origin}
SOURCE_BRANCH=${SOURCE_BRANCH:-master}
PUBLISH_BRANCH=${PUBLISH_BRANCH:-gh-pages}
COMMIT_MESSAGE=${COMMIT_MESSAGE:-Update Hugo docs}

usage() {
  cat <<USAGE
Usage: tools/release_hugo.sh [--allow-non-master] [--allow-dirty]

Build docs with Hugo and publish docs/public to ${PUBLISH_BRANCH} from your local machine.

Environment variables:
  HUGO_BIN          Hugo executable to use (default: hugo)
  HUGO_VERSION      Expected Hugo version (default: 0.110.0)
  REMOTE            Git remote to push to (default: origin)
  SOURCE_BRANCH     Source branch expected for release (default: master)
  PUBLISH_BRANCH    Publish branch (default: gh-pages)
  COMMIT_MESSAGE    Commit message for the generated site
USAGE
}

allow_non_master=0
allow_dirty=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --allow-non-master)
      allow_non_master=1
      ;;
    --allow-dirty)
      allow_dirty=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

root_dir=$(git rev-parse --show-toplevel)
cd "$root_dir"

if ! command -v "$HUGO_BIN" >/dev/null 2>&1; then
  echo "Hugo executable was not found: ${HUGO_BIN}" >&2
  echo "Install Hugo ${HUGO_VERSION}, or set HUGO_BIN to the Hugo executable path." >&2
  exit 1
fi

hugo_version_output=$("$HUGO_BIN" version)
if [[ "$hugo_version_output" != *"v${HUGO_VERSION}"* ]]; then
  echo "Warning: expected Hugo v${HUGO_VERSION}, but found: ${hugo_version_output}" >&2
fi

current_branch=$(git branch --show-current)
if [[ "$allow_non_master" -eq 0 && "$current_branch" != "$SOURCE_BRANCH" ]]; then
  echo "Run this script from ${SOURCE_BRANCH}, or pass --allow-non-master." >&2
  exit 1
fi

if [[ "$allow_dirty" -eq 0 && -n "$(git status --porcelain)" ]]; then
  echo "Working tree has uncommitted changes. Commit/stash them, or pass --allow-dirty." >&2
  exit 1
fi

echo "Building Hugo site with: ${hugo_version_output}"
rm -rf docs/public
"$HUGO_BIN" --minify --source docs --destination public

worktree_dir=$(mktemp -d "${TMPDIR:-/tmp}/pagoda-hugo-release.XXXXXX")
cleanup() {
  git -C "$root_dir" worktree remove --force "$worktree_dir" >/dev/null 2>&1 || rm -rf "$worktree_dir"
}
trap cleanup EXIT

git fetch "$REMOTE" "$PUBLISH_BRANCH"
git worktree add --detach "$worktree_dir" FETCH_HEAD

find "$worktree_dir" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -a docs/public/. "$worktree_dir"/
touch "$worktree_dir/.nojekyll"
git -C "$worktree_dir" add -A

if git -C "$worktree_dir" diff --cached --quiet; then
  echo "No Hugo release changes to publish."
  exit 0
fi

git -C "$worktree_dir" commit -m "$COMMIT_MESSAGE"
git -C "$worktree_dir" push "$REMOTE" "HEAD:${PUBLISH_BRANCH}"

echo "Published Hugo site to ${REMOTE}/${PUBLISH_BRANCH}."