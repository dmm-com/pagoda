import math
from typing import Any, List, Optional, Union

from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from acl.models import ACLBase
from airone.lib.acl import ACLObjType
from airone.lib.types import AttrDefaultValue, AttrType
from category.models import Category
from webhook.models import Webhook


class ItemNameType(models.TextChoices):
    USER = ("US", "USER")  # Specify Item name manually by user
    UUID = ("ID", "UUID")  # Specify Item name automatically by system using UUID
    ATTR = ("AT", "Attribute")  # Specify Item name automatically by system using Attribute


class EntityAttr(ACLBase):
    # This parameter is needed to make a relationship to the corresponding Entity at importing
    parent_entity = models.ForeignKey("Entity", related_name="attrs", on_delete=models.DO_NOTHING)

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
    default_value = models.JSONField(null=True, blank=True, default=None)

    history = HistoricalRecords(m2m_fields=[referral], excluded_fields=["status", "updated_time"])

    # These fields describes the configuration of specifying Item name from Attriute
    # Only used when ItemNameType.ATTR is selected for Entity.item_name_type
    name_order = models.IntegerField(default=0)
    name_prefix = models.CharField(max_length=20, blank=True, default="")
    name_postfix = models.CharField(max_length=20, blank=True, default="")

    def __init__(self, *args, **kwargs):
        super(ACLBase, self).__init__(*args, **kwargs)
        self.objtype = ACLObjType.EntityAttr

    def is_updated(self, name, is_mandatory, is_delete_in_chain, index, default_value=None) -> bool:
        # checks each parameters that are different between current object parameters
        if (
            self.name != name
            or self.is_mandatory != is_mandatory
            or self.is_delete_in_chain != is_delete_in_chain
            or self.index != int(index)
            or self.default_value != default_value
        ):
            return True
        return False

    def is_referral_updated(self, refs) -> bool:
        # checks each parameters that are different between current object parameters
        return sorted([x.id for x in self.referral.all()]) != sorted(refs)

    def referral_clear(self):
        # In order not to leave a historical record
        self.skip_history_when_saving = True
        try:
            self.referral.clear()
        finally:
            del self.skip_history_when_saving

    def add_referral(
        self, referral: Union["Entity", str, int, List[Union["Entity", str, int]]]
    ) -> None:
        adding_referral = None
        if isinstance(referral, list):
            for x in referral:
                if x:
                    self.add_referral(x)

        elif isinstance(referral, str):
            adding_referral = Entity.objects.filter(name=referral, is_active=True).first()

        elif isinstance(referral, int) and not isinstance(referral, bool):  # noqa: E721
            adding_referral = Entity.objects.filter(id=referral, is_active=True).first()

        elif isinstance(referral, Entity) and referral.is_active:
            adding_referral = referral

        # Add referral when a valid referral is passed
        if adding_referral:
            self.referral.add(adding_referral)

    def save(self, *args, **kwargs) -> None:
        max_attributes_per_entity: Optional[int] = settings.MAX_ATTRIBUTES_PER_ENTITY
        if (
            max_attributes_per_entity
            and EntityAttr.objects.filter(parent_entity=self.parent_entity).count()
            >= max_attributes_per_entity
        ):
            raise RuntimeError("The number of attributes per entity is over the limit")
        return super(EntityAttr, self).save(*args, **kwargs)

    def get_default_value(self) -> Any:
        """Returns custom default value if set, otherwise returns type-based default value"""
        if self.default_value is not None:
            return self.default_value
        return AttrDefaultValue.get(self.type, None)

    def validate_default_value(self, value: Any) -> bool:
        """Validates if the given value is valid for this attribute type as default value"""
        if value is None:
            return True  # None is always valid

        # Only String, Text, Boolean, Number types support custom default values, currently
        supported_types = [AttrType.STRING, AttrType.TEXT, AttrType.BOOLEAN, AttrType.NUMBER]
        if self.type not in supported_types:
            return False

        # Type-specific validation for supported types
        if self.type == AttrType.STRING or self.type == AttrType.TEXT:
            return isinstance(value, str)
        elif self.type == AttrType.BOOLEAN:
            return isinstance(value, bool)
        elif self.type == AttrType.NUMBER:
            # Only accept int/float types, but reject bool (bool is a subclass of int)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False
            # Reject NaN and Infinity values
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                return False
            return True

        return True


class Entity(ACLBase):
    STATUS_TOP_LEVEL = 1 << 0
    STATUS_CREATING = 1 << 1
    STATUS_EDITING = 1 << 2

    # This describes which Attribute types are selectable when itm_name_type is ATTR
    ITEM_NAME_SELECTABLE_TYPES = [AttrType.STRING, AttrType.OBJECT]

    note = models.CharField(max_length=200, blank=True)

    # This indicates informatoin where to send request for notification
    webhooks = models.ManyToManyField(Webhook, default=[], related_name="registered_entity")

    history = HistoricalRecords(excluded_fields=["status", "updated_time"])

    # The Category that groups Models according to their purpose (which is defined by User)
    categories = models.ManyToManyField(Category, default=[], related_name="models")

    # This is a pattern for making Item that that is written by regex
    item_name_pattern = models.CharField(max_length=400, blank=True)

    # This represents how to specify Item name
    item_name_type = models.CharField(
        choices=ItemNameType.choices, max_length=10, default=ItemNameType.USER
    )

    def __init__(self, *args, **kwargs):
        super(Entity, self).__init__(*args, **kwargs)
        self.objtype = ACLObjType.Entity

    def save(self, *args, **kwargs) -> None:
        max_entities: Optional[int] = settings.MAX_ENTITIES
        if max_entities and Entity.objects.count() >= max_entities:
            raise RuntimeError("The number of entities is over the limit")
        return super(Entity, self).save(*args, **kwargs)

    def is_available(self, name: str, exclude_item_ids: Optional[List[int]] = None) -> bool:
        from entry.models import AliasEntry, Entry

        if exclude_item_ids is None:
            exclude_item_ids = []

        if (
            Entry.objects.filter(name=name, schema=self, is_active=True)
            .exclude(id__in=exclude_item_ids)
            .exists()
        ):
            return False
        if AliasEntry.objects.filter(name=name, entry__schema=self, entry__is_active=True).exists():
            return False
        return True
