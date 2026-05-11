import enum
import math
from typing import Any


def coerce_number(raw: str | int | float | None) -> int | float | None:
    """Normalise a Number-attribute value, returning int when integer-valued.

    Number values are persisted as strings (e.g. "4.0") via str(float(...))
    in entry.models.Attribute.add_value, and Elasticsearch may return either
    a string or a numeric type via ``_source``. Both routes used to call
    float() unconditionally, which turned integer inputs (4) into 4.0. This
    helper accepts any of those shapes and returns int when the parsed value
    has no fractional part (regression for #3458).
    """
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        f = float(raw)
    elif isinstance(raw, str):
        if not raw.strip():
            return None
        try:
            f = float(raw)
        except ValueError:
            return None
    else:
        return None
    if not math.isfinite(f):
        return None
    return int(f) if f.is_integer() else f


class BaseIntEnum(enum.IntEnum):
    @classmethod
    def isin(cls, v: int) -> bool:
        return v in cls.__members__.values()


@enum.unique
class AttrType(BaseIntEnum):
    OBJECT = 1 << 0
    STRING = 1 << 1
    TEXT = 1 << 2
    BOOLEAN = 1 << 3
    GROUP = 1 << 4
    DATE = 1 << 5
    ROLE = 1 << 6
    DATETIME = 1 << 7
    NUMBER = 1 << 8
    _ARRAY = 1 << 10
    _NAMED = 1 << 11
    NAMED_OBJECT = _NAMED | OBJECT
    ARRAY_OBJECT = _ARRAY | OBJECT
    ARRAY_STRING = _ARRAY | STRING
    ARRAY_NUMBER = _ARRAY | NUMBER
    ARRAY_NAMED_OBJECT = _ARRAY | _NAMED | OBJECT
    ARRAY_NAMED_OBJECT_BOOLEAN = 3081  # unmanaged by AttrTypeXXX
    ARRAY_GROUP = _ARRAY | GROUP
    ARRAY_ROLE = _ARRAY | ROLE


# Mapping from string to AttrType enum values (backwards compatibility)
AttrTypeValue = {
    "string": AttrType.STRING,
    "object": AttrType.OBJECT,
    "named_object": AttrType.NAMED_OBJECT,
    "group": AttrType.GROUP,
    "role": AttrType.ROLE,
    "array_string": AttrType.ARRAY_STRING,
    "array_number": AttrType.ARRAY_NUMBER,
    "array_object": AttrType.ARRAY_OBJECT,
    "array_named_object": AttrType.ARRAY_NAMED_OBJECT,
    "array_group": AttrType.ARRAY_GROUP,
    "array_role": AttrType.ARRAY_ROLE,
    "textarea": AttrType.TEXT,
    "boolean": AttrType.BOOLEAN,
    "date": AttrType.DATE,
    "datetime": AttrType.DATETIME,
    "number": AttrType.NUMBER,
}
AttrDefaultValue: dict[int, Any] = {
    AttrType.OBJECT: None,
    AttrType.STRING: "",
    AttrType.NAMED_OBJECT: {"name": "", "id": None},
    AttrType.ARRAY_OBJECT: [],
    AttrType.ARRAY_STRING: [],
    AttrType.ARRAY_NUMBER: [],
    AttrType.ARRAY_NAMED_OBJECT: dict().values(),
    AttrType.ARRAY_GROUP: [],
    AttrType.ARRAY_ROLE: [],
    AttrType.TEXT: "",
    AttrType.BOOLEAN: False,
    AttrType.GROUP: None,
    AttrType.DATE: None,
    AttrType.ROLE: None,
    AttrType.DATETIME: None,
    AttrType.NUMBER: None,
}
