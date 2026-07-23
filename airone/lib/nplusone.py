"""Opt-in N+1 query detection for Django tests.

The test runner installs middleware that inspects SQL executed by each HTTP
request. It reports repeated SELECT shapes with a source location and a repair
hint, while excluding fixture setup and other queries outside the request.
"""

from __future__ import annotations

import json
import os
import re
import traceback
import unittest
from collections import defaultdict
from collections.abc import Callable, Iterator, Sequence
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from django.conf import settings
from django.db import connections
from django.http import HttpRequest, HttpResponse
from django.test import override_settings
from django.test.runner import DiscoverRunner

_CURRENT_TEST: ContextVar[str] = ContextVar("nplusone_current_test", default="unknown")
_NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?")
_QUOTED_VALUE = re.compile(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"")
_WHITESPACE = re.compile(r"\s+")
_SELECT = re.compile(r"^\s*(?:/\*.*?\*/\s*)*SELECT\b", re.IGNORECASE | re.DOTALL)


@dataclass(frozen=True)
class SourceLocation:
    path: str
    line: int
    function: str


@dataclass(frozen=True)
class QueryFinding:
    fingerprint: str
    occurrences: int
    sample_sql: str
    location: SourceLocation | None
    hint: str


@dataclass(frozen=True)
class RequestFinding:
    test: str
    method: str
    path: str
    query_count: int
    candidates: list[QueryFinding]


def normalize_sql(sql: str) -> str:
    """Return a stable query shape while preserving identifiers."""
    normalized = _QUOTED_VALUE.sub("?", sql)
    normalized = _NUMBER.sub("?", normalized)
    return _WHITESPACE.sub(" ", normalized).strip()


def _project_location(stack: Sequence[traceback.FrameSummary]) -> SourceLocation | None:
    root = Path(settings.BASE_DIR).resolve()
    ignored = Path(__file__).resolve()
    for frame in reversed(stack):
        path = Path(frame.filename).resolve()
        if path == ignored:
            continue
        try:
            relative_path = path.relative_to(root)
        except ValueError:
            continue
        if relative_path.parts[0] in {".venv", "node_modules"}:
            continue
        return SourceLocation(str(relative_path), frame.lineno or 0, frame.name)
    return None


def _repair_hint(location: SourceLocation | None, fingerprint: str) -> str:
    if location and "serializers.py" in location.path:
        return (
            "Move relation loading to the view queryset with select_related/prefetch_related "
            "and consume the prefetched relation in the serializer."
        )
    if " COUNT(" in f" {fingerprint.upper()}":
        return "Compute the count once or annotate it on the parent queryset."
    return (
        "Inspect the source loop and load related rows in bulk with select_related, "
        "prefetch_related, Prefetch, or an id-keyed map."
    )


class QueryDetector:
    """Collect repeated SELECT shapes for one unit of application work."""

    def __init__(self, min_repeats: int = 5) -> None:
        if min_repeats < 2:
            raise ValueError("min_repeats must be at least 2")
        self.min_repeats = min_repeats
        self.query_count = 0
        self._samples: dict[str, str] = {}
        self._locations: dict[str, SourceLocation | None] = {}
        self._counts: defaultdict[str, int] = defaultdict(int)

    def observe(
        self, sql: str, stack: Sequence[traceback.FrameSummary] | None = None
    ) -> None:
        self.query_count += 1
        if not _SELECT.match(sql):
            return
        fingerprint = normalize_sql(sql)
        self._counts[fingerprint] += 1
        if fingerprint not in self._samples:
            self._samples[fingerprint] = _WHITESPACE.sub(" ", sql).strip()
            self._locations[fingerprint] = _project_location(
                stack if stack is not None else traceback.extract_stack(limit=50)
            )

    def findings(self) -> list[QueryFinding]:
        findings = [
            QueryFinding(
                fingerprint=fingerprint,
                occurrences=count,
                sample_sql=self._samples[fingerprint],
                location=self._locations[fingerprint],
                hint=_repair_hint(self._locations[fingerprint], fingerprint),
            )
            for fingerprint, count in self._counts.items()
            if count >= self.min_repeats
        ]
        return sorted(findings, key=lambda finding: finding.occurrences, reverse=True)

    def __call__(
        self,
        execute: Callable[..., Any],
        sql: str,
        params: Any,
        many: bool,
        context: dict[str, Any],
    ) -> Any:
        self.observe(sql)
        return execute(sql, params, many, context)

    @contextmanager
    def capture(self) -> Iterator[None]:
        with ExitStack() as stack:
            for connection in connections.all():
                stack.enter_context(connection.execute_wrapper(self))
            yield


class NPlusOneDetected(AssertionError):
    pass


class FindingReporter:
    def __init__(self) -> None:
        self._findings: list[RequestFinding] = []
        self._lock = Lock()

    def add(self, finding: RequestFinding) -> None:
        with self._lock:
            self._findings.append(finding)

    @property
    def findings(self) -> list[RequestFinding]:
        with self._lock:
            return list(self._findings)

    def write(self, report_path: Path, min_repeats: int) -> None:
        findings = self.findings
        payload = {
            "schema_version": 1,
            "summary": {
                "requests_inspected": len(findings),
                "requests_with_candidates": sum(bool(item.candidates) for item in findings),
                "candidates": sum(len(item.candidates) for item in findings),
                "min_repeats": min_repeats,
            },
            "requests": [asdict(item) for item in findings],
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


_REPORTER = FindingReporter()


def _format_candidates(finding: RequestFinding) -> str:
    lines = [f"{finding.method} {finding.path} ({finding.test})"]
    for candidate in finding.candidates:
        location = (
            f"{candidate.location.path}:{candidate.location.line}"
            if candidate.location
            else "unknown source"
        )
        lines.append(f"  {candidate.occurrences}x at {location}: {candidate.hint}")
    return "\n".join(lines)


class NPlusOneMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        min_repeats = int(os.environ.get("AIRONE_NPLUSONE_MIN_REPEATS", "5"))
        detector = QueryDetector(min_repeats=min_repeats)
        try:
            with detector.capture():
                response = self.get_response(request)
        finally:
            finding = RequestFinding(
                test=_CURRENT_TEST.get(),
                method=request.method or "UNKNOWN",
                path=request.path,
                query_count=detector.query_count,
                candidates=detector.findings(),
            )
            _REPORTER.add(finding)
        if finding.candidates and os.environ.get("AIRONE_NPLUSONE_MODE", "report") == "fail":
            raise NPlusOneDetected(_format_candidates(finding))
        return response


class NPlusOneTextTestResult(unittest.TextTestResult):
    def startTest(self, test: Any) -> None:
        self._nplusone_token = _CURRENT_TEST.set(test.id())
        super().startTest(test)

    def stopTest(self, test: Any) -> None:
        super().stopTest(test)
        _CURRENT_TEST.reset(self._nplusone_token)


class NPlusOneTextTestRunner(unittest.TextTestRunner):
    resultclass = NPlusOneTextTestResult  # type: ignore[assignment]


class NPlusOneDiscoverRunner(DiscoverRunner):
    """Django test runner that produces an actionable N+1 JSON report."""

    test_runner = NPlusOneTextTestRunner

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.parallel > 1:
            raise ValueError("N+1 detection requires --parallel=1 so reports remain attributable")

    def run_suite(self, suite: Any, **kwargs: Any) -> Any:
        global _REPORTER
        _REPORTER = FindingReporter()
        middleware = [
            "airone.lib.nplusone.NPlusOneMiddleware",
            *[
                item
                for item in settings.MIDDLEWARE
                if item != "airone.lib.nplusone.NPlusOneMiddleware"
            ],
        ]
        with override_settings(MIDDLEWARE=middleware):
            result = super().run_suite(suite, **kwargs)

        min_repeats = int(os.environ.get("AIRONE_NPLUSONE_MIN_REPEATS", "5"))
        report_path = Path(
            os.environ.get("AIRONE_NPLUSONE_REPORT", ".artifacts/nplusone-report.json")
        )
        _REPORTER.write(report_path, min_repeats)
        candidates = [item for item in _REPORTER.findings if item.candidates]
        if candidates:
            self.log("\nN+1 candidates:\n" + "\n".join(_format_candidates(x) for x in candidates))
        self.log(f"N+1 report: {report_path}")
        return result
