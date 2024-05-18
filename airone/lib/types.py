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
    _ARRAY = 1 << 10
    _NAMED = 1 << 11
    NAMED_OBJECT = _NAMED | OBJECT
    ARRAY_OBJECT = _ARRAY | OBJECT
    ARRAY_STRING = _ARRAY | STRING
    ARRAY_NAMED_OBJECT = _ARRAY | _NAMED | OBJECT
    ARRAY_NAMED_OBJECT_BOOLEAN = 3081  # unmanaged by AttrTypeXXX
    ARRAY_GROUP = _ARRAY | GROUP
    ARRAY_ROLE = _ARRAY | ROLE


class MetaAttrType(type):
    def __eq__(cls, comp):
        if isinstance(comp, int):
            return cls.TYPE == comp
        elif isinstance(comp, str):
            return cls.NAME == comp
        else:
            return cls.TYPE == comp.TYPE

    def __ne__(cls, comp):
        return not cls == comp

    def __repr__(cls):
        return str(cls.TYPE)

    def __int__(cls):
        return cls.TYPE


class AttrTypeObj(metaclass=MetaAttrType):
    NAME = "entry"
    TYPE = AttrType.OBJECT
    DEFAULT_VALUE = None


# STRING-type restricts data size to AttributeValue.MAXIMUM_VALUE_LENGTH
class AttrTypeStr(metaclass=MetaAttrType):
    NAME = "string"
    TYPE = AttrType.STRING
    DEFAULT_VALUE = ""


class AttrTypeNamedObj(metaclass=MetaAttrType):
    NAME = "named_entry"
    TYPE = AttrType.NAMED_OBJECT
    DEFAULT_VALUE = {"name": "", "id": None}


class AttrTypeArrObj(metaclass=MetaAttrType):
    NAME = "array_entry"
    TYPE = AttrType.ARRAY_OBJECT
    DEFAULT_VALUE = []


class AttrTypeArrStr(metaclass=MetaAttrType):
    NAME = "array_string"
    TYPE = AttrType.ARRAY_STRING
    DEFAULT_VALUE = []


class AttrTypeArrNamedObj(metaclass=MetaAttrType):
    NAME = "array_named_entry"
    TYPE = AttrType.ARRAY_NAMED_OBJECT
    DEFAULT_VALUE: Any = dict().values()


class AttrTypeArrGroup(metaclass=MetaAttrType):
    NAME = "array_group"
    TYPE = AttrType.ARRAY_GROUP
    DEFAULT_VALUE = []


class AttrTypeText(metaclass=MetaAttrType):
    NAME = "textarea"
    TYPE = AttrType.TEXT
    DEFAULT_VALUE = ""


class AttrTypeBoolean(metaclass=MetaAttrType):
    NAME = "boolean"
    TYPE = AttrType.BOOLEAN
    DEFAULT_VALUE = False


class AttrTypeGroup(metaclass=MetaAttrType):
    NAME = "group"
    TYPE = AttrType.GROUP
    DEFAULT_VALUE = None


class AttrTypeDate(metaclass=MetaAttrType):
    NAME = "date"
    TYPE = AttrType.DATE
    DEFAULT_VALUE = None


class AttrTypeRole(metaclass=MetaAttrType):
    NAME = "role"
    TYPE = AttrType.ROLE
    DEFAULT_VALUE = None


class AttrTypeArrRole(metaclass=MetaAttrType):
    NAME = "array_role"
    TYPE = AttrType.ARRAY_ROLE
    DEFAULT_VALUE = []


AttrTypes = [
    AttrTypeStr,
    AttrTypeObj,
    AttrTypeNamedObj,
    AttrTypeArrStr,
    AttrTypeArrObj,
    AttrTypeArrNamedObj,
    AttrTypeArrGroup,
    AttrTypeText,
    AttrTypeBoolean,
    AttrTypeGroup,
    AttrTypeDate,
    AttrTypeRole,
    AttrTypeArrRole,
]
AttrTypeValue = {
    "object": AttrType.OBJECT,
    "string": AttrType.STRING,
    "named": AttrType._NAMED,
    "named_object": AttrType.NAMED_OBJECT,
    "array": AttrType._ARRAY,
    "array_object": AttrType.ARRAY_OBJECT,
    "array_string": AttrType.ARRAY_STRING,
    "array_named_object": AttrType.ARRAY_NAMED_OBJECT,
    "array_group": AttrType.ARRAY_GROUP,
    "array_role": AttrType.ARRAY_ROLE,
    "text": AttrType.TEXT,
    "boolean": AttrType.BOOLEAN,
    "group": AttrType.GROUP,
    "date": AttrType.DATE,
    "role": AttrType.ROLE,
}
AttrDefaultValue: dict[int, Any] = {
    AttrType.OBJECT: AttrTypeObj.DEFAULT_VALUE,
    AttrType.STRING: AttrTypeStr.DEFAULT_VALUE,
    AttrType.NAMED_OBJECT: AttrTypeNamedObj.DEFAULT_VALUE,
    AttrType.ARRAY_OBJECT: AttrTypeArrObj.DEFAULT_VALUE,
    AttrType.ARRAY_STRING: AttrTypeArrStr.DEFAULT_VALUE,
    AttrType.ARRAY_NAMED_OBJECT: AttrTypeArrNamedObj.DEFAULT_VALUE,
    AttrType.ARRAY_GROUP: AttrTypeArrGroup.DEFAULT_VALUE,
    AttrType.ARRAY_ROLE: AttrTypeArrRole.DEFAULT_VALUE,
    AttrType.TEXT: AttrTypeText.DEFAULT_VALUE,
    AttrType.BOOLEAN: AttrTypeBoolean.DEFAULT_VALUE,
    AttrType.GROUP: AttrTypeGroup.DEFAULT_VALUE,
    AttrType.DATE: AttrTypeDate.DEFAULT_VALUE,
    AttrType.ROLE: AttrTypeRole.DEFAULT_VALUE,
}
