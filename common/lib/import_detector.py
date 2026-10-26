import enum
from typing import Any


class ImportType(enum.Enum):
    ENTITY = "entity"
    ENTRY = "entry"
    USER = "user"
    GROUP = "group"
    ROLE = "role"


class UnknownImportFormatError(Exception):
    """The document does not match any import format."""


_ENTITY_KEYS = {"Entity", "EntityAttr"}
_ENTRY_KEYS = {"entity", "entries"}
_USER_KEYS = {"username", "email", "is_superuser"}
_ROLE_KEYS = {"users", "admin_users", "admin_groups", "description", "permissions"}
_GROUP_KEYS = {"id", "name"}


def _detect_record_type(record: Any) -> ImportType | None:
    if not isinstance(record, dict):
        return None

    keys = set(record)
    if keys & _ENTRY_KEYS:
        return ImportType.ENTRY
    if keys & _USER_KEYS:
        return ImportType.USER
    if keys & _ROLE_KEYS:
        return ImportType.ROLE
    # ``groups`` is a comma-separated string for a user and a list of names for a role
    if "groups" in keys:
        return ImportType.USER if isinstance(record["groups"], str) else ImportType.ROLE
    if keys and keys <= _GROUP_KEYS:
        return ImportType.GROUP
    return None


def detect_import_type(data: Any) -> ImportType:
    """Decide which import format a parsed document is, from its structure alone.

    Raises UnknownImportFormatError when it fits none of them, or more than one
    (an empty list, a list that mixes formats, or a dict that is not a model file).
    """
    if isinstance(data, dict):
        if set(data) & _ENTITY_KEYS:
            return ImportType.ENTITY
        raise UnknownImportFormatError("The document does not match any import format")

    if not isinstance(data, list) or not data:
        raise UnknownImportFormatError(
            "The document must be a non-empty list of records or a model definition"
        )

    types = {_detect_record_type(record) for record in data}
    if None in types:
        raise UnknownImportFormatError("Some records do not match any import format")
    if len(types) > 1:
        raise UnknownImportFormatError("The document mixes records of different import formats")
    (import_type,) = types
    assert import_type is not None
    return import_type
