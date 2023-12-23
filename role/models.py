import importlib
import sys
from datetime import datetime
from typing import List, Optional

from django.contrib.auth.models import Group, Permission
from django.db import models
from django.db.models import Q
from simple_history.models import HistoricalRecords

from airone import settings
from airone.lib.acl import ACLType
from airone.lib.types import AttrTypeValue


class Role(models.Model):
    name = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    users = models.ManyToManyField("user.User", related_name="role", blank=True)
    groups = models.ManyToManyField("group.Group", related_name="role", blank=True)
    admin_users = models.ManyToManyField("user.User", related_name="admin_role", blank=True)
    admin_groups = models.ManyToManyField("group.Group", related_name="admin_role", blank=True)

    @classmethod
    def editable(kls, user, admin_users, admin_groups: List[Group]):
        # This checks whether spcified user is belonged to the specified
        # admin_users and admin_groups.
        if user.is_superuser:
            return True

        if user.id in [u.id for u in admin_users]:
            return True

        if bool(set([g.id for g in user.belonging_groups()]) & set([g.id for g in admin_groups])):
            return True

        return False

    def is_belonged_to(self, user, as_member=False):
        """This checks wether specified User is belonged to this Role.
        When "as_member" parameter is True, then this method only doesn't check
        admin users and groups.
        """
        if user.id in [
            u.id
            for u in set(
                list(self.users.filter(is_active=True))
                + ([] if as_member else list(self.admin_users.filter(is_active=True)))
            )
        ]:
            return True

        if bool(
            set([g.id for g in user.belonging_groups()])
            & set(
                [
                    g.id
                    for g in set(
                        list(self.groups.filter(is_active=True))
                        + ([] if as_member else list(self.admin_groups.filter(is_active=True)))
                    )
                ]
            )
        ):
            return True

        return False

    def is_editable(self, user):
        """check wether specified User has permission to edit this Role"""
        return Role.editable(
            user,
            list(self.admin_users.filter(is_active=True)),
            list(self.admin_groups.all()),
        )

    def is_permitted(self, target_obj, permission_level):
        """This method has regulation
        * You don't call this method to check object permission directly because,
          this method don't care about hieralchical data structure
          (e.g. Entity/Entry, EntityAttr/Attribute).
        """
        return any(
            [
                permission_level.id <= x.get_aclid()
                for x in self.permissions.filter(codename__startswith=(str(target_obj.id) + "."))
            ]
        )

    def save(self, *args, **kwargs):
        """
        Override Model.save method of Django
        """
        max_roles: Optional[int] = settings.MAX_ROLES
        if max_roles and Role.objects.count() >= max_roles:
            raise RuntimeError("The number of roles is over the limit")
        return super(Role, self).save(*args, **kwargs)

    def delete(self):
        """
        Override Model.delete method of Django
        """
        self.is_active = False
        self.name = "%s_deleted_%s" % (
            self.name,
            datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
        self.save(update_fields=["is_active", "name"])

        for entry in self.get_referred_entries():
            entry.register_es()

    def get_current_permission(self, aclbase) -> int:
        permissions = [x for x in self.permissions.all() if x.get_objid() == aclbase.id]
        if permissions:
            return permissions[0].get_aclid()
        else:
            return ACLType.Nothing().id

    def get_referred_entries(self, entity_name=None):
        # make query to identify AttributeValue that specify this Role instance
        query = Q(
            Q(
                is_latest=True,
                parent_attr__schema__type=AttrTypeValue["role"],
            )
            | Q(
                parent_attrv__is_latest=True,
                parent_attr__schema__type=AttrTypeValue["array_role"],
            ),
            value=str(self.id),
            parent_attr__parent_entry__is_active=True,
            parent_attr__parent_entry__schema__is_active=True,
        )
        if entity_name:
            query = Q(query, parent_attr__parent_entry__schema__name=entity_name)

        # import entry.models if it's necessary
        if "entry" in sys.modules:
            entry_model = sys.modules["entry"].models
        else:
            entry_model = importlib.import_module("entry.models")

        # get Entries that has AttributeValues, which specify this Role instance.
        return entry_model.Entry.objects.filter(
            pk__in=entry_model.AttributeValue.objects.filter(query).values_list(
                "parent_attr__parent_entry", flat=True
            )
        )


class HistoricalPermission(Permission):
    """
    3 HistoricalPermission objects are generated for each object of ACLBase model.
    A large number of ACLBase objects has a significant impact on performance.
    In that case, please set the index below.

    mysql> CREATE INDEX permission_codename_idx ON auth_permission (codename);`

    This is because the permission model is an external library and cannot be changed.

    Exact match filtering by code name is faster.
    NG: HistoricalPermission.objects.filter(codename__startswith="%s." % aclbase.id)
    OK: HistoricalPermission.objects.filter(
        Q(codename="%s.%s" % (aclbase.id, ACLType.Full.id))|
        Q(codename="%s.%s" % (aclbase.id, ACLType.Writable.id))|
        Q(codename="%s.%s" % (aclbase.id, ACLType.Readable.id))
    )
    """

    roles = models.ManyToManyField(Role, related_name="permissions", blank=True)
    history = HistoricalRecords(m2m_fields=[roles])
