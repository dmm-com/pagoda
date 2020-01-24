from django.db import models
from django.contrib.auth.models import Group as DjangoGroup
from datetime import datetime

DjangoGroup.get_acls = (lambda x, obj: x.permissions.filter(codename__regex=(r'^%d\.' % obj.id)))


class Group(DjangoGroup):
    is_active = models.BooleanField(default=True)

    def delete(self):
        """
        Override Model.delete method of Django
        """
        self.is_active = False
        self.name = "%s_deleted_%s" % (self.name, datetime.now().strftime("%Y%m%d_%H%M%S"))
        self.save()
