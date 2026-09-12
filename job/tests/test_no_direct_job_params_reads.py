"""Forbid production code from reading persisted job parameters directly.

Job parameters are persisted as JSON, but task modules must consume the
validated DTO exposed by ``Job.get_typed_params``.  Their ``params`` attribute
is reserved so aliases and alternative parsers cannot bypass the operation
registry.  Outside task modules, explicitly Job-named values are also checked.

This invariant lives in the test suite rather than a standalone CI step: the
repository scan below runs as part of ``manage.py test job``.
"""

from __future__ import annotations

import ast
import os
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from django.test import SimpleTestCase

_SKIPPED_PARTS = frozenset(
    {
        ".git",
        ".agents",
        ".claude",
        ".codex",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "migrations",
        "node_modules",
        "tests",
        "virtualenv_old",
    }
)


@dataclass(frozen=True)
class Violation:
    """A direct Job.params read found in a production Python module."""

    path: Path
    line: int
    column: int
    expression: str

    def format(self, root: Path) -> str:
        """Render a violation in a format understood by CI log viewers."""

        try:
            path = self.path.relative_to(root)
        except ValueError:
            path = self.path
        return f"{path}:{self.line}:{self.column}: direct Job.params access ({self.expression})"


def find_violations(source: str, path: Path) -> list[Violation]:
    """Return direct reads of the reserved params attribute in one source file."""

    tree = ast.parse(source, filename=str(path))
    is_task_module = path.name == "tasks.py" or "tasks" in path.parts
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or node.attr != "params":
            continue
        if not is_task_module:
            if not isinstance(node.value, ast.Name):
                continue
            name = node.value.id
            if name != "job" and not name.endswith("_job"):
                continue
        violations.append(
            Violation(
                path=path,
                line=node.lineno,
                column=node.col_offset + 1,
                expression=ast.unparse(node),
            )
        )
    return violations


def _is_production_file(path: Path) -> bool:
    parts = set(path.parts)
    if parts & _SKIPPED_PARTS:
        return False
    return not path.name.startswith("test_")


def iter_production_python_files(root: Path) -> Iterable[Path]:
    """Yield production Python files while excluding test and generated trees."""

    for current_root, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in _SKIPPED_PARTS]
        directory = Path(current_root)
        for name in files:
            if name.endswith(".py"):
                path = directory / name
                if _is_production_file(path):
                    yield path


def check_repository(root: Path) -> list[Violation]:
    """Scan production Python files under ``root``."""

    violations: list[Violation] = []
    for path in iter_production_python_files(root):
        # The model itself owns the raw field and is deliberately exempt.
        if path.relative_to(root) == Path("job/models.py"):
            continue
        violations.extend(find_violations(path.read_text(encoding="utf-8"), path))
    return sorted(violations, key=lambda item: (item.path, item.line, item.column))


_REPO_ROOT = Path(__file__).resolve().parents[2]


class DirectJobParamsReadTest(SimpleTestCase):
    def test_detects_json_and_pydantic_parsers(self) -> None:
        source = """
import json

def task(job):
    first = json.loads(job.params)
    second = Params.model_validate_json(job.params)
    third = Params.parse_raw(data=job.params)
    return first, second, third
"""

        violations = find_violations(source, Path("job/tasks.py"))

        self.assertEqual(len(violations), 3)
        self.assertEqual([violation.line for violation in violations], [5, 6, 7])
        self.assertEqual([violation.expression for violation in violations], ["job.params"] * 3)

    def test_detects_imported_json_loads_alias(self) -> None:
        source = """
import json as jsonlib
from json import loads as decode_json

def task(job):
    return decode_json(payload=jsonlib.loads(job.params))
"""

        self.assertEqual(len(find_violations(source, Path("job/tasks.py"))), 1)

    def test_detects_job_alias_intermediate_value_and_alternative_json_module(self) -> None:
        source = """
import json
import orjson

def task(task_job):
    raw = task_job.params
    first = json.loads(raw)
    queued = task_job
    second = orjson.loads(queued.params)
    return first, second
"""

        violations = find_violations(source, Path("plugin/tasks.py"))

        self.assertEqual(len(violations), 2)
        self.assertEqual([violation.line for violation in violations], [6, 9])

    def test_task_modules_reserve_params_for_any_variable_name(self) -> None:
        source = """
def task(current, job_config):
    return current.params, job_config.params
"""

        violations = find_violations(source, Path("plugin/tasks.py"))

        self.assertEqual(len(violations), 2)

    def test_non_task_context_params_is_not_a_job_violation(self) -> None:
        source = """
def dispatch(context):
    return context.params
"""

        self.assertEqual(find_violations(source, Path("plugin/handlers.py")), [])

    def test_allows_validated_dto_and_non_production_fixtures(self) -> None:
        source = """
def task(job):
    params = job.get_typed_params(Params)
    return params.model_dump()
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "job").mkdir()
            (root / "job" / "tasks.py").write_text(source, encoding="utf-8")
            (root / "job" / "tests").mkdir()
            (root / "job" / "tests" / "test_fixture.py").write_text(
                "import json\njson.loads(job.params)\n", encoding="utf-8"
            )

            self.assertEqual(check_repository(root), [])

    def test_repository_reports_violations_outside_tests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "job").mkdir()
            (root / "job" / "tasks.py").write_text(
                "import json\n\ndef task(job):\n    return json.loads(job.params)\n",
                encoding="utf-8",
            )
            (root / "job" / "tests").mkdir()
            (root / "job" / "tests" / "test_fixture.py").write_text(
                "import json\njson.loads(job.params)\n", encoding="utf-8"
            )

            violations = check_repository(root)

            self.assertEqual(len(violations), 1)
            self.assertEqual(violations[0].path, root / "job" / "tasks.py")

    def test_production_tree_has_no_direct_job_params_access(self) -> None:
        """Keep the reserved-attribute invariant enforced by the test suite."""

        violations = check_repository(_REPO_ROOT)
        self.assertEqual(
            [violation.format(_REPO_ROOT) for violation in violations],
            [],
            "Consume Job parameters through Job.get_typed_params()",
        )
