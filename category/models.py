from django.db import models

from acl.models import ACLBase, ACLObjType


class Category(ACLBase):
    note = models.CharField(max_length=500, blank=True, default="")
    priority = models.IntegerField(default=0)

    @classmethod
    def all(kls):
        return Category.objects.order_by("-priority")

    def __init__(self, *args, **kwargs):
        super(Category, self).__init__(*args, **kwargs)
        self.objtype = ACLObjType.Category
