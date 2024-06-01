from copy import copy

from django.conf import settings
from django.test import TestCase

from airone.lib.types import AttrType
from entity.admin import EntityAttrResource, EntityResource
from entity.models import Entity, EntityAttr
from user.models import User


class ModelTest(TestCase):
    def setUp(self):
        self._test_user = User(username="test")
        self._test_user.save()

    def test_make_attrbase(self):
        entity = Entity(name="test01", created_user=self._test_user)
        entity.save()

        attr_base = EntityAttr(
            name="hoge",
            type=AttrType.OBJECT,
            created_user=self._test_user,
            parent_entity=entity,
        )
        attr_base.save()

        self.assertEqual(attr_base.name, "hoge")
        self.assertTrue(isinstance(attr_base.type, int))
        self.assertEqual(attr_base.referral.count(), 0)

    def test_make_entity(self):
        entity = Entity(name="test01", created_user=self._test_user)
        entity.save()

        self.assertEqual(entity.name, "test01")
        self.assertEqual(list(entity.attrs.all()), [])
        self.assertTrue(entity.is_active)

    def test_set_parent(self):
        entity = Entity(name="test01", created_user=self._test_user)
        entity.save()

        attr_base = EntityAttr(
            name="hoge",
            type=AttrType.OBJECT,
            created_user=self._test_user,
            parent_entity=entity,
        )
        attr_base.save()

        self.assertEqual(attr_base.parent_entity, entity)

    def test_import_with_existed_object(self):
        entity = Entity(name="test01", note="note1", created_user=self._test_user)
        entity.save()

        EntityResource.import_data_from_request(
            {
                "id": entity.id,
                "name": entity.name,
                "note": entity.note,
                "created_user": entity.created_user.username,
            },
            self._test_user,
        )

        self.assertEqual(Entity.objects.count(), 1)
        self.assertEqual(Entity.objects.last().name, entity.name)
        self.assertEqual(Entity.objects.last().note, entity.note)
        self.assertEqual(Entity.objects.last().created_user, self._test_user)

    def test_import_with_new_object(self):
        EntityResource.import_data_from_request(
            {
                "name": "foo",
                "note": "bar",
                "created_user": self._test_user,
            },
            self._test_user,
        )
        self.assertEqual(Entity.objects.count(), 1)
        self.assertEqual(Entity.objects.last().name, "foo")
        self.assertEqual(Entity.objects.last().note, "bar")
        self.assertEqual(Entity.objects.last().created_user, self._test_user)

    def test_import_with_updating_object(self):
        entity = Entity(name="test01", note="note1", created_user=self._test_user)
        entity.save()

        EntityResource.import_data_from_request(
            {
                "id": entity.id,
                "name": "changed_name",
                "note": "changed_note",
                "created_user": entity.created_user.username,
            },
            self._test_user,
        )

        self.assertEqual(Entity.objects.count(), 1)
        self.assertEqual(Entity.objects.last().name, "changed_name")
        self.assertEqual(Entity.objects.last().note, "changed_note")
        self.assertEqual(Entity.objects.last().created_user, self._test_user)

    def test_import_with_invalid_parameter(self):
        with self.assertRaises(RuntimeError):
            EntityResource.import_data_from_request(
                {
                    "name": "hoge",
                    "note": "fuga",
                    "invalid_key": "invalid_value",
                    "created_user": self._test_user.username,
                },
                self._test_user,
            )

        self.assertEqual(Entity.objects.count(), 0)

    def test_import_without_mandatory_parameter(self):
        with self.assertRaises(RuntimeError):
            EntityResource.import_data_from_request(
                {
                    "note": "fuga",
                    "created_user": self._test_user.username,
                },
                self._test_user,
            )

        self.assertEqual(Entity.objects.count(), 0)

    def test_import_with_spoofing_parameter(self):
        user = User.objects.create(username="another_user")

        EntityResource.import_data_from_request(
            {"name": "entity", "note": "note", "created_user": user}, self._test_user
        )

        self.assertEqual(Entity.objects.count(), 0)

    def test_import_without_permission_parameter(self):
        user = User.objects.create(username="another_user")
        entity = Entity.objects.create(name="origin_name", created_user=user, is_public=False)
        entity.save()

        EntityResource.import_data_from_request(
            {
                "id": entity.id,
                "name": "changed_name",
                "note": "changed_note",
                "created_user": entity.created_user.username,
            },
            self._test_user,
        )

        self.assertEqual(Entity.objects.count(), 1)
        self.assertEqual(Entity.objects.last().name, "origin_name")

    def test_import_entity_attr_with_changing_type(self):
        """
        This checks the attribute type wouldn't be changed by specifying type.
        """
        user = self._test_user
        entity = Entity.objects.create(name="Entity", created_user=user)
        entity_attr = EntityAttr.objects.create(
            **{
                "name": "attr",
                "type": AttrType.STRING,
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity.attrs.add(entity_attr)

        EntityAttrResource.import_data_from_request(
            {
                "id": entity_attr.id,
                "name": "changed-attr",
                "type": AttrType.ARRAY_STRING,
                "entity": entity.name,
                "created_user": user.username,
            },
            user,
        )

        entity_attr.refresh_from_db()
        self.assertEqual(entity_attr.name, "changed-attr")
        self.assertEqual(entity_attr.type, AttrType.STRING)

    def test_import_entity_attr_without_specifying_type(self):
        """
        This import EntityAttr without specifying type parameter.
        """
        user = self._test_user
        entity = Entity.objects.create(name="Entity", created_user=user)
        entity_attr = EntityAttr.objects.create(
            **{
                "name": "attr",
                "type": AttrType.STRING,
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity.attrs.add(entity_attr)

        EntityAttrResource.import_data_from_request(
            {
                "id": entity_attr.id,
                "name": "changed-attr",
                "entity": entity.name,
                "created_user": user.username,
            },
            user,
        )

        entity_attr.refresh_from_db()
        self.assertEqual(entity_attr.name, "changed-attr")
        self.assertEqual(entity_attr.type, AttrType.STRING)

    def test_import_entity_attr_without_specifying_id(self):
        """
        This checks an attribute would be created by importing.
        """
        user = self._test_user
        entity = Entity.objects.create(name="Entity", created_user=user)

        EntityAttrResource.import_data_from_request(
            {
                "name": "attr",
                "type": AttrType.ARRAY_STRING,
                "entity": entity.name,
                "created_user": user.username,
            },
            user,
        )

        entity.refresh_from_db()
        self.assertEqual(
            [(x.name, x.type) for x in entity.attrs.all()],
            [("attr", AttrType.ARRAY_STRING)],
        )

    def test_import_entity_attr_without_specifying_id_and_type(self):
        """
        This checks an attribute wouldn't be created by importing because of luck of parameters
        """
        user = self._test_user
        entity = Entity.objects.create(name="Entity", created_user=user)

        # This processing would be failed because 'type' parameter is necessary for creating
        # a new EntityAttr instance by importing processing.
        with self.assertRaises(RuntimeError) as cm:
            EntityAttrResource.import_data_from_request(
                {"name": "attr", "entity": entity.name, "created_user": user.username},
                user,
            )

        # Check assert exception message
        self.assertEqual(
            cm.exception.args[0],
            "The parameter 'type' is mandatory when a new EntityAtter create",
        )

        # This checks EntityAttr would not be created
        self.assertFalse(EntityAttr.objects.filter(parent_entity=entity, is_active=True).exists())

    def test_is_update_method(self):
        user = User.objects.create(username="another_user")

        entity_ref = Entity.objects.create(name="entity_ref", created_user=user)
        entity = Entity.objects.create(name="entity", created_user=user)
        attr = EntityAttr.objects.create(
            name="attr",
            type=AttrType.OBJECT,
            created_user=user,
            parent_entity=entity,
        )
        attr.add_referral(entity)

        # initialize params which is same with the EntityAttr `attr`
        params = {
            "name": attr.name,
            "index": attr.index,
            "is_mandatory": attr.is_mandatory,
            "is_delete_in_chain": attr.is_delete_in_chain,
        }

        # check not to change any parameter
        self.assertFalse(attr.is_updated(**params))
        self.assertFalse(attr.is_referral_updated([entity.id]))

        # check to change name parameter
        changed_params = copy(params)
        changed_params["name"] = "name (changed)"
        self.assertTrue(attr.is_updated(**changed_params))

        # check to change referrals parameter
        self.assertTrue(attr.is_referral_updated([entity_ref]))

        # check to change index parameter
        changed_params = copy(params)
        changed_params["index"] = attr.index + 1
        self.assertTrue(attr.is_updated(**changed_params))

        # check to change is_mandatory parameter
        changed_params = copy(params)
        changed_params["is_mandatory"] = not params["is_mandatory"]
        self.assertTrue(attr.is_updated(**changed_params))

        # check to change is_delete_in_chain parameter
        changed_params = copy(params)
        changed_params["is_delete_in_chain"] = not params["is_delete_in_chain"]
        self.assertTrue(attr.is_updated(**changed_params))

    def test_add_referral(self):
        # create Entities to be referred by test EntityAttr
        ref_entities = [
            Entity.objects.create(name="r-%d" % i, created_user=self._test_user) for i in range(3)
        ]

        # create EntityAttr for test
        entity = Entity.objects.create(name="entity", created_user=self._test_user)
        attr = EntityAttr.objects.create(
            name="attr",
            type=AttrType.OBJECT,
            created_user=self._test_user,
            parent_entity=entity,
        )

        # set referrals with invalid patterns and confirms it works safely and
        # confirms that no referral will be set
        attr.add_referral("invalid referral Entity")
        attr.add_referral(9999999)
        attr.add_referral(True)
        attr.add_referral(None)
        attr.add_referral(("foo", "bar", "baz"))
        attr.add_referral(["foo", "bar", "baz"])
        attr.add_referral({"hoge": "fuga"})
        self.assertEqual([x.name for x in attr.referral.all()], [])

        # set referrals with valid immediate values and confirms expected referrals are set
        attr.add_referral(ref_entities[0].name)
        attr.add_referral(ref_entities[1].id)
        attr.add_referral(ref_entities[2])
        self.assertEqual([x.name for x in attr.referral.all()], [x.name for x in ref_entities])

        # set referrals with valid list value and confirms expected referrals are set
        attr.referral_clear()
        attr.add_referral(
            [
                ref_entities[0].name,
                ref_entities[1].id,
                ref_entities[2],
            ]
        )
        self.assertEqual([x.name for x in attr.referral.all()], [x.name for x in ref_entities])

    def test_max_entities(self):
        max_entities = 10
        for i in range(max_entities):
            Entity.objects.create(name=f"entity-{i}", created_user=self._test_user)

        # if the limit exceeded, RuntimeError should be raised
        settings.MAX_ENTITIES = max_entities
        with self.assertRaises(RuntimeError):
            Entity.objects.create(name=f"entity-{max_entities}", created_user=self._test_user)

        # if the limit is not set, RuntimeError should not be raised
        settings.MAX_ENTITIES = None
        Entity.objects.create(name=f"entity-{max_entities}", created_user=self._test_user)

    def test_max_attributes_per_entity(self):
        max_attributes_per_entity = 10

        entity = Entity.objects.create(
            name="test_max_attributes_per_entity", created_user=self._test_user
        )

        for i in range(max_attributes_per_entity):
            EntityAttr.objects.create(
                name="entity_attr-%d" % i,
                type=AttrType.STRING,
                created_user=self._test_user,
                parent_entity=entity,
            )

        # if the limit exceeded, RuntimeError should be raised
        settings.MAX_ATTRIBUTES_PER_ENTITY = max_attributes_per_entity
        with self.assertRaises(RuntimeError):
            EntityAttr.objects.create(
                name="entity_attr-%d" % max_attributes_per_entity,
                type=AttrType.STRING,
                created_user=self._test_user,
                parent_entity=entity,
            )

        # if the limit is not set, RuntimeError should not be raised
        settings.MAX_ATTRIBUTES_PER_ENTITY = None
        EntityAttr.objects.create(
            name="entity_attr-%d" % max_attributes_per_entity,
            type=AttrType.STRING,
            created_user=self._test_user,
            parent_entity=entity,
        )
