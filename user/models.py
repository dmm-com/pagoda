from importlib import import_module

from django.db import models
from django.contrib.auth.models import User as DjangoUser
from airone.lib.acl import ACLTypeBase
from group.models import Group

from rest_framework.authtoken.models import Token

from datetime import datetime


class User(DjangoUser):
    MAXIMUM_TOKEN_LIFETIME = 10 ** 8
    TOKEN_LIFETIME = 86400

    # These constants describe where user data is stored.
    AUTH_TYPE_LOCAL = 1 << 0
    AUTH_TYPE_LDAP = 1 << 1

    authenticate_type = models.IntegerField(default=AUTH_TYPE_LOCAL)
    authorized_type = models.IntegerField(default=0)
    token_lifetime = models.IntegerField(default=TOKEN_LIFETIME)

    # to make a polymorphism between the Group model
    @property
    def permissions(self):
        return self.user_permissions

    @property
    def token(self):
        return Token.objects.get_or_create(user=self)[0]

    def _user_has_permission(self, target_obj, permission_level):
        return any([permission_level.id <= x.get_aclid()
                   for x in self.permissions.all() if target_obj.id == x.get_objid()])

    def _group_has_permission(self, target_obj, permission_level, groups):
        return any(sum([[permission_level.id <= x.get_aclid()
                   for x in g.permissions.all() if target_obj.id == x.get_objid()] for g in groups],
                   []))

    def is_permitted(self, target_obj, permission_level, groups=[]):
        if not groups:
            groups = self.groups.all()

        return (self._user_has_permission(target_obj, permission_level) or
                self._group_has_permission(target_obj, permission_level, groups))

    def may_permitted(self, target_obj, expected_permission, is_public, default_permission,
                      acl_settings):
        '''
        This checks specified permission settings have expected_permission for this user

        Return value:
            - True: user has expected_permission
            - False: user doesn't have expected_permission
        '''
        if self.is_superuser:
            return True

        if is_public:
            return True

        if expected_permission <= default_permission:
            return True

        groups = [g.id for g in self.groups.all()]
        for acl_data in [x for x in acl_settings if x['value']]:
            if (acl_data['member_type'] == 'user' and
                    int(acl_data['member_id']) == self.id and
                    int(acl_data['value']) >= expected_permission):
                return True

            elif (acl_data['member_type'] == 'group' and
                  int(acl_data['member_id']) in groups and
                  int(acl_data['value']) >= expected_permission):
                return True

            # get rid of group id for checking permission
            if int(acl_data['member_id']) in groups:
                groups.remove(int(acl_data['member_id']))

        # If input won't change current user's permission and user has permission originally,
        # then this permits to change permissoin
        args = [target_obj, expected_permission]
        if not any(
                [int(x['member_id']) == self.id for x in acl_settings]
                ) and self._user_has_permission(*args):
            return True

        if groups and self._group_has_permission(*(args + [Group.objects.filter(id__in=groups)])):
            return True

        return False

    def has_permission(self, target_obj, permission_level, groups=[]):
        # The case that parent data structure (Entity in Entry, or EntityAttr in Attribute)
        # doesn't permit, access to the children's objects are also not permitted.
        if ((isinstance(target_obj, import_module('entry.models').Entry) or
             isinstance(target_obj, import_module('entry.models').Attribute)) and
            (not self.is_permitted(target_obj, permission_level) and
             not self.has_permission(target_obj.schema, permission_level))):
            return False

        # A bypass processing to rapidly return.
        # This condition is effective when the public objects are majority.
        if target_obj.is_public or self.is_superuser:
            return True

        # This try-catch syntax is needed because the 'issubclass' may occur a
        # TypeError exception when permission_level is not object.
        try:
            if not issubclass(permission_level, ACLTypeBase):
                return False
        except TypeError:
            return False

        # Checks that the default permission permits to access, or not
        if permission_level <= target_obj.default_permission:
            return True

        return self.is_permitted(target_obj, permission_level, groups)

    def get_acls(self, aclobj):
        return self.permissions.filter(codename__regex=(r'^%d\.' % aclobj.id))

    def delete(self):
        """
        Override Model.delete method of Django
        """
        self.is_active = False
        self.username = "%s_deleted_%s" % (self.username, datetime.now().strftime("%Y%m%d_%H%M%S"))
        self.email = "deleted__%s" % (self.email)
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

    target_obj = models.ForeignKey(import_module('acl.models').ACLBase,
                                   related_name='referred_target_obj',
                                   on_delete=models.SET_NULL, null=True)
    time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    operation = models.IntegerField(default=0)
    text = models.CharField(max_length=512)
    is_detail = models.BooleanField(default=False)

    # This parameter is needed to record related operation histories
    details = models.ManyToManyField('History')

    def add_attr(self, target, text=''):
        detail = History.register(target=target,
                                  operation=History.ADD_ATTR,
                                  user=self.user,
                                  text=text,
                                  is_detail=True)
        self.details.add(detail)

    def mod_attr(self, target, text=''):
        detail = History.register(target=target,
                                  operation=History.MOD_ATTR,
                                  user=self.user,
                                  text=text,
                                  is_detail=True)
        self.details.add(detail)

    def del_attr(self, target, text=''):
        detail = History.register(target=target,
                                  operation=History.DEL_ATTR,
                                  user=self.user,
                                  text=text,
                                  is_detail=True)
        self.details.add(detail)

    def mod_entity(self, target, text=''):
        detail = History.register(target=target,
                                  operation=History.MOD_ENTITY,
                                  user=self.user,
                                  text=text,
                                  is_detail=True)
        self.details.add(detail)

    @classmethod
    def register(kls, user, target, operation, is_detail=False, text=''):
        if kls._type_check(target, operation):
            return kls.objects.create(target_obj=target,
                                      user=user,
                                      operation=operation,
                                      text=text,
                                      is_detail=is_detail)
        else:
            raise TypeError("Couldn't register history '%s' because of invalid type" % str(target))

    @classmethod
    def _type_check(kls, target, operation):
        if ((operation & kls.TARGET_ENTITY and
             isinstance(target, import_module('entity.models').Entity) or
            (operation & kls.TARGET_ATTR and
                 isinstance(target, import_module('entity.models').EntityAttr)) or
            (operation & kls.TARGET_ENTRY and
                 isinstance(target, import_module('entry.models').Entry)))):
            return True
        else:
            return False
