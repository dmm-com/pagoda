"""Support reverse membership updates with simple-history's native M2M records."""

from typing import Any

from simple_history.models import HistoricalRecords


class RoleHistoricalRecords(HistoricalRecords):  # type: ignore[misc]
    # simple-history does not ship typing metadata.
    def m2m_changed(
        self, instance: Any, action: str, attr: str, pk_set: Any, reverse: bool, **kwargs: Any
    ) -> None:
        if not reverse:
            super().m2m_changed(instance, action, attr, pk_set, reverse, **kwargs)
            return

        # The library's handler assumes a forward-side instance. On User/Group
        # managers, resolve the affected roles before recording their memberships.
        if action == "pre_clear":
            instance._role_history_ids = list(
                self.cls.objects.filter(**{attr: instance}).values_list("pk", flat=True)
            )
        if action not in ("post_add", "post_remove", "post_clear"):
            return
        role_ids = getattr(instance, "_role_history_ids", []) if action == "post_clear" else pk_set
        for role in self.cls.objects.filter(pk__in=role_ids or []):
            if hasattr(instance, "_history_user"):
                role._history_user = instance._history_user
            if hasattr(instance, "_change_reason"):
                role._change_reason = instance._change_reason
            super().m2m_changed(role, action, attr, pk_set, False, **kwargs)
