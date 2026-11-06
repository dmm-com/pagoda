"""Capture role membership and reverse ACL relations in immutable history rows."""

from contextvars import ContextVar
from typing import Any

from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from simple_history.signals import pre_create_historical_record

from acl.models import ACLBase
from role.models import Role

ROLE_RELATIONS = ("users", "groups", "admin_users", "admin_groups")
suppress_role_history: ContextVar[bool] = ContextVar("suppress_role_history", default=False)


def permission_target_names(permissions: list[dict[str, Any]]) -> dict[str, str]:
    targets = {
        permission["codename"]: int(permission["codename"].split(".")[0])
        for permission in permissions
        if permission.get("codename", "").split(".")[0].isdecimal()
    }
    names = dict(ACLBase.objects.filter(pk__in=set(targets.values())).values_list("pk", "name"))
    return {
        codename: names[target_id] for codename, target_id in targets.items() if target_id in names
    }


@receiver(pre_create_historical_record, sender=Role.history.model)
def capture_relations(instance: Role, history_instance: Any, **kwargs: Any) -> None:
    history_instance.relations = {
        key: list(getattr(instance, key).order_by("pk").values("id", name_field))
        for key, name_field in [
            ("users", "username"),
            ("groups", "name"),
            ("admin_users", "username"),
            ("admin_groups", "name"),
            ("permissions", "codename"),
        ]
    }
    permissions = history_instance.relations["permissions"]
    names = permission_target_names(permissions)
    for permission in permissions:
        permission["name"] = names.get(permission["codename"])


def record_relation_change(
    sender: Any, instance: Any, action: str, reverse: bool, pk_set: Any, **kwargs: Any
) -> None:
    if suppress_role_history.get():
        return
    # Role membership is forward; HistoricalPermission.roles is reverse.
    role_side = isinstance(instance, Role)
    if action.startswith("pre_"):
        if role_side:
            role_ids = [instance.pk]
        elif action == "pre_clear":
            field = next(
                key
                for key in (*ROLE_RELATIONS, "permissions")
                if getattr(Role, key).through is sender
            )
            role_ids = list(Role.objects.filter(**{field: instance}).values_list("pk", flat=True))
        else:
            role_ids = list(pk_set or [])
        instance._role_history_ids = role_ids
        for role in Role.objects.filter(pk__in=role_ids):
            if not role.history.exists():
                role.save()
    elif action.startswith("post_"):
        for role in Role.objects.filter(pk__in=getattr(instance, "_role_history_ids", [])):
            if hasattr(instance, "_history_user"):
                role._history_user = instance._history_user
            if hasattr(instance, "_change_reason"):
                role._change_reason = instance._change_reason
            role.save()


for relation in (*ROLE_RELATIONS, "permissions"):
    m2m_changed.connect(
        record_relation_change,
        sender=getattr(Role, relation).through,
        dispatch_uid=f"role_history_{relation}",
    )
