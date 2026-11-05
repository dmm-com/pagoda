import enum
from typing import Any, NamedTuple


class ImportType(enum.Enum):
    ENTITY = "entity"
    ENTRY = "entry"
    USER = "user"
    GROUP = "group"
    ROLE = "role"


class UnknownImportFormatError(Exception):
    """The document does not match any import format."""


class ImportDocument(NamedTuple):
    import_type: ImportType
    payload: Any


# Export files carry their type in an envelope: {"import_type": ..., "data": ...}.
# Files without the envelope are the legacy format and are detected from their structure.
ENVELOPE_TYPE_KEY = "import_type"
ENVELOPE_DATA_KEY = "data"

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


def wrap_envelope(import_type: ImportType, data: Any) -> dict[str, Any]:
    """Put a payload into the envelope that declares its import type."""
    return {ENVELOPE_TYPE_KEY: import_type.value, ENVELOPE_DATA_KEY: data}


def unwrap_envelope(data: Any) -> tuple[ImportType | None, Any]:
    """Split an envelope into its declared type and payload.

    A document without the envelope is returned as ``(None, data)`` so that the
    caller can fall back to structural detection.
    """
    if not isinstance(data, dict) or ENVELOPE_TYPE_KEY not in data:
        return None, data

    try:
        declared = ImportType(data[ENVELOPE_TYPE_KEY])
    except ValueError:
        raise UnknownImportFormatError(f"Unknown import_type: {data[ENVELOPE_TYPE_KEY]!r}")
    if ENVELOPE_DATA_KEY not in data:
        raise UnknownImportFormatError(f"The envelope has no '{ENVELOPE_DATA_KEY}' key")
    return declared, data[ENVELOPE_DATA_KEY]


def parse_import_document(data: Any) -> ImportDocument:
    """Return the import type of a document and the payload to hand to the import.

    An envelope's declared type wins and its payload is not scanned, so the common case
    costs nothing extra. The per-type serializers validate the payload, and a payload
    labelled as one type but shaped like another is rejected there before any job is created.
    """
    declared, payload = unwrap_envelope(data)
    if declared is None:
        return ImportDocument(_detect_legacy(data), data)
    return ImportDocument(declared, payload)


def detect_import_type(data: Any) -> ImportType:
    """Decide which import format a parsed document is.

    Raises UnknownImportFormatError when the document fits none of them, or more than one.
    """
    return parse_import_document(data).import_type


def _detect_legacy(data: Any) -> ImportType:
    """Decide the import format of a document without an envelope, from its structure alone.

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
