"""Helpers for Pagoda's containerless local development mode ("lite mode").

Lite mode trades production fidelity for iteration speed: it swaps MySQL for
SQLite, Elasticsearch for an in-process index, and RabbitMQ/Celery for eager
task execution, so that ``manage.py runserver`` and ``manage.py test`` run with
no containers at all.

It also gives every checkout (in particular every ``git worktree``) its own
deterministic *slot*: a stable small integer derived from the checkout path.
The slot namespaces everything a second concurrently-running checkout would
otherwise fight over -- the HTTP port, the SQLite file, the Elasticsearch index
name, the media directory and the docker compose project name.

This module deliberately imports nothing from Django -- not even its own
package -- so shell scripts can run it as a standalone file and get an answer
without paying for Django and Celery startup::

    python airone/lib/devmode.py        # human readable summary
    python airone/lib/devmode.py --env  # shell-eval'able exports
"""

import hashlib
import json
import os
import subprocess
import sys

#: Number of distinct slots. Keeps derived ports inside a predictable window
#: while making a collision between two checkouts unlikely but harmless (a
#: collision only means the two cannot run their dev servers simultaneously).
SLOT_SPACE = 100

#: Base TCP port; the dev server for slot N listens on ``PORT_BASE + N``.
DEFAULT_PORT_BASE = 8000


def _repo_root() -> str:
    """Absolute path of the checkout this module lives in."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def workspace_path() -> str:
    """Canonical path used to derive every per-checkout identifier."""
    return os.path.realpath(_repo_root())


def workspace_name() -> str:
    """Human-friendly name of this checkout, e.g. the worktree directory name."""
    return os.path.basename(workspace_path())


def slot() -> int:
    """Deterministic per-checkout slot in ``[0, SLOT_SPACE)``.

    Derived from the checkout path so that it survives reboots, branch
    switches and re-clones of the same directory. ``PAGODA_SLOT`` overrides it
    when a human wants to pin a specific value.
    """
    override = os.environ.get("PAGODA_SLOT")
    if override:
        return int(override) % SLOT_SPACE

    digest = hashlib.sha1(workspace_path().encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % SLOT_SPACE


def port() -> int:
    """HTTP port this checkout's dev server should listen on."""
    base = int(os.environ.get("PAGODA_PORT_BASE", DEFAULT_PORT_BASE))
    return base + slot()


#: Host ports for the optional containers, offset by slot so that several
#: checkouts can run their own stack simultaneously.
SERVICE_PORT_BASES = {
    "MYSQL": 3306,
    "ES": 9200,
    "RABBITMQ": 5672,
    "RABBITMQ_MGMT": 15672,
}


def service_port(service: str) -> int:
    return SERVICE_PORT_BASES[service] + slot()


def namespace() -> str:
    """Short identifier safe to embed in index names, DB names and file paths."""
    return "%s-%02d" % (_slugify(workspace_name()), slot())


def _slugify(value: str) -> str:
    kept = [c if (c.isalnum() or c in "-_") else "-" for c in value.lower()]
    return "".join(kept).strip("-") or "pagoda"


def state_dir() -> str:
    """Per-checkout directory for generated dev state (DB file, dumps, pids).

    Lives inside the checkout so that removing a worktree removes its state,
    and so two worktrees never share a SQLite file.
    """
    path = os.environ.get("PAGODA_STATE_DIR") or os.path.join(_repo_root(), ".pagoda-lite")
    return os.path.realpath(path)


def ensure_state_dir() -> str:
    path = state_dir()
    os.makedirs(path, exist_ok=True)
    return path


def sqlite_url() -> str:
    """django-environ style URL for this checkout's SQLite database."""
    return "sqlite:///" + os.path.join(state_dir(), "pagoda.sqlite3")


def compose_project() -> str:
    """docker compose project name, so containers never collide between checkouts."""
    return "pagoda-" + namespace()


def is_lite() -> bool:
    """Whether lite mode is requested for this process."""
    return os.environ.get("PAGODA_LITE", "").lower() in ("1", "true", "yes", "on")


def git_worktrees() -> list[str]:
    """Every worktree of the current repository, best effort."""
    try:
        out = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=_repo_root(),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [line[len("worktree ") :] for line in out.splitlines() if line.startswith("worktree ")]


def summary() -> dict[str, object]:
    return {
        "workspace": workspace_path(),
        "name": workspace_name(),
        "slot": slot(),
        "namespace": namespace(),
        "port": port(),
        "state_dir": state_dir(),
        "sqlite_url": sqlite_url(),
        "compose_project": compose_project(),
        "container_ports": {name: service_port(name) for name in SERVICE_PORT_BASES},
        "lite": is_lite(),
    }


def _print_env() -> None:
    exports = {
        "PAGODA_SLOT": str(slot()),
        "PAGODA_NAMESPACE": namespace(),
        "PAGODA_PORT": str(port()),
        "PAGODA_STATE_DIR": state_dir(),
        "COMPOSE_PROJECT_NAME": compose_project(),
    }
    exports.update(
        {"PAGODA_%s_PORT" % name: str(service_port(name)) for name in SERVICE_PORT_BASES}
    )
    for key, value in exports.items():
        print("export %s=%s" % (key, value))


def main(argv: list[str]) -> int:
    if "--env" in argv:
        _print_env()
    elif "--json" in argv:
        print(json.dumps(summary(), indent=2))
    else:
        for key, value in summary().items():
            print("%-16s %s" % (key, value))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
