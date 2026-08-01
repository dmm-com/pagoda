"""Read-only preview of a model import file.

Nothing here writes. An earlier version ran the real import inside a transaction
and rolled it back, which reported the truth but took write locks on rows a user
had only asked to look at -- and would have left the damage behind had the
rollback not run. A preview is a read, so it reads.

Staying read-only means the rules the importer enforces are checked here rather
than observed. To keep the two from drifting, the rules themselves live in
entity.admin and are called from both.
"""

from typing import Any, Callable, NamedTuple

from airone.lib.acl import ACLType
from airone.lib.import_preview import PreviewAction, PreviewCollector
from airone.lib.resources import AironeModelResource
from entity.admin import (
    EntityAttrResource,
    EntityResource,
    check_entity_attr_row,
    check_entity_row,
)
from entity.models import Entity, EntityAttr
from user.models import User


class PreviewField(NamedTuple):
    """One comparable field, read from the file and from the stored object.

    The two sides are rendered as text before they are compared: the file holds
    '1' where the model holds True, and a difference in spelling is not a change.
    """

    name: str
    from_row: Callable[[dict[str, Any]], str]
    from_instance: Callable[[Any], str]


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _bool_text(value: Any) -> str:
    if isinstance(value, str):
        return str(bool(int(value))) if value.isdigit() else str(bool(value))
    return str(bool(value))


ENTITY_FIELDS = [
    PreviewField("name", lambda row: _text(row.get("name")), lambda x: _text(x.name)),
    PreviewField("note", lambda row: _text(row.get("note")), lambda x: _text(x.note)),
    PreviewField(
        "status",
        lambda row: _text(int(row.get("status") or 0)),
        lambda x: _text(x.status),
    ),
    PreviewField(
        "created_user",
        lambda row: _text(row.get("created_user")),
        lambda x: _text(x.created_user.username),
    ),
]

ENTITY_ATTR_FIELDS = [
    PreviewField("name", lambda row: _text(row.get("name")), lambda x: _text(x.name)),
    PreviewField(
        "is_mandatory",
        lambda row: _bool_text(row.get("is_mandatory")),
        lambda x: _bool_text(x.is_mandatory),
    ),
    PreviewField(
        "referral",
        lambda row: ",".join(sorted(x for x in _text(row.get("refer")).split(",") if x)),
        lambda x: ",".join(sorted(e.name for e in x.referral.all())),
    ),
    PreviewField(
        "parent_entity",
        lambda row: _text(row.get("entity")),
        lambda x: _text(x.parent_entity.name),
    ),
    PreviewField(
        "created_user",
        lambda row: _text(row.get("created_user")),
        lambda x: _text(x.created_user.username),
    ),
]


class _RowOutcome(NamedTuple):
    action: PreviewAction
    reason: str | None
    changes: list[dict[str, str | None]]


def build_entity_import_preview(
    user: User,
    validated_data: dict[str, Any],
    on_progress: Callable[[int, int], None] | None = None,
    is_canceled: Callable[[], bool] | None = None,
) -> dict[str, Any] | None:
    """Report what importing this file would change. Returns None if canceled."""
    entities: list[dict[str, Any]] = validated_data["Entity"]
    entity_attrs: list[dict[str, Any]] = validated_data["EntityAttr"]

    collector = PreviewCollector()
    total = len(entities) + len(entity_attrs)

    # Models this very file would create count as existing for the attribute rows
    # that follow, exactly as they do when the file is imported for real.
    created_entity_names: set[str] = set()

    for row in entities:
        if is_canceled is not None and is_canceled():
            return None
        if on_progress is not None:
            on_progress(collector.summary["total"] + 1, total)

        outcome = _preview_entity_row(user, row)
        if outcome.action == "create":
            created_entity_names.add(_text(row.get("name")))
        collector.add(
            kind="Entity",
            name=_text(row.get("name")),
            action=outcome.action,
            reason=outcome.reason,
            changes=outcome.changes,
        )

    for row in entity_attrs:
        if is_canceled is not None and is_canceled():
            return None
        if on_progress is not None:
            on_progress(collector.summary["total"] + 1, total)

        outcome = _preview_entity_attr_row(user, row, created_entity_names)
        collector.add(
            kind="EntityAttr",
            name=_text(row.get("name")),
            action=outcome.action,
            reason=outcome.reason,
            changes=outcome.changes,
        )

    return collector.payload()


def _preview_entity_row(user: User, row: dict[str, Any]) -> _RowOutcome:
    try:
        EntityResource.validate_import_row(row)
    except RuntimeError as e:
        return _RowOutcome("error", str(e), [])

    # From here on the row is shaped the way the importer sees it, so that the
    # shared checks read the same keys they read during an import.
    row = EntityResource.normalize_import_row(row)

    try:
        check_entity_row(row)
    except RuntimeError as e:
        return _RowOutcome("error", str(e), [])

    if not User.objects.filter(username=_text(row.get("created_user"))).exists():
        return _RowOutcome("error", "created_user does not exist", [])

    instance = Entity.objects.filter(id=row["id"]).first() if row.get("id") else None
    return _compare(user, EntityResource, ENTITY_FIELDS, row, instance)


def _preview_entity_attr_row(
    user: User, row: dict[str, Any], created_entity_names: set[str]
) -> _RowOutcome:
    try:
        EntityAttrResource.validate_import_row(row)
    except RuntimeError as e:
        return _RowOutcome("error", str(e), [])

    row = EntityAttrResource.normalize_import_row(row)
    instance = EntityAttr.objects.filter(id=row["id"]).first() if row.get("id") else None

    try:
        check_entity_attr_row(
            row,
            is_new=instance is None,
            known_entity_names=created_entity_names,
        )
    except RuntimeError as e:
        return _RowOutcome("error", str(e), [])

    if not User.objects.filter(username=_text(row.get("created_user"))).exists():
        return _RowOutcome("error", "created_user does not exist", [])

    return _compare(user, EntityAttrResource, ENTITY_ATTR_FIELDS, row, instance)


def _compare(
    user: User,
    resource: type[AironeModelResource],
    fields: list[PreviewField],
    row: dict[str, Any],
    instance: Any | None,
) -> _RowOutcome:
    if instance is None:
        # Inhibits the spoofing, as AironeModelResource.skip_row() does.
        if _text(row.get("created_user")) != user.username:
            return _RowOutcome("skip", "spoofing", [])
        return _RowOutcome(
            "create",
            None,
            [
                {"field": f.name, "before": None, "after": f.from_row(row)}
                for f in fields
                if f.from_row(row)
            ],
        )

    changes: list[dict[str, str | None]] = [
        {"field": f.name, "before": f.from_instance(instance), "after": f.from_row(row)}
        for f in fields
        if f.from_instance(instance) != f.from_row(row)
    ]
    if not changes:
        return _RowOutcome("unchanged", None, [])

    if not user.has_permission(instance, ACLType.Writable):
        return _RowOutcome("skip", "permission_denied", [])

    changed_fields = {change["field"] for change in changes}
    if changed_fields & set(resource.DISALLOW_UPDATE_KEYS):
        return _RowOutcome("skip", "disallow_update", [])

    return _RowOutcome("update", None, changes)
