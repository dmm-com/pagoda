from datetime import datetime
from importlib import import_module

from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.authtoken.models import Token

from airone.lib.acl import ACLType, ACLTypeBase
from group.models import Group
from role.models import Role

from django.contrib.auth.models import (
    BaseUserManager,
)


class UserManager(BaseUserManager):
    def create_user(self, request_data, **kwargs):
        user = User(
            username=request_data.get("username"),
            email=request_data.get("email"),
            is_superuser=request_data.get("is_superuser"),
        )
        user.set_password(request_data.get("password"))
        user.save()

        return user


class User(AbstractUser):
    objects = UserManager()

    MAXIMUM_TOKEN_LIFETIME = 10**8
    TOKEN_LIFETIME = 86400

    # These constants describe where user data is stored.
    AUTH_TYPE_LOCAL = 1 << 0
    AUTH_TYPE_LDAP = 1 << 1

    authenticate_type = models.IntegerField(default=AUTH_TYPE_LOCAL)
    authorized_type = models.IntegerField(default=0)
    token_lifetime = models.IntegerField(default=TOKEN_LIFETIME)

    @property
    def airone_groups(self):
        """
        This returns groups that current user just belongs to
        (not include hierarchical parent groups)
        """
        return Group.objects.filter(id__in=[g.id for g in self.groups.all()], is_active=True)

    # to make a polymorphism between the Group model
    @property
    def permissions(self):
        return self.user_permissions

    @property
    def token(self):
        return Token.objects.filter(user=self).first()

    def belonging_groups(self, is_direct_belonging=False):
        """This returns groups that include hierarchical superior groups"""

        def _scan_superior_groups(group, parent_groups):
            if group.parent_group and group.parent_group not in parent_groups:
                parent_groups.append(group.parent_group)
                _scan_superior_groups(group.parent_group, parent_groups)

        if is_direct_belonging:
            return self.airone_groups
        else:
            parent_groups = []
            for group in self.airone_groups:
                _scan_superior_groups(group, parent_groups)

            return set(list(self.airone_groups) + parent_groups)

    def has_permission(self, target_obj, permission_level):
        # A bypass processing to rapidly return.
        # This condition is effective when the public objects are majority.
        if self.is_superuser:
            return True

        # This try-catch syntax is needed because the 'issubclass' may occur a
        # TypeError exception when permission_level is not object.
        try:
            if not issubclass(permission_level, ACLTypeBase):
                return False
        except TypeError:
            return False

        # doesn't permit, access to the children's objects are also not permitted.
        if (
            isinstance(target_obj, import_module("entry.models").Entry)
            or isinstance(target_obj, import_module("entry.models").Attribute)
        ) and not self.has_permission(target_obj.schema, permission_level):
            return False

        # This check processing must be set after checking superior data structure's check
        if target_obj.is_public:
            return True

        # Checks that the default permission permits to access, or not
        if permission_level <= target_obj.default_permission:
            return True

        # This checks Roles that this user and groups, which this user belongs to,
        # have permission of specified permission_level
        belonged_roles = set(
            list(self.role.filter(is_active=True))
            + list(self.admin_role.filter(is_active=True))
            + sum(
                [
                    (
                        list(g.role.filter(is_active=True))
                        + list(g.admin_role.filter(is_active=True))
                    )
                    for g in self.belonging_groups()
                ],
                [],
            )
        )
        for role in belonged_roles:
            if role.is_permitted(target_obj, permission_level):
                return True

        return False

    def is_permitted_to_change(
        self, target_obj, expected_permission, will_be_public, default_permission, acl_settings
    ):
        """
        This checks specified permission settings have expected_permission for this user.

        * Params:
            - acl_settings[dict]: it must have following members
                - role [Role]: Role instance to set ACL
                - value [ACLType]: An ACLType value to set

        * Return value:
            - True: user has expected_permission
            - False: user doesn't have expected_permission

        * Use-case:
            This method is called only when ACL configuration is changed of it and decide
            whether current user has "expected" permission to the target_obj.
        """
        # These are obvious cases when current user has permission to operate target_obj
        if self.is_superuser or will_be_public or expected_permission <= default_permission:
            return True

        for acl_info in acl_settings:
            role = acl_info.get("role")
            if not (role and role.is_belonged_to(self)):
                return False

        # This checks there are any administrative roles that can control this object left
        def _tobe_admin(role):
            for r_info in acl_settings:
                if r_info["role"].id == role.id and r_info["value"] != ACLType.Full.id:
                    return False

            # This means specified "role" has full-control permission to the acl_obj
            return True

        admin_roles = Role.objects.filter(
            permissions__codename="%s.%s" % (target_obj.id, ACLType.Full.id)
        )
        if (
            len(
                [r for r in admin_roles if _tobe_admin(r)]
                + [r for r in acl_settings if r["value"] == ACLType.Full.id]
            )
            == 0
        ):
            return False

        return True

    def delete(self):
        """
        Override Model.delete method of Django
        """
        self.is_active = False
        self.username = "%s_deleted_%s" % (
            self.username,
            datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
        self.email = "deleted__%s" % (self.email)
        for social_auth in self.social_auth.all():
            social_auth.delete()
        self.save()

    # operations for registering History
    def seth_entity_add(self, target):
        return History.register(self, target, History.ADD_ENTITY)

    def seth_entity_mod(self, target):
        return History.register(self, target, History.MOD_ENTITY)

    def seth_entity_del(self, target):
        return History.register(self, target, History.DEL_ENTITY)

    def seth_entry_del(self, target):
        return History.register(self, target, History.DEL_ENTRY)


class History(models.Model):
    """
    These constants describe operations of History and bit-map construct following
    * The last 3-bits (0000xxx)[2]: describe operation flag
      - 001 : ADD
      - 010 : MOD
      - 100 : DEL
    * The last 4-bit or later (xxxx000)[2] describe operation target
      - 001 : Entity
      - 010 : EntityAttr
      - 100 : Entry
    """

    OP_ADD = 1 << 0
    OP_MOD = 1 << 1
    OP_DEL = 1 << 2

    TARGET_ENTITY = 1 << 3
    TARGET_ATTR = 1 << 4
    TARGET_ENTRY = 1 << 5

    ADD_ENTITY = OP_ADD + TARGET_ENTITY
    ADD_ATTR = OP_ADD + TARGET_ATTR
    MOD_ENTITY = OP_MOD + TARGET_ENTITY
    MOD_ATTR = OP_MOD + TARGET_ATTR
    DEL_ENTITY = OP_DEL + TARGET_ENTITY
    DEL_ATTR = OP_DEL + TARGET_ATTR
    DEL_ENTRY = OP_DEL + TARGET_ENTRY

    target_obj = models.ForeignKey(
        import_module("acl.models").ACLBase,
        related_name="referred_target_obj",
        on_delete=models.DO_NOTHING,
    )
    time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    operation = models.IntegerField(default=0)
    text = models.CharField(max_length=512)
    is_detail = models.BooleanField(default=False)

    # This parameter is needed to record related operation histories
    details = models.ManyToManyField("History")

    def add_attr(self, target, text=""):
        detail = History.register(
            target=target,
            operation=History.ADD_ATTR,
            user=self.user,
            text=text,
            is_detail=True,
        )
        self.details.add(detail)

    def mod_attr(self, target, text=""):
        detail = History.register(
            target=target,
            operation=History.MOD_ATTR,
            user=self.user,
            text=text,
            is_detail=True,
        )
        self.details.add(detail)

    def del_attr(self, target, text=""):
        detail = History.register(
            target=target,
            operation=History.DEL_ATTR,
            user=self.user,
            text=text,
            is_detail=True,
        )
        self.details.add(detail)

    def mod_entity(self, target, text=""):
        detail = History.register(
            target=target,
            operation=History.MOD_ENTITY,
            user=self.user,
            text=text,
            is_detail=True,
        )
        self.details.add(detail)

    @classmethod
    def register(kls, user, target, operation, is_detail=False, text=""):
        if kls._type_check(target, operation):
            return kls.objects.create(
                target_obj=target,
                user=user,
                operation=operation,
                text=text,
                is_detail=is_detail,
            )
        else:
            raise TypeError("Couldn't register history '%s' because of invalid type" % str(target))

    @classmethod
    def _type_check(kls, target, operation):
        if (
            operation & kls.TARGET_ENTITY
            and isinstance(target, import_module("entity.models").Entity)
            or (
                operation & kls.TARGET_ATTR
                and isinstance(target, import_module("entity.models").EntityAttr)
            )
            or (
                operation & kls.TARGET_ENTRY
                and isinstance(target, import_module("entry.models").Entry)
            )
        ):
            return True
        else:
            return False
