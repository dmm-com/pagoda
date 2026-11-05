"""Run the import requests of the per-kind import tests against /common/api/v2/import too.

The per-kind import tests post to their own endpoint through ``post_import``. It
first posts the same request to /common/api/v2/import from the same database
state and rolls that back, then makes the real request and returns its
response, so the assertions that follow stay about the per-kind endpoint. The
two outcomes (status, resulting records, jobs) are compared right there, so
every existing import scenario also proves the common endpoint compatible.
"""

import logging
from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock, patch

from django.db import transaction
from django.http import HttpResponse

from entity.models import Entity, EntityAttr
from entry.models import Attribute, AttributeValue, Entry
from group.models import Group
from job import tasks as job_tasks
from job.models import Job, JobOperation, JobStatus
from role.models import Role
from user.models import User

COMMON_IMPORT_URL = "/common/api/v2/import"

# Rows are compared by what they hold, never by id or timestamp: the common request
# runs first and its auto-increment ids are not given back by the rollback.
_STATE_MODELS = (Entity, EntityAttr, Entry, Attribute, AttributeValue, User, Group, Role)
_IGNORED_FIELDS = {"password", "last_login", "date_joined"}

# Errors raised before the body is looked at, so both endpoints must word them alike.
_SHARED_ERROR_CODES = {"AE-130000", "AE-140000"}


def _label(obj: Any) -> Any:
    if obj is None:
        return None
    for attr in ("name", "username", "value"):
        if hasattr(obj, attr):
            return getattr(obj, attr)
    return type(obj).__name__


def _snapshot_state() -> dict[str, list[str]]:
    state: dict[str, list[str]] = {}
    for model in _STATE_MODELS:
        rows = []
        for obj in model.objects.all():
            row: dict[str, Any] = {}
            for field in model._meta.concrete_fields:
                if (
                    field.primary_key
                    or field.name in _IGNORED_FIELDS
                    or field.name.endswith(("_time", "_at"))
                ):
                    continue
                value = getattr(obj, field.name)
                row[field.name] = _label(value) if field.is_relation else value
            for field in model._meta.many_to_many:
                row[field.name] = sorted(str(_label(x)) for x in getattr(obj, field.name).all())
            rows.append(repr(sorted(row.items())))
        state[model.__name__] = sorted(rows)
    return state


@dataclass
class _Outcome:
    status: int
    body: Any
    state: dict[str, list[str]]
    # (operation, status, text) of every job that exists after the request
    jobs: list[tuple[int, int, str]]


def _capture(response: HttpResponse) -> _Outcome:
    # a response without a body (200 / 403) has no content type to parse
    body = response.json() if response.get("Content-Type") else None  # type: ignore[attr-defined]
    return _Outcome(
        status=response.status_code,
        body=body,
        state=_snapshot_state(),
        jobs=sorted(Job.objects.values_list("operation", "status", "text")),
    )


def _assert_compatible(testcase: Any, legacy: _Outcome, common: _Outcome) -> None:
    general_jobs = [j for j in common.jobs if j[0] == JobOperation.IMPORT_GENERAL_V2]

    if legacy.status == 400 and common.status == 200 and general_jobs:
        # The per-kind endpoint applies models, users and groups while answering, so it
        # rejects what cannot be applied. The common one answers at once and its job
        # fails with the very same message.
        testcase.assertEqual([j[1] for j in general_jobs], [JobStatus.ERROR])
        testcase.assertEqual(general_jobs[0][2], legacy.body)
    else:
        testcase.assertEqual(common.status, legacy.status, common.body)
        testcase.assertEqual([j[1] for j in general_jobs], [JobStatus.DONE] * len(general_jobs))

    if isinstance(legacy.body, dict) and legacy.body.get("code") in _SHARED_ERROR_CODES:
        testcase.assertEqual(common.body, legacy.body)

    if legacy.status == 200 and isinstance(legacy.body, dict) and "result" in legacy.body:
        # item import: the same models are refused and as many jobs are started
        testcase.assertEqual(common.body["error"], legacy.body["result"]["error"])
        testcase.assertEqual(len(common.body["job_ids"]), len(legacy.body["result"]["job_ids"]))

    testcase.assertEqual(
        [j for j in common.jobs if j[0] != JobOperation.IMPORT_GENERAL_V2], legacy.jobs
    )
    testcase.assertEqual(common.state, legacy.state)


def post_import(
    testcase: Any,
    path: str,
    data: Any = None,
    content_type: str = "application/yaml",
    **extra: Any,
) -> HttpResponse:
    """Post an import request to ``path`` and to /common/api/v2/import, and compare them."""
    query = path.partition("?")[1:]
    common_url = COMMON_IMPORT_URL + "".join(query)

    entry_ids_before = set(Entry.objects.values_list("id", flat=True))
    previously_disabled = logging.root.manager.disable
    # the request is a rehearsal: keep it out of the log assertions of the test
    logging.disable(logging.CRITICAL)
    try:
        with (
            patch("job.tasks.import_general.delay", Mock(side_effect=job_tasks.import_general)),
            transaction.atomic(),
        ):
            response = testcase.client.post(common_url, data, content_type=content_type, **extra)
            common = _capture(response)
            # the search index is not part of the transaction
            for entry in Entry.objects.exclude(id__in=entry_ids_before):
                entry.unregister_es()
            transaction.set_rollback(True)
    finally:
        logging.disable(previously_disabled)

    response = testcase.client.post(path, data, content_type=content_type, **extra)
    _assert_compatible(testcase, _capture(response), common)
    return response
