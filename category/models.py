from typing import Any

from django.db import models
from django.db.models import QuerySet

from acl.models import ACLBase, ACLObjType


class Category(ACLBase):
    note = models.CharField(max_length=500, blank=True, default="")
    priority = models.IntegerField(default=0)

    @classmethod
    def all(kls) -> QuerySet["Category"]:
        return Category.objects.order_by("-priority")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(Category, self).__init__(*args, **kwargs)
        self.objtype = ACLObjType.Category
