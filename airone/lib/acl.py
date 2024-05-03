import enum

__all__ = ["ACLType", "ACLObjType"]


class Iteratable(object):
    def __iter__(self):
        return self._types.__iter__()


@enum.unique
class ACLObjType(enum.IntEnum):
    Entity = 1 << 0
    EntityAttr = 1 << 1
    Entry = 1 << 2
    EntryAttr = 1 << 3


class MetaACLType(type):
    def __eq__(cls, comp):
        if isinstance(comp, int):
            return cls.id == comp
        elif isinstance(comp, str):
            return cls.name == comp
        elif issubclass(comp, ACLTypeBase):
            return cls.id == comp.id
        else:
            return False

    def __ne__(cls, comp):
        return not cls == comp

    def __le__(cls, comp):
        if isinstance(comp, int):
            return cls.id <= comp
        elif issubclass(comp, ACLTypeBase):
            return cls.id <= comp.id
        else:
            return False


class ACLTypeBase(metaclass=MetaACLType):
    pass


class ACLType(Iteratable):
    Nothing = type(
        "ACLTypeNone",
        (ACLTypeBase,),
        {"id": (1 << 0), "name": "nothing", "label": "Nothing"},
    )
    Readable = type(
        "ACLTypeReadable",
        (ACLTypeBase,),
        {"id": (1 << 1), "name": "readable", "label": "Readable"},
    )
    Writable = type(
        "ACLTypeWritable",
        (ACLTypeBase,),
        {"id": (1 << 2), "name": "writable", "label": "Writable"},
    )
    Full = type(
        "ACLTypeFull",
        (ACLTypeBase,),
        {"id": (1 << 3), "name": "full", "label": "Full Controllable"},
    )

    @classmethod
    def all(cls):
        return [cls.Nothing, cls.Readable, cls.Writable, cls.Full]

    @classmethod
    def availables(cls):
        return [cls.Readable, cls.Writable, cls.Full]


def get_permitted_objects(user, model, permission_level):
    # This method assumes that model is a subclass of ACLBase
    return [
        x for x in model.objects.all() if user.has_permission(x, permission_level) and x.is_active
    ]
