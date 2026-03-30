from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver

from airone.lib.acl import ACLType
from category.models import Category
from entity.models import Entity, EntityAttr
from entry.models import Attribute, Entry
from role.models import HistoricalPermission

from .models import ACLBase


def create_permission(instance: Model) -> None:
    content_type = ContentType.objects.get_for_model(instance)
    for acltype in ACLType.availables():
        codename = "%s.%s" % (instance.id, acltype.id)
        HistoricalPermission(name=acltype.name, codename=codename, content_type=content_type).save()


@receiver(post_save, sender=ACLBase)
def aclbase_create_permission(
    sender: type[ACLBase], instance: ACLBase, created: bool, **kwargs: Any
) -> None:
    if created:
        create_permission(instance)


@receiver(post_save, sender=Category)
def category_create_permission(
    sender: type[Category], instance: Category, created: bool, **kwargs: Any
) -> None:
    if created:
        create_permission(instance)


@receiver(post_save, sender=Entity)
def entity_create_permission(
    sender: type[Entity], instance: Entity, created: bool, **kwargs: Any
) -> None:
    if created:
        create_permission(instance)


@receiver(post_save, sender=EntityAttr)
def entity_attr_create_permission(
    sender: type[EntityAttr], instance: EntityAttr, created: bool, **kwargs: Any
) -> None:
    if created:
        create_permission(instance)


@receiver(post_save, sender=Entry)
def entry_create_permission(
    sender: type[Entry], instance: Entry, created: bool, **kwargs: Any
) -> None:
    if created:
        create_permission(instance)


@receiver(post_save, sender=Attribute)
def attribute_create_permission(
    sender: type[Attribute], instance: Attribute, created: bool, **kwargs: Any
) -> None:
    if created:
        create_permission(instance)
