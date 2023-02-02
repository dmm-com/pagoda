import importlib
import re
from datetime import datetime

from django.contrib.auth.models import Permission
from django.db import models
from django.utils.timezone import make_aware

from airone.lib.acl import ACLObjType, ACLType
from airone.lib.log import Logger
from role.models import HistoricalPermission
from user.models import User


# Add comparison operations to the Permission model
def _get_acltype(permission):
    if not any([permission.name == x.name for x in ACLType.all()]):
        return 0
    return int(permission.codename.split(".")[-1])


def _get_objid(permission):
    if not any([permission.name == x.name for x in ACLType.all()]):
        return 0
    return int(permission.codename.split(".")[0])


Permission.get_aclid = lambda self: _get_acltype(self)
Permission.get_objid = lambda self: _get_objid(self)
Permission.__le__ = lambda self, comp: _get_acltype(self) <= _get_acltype(comp)
Permission.__ge__ = lambda self, comp: _get_acltype(self) >= _get_acltype(comp)


class HistoricalDifference(object):
    def __init__(self, field_val, prev_val, next_val):
        self.field = field_val
        self.prev = prev_val
        self.next = next_val


class ACLBase(models.Model):
    name = models.CharField(max_length=200)
    is_public = models.BooleanField(default=True)
    created_user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    is_active = models.BooleanField(default=True)
    status = models.IntegerField(default=0)
    default_permission = models.IntegerField(default=ACLType.Nothing().id)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    deleted_user = models.ForeignKey(
        User, null=True, on_delete=models.DO_NOTHING, related_name="deleted_user"
    )
    deleted_time = models.DateTimeField(null=True)

    # This fields describes the sub-class of this object
    objtype = models.IntegerField(default=0)

    def save(self, update_fields=None, *args, **kwargs):
        """This forcely adds updated_time to update_fields parameter when it's not specified
        on its parameter.
        """
        new_update_fields = update_fields
        if isinstance(update_fields, list) and "updated_time" not in update_fields:
            new_update_fields = update_fields + ["updated_time"]

        return super(ACLBase, self).save(update_fields=new_update_fields, *args, **kwargs)

    def get_diff(instance, offset=0):
        ret = []
        try:
            (before_last, last) = list(reversed(instance.history.order_by("history_id")))[
                offset : offset + 2
            ]
            for change in before_last.diff_against(last, excluded_fields=["status"]).changes:
                ret.append(HistoricalDifference(change.field, change.old, change.new))

        except AttributeError as e:
            Logger.warn(str(e))

        return ret

    def show_diff(self, offset=0):
        for diff in self.get_diff(offset):
            print("{} changed from {} to {}".format(diff.field, diff.prev, diff.next))

    def save_without_historical_record(self, *args, **kwargs):
        self.skip_history_when_saving = True
        try:
            ret = self.save(*args, **kwargs)
        finally:
            del self.skip_history_when_saving
        return ret

    def set_status(self, val):
        self.status |= val
        self.save_without_historical_record(update_fields=["status"])

    def del_status(self, val):
        self.status &= ~val
        self.save_without_historical_record(update_fields=["status"])

    def get_status(self, val):
        return self.status & val

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.name = "%s_deleted_%s" % (
            self.name,
            datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
        self.deleted_time = make_aware(datetime.now())
        self.deleted_user = kwargs.get("deleted_user")
        self.save()

    def restore(self, *args, **kwargs):
        self.is_active = True
        self.name = re.sub(r"_deleted_[0-9_]*$", "", self.name)
        self.deleted_user = None
        self.deleted_time = None
        self.save()

    def inherit_acl(self, aclobj):
        if not isinstance(aclobj, ACLBase):
            raise TypeError("specified object(%s) is not ACLBase object")

        # inherit parameter of ACL
        self.is_public = aclobj.is_public
        self.default_permission = aclobj.default_permission

    def is_acl_updated(self, is_public, default_permission):
        # checks each parameters that are different between current object parameters
        if self.is_public != is_public or self.default_permission != default_permission:
            return True

    @property
    def readable(self):
        return self._get_permission(ACLType.Readable.id)

    @property
    def writable(self):
        return self._get_permission(ACLType.Writable.id)

    @property
    def full(self):
        return self._get_permission(ACLType.Full.id)

    def _get_permission(self, acltype):
        return HistoricalPermission.objects.get(codename="%s.%s" % (self.id, acltype))

    def get_subclass_object(self):
        # Use importlib to prevent circular import
        if self.objtype == ACLObjType.Entity:
            model = importlib.import_module("entity.models").Entity
        elif self.objtype == ACLObjType.EntityAttr:
            model = importlib.import_module("entity.models").EntityAttr
        elif self.objtype == ACLObjType.Entry:
            model = importlib.import_module("entry.models").Entry
        elif self.objtype == ACLObjType.EntryAttr:
            model = importlib.import_module("entry.models").Attribute
        else:
            # set ACLBase model
            model = type(self)

        return model.objects.get(id=self.id)

    def is_same_object(self, comp):
        return all([self[x] == comp[x] for x in self._IMPORT_INFO["header"]])

    @classmethod
    def search(kls, query):
        results = []
        for obj in kls.objects.filter(name__icontains=query):
            results.append(
                {
                    "type": kls.__name__,
                    "object": obj,
                    "hint": "",
                }
            )

        return results
