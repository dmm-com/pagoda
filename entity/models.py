from django.db import models
from airone.lib.acl import ACLObjType
from acl.models import ACLBase


class EntityAttr(ACLBase):
    # This parameter is needed to make a relationship to the corresponding Entity at importing
    parent_entity = models.ForeignKey('Entity', on_delete=models.SET_NULL, null=True)

    type = models.IntegerField(default=0)
    is_mandatory = models.BooleanField(default=False)
    referral = models.ManyToManyField(ACLBase, default=[], related_name='referred_attr_base')
    index = models.IntegerField(default=0)

    # When this parameters set, all entries which are related to the parent_entity will be analyzed
    # at the dashboard of entity
    is_summarized = models.BooleanField(default=False)

    # When an entry is deleted, another entry that is referred from this Attribute will be delete,
    # if this parameter set.
    is_delete_in_chain = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super(ACLBase, self).__init__(*args, **kwargs)
        self.objtype = ACLObjType.EntityAttr

    def is_updated(self, name, is_mandatory, is_delete_in_chain, index, refs):
        # checks each parameters that are different between current object parameters
        if (self.name != name or
                self.is_mandatory != is_mandatory or
                self.is_delete_in_chain != is_delete_in_chain or
                self.index != int(index) or
                sorted([x.id for x in self.referral.all()]) != sorted(refs)):

            return True

        # This means that all specified parameters are same with current object's ones.
        return False

    def unset_latest_flag(self):
        from entry.models import AttributeValue
        AttributeValue.objects.filter(parent_attr__schema=self,
                                      is_latest=True).update(is_latest=False)


class Entity(ACLBase):
    STATUS_TOP_LEVEL = 1 << 0
    STATUS_CREATING = 1 << 1
    STATUS_EDITING = 1 << 2

    note = models.CharField(max_length=200)
    attrs = models.ManyToManyField(EntityAttr)

    def __init__(self, *args, **kwargs):
        super(Entity, self).__init__(*args, **kwargs)
        self.objtype = ACLObjType.Entity
