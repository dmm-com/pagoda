from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from airone.lib.acl import ACLType
from entity.models import Entity, EntityAttr
from entry.models import Attribute, Entry

from .models import ACLBase


def create_permission(instance):
    content_type = ContentType.objects.get_for_model(instance)
    for acltype in ACLType.availables():
        codename = "%s.%s" % (instance.id, acltype.id)
        Permission(name=acltype.name, codename=codename, content_type=content_type).save()


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
