from django.db import models

from acl.models import ACLBase


class Category(ACLBase):
    note = models.CharField(max_length=500, blank=True, default="")
