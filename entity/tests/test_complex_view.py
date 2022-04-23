import json

from airone.lib.acl import ACLType
from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeStr
from airone.lib.types import AttrTypeArrStr, AttrTypeArrObj
from airone.lib.types import AttrTypeValue

from django.urls import reverse

from entity.models import Entity, EntityAttr
from entry.models import Entry, AttributeValue
from entry import tasks as entry_tasks
from entity import tasks as entity_tasks

from unittest.mock import patch
from unittest.mock import Mock


class ComplexViewTest(AironeViewTest):
    """
    This has complex tests that combine multiple requests across the inter-applicational
    """

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=entry_tasks.create_entry_attrs),
    )
    @patch(
        "entry.tasks.edit_entry_attrs.delay",
        Mock(side_effect=entry_tasks.edit_entry_attrs),
    )
    @patch("entity.tasks.create_entity.delay", Mock(side_effect=entity_tasks.create_entity))
    @patch("entity.tasks.edit_entity.delay", Mock(side_effect=entity_tasks.edit_entity))
    def test_add_attr_after_creating_entry(self):
        """
        This test executes followings
        - create a new Entity(entity) with an EntityAttr(attr)
        - create a new Entry for entity
        - update entity to append new EntityAttrs(arr-str, arr-obj)

        Then, this checks following
        - being able to edit the entry corresponding to the added EntityAttr.
        - enable to edit entry correctly because #152 is fixed
        """
        user = self.admin_login()

        # create an Entity
        params = {
            "name": "entity",
            "note": "",
            "is_toplevel": False,
            "attrs": [
                {
                    "name": "attr",
                    "type": str(AttrTypeStr),
                    "is_delete_in_chain": True,
                    "is_mandatory": False,
                    "row_index": "1",
                },
            ],
        }
        resp = self.client.post(reverse("entity:do_create"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)

        # get created objects
        entity = Entity.objects.get(name="entity")
        attr = entity.attrs.get(name="attr")

        # create an Entry for the created entity
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(attr.id),
                    "type": str(AttrTypeStr),
                    "value": [{"data": "attr-value", "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)

        # get created entry object
        entry = Entry.objects.get(name="entry")
        refer_entity = Entity.objects.create(name="E0", note="", created_user=user)

        # edit entity to append a new Array attributes
        params = {
            "name": "entity",
            "note": "",
            "is_toplevel": False,
            "attrs": [
                {
                    "id": str(attr.id),
                    "name": attr.name,
                    "type": str(attr.type),
                    "is_mandatory": attr.is_mandatory,
                    "is_delete_in_chain": False,
                    "row_index": "1",
                },
                {
                    "name": "arr-str",
                    "type": str(AttrTypeArrStr),
                    "is_mandatory": True,
                    "is_delete_in_chain": False,
                    "row_index": "2",
                },
                {
                    "name": "arr-obj",
                    "type": str(AttrTypeArrObj),
                    "ref_ids": [refer_entity.id],
                    "is_mandatory": True,
                    "is_delete_in_chain": False,
                    "row_index": "3",
                },
            ],
        }
        resp = self.client.post(
            reverse("entity:do_edit", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # Checks that the Attributes associated to the added EntityAttrs are not created
        self.assertEqual(entity.attrs.count(), 3)
        self.assertEqual(entry.attrs.count(), 1)

        resp = self.client.get(reverse("entry:show", args=[entry.id]))
        self.assertEqual(resp.status_code, 200)

        # Checks that the new Attibutes is not created in the show processing
        self.assertEqual(entity.attrs.count(), 3)
        self.assertEqual(entry.attrs.count(), 1)

        attr_str = entry.attrs.get(name=attr.name)
        entity_attr_arr_str = entity.attrs.get(name="arr-str")
        entity_attr_arr_obj = entity.attrs.get(name="arr-obj")
        refer_entry = Entry.objects.create(name="e0", schema=refer_entity, created_user=user)

        # edit to add values to the new attributes
        params = {
            "entry_name": entry.name,
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(attr_str.id),
                    "type": str(attr.type),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
                {
                    "entity_attr_id": str(entity_attr_arr_str.id),
                    "id": "",
                    "type": str(AttrTypeArrStr),
                    "value": [
                        {"data": "foo", "index": 0},
                        {"data": "bar", "index": 1},
                    ],
                    "referral_key": [],
                },
                {
                    "entity_attr_id": str(entity_attr_arr_obj.id),
                    "id": "",
                    "type": str(AttrTypeArrObj),
                    "value": [{"data": refer_entry.id, "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            [attr.get_latest_value().get_value() for attr in entry.attrs.all()],
            ["hoge", ["foo", "bar"], ["e0"]],
        )

    @patch("entity.tasks.create_entity.delay", Mock(side_effect=entity_tasks.create_entity))
    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=entry_tasks.create_entry_attrs),
    )
    def test_inherite_attribute_acl(self):
        """
        This test executes followings
        - create a new Entity(entity) with an EntityAttr(attr)
        - change ACL of attr to be private by admin user
        - create a new Entry(entry1) from entity by admin user
        - switch the user to guest
        - create a new Entry(entry2) from entity by guest user

        Then, this checks following
        - The Entry(entry1) whcih is created by the admin user has one Attribute
        - The Entry(entry2) whcih is created by the guest user has no Attribute
        """
        user = self.admin_login()

        # create an Entity
        params = {
            "name": "entity",
            "note": "",
            "is_toplevel": False,
            "attrs": [
                {
                    "name": "attr",
                    "type": str(AttrTypeStr),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "1",
                },
            ],
        }
        resp = self.client.post(reverse("entity:do_create"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(EntityAttr.objects.count(), 1)

        # set acl of attr
        entityattr = EntityAttr.objects.get(name="attr")
        params = {
            "object_id": str(entityattr.id),
            "object_type": str(entityattr.objtype),
            "acl": [
                {
                    "member_id": str(user.id),
                    "member_type": "user",
                    "value": str(ACLType.Full.id),
                }
            ],
            "default_permission": str(ACLType.Nothing.id),
        }
        resp = self.client.post(reverse("acl:set"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entity.objects.count(), 1)
        self.assertFalse(EntityAttr.objects.get(name="attr").is_public)

        # create Entity by admin
        entity = Entity.objects.get(name="entity")
        params = {
            "entry_name": "entry1",
            "attrs": [
                {
                    "id": str(entityattr.id),
                    "type": str(entityattr.objtype),
                    "value": [{"data": "attr-value", "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), 1)
        entry1 = Entry.objects.get(name="entry1")
        self.assertEqual(entry1.attrs.first().get_latest_value().get_value(), "attr-value")

        # switch to guest user
        self.guest_login()
        entity = Entity.objects.get(name="entity")
        params = {
            "entry_name": "entry2",
            "attrs": [
                {
                    "id": str(entityattr.id),
                    "type": str(entityattr.objtype),
                    "value": [{"data": "attr-value", "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), 2)
        entry2 = Entry.objects.get(name="entry2")
        self.assertEqual(entry2.attrs.first().get_latest_value().get_value(), "")

    @patch("entity.tasks.edit_entity.delay", Mock(side_effect=entity_tasks.edit_entity))
    def test_cache_referred_entry_at_deleting_attr(self):
        user = self.admin_login()

        ref_entity = Entity.objects.create(name="ref_entity", created_user=user)
        ref_entry = Entry.objects.create(name="ref_entry", schema=ref_entity, created_user=user)

        entity = Entity.objects.create(name="entity", created_user=user)
        entity.attrs.add(
            EntityAttr.objects.create(
                name="ref",
                type=AttrTypeValue["object"],
                parent_entity=entity,
                created_user=user,
            )
        )
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        attrv_params = {
            "value": "",
            "created_user": user,
            "parent_attr": entry.attrs.get(name="ref"),
            "referral": ref_entry,
        }
        entry.attrs.get(name="ref").values.add(AttributeValue.objects.create(**attrv_params))

        # make referred entry cache
        ref_entries = ref_entry.get_referred_objects()
        self.assertEqual(list(ref_entries), [entry])
        self.assertEqual(ref_entries.count(), 1)

        entity_attr = entity.attrs.last()
        params = {
            "name": "entity",
            "note": "",
            "is_toplevel": False,
            "attrs": [
                {
                    "id": entity_attr.id,
                    "name": entity_attr.name,
                    "type": str(entity_attr.type),
                    "is_mandatory": entity_attr.is_mandatory,
                    "is_delete_in_chain": False,
                    "ref_ids": [ref_entity.id],
                    "deleted": True,
                    "row_index": "1",
                }
            ],  # delete EntityAttr 'ref'
        }
        resp = self.client.post(
            reverse("entity:do_edit", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        # checks that the cache is cleared because of the removing EntityAttr
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(entity.attrs.filter(is_active=True).count(), 0)
        self.assertEqual(entry.attrs.filter(is_active=True).count(), 1)

    def test_make_cache_referred_entry_after_updating_attr_type(self):
        user = self.admin_login()

        ref_entity = Entity.objects.create(name="ref_entity", created_user=user)
        ref_entry = Entry.objects.create(name="ref_entry", schema=ref_entity, created_user=user)

        entity = Entity.objects.create(name="entity", created_user=user)
        entity.attrs.add(
            EntityAttr.objects.create(
                name="ref",
                type=AttrTypeValue["object"],
                parent_entity=entity,
                created_user=user,
            )
        )
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        attrv_params = {
            "value": "",
            "created_user": user,
            "parent_attr": entry.attrs.get(name="ref"),
            "referral": ref_entry,
        }
        entry.attrs.get(name="ref").values.add(AttributeValue.objects.create(**attrv_params))

        # make referred entry cache
        ref_entries = ref_entry.get_referred_objects()
        self.assertEqual(list(ref_entries), [entry])
        self.assertEqual(ref_entries.count(), 1)

        entity_attr = entity.attrs.last()
        params = {
            "name": "entity",
            "note": "",
            "is_toplevel": False,
            "attrs": [
                {
                    "id": entity_attr.id,
                    "name": entity_attr.name,
                    "type": str(AttrTypeValue["string"]),
                    "is_mandatory": entity_attr.is_mandatory,
                    "is_delete_in_chain": False,
                    "row_index": "1",
                }
            ],  # delete EntityAttr 'ref'
        }
        resp = self.client.post(
            reverse("entity:do_edit", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        # These check that request was succeeded, but attr type and values
        # which are registered at that Attribute  would not be changed.
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(ref_entry.get_referred_objects()), [entry])
