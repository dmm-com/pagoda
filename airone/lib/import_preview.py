"""Shared payload for import previews.

Every importable resource reports a preview in the same shape, so that one job
endpoint can serve them all and the frontend needs a single renderer.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

PreviewAction = Literal["create", "update", "unchanged", "skip", "error"]

# Summary keys are past tense because "create"/"update" would shadow
# rest_framework.serializers.BaseSerializer.create()/update().
PREVIEW_SUMMARY_KEYS: dict[PreviewAction, str] = {
    "create": "created",
    "update": "updated",
    "unchanged": "unchanged",
    "skip": "skipped",
    "error": "errored",
}

# How many rows a preview keeps in detail. The summary always counts every row;
# this only bounds how many are listed, so that previewing a huge file cannot
# exhaust memory. Rows that would change something are kept first.
PREVIEW_MAX_DETAIL_ROWS = 10000


@dataclass
class PreviewCollector:
    """Accumulates preview rows while keeping the summary exact.

    Rows that report a change (or a problem) are kept ahead of unchanged rows,
    so the rows a user actually needs are never the ones dropped by the cap.
    """

    # Read through a factory so that tests (and settings overrides) can change the
    # module-level cap without every collector having frozen it at import time.
    max_detail_rows: int = field(default_factory=lambda: PREVIEW_MAX_DETAIL_ROWS)
    summary: dict[str, int] = field(
        default_factory=lambda: {key: 0 for key in PREVIEW_SUMMARY_KEYS.values()} | {"total": 0}
    )
    _notable: list[dict[str, Any]] = field(default_factory=list)
    _unchanged: list[dict[str, Any]] = field(default_factory=list)
    _dropped: int = 0

    def add(
        self,
        *,
        kind: str,
        name: str,
        action: PreviewAction,
        reason: str | None = None,
        changes: list[dict[str, str | None]] | None = None,
    ) -> None:
        self.summary[PREVIEW_SUMMARY_KEYS[action]] += 1
        self.summary["total"] += 1

        row = {
            "index": self.summary["total"] - 1,
            "kind": kind,
            "name": name,
            "action": action,
            "reason": reason,
            "changes": changes or [],
        }

        bucket = self._unchanged if action == "unchanged" else self._notable
        if len(self._notable) + len(self._unchanged) < self.max_detail_rows:
            bucket.append(row)
        elif action != "unchanged" and self._unchanged:
            # A notable row displaces an unchanged one rather than being dropped.
            self._unchanged.pop()
            self._notable.append(row)
            self._dropped += 1
        else:
            self._dropped += 1

    @property
    def rows(self) -> list[dict[str, Any]]:
        return self._notable + self._unchanged

    def payload(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "rows": self.rows,
            # True when the summary covers more rows than the list does.
            "truncated": self._dropped > 0,
        }
