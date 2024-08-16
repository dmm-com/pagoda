import enum
from typing import Any


@enum.unique
class AttrType(enum.IntEnum):
    OBJECT = 1 << 0
    STRING = 1 << 1
    TEXT = 1 << 2
    BOOLEAN = 1 << 3
    GROUP = 1 << 4
    DATE = 1 << 5
    ROLE = 1 << 6
    DATETIME = 1 << 7
    _ARRAY = 1 << 10
    _NAMED = 1 << 11
    NAMED_OBJECT = _NAMED | OBJECT
    ARRAY_OBJECT = _ARRAY | OBJECT
    ARRAY_STRING = _ARRAY | STRING
    ARRAY_NAMED_OBJECT = _ARRAY | _NAMED | OBJECT
    ARRAY_NAMED_OBJECT_BOOLEAN = 3081  # unmanaged by AttrTypeXXX
    ARRAY_GROUP = _ARRAY | GROUP
    ARRAY_ROLE = _ARRAY | ROLE


AttrTypeValue = {
    "object": AttrType.OBJECT,
    "string": AttrType.STRING,
    "named_object": AttrType.NAMED_OBJECT,
    "array_object": AttrType.ARRAY_OBJECT,
    "array_string": AttrType.ARRAY_STRING,
    "array_named_object": AttrType.ARRAY_NAMED_OBJECT,
    "array_group": AttrType.ARRAY_GROUP,
    "array_role": AttrType.ARRAY_ROLE,
    "textarea": AttrType.TEXT,
    "boolean": AttrType.BOOLEAN,
    "group": AttrType.GROUP,
    "date": AttrType.DATE,
    "role": AttrType.ROLE,
    "datetime": AttrType.DATETIME,
}
AttrDefaultValue: dict[int, Any] = {
    AttrType.OBJECT: None,
    AttrType.STRING: "",
    AttrType.NAMED_OBJECT: {"name": "", "id": None},
    AttrType.ARRAY_OBJECT: [],
    AttrType.ARRAY_STRING: [],
    AttrType.ARRAY_NAMED_OBJECT: dict().values(),
    AttrType.ARRAY_GROUP: [],
    AttrType.ARRAY_ROLE: [],
    AttrType.TEXT: "",
    AttrType.BOOLEAN: False,
    AttrType.GROUP: None,
    AttrType.DATE: None,
    AttrType.ROLE: None,
    AttrType.DATETIME: None,
}
