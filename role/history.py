"""Combine native role membership and permission histories for display and restore."""

from datetime import datetime
from typing import Any

from rest_framework.exceptions import ValidationError

from acl.models import ACLBase
from role.models import HistoricalPermission, Role

ROLE_RELATIONS = ("users", "groups", "admin_users", "admin_groups")
MEMBER_FIELDS = {
    "users": ("user", "username"),
    "groups": ("group", "name"),
    "admin_users": ("user", "username"),
    "admin_groups": ("group", "name"),
}


def role_history_events(role: Role) -> list[dict[str, Any]]:
    role_records = list(role.history.select_related("history_user"))
    if not role_records:
        return []
    members_by_history: dict[int, dict[str, list[dict[str, Any]]]] = {
        record.history_id: {key: [] for key in ROLE_RELATIONS} for record in role_records
    }
    for key, (field, name) in MEMBER_FIELDS.items():
        through_model = getattr(Role.history.model, key).model
        links = through_model.objects.filter(history_id__in=members_by_history).select_related(
            field
        )
        for link in links:
            members_by_history[link.history_id][key].append(
                {
                    "id": getattr(link, f"{field}_id"),
                    name: getattr(getattr(link, field), name, str(getattr(link, f"{field}_id"))),
                }
            )

    # Include all snapshots of permissions ever assigned to the role. Filtering
    # snapshots by membership alone would lose removal and clear events.
    permission_memberships = HistoricalPermission.history.model.roles.model
    assigned_history_ids = permission_memberships.objects.filter(role_id=role.pk).values(
        "history_id"
    )
    permission_ids = HistoricalPermission.history.filter(
        history_id__in=assigned_history_ids
    ).values("permission_ptr_id")
    permission_records = list(
        HistoricalPermission.history.filter(permission_ptr_id__in=permission_ids).select_related(
            "history_user"
        )
    )
    belonged_history_ids = set(
        permission_memberships.objects.filter(
            role_id=role.pk, history_id__in=[record.history_id for record in permission_records]
        ).values_list("history_id", flat=True)
    )
    records: list[tuple[datetime, str, Any]] = [
        (record.history_date, "role", record) for record in role_records
    ] + [(record.history_date, "permission", record) for record in permission_records]
    records.sort(key=lambda item: (item[0], item[1] == "permission", item[2].history_id))
    target_ids = {
        int(record.codename.split(".")[0])
        for _, source, record in records
        if source == "permission" and record.codename.split(".")[0].isdecimal()
    }
    targets = ACLBase.objects.in_bulk(target_ids)
    target_names: dict[tuple[int, datetime], str | None] = {}
    permissions: dict[int, Any] = {}
    role_record = None
    members: dict[str, list[dict[str, Any]]] = {}
    events = []

    for date, source, record in records:
        if source == "role":
            role_record = record
            members = members_by_history[record.history_id]
        else:
            permission_id = record.permission_ptr_id
            belonged = permission_id in permissions
            belongs = record.history_type != "-" and record.history_id in belonged_history_ids
            if belongs:
                permissions[permission_id] = record
            else:
                permissions.pop(permission_id, None)
            if belonged == belongs:
                continue
        # Permission history may predate role tracking. Keep it for reconstructing
        # permissions, and start the combined timeline when role tracking begins.
        if role_record is None:
            continue
        permission_values = []
        for permission_id, permission in sorted(permissions.items()):
            target_id = int(permission.codename.split(".")[0])
            cache_key = (target_id, date)
            if cache_key not in target_names:
                target = targets.get(target_id)
                target_name: str | None = target.name if target else None
                if target:
                    target_history = getattr(target.get_subclass_object(), "history", None)
                    if target_history is not None:
                        historical_target = target_history.filter(history_date__lte=date).first()
                        if historical_target is not None:
                            target_name = historical_target.name
                target_names[cache_key] = target_name
            permission_values.append(
                {
                    "id": permission_id,
                    "codename": permission.codename,
                    "name": target_names[cache_key],
                }
            )
        events.append(
            {
                "history_id": record.history_id,
                "history_source": source,
                "history_date": date,
                "history_user": record.history_user,
                "history_type": record.history_type if source == "role" else "~",
                "history_change_reason": record.history_change_reason,
                "name": role_record.name,
                "description": role_record.description,
                "is_active": role_record.is_active,
                "relations": {**members, "permissions": permission_values},
            }
        )
    return list(reversed(events))


def get_role_history_event(role: Role, history_id: int, history_source: str) -> dict[str, Any]:
    for event in role_history_events(role):
        if event["history_source"] == history_source and event["history_id"] == history_id:
            if event["is_active"]:
                return event
            break
    raise ValidationError("The specified role history does not exist or is inactive")
