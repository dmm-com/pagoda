#!/usr/bin/env python3
"""Fail when mypy errors increase relative to a Git base revision."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Sequence


class RatchetError(RuntimeError):
    """Raised when the comparison cannot be performed reliably."""


@dataclass(frozen=True, order=True)
class Diagnostic:
    path: str
    message: str
    code: str


def _run(
    command: Sequence[str], *, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def _normalize_path(raw_path: str, root: Path) -> str:
    path = Path(raw_path)
    if path.is_absolute():
        try:
            path = path.relative_to(root)
        except ValueError as exc:
            raise RatchetError(f"mypy reported a path outside the source tree: {raw_path}") from exc
    normalized = PurePosixPath(path.as_posix())
    if ".." in normalized.parts:
        raise RatchetError(f"mypy reported an unsafe path: {raw_path}")
    return normalized.as_posix().removeprefix("./")


def parse_mypy_output(output: str, *, root: Path) -> Counter[Diagnostic]:
    """Parse error diagnostics, deliberately discarding line and column positions."""
    errors: Counter[Diagnostic] = Counter()
    unparsed: list[str] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
            path = payload["file"]
            severity = payload["severity"]
            message = payload["message"]
            code = payload.get("code")
            if (
                not isinstance(path, str)
                or severity not in ("error", "note")
                or not isinstance(message, str)
                or not isinstance(code, (str, type(None)))
            ):
                raise ValueError("invalid diagnostic fields")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            unparsed.append(raw_line)
            continue
        if severity == "note":
            continue
        diagnostic = Diagnostic(
            path=_normalize_path(path, root),
            message=message,
            code=code or "",
        )
        errors[diagnostic] += 1
    if unparsed:
        rendered = "\n".join(f"  {line}" for line in unparsed)
        raise RatchetError(f"could not parse mypy output:\n{rendered}")
    return errors


def run_mypy(root: Path) -> Counter[Diagnostic]:
    command = [
        sys.executable,
        "-m",
        "mypy",
        ".",
        "--config-file=pyproject.toml",
        "--output=json",
        "--no-error-summary",
        "--no-incremental",
    ]
    env = os.environ.copy()
    env.setdefault("PAGODA_LITE", "1")
    # Older base revisions predate lite mode. Force a backend available to both
    # revisions so importing Django models never requires a local MySQL client.
    env.setdefault("AIRONE_MYSQL_MASTER_URL", "sqlite://:memory:")
    env.setdefault("AIRONE_SQLITE_ENGINE", "django.db.backends.sqlite3")
    result = _run(command, cwd=root, env=env)
    if result.returncode not in (0, 1):
        details = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
        raise RatchetError(f"mypy failed with exit code {result.returncode}:\n{details}")
    # Django initialization and mypy itself may log non-diagnostic information
    # to stderr. Diagnostics use stdout with this invocation; exit codes above
    # still fail closed for crashes and configuration errors.
    try:
        diagnostics = parse_mypy_output(result.stdout, root=root)
    except RatchetError as exc:
        stderr = f"\nmypy stderr:\n{result.stderr.strip()}" if result.stderr.strip() else ""
        raise RatchetError(f"{exc}{stderr}") from exc
    if result.returncode == 0 and diagnostics:
        raise RatchetError("mypy exited successfully but emitted error diagnostics")
    if result.returncode == 1 and not diagnostics:
        raise RatchetError("mypy exited with errors but emitted no parseable error diagnostics")
    return diagnostics


def _snapshot_paths(repo: Path, base_ref: str) -> list[str]:
    result = _run(["git", "ls-tree", "-r", "--name-only", "-z", base_ref], cwd=repo)
    if result.returncode != 0:
        raise RatchetError(f"cannot list files at {base_ref}: {result.stderr.strip()}")
    paths = result.stdout.rstrip("\0").split("\0") if result.stdout else []
    return [path for path in paths if path.endswith(".py") or path.endswith("/py.typed")]


def create_base_snapshot(repo: Path, base_ref: str, destination: Path) -> None:
    """Extract only tracked Python sources and typing markers from the base revision."""
    paths = _snapshot_paths(repo, base_ref)
    if not paths:
        raise RatchetError(f"no Python sources found at {base_ref}")
    archive = subprocess.Popen(
        ["git", "archive", "--format=tar", base_ref, "--", *paths],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert archive.stdout is not None
    try:
        with tarfile.open(fileobj=archive.stdout, mode="r|") as tar:
            tar.extractall(destination, filter="data")
    except (tarfile.TarError, OSError) as exc:
        archive.kill()
        archive.wait()
        raise RatchetError(f"cannot extract sources at {base_ref}: {exc}") from exc
    stderr = archive.communicate()[1].decode(errors="replace")
    if archive.returncode != 0:
        raise RatchetError(f"cannot archive sources at {base_ref}: {stderr.strip()}")
    shutil.copy2(repo / "pyproject.toml", destination / "pyproject.toml")

    # CI exposes custom_view_sample under its runtime package name before mypy.
    if (repo / "custom_view").is_dir() and not (repo / "custom_view_sample").exists():
        sample = destination / "custom_view_sample"
        if sample.is_dir():
            sample.rename(destination / "custom_view")


def _rename_map(repo: Path, base_ref: str) -> dict[str, str]:
    """Map current Python paths back to their base paths for rename-tolerant comparison."""
    result = _run(["git", "diff", "--name-status", "-M", base_ref, "--"], cwd=repo)
    if result.returncode != 0:
        raise RatchetError(f"cannot detect renames from {base_ref}: {result.stderr.strip()}")
    renames: dict[str, str] = {}
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) == 3 and fields[0].startswith("R") and fields[2].endswith(".py"):
            old_path, current_path = fields[1:]
            renames[current_path] = old_path
    return renames


def new_diagnostics(
    base: Counter[Diagnostic],
    current: Counter[Diagnostic],
    path_aliases: dict[str, str] | None = None,
) -> Counter[Diagnostic]:
    """Return additions while preserving current paths in reported diagnostics."""
    aliases = path_aliases or {}
    added: Counter[Diagnostic] = Counter()
    for diagnostic, count in current.items():
        comparable = Diagnostic(
            path=aliases.get(diagnostic.path, diagnostic.path),
            message=diagnostic.message,
            code=diagnostic.code,
        )
        excess = count - base[comparable]
        if excess > 0:
            added[diagnostic] = excess
    return added


def _format_diagnostic(diagnostic: Diagnostic, count: int) -> str:
    code = f" [{diagnostic.code}]" if diagnostic.code else ""
    suffix = f" (x{count})" if count > 1 else ""
    return f"{diagnostic.path}: error: {diagnostic.message}{code}{suffix}"


def check(repo: Path, base_ref: str) -> int:
    path_aliases = _rename_map(repo, base_ref)
    with tempfile.TemporaryDirectory(prefix="pagoda-mypy-base-") as temporary:
        snapshot = Path(temporary)
        create_base_snapshot(repo, base_ref, snapshot)
        base = run_mypy(snapshot)
    current = run_mypy(repo)
    added = new_diagnostics(base, current, path_aliases)
    print(f"mypy errors: base={base.total()}, current={current.total()}")
    if not added:
        print("No new mypy errors.")
        return 0
    print(f"New mypy errors ({added.total()}):", file=sys.stderr)
    for diagnostic, count in sorted(added.items()):
        print(_format_diagnostic(diagnostic, count), file=sys.stderr)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", required=True, help="Git revision used as the ratchet base")
    args = parser.parse_args(argv)
    repo_result = _run(["git", "rev-parse", "--show-toplevel"], cwd=Path.cwd())
    if repo_result.returncode != 0:
        print(f"mypy ratchet failed: {repo_result.stderr.strip()}", file=sys.stderr)
        return 2
    repo = Path(repo_result.stdout.strip()).resolve()
    try:
        return check(repo, args.base_ref)
    except RatchetError as exc:
        print(f"mypy ratchet failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
