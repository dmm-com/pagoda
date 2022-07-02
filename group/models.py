from django.db import models
from django.contrib.auth.models import Group as DjangoGroup
from datetime import datetime


class Group(DjangoGroup):
    is_active = models.BooleanField(default=True)
    parent_group = models.ForeignKey(
        "Group", on_delete=models.DO_NOTHING, related_name="subordinates", null=True
    )

    def delete(self):
        """
        Override Model.delete method of Django
        """
        # replace parent_group of subordinates instances
        for child_group in self.subordinates.filter(is_active=True):
            child_group.parent_group = self.parent_group
            child_group.save(update_fields=["parent_group"])

        self.is_active = False
        self.name = "%s_deleted_%s" % (
            self.name,
            datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
        self.save()

    def has_permission(self, target_obj, permission_level):
        """[NOTE]
        This function will be obsoleted, then will be alternated by Role feature
        """
        # A bypass processing to rapidly return.
        # This condition is effective when the public objects are majority.
        if target_obj.is_public:
            return True

        return any(
            [
                permission_level.id <= x.get_aclid()
                for x in self.permissions.all()
                if target_obj.id == x.get_objid()
            ]
        )
