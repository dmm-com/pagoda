from django.db import models
from group.models import Group
from user.models import User
from django.contrib.auth.models import Group as DjangoGroup


class Role(DjangoGroup):
    is_active = models.BooleanField(default=True)

    users = models.ManyToManyField(User, related_name='role')
    groups = models.ManyToManyField(Group, related_name='role')
    administrative_users = models.ManyToManyField(User, related_name='admin_role')
    administrative_groups = models.ManyToManyField(Group, related_name='admin_role')
