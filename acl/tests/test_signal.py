from django.test import TestCase
from django.contrib.auth.models import Permission

from acl.models import ACLBase
from airone.lib.types import AttrTypeValue
from entity.models import Entity, EntityAttr
from entry.models import Entry, Attribute
from user.models import User


class SignalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="foo", email="hoge@example.com", password="fuga")

    def test_create_aclbase_object(self):
        for i, model in enumerate([ACLBase, Entity, EntityAttr, Entry, Attribute]):
            if model is EntityAttr:
                obj = model.objects.create(
                    name=i, type=AttrTypeValue["object"], created_user=self.user
                )
            else:
                obj = model.objects.create(name=i, created_user=self.user)

            self.assertTrue(Permission.objects.filter(name="readable", codename="%s.2" % obj.id))
            self.assertTrue(Permission.objects.filter(name="writable", codename="%s.4" % obj.id))
            self.assertTrue(Permission.objects.filter(name="full", codename="%s.8" % obj.id))

    def test_edit_aclebase_object(self):
        for i, model in enumerate([ACLBase, Entity, EntityAttr, Entry, Attribute]):
            if model is EntityAttr:
                obj = model.objects.create(
                    name=i, type=AttrTypeValue["object"], created_user=self.user
                )
            else:
                obj = model.objects.create(name=i, created_user=self.user)

            obj.name = str(i) + "_new"
            obj.save(update_fields=["name"])

            self.assertTrue(model.objects.filter(name=str(i) + "_new", is_active=True).exists())
