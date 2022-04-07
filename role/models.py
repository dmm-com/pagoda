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
    administrative_users = models.ManyToManyField(User, related_name='admin_role')
    administrative_groups = models.ManyToManyField(Group, related_name='admin_role')

    def is_belonged_to(self, user: User):
        """check wether specified User is belonged to this Role"""
        if user.id in [u.id for u in self.users.filter(is_active=True)]:
            return True

        if bool(set([g.id for g in user.groups.all()]) &
                set([g.id for g in self.groups.all()])):
            return True

        return False

    def permit_to_edit(self, user):
        """check wether specified User has permission to edit this Role"""
        if user.is_superuser:
            return True

        if user.id in [u.id for u in self.administrative_users.filter(is_active=True)]:
            return True

        if bool(set([g.id for g in user.groups.all()]) &
                set([g.id for g in self.administrative_groups.all()])):
            return True

        return False

    def is_permitted(self, target_obj, permission_level):
        return any([permission_level.id <= x.get_aclid()
                   for x in self.permissions.filter(codename__startswith=(str(target_obj.id)+'.'))])
