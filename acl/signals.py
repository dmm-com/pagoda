from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.db.models import Q
from django.dispatch import receiver

from airone.lib.acl import ACLType
from entity.models import Entity, EntityAttr
from entry.models import Attribute, Entry
from role.models import HistoricalPermission

from .models import ACLBase


def create_permission(instance):
    content_type = ContentType.objects.get_for_model(instance)
    for acltype in ACLType.availables():
        codename = "%s.%s" % (instance.id, acltype.id)
        if acltype.id == ACLType.Readable.id:
            HistoricalPermission(
                name=acltype.name,
                codename=codename,
                content_type=content_type,
                target_obj_id=instance.id,
                is_readable=True,
            ).save()
        if acltype.id == ACLType.Writable.id:
            HistoricalPermission(
                name=acltype.name,
                codename=codename,
                content_type=content_type,
                target_obj_id=instance.id,
                is_writable=True,
            ).save()
        if acltype.id == ACLType.Full.id:
            HistoricalPermission(
                name=acltype.name,
                codename=codename,
                content_type=content_type,
                target_obj_id=instance.id,
                is_full=True,
            ).save()


@receiver(post_save, sender=ACLBase)
def aclbase_create_permission(sender, instance, created, **kwargs):
    if created:
        create_permission(instance)


@receiver(post_save, sender=Entity)
def entity_create_permission(sender, instance, created, **kwargs):
    if created:
        create_permission(instance)


@receiver(post_save, sender=EntityAttr)
def entity_attr_create_permission(sender, instance, created, **kwargs):
    if created:
        create_permission(instance)


@receiver(post_save, sender=Entry)
def entry_create_permission(sender, instance, created, **kwargs):
    if created:
        create_permission(instance)


@receiver(post_save, sender=Attribute)
def attribute_create_permission(sender, instance, created, **kwargs):
    if created:
        create_permission(instance)
