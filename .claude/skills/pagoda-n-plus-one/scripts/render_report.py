#!/usr/bin/env python3
"""Render before/after N+1 detector JSON as a compact Markdown report."""

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_rows(label: str, report: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for request in report["requests"]:
        for candidate in request["candidates"]:
            location = candidate.get("location")
            source = (
                f"{location['path']}:{location['line']}" if location else "unknown source"
            )
            rows.append(
                f"| {label} | `{request['method']} {request['path']}` | "
                f"{candidate['occurrences']} | `{source}` | {candidate['hint']} |"
            )
    return rows


def render(before: dict[str, Any], after: dict[str, Any]) -> str:
    before_summary = before["summary"]
    after_summary = after["summary"]
    rows = _candidate_rows("Before", before) + _candidate_rows("After", after)
    if not rows:
        rows = ["| - | - | 0 | - | - |"]
    return "\n".join(
        [
            "# N+1 remediation report",
            "",
            "## Detector summary",
            "",
            "| Run | Requests inspected | Requests with candidates | Candidates |",
            "| --- | ---: | ---: | ---: |",
            f"| Before | {before_summary['requests_inspected']} | "
            f"{before_summary['requests_with_candidates']} | {before_summary['candidates']} |",
            f"| After | {after_summary['requests_inspected']} | "
            f"{after_summary['requests_with_candidates']} | {after_summary['candidates']} |",
            "",
            "## Candidate evidence",
            "",
            "| Run | Request | Repetitions | Source | Suggested repair |",
            "| --- | --- | ---: | --- | --- |",
            *rows,
            "",
            "## Human review",
            "",
            "- Fix and query-shape explanation: TODO",
            "- Regression test and before/after growth: TODO",
            "- Semantics and ACL review: TODO",
            "- Residual risks or candidates: TODO",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(_load(args.before), _load(args.after)), encoding="utf-8")


if __name__ == "__main__":
    main()
