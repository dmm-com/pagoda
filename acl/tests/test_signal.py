from django.test import TestCase
from django.contrib.auth.models import Permission

from acl.models import ACLBase
from airone.lib.acl import ACLType
from entity.models import Entity, EntityAttr
from entry.models import Entry, Attribute
from user.models import User


class SignalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="foo", email="hoge@example.com", password="fuga")

    def _check_object_permissions(self, obj):
        self.assertTrue(
            Permission.objects.filter(
                name="readable", codename="%s.%d" % (obj.id, ACLType.Readable.id)
            )
        )
        self.assertTrue(
            Permission.objects.filter(
                name="writable", codename="%s.%d" % (obj.id, ACLType.Writable.id)
            )
        )
        self.assertTrue(
            Permission.objects.filter(name="full", codename="%s.%d" % (obj.id, ACLType.Full.id))
        )

    def test_aclbase(self):
        # This checks signal processing creates permission objects after creating object
        obj = ACLBase.objects.create(name="object", created_user=self.user)
        self._check_object_permissions(obj)

        obj.name = "changedName"
        obj.save(update_fields=["name"])
        self.assertTrue(ACLBase.objects.filter(name="changedName", is_active=True).exists())

    def test_entity(self):
        # This checks signal processing creates permission objects after creating object
        obj = Entity.objects.create(name="object", created_user=self.user)
        self._check_object_permissions(obj)

        obj.name = "changedName"
        obj.save(update_fields=["name"])
        self.assertTrue(Entity.objects.filter(name="changedName", is_active=True).exists())

    def test_entity_attr(self):
        # This checks signal processing creates permission objects after creating object
        entity = Entity.objects.create(name="object", created_user=self.user)
        obj = EntityAttr.objects.create(name="object", created_user=self.user, parent_entity=entity)
        self._check_object_permissions(obj)

        obj.name = "changedName"
        obj.save(update_fields=["name"])
        self.assertTrue(EntityAttr.objects.filter(name="changedName", is_active=True).exists())

    def test_entry(self):
        # This checks signal processing creates permission objects after creating object
        entity = Entity.objects.create(name="object", created_user=self.user)
        obj = Entry.objects.create(name="object", created_user=self.user, schema=entity)
        self._check_object_permissions(obj)

        obj.name = "changedName"
        obj.save(update_fields=["name"])
        self.assertTrue(Entry.objects.filter(name="changedName", is_active=True).exists())

    def test_attribute(self):
        # This checks signal processing creates permission objects after creating object
        entity = Entity.objects.create(name="object", created_user=self.user)
        entity_attr = EntityAttr.objects.create(
            name="object", created_user=self.user, parent_entity=entity
        )
        entry = Entry.objects.create(name="object", created_user=self.user, schema=entity)
        obj = Attribute.objects.create(
            name="object", created_user=self.user, schema=entity_attr, parent_entry=entry
        )
        self._check_object_permissions(obj)

        obj.name = "changedName"
        obj.save(update_fields=["name"])
        self.assertTrue(Attribute.objects.filter(name="changedName", is_active=True).exists())
