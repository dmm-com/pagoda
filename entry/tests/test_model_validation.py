import math
from datetime import date, datetime, timezone

from django.conf import settings

from acl.models import ACLBase
from airone.lib.acl import ACLType
from airone.lib.drf import ExceedLimitError
from airone.lib.elasticsearch import AttrHint
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr, ItemNameType
from entry.models import Attribute, AttributeValue, Entry, ItemWalker
from entry.services import AdvancedSearchService
from entry.tests.test_model import BaseModelTest
from group.models import Group
from role.models import Role
from user.models import User


class ModelValidationTest(BaseModelTest):
    def test_get_attrv_method_of_entry(self):
        # prepare Entry and Attribute for testing Entry.get_attrv method
        user = User.objects.create(username="hoge")
        entity = Entity.objects.create(name="entity", created_user=user)

        for attrname in ["attr", "attr-deleted"]:
            EntityAttr.objects.create(
                name=attrname,
                type=AttrType.STRING,
                created_user=user,
                parent_entity=entity,
            )

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        for attr in entry.attrs.all():
            # set value to testing attribute
            attr.add_value(user, "hoge")

        # remove EntityAttr attr-deleted
        entity.attrs.get(name="attr-deleted").delete()

        # tests of get_attrv method
        self.assertEqual(entry.get_attrv("attr").value, "hoge")
        self.assertIsNone(entry.get_attrv("attr-deleted"))
        self.assertIsNone(entry.get_attrv("invalid-attribute-name"))

        # update AttributeValue
        entry.attrs.get(schema__name="attr").add_value(user, "fuga")
        self.assertEqual(entry.get_attrv("attr").value, "fuga")

        # AttributeValue with is_latest set to True is duplicated(rare case)
        entry.attrs.get(schema__name="attr").values.all().update(is_latest=True)
        self.assertEqual(entry.get_attrv("attr").value, "fuga")

    def test_get_attrv_after_changing_attrname(self):
        # prepare Entry and Attribute for testing Entry.get_attrv method
        entity = self.create_entity(
            self._user,
            "Test Entity",
            attrs=[{"name": "attr", "type": AttrType.STRING}],
        )
        entry = self.add_entry(
            self._user, "Test Entry", entity, is_public=False, values={"attr": "value"}
        )

        # change EntityAttr name after creating Entry
        entity_attr = entity.attrs.last()
        entity_attr.name = "attr-changed"
        entity_attr.save()

        self.assertEqual(entry.get_attrv("attr-changed").value, "value")

    def test_get_attrv_item(self):
        model_ref = self.create_entity(self._user, "Ref")
        model_test = self.create_entity(
            self._user,
            "Test Entity",
            attrs=[
                {"name": "str", "type": AttrType.STRING},
                {"name": "obj", "type": AttrType.OBJECT},
                {"name": "name", "type": AttrType.NAMED_OBJECT},
                {"name": "arr_str", "type": AttrType.ARRAY_STRING},
                {"name": "arr_obj", "type": AttrType.ARRAY_OBJECT},
                {"name": "arr_name", "type": AttrType.ARRAY_NAMED_OBJECT},
            ],
        )

        item_refs = [self.add_entry(self._user, "ref%d" % x, model_ref) for x in range(2)]
        item_test = self.add_entry(
            self._user,
            "test",
            model_test,
            values={
                "str": "foo",
                "obj": item_refs[0],
                "name": {"name": "hoge", "id": item_refs[1].id},
                "arr_obj": item_refs,
                "arr_name": [{"name": "hoge", "id": x.id} for x in item_refs],
            },
        )

        # check AttributeValue.get_attrv_item() returns expected results
        self.assertEqual(item_test.get_attrv_item("str"), None)
        self.assertEqual(item_test.get_attrv_item("obj"), item_refs[0])
        self.assertIsInstance(item_test.get_attrv_item("obj"), Entry)
        self.assertEqual(item_test.get_attrv_item("name"), item_refs[1])
        self.assertEqual(item_test.get_attrv_item("arr_obj"), item_refs)
        self.assertEqual(item_test.get_attrv_item("arr_name"), item_refs)

    def test_inherit_individual_attribute_permissions_when_it_is_complemented(self):
        [user1, user2] = [User.objects.create(username=x) for x in ["u1", "u2"]]
        groups = [Group.objects.create(name=x) for x in ["g1", "g2"]]
        [user1.groups.add(g) for g in groups]

        # initialize Role instance
        role = Role.objects.create(name="Role")
        [role.users.add(x) for x in [user1, user2]]
        [role.groups.add(x) for x in groups]

        entity = Entity.objects.create(name="entity", created_user=user1)
        entity_attr = EntityAttr.objects.create(
            name="attr",
            type=AttrType.STRING,
            created_user=user1,
            parent_entity=entity,
            is_public=False,
        )

        # set permission for test Role instance
        entity_attr.full.roles.add(role)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user1)
        entry.complement_attrs(user1)

        # This checks both users have permissions for Attribute 'attr'
        attr = entry.attrs.first()
        self.assertTrue(attr.is_public)
        self.assertTrue(all([g.has_permission(attr, ACLType.Full) for g in groups]))
        self.assertTrue(all([u.has_permission(attr, ACLType.Full) for u in [user1, user2]]))

    def test_format_for_history(self):
        user = User.objects.create(username="hoge")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        test_ref = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)
        test_grp = Group.objects.create(name="g0")

        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        attr_info = [
            {"name": "str", "set_val": "foo", "exp_val": "foo"},
            {
                "name": "obj",
                "set_val": str(test_ref.id),
                "exp_val": ACLBase.objects.get(id=test_ref.id),
            },
            {
                "name": "obj",
                "set_val": test_ref.id,
                "exp_val": ACLBase.objects.get(id=test_ref.id),
            },
            {
                "name": "obj",
                "set_val": test_ref,
                "exp_val": ACLBase.objects.get(id=test_ref.id),
            },
            {
                "name": "name",
                "set_val": {"name": "bar", "id": str(test_ref.id)},
                "exp_val": {
                    "value": "bar",
                    "referral": ACLBase.objects.get(id=test_ref.id),
                },
            },
            {
                "name": "name",
                "set_val": {"name": "bar", "id": test_ref.id},
                "exp_val": {
                    "value": "bar",
                    "referral": ACLBase.objects.get(id=test_ref.id),
                },
            },
            {
                "name": "name",
                "set_val": {"name": "bar", "id": test_ref},
                "exp_val": {
                    "value": "bar",
                    "referral": ACLBase.objects.get(id=test_ref.id),
                },
            },
            {
                "name": "arr_str",
                "set_val": ["foo", "bar", "baz"],
                "exp_val": ["foo", "bar", "baz"],
            },
            {
                "name": "arr_obj",
                "set_val": [str(test_ref.id)],
                "exp_val": [ACLBase.objects.get(id=test_ref.id)],
            },
            {
                "name": "arr_obj",
                "set_val": [test_ref.id],
                "exp_val": [ACLBase.objects.get(id=test_ref.id)],
            },
            {
                "name": "arr_obj",
                "set_val": [test_ref],
                "exp_val": [ACLBase.objects.get(id=test_ref.id)],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": str(test_ref.id)}],
                "exp_val": [{"value": "hoge", "referral": ACLBase.objects.get(id=test_ref.id)}],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": test_ref.id}],
                "exp_val": [{"value": "hoge", "referral": ACLBase.objects.get(id=test_ref.id)}],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": test_ref}],
                "exp_val": [{"value": "hoge", "referral": ACLBase.objects.get(id=test_ref.id)}],
            },
            {
                "name": "date",
                "set_val": date(2018, 12, 31),
                "exp_val": date(2018, 12, 31),
            },
            {"name": "group", "set_val": str(test_grp.id), "exp_val": test_grp},
            {"name": "group", "set_val": test_grp.id, "exp_val": test_grp},
            {"name": "group", "set_val": test_grp, "exp_val": test_grp},
            {"name": "group", "set_val": "abcd", "exp_val": ""},
            {"name": "arr_group", "set_val": [str(test_grp.id)], "exp_val": [test_grp]},
            {"name": "arr_group", "set_val": [test_grp.id], "exp_val": [test_grp]},
            {"name": "arr_group", "set_val": [test_grp], "exp_val": [test_grp]},
            {"name": "arr_group", "set_val": ["abcd"], "exp_val": []},
            {
                "name": "datetime",
                "set_val": datetime(2018, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
                "exp_val": datetime(2018, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
            },
        ]
        for info in attr_info:
            attr = entry.attrs.get(name=info["name"])
            attr.add_value(user, info["set_val"])

            self.assertEqual(attr.get_latest_value().format_for_history(), info["exp_val"])

    def test_get_default_value(self):
        user = User.objects.create(username="hoge")
        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        default_values = {
            "str": "",
            "text": "",
            "obj": None,
            "name": {"name": "", "id": None},
            "bool": False,
            "group": None,
            "date": None,
            "arr_str": [],
            "arr_obj": [],
            "arr_name": dict().values(),
            "arr_group": [],
            "arr_num": [],
            "role": None,
            "arr_role": [],
            "num": None,
            "datetime": None,
        }
        for attr in entry.attrs.all():
            if attr.name == "arr_name":
                self.assertEqual(
                    list(default_values[attr.name]),
                    list(AttributeValue.get_default_value(attr)),
                )
            else:
                self.assertEqual(default_values[attr.name], AttributeValue.get_default_value(attr))

    def test_validate_attr_value(self):
        for type in [AttrType.STRING, AttrType.TEXT]:
            self.assertEqual(AttributeValue.validate_attr_value(type, "hoge", False), (True, None))
            self.assertEqual(AttributeValue.validate_attr_value(type, "", False), (True, None))
            self.assertEqual(
                AttributeValue.validate_attr_value(type, ["hoge"], False),
                (False, "value(['hoge']) is not str"),
            )
            self.assertEqual(
                AttributeValue.validate_attr_value(
                    type, "a" * AttributeValue.MAXIMUM_VALUE_SIZE, False
                ),
                (True, None),
            )
            with self.assertRaises(ExceedLimitError):
                AttributeValue.validate_attr_value(
                    type, "a" * (AttributeValue.MAXIMUM_VALUE_SIZE + 1), False
                )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.OBJECT, self._entry.id, False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.OBJECT, None, False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.OBJECT, "", False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.OBJECT, "hoge", False),
            (False, "value(hoge) is not int"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.OBJECT, 9999, False),
            (False, "value(9999) is not entry id"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": "hoge", "id": self._entry.id}, False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": "", "id": self._entry.id}, False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": "hoge", "id": ""}, False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": "hoge", "id": None}, False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": "", "id": ""}, False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": "", "id": None}, False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": ["hoge"], "id": self._entry.id}, False
            ),
            (False, "value(['hoge']) is not str"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT,
                {"name": "a" * AttributeValue.MAXIMUM_VALUE_SIZE, "id": self._entry.id},
                False,
            ),
            (True, None),
        )
        with self.assertRaises(ExceedLimitError):
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT,
                {"name": "a" * (AttributeValue.MAXIMUM_VALUE_SIZE + 1), "id": self._entry.id},
                False,
            )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": "hoge", "id": "hoge"}, False
            ),
            (False, "value(hoge) is not int"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": "hoge", "id": 9999}, False
            ),
            (False, "value(9999) is not entry id"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.NAMED_OBJECT, "hoge", False),
            (False, "value(hoge) is not dict"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.NAMED_OBJECT, {"a": 1, "b": 2}, False),
            (False, "value({'a': 1, 'b': 2}) is not key('name', 'id')"),
        )

        group: Group = Group.objects.create(name="group0")
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.GROUP, group.id, False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.GROUP, None, False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.GROUP, "", False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.GROUP, "hoge", False),
            (False, "value(hoge) is not int"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.GROUP, 9999, False),
            (False, "value(9999) is not group id"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.BOOLEAN, True, False), (True, None)
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.BOOLEAN, False, False), (True, None)
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.BOOLEAN, "hoge", False),
            (False, "value(hoge) is not bool"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.DATE, "2020-01-01", False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.DATE, "", False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.DATE, "01-01", False),
            (False, "value(01-01) is not format(YYYY-MM-DD)"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.DATE, "hoge", False),
            (False, "value(hoge) is not format(YYYY-MM-DD)"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_STRING, ["hoge", "fuga"], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_STRING, [], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_STRING, ["hoge", ""], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_STRING, "hoge", False),
            (False, "value(hoge) is not list"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_OBJECT, [self._entry.id], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_OBJECT, [], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_OBJECT, [self._entry.id, ""], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.ARRAY_OBJECT, [self._entry.id, None], False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_OBJECT, self._entry.id, False),
            (False, "value(%s) is not list" % self._entry.id),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.ARRAY_NAMED_OBJECT, [{"name": "hoge", "id": self._entry.id}], False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_NAMED_OBJECT, [], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.ARRAY_NAMED_OBJECT, [{"name": "", "id": ""}], False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.ARRAY_NAMED_OBJECT, [{"name": "", "id": None}], False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.ARRAY_NAMED_OBJECT,
                [{"name": "hoge", "id": self._entry.id}, {"name": "", "id": ""}],
                False,
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.ARRAY_NAMED_OBJECT,
                [{"name": "hoge", "id": self._entry.id}, {"name": "", "id": None}],
                False,
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.ARRAY_NAMED_OBJECT, {"name": "hoge", "id": self._entry.id}, False
            ),
            (False, "value({'name': 'hoge', 'id': %s}) is not list" % self._entry.id),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_GROUP, [group.id], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_GROUP, [], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_GROUP, [group.id, ""], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_GROUP, [group.id, None], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_GROUP, group.id, False),
            (False, "value(%s) is not list" % group.id),
        )

    def test_validate_attr_value_is_mandatory(self):
        for type in [AttrType.STRING, AttrType.TEXT]:
            self.assertEqual(
                AttributeValue.validate_attr_value(type, "", True),
                (False, "mandatory attrs value is not specified"),
            )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.OBJECT, None, True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.OBJECT, "", True),
            (False, "mandatory attrs value is not specified"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": "", "id": self._entry.id}, True
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": "hoge", "id": ""}, True
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": "hoge", "id": None}, True
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.NAMED_OBJECT, {"name": "", "id": ""}, True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.NAMED_OBJECT, {"name": "", "id": None}, True
            ),
            (False, "mandatory attrs value is not specified"),
        )

        group: Group = Group.objects.create(name="group0")
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.GROUP, None, True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.GROUP, "", True),
            (False, "mandatory attrs value is not specified"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.BOOLEAN, True, True), (True, None)
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.BOOLEAN, False, True), (True, None)
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.DATE, "", True),
            (False, "mandatory attrs value is not specified"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_STRING, [], True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_STRING, ["hoge", ""], True),
            (True, None),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_OBJECT, [], True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_OBJECT, [self._entry.id, ""], True),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_OBJECT, [self._entry.id, None], True),
            (True, None),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_NAMED_OBJECT, [], True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.ARRAY_NAMED_OBJECT, [{"name": "", "id": ""}], True
            ),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.ARRAY_NAMED_OBJECT, [{"name": "", "id": None}], True
            ),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.ARRAY_NAMED_OBJECT,
                [{"name": "hoge", "id": self._entry.id}, {"name": "", "id": ""}],
                True,
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrType.ARRAY_NAMED_OBJECT,
                [{"name": "hoge", "id": self._entry.id}, {"name": "", "id": None}],
                True,
            ),
            (True, None),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_GROUP, [], True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_GROUP, [group.id, ""], True),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrType.ARRAY_GROUP, [group.id, None], True),
            (True, None),
        )

    def test_check_duplication_entry_at_restoring_one_chain(self):
        """
        Test case confirms to fail to restore EntryA at following case
        * EntryA -> EntryB (there is another active Entry which is same name)
        """
        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=self._user)
        ref_entries = [
            Entry.objects.create(name="ref-%d" % i, created_user=self._user, schema=ref_entity)
            for i in range(3)
        ]

        # initialize EntityAttrs
        attr_info = {
            "obj": {"type": AttrType.OBJECT, "value": ref_entries[0]},
            "arr_obj": {
                "type": AttrType.ARRAY_OBJECT,
                "value": ref_entries[1:],
            },
        }
        for attr_name, info in attr_info.items():
            # create EntityAttr object with is_delete_in_chain object
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                is_delete_in_chain=True,
                created_user=self._user,
                parent_entity=self._entity,
            )

            if info["type"] & AttrType.OBJECT:
                attr.referral.add(ref_entity)

        # initialize target entry
        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=self._user)
        entry.complement_attrs(self._user)

        for attr_name, info in attr_info.items():
            attr = entry.attrs.get(schema__name=attr_name)
            attr.add_value(self._user, info["value"])

        # delete target entry at first
        entry.delete()

        # create same name entry
        Entry.objects.create(name="ref-1", created_user=self._user, schema=ref_entity)

        # check duplicate entry
        ret = entry.check_duplication_entry_at_restoring(entry_chain=[])
        self.assertTrue(ret)

    def test_check_duplication_entry_at_restoring_two_chain(self):
        """
        Test case confirms to fail to restore EntryA at following case
        * EntryA -> EntryB -> EntryC(there is another active Entry which is same name)
        """
        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=self._user)
        ref_entries = [
            Entry.objects.create(name="ref-%d" % i, created_user=self._user, schema=ref_entity)
            for i in range(3)
        ]
        ref_entity_2 = Entity.objects.create(name="ReferredEntity2", created_user=self._user)
        ref_entries_2 = [
            Entry.objects.create(name="ref2-%d" % i, created_user=self._user, schema=ref_entity_2)
            for i in range(3)
        ]

        # initialize EntityAttrs
        attr_info = {
            "obj": {"type": AttrType.OBJECT, "value": ref_entries[0]},
            "arr_obj": {
                "type": AttrType.ARRAY_OBJECT,
                "value": ref_entries[1:],
            },
        }
        attr_info_2 = {
            "obj": {"type": AttrType.OBJECT, "value": ref_entries_2[0]},
            "arr_obj": {
                "type": AttrType.ARRAY_OBJECT,
                "value": ref_entries_2[1:],
            },
        }
        for attr_name, info in attr_info.items():
            # create EntityAttr object with is_delete_in_chain object
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                is_delete_in_chain=True,
                created_user=self._user,
                parent_entity=self._entity,
            )

            if info["type"] & AttrType.OBJECT:
                attr.referral.add(ref_entity)

        for attr_name, info in attr_info_2.items():
            # create EntityAttr object with is_delete_in_chain object
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                is_delete_in_chain=True,
                created_user=self._user,
                parent_entity=ref_entity,
            )

            if info["type"] & AttrType.OBJECT:
                attr.referral.add(ref_entity_2)

        # initialize target entry
        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=self._user)
        entry.complement_attrs(self._user)

        for attr_name, info in attr_info.items():
            attr = entry.attrs.get(schema__name=attr_name)
            attr.add_value(self._user, info["value"])

        ref_entries[0].complement_attrs(self._user)
        for attr_name, info in attr_info_2.items():
            attr = ref_entries[0].attrs.get(schema__name=attr_name)
            attr.add_value(self._user, info["value"])

        # delete target entry at first
        entry.delete()
        # sync referral entries from database
        [x.refresh_from_db() for x in ref_entries]
        [x.refresh_from_db() for x in ref_entries_2]

        self.assertFalse(ref_entries_2[1].is_active)

        # create same name entry
        Entry.objects.create(name="ref2-1", created_user=self._user, schema=ref_entity_2)

        # check duplicate entry
        ret = entry.check_duplication_entry_at_restoring(entry_chain=[])
        self.assertTrue(ret)

    def test_check_duplication_entry_at_restoring_loop(self):
        """
        Test case confirm to pass the duplicate check to restore EntryA in the following cases
        * EntryA -> EntryB -> EntryA
        """
        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=self._user)
        ref_entry = Entry.objects.create(name="ref", created_user=self._user, schema=ref_entity)
        # initialize target entry
        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=self._user)

        # initialize EntityAttrs
        attr_info = {
            "obj": {"type": AttrType.OBJECT, "value": ref_entry},
        }
        for attr_name, info in attr_info.items():
            # create EntityAttr object with is_delete_in_chain object
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                is_delete_in_chain=True,
                created_user=self._user,
                parent_entity=self._entity,
            )

            if info["type"] & AttrType.OBJECT:
                attr.referral.add(ref_entity)

        entry.complement_attrs(self._user)
        for attr_name, info in attr_info.items():
            attr = entry.attrs.get(schema__name=attr_name)
            attr.add_value(self._user, info["value"])

        # delete target entry at first
        entry.delete()
        # sync referral entry from database
        ref_entry.refresh_from_db()
        self.assertFalse(ref_entry.is_active)

        # check duplicate entry
        ret = entry.check_duplication_entry_at_restoring(entry_chain=[])
        self.assertFalse(ret)

    def test_get_prev_refers_objects_for_array_object_attr(self):
        user = User.objects.create(username="test-user")

        # Initiate Entities and Entries for this test
        ref_entity = self.create_entity(user, "RefEntity")
        (e0, e1, e2) = [self.add_entry(user, "e%s" % i, ref_entity) for i in range(3)]

        entity = self.create_entity(
            user,
            "Entity",
            attrs=[{"name": "attr", "type": AttrType.ARRAY_OBJECT, "ref": ref_entity}],
        )
        entry = self.add_entry(user, "entry", entity, values={"attr": [e0, e1]})
        attr = entry.attrs.get(schema__name="attr", is_active=True)

        # check initial referring Entries and last referring ones.
        self.assertEqual(list(entry.get_refers_objects()), [e0, e1])
        self.assertEqual(list(entry.get_prev_refers_objects()), [])

        # update referring Entry and check them
        attr.add_value(user, [e1, e2])
        self.assertEqual(list(entry.get_refers_objects()), [e1, e2])
        self.assertEqual(list(entry.get_prev_refers_objects()), [e0, e1])

        # update referring Entry and check them
        attr.add_value(user, [e0])
        self.assertEqual(list(entry.get_refers_objects()), [e0])
        self.assertEqual(list(entry.get_prev_refers_objects()), [e1, e2])

    def test_search_entries_without_user(self):
        entity = self.create_entity(
            self._user,
            "Test Another Entity",
            attrs=[{"name": "attr", "type": AttrType.STRING}],
        )
        entry = self.add_entry(
            self._user, "Test Entry", entity, is_public=False, values={"attr": "value"}
        )

        # set permission for creating user to read
        role = Role.objects.create(name="role")
        entry.full.roles.add(role)
        role.users.add(self._user)

        # Check the result of AdvancedSearchService.search_entries()
        # when the 1st argument of user is None,
        # that returns all data regardless of the permission settings.
        search_params = {
            "hint_entity_ids": [entity.id],
            "hint_attrs": [AttrHint(name="attr", keyword="")],
        }
        self.assertEqual(
            AdvancedSearchService.search_entries(self._user, **search_params),
            AdvancedSearchService.search_entries(None, **search_params),
        )

    def test_get_preview_next_value(self):
        # case not array
        attr = self.make_attr("test", AttrType.STRING)
        attrv1 = attr.add_value(self._user, "hoge1")
        attrv2 = attr.add_value(self._user, "hoge2")
        attrv3 = attr.add_value(self._user, "hoge3")

        self.assertIsNone(attrv1.get_preview_value())
        self.assertEqual(attrv1.get_next_value(), attrv2)

        self.assertEqual(attrv2.get_preview_value(), attrv1)
        self.assertEqual(attrv2.get_next_value(), attrv3)

        self.assertEqual(attrv3.get_preview_value(), attrv2)
        self.assertIsNone(attrv3.get_next_value())

        # case array
        array_attr = self.make_attr("array", AttrType.ARRAY_STRING)
        array_attrv1 = array_attr.add_value(self._user, ["hoge1", "fuga1"])
        array_attrv2 = array_attr.add_value(self._user, ["hoge2", "fuga2"])
        array_attrv3 = array_attr.add_value(self._user, ["hoge3", "fuga3"])

        self.assertIsNone(array_attrv1.get_preview_value())
        self.assertEqual(array_attrv1.get_next_value(), array_attrv2)

        self.assertEqual(array_attrv2.get_preview_value(), array_attrv1)
        self.assertEqual(array_attrv2.get_next_value(), array_attrv3)

        self.assertEqual(array_attrv3.get_preview_value(), array_attrv2)
        self.assertIsNone(array_attrv3.get_next_value())

    def test_search_entries_with_limit(self):
        self._entry.register_es()
        ret = AdvancedSearchService.search_entries(self._user, [self._entity.id], [], 99999999)
        self.assertEqual(ret.ret_count, 1)

    def test_max_entries(self):
        max_entries = 10
        for i in range(max_entries):
            Entry.objects.create(name=f"entry-{i}", created_user=self._user, schema=self._entity)

        # if the limit exceeded, RuntimeError should be raised
        settings.MAX_ENTRIES = max_entries
        with self.assertRaises(RuntimeError):
            Entry.objects.create(
                name=f"entry-{max_entries}", created_user=self._user, schema=self._entity
            )

        # if the limit is not set, RuntimeError should not be raised
        settings.MAX_ENTRIES = None
        Entry.objects.create(
            name=f"entry-{max_entries}", created_user=self._user, schema=self._entity
        )

    def test_item_walker(self):
        # initialize models and items that spans each ones.
        model_vlan = self.create_entity(self._user, "VLAN")
        model_nw = self.create_entity(
            self._user,
            "Network",
            attrs=[
                {"name": "vlan", "type": AttrType.OBJECT},
                {"name": "cidr", "type": AttrType.ARRAY_OBJECT},
                {"name": "netmask", "type": AttrType.STRING},
                {"name": "label", "type": AttrType.ARRAY_STRING},
                {"name": "deleted", "type": AttrType.BOOLEAN},
                {"name": "created_at", "type": AttrType.DATE},
            ],
        )
        model_ip_type = self.create_entity(self._user, "IPType")
        model_ip = self.create_entity(
            self._user,
            "IPAddress",
            attrs=[
                {"name": "nw", "type": AttrType.OBJECT},
                {"name": "type", "type": AttrType.OBJECT},
                {"name": "created_at", "type": AttrType.DATETIME},
            ],
        )
        model_srv = self.create_entity(
            self._user,
            "Server",
            attrs=[
                {"name": "I/F", "type": AttrType.NAMED_OBJECT},
            ],
        )

        # create items that have following referral structure
        # ( item2.obj -> item1.obj -> item0 )
        # ( item2.arr -> [item0, item1] )
        item_vlan1 = self.add_entry(self._user, "vlan0001", model_vlan)
        item_nw1 = self.add_entry(
            self._user,
            "192.168.0.0/16",
            model_nw,
            values={
                "vlan": item_vlan1,
                "netmask": "16",
                "cidr": [],
                "label": [],
                "deleted": False,
                "created_at": None,
            },
        )
        item_nw2 = self.add_entry(
            self._user,
            "192.168.0.0/24",
            model_nw,
            values={
                "vlan": item_vlan1,
                "netmask": "24",
                "cidr": [item_nw1],
                "label": ["child", "24"],
                "deleted": True,
                "created_at": date(2025, 10, 28),
            },
        )
        item_ip_type = self.add_entry(self._user, "Shared", model_ip_type)
        item_ip1 = self.add_entry(
            self._user,
            "192.168.0.1",
            model_ip,
            values={
                "nw": item_nw2,
                "type": item_ip_type,
                "created_at": datetime(2025, 10, 28, 10, 0, 0, tzinfo=timezone.utc),
            },
        )
        item_srv1 = self.add_entry(
            self._user,
            "srv1000",
            model_srv,
            values={
                "I/F": {"name": "eth0", "id": item_ip1},
            },
        )

        # create ItemWalker instance to step each items along with prepared roadmap
        iw = ItemWalker(
            [item_srv1.id],
            {
                "I/F": {
                    "nw": {
                        "vlan": {},
                        "netmask": {},
                        "cidr": {
                            "vlan": {},
                            "netmask": {},
                        },
                        "label": {},
                        "deleted": {},
                        "created_at": {},
                    },
                    "type": {},
                    "created_at": {},
                },
            },
        )
        for piw in iw.list:
            # This tests basic feature of its item() method
            self.assertEqual(piw.item, item_srv1)
            self.assertEqual(piw.value, "")

            # This tests getting neighbor items
            self.assertEqual(item_srv1.get_attrv_item("I/F"), item_ip1)
            self.assertEqual(piw["I/F"].item, item_ip1)
            self.assertEqual(piw["I/F"].value, "eth0")

            # This gets neighbor item's attribute value
            self.assertEqual(piw["I/F"]["nw"].item, item_nw2)
            self.assertEqual(piw["I/F"]["nw"].value, "")
            self.assertEqual(piw["I/F"]["type"].item, item_ip_type)
            self.assertEqual(piw["I/F"]["nw"]["netmask"].item, None)
            self.assertEqual(piw["I/F"]["nw"]["netmask"].value, "24")
            self.assertEqual(piw["I/F"]["nw"]["deleted"].boolean, True)

            # check date and datetime values can be retrieved expectedly
            self.assertEqual(
                piw["I/F"]["created_at"].datetime,
                datetime(2025, 10, 28, 10, 0, 0, tzinfo=timezone.utc),
            )
            self.assertEqual(piw["I/F"]["nw"]["created_at"].date, date(2025, 10, 28))
            self.assertIsNone(piw["I/F"]["created_at"].date)
            self.assertIsNone(piw["I/F"]["nw"]["created_at"].datetime)

            # This tests stepping another next item
            self.assertEqual(piw["I/F"]["nw"]["vlan"].item, item_vlan1)

            # This tests stepping another branched next item and its attribute value
            # for ARRAY typed attribute "cidr"
            self.assertEqual([x.item for x in piw["I/F"]["nw"]["cidr"]], [item_nw1])
            self.assertEqual([x["netmask"].value for x in piw["I/F"]["nw"]["cidr"]], ["16"])

            # This tests stepping another branched next item and its attribute value
            # for ARRAY typed attribute "label"
            self.assertEqual([x.value for x in piw["I/F"]["nw"]["label"]], ["child", "24"])

    def test_item_walker_abnormal_way(self):
        model = self.create_entity(
            self._user, "Model", attrs=self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
        )
        item = self.add_entry(self._user, "item0", model)
        iw = ItemWalker(
            [item.id],
            {"ref": {}},
        )
        for piw in iw.list:
            # check to raise KeyError when unexpected key was specified
            with self.assertRaises(
                KeyError, msg="Invalid attribute name was specified (InvalidAttr)"
            ):
                piw["InvalidAttr"]
                piw["ref"]["InvalidAttr"]

            # check to raise IndexError when when it's handled as array
            with self.assertRaises(IndexError):
                piw[0]
                [x for x in piw]

    def test_item_walker_with_empty_values(self):
        model = self.create_entity(
            self._user, "Model", attrs=self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
        )
        item0 = self.add_entry(self._user, "item0", model)
        item1 = self.add_entry(self._user, "item1", model, values={"ref": item0})

        iw = ItemWalker(
            [item1.id],
            {
                "ref": {
                    "val": {},
                    "vals": {},
                    "ref": {},
                    "refs": {},
                    "name": {},
                    "names": {},
                    "bool": {},
                }
            },
        )
        # This refers each empty referral values
        for piw in iw.list:
            # check to get actual attribute values
            self.assertEqual(piw["ref"].item, item0)
            self.assertEqual(piw["ref"].value, "")
            self.assertEqual(piw["ref"]["val"].item, None)
            self.assertEqual(piw["ref"]["val"].value, "")
            self.assertEqual(piw["ref"]["ref"].item, None)
            self.assertEqual(piw["ref"]["ref"].value, "")
            self.assertEqual(piw["ref"]["name"].item, None)
            self.assertEqual(piw["ref"]["name"].value, "")
            self.assertEqual(piw["ref"]["bool"].boolean, False)
            self.assertEqual(piw["ref"]["vals"], [])
            self.assertEqual(piw["ref"]["refs"], [])
            self.assertEqual(piw["ref"]["names"], [])

    def test_array_number_attribute_value_storage_and_retrieval(self):
        """Test comprehensive array number attribute value storage and retrieval"""
        user = User.objects.create(username="test_array_number_user")
        entity_schema = Entity.objects.create(name="test_array_number_entity", created_user=user)
        array_number_attr_schema = EntityAttr.objects.create(
            name="test_array_number_attr",
            type=AttrType.ARRAY_NUMBER,
            created_user=user,
            parent_entity=entity_schema,
        )

        entry_instance = Entry.objects.create(
            name="test_array_number_entry", schema=entity_schema, created_user=user
        )
        attribute_instance = Attribute.objects.create(
            name="test_array_number_attr",
            schema=array_number_attr_schema,
            created_user=user,
            parent_entry=entry_instance,
        )

        # Test various array number scenarios
        test_cases = [
            # (input_value, expected_output)
            ([123.45, 67.89, 0.123], [123.45, 67.89, 0.123]),  # Basic numbers
            ([1, 2, 3], [1.0, 2.0, 3.0]),  # Integers converted to floats
            ([-123.45, -67.89], [-123.45, -67.89]),  # Negative numbers
            ([0, -0], [0.0, 0.0]),  # Zero values
            ([1e10, 1e-10], [1e10, 1e-10]),  # Scientific notation
            ([123.45, None, 67.89], [123.45, None, 67.89]),  # With null values
            ([], []),  # Empty array
            ([None, None], [None, None]),  # All null values
        ]

        for input_val, expected_output in test_cases:
            with self.subTest(input_value=input_val):
                # Clear any existing values
                AttributeValue.objects.filter(parent_attr=attribute_instance).delete()

                # Add the array number value
                attribute_instance.add_value(user, input_val)

                # Get the parent AttributeValue (container for array)
                parent_attr_v = AttributeValue.objects.filter(
                    parent_attr=attribute_instance, status=AttributeValue.STATUS_DATA_ARRAY_PARENT
                ).first()
                self.assertIsNotNone(
                    parent_attr_v, f"Parent AttributeValue not found for input: {input_val}"
                )

                # Retrieve the value and compare
                retrieved = parent_attr_v.get_value()
                self.assertEqual(
                    retrieved, expected_output, f"Retrieved value mismatch for input: {input_val}"
                )

                # Test individual array items
                child_values = parent_attr_v.data_array.all().order_by("id")
                if input_val:  # Non-empty array
                    self.assertEqual(
                        len(child_values),
                        len(input_val),
                        f"Child value count mismatch for input: {input_val}",
                    )

                    for i, child_value in enumerate(child_values):
                        self.assertEqual(child_value.data_type, AttrType.ARRAY_NUMBER)
                        # For array number child values, access the stored value directly
                        if input_val[i] is None:
                            # Check if the stored value is empty or None
                            self.assertTrue(
                                not child_value.value or child_value.value.strip() == "",
                                f"Child value should be None/empty at index {i}",
                            )
                        else:
                            # Convert the stored string value back to float for comparison
                            if child_value.value and child_value.value.strip():
                                child_retrieved = float(child_value.value)
                                self.assertAlmostEqual(
                                    child_retrieved,
                                    expected_output[i],
                                    places=10,
                                    msg=f"Child value mismatch at index {i} for input: {input_val}",
                                )
                            else:
                                self.fail(
                                    f"Expected value {expected_output[i]} but got empty/None "
                                    f"at index {i}"
                                )
                else:  # Empty array
                    self.assertEqual(
                        len(child_values), 0, "Empty array should have no child values"
                    )

        # Clean up
        AttributeValue.objects.filter(parent_attr=attribute_instance).delete()
        array_number_attr_schema.delete()
        entry_instance.delete()
        entity_schema.delete()
        user.delete()

    def test_array_number_edge_cases_and_validation(self):
        """Test array number edge cases and validation scenarios"""
        user = User.objects.create(username="test_array_number_edge_user")
        entity_schema = Entity.objects.create(
            name="test_array_number_edge_entity", created_user=user
        )
        array_number_attr_schema = EntityAttr.objects.create(
            name="test_array_number_edge_attr",
            type=AttrType.ARRAY_NUMBER,
            created_user=user,
            parent_entity=entity_schema,
        )

        entry_instance = Entry.objects.create(
            name="test_array_number_edge_entry", schema=entity_schema, created_user=user
        )
        attribute_instance = Attribute.objects.create(
            name="test_array_number_edge_attr",
            schema=array_number_attr_schema,
            created_user=user,
            parent_entry=entry_instance,
        )

        # Test edge case values
        edge_cases = [
            # Very large numbers
            ([1e100, -1e100], [1e100, -1e100]),
            # Very small numbers
            ([1e-100, -1e-100], [1e-100, -1e-100]),
            # Mathematical constants
            ([math.pi, math.e], [math.pi, math.e]),
            # Mixed precision
            ([1.123456789012345, 2.987654321098765], [1.123456789012345, 2.987654321098765]),
        ]

        for input_val, expected_output in edge_cases:
            with self.subTest(input_value=input_val):
                # Clear any existing values
                AttributeValue.objects.filter(parent_attr=attribute_instance).delete()

                # Add the array number value
                attribute_instance.add_value(user, input_val)

                # Get the parent AttributeValue
                parent_attr_v = AttributeValue.objects.filter(
                    parent_attr=attribute_instance, status=AttributeValue.STATUS_DATA_ARRAY_PARENT
                ).first()
                self.assertIsNotNone(parent_attr_v)

                # Retrieve and verify
                retrieved = parent_attr_v.get_value()
                self.assertEqual(len(retrieved), len(expected_output))

                for i, (actual, expected) in enumerate(zip(retrieved, expected_output)):
                    self.assertAlmostEqual(
                        actual,
                        expected,
                        places=10,
                        msg=f"Edge case value mismatch at index {i} for input: {input_val}",
                    )

        # Clean up
        AttributeValue.objects.filter(parent_attr=attribute_instance).delete()
        array_number_attr_schema.delete()
        entry_instance.delete()
        entity_schema.delete()
        user.delete()

    def test_array_number_default_values(self):
        """Test array number default value behavior"""
        user = User.objects.create(username="test_array_number_default_user")
        entity_schema = Entity.objects.create(
            name="test_array_number_default_entity", created_user=user
        )
        array_number_attr_schema = EntityAttr.objects.create(
            name="test_array_number_default_attr",
            type=AttrType.ARRAY_NUMBER,
            created_user=user,
            parent_entity=entity_schema,
        )

        entry_instance = Entry.objects.create(
            name="test_array_number_default_entry", schema=entity_schema, created_user=user
        )
        attribute_instance = Attribute.objects.create(
            name="test_array_number_default_attr",
            schema=array_number_attr_schema,
            created_user=user,
            parent_entry=entry_instance,
        )

        # Test that default value for array number is an empty list
        default_value = AttributeValue.get_default_value(attribute_instance)
        self.assertEqual(default_value, [])
        self.assertIsInstance(default_value, list)

        # Test that when no value is set, get_value returns the default
        # Since no AttributeValue exists yet, this should return the default
        attr_values = AttributeValue.objects.filter(parent_attr=attribute_instance)
        self.assertEqual(attr_values.count(), 0, "No AttributeValue should exist initially")

        # Clean up
        array_number_attr_schema.delete()
        entry_instance.delete()
        entity_schema.delete()
        user.delete()

    def test_array_number_serialization_and_history(self):
        """Test array number serialization and history formatting"""
        user = User.objects.create(username="test_array_number_serial_user")
        entity_schema = Entity.objects.create(
            name="test_array_number_serial_entity", created_user=user
        )
        array_number_attr_schema = EntityAttr.objects.create(
            name="test_array_number_serial_attr",
            type=AttrType.ARRAY_NUMBER,
            created_user=user,
            parent_entity=entity_schema,
        )

        entry_instance = Entry.objects.create(
            name="test_array_number_serial_entry", schema=entity_schema, created_user=user
        )
        attribute_instance = Attribute.objects.create(
            name="test_array_number_serial_attr",
            schema=array_number_attr_schema,
            created_user=user,
            parent_entry=entry_instance,
        )

        test_values = [123.45, 67.89, None, -45.67]
        attribute_instance.add_value(user, test_values)

        # Get the parent AttributeValue
        parent_attr_v = AttributeValue.objects.filter(
            parent_attr=attribute_instance, status=AttributeValue.STATUS_DATA_ARRAY_PARENT
        ).first()
        self.assertIsNotNone(parent_attr_v)

        # Test serialization
        serialized_value = parent_attr_v.get_value(serialize=True)
        expected_serialized = [123.45, 67.89, None, -45.67]
        self.assertEqual(serialized_value, expected_serialized)

        # Test history formatting
        history_value = parent_attr_v.format_for_history()
        expected_history = [123.45, 67.89, None, -45.67]
        self.assertEqual(history_value, expected_history)

        # Test with metadata
        value_with_meta = parent_attr_v.get_value(with_metainfo=True)
        expected_meta = {"type": AttrType.ARRAY_NUMBER, "value": [123.45, 67.89, None, -45.67]}
        self.assertEqual(value_with_meta, expected_meta)

        # Clean up
        AttributeValue.objects.filter(parent_attr=attribute_instance).delete()
        array_number_attr_schema.delete()
        entry_instance.delete()
        entity_schema.delete()
        user.delete()

    def test_autoname_method(self):
        model_lb = self.create_entity(self._user, "LB")
        model_lb_sg = self.create_entity(
            self._user,
            "LBServiceGroup",
            attrs=[
                {
                    "name": "LB",
                    "type": AttrType.OBJECT,
                    "ref": model_lb,
                    "name_order": 1,
                    "name_prefix": "[",
                    "name_postfix": "]",
                },
                {"name": "label", "type": AttrType.STRING},
                {"name": "domain", "type": AttrType.STRING, "name_order": 2, "name_prefix": " "},
                {"name": "port", "type": AttrType.STRING, "name_order": 3, "name_prefix": ":"},
                {
                    "name": "number",
                    "type": AttrType.NUMBER,
                    "name_order": 4,
                },  # This should be ignored
                {
                    "name": "dict",
                    "type": AttrType.NAMED_OBJECT,
                    "name_order": 5,
                },  # This should be ignored
            ],
            item_name_type=ItemNameType.ATTR,
        )

        lb1 = self.add_entry(self._user, "LB0001", model_lb)
        lb_sg1 = self.add_entry(
            self._user,
            "TestLB but this is not set, actually :)",
            model_lb_sg,
            values={
                "LB": lb1,
                "label": "This is a test LB ServiceGroup",
                "domain": "pagoda-test.example.com",
                "port": 80,
                "number": 100,
                "dict": {"name": "TestDict", "id": lb1},
            },
        )
        self.assertEqual(lb_sg1.autoname, "[LB0001] pagoda-test.example.com:80")

    def test_save_autoname_with_duplicated_values(self):
        model = self.create_entity(
            self._user,
            "Auto Save",
            attrs=[
                {"name": "a1", "type": AttrType.STRING, "name_order": 1},
                {"name": "a2", "type": AttrType.STRING, "name_order": 2, "name_prefix": "-"},
            ],
            item_name_type=ItemNameType.ATTR,
        )

        items = [
            self.add_entry(self._user, x, model, values={"a1": "foo", "a2": "bar"})
            for x in range(3)
        ]
        [x.save_autoname() for x in items]

        self.assertEqual(items[0].name, "foo-bar")
        self.assertRegex(items[1].name, r"^foo-bar -- duplicate of ID:%s -- " % str(items[0].id))
        self.assertRegex(items[2].name, r"^foo-bar -- duplicate of ID:%s -- " % str(items[0].id))

    def test_may_change_referred_item_names(self):
        """
        This tests Entry.may_change_referred_item_names() method works propery
        when circular reference structure is present.
        """
        model0 = self.create_entity(
            self._user,
            "Model0",
            attrs=[
                {"name": "val", "type": AttrType.STRING, "name_order": 1},
            ],
            item_name_type=ItemNameType.ATTR,
        )
        model1 = self.create_entity(
            self._user,
            "Model1",
            attrs=[
                {"name": "ref", "type": AttrType.OBJECT, "name_order": 1, "ref": model0},
                {"name": "val", "type": AttrType.STRING, "name_order": 2, "name_prefix": "-"},
            ],
            item_name_type=ItemNameType.ATTR,
        )
        model2 = self.create_entity(
            self._user,
            "Model2",
            attrs=[
                {"name": "ref", "type": AttrType.OBJECT, "name_order": 1, "ref": model1},
                {"name": "val", "type": AttrType.STRING, "name_order": 2, "name_prefix": "-"},
            ],
            item_name_type=ItemNameType.ATTR,
        )
        self.update_entity(
            self._user, model0, attrs=[{"name": "ref", "type": AttrType.OBJECT, "ref": model2}]
        )

        # create items that have circular reference structure
        # (item0 -> item1 -> item2 -> item0 ...)
        item0 = self.add_entry(self._user, "tmp00", model0, values={"val": "BEFORE"})
        item0.save_autoname()
        item1 = self.add_entry(self._user, "tmp01", model1, values={"val": "hoge", "ref": item0})
        item1.save_autoname()
        item2 = self.add_entry(self._user, "tmp02", model2, values={"val": "fuga", "ref": item1})
        item2.save_autoname()
        item0.attrs.get(schema__name="ref").add_value(self._user, item2)

        self.assertEqual(item1.autoname, "BEFORE-hoge")
        self.assertEqual(item2.autoname, "BEFORE-hoge-fuga")

        # change referred item's name
        item0.attrs.get(schema__name="val").add_value(self._user, "AFTER")
        item0.save_autoname()

        # check all referred items are updated
        item1.refresh_from_db()
        self.assertEqual(item1.name, "AFTER-hoge")
        item2.refresh_from_db()
        self.assertEqual(item2.name, "AFTER-hoge-fuga")
