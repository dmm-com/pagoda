from typing import Optional

from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from acl.models import ACLBase
from airone.lib.acl import ACLObjType
from webhook.models import Webhook


class EntityAttr(ACLBase):
    # This parameter is needed to make a relationship to the corresponding Entity at importing
    parent_entity = models.ForeignKey("Entity", on_delete=models.DO_NOTHING)

    type = models.IntegerField()
    is_mandatory = models.BooleanField(default=False)
    referral = models.ManyToManyField(
        ACLBase, default=[], blank=True, related_name="referred_attr_base"
    )
    index = models.IntegerField(default=0)

    # When this parameters set, all entries which are related to the parent_entity will be analyzed
    # at the dashboard of entity
    is_summarized = models.BooleanField(default=False)

    # When an entry is deleted, another entry that is referred from this Attribute will be delete,
    # if this parameter set.
    is_delete_in_chain = models.BooleanField(default=False)

    note = models.CharField(max_length=200, blank=True, default="")

    history = HistoricalRecords(m2m_fields=[referral], excluded_fields=["status", "updated_time"])

    def __init__(self, *args, **kwargs):
        super(ACLBase, self).__init__(*args, **kwargs)
        self.objtype = ACLObjType.EntityAttr.value

    def is_updated(self, name, is_mandatory, is_delete_in_chain, index):
        # checks each parameters that are different between current object parameters
        if (
            self.name != name
            or self.is_mandatory != is_mandatory
            or self.is_delete_in_chain != is_delete_in_chain
            or self.index != int(index)
        ):
            return True

    def is_referral_updated(self, refs):
        # checks each parameters that are different between current object parameters
        return sorted([x.id for x in self.referral.all()]) != sorted(refs)

    def referral_clear(self):
        # In order not to leave a historical record
        self.skip_history_when_saving = True
        try:
            self.referral.clear()
        finally:
            del self.skip_history_when_saving

    def add_referral(self, referral):
        adding_referral = None
        if isinstance(referral, list):
            [self.add_referral(x) for x in referral if x]

        elif isinstance(referral, str):
            adding_referral = Entity.objects.filter(name=referral, is_active=True).first()

        elif isinstance(referral, int) and not isinstance(referral, bool):  # noqa: E721
            adding_referral = Entity.objects.filter(id=referral, is_active=True).first()

        elif isinstance(referral, Entity) and referral.is_active:
            adding_referral = referral

        # Add referral when a valid referral is passed
        if adding_referral:
            self.referral.add(adding_referral)

    def save(self, *args, **kwargs):
        max_attributes_per_entity: Optional[int] = settings.MAX_ATTRIBUTES_PER_ENTITY
        if (
            max_attributes_per_entity
            and EntityAttr.objects.filter(parent_entity=self.parent_entity).count()
            >= max_attributes_per_entity
        ):
            raise RuntimeError("The number of attributes per entity is over the limit")
        return super(EntityAttr, self).save(*args, **kwargs)


class Entity(ACLBase):
    STATUS_TOP_LEVEL = 1 << 0
    STATUS_CREATING = 1 << 1
    STATUS_EDITING = 1 << 2

    note = models.CharField(max_length=200, blank=True)
    attrs = models.ManyToManyField(EntityAttr)

    # This indicates informatoin where to send request for notification
    webhooks = models.ManyToManyField(Webhook, default=[], related_name="registered_entity")

    history = HistoricalRecords(m2m_fields=[attrs], excluded_fields=["status", "updated_time"])

    def __init__(self, *args, **kwargs):
        super(Entity, self).__init__(*args, **kwargs)
        self.objtype = ACLObjType.Entity.value

    def save(self, *args, **kwargs):
        max_entities: Optional[int] = settings.MAX_ENTITIES
        if max_entities and Entity.objects.count() >= max_entities:
            raise RuntimeError("The number of entities is over the limit")
        return super(Entity, self).save(*args, **kwargs)
