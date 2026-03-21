from datetime import date, datetime, timezone

from django.conf import settings

from airone.lib.acl import ACLObjType, ACLType
from airone.lib.test import AironeTestCase
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.models import Attribute, AttributeValue, Entry
from group.models import Group
from user.models import User


class BaseModelTest(AironeTestCase):
    def setUp(self):
        super(BaseModelTest, self).setUp()

        self._user: User = User(username="test")
        self._user.save()

        self._entity: Entity = Entity(name="entity", created_user=self._user)
        self._entity.save()

        self._entry: Entry = Entry(name="entry", created_user=self._user, schema=self._entity)
        self._entry.save()

        self._attr: Attribute = self.make_attr("attr")
        self._attr.save()

        # make auto complement user
        self._complement_user: User = User(
            username=settings.AIRONE["AUTO_COMPLEMENT_USER"],
            email="hoge@example.com",
            is_superuser=True,
        )
        self._complement_user.set_password(settings.AIRONE["AUTO_COMPLEMENT_USER"])
        self._complement_user.save()

    def _get_attrinfo_template(self, ref=None, group=None, role=None):
        attrinfo = [
            {"name": "str", "set_val": "foo", "exp_val": "foo"},
            {"name": "text", "set_val": "bar", "exp_val": "bar"},
            {"name": "bool", "set_val": False, "exp_val": False},
            {
                "name": "arr_str",
                "set_val": ["foo", "bar", "baz"],
                "exp_val": ["foo", "bar", "baz"],
            },
            {
                "name": "arr_num",
                "set_val": [123.45, 67.89, 0.123, -45.67],
                "exp_val": [123.45, 67.89, 0.123, -45.67],
            },
            {
                "name": "date",
                "set_val": date(2018, 12, 31),
                "exp_val": date(2018, 12, 31),
            },
            {
                "name": "datetime",
                "set_val": datetime(2018, 12, 31, 12, 34, 56, tzinfo=timezone.utc),
                "exp_val": datetime(2018, 12, 31, 12, 34, 56, tzinfo=timezone.utc),
            },
            {"name": "num", "set_val": 123.45, "exp_val": 123.45},
        ]
        if ref:
            attrinfo.append({"name": "obj", "set_val": ref, "exp_val": ref.name})
            attrinfo.append(
                {
                    "name": "name",
                    "set_val": {"name": "bar", "id": ref},
                    "exp_val": {"bar": ref.name},
                }
            )
            attrinfo.append({"name": "arr_obj", "set_val": [ref], "exp_val": [ref.name]})
            attrinfo.append(
                {
                    "name": "arr_name",
                    "set_val": [{"name": "hoge", "id": ref}],
                    "exp_val": [{"hoge": ref.name}],
                }
            )
        if group:
            attrinfo.append({"name": "group", "set_val": group, "exp_val": group.name})
            attrinfo.append({"name": "arr_group", "set_val": [group], "exp_val": [group.name]})
        if role:
            attrinfo.append({"name": "role", "set_val": role, "exp_val": role})
            attrinfo.append({"name": "arr_role", "set_val": [role], "exp_val": [role]})

        return attrinfo


class ModelTest(BaseModelTest):
    def test_make_attribute_value(self):
        AttributeValue(value="hoge", created_user=self._user, parent_attr=self._attr).save()

        self.assertEqual(AttributeValue.objects.count(), 1)
        self.assertEqual(AttributeValue.objects.last().value, "hoge")
        self.assertEqual(AttributeValue.objects.last().created_user, self._user)
        self.assertIsNotNone(AttributeValue.objects.last().created_time)

    def test_make_attribute(self):
        value = AttributeValue(value="hoge", created_user=self._user, parent_attr=self._attr)
        value.save()

        self._attr.values.add(value)

        self.assertEqual(Attribute.objects.count(), 1)
        self.assertEqual(Attribute.objects.last().objtype, ACLObjType.EntryAttr)
        self.assertEqual(Attribute.objects.last().values.count(), 1)
        self.assertEqual(Attribute.objects.last().values.last(), value)

    def test_make_entry(self):
        entry = Entry(name="test", schema=self._entity, created_user=self._user)
        entry.save()

        attr = self.make_attr("attr", entry=entry)

        self.assertEqual(Entry.objects.count(), 2)
        self.assertEqual(Entry.objects.last().created_user, self._user)
        self.assertEqual(Entry.objects.last().attrs.count(), 1)
        self.assertEqual(Entry.objects.last().attrs.last(), attr)
        self.assertEqual(Entry.objects.last().name, "test")
        self.assertEqual(
            Entry.objects.last().is_active,
            True,
            "Entry should not be deleted after created",
        )

    def test_inherite_attribute_permission_of_user(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="entity", created_user=user)
        attrbase = EntityAttr.objects.create(
            name="attr", type=AttrType.OBJECT, created_user=user, parent_entity=entity
        )

        # update acl metadata
        attrbase.is_public = False
        attrbase.default_permission = ACLType.Readable.id

        # set a permission to the user
        user.permissions.add(attrbase.writable)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        attr = entry.add_attribute_from_base(attrbase, user)

        # checks that acl metadata is not inherited
        self.assertTrue(attr.is_public)
        self.assertEqual(attr.default_permission, ACLType.Nothing.id)
        self.assertEqual(user.permissions.get(name="writable").codename, attrbase.writable.codename)

    def test_inherite_attribute_permission_of_group(self):
        user = User.objects.create(username="hoge")
        group = Group.objects.create(name="group")
        user.groups.add(group)

        entity = Entity.objects.create(name="entity", created_user=user)
        attrbase = EntityAttr.objects.create(
            name="attr", type=AttrType.OBJECT, created_user=user, parent_entity=entity
        )

        # set a permission to the user
        group.permissions.add(attrbase.writable)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.add_attribute_from_base(attrbase, user)

        self.assertEqual(
            group.permissions.get(name="writable").codename, attrbase.writable.codename
        )

    def test_update_attribute_from_base(self):
        user = User.objects.create(username="hoge")

        # test objects to be handled as referral
        entity = Entity.objects.create(name="entity", created_user=user)

        attrbase = EntityAttr.objects.create(
            name="attrbase",
            type=AttrType.STRING,
            created_user=user,
            parent_entity=entity,
        )
        entry: Entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        attr = entry.add_attribute_from_base(attrbase, user)
        self.assertTrue(entry.attrs.filter(id=attr.id).exists())
        self.assertEqual(entry.attrs.count(), 1)

        # check not to create multiple same Attribute objects by add_attribute_from_base method
        entry.add_attribute_from_base(attrbase, user)
        self.assertTrue(entry.attrs.filter(id=attr.id).exists())
        self.assertEqual(entry.attrs.count(), 1)

        # check that deleted attributes are restored
        attr.delete()
        entry.add_attribute_from_base(attrbase, user)
        self.assertTrue(entry.attrs.filter(id=attr.id, is_active=True).exists())
        self.assertEqual(entry.attrs.count(), 1)

    def test_status_update_methods_of_attribute_value(self):
        value = AttributeValue(value="hoge", created_user=self._user, parent_attr=self._attr)
        value.save()

        self.assertFalse(value.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT))

        value.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)

        self.assertTrue(value.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT))

        value.del_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)

        self.assertFalse(value.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT))

    def test_attr_helper_of_attribute_with_string_values(self):
        self.assertTrue(self._attr.is_updated("hoge"))

        self._attr.values.add(
            AttributeValue.objects.create(
                value="hoge", created_user=self._user, parent_attr=self._attr
            )
        )
        self._attr.values.add(
            AttributeValue.objects.create(
                value="fuga", created_user=self._user, parent_attr=self._attr
            )
        )

        self.assertFalse(self._attr.is_updated("fuga"))
        self.assertTrue(self._attr.is_updated("hgoe"))
        self.assertTrue(self._attr.is_updated("puyo"))

    def test_attr_helper_of_attribute_with_object_values(self):
        e1 = Entry.objects.create(name="E1", created_user=self._user, schema=self._entity)
        e2 = Entry.objects.create(name="E2", created_user=self._user, schema=self._entity)

        entity = Entity.objects.create(name="e2", created_user=self._user)
        entry = Entry.objects.create(name="_E", created_user=self._user, schema=entity)

        attr = self.make_attr("attr2", attrtype=AttrType.OBJECT, entity=entity, entry=entry)
        attr.values.add(
            AttributeValue.objects.create(referral=e1, created_user=self._user, parent_attr=attr)
        )

        self.assertFalse(attr.is_updated(e1.id))
        self.assertTrue(attr.is_updated(e2.id))

        # checks that this method accepts Entry
        self.assertFalse(attr.is_updated(e1))
        self.assertTrue(attr.is_updated(e2))

    def test_attr_helper_of_attribute_with_array_string_vlaues(self):
        entity = Entity.objects.create(name="e2", created_user=self._user)
        entry = Entry.objects.create(name="_E", created_user=self._user, schema=entity)

        attr = self.make_attr("attr2", attrtype=AttrType.ARRAY_STRING, entity=entity, entry=entry)
        attr_value = AttributeValue.objects.create(created_user=self._user, parent_attr=attr)
        attr_value.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)

        AttributeValue.objects.create(
            value="hoge", created_user=self._user, parent_attr=attr, parent_attrv=attr_value
        )
        AttributeValue.objects.create(
            value="fuga", created_user=self._user, parent_attr=attr, parent_attrv=attr_value
        )

        attr.values.add(attr_value)

        self.assertFalse(attr.is_updated(["hoge", "fuga"]))
        self.assertFalse(attr.is_updated(["fuga", "hoge"]))
        self.assertTrue(attr.is_updated(["hoge", "puyo"]))  # update
        self.assertTrue(attr.is_updated(["hoge"]))  # delete
        self.assertTrue(attr.is_updated(["puyo"]))  # delete & update
        self.assertTrue(attr.is_updated(["hoge", "fuga", "puyo"]))  # add
        self.assertTrue(attr.is_updated(["hoge", "fuga", "abcd"]))  # add & update

    def test_attr_helper_of_attribute_with_array_object_values(self):
        e1 = Entry.objects.create(name="E1", created_user=self._user, schema=self._entity)
        e2 = Entry.objects.create(name="E2", created_user=self._user, schema=self._entity)
        e3 = Entry.objects.create(name="E3", created_user=self._user, schema=self._entity)
        e4 = Entry.objects.create(name="E4", created_user=self._user, schema=self._entity)

        entity = Entity.objects.create(name="e2", created_user=self._user)
        entry = Entry.objects.create(name="_E", created_user=self._user, schema=entity)

        attr = self.make_attr("attr2", attrtype=AttrType.ARRAY_OBJECT, entity=entity, entry=entry)
        attr_value = AttributeValue.objects.create(created_user=self._user, parent_attr=attr)
        attr_value.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)

        AttributeValue.objects.create(
            referral=e1, created_user=self._user, parent_attr=attr, parent_attrv=attr_value
        )
        AttributeValue.objects.create(
            referral=e2, created_user=self._user, parent_attr=attr, parent_attrv=attr_value
        )

        attr.values.add(attr_value)

        self.assertFalse(attr.is_updated([e1.id, e2.id]))
        self.assertFalse(attr.is_updated([e2.id, e1.id]))
        self.assertTrue(attr.is_updated([e1.id, e3.id]))  # update
        self.assertTrue(attr.is_updated([e1.id]))  # delete
        self.assertTrue(attr.is_updated([e3.id]))  # delete & update
        self.assertTrue(attr.is_updated([e1.id, e2.id, e3.id]))  # create
        self.assertTrue(attr.is_updated([e1.id, e3.id, e4.id]))  # create & update
        self.assertTrue(attr.is_updated([]))
        self.assertTrue(attr.is_updated([None, e1.id]))
        self.assertTrue(attr.is_updated(["", e1.id]))
        self.assertTrue(attr.is_updated(["0", e1.id]))
        self.assertTrue(attr.is_updated(["hoge", e1.id]))

        # checks that this method also accepts Entry
        self.assertFalse(attr.is_updated([e2, e1]))
        self.assertTrue(attr.is_updated([e1, e3]))

    def test_attr_helper_of_attribute_with_array_object_values_at_empty(self):
        e1 = Entry.objects.create(name="E1", created_user=self._user, schema=self._entity)
        e2 = Entry.objects.create(name="E2", created_user=self._user, schema=self._entity)

        entity = Entity.objects.create(name="e2", created_user=self._user)
        entry = Entry.objects.create(name="_E", created_user=self._user, schema=entity)

        attr = self.make_attr("attr2", attrtype=AttrType.ARRAY_OBJECT, entity=entity, entry=entry)
        attr_value = AttributeValue.objects.create(created_user=self._user, parent_attr=attr)
        attr_value.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)

        AttributeValue.objects.create(
            referral=e1, created_user=self._user, parent_attr=attr, parent_attrv=attr_value
        )
        AttributeValue.objects.create(
            referral=e2, created_user=self._user, parent_attr=attr, parent_attrv=attr_value
        )

        attr.values.add(attr_value)

        self.assertFalse(attr.is_updated([e1.id, e2.id]))
        e2.delete()
        self.assertTrue(attr.is_updated([e1.id, ""]))  # value=""

    def test_attr_helper_of_attribute_with_named_ref(self):
        ref_entity = Entity.objects.create(name="referred_entity", created_user=self._user)
        ref_entry1 = Entry.objects.create(
            name="referred_entry1", created_user=self._user, schema=ref_entity
        )
        ref_entry2 = Entry.objects.create(
            name="referred_entry2", created_user=self._user, schema=ref_entity
        )

        entity = Entity.objects.create(name="entity", created_user=self._user)
        new_attr_params = {
            "name": "named_ref",
            "type": AttrType.NAMED_OBJECT,
            "created_user": self._user,
            "parent_entity": entity,
        }
        attr_base = EntityAttr.objects.create(**new_attr_params)
        attr_base.referral.add(ref_entity)

        entry = Entry.objects.create(name="entry", created_user=self._user, schema=entity)
        entry.complement_attrs(self._user)

        attr = entry.attrs.get(name="named_ref")
        self.assertTrue(attr.is_updated(ref_entry1.id))

        # Check user id
        self.assertEqual(attr.created_user_id, self._complement_user.id)

        attr.values.add(
            AttributeValue.objects.create(
                created_user=self._user,
                parent_attr=attr,
                value="hoge",
                referral=ref_entry1,
            )
        )

        self.assertFalse(attr.is_updated({"id": ref_entry1.id, "name": "hoge"}))
        self.assertTrue(attr.is_updated({"id": ref_entry2.id, "name": "hoge"}))
        self.assertTrue(attr.is_updated({"id": ref_entry1.id, "name": "fuga"}))
        self.assertTrue(attr.is_updated({"id": ref_entry1.id, "name": ""}))

    def test_attr_helper_of_attribute_with_array_named_ref(self):
        # If 'AUTO_COMPLEMENT_USER' in settings is unmatch
        settings.AIRONE["AUTO_COMPLEMENT_USER"] = settings.AIRONE["AUTO_COMPLEMENT_USER"] + "1"

        ref_entity = Entity.objects.create(name="referred_entity", created_user=self._user)
        ref_entry = Entry.objects.create(
            name="referred_entry", created_user=self._user, schema=ref_entity
        )

        r_entries = []
        for i in range(0, 3):
            r_entry = Entry.objects.create(
                name="r_%d" % i, created_user=self._user, schema=ref_entity
            )
            r_entries.append({"id": r_entry.id})

        entity = Entity.objects.create(name="entity", created_user=self._user)
        new_attr_params = {
            "name": "arr_named_ref",
            "type": AttrType.ARRAY_NAMED_OBJECT,
            "created_user": self._user,
            "parent_entity": entity,
        }
        attr_base = EntityAttr.objects.create(**new_attr_params)
        attr_base.referral.add(ref_entity)

        # create an Entry associated to the 'entity'
        entry = Entry.objects.create(name="entry", created_user=self._user, schema=entity)
        entry.complement_attrs(self._user)

        attr: Attribute = entry.attrs.get(name="arr_named_ref")
        self.assertFalse(attr.is_updated([]))
        self.assertTrue(attr.is_updated([{"id": None}]))
        self.assertTrue(attr.is_updated([{"name": ""}]))
        self.assertTrue(attr.is_updated([{"boolean": False}]))
        self.assertTrue(attr.is_updated([{"id": ref_entry.id}]))
        self.assertTrue(attr.is_updated([{"name": "hoge"}]))
        self.assertTrue(attr.is_updated([{"boolean": True}]))

        attr.add_value(self._user, [{"name": "hoge"}])
        self.assertFalse(attr.is_updated([{"name": "hoge"}]))
        self.assertFalse(attr.is_updated([{"name": "hoge", "id": ""}]))
        self.assertFalse(attr.is_updated([{"name": "hoge", "id": None}]))
        self.assertFalse(attr.is_updated([{"name": "hoge", "boolean": False}]))
        self.assertTrue(attr.is_updated([{"name": ""}]))

        attr.add_value(self._user, [{"id": ref_entry.id}])
        self.assertFalse(attr.is_updated([{"id": ref_entry}]))
        self.assertFalse(attr.is_updated([{"id": ref_entry.id}]))
        self.assertFalse(attr.is_updated([{"id": ref_entry.id, "name": ""}]))
        self.assertFalse(attr.is_updated([{"id": ref_entry.id, "boolean": False}]))
        self.assertTrue(attr.is_updated([{"id": ""}]))
        self.assertTrue(attr.is_updated([{"id": None}]))

        attr.add_value(self._user, [{"name": "hoge", "boolean": True}])
        self.assertFalse(attr.is_updated([{"name": "hoge", "boolean": True}]))
        self.assertFalse(attr.is_updated([{"name": "hoge", "boolean": True, "id": ""}]))
        self.assertFalse(attr.is_updated([{"name": "hoge", "boolean": True, "id": None}]))
        self.assertTrue(attr.is_updated([{"name": "hoge", "boolean": False}]))

        attr.add_value(
            self._user,
            [
                {
                    "name": "key_%d" % x,
                    "id": r_entries[x]["id"],
                }
                for x in range(0, 3)
            ],
        )

        self.assertFalse(
            attr.is_updated(
                [{"id": x["id"], "name": y} for x, y in zip(r_entries, ["key_0", "key_1", "key_2"])]
            )
        )
        self.assertFalse(
            attr.is_updated(
                [
                    {"id": x["id"], "name": y, "boolean": False}
                    for x, y in zip(r_entries, ["key_0", "key_1", "key_2"])
                ]
            )
        )
        self.assertTrue(attr.is_updated([{"name": x} for x in ["key_0", "key_1", "key_2"]]))
        self.assertTrue(
            attr.is_updated(
                [{"id": x["id"], "name": y} for x, y in zip(r_entries, ["key_0", "key_1"])]
            )
        )
        self.assertTrue(attr.is_updated(r_entries))
        self.assertTrue(
            attr.is_updated(
                [
                    {"id": x["id"], "name": y, "boolean": True}
                    for x, y in zip(r_entries, ["key_0", "key_1", "key_2"])
                ]
            )
        )

    def test_for_boolean_attr_and_value(self):
        attr = self.make_attr("attr_bool", AttrType.BOOLEAN)

        # Checks get_latest_value returns empty AttributeValue
        # even if target attribute doesn't have any value
        attrv = attr.get_latest_value()
        self.assertIsNotNone(attrv)
        self.assertIsNone(attrv.referral)
        self.assertIsNone(attrv.date)

        attr.values.add(
            AttributeValue.objects.create(
                **{
                    "created_user": self._user,
                    "parent_attr": attr,
                }
            )
        )

        # Checks default value
        self.assertIsNotNone(attr.get_latest_value())
        self.assertFalse(attr.get_latest_value().boolean)

        # Checks attitude of is_update
        self.assertFalse(attr.is_updated(False))
        self.assertTrue(attr.is_updated(True))

    def test_for_date_attr_and_value(self):
        attr = self.make_attr("attr_date", AttrType.DATE)

        attr.values.add(
            AttributeValue.objects.create(
                **{
                    "created_user": self._user,
                    "parent_attr": attr,
                }
            )
        )

        # Checks default value
        self.assertIsNotNone(attr.get_latest_value())
        self.assertIsNone(attr.get_latest_value().date)

        # Checks attitude of is_update
        self.assertTrue(attr.is_updated(date(9999, 12, 31)))
        self.assertTrue(attr.is_updated("9999-12-31"))

        # Checks is_updated() return False when current value is empty
        # and empty string "" was specified
        self.assertFalse(attr.is_updated(""))
        self.assertFalse(attr.is_updated("2022-01-99"))

        # Checks is_updated() return True when current value is NOT empty
        # and empty string "" was specified
        attr.add_value(self._user, date(2022, 7, 7))
        self.assertTrue(attr.is_updated(""))

    def test_for_group_attr_and_value(self):
        test_group = Group.objects.create(name="g0")

        # create test target Attribute and empty AttributeValue for it
        attr = self.make_attr("attr_date", AttrType.GROUP)
        attr.add_value(self._user, None)

        # The cases when value will be updated
        for v in [str(test_group.id), test_group.id, test_group]:
            self.assertTrue(attr.is_updated(v))

        # The cases when value won't be updated
        for v in [None, "0", 0, "123456"]:
            self.assertFalse(attr.is_updated(v))

    def test_for_array_group_attr_and_value(self):
        test_groups = [Group.objects.create(name=x) for x in ["g0", "g1"]]

        # create test target Attribute and empty AttributeValue for it
        attr = self.make_attr("attr_date", AttrType.ARRAY_GROUP)
        attr.add_value(self._user, None)

        # The cases when value will be updated
        for v in [
            [str(x.id) for x in test_groups],
            [x.id for x in test_groups],
            test_groups,
        ]:
            self.assertTrue(attr.is_updated(v))

        # The cases when value won't be updated
        for v in [[], [None], None]:
            self.assertFalse(attr.is_updated(v))

    def test_for_number_attr_and_value(self):
        # create test target Attribute and empty AttributeValue for it
        attr = self.make_attr("attr_number", AttrType.NUMBER)
        attr.add_value(self._user, None)

        # The cases when value will be updated
        for v in [123.45, 67.89, -45.67, 0, 1e10, 1e-10, "123.45", "67"]:
            self.assertTrue(attr.is_updated(v))

        # The cases when value won't be updated
        for v in [None]:
            self.assertFalse(attr.is_updated(v))

        # Test with existing value
        attr.add_value(self._user, 123.45)
        self.assertFalse(attr.is_updated(123.45))
        self.assertTrue(attr.is_updated(67.89))

    def test_for_array_number_attr_and_value(self):
        # create test target Attribute and empty AttributeValue for it
        attr = self.make_attr("attr_array_number", AttrType.ARRAY_NUMBER)
        attr.add_value(self._user, None)

        # The cases when value will be updated
        for v in [
            [123.45, 67.89],
            [1, 2, 3],
            [-123.45, -67.89],
            [0, -0],
            [1e10, 1e-10],
            [123.45, None, 67.89],
            ["123.45", "67.89"],
        ]:
            self.assertTrue(attr.is_updated(v))

        # The cases when value won't be updated
        for v in [[], [None], None]:
            self.assertFalse(attr.is_updated(v))

        # Test with existing value
        attr.add_value(self._user, [123.45, 67.89])
        self.assertFalse(attr.is_updated([123.45, 67.89]))
        self.assertTrue(attr.is_updated([123.45, 99.99]))

        # Test with None values - None is treated as "no value" so filtered out
        attr.add_value(self._user, [123.45, None, 67.89])
        self.assertFalse(attr.is_updated([123.45, None, 67.89]))  # Same values should not update
        self.assertFalse(attr.is_updated([67.89, 123.45]))  # Order doesn't matter, None filtered
        self.assertTrue(attr.is_updated([123.45, 67.89, 999]))  # Adding value should update
