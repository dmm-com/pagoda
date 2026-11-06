"""Validation shared by role requests and their asynchronous workers."""

from types import SimpleNamespace
from typing import Any

from rest_framework.exceptions import PermissionDenied, ValidationError

from acl.models import ACLBase
from airone.lib.acl import ACLType
from role.api_v2.serializers import RoleCreateUpdateSerializer
from role.history import ROLE_RELATIONS
from role.models import HistoricalPermission, Role
from user.models import User


def restore_data(role: Role, history_id: int, user: User) -> tuple[dict[str, Any], list[int]]:
    record = role.history.filter(history_id=history_id, is_active=True).first()
    if record is None:
        raise ValidationError("The specified role history does not exist or is inactive")
    data: dict[str, Any] = {
        "name": record.name,
        "description": record.description,
        "is_active": True,
    }
    for key in ROLE_RELATIONS:
        data[key] = [value["id"] for value in record.relations.get(key, [])]
    permission_ids = [value["id"] for value in record.relations.get("permissions", [])]
    permissions = HistoricalPermission.objects.filter(pk__in=permission_ids)
    if permissions.count() != len(permission_ids):
        raise ValidationError("A permission in this history no longer exists")
    current_ids = set(role.permissions.values_list("pk", flat=True))
    changed_ids = current_ids.symmetric_difference(permission_ids)
    for permission in HistoricalPermission.objects.filter(pk__in=changed_ids):
        target = ACLBase.objects.filter(
            pk=int(permission.codename.split(".")[0]), is_active=True
        ).first()
        if target is None:
            raise ValidationError("A permission target in this history no longer exists")
        if not user.has_permission(target.get_subclass_object(), ACLType.Full):
            raise PermissionDenied("Full permission is required to restore role permissions")
    return data, permission_ids


def validate_role_data(role: Role, data: dict[str, Any], user: User) -> RoleCreateUpdateSerializer:
    serializer = RoleCreateUpdateSerializer(
        role, data=data, context={"request": SimpleNamespace(user=user)}
    )
    serializer.is_valid(raise_exception=True)
    return serializer
