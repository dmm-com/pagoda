import enum

__all__ = ["ACLType", "ACLObjType"]


@enum.unique
class ACLObjType(enum.IntEnum):
    Entity = 1 << 0
    EntityAttr = 1 << 1
    Entry = 1 << 2
    EntryAttr = 1 << 3
    Category = 1 << 4


class ACLType(enum.IntEnum):
    Nothing = 1 << 0
    Readable = 1 << 1
    Writable = 1 << 2
    Full = 1 << 3

    @property
    def id(self):
        return self.value

    @property
    def name(self):
        names = {
            self.Nothing: "nothing",
            self.Readable: "readable",
            self.Writable: "writable",
            self.Full: "full",
        }
        return names[self.value]

    @property
    def label(self):
        labels = {
            self.Nothing: "Nothing",
            self.Readable: "Readable",
            self.Writable: "Writable",
            self.Full: "Full Controllable",
        }
        return labels[self.value]

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
