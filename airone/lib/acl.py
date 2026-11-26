import enum
from typing import TYPE_CHECKING, TypeVar

from airone.lib.types import BaseIntEnum

if TYPE_CHECKING:
    from acl.models import ACLBase
    from user.models import User

__all__ = ["ACLType", "ACLObjType", "ACLReader", "get_permission_level"]

_ACLBaseT = TypeVar("_ACLBaseT", bound="ACLBase")


@enum.unique
class ACLObjType(BaseIntEnum):
    Entity = 1 << 0
    EntityAttr = 1 << 1
    Entry = 1 << 2
    EntryAttr = 1 << 3
    Category = 1 << 4


class ACLType(BaseIntEnum):
    Nothing = 1 << 0
    Readable = 1 << 1
    Writable = 1 << 2
    Full = 1 << 3

    @property
    def id(self) -> int:
        return self.value

    @property
    def name(self) -> str:
        names = {
            self.Nothing: "nothing",
            self.Readable: "readable",
            self.Writable: "writable",
            self.Full: "full",
        }
        return names[self]

    @property
    def label(self) -> str:
        labels = {
            self.Nothing: "Nothing",
            self.Readable: "Readable",
            self.Writable: "Writable",
            self.Full: "Full Controllable",
        }
        return labels[self]

    @classmethod
    def all(cls) -> list["ACLType"]:
        return [cls.Nothing, cls.Readable, cls.Writable, cls.Full]

    @classmethod
    def availables(cls) -> list["ACLType"]:
        return [cls.Readable, cls.Writable, cls.Full]


class ACLReader:
    """Share a lazy role snapshot within one response without caching across requests."""

    def __init__(self, user: "User"):
        self.user = user
        self._role_permissions: dict[str, int] | None = None

    def _get_role_permissions(self) -> dict[str, int]:
        # This module is imported while Django models are still initializing.
        from django.contrib.auth.models import Permission

        if self._role_permissions is None:
            roles = [belonging.role.id for belonging in self.user.belonging_roles()]
            self._role_permissions = {}
            codenames = Permission.objects.filter(
                historicalpermission__roles__id__in=roles,
                name__in=[level.name for level in ACLType.all()],
            ).values_list("codename", flat=True)
            for codename in codenames:
                object_id, separator, _ = codename.partition(".")
                if not separator:
                    continue
                level = int(codename.rsplit(".", 1)[-1])
                self._role_permissions[object_id] = max(
                    self._role_permissions.get(object_id, 0), level
                )
        return self._role_permissions

    def has_permission(self, obj: "ACLBase", level: ACLType) -> bool:
        return self.user.has_permission(obj, level, role_permissions=self._get_role_permissions)


def get_permitted_objects(
    user: "User", model: type[_ACLBaseT], permission_level: "ACLType"
) -> list[_ACLBaseT]:
    # This method assumes that model is a subclass of ACLBase
    return [
        x for x in model.objects.all() if user.has_permission(x, permission_level) and x.is_active
    ]


def get_permission_level(user: "User", obj: "ACLBase") -> int:
    """Returns the highest permission level the user has on the object.

    Args:
        user: User object to check permissions for
        obj: ACLBase subclass object to check permissions against

    Returns:
        int: The highest permission level (1=Nothing, 2=Readable, 4=Writable, 8=Full)
    """
    if user.has_permission(obj, ACLType.Full):
        return ACLType.Full.value
    elif user.has_permission(obj, ACLType.Writable):
        return ACLType.Writable.value
    elif user.has_permission(obj, ACLType.Readable):
        return ACLType.Readable.value
    else:
        return ACLType.Nothing.value
