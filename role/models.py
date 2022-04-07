from django.db import models
from group.models import Group
from user.models import User
from django.contrib.auth.models import Permission


class Role(models.Model):
    name = models.CharField(max_length=200, unique=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    is_active = models.BooleanField(default=True)

    users = models.ManyToManyField(User, related_name='role')
    groups = models.ManyToManyField(Group, related_name='role')
    admin_users = models.ManyToManyField(User, related_name='admin_role')
    admin_groups = models.ManyToManyField(Group, related_name='admin_role')

    @classmethod
    def editable(kls, user, admin_users, admin_groups):
        # This checks whether spcified user is belonged to the specified
        # admin_users and admin_groups.
        if user.is_superuser:
            return True

        if user.id in [u.id for u in admin_users]:
            return True

        if bool(set([g.id for g in user.groups.all()]) &
                set([g.id for g in admin_groups])):
            return True

        return False

    def is_belonged_to(self, user: User):
        """check wether specified User is belonged to this Role"""
        if user.id in [u.id for u in self.users.filter(is_active=True)]:
            return True

        if bool(set([g.id for g in user.groups.all()]) &
                set([g.id for g in self.groups.all()])):
            return True

        return False

    def is_editable(self, user):
        """check wether specified User has permission to edit this Role"""
        return Role.editable(user,
                             list(self.admin_users.filter(is_active=True)),
                             list(self.admin_groups.all()))

    def is_permitted(self, target_obj, permission_level):
        return any([permission_level.id <= x.get_aclid()
                   for x in self.permissions.filter(codename__startswith=(str(target_obj.id)+'.'))])
