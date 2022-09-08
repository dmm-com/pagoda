from datetime import date
from unittest import skip

from django.conf import settings
from django.core.cache import cache

from acl.models import ACLBase
from airone.lib.acl import ACLObjType, ACLType
from airone.lib.test import AironeTestCase
from airone.lib.types import AttrTypeArrObj, AttrTypeArrStr, AttrTypeObj, AttrTypeStr, AttrTypeValue
from entity.models import Entity, EntityAttr
from entry.models import Attribute, AttributeValue, Entry
from entry.settings import CONFIG
from group.models import Group
from role.models import Role
from user.models import User


class ModelTest(AironeTestCase):
    def setUp(self):
        super(ModelTest, self).setUp()

        self._user = User(username="test")
        self._user.save()

        self._entity = Entity(name="entity", created_user=self._user)
        self._entity.save()

        self._entry = Entry(name="entry", created_user=self._user, schema=self._entity)
        self._entry.save()

        self._attr = self.make_attr("attr")
        self._attr.save()

        # clear all cache before start
        cache.clear()

        self._org_auto_complement_user = settings.AIRONE["AUTO_COMPLEMENT_USER"]

        # make auto complement user
        self._complement_user = User(
            username=self._org_auto_complement_user,
            email="hoge@example.com",
            is_superuser=True,
        )
        self._complement_user.set_password(self._org_auto_complement_user)
        self._complement_user.save()

    def _get_attrinfo_template(self, ref=None, group=None):
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
                "name": "date",
                "set_val": date(2018, 12, 31),
                "exp_val": date(2018, 12, 31),
            },
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

        return attrinfo

    def create_entity_with_all_type_attributes(self, user, ref_entity=None):
        """
        This is a test helper method to add attributes of all attribute-types
        to specified entity.
        """
        entity = Entity.objects.create(name="entity", created_user=user)
        attr_info = {
            "str": AttrTypeValue["string"],
            "text": AttrTypeValue["text"],
            "obj": AttrTypeValue["object"],
            "name": AttrTypeValue["named_object"],
            "bool": AttrTypeValue["boolean"],
            "group": AttrTypeValue["group"],
            "date": AttrTypeValue["date"],
            "arr_str": AttrTypeValue["array_string"],
            "arr_obj": AttrTypeValue["array_object"],
            "arr_name": AttrTypeValue["array_named_object"],
            "arr_group": AttrTypeValue["array_group"],
        }
        for attr_name, attr_type in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name, type=attr_type, created_user=user, parent_entity=entity
            )

            if attr_type & AttrTypeValue["object"] and ref_entity:
                attr.referral.add(ref_entity)

            entity.attrs.add(attr)

        return entity

    def tearDown(self):

        # settings initialization
        settings.AIRONE["AUTO_COMPLEMENT_USER"] = self._org_auto_complement_user

    def make_attr(self, name, attrtype=AttrTypeStr, user=None, entity=None, entry=None):
        entity_attr = EntityAttr.objects.create(
            name=name,
            type=attrtype,
            created_user=(user and user or self._user),
            parent_entity=(entity and entity or self._entity),
        )

        return Attribute.objects.create(
            name=name,
            schema=entity_attr,
            created_user=(user and user or self._user),
            parent_entry=(entry and entry or self._entry),
        )

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
        entry.attrs.add(attr)

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
            name="attr", type=AttrTypeValue["object"], created_user=user, parent_entity=entity
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
        self.assertEqual(list(user.permissions.filter(name="writable").all()), [attrbase.writable])

    def test_inherite_attribute_permission_of_group(self):
        user = User.objects.create(username="hoge")
        group = Group.objects.create(name="group")
        user.groups.add(group)

        entity = Entity.objects.create(name="entity", created_user=user)
        attrbase = EntityAttr.objects.create(
            name="attr", type=AttrTypeValue["object"], created_user=user, parent_entity=entity
        )

        # set a permission to the user
        group.permissions.add(attrbase.writable)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.add_attribute_from_base(attrbase, user)

        self.assertEqual(list(group.permissions.filter(name="writable").all()), [attrbase.writable])

    def test_update_attribute_from_base(self):
        user = User.objects.create(username="hoge")

        # test objects to be handled as referral
        entity = Entity.objects.create(name="entity", created_user=user)

        attrbase = EntityAttr.objects.create(
            name="attrbase",
            type=AttrTypeStr.TYPE,
            created_user=user,
            parent_entity=entity,
        )
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        # the case setting attribute lock to assure adding adding attribute processing
        # should be run only one time.
        cache_key = "add_%d" % attrbase.id
        entry.set_cache(cache_key, True)
        self.assertIsNone(entry.add_attribute_from_base(attrbase, user))
        self.assertEqual(entry.attrs.count(), 0)

        entry.clear_cache(cache_key)
        attr = entry.add_attribute_from_base(attrbase, user)
        self.assertEqual(entry.attrs.count(), 1)

        # check not to create multiple same Attribute objects by add_attribute_from_base method
        self.assertIsNone(entry.add_attribute_from_base(attrbase, user))
        self.assertEqual(entry.attrs.count(), 1)

        # update attrbase
        attrbase.name = "hoge"
        attrbase.type = AttrTypeObj.TYPE
        attrbase.referral.add(entity)
        attrbase.is_mandatory = True

        self.assertEqual(Attribute.objects.get(id=attr.id).schema, attrbase)

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

        attr = self.make_attr("attr2", attrtype=AttrTypeObj, entity=entity, entry=entry)
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

        attr = self.make_attr("attr2", attrtype=AttrTypeArrStr, entity=entity, entry=entry)
        attr_value = AttributeValue.objects.create(created_user=self._user, parent_attr=attr)
        attr_value.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)

        attr_value.data_array.add(
            AttributeValue.objects.create(value="hoge", created_user=self._user, parent_attr=attr)
        )

        attr_value.data_array.add(
            AttributeValue.objects.create(value="fuga", created_user=self._user, parent_attr=attr)
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

        attr = self.make_attr("attr2", attrtype=AttrTypeArrObj, entity=entity, entry=entry)
        attr_value = AttributeValue.objects.create(created_user=self._user, parent_attr=attr)
        attr_value.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)

        attr_value.data_array.add(
            AttributeValue.objects.create(referral=e1, created_user=self._user, parent_attr=attr)
        )

        attr_value.data_array.add(
            AttributeValue.objects.create(referral=e2, created_user=self._user, parent_attr=attr)
        )

        attr.values.add(attr_value)

        self.assertFalse(attr.is_updated([e1.id, e2.id]))
        self.assertFalse(attr.is_updated([e2.id, e1.id]))
        self.assertTrue(attr.is_updated([e1.id, e3.id]))  # update
        self.assertTrue(attr.is_updated([e1.id]))  # delete
        self.assertTrue(attr.is_updated([e3.id]))  # delete & update
        self.assertTrue(attr.is_updated([e1.id, e2.id, e3.id]))  # create
        self.assertTrue(attr.is_updated([e1.id, e3.id, e4.id]))  # create & update

        # checks that this method also accepts Entry
        self.assertFalse(attr.is_updated([e2, e1]))
        self.assertTrue(attr.is_updated([e1, e3]))

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
            "type": AttrTypeValue["named_object"],
            "created_user": self._user,
            "parent_entity": entity,
        }
        attr_base = EntityAttr.objects.create(**new_attr_params)
        attr_base.referral.add(ref_entity)

        entity.attrs.add(attr_base)

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
        settings.AIRONE["AUTO_COMPLEMENT_USER"] = self._org_auto_complement_user + "1"

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
            "type": AttrTypeValue["array_named_object"],
            "created_user": self._user,
            "parent_entity": entity,
        }
        attr_base = EntityAttr.objects.create(**new_attr_params)
        attr_base.referral.add(ref_entity)

        entity.attrs.add(attr_base)

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
        attr = self.make_attr("attr_bool", AttrTypeValue["boolean"])

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
        attr = self.make_attr("attr_date", AttrTypeValue["date"])

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
        attr = self.make_attr("attr_date", AttrTypeValue["group"])
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
        attr = self.make_attr("attr_date", AttrTypeValue["array_group"])
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

    def test_get_attribute_value_during_updating(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="entity", created_user=user)
        entity.attrs.add(
            EntityAttr.objects.create(
                name="attr",
                type=AttrTypeValue["string"],
                created_user=user,
                parent_entity=entity,
            )
        )

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        attr = entry.attrs.first()

        attrvs = [attr.add_value(self._user, str(x)) for x in range(2)]

        # Clear all is_latest flags to simulate a period of time in adding AttributeValue.
        attr.unset_latest_flag()

        # During updating processing, it may happen that there is no latest value in an attribute
        # for a short period of time. At that case, this returns last attribute value instead of
        # creating new one.
        self.assertEqual(attr.get_latest_value(), attrvs[-1])

    def test_get_referred_objects(self):
        entity = Entity.objects.create(name="Entity2", created_user=self._user)
        entry1 = Entry.objects.create(name="r1", created_user=self._user, schema=entity)
        entry2 = Entry.objects.create(name="r2", created_user=self._user, schema=entity)

        attr = self.make_attr("attr_ref", attrtype=AttrTypeValue["object"])

        # this attribute is needed to check not only get referral from normal object attribute,
        # but also from an attribute that refers array referral objects
        arr_attr = self.make_attr("attr_arr_ref", attrtype=AttrTypeValue["array_object"])

        # make multiple value that refer 'entry' object
        [
            attr.values.add(
                AttributeValue.objects.create(
                    created_user=self._user, parent_attr=attr, referral=entry1
                )
            )
            for _ in range(0, 10)
        ]
        # make a self reference value
        attr.values.add(
            AttributeValue.objects.create(
                created_user=self._user, parent_attr=attr, referral=self._entry
            )
        )

        # set another referral value to the 'attr_arr_ref' attr
        arr_attr.add_value(self._user, [entry1, entry2])

        self._entry.attrs.add(attr)
        self._entry.attrs.add(arr_attr)

        # This function checks that this get_referred_objects method only get
        # unique reference objects except for the self referred object.
        for entry in [entry1, entry2]:
            referred_entries = entry.get_referred_objects()
            self.assertEqual(referred_entries.count(), 1)
            self.assertEqual(list(referred_entries), [self._entry])

    def test_get_referred_objects_with_entity_param(self):
        for i in range(3, 6):
            entity = Entity.objects.create(name="Entity" + str(i), created_user=self._user)
            entry = Entry.objects.create(
                name="entry" + str(i), created_user=self._user, schema=entity
            )

            attr = self.make_attr(
                "attr_ref" + str(i),
                attrtype=AttrTypeValue["object"],
                entity=entity,
                entry=entry,
            )

            # make a reference 'entry' object
            attr.values.add(
                AttributeValue.objects.create(
                    created_user=self._user, parent_attr=attr, referral=self._entry
                )
            )

            entry.attrs.add(attr)

        # This function checks that this get_referred_objects method only get
        # unique reference objects except for the self referred object.
        referred_entries = self._entry.get_referred_objects()
        self.assertEqual(referred_entries.count(), 3)

        referred_entries = self._entry.get_referred_objects(filter_entities=["Entity3"])
        self.assertEqual(referred_entries.count(), 1)
        self.assertEqual(referred_entries.first().name, "entry3")

        referred_entries = self._entry.get_referred_objects(exclude_entities=["Entity3"])
        self.assertEqual(referred_entries.count(), 2)
        self.assertEqual([x.name for x in referred_entries], ["entry4", "entry5"])

    def test_coordinating_attribute_with_dynamically_added_one(self):
        newattr = EntityAttr.objects.create(
            name="newattr",
            type=AttrTypeStr,
            created_user=self._user,
            parent_entity=self._entity,
        )
        self._entity.attrs.add(newattr)

        # create new attributes which are appended after creation of Entity
        self._entry.complement_attrs(self._user)

        self.assertEqual(self._entry.attrs.count(), 1)
        self.assertEqual(self._entry.attrs.last().schema, newattr)

    def test_get_value_history(self):
        self._entity.attrs.add(
            EntityAttr.objects.create(
                **{
                    "name": "attr",
                    "type": AttrTypeStr,
                    "created_user": self._user,
                    "parent_entity": self._entity,
                }
            )
        )
        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=self._user)
        entry.complement_attrs(self._user)

        for i in range(10):
            entry.attrs.first().add_value(self._user, "value-%d" % i)

        # check to get value history from the rear
        history = entry.get_value_history(self._user, count=2)
        self.assertEqual(len(history), 2)
        self.assertEqual([x["curr"]["value"] for x in history], ["value-9", "value-8"])
        self.assertEqual([x["prev"]["value"] for x in history], ["value-8", "value-7"])

        # check to skip history value by specifying index parameter
        history = entry.get_value_history(self._user, count=3, index=3)
        self.assertEqual(len(history), 3)
        self.assertEqual([x["curr"]["value"] for x in history], ["value-6", "value-5", "value-4"])

        # check get the oldest value of history value
        history = entry.get_value_history(self._user, count=10, index=9)
        self.assertEqual(len(history), 1)
        self.assertEqual([x["curr"]["value"] for x in history], ["value-0"])
        self.assertEqual([x["prev"] for x in history], [None])

    def test_delete_entry(self):
        entity = Entity.objects.create(name="ReferredEntity", created_user=self._user)
        entry = Entry.objects.create(name="entry", created_user=self._user, schema=entity)

        attr = self.make_attr("attr_ref", attrtype=AttrTypeObj)

        self._entry.attrs.add(attr)

        # make a self reference value
        attr.values.add(
            AttributeValue.objects.create(created_user=self._user, parent_attr=attr, referral=entry)
        )

        # set referral cache
        self.assertEqual(list(entry.get_referred_objects()), [self._entry])

        # register entry to the Elasticsearch to check that will be deleted
        deleting_entry_id = self._entry.id
        self._entry.register_es()
        res = self._es.get(
            index=settings.ES_CONFIG["INDEX"], doc_type="entry", id=deleting_entry_id
        )
        self.assertTrue(res["found"])

        # delete an entry that have an attribute which refers to the entry of ReferredEntity
        self._entry.delete(deleted_user=self._user)
        self.assertFalse(self._entry.is_active)
        self.assertEqual(self._entry.attrs.filter(is_active=True).count(), 0)
        self.assertEqual(self._entry.deleted_user, self._user)
        self.assertIsNotNone(self._entry.deleted_time)

        # make sure that referral cache is updated by deleting referring entry
        self.assertEqual(list(entry.get_referred_objects()), [])

        # checks that the document in the Elasticsearch associated with the entry was also deleted
        res = self._es.get(
            index=settings.ES_CONFIG["INDEX"],
            doc_type="entry",
            id=deleting_entry_id,
            ignore=[404],
        )
        self.assertFalse(res["found"])

    def test_delete_entry_in_chain(self):
        # initilaize referral Entries for checking processing caused
        # by setting 'is_delete_in_chain' flag
        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=self._user)
        ref_entries = [
            Entry.objects.create(name="ref-%d" % i, created_user=self._user, schema=ref_entity)
            for i in range(3)
        ]

        # initialize EntityAttrs
        attr_info = {
            "obj": {"type": AttrTypeValue["object"], "value": ref_entries[0]},
            "arr_obj": {"type": AttrTypeValue["array_object"], "value": ref_entries},
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

            if info["type"] & AttrTypeValue["object"]:
                attr.referral.add(ref_entity)

            self._entity.attrs.add(attr)

        # create and initialize Entries
        entries = []
        for index in range(2):
            entry = Entry.objects.create(
                name="entry-%d" % index, schema=self._entity, created_user=self._user
            )
            entry.complement_attrs(self._user)
            entries.append(entry)

        # set AttributeValues of entry-0 that refers all referral entries
        for attr_name, info in attr_info.items():
            attr = entries[0].attrs.get(schema__name=attr_name)
            attr.add_value(self._user, info["value"])

        # set AttributeValues of entry-1 that refers only ref-2
        entries[1].attrs.get(schema__name="obj").add_value(self._user, ref_entries[2])

        # delete entry-0 and check the existance of each referred entries
        entries[0].delete()

        # sync referral entries from database
        [x.refresh_from_db() for x in ref_entries]

        self.assertFalse(ref_entries[0].is_active)
        self.assertFalse(ref_entries[1].is_active)
        self.assertTrue(ref_entries[2].is_active)

    def test_order_of_array_named_ref_entries(self):
        ref_entity = Entity.objects.create(name="referred_entity", created_user=self._user)
        ref_entry = Entry.objects.create(
            name="referred_entry", created_user=self._user, schema=ref_entity
        )

        entity = Entity.objects.create(name="entity", created_user=self._user)
        new_attr_params = {
            "name": "arr_named_ref",
            "type": AttrTypeValue["array_named_object"],
            "created_user": self._user,
            "parent_entity": entity,
        }
        attr_base = EntityAttr.objects.create(**new_attr_params)
        attr_base.referral.add(ref_entity)

        entity.attrs.add(attr_base)

        # create an Entry associated to the 'entity'
        entry = Entry.objects.create(name="entry", created_user=self._user, schema=entity)
        entry.complement_attrs(self._user)

        attr = entry.attrs.get(name="arr_named_ref")
        self.assertTrue(attr.is_updated([{"id": ref_entry.id}]))

        attrv = attr.add_value(
            self._user,
            [
                {
                    "name": "key_%d" % i,
                    "id": Entry.objects.create(
                        name="r_%d" % i, created_user=self._user, schema=ref_entity
                    ),
                }
                for i in range(3, 0, -1)
            ],
        )

        # checks the order of entries for array_named_ref that are shown in the views of
        # list/show/edit
        results = entry.get_available_attrs(self._user)
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]["last_value"]), 3)
        self.assertEqual(results[0]["last_value"][0]["value"], "key_1")
        self.assertEqual(results[0]["last_value"][1]["value"], "key_2")
        self.assertEqual(results[0]["last_value"][2]["value"], "key_3")

        # checks whether attribute will be invisible when a correspond EntityAttr is deleted
        attr_base.delete()
        results = entry.get_available_attrs(self._user)
        self.assertEqual(len(results), 0)

        # check following switched value case
        # initiated value is
        #   - [{'key_3': 'r_3'}, {'key_2': 'r_2'}, {'key_1': 'r_1'}]
        # then, check following value is different
        #   - [{'key_1': 'r_3'}, {'key_2': 'r_2'}, {'key_3': 'r_1'}]
        new_value = [
            {
                "name": "key_3",
                "id": attrv.data_array.get(referral__name="r_1").referral.id,
            },
            {
                "name": "key_2",
                "id": attrv.data_array.get(referral__name="r_2").referral.id,
            },
            {
                "name": "key_1",
                "id": attrv.data_array.get(referral__name="r_3").referral.id,
            },
        ]
        self.assertTrue(attr.is_updated(new_value))

    def test_clone_attribute_value(self):
        basic_params = {
            "created_user": self._user,
            "parent_attr": self._attr,
        }
        attrv = AttributeValue.objects.create(value="hoge", **basic_params)

        for i in range(0, 10):
            attrv.data_array.add(AttributeValue.objects.create(value=str(i), **basic_params))

        clone = attrv.clone(self._user)

        self.assertIsNotNone(clone)
        self.assertNotEqual(clone.id, attrv.id)
        self.assertNotEqual(clone.created_time, attrv.created_time)

        # check that data_array is cleared after cloning
        self.assertEqual(attrv.data_array.count(), 10)
        self.assertEqual(clone.data_array.count(), 0)

        # check that value and permission will be inherited from original one
        self.assertEqual(clone.value, attrv.value)

    def test_clone_attribute_without_permission(self):
        unknown_user = User.objects.create(username="unknown")

        attr = self.make_attr(name="attr", attrtype=AttrTypeValue["array_string"])
        attr.is_public = False
        attr.save()
        self.assertIsNone(attr.clone(unknown_user))

    def test_clone_attribute_typed_string(self):
        attr = self.make_attr(name="attr", attrtype=AttrTypeValue["string"])
        attr.add_value(self._user, "hoge")
        cloned_attr = attr.clone(self._user)

        self.assertIsNotNone(cloned_attr)
        self.assertNotEqual(cloned_attr.id, attr.id)
        self.assertEqual(cloned_attr.name, attr.name)
        self.assertEqual(cloned_attr.values.count(), attr.values.count())
        self.assertNotEqual(cloned_attr.values.last(), attr.values.last())

    def test_clone_attribute_typed_array_string(self):
        attr = self.make_attr(name="attr", attrtype=AttrTypeValue["array_string"])
        attr.add_value(self._user, [str(i) for i in range(10)])

        cloned_attr = attr.clone(self._user)
        self.assertIsNotNone(cloned_attr)
        self.assertNotEqual(cloned_attr.id, attr.id)
        self.assertEqual(cloned_attr.name, attr.name)
        self.assertEqual(cloned_attr.values.count(), attr.values.count())
        self.assertNotEqual(cloned_attr.values.last(), attr.values.last())

        # checks that AttributeValues that parent_attr has also be cloned
        orig_attrv = attr.values.last()
        cloned_attrv = cloned_attr.values.last()

        self.assertEqual(orig_attrv.data_array.count(), cloned_attrv.data_array.count())
        for v1, v2 in zip(orig_attrv.data_array.all(), cloned_attrv.data_array.all()):
            self.assertNotEqual(v1, v2)
            self.assertEqual(v1.value, v2.value)

    def test_clone_entry(self):
        test_entity = Entity.objects.create(name="E0", created_user=self._user)
        test_entity.attrs.add(
            EntityAttr.objects.create(
                **{
                    "name": "string",
                    "type": AttrTypeValue["string"],
                    "created_user": self._user,
                    "parent_entity": test_entity,
                }
            )
        )

        test_entity.attrs.add(
            EntityAttr.objects.create(
                **{
                    "name": "arrobj",
                    "type": AttrTypeValue["array_object"],
                    "created_user": self._user,
                    "parent_entity": test_entity,
                }
            )
        )

        entry = Entry.objects.create(name="entry", schema=test_entity, created_user=self._user)
        entry.complement_attrs(self._user)

        # register initial AttributeValue for each Attributes
        attr_string = entry.attrs.get(schema__name="string", is_active=True)
        for i in range(3):
            attr_string.add_value(self._user, str(i))

        attr_arrobj = entry.attrs.get(schema__name="arrobj", is_active=True)
        attr_arrobj.add_value(self._user, [entry])

        cloned_entry = entry.clone(self._user)

        self.assertIsNotNone(cloned_entry)
        self.assertNotEqual(cloned_entry.id, entry.id)
        self.assertEqual(cloned_entry.name, entry.name)
        self.assertEqual(cloned_entry.attrs.count(), entry.attrs.count())
        self.assertNotEqual(cloned_entry.attrs.last(), attr_string)

        # checks parent_entry in the cloned Attribute object is updated
        for (original_attr, cloned_attr) in [
            (
                attr_string,
                cloned_entry.attrs.get(schema__name="string", is_active=True),
            ),
            (
                attr_arrobj,
                cloned_entry.attrs.get(schema__name="arrobj", is_active=True),
            ),
        ]:

            self.assertEqual(original_attr.parent_entry, entry)
            self.assertEqual(cloned_attr.parent_entry, cloned_entry)

            # checks parent_entry in the cloned AttributeValue object is updated
            self.assertEqual(original_attr.values.last().parent_attr, original_attr)
            self.assertEqual(cloned_attr.values.last().parent_attr, cloned_attr)

            # checks AttributeValue.parent_attr for each child AttributeValue(s)
            cloned_attrv = cloned_attr.values.last()
            for co_attrv in cloned_attrv.data_array.all():
                self.assertEqual(co_attrv.parent_attr, cloned_attr)
                self.assertEqual(co_attrv.parent_attrv, cloned_attrv)

    def test_clone_entry_with_non_permitted_attributes(self):
        # set EntityAttr attr3 is not public
        attr_infos = [
            {"name": "attr1", "is_public": True},
            {"name": "attr2", "is_public": True},
            {"name": "attr3", "is_public": False},
        ]
        for info in attr_infos:
            self._entity.attrs.add(
                EntityAttr.objects.create(
                    **{
                        "type": AttrTypeValue["string"],
                        "created_user": self._user,
                        "parent_entity": self._entity,
                        "name": info["name"],
                        "is_public": info["is_public"],
                    }
                )
            )

        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=self._user)
        entry.complement_attrs(self._user)

        # set Attribute attr2 is not public
        entry.attrs.filter(schema__name="attr2").update(is_public=False)

        # checks that cloned entry doesn't have non-permitted attributes
        cloned_entry = entry.clone(self._user)

        self.assertEqual(cloned_entry.attrs.count(), 1)
        self.assertEqual(cloned_entry.attrs.first().schema.name, "attr1")

    def test_clone_entry_with_extra_params(self):
        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=self._user)
        entry.complement_attrs(self._user)

        clone = entry.clone(self._user, name="cloned_entry")

        self.assertIsNotNone(clone)
        self.assertNotEqual(clone.id, entry.id)
        self.assertEqual(clone.name, "cloned_entry")

    def test_clone_entry_without_permission(self):
        unknown_user = User.objects.create(username="unknown_user")
        role = Role.objects.create(name="role")

        entry = Entry.objects.create(
            name="entry", schema=self._entity, created_user=self._user, is_public=False
        )

        entry.complement_attrs(self._user)
        self.assertIsNone(entry.clone(unknown_user))

        # set permission to access, then it can be cloned
        role.permissions.add(entry.readable)
        role.users.add(unknown_user)
        self.assertIsNotNone(entry.clone(unknown_user))

    def test_set_value_method(self):
        user = User.objects.create(username="hoge")
        test_groups = [Group.objects.create(name=x) for x in ["g1", "g2"]]

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)

        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        # set initial values for entry
        attr_info = [
            {"name": "obj", "val": ref_entry},
            {"name": "name", "val": {"name": "new_value", "id": ref_entry}},
            {"name": "arr_obj", "val": [ref_entry]},
            {"name": "arr_name", "val": [{"name": "new_value", "id": ref_entry}]},
            {"name": "arr_group", "val": test_groups},
        ]
        for info in attr_info:
            attr = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["val"])

        latest_value = entry.attrs.get(name="obj").get_latest_value()
        self.assertEqual(latest_value.referral.id, ref_entry.id)

        latest_value = entry.attrs.get(name="name").get_latest_value()
        self.assertEqual(latest_value.value, "new_value")
        self.assertEqual(latest_value.referral.id, ref_entry.id)

        latest_value = entry.attrs.get(name="arr_obj").get_latest_value()
        self.assertEqual([x.referral.id for x in latest_value.data_array.all()], [ref_entry.id])

        latest_value = entry.attrs.get(name="arr_name").get_latest_value()
        self.assertEqual(
            [(x.value, x.referral.id) for x in latest_value.data_array.all()],
            [("new_value", ref_entry.id)],
        )

        latest_value = entry.attrs.get(name="arr_group").get_latest_value()
        self.assertEqual(
            [int(x.value) for x in latest_value.data_array.all()],
            [x.id for x in test_groups],
        )

    def test_get_available_attrs(self):
        user = User.objects.create(username="hoge")
        test_group = Group.objects.create(name="test-group")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)
        aclbase_ref = ACLBase.objects.get(id=ref_entry.id)

        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        # set initial values for entry
        attrinfo = {}
        for info in self._get_attrinfo_template(ref_entry, test_group):
            attr = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["set_val"])

            if info["name"] not in attrinfo:
                attrinfo[info["name"]] = {}

            attrinfo[info["name"]]["attr"] = attr
            if attr.schema.type == AttrTypeValue["named_object"]:
                attrinfo[info["name"]]["exp_val"] = {
                    "value": "bar",
                    "id": aclbase_ref.id,
                    "name": aclbase_ref.name,
                }
            elif attr.schema.type == AttrTypeValue["object"]:
                attrinfo[info["name"]]["exp_val"] = aclbase_ref
            elif attr.schema.type == AttrTypeValue["array_named_object"]:
                attrinfo[info["name"]]["exp_val"] = [
                    {
                        "value": "hoge",
                        "id": aclbase_ref.id,
                        "name": aclbase_ref.name,
                    }
                ]
            elif attr.schema.type == AttrTypeValue["array_object"]:
                attrinfo[info["name"]]["exp_val"] = [aclbase_ref]
            elif attr.schema.type == AttrTypeValue["group"]:
                attrinfo[info["name"]]["exp_val"] = test_group
            elif attr.schema.type == AttrTypeValue["array_group"]:
                attrinfo[info["name"]]["exp_val"] = [test_group]
            else:
                attrinfo[info["name"]]["exp_val"] = info["exp_val"]

        results = entry.get_available_attrs(user)
        for result in results:
            attr = attrinfo[result["name"]]["attr"]

            self.assertEqual(result["id"], attr.id)
            self.assertEqual(result["entity_attr_id"], attr.schema.id)
            self.assertEqual(result["type"], attr.schema.type)
            self.assertEqual(result["is_mandatory"], attr.schema.is_mandatory)
            self.assertEqual(result["index"], attr.schema.index)
            self.assertEqual(result["is_readble"], True)
            self.assertEqual(result["last_value"], attrinfo[attr.name]["exp_val"])

    def test_get_available_attrs_with_multi_attribute(self):
        self._entity.attrs.add(self._attr.schema)
        self._entry.attrs.add(self._attr)

        # Add and register duplicate Attribute after registers
        dup_attr = Attribute.objects.create(
            name=self._attr.schema.name,
            schema=self._attr.schema,
            created_user=self._user,
            parent_entry=self._entry,
        )
        self._entry.attrs.add(dup_attr)

        self._attr.delete()

        attr = self._entry.attrs.filter(schema=self._attr.schema, is_active=True).first()
        attr.add_value(self._user, "hoge")

        results = self._entry.get_available_attrs(self._user)
        self.assertEqual(results[0]["last_value"], "hoge")

    def test_get_available_attrs_with_multi_attribute_value(self):
        self._entity.attrs.add(self._attr.schema)
        self._entry.attrs.add(self._attr)

        attr = self._entry.attrs.filter(schema=self._attr.schema, is_active=True).first()
        attr.add_value(self._user, "hoge")
        attr.add_value(self._user, "fuga")

        results = self._entry.get_available_attrs(self._user)
        self.assertEqual(results[0]["last_value"], "fuga")

        # AttributeValue with is_latest set to True is duplicated(rare case)
        attr.values.all().update(is_latest=True)

        results = self._entry.get_available_attrs(self._user)
        self.assertEqual(results[0]["last_value"], "fuga")

    def test_set_attrvalue_to_entry_attr_without_availabe_value(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="entity", created_user=user)
        entity.attrs.add(
            EntityAttr.objects.create(
                **{
                    "name": "attr",
                    "type": AttrTypeValue["object"],
                    "created_user": user,
                    "parent_entity": entity,
                }
            )
        )

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        attr = entry.attrs.first()
        attrv = attr.add_value(user, None)

        self.assertIsNotNone(attrv)
        self.assertEqual(attr.values.count(), 1)
        self.assertIsNone(attr.values.first().referral)

    @skip(
        """
    The situation of this test mentioned, data_type of AttributeValue is changed, may not happen
    thrugoh current implementation. So test skips this case.
    """
    )
    def test_update_data_type_of_attrvalue(self):
        """
        This test checks that data_type parameter of AttributeValue will be changed after
        calling 'get_available_attrs' method if that parameter is not set.

        Basically, the data_type of AttributeValue is same with the type of Attribute. But,
        some AttributeValues which are registered before adding this parameter do not have
        available value. So this processing is needed to set. This assumes unknown typed
        AttributeValue as the current type of Attribute.
        """
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="entity", created_user=user)
        entity.attrs.add(
            EntityAttr.objects.create(
                **{
                    "name": "attr",
                    "type": AttrTypeValue["string"],
                    "created_user": user,
                    "parent_entity": entity,
                }
            )
        )

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        attrv = entry.attrs.first().add_value(user, "hoge")

        # vanish data_type of initial AttributeValue instance
        attrv.data_type = 0
        attrv.save()

        # this processing complements data_type parameter of latest AttributeValue
        # as the current type of Attribute instance
        results = entry.get_available_attrs(self._user)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["last_value"], "")
        self.assertEqual(AttributeValue.objects.get(id=attrv.id).data_type, AttrTypeValue["string"])

    def test_get_deleted_referred_attrs(self):
        user = User.objects.create(username="hoge")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=user)
        ref_entry = Entry.objects.create(name="ReferredEntry", schema=ref_entity, created_user=user)

        attr_info = {
            "obj": {"type": AttrTypeValue["object"], "value": ref_entry},
            "name": {
                "type": AttrTypeValue["named_object"],
                "value": {"name": "hoge", "id": ref_entry},
            },
            "arr_obj": {"type": AttrTypeValue["array_object"], "value": [ref_entry]},
            "arr_name": {
                "type": AttrTypeValue["array_named_object"],
                "value": [{"name": "hoge", "id": ref_entry}],
            },
        }

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )

            attr.referral.add(ref_entity)
            entity.attrs.add(attr)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        for attr_name, info in attr_info.items():
            entry.attrs.get(name=attr_name).add_value(user, info["value"])

        # checks all set vaialbles can be got correctly
        available_attrs = entry.get_available_attrs(user)
        self.assertEqual(len(available_attrs), len(attr_info))
        for attr in available_attrs:
            if attr["name"] == "obj":
                self.assertEqual(attr["last_value"].id, ref_entry.id)
            elif attr["name"] == "name":
                self.assertEqual(attr["last_value"]["value"], "hoge")
                self.assertEqual(attr["last_value"]["id"], ref_entry.id)
                self.assertEqual(attr["last_value"]["name"], ref_entry.name)
            elif attr["name"] == "arr_obj":
                self.assertEqual([x.id for x in attr["last_value"]], [ref_entry.id])
            elif attr["name"] == "arr_name":
                self.assertEqual([x["value"] for x in attr["last_value"]], ["hoge"])
                self.assertEqual([x["id"] for x in attr["last_value"]], [ref_entry.id])
                self.assertEqual([x["name"] for x in attr["last_value"]], [ref_entry.name])

        # delete referral entry, then get available attrs
        ref_entry.delete()
        available_attrs = entry.get_available_attrs(user)
        self.assertEqual(len(available_attrs), len(attr_info))
        for attr in available_attrs:
            if attr["name"] == "obj":
                self.assertIsNone(attr["last_value"])
            elif attr["name"] == "name":
                self.assertEqual(attr["last_value"]["value"], "hoge")
                self.assertFalse(any([x in attr["last_value"] for x in ["id", "name"]]))
            elif attr["name"] == "arr_obj":
                self.assertEqual(attr["last_value"], [])
            elif attr["name"] == "arr_name":
                self.assertEqual([x["value"] for x in attr["last_value"]], ["hoge"])
                self.assertFalse(any([x in attr["last_value"] for x in ["id", "name"]]))

    def test_get_available_attrs_with_empty_referral(self):
        user = User.objects.create(username="hoge")

        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=user)
        entity = Entity.objects.create(name="entity", created_user=user)
        attr_info = {
            "obj": {"type": AttrTypeValue["object"], "value": None},
            "name": {
                "type": AttrTypeValue["named_object"],
                "value": {"name": "hoge", "id": None},
            },
            "arr_obj": {"type": AttrTypeValue["array_object"], "value": []},
            "arr_name": {
                "type": AttrTypeValue["array_named_object"],
                "value": [{"name": "hoge", "id": None}],
            },
        }

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )

            attr.referral.add(ref_entity)
            entity.attrs.add(attr)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        for attr_name, info in attr_info.items():
            entry.attrs.get(name=attr_name).add_value(user, info["value"])

        # get empty values for each attributes
        available_attrs = entry.get_available_attrs(user)
        self.assertEqual(len(available_attrs), len(attr_info))
        for attr in available_attrs:
            if attr["name"] == "obj":
                self.assertIsNone(attr["last_value"])
            elif attr["name"] == "name":
                self.assertEqual(attr["last_value"], {"value": "hoge"})
            elif attr["name"] == "arr_obj":
                self.assertEqual(attr["last_value"], [])
            elif attr["name"] == "arr_name":
                self.assertEqual(attr["last_value"], [{"value": "hoge"}])

    def test_get_value_of_attrv(self):
        user = User.objects.create(username="hoge")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        test_ref = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)
        test_grp = Group.objects.create(name="g0")

        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        # memo
        attr_info = [
            {"name": "str", "set_val": "foo", "exp_val": "foo"},
            {"name": "obj", "set_val": str(test_ref.id), "exp_val": test_ref.name},
            {"name": "obj", "set_val": test_ref.id, "exp_val": test_ref.name},
            {"name": "obj", "set_val": test_ref, "exp_val": test_ref.name},
            {
                "name": "name",
                "set_val": {"name": "bar", "id": str(test_ref.id)},
                "exp_val": {"bar": test_ref.name},
            },
            {
                "name": "name",
                "set_val": {"name": "bar", "id": test_ref.id},
                "exp_val": {"bar": test_ref.name},
            },
            {
                "name": "name",
                "set_val": {"name": "bar", "id": test_ref},
                "exp_val": {"bar": test_ref.name},
            },
            {"name": "bool", "set_val": False, "exp_val": False},
            {
                "name": "arr_str",
                "set_val": ["foo", "bar", "baz"],
                "exp_val": ["foo", "bar", "baz"],
            },
            {
                "name": "arr_obj",
                "set_val": [str(test_ref.id)],
                "exp_val": [test_ref.name],
            },
            {"name": "arr_obj", "set_val": [test_ref.id], "exp_val": [test_ref.name]},
            {"name": "arr_obj", "set_val": [test_ref], "exp_val": [test_ref.name]},
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": str(test_ref.id)}],
                "exp_val": [{"hoge": test_ref.name}],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": test_ref.id}],
                "exp_val": [{"hoge": test_ref.name}],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": test_ref}],
                "exp_val": [{"hoge": test_ref.name}],
            },
            {
                "name": "date",
                "set_val": date(2018, 12, 31),
                "exp_val": date(2018, 12, 31),
            },
            {"name": "group", "set_val": str(test_grp.id), "exp_val": test_grp.name},
            {"name": "group", "set_val": test_grp.id, "exp_val": test_grp.name},
            {"name": "group", "set_val": test_grp, "exp_val": test_grp.name},
            {
                "name": "arr_group",
                "set_val": [str(test_grp.id)],
                "exp_val": [test_grp.name],
            },
            {"name": "arr_group", "set_val": [test_grp.id], "exp_val": [test_grp.name]},
            {"name": "arr_group", "set_val": [test_grp], "exp_val": [test_grp.name]},
        ]
        for info in attr_info:
            attr = entry.attrs.get(name=info["name"])
            attr.add_value(user, info["set_val"])
            attrv = attr.get_latest_value()

            # test return value of get_value method
            self.assertEqual(attrv.get_value(), info["exp_val"])

            # test return value of get_value method with 'with_metainfo' parameter
            expected_value = {"type": attr.schema.type, "value": info["exp_val"]}
            if attr.schema.type & AttrTypeValue["array"]:
                if attr.schema.type & AttrTypeValue["named"]:
                    expected_value["value"] = [{"hoge": {"id": test_ref.id, "name": test_ref.name}}]
                elif attr.schema.type & AttrTypeValue["object"]:
                    expected_value["value"] = [{"id": test_ref.id, "name": test_ref.name}]
                elif attr.schema.type & AttrTypeValue["group"]:
                    expected_value["value"] = [{"id": test_grp.id, "name": test_grp.name}]

            elif attr.schema.type & AttrTypeValue["named"]:
                expected_value["value"] = {"bar": {"id": test_ref.id, "name": test_ref.name}}
            elif attr.schema.type & AttrTypeValue["object"]:
                expected_value["value"] = {"id": test_ref.id, "name": test_ref.name}
            elif attr.schema.type & AttrTypeValue["group"]:
                expected_value["value"] = {"id": test_grp.id, "name": test_grp.name}

            self.assertEqual(attrv.get_value(with_metainfo=True), expected_value)

    def test_get_value_with_serialize_parameter(self):
        # Craete Attribute instance and set test Date value
        date_value = date(2021, 6, 8)
        attr_date = self.make_attr("date", attrtype=AttrTypeValue["date"])
        attr_date.add_value(self._user, date_value)

        # test retrieved value by get_value method with serialize parameter is expected
        self.assertEqual(attr_date.get_latest_value().get_value(), date_value)
        self.assertEqual(attr_date.get_latest_value().get_value(serialize=True), str(date_value))

    def test_get_value_of_attrv_that_refers_deleted_entry(self):
        user = User.objects.create(username="hoge")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="Ref", schema=ref_entity, created_user=user)

        attr_info = {
            "obj": {"type": AttrTypeValue["object"], "value": str(ref_entry.id)},
            "name": {
                "type": AttrTypeValue["named_object"],
                "value": {"name": "foo", "id": str(ref_entry.id)},
            },
            "arr_obj": {
                "type": AttrTypeValue["array_object"],
                "value": [str(ref_entry.id)],
            },
            "arr_name": {
                "type": AttrTypeValue["array_named_object"],
                "value": [{"name": "bar", "id": str(ref_entry.id)}],
            },
        }
        entity = Entity.objects.create(name="Entity", created_user=user)
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )

            if info["type"] & AttrTypeValue["object"]:
                attr.referral.add(ref_entity)

            entity.attrs.add(attr)

        entry = Entry.objects.create(name="Entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        [entry.attrs.get(name=x).add_value(user, y["value"]) for (x, y) in attr_info.items()]

        # delete entry to which all attribute values refer
        ref_entry.delete()

        expected_results = {
            "obj": None,
            "name": {"foo": None},
            "arr_obj": [None],
            "arr_name": [{"bar": None}],
        }
        for name, result in expected_results.items():
            self.assertEqual(entry.attrs.get(name=name).get_latest_value().get_value(), result)

    def test_convert_value_to_register(self):
        user = User.objects.create(username="hoge")

        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="Ref Entry", schema=ref_entity, created_user=user)

        entity = self.create_entity_with_all_type_attributes(user, ref_entity)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        group = Group.objects.create(name="Group")
        deleted_group = Group.objects.create(name="Deleting Group")
        deleted_group.delete()

        checklist = [
            {"attr": "str", "input": "foo", "checker": lambda x: x == "foo"},
            {
                "attr": "obj",
                "input": "Ref Entry",
                "checker": lambda x: x.id == ref_entry.id,
            },
            {"attr": "obj", "input": "Invalid Entry", "checker": lambda x: x is None},
            {
                "attr": "name",
                "input": {"foo": ref_entry},
                "checker": lambda x: x["name"] == "foo" and x["id"].id == ref_entry.id,
            },
            {"attr": "bool", "input": False, "checker": lambda x: x is False},
            {
                "attr": "arr_str",
                "input": ["foo", "bar"],
                "checker": lambda x: x == ["foo", "bar"],
            },
            {
                "attr": "arr_obj",
                "input": ["Ref Entry"],
                "checker": lambda x: len(x) == 1 and x[0].id == ref_entry.id,
            },
            {
                "attr": "arr_obj",
                "input": ["Ref Entry", "Invalid Entry"],
                "checker": lambda x: len(x) == 1 and x[0].id == ref_entry.id,
            },
            {
                "attr": "arr_name",
                "input": [{"foo": "Ref Entry"}],
                "checker": lambda x: len(x) == 1
                and x[0]["name"] == "foo"
                and x[0]["id"].id == ref_entry.id,
            },
            {
                "attr": "arr_name",
                "input": [{"foo": "Ref Entry"}, {"bar": "Invalid Entry"}],
                "checker": lambda x: (
                    len(x) == 2
                    and x[0]["name"] == "foo"
                    and x[0]["id"].id == ref_entry.id
                    and x[1]["name"] == "bar"
                    and x[1]["id"] is None
                ),
            },
            {
                "attr": "group",
                "input": "Group",
                "checker": lambda x: x == str(group.id),
            },
            {
                "attr": "group",
                "input": str(group.id),
                "checker": lambda x: x == str(group.id),
            },
            {
                "attr": "group",
                "input": group.id,
                "checker": lambda x: x == str(group.id),
            },
            {"attr": "group", "input": group, "checker": lambda x: x == str(group.id)},
            {"attr": "group", "input": deleted_group, "checker": lambda x: x is None},
            {
                "attr": "arr_group",
                "input": ["Group"],
                "checker": lambda x: x == [str(group.id)],
            },
            {
                "attr": "arr_group",
                "input": [str(group.id)],
                "checker": lambda x: x == [str(group.id)],
            },
            {
                "attr": "arr_group",
                "input": [group.id],
                "checker": lambda x: x == [str(group.id)],
            },
            {
                "attr": "arr_group",
                "input": [group],
                "checker": lambda x: x == [str(group.id)],
            },
            {
                "attr": "arr_group",
                "input": [deleted_group],
                "checker": lambda x: x == [],
            },
            {
                "attr": "date",
                "input": date(2018, 12, 31),
                "checker": lambda x: x == date(2018, 12, 31),
            },
            {
                "attr": "date",
                "input": "2020-01-01",
                "checker": lambda x: x == "2020-01-01",
            },
        ]
        for info in checklist:
            attr = entry.attrs.get(name=info["attr"])

            converted_data = attr.convert_value_to_register(info["input"])

            self.assertTrue(info["checker"](converted_data))

            # create AttributeValue using converted value
            attr.add_value(user, converted_data)

            self.assertIsNotNone(attr.get_latest_value())

    def test_export_entry(self):
        user = User.objects.create(username="hoge")

        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        attr_info = {
            "str1": {"type": AttrTypeValue["string"], "is_public": True},
            "str2": {"type": AttrTypeValue["string"], "is_public": True},
            "obj": {"type": AttrTypeValue["object"], "is_public": True},
            "invisible": {"type": AttrTypeValue["string"], "is_public": False},
        }

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
                is_public=info["is_public"],
            )

            if info["type"] & AttrTypeValue["object"]:
                attr.referral.add(ref_entity)

            entity.attrs.add(attr)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.attrs.get(name="str1").add_value(user, "hoge")

        entry.attrs.get(name="str2").add_value(user, "foo")
        # update AttributeValue of Attribute 'str2'
        entry.attrs.get(name="str2").add_value(user, "bar")

        exported_data = entry.export(user)
        self.assertEqual(exported_data["name"], entry.name)
        self.assertEqual(
            len(exported_data["attrs"]),
            len([x for x in attr_info.values() if x["is_public"]]),
        )

        self.assertEqual(exported_data["attrs"]["str1"], "hoge")
        self.assertEqual(exported_data["attrs"]["str2"], "bar")
        self.assertIsNone(exported_data["attrs"]["obj"])

        # change the name of EntityAttr then export entry
        NEW_ATTR_NAME = "str1 (changed)"
        entity_attr = entry.schema.attrs.get(name="str1")
        entity_attr.name = NEW_ATTR_NAME
        entity_attr.save()

        exported_data = entry.export(user)
        self.assertTrue(NEW_ATTR_NAME in exported_data["attrs"])
        self.assertEqual(exported_data["attrs"][NEW_ATTR_NAME], "hoge")

        # Add an Attribute after creating entry
        entity.attrs.add(
            EntityAttr.objects.create(
                **{
                    "name": "new_attr",
                    "type": AttrTypeValue["string"],
                    "created_user": user,
                    "parent_entity": entity,
                }
            )
        )
        exported_data = entry.export(user)
        self.assertTrue("new_attr" in exported_data["attrs"])

    def test_search_entries(self):
        user = User.objects.create(username="hoge")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(
            name="referred_entry", schema=ref_entity, created_user=user
        )
        ref_group = Group.objects.create(name="group")

        attr_info = {
            "str": {"type": AttrTypeValue["string"], "value": "foo-%d"},
            "str2": {"type": AttrTypeValue["string"], "value": "foo-%d"},
            "obj": {"type": AttrTypeValue["object"], "value": str(ref_entry.id)},
            "name": {
                "type": AttrTypeValue["named_object"],
                "value": {"name": "bar", "id": str(ref_entry.id)},
            },
            "bool": {"type": AttrTypeValue["boolean"], "value": True},
            "group": {"type": AttrTypeValue["group"], "value": str(ref_group.id)},
            "date": {"type": AttrTypeValue["date"], "value": date(2018, 12, 31)},
            "arr_str": {
                "type": AttrTypeValue["array_string"],
                "value": ["foo", "bar", "baz"],
            },
            "arr_obj": {
                "type": AttrTypeValue["array_object"],
                "value": [str(x.id) for x in Entry.objects.filter(schema=ref_entity)],
            },
            "arr_name": {
                "type": AttrTypeValue["array_named_object"],
                "value": [{"name": "hoge", "id": str(ref_entry.id)}],
            },
            "arr_group": {"type": AttrTypeValue["array_group"], "value": [ref_group]},
        }

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )

            if info["type"] & AttrTypeValue["object"]:
                attr.referral.add(ref_entity)

            entity.attrs.add(attr)

        for index in range(0, 11):
            entry = Entry.objects.create(name="e-%d" % index, schema=entity, created_user=user)
            entry.complement_attrs(user)

            for attr_name, info in attr_info.items():
                attr = entry.attrs.get(name=attr_name)
                if attr_name == "str":
                    attr.add_value(user, info["value"] % index)
                elif attr_name == "str2":
                    attr.add_value(user, info["value"] % (index + 100))
                else:
                    attr.add_value(user, info["value"])

            entry.register_es()

        # search entries
        ret = Entry.search_entries(
            user,
            [entity.id],
            [
                {"name": "str"},
                {"name": "str2"},
                {"name": "obj"},
                {"name": "name"},
                {"name": "bool"},
                {"name": "group"},
                {"name": "date"},
                {"name": "arr_str"},
                {"name": "arr_obj"},
                {"name": "arr_name"},
                {"name": "arr_group"},
            ],
        )
        self.assertEqual(ret["ret_count"], 11)
        self.assertEqual(len(ret["ret_values"]), 11)

        # check returned contents is corrected
        for v in ret["ret_values"]:
            self.assertEqual(v["entity"]["id"], entity.id)
            self.assertEqual(len(v["attrs"]), len(attr_info))

            entry = Entry.objects.get(id=v["entry"]["id"])

            for (attrname, attrinfo) in v["attrs"].items():
                attr = entry.attrs.get(schema__name=attrname)
                attrv = attr.get_latest_value()

                # checks accurate type parameters are stored
                self.assertEqual(attrinfo["type"], attrv.data_type)

                # checks accurate values are stored
                if attrname == "str" or attrname == "str2":
                    self.assertEqual(attrinfo["value"], attrv.value)

                elif attrname == "obj":
                    self.assertEqual(attrinfo["value"]["id"], attrv.referral.id)
                    self.assertEqual(attrinfo["value"]["name"], attrv.referral.name)

                elif attrname == "name":
                    key = attrv.value
                    self.assertEqual(attrinfo["value"][key]["id"], attrv.referral.id)
                    self.assertEqual(attrinfo["value"][key]["name"], attrv.referral.name)

                if attrname == "bool":
                    self.assertEqual(attrinfo["value"], str(attrv.boolean))

                if attrname == "date":
                    self.assertEqual(attrinfo["value"], str(attrv.date))

                elif attrname == "group":
                    group = Group.objects.get(id=int(attrv.value))
                    self.assertEqual(attrinfo["value"]["id"], group.id)
                    self.assertEqual(attrinfo["value"]["name"], group.name)

                elif attrname == "arr_str":
                    self.assertEqual(
                        sorted([x for x in attrinfo["value"]]),
                        sorted([x.value for x in attrv.data_array.all()]),
                    )

                elif attrname == "arr_obj":
                    self.assertEqual(
                        [x["id"] for x in attrinfo["value"]],
                        [x.referral.id for x in attrv.data_array.all()],
                    )
                    self.assertEqual(
                        [x["name"] for x in attrinfo["value"]],
                        [x.referral.name for x in attrv.data_array.all()],
                    )

                elif attrname == "arr_name":
                    for co_attrv in attrv.data_array.all():
                        _co_v = [x[co_attrv.value] for x in attrinfo["value"]]
                        self.assertTrue(_co_v)
                        self.assertEqual(_co_v[0]["id"], co_attrv.referral.id)
                        self.assertEqual(_co_v[0]["name"], co_attrv.referral.name)

                elif attrname == "arr_group":
                    self.assertEqual(
                        attrinfo["value"],
                        [{"id": ref_group.id, "name": ref_group.name}],
                    )

                else:
                    assert "Invalid result was happend"

        # search entries with maximum entries to get
        ret = Entry.search_entries(user, [entity.id], [{"name": "str"}], 5)
        self.assertEqual(ret["ret_count"], 11)
        self.assertEqual(len(ret["ret_values"]), 5)

        # search entries with keyword
        ret = Entry.search_entries(user, [entity.id], [{"name": "str", "keyword": "foo-5"}])
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual(ret["ret_values"][0]["entry"]["name"], "e-5")

        # search entries with blank values
        entry = Entry.objects.create(name="entry-blank", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.register_es()

        for attrname in attr_info.keys():
            ret = Entry.search_entries(user, [entity.id], [{"name": attrname}])
            self.assertEqual(len([x for x in ret["ret_values"] if x["entry"]["id"] == entry.id]), 1)

        # check functionallity of the 'exact_match' parameter
        ret = Entry.search_entries(user, [entity.id], [{"name": "str", "keyword": "foo-1"}])
        self.assertEqual(ret["ret_count"], 2)
        ret = Entry.search_entries(
            user,
            [entity.id],
            [{"name": "str", "keyword": "foo-1", "exact_match": True}],
        )
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual(ret["ret_values"][0]["entry"]["name"], "e-1")

        # check functionallity of the 'entry_name' parameter
        ret = Entry.search_entries(user, [entity.id], entry_name="e-1")
        self.assertEqual(ret["ret_count"], 2)

        # check combination of 'entry_name' and 'hint_attrs' parameter
        ret = Entry.search_entries(
            user, [entity.id], [{"name": "str", "keyword": "foo-10"}], entry_name="e-1"
        )
        self.assertEqual(ret["ret_count"], 1)

        # check whether keyword would be insensitive case
        ret = Entry.search_entries(user, [entity.id], [{"name": "str", "keyword": "FOO-10"}])
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual(ret["ret_values"][0]["entry"]["name"], "e-10")

        # check to get Entries that only have substantial Attribute values
        for attr in entity.attrs.filter(is_active=True):
            result = Entry.search_entries(user, [entity.id], [{"name": attr.name, "keyword": "*"}])

            if attr.type != AttrTypeValue["boolean"]:
                # confirm "entry-black" Entry, which doesn't have any substantial Attribute values,
                # doesn't exist on the result.
                isin_entry_blank = any(
                    [x["entry"]["name"] == "entry-blank" for x in result["ret_values"]]
                )
                self.assertFalse(isin_entry_blank)

                # confirm Entries, which have substantial Attribute values, are returned
                self.assertEqual(result["ret_count"], 11)

            else:
                # both True and False value will be matched for boolean type Attribute
                self.assertEqual(result["ret_count"], 12)

    def test_search_entries_with_hint_referral(self):
        user = User.objects.create(username="hoge")

        # Initialize entities -- there are 2 entities as below
        # * ReferredEntity - has no attribute
        # * Entity - has an attribute that refers ReferredEntity
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        entity = Entity.objects.create(name="Entity", created_user=user)
        entity_attr = EntityAttr.objects.create(
            name="attr_ref",
            type=AttrTypeValue["object"],
            created_user=user,
            parent_entity=entity,
        )
        entity_attr.referral.add(ref_entity)
        entity.attrs.add(entity_attr)

        # Initialize entries as below
        ref_entries = [
            Entry.objects.create(name="ref%d" % i, schema=ref_entity, created_user=user)
            for i in range(3)
        ]
        for index in range(10):
            entry = Entry.objects.create(name="e-%d" % index, schema=entity, created_user=user)
            entry.complement_attrs(user)

            # set referral entry (ref0, ref1) alternately
            entry.attrs.first().add_value(user, ref_entries[index % 2])

        for ref_entry in ref_entries:
            ref_entry.register_es()

        # call search_entries with 'hint_referral' parameter,
        # then checks that result includes referral entries
        ret = Entry.search_entries(user, [ref_entity.id], [], hint_referral=True)
        self.assertEqual(ret["ret_count"], 3)
        self.assertEqual(
            sorted([x["id"] for x in ret["ret_values"][0]["referrals"]]),
            sorted([x.id for x in ref_entries[0].get_referred_objects()]),
        )

        # call search_entries with 'hint_referral',
        ret = Entry.search_entries(user, [ref_entity.id], [], hint_referral="e-")
        self.assertEqual(ret["ret_count"], 2)

        # call search_entries with 'hint_referral' parameter as string,
        # then checks that result includes referral entries that match specified referral name
        ret = Entry.search_entries(user, [ref_entity.id], [], hint_referral="e-1")
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual([x["entry"]["name"] for x in ret["ret_values"]], ["ref1"])

        # call search_entries with 'hint_referral' parameter as name of entry
        # which is not referred from any entries.
        ret = Entry.search_entries(user, [ref_entity.id], [], hint_referral="hogefuga")
        self.assertEqual(ret["ret_count"], 0)

        # call search_entries with 'backslash' in the 'hint_referral' parameter as entry of name
        ret = Entry.search_entries(
            user, [ref_entity.id], [], hint_referral=CONFIG.EMPTY_SEARCH_CHARACTER
        )
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual([x["entry"]["name"] for x in ret["ret_values"]], ["ref2"])

    def test_search_entries_with_exclusive_attrs(self):
        user = User.objects.create(username="hoge")
        entity_info = {
            "E1": [{"type": AttrTypeValue["string"], "name": "foo"}],
            "E2": [{"type": AttrTypeValue["string"], "name": "bar"}],
        }

        entity_ids = []
        for (name, attrinfos) in entity_info.items():
            entity = Entity.objects.create(name=name, created_user=user)
            entity_ids.append(entity.id)

            for attrinfo in attrinfos:
                entity.attrs.add(
                    EntityAttr.objects.create(
                        **{
                            "name": attrinfo["name"],
                            "type": attrinfo["type"],
                            "created_user": user,
                            "parent_entity": entity,
                        }
                    )
                )

            for i in [x for x in range(0, 5)]:
                entry = Entry.objects.create(
                    name="%s-%d" % (entity.name, i), schema=entity, created_user=user
                )
                entry.complement_attrs(user)

                for attrinfo in attrinfos:
                    attr = entry.attrs.get(schema__name=attrinfo["name"])
                    attr.add_value(user, str(i))

                entry.register_es()

        # search entries by only attribute name and keyword without entity with exclusive attrs
        ret = Entry.search_entries(
            user,
            entity_ids,
            [{"name": "foo", "keyword": ""}, {"name": "bar", "keyword": ""}],
        )
        self.assertEqual(ret["ret_count"], 10)
        self.assertEqual(
            sorted([x["entry"]["name"] for x in ret["ret_values"]]),
            sorted(["E1-%d" % i for i in range(5)] + ["E2-%d" % i for i in range(5)]),
        )

        # search entries by only attribute name and keyword without entity
        # with exclusive attrs and one keyword
        ret = Entry.search_entries(
            user,
            entity_ids,
            [{"name": "foo", "keyword": "3"}, {"name": "bar", "keyword": ""}],
        )
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual(sorted([x["entry"]["name"] for x in ret["ret_values"]]), sorted(["E1-3"]))

        # search entries by only attribute name and keyword without entity
        # with exclusive hint attrs and keywords
        ret = Entry.search_entries(
            user,
            entity_ids,
            [{"name": "foo", "keyword": "3"}, {"name": "bar", "keyword": "3"}],
        )
        self.assertEqual(ret["ret_count"], 0)

    def test_search_entries_about_insensitive_case(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="Entity", created_user=user)
        entry = Entry.objects.create(name="Foo", schema=entity, created_user=user)
        entry.register_es()

        # This checks entry_name parameter would be insensitive case
        for name in ["foo", "fOO", "OO", "f"]:
            resp = Entry.search_entries(user, [entity.id], entry_name=name)
            self.assertEqual(resp["ret_count"], 1)
            self.assertEqual(resp["ret_values"][0]["entry"]["id"], entry.id)

    def test_search_entries_with_deleted_hint(self):
        # This call search_entries with hint_attrs that contains values which specify
        # entry name that has already deleted.

        # Initialize entities -- there are 2 entities as below
        # * ReferredEntity - has no attribute
        # * Entity - has an attribute that refers ReferredEntity
        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=self._user)
        ref_entries = [
            Entry.objects.create(name="ref-%d" % i, schema=ref_entity, created_user=self._user)
            for i in range(4)
        ]

        entity = Entity.objects.create(name="Entity", created_user=self._user)
        ref_info = {
            "ref": {
                "type": AttrTypeValue["object"],
                "value": ref_entries[0],
                "expected_value": {"name": "", "id": ""},
            },
            "name": {
                "type": AttrTypeValue["named_object"],
                "value": {"name": "hoge", "id": ref_entries[1]},
                "expected_value": {"hoge": {"name": "", "id": ""}},
            },
            "arr_ref": {
                "type": AttrTypeValue["array_object"],
                "value": [ref_entries[2]],
                "expected_value": [],
            },
            "arr_name": {
                "type": AttrTypeValue["array_named_object"],
                "value": [{"name": "hoge", "id": ref_entries[3]}],
                "expected_value": [{"hoge": {"name": "", "id": ""}}],
            },
        }
        for (attr_name, info) in ref_info.items():
            entity_attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=self._user,
                parent_entity=entity,
            )
            entity_attr.referral.add(ref_entity)
            entity.attrs.add(entity_attr)

        # Initialize an entry that refers 'ref' entry which will be deleted later
        entry = Entry.objects.create(name="ent", schema=entity, created_user=self._user)
        entry.complement_attrs(self._user)
        for (attr_name, info) in ref_info.items():
            attr = entry.attrs.get(name=attr_name)
            attr.add_value(self._user, info["value"])

        # Finally, register this created entry to Elasticsearch
        entry.register_es()

        # delete each referred entries from 'ent' entry
        for ent in ref_entries:
            ent.delete()

        # Check search result when each referred entries which is specified in the hint still exist
        for attr_name in ref_info.keys():
            # Check search result without keyword of hint_attrs
            hint_attr = {"name": attr_name, "keyword": ""}
            ret = Entry.search_entries(self._user, [entity.id], hint_attrs=[hint_attr])
            self.assertEqual(ret["ret_count"], 1)
            self.assertEqual(len(ret["ret_values"][0]["attrs"]), 1)

            for (_name, _info) in ret["ret_values"][0]["attrs"].items():
                self.assertTrue(_name in ref_info)
                self.assertEqual(_info["value"], ref_info[_name]["expected_value"])

            hint_attr = {"name": attr_name, "keyword": "ref"}
            ret = Entry.search_entries(self._user, [entity.id], hint_attrs=[hint_attr])
            self.assertEqual(ret["ret_count"], 0)
            self.assertEqual(ret["ret_values"], [])

    def test_search_entries_with_regex_hint_attrs(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="entity", created_user=user)
        attr = EntityAttr.objects.create(
            name="attr",
            type=AttrTypeValue["string"],
            created_user=user,
            parent_entity=entity,
        )
        entity.attrs.add(attr)

        for value in ["100", "101", "200"]:
            entry = Entry.objects.create(name=value, schema=entity, created_user=user)
            entry.complement_attrs(user)
            entry.attrs.get(schema=attr).add_value(user, value)
            entry.register_es()

        resp = Entry.search_entries(user, [entity.id], [{"name": attr.name, "keyword": "^10"}])
        self.assertEqual(resp["ret_count"], 2)
        resp = Entry.search_entries(user, [entity.id], [{"name": attr.name, "keyword": "00$"}])
        self.assertEqual(resp["ret_count"], 2)
        resp = Entry.search_entries(user, [entity.id], [{"name": attr.name, "keyword": "^100$"}])
        self.assertEqual(resp["ret_count"], 1)

    def test_register_entry_to_elasticsearch(self):
        ENTRY_COUNTS = 10
        user = User.objects.create(username="hoge")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)

        ref_entry1 = Entry.objects.create(
            name="referred_entry1", schema=ref_entity, created_user=user
        )
        Entry.objects.create(name="referred_entry2", schema=ref_entity, created_user=user)

        ref_group = Group.objects.create(name="group")

        attr_info = {
            "str": {
                "type": AttrTypeValue["string"],
                "value": "foo",
            },
            "obj": {
                "type": AttrTypeValue["object"],
                "value": str(ref_entry1.id),
            },
            "name": {
                "type": AttrTypeValue["named_object"],
                "value": {"name": "bar", "id": str(ref_entry1.id)},
            },
            "bool": {
                "type": AttrTypeValue["boolean"],
                "value": False,
            },
            "date": {
                "type": AttrTypeValue["date"],
                "value": date(2018, 1, 1),
            },
            "group": {
                "type": AttrTypeValue["group"],
                "value": str(ref_group.id),
            },
            "arr_str": {
                "type": AttrTypeValue["array_string"],
                "value": ["foo", "bar", "baz"],
            },
            "arr_obj": {
                "type": AttrTypeValue["array_object"],
                "value": [str(x.id) for x in Entry.objects.filter(schema=ref_entity)],
            },
            "arr_name": {
                "type": AttrTypeValue["array_named_object"],
                "value": [
                    {"name": "hoge", "id": str(x.id)}
                    for x in Entry.objects.filter(schema=ref_entity)
                ],
            },
        }

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )

            if info["type"] & AttrTypeValue["object"]:
                attr.referral.add(ref_entity)

            entity.attrs.add(attr)

        for index in range(0, ENTRY_COUNTS):
            entry = Entry.objects.create(name="e-%d" % index, schema=entity, created_user=user)
            entry.complement_attrs(user)

            for attr_name, info in attr_info.items():
                attr = entry.attrs.get(name=attr_name)
                attr.add_value(user, info["value"])

            entry.register_es()

        # checks that all entries are registered to the ElasticSearch.
        res = self._es.indices.stats(index=settings.ES_CONFIG["INDEX"])
        self.assertEqual(res["_all"]["total"]["segments"]["count"], ENTRY_COUNTS)

        # checks that all registered entries can be got from Elasticsearch
        for entry in Entry.objects.filter(schema=entity):
            res = self._es.get(index=settings.ES_CONFIG["INDEX"], doc_type="entry", id=entry.id)
            self.assertTrue(res["found"])

            # This checks whether returned results have all values of attributes
            self.assertEqual(
                set([x["name"] for x in res["_source"]["attr"]]),
                set(k for k in attr_info.keys()),
            )

            for (k, v) in attr_info.items():
                value = [x for x in res["_source"]["attr"] if x["name"] == k]

                self.assertTrue(all([x["type"] == v["type"] for x in value]))
                if k == "str":
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0]["value"], "foo")

                elif k == "obj":
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0]["value"], ref_entry1.name)
                    self.assertEqual(value[0]["referral_id"], ref_entry1.id)

                elif k == "name":
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0]["key"], "bar")
                    self.assertEqual(value[0]["value"], ref_entry1.name)
                    self.assertEqual(value[0]["referral_id"], ref_entry1.id)

                elif k == "bool":
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0]["value"], "False")

                elif k == "date":
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0]["date_value"], "2018-01-01")

                elif k == "group":
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0]["value"], ref_group.name)
                    self.assertEqual(value[0]["referral_id"], ref_group.id)

                elif k == "arr_str":
                    self.assertEqual(len(value), 3)
                    self.assertEqual(
                        sorted([x["value"] for x in value]),
                        sorted(["foo", "bar", "baz"]),
                    )

                elif k == "arr_obj":
                    self.assertEqual(len(value), Entry.objects.filter(schema=ref_entity).count())
                    self.assertEqual(
                        sorted([x["value"] for x in value]),
                        sorted([x.name for x in Entry.objects.filter(schema=ref_entity)]),
                    )
                    self.assertEqual(
                        sorted([x["referral_id"] for x in value]),
                        sorted([x.id for x in Entry.objects.filter(schema=ref_entity)]),
                    )

                elif k == "arr_name":
                    self.assertEqual(len(value), Entry.objects.filter(schema=ref_entity).count())
                    self.assertEqual(
                        sorted([x["value"] for x in value]),
                        sorted([x.name for x in Entry.objects.filter(schema=ref_entity)]),
                    )
                    self.assertEqual(
                        sorted([x["referral_id"] for x in value]),
                        sorted([x.id for x in Entry.objects.filter(schema=ref_entity)]),
                    )
                    self.assertTrue(all([x["key"] == "hoge" for x in value]))

        # checks delete entry and checks deleted entry will also be removed from Elasticsearch
        entry = Entry.objects.filter(schema=entity).last()
        entry.delete()

        res = self._es.indices.stats(index=settings.ES_CONFIG["INDEX"])
        self.assertEqual(res["_all"]["total"]["segments"]["count"], ENTRY_COUNTS - 1)

        res = self._es.get(
            index=settings.ES_CONFIG["INDEX"],
            doc_type="entry",
            id=entry.id,
            ignore=[404],
        )
        self.assertFalse(res["found"])

    def test_register_entry_to_elasticsearch_with_multi_attribute(self):
        self._entity.attrs.add(self._attr.schema)
        self._entry.attrs.add(self._attr)

        # Add and register duplicate Attribute after registers
        dup_attr = Attribute.objects.create(
            name=self._attr.schema.name,
            schema=self._attr.schema,
            created_user=self._user,
            parent_entry=self._entry,
        )
        self._entry.attrs.add(dup_attr)

        self._attr.delete()

        attr = self._entry.attrs.filter(schema=self._attr.schema, is_active=True).first()
        attr.add_value(self._user, "hoge")

        self._entry.register_es()

        res = self._es.get(index=settings.ES_CONFIG["INDEX"], doc_type="entry", id=self._entry.id)
        self.assertEqual(res["_source"]["attr"][0]["value"], "hoge")

    def test_unregister_entry_to_elasticsearch(self):
        user = User.objects.create(username="hoge")

        # initialize Entity and Entry to test
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        # register entry information to the Elasticsearch
        entry.register_es()

        ret = Entry.search_entries(user, [entity.id], [])
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual(
            [x["entry"] for x in ret["ret_values"]],
            [{"name": entry.name, "id": entry.id}],
        )

        # unregister entry information from the Elasticsearch
        entry.unregister_es()

        ret = Entry.search_entries(user, [entity.id], [])
        self.assertEqual(ret["ret_count"], 0)
        self.assertEqual(ret["ret_values"], [])

    def test_update_elasticsearch_field(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="entity", created_user=user)
        entity_attr = EntityAttr.objects.create(
            name="attr",
            type=AttrTypeValue["string"],
            created_user=user,
            parent_entity=entity,
        )
        entity.attrs.add(entity_attr)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        attr = entry.attrs.get(schema=entity_attr)
        attr.add_value(user, "hoge")

        # register entry to the Elasticsearch
        entry.register_es()

        # checks registered value is corrected
        res = self._es.get(index=settings.ES_CONFIG["INDEX"], doc_type="entry", id=entry.id)
        self.assertEqual(res["_source"]["attr"][0]["name"], entity_attr.name)
        self.assertEqual(res["_source"]["attr"][0]["type"], entity_attr.type)
        self.assertEqual(res["_source"]["attr"][0]["value"], "hoge")

        # update latest value of Attribute 'attr'
        attr.add_value(user, "fuga")
        entry.register_es()

        # checks registered value was also updated
        res = self._es.get(index=settings.ES_CONFIG["INDEX"], doc_type="entry", id=entry.id)
        self.assertEqual(res["_source"]["attr"][0]["value"], "fuga")

    def test_search_entries_from_elasticsearch(self):
        user = User.objects.create(username="hoge")

        entities = []
        for ename in ["eitnty1", "entity2"]:
            entity = Entity.objects.create(name=ename, created_user=user)

            entities.append(entity)
            for index in range(0, 2):
                entity.attrs.add(
                    EntityAttr.objects.create(
                        name="attr-%s" % index,
                        type=AttrTypeValue["string"],
                        created_user=user,
                        parent_entity=entity,
                    )
                )

            entity.attrs.add(
                EntityAttr.objects.create(
                    name="ほげ",
                    type=AttrTypeValue["string"],
                    created_user=user,
                    parent_entity=entity,
                )
            )

            entity.attrs.add(
                EntityAttr.objects.create(
                    name="attr-arr",
                    type=AttrTypeValue["array_string"],
                    created_user=user,
                    parent_entity=entity,
                )
            )

            entity.attrs.add(
                EntityAttr.objects.create(
                    name="attr-date",
                    type=AttrTypeValue["date"],
                    created_user=user,
                    parent_entity=entity,
                )
            )

        entry_info = {
            "entry1": {
                "attr-0": "2018/01/01",
                "attr-1": "bar",
                "ほげ": "ふが",
                "attr-date": date(2018, 1, 2),
                "attr-arr": ["hoge", "fuga"],
            },
            "entry2": {
                "attr-0": "hoge",
                "attr-1": "bar",
                "ほげ": "ふが",
                "attr-date": None,
                "attr-arr": ["2018/01/01"],
            },
            "entry3": {
                "attr-0": "0123-45-6789",  # This is date format but not date value
                "attr-1": "hoge",
                "ほげ": "fuga",
                "attr-date": None,
                "attr-arr": [],
            },
        }

        for entity in entities:
            for (name, attrinfo) in entry_info.items():
                entry = Entry.objects.create(name=name, schema=entity, created_user=user)
                entry.complement_attrs(user)

                for attr in entry.attrs.all():
                    attr.add_value(user, attrinfo[attr.schema.name])

                entry.register_es()

        # search entries of entity1 from Elasticsearch and checks that the entreis of non entity1
        # are not returned.
        resp = Entry.search_entries(user, [entities[0].id], [{"name": "attr-0"}])
        self.assertEqual(resp["ret_count"], 3)
        self.assertTrue(all([x["entity"]["id"] == entities[0].id for x in resp["ret_values"]]))

        # checks the value which is non date but date format was registered correctly
        self.assertEqual(
            [entry_info["entry3"]["attr-0"]],
            [
                x["attrs"]["attr-0"]["value"]
                for x in resp["ret_values"]
                if x["entry"]["name"] == "entry3"
            ],
        )

        # checks ret_count counts number of entries whatever attribute contidion was changed
        resp = Entry.search_entries(
            user, [entities[0].id], [{"name": "attr-0"}, {"name": "attr-1"}]
        )
        self.assertEqual(resp["ret_count"], 3)
        resp = Entry.search_entries(user, [entities[0].id, entities[1].id], [{"name": "attr-0"}])
        self.assertEqual(resp["ret_count"], 6)

        # checks results that contain multi-byte values could be got
        resp = Entry.search_entries(user, [entities[0].id], [{"name": "ほげ", "keyword": "ふが"}])
        self.assertEqual(resp["ret_count"], 2)
        self.assertEqual(
            sorted([x["entry"]["name"] for x in resp["ret_values"]]),
            sorted(["entry1", "entry2"]),
        )

        # search entries with date keyword parameter in string type from Elasticsearch
        resp = Entry.search_entries(
            user, [entities[0].id], [{"name": "attr-0", "keyword": "2018/01/01"}]
        )
        self.assertEqual(resp["ret_count"], 1)
        self.assertEqual(resp["ret_values"][0]["entry"]["name"], "entry1")
        self.assertEqual(resp["ret_values"][0]["attrs"]["attr-0"]["value"], "2018-01-01")

        # search entries with date keyword parameter in date type from Elasticsearch
        for x in ["2018-01-02", "2018/01/02", "2018-1-2", "2018-01-2", "2018-1-02"]:
            resp = Entry.search_entries(
                user, [entities[0].id], [{"name": "attr-date", "keyword": x}]
            )
            self.assertEqual(resp["ret_count"], 1)
            self.assertEqual(resp["ret_values"][0]["entry"]["name"], "entry1")
            self.assertEqual(resp["ret_values"][0]["attrs"]["attr-date"]["value"], "2018-01-02")

        # search entries with date keyword parameter in string array type from Elasticsearch
        resp = Entry.search_entries(
            user, [entities[0].id], [{"name": "attr-arr", "keyword": "2018-01-01"}]
        )
        self.assertEqual(resp["ret_count"], 1)
        self.assertEqual(resp["ret_values"][0]["entry"]["name"], "entry2")
        self.assertEqual(resp["ret_values"][0]["attrs"]["attr-arr"]["value"], ["2018-01-01"])

        # search entries with keyword parameter that other entry has same value in untarget attr
        resp = Entry.search_entries(user, [entities[0].id], [{"name": "attr-0", "keyword": "hoge"}])
        self.assertEqual(resp["ret_count"], 1)
        self.assertEqual(resp["ret_values"][0]["entry"]["name"], "entry2")

        # search entries with keyword parameter which is array type
        resp = Entry.search_entries(
            user, [entities[0].id], [{"name": "attr-arr", "keyword": "hoge"}]
        )
        self.assertEqual(resp["ret_count"], 1)
        self.assertEqual(resp["ret_values"][0]["entry"]["name"], "entry1")
        self.assertEqual(
            sorted(resp["ret_values"][0]["attrs"]["attr-arr"]["value"]),
            sorted(["hoge", "fuga"]),
        )

        # search entries with an invalid or unmatch date keyword parameter in date type
        # from Elasticsearch
        for x in ["2018/02/01", "hoge"]:
            resp = Entry.search_entries(
                user, [entities[0].id], [{"name": "attr-date", "keyword": x}]
            )
            self.assertEqual(resp["ret_count"], 0)

    def test_search_result_count(self):
        """
        This tests that ret_count of search_entries will be equal with actual count of entries.
        """
        user = User.objects.create(username="hoge")

        ref_entity = Entity.objects.create(name="ref_entity", created_user=user)
        ref_entry = Entry.objects.create(name="ref", schema=ref_entity, created_user=user)

        entity = Entity.objects.create(name="entity", created_user=user)
        for name in ["foo", "bar"]:
            attr = EntityAttr.objects.create(
                name=name,
                type=AttrTypeValue["object"],
                created_user=user,
                parent_entity=entity,
            )
            attr.referral.add(ref_entity)
            entity.attrs.add(attr)

        for i in range(0, 20):
            entry = Entry.objects.create(name="e%3d" % i, schema=entity, created_user=user)
            entry.complement_attrs(user)

            if i < 10:
                entry.attrs.get(schema__name="foo").add_value(user, ref_entry)
            else:
                entry.attrs.get(schema__name="bar").add_value(user, ref_entry)

            entry.register_es()

        resp = Entry.search_entries(user, [entity.id], [{"name": "foo", "keyword": "ref"}], limit=5)
        self.assertEqual(resp["ret_count"], 10)
        self.assertEqual(len(resp["ret_values"]), 5)

    def test_search_entities_have_individual_attrs(self):
        user = User.objects.create(username="hoge")

        entity_info = {"entity1": ["foo", "bar"], "entity2": ["bar", "hoge"]}

        entities = []
        for (entity_name, attrnames) in entity_info.items():
            entity = Entity.objects.create(name=entity_name, created_user=user)
            entities.append(entity.id)

            for attrname in attrnames:
                entity.attrs.add(
                    EntityAttr.objects.create(
                        name=attrname,
                        type=AttrTypeValue["string"],
                        created_user=user,
                        parent_entity=entity,
                    )
                )

            # create entries for this entity
            for i in range(0, 5):
                e = Entry.objects.create(name="entry-%d" % i, created_user=user, schema=entity)
                e.register_es()

        resp = Entry.search_entries(user, entities, [{"name": "foo"}])
        self.assertEqual(resp["ret_count"], 5)

        resp = Entry.search_entries(user, entities, [{"name": x} for x in ["foo", "hoge"]])
        self.assertEqual(resp["ret_count"], 10)

        resp = Entry.search_entries(user, entities, [{"name": x} for x in ["bar"]])
        self.assertEqual(resp["ret_count"], 10)
        for name in entity_info.keys():
            self.assertEqual(len([x for x in resp["ret_values"] if x["entity"]["name"] == name]), 5)

    def test_search_entries_sorted_result(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="EntityA", created_user=user)
        entity.save()

        # register AAA5, AAA0, AAA4, AAA1, AAA3, AAA2 in this order
        for i in range(3):
            e1 = Entry.objects.create(name="AAA%d" % (5 - i), schema=entity, created_user=user)
            e1.save()
            e1.register_es()

            e2 = Entry.objects.create(name="AAA%d" % i, schema=entity, created_user=user)
            e2.save()
            e2.register_es()

        # search
        resp = Entry.search_entries(user, [entity.id], entry_name="AAA")

        # 6 results should be returned
        self.assertEqual(resp["ret_count"], 6)
        # 6 results should be sorted
        for i in range(6):
            self.assertEqual(resp["ret_values"][i]["entry"]["name"], "AAA%d" % i)

    def test_search_entries_with_date(self):
        user = User.objects.create(username="hoge")

        # initialize Entity
        entity = Entity.objects.create(name="entity", created_user=user)
        entity.attrs.add(
            EntityAttr.objects.create(
                name="date",
                type=AttrTypeValue["date"],
                created_user=user,
                parent_entity=entity,
            )
        )

        # Initialize to create following Entries
        # (entry name) : (value in Attribute date)
        #   - entry-1  :  2018-01-01
        #   - entry-2  :  2018-02-01
        #   - entry-3  :  2018-03-01
        for month in range(1, 4):
            entry = Entry.objects.create(name="entry-%d" % month, schema=entity, created_user=user)
            entry.complement_attrs(user)

            attr = entry.attrs.first()
            attr.add_value(user, "2018-%02d-01" % month)

            entry.register_es()

        # search entry that have AttributeValue exact matches with specified date.
        ret = Entry.search_entries(user, [entity.id], [{"name": "date", "keyword": "2018/01/01"}])
        self.assertEqual(len(ret["ret_values"]), 1)
        self.assertEqual(ret["ret_values"][0]["entry"]["name"], "entry-1")

        # The case of using condition 'less thatn',
        # this expects that entry-2 and entry-3 are matched
        ret = Entry.search_entries(user, [entity.id], [{"name": "date", "keyword": ">2018-01-01"}])
        self.assertEqual(len(ret["ret_values"]), 2)
        self.assertEqual(
            sorted([x["entry"]["name"] for x in ret["ret_values"]]),
            ["entry-2", "entry-3"],
        )

        # The case of using condition 'greater thatn',
        # this expects that entry-1 and entry-2 are matched
        ret = Entry.search_entries(user, [entity.id], [{"name": "date", "keyword": "<2018-03-01"}])
        self.assertEqual(len(ret["ret_values"]), 2)
        self.assertEqual(
            sorted([x["entry"]["name"] for x in ret["ret_values"]]),
            ["entry-1", "entry-2"],
        )

        # The case of using both conditions, this expects that only entry-2 is matched
        ret = Entry.search_entries(
            user, [entity.id], [{"name": "date", "keyword": "<2018-03-01 >2018-01-01"}]
        )
        self.assertEqual(len(ret["ret_values"]), 1)
        self.assertEqual(ret["ret_values"][0]["entry"]["name"], "entry-2")

        # The same case of before one, but date format of keyward was changed
        ret = Entry.search_entries(
            user, [entity.id], [{"name": "date", "keyword": "<2018/03/01 >2018/01/01"}]
        )
        self.assertEqual(len(ret["ret_values"]), 1)
        self.assertEqual(ret["ret_values"][0]["entry"]["name"], "entry-2")

    def test_get_last_value(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="entity", created_user=user)
        for name in ["foo", "bar"]:
            entity.attrs.add(
                EntityAttr.objects.create(
                    name=name,
                    type=AttrTypeValue["string"],
                    created_user=user,
                    parent_entity=entity,
                )
            )

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        # the case of creating default empty AttributeValue
        attr = entry.attrs.get(schema__name="foo")
        self.assertEqual(attr.values.count(), 0)

        attrv = attr.get_last_value()
        self.assertIsNotNone(attrv)
        self.assertEqual(attrv.value, "")
        self.assertEqual(attrv, attr.get_latest_value())
        self.assertEqual(attr.values.count(), 1)

        # the case of creating specified AttributeValue
        attr = entry.attrs.get(schema__name="bar")
        self.assertEqual(attr.values.count(), 0)

        attr.add_value(user, "hoge")
        attrv = attr.get_last_value()
        self.assertIsNotNone(attrv)
        self.assertEqual(attrv.value, "hoge")
        self.assertEqual(attrv, attr.get_latest_value())
        self.assertEqual(attr.values.count(), 1)

    def test_get_latest_value_with_readonly(self):
        user = User.objects.create(username="hoge")
        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        for entity_attr in entity.attrs.all():
            entry.add_attribute_from_base(entity_attr, user)

        for attr in entry.attrs.all():
            self.assertIsNone(attr.get_latest_value(is_readonly=True))

    def test_get_value_with_is_active_false(self):
        user = User.objects.create(username="hoge")
        entity = self.create_entity_with_all_type_attributes(user)

        # create referred Entity and Entries
        test_ref = Entry.objects.create(name="r0", schema=entity, created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        
        attr_info = [
            {"name": "obj", "set_val": str(test_ref.id), "exp_val": test_ref.name},
            {"name": "obj", "set_val": test_ref.id, "exp_val": test_ref.name},
            {"name": "obj", "set_val": test_ref, "exp_val": test_ref.name},
            {
                "name": "name",
                "set_val": {"name": "bar", "id": str(test_ref.id)},
                "exp_val": {"bar": test_ref.name},
            },
            {
                "name": "name",
                "set_val": {"name": "bar", "id": test_ref.id},
                "exp_val": {"bar": test_ref.name},
            },
            {
                "name": "name",
                "set_val": {"name": "bar", "id": test_ref},
                "exp_val": {"bar": test_ref.name},
            },
            {
                "name": "arr_obj",
                "set_val": [str(test_ref.id)],
                "exp_val": [test_ref.name],
            },
            
            {"name": "arr_obj", "set_val": [test_ref.id], "exp_val": [test_ref.name]},
            {"name": "arr_obj", "set_val": [test_ref], "exp_val": [test_ref.name]},
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": str(test_ref.id)}],
                "exp_val": [{"hoge": test_ref.name}],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": test_ref.id}],
                "exp_val": [{"hoge": test_ref.name}],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": test_ref}],
                "exp_val": [{"hoge": test_ref.name}],
            },
        ]

        for info in attr_info:
            attr = entry.attrs.get(name=info["name"])
            attr.add_value(user, info["set_val"])
            attrv = attr.get_latest_value()

            # test return value of get_value method
            self.assertEqual(attrv.get_value(is_active=False), info["exp_val"])

            # test return value of get_value method with 'with_metainfo' parameter
            expected_value = {"type": attr.schema.type, "value": info["exp_val"]}
            if attr.schema.type & AttrTypeValue["array"]:
                if attr.schema.type & AttrTypeValue["named"]:
                    expected_value["value"] = [{"hoge": {"id": test_ref.id, "name": test_ref.name}}]
                elif attr.schema.type & AttrTypeValue["object"]:
                    expected_value["value"] = [{"id": test_ref.id, "name": test_ref.name}]
            elif attr.schema.type & AttrTypeValue["named"]:
                expected_value["value"] = {"bar": {"id": test_ref.id, "name": test_ref.name}}
            elif attr.schema.type & AttrTypeValue["object"]:
                expected_value["value"] = {"id": test_ref.id, "name": test_ref.name}

            self.assertEqual(attrv.get_value(with_metainfo=True, is_active=False), expected_value)
    
    def test_get_value_deleted_entry_with_is_active_false(self):
        user = User.objects.create(username="hoge")
        entity = self.create_entity_with_all_type_attributes(user)

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        test_ref = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        
        attr_info = [
            {"name": "obj", "set_val": str(test_ref.id), "exp_val": test_ref.id},
            {"name": "obj", "set_val": test_ref.id, "exp_val": test_ref.id},
            {"name": "obj", "set_val": test_ref, "exp_val": test_ref.id},
            {
                "name": "arr_obj",
                "set_val": [str(test_ref.id)],
                "exp_val": [test_ref.id],
            },
            {"name": "arr_obj", "set_val": [test_ref.id], "exp_val": [test_ref.id]},
            {"name": "arr_obj", "set_val": [test_ref], "exp_val": [test_ref.id]},
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": str(test_ref.id)}],
                "exp_val": [{"hoge": test_ref.id}],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": test_ref.id}],
                "exp_val": [{"hoge": test_ref.id}],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": test_ref.id}],
                "exp_val": [{"hoge": test_ref.id}],
            },
        ]
        test_ref.delete()
        for info in attr_info:
            attr = entry.attrs.get(name=info["name"])
            attr.add_value(user, info["set_val"])
            attrv = attr.get_latest_value()

            # test return value of get_value method with 'with_metainfo', 'is_active=False' parameter
            print(attrv.referral)
            expected_value = {"type": attr.schema.type, "value": info["exp_val"]}
            if attr.schema.type & AttrTypeValue["array"]:
                if attr.schema.type & AttrTypeValue["named"]:
                    expected_value["value"] = [{"hoge": {"id": test_ref.id}}]
                elif attr.schema.type & AttrTypeValue["object"]:
                    expected_value["value"] = [{"id": test_ref.id}]
            elif attr.schema.type & AttrTypeValue["named"]:
                expected_value["value"] = {"bar": {"id": test_ref.id}}
            elif attr.schema.type & AttrTypeValue["object"]:
                expected_value["value"] = {"id": test_ref.id}

            self.assertEqual(attrv.get_value(with_metainfo=True, is_active=False)["value"], expected_value["value"])

    def test_add_to_attrv(self):
        user = User.objects.create(username="hoge")
        entity_ref = Entity.objects.create(name="Ref", created_user=user)
        entity = self.create_entity_with_all_type_attributes(user, entity_ref)

        # create test groups but g2 is deleted
        test_groups = [Group.objects.create(name=x) for x in ["g0", "g1", "g2-deleted"]]
        test_groups[2].delete()

        # initialize test entry
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry_refs = [
            Entry.objects.create(name="ref-%d" % i, schema=entity_ref, created_user=user)
            for i in range(2)
        ]

        set_attrinfo = [
            {"name": "arr_str", "value": ["foo"]},
            {"name": "arr_obj", "value": [entry_refs[0]]},
            {"name": "arr_name", "value": [{"id": entry_refs[0], "name": "foo"}]},
            {"name": "arr_group", "value": [test_groups[0]]},
        ]
        attrs = {}
        for info in set_attrinfo:
            attr = attrs[info["name"]] = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["value"])

        # test added invalid values
        attrs["arr_str"].add_to_attrv(user, value="")
        self.assertEqual(
            [x.value for x in attrs["arr_str"].get_latest_value().data_array.all()],
            ["foo"],
        )
        attrs["arr_obj"].add_to_attrv(user, referral=None)
        self.assertEqual(
            [x.referral for x in attrs["arr_obj"].get_latest_value().data_array.all()],
            [ACLBase.objects.get(id=entry_refs[0].id)],
        )
        attrs["arr_name"].add_to_attrv(user, value="", referral=None)
        self.assertEqual(
            [
                (x.value, x.referral.name)
                for x in attrs["arr_name"].get_latest_value().data_array.all()
            ],
            [("foo", "ref-0")],
        )
        attrs["arr_group"].add_to_attrv(user, value=test_groups[2])
        self.assertEqual(
            [x.value for x in attrs["arr_group"].get_latest_value().data_array.all()],
            [str(test_groups[0].id)],
        )

        # test append attrv
        attrs["arr_str"].add_to_attrv(user, value="bar")
        attrv = attrs["arr_str"].get_latest_value()
        self.assertEqual(attrv.data_array.count(), 2)
        self.assertEqual(sorted([x.value for x in attrv.data_array.all()]), sorted(["foo", "bar"]))

        attrs["arr_obj"].add_to_attrv(user, referral=entry_refs[1])
        attrv = attrs["arr_obj"].get_latest_value()
        self.assertEqual(attrv.data_array.count(), 2)
        self.assertEqual(
            sorted([x.referral.name for x in attrv.data_array.all()]),
            sorted(["ref-0", "ref-1"]),
        )

        attrs["arr_name"].add_to_attrv(user, referral=entry_refs[1], value="baz", boolean=True)
        attrv = attrs["arr_name"].get_latest_value()
        self.assertEqual(attrv.data_array.count(), 2)
        self.assertEqual(sorted([x.value for x in attrv.data_array.all()]), sorted(["foo", "baz"]))
        self.assertEqual(
            sorted([x.referral.name for x in attrv.data_array.all()]),
            sorted(["ref-0", "ref-1"]),
        )
        self.assertEqual([x.boolean for x in attrv.data_array.filter(value="baz")], [True])

        attrs["arr_group"].add_to_attrv(user, value=test_groups[1])
        self.assertEqual(
            [x.value for x in attrs["arr_group"].get_latest_value().data_array.all()],
            [str(test_groups[0].id), str(test_groups[1].id)],
        )

    def test_remove_from_attrv(self):
        user = User.objects.create(username="hoge")
        entity_ref = Entity.objects.create(name="Ref", created_user=user)
        entity = self.create_entity_with_all_type_attributes(user, entity_ref)

        # create test groups but g1 is deleted
        test_groups = [Group.objects.create(name=x) for x in ["g0", "g1", "g2-deleted"]]

        # initialize test entry
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry_refs = [
            Entry.objects.create(name="ref-%d" % i, schema=entity_ref, created_user=user)
            for i in range(2)
        ]

        set_attrinfo = [
            {"name": "arr_str", "value": ["foo", "bar"]},
            {"name": "arr_obj", "value": entry_refs},
            {
                "name": "arr_name",
                "value": [
                    {"id": entry_refs[0], "name": "foo"},
                    {"id": entry_refs[1], "name": "bar"},
                ],
            },
            {"name": "arr_group", "value": test_groups},
        ]
        attrs = {}
        for info in set_attrinfo:
            attr = attrs[info["name"]] = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["value"])

        # remove group2 after registering
        test_groups[2].delete()

        # test remove_from_attrv with invalid value
        attrs["arr_str"].remove_from_attrv(user, value=None)
        attrv = attrs["arr_str"].get_latest_value()
        self.assertEqual(sorted([x.value for x in attrv.data_array.all()]), sorted(["foo", "bar"]))

        attrs["arr_obj"].remove_from_attrv(user, referral=None)
        attrv = attrs["arr_obj"].get_latest_value()
        self.assertEqual(
            sorted([x.referral.name for x in attrv.data_array.all()]),
            sorted(["ref-0", "ref-1"]),
        )

        attrs["arr_name"].remove_from_attrv(user, referral=None)
        attrv = attrs["arr_name"].get_latest_value()
        self.assertEqual(sorted([x.value for x in attrv.data_array.all()]), sorted(["foo", "bar"]))
        self.assertEqual(
            sorted([x.referral.name for x in attrv.data_array.all()]),
            sorted(["ref-0", "ref-1"]),
        )

        attrs["arr_group"].remove_from_attrv(user, value=None)
        self.assertEqual(
            [x.value for x in attrs["arr_group"].get_latest_value().data_array.all()],
            [str(x.id) for x in test_groups],
        )

        # test remove_from_attrv with valid value
        attrs["arr_str"].remove_from_attrv(user, value="foo")
        attrv = attrs["arr_str"].get_latest_value()
        self.assertEqual(sorted([x.value for x in attrv.data_array.all()]), sorted(["bar"]))

        attrs["arr_obj"].remove_from_attrv(user, referral=entry_refs[0])
        attrv = attrs["arr_obj"].get_latest_value()
        self.assertEqual(
            sorted([x.referral.name for x in attrv.data_array.all()]), sorted(["ref-1"])
        )

        attrs["arr_name"].remove_from_attrv(user, referral=entry_refs[0])
        attrv = attrs["arr_name"].get_latest_value()
        self.assertEqual(sorted([x.value for x in attrv.data_array.all()]), sorted(["bar"]))
        self.assertEqual(
            sorted([x.referral.name for x in attrv.data_array.all()]), sorted(["ref-1"])
        )

        # This checks that both specified group and invalid groups are removed
        attrs["arr_group"].remove_from_attrv(user, value=test_groups[1])
        self.assertEqual(
            [x.value for x in attrs["arr_group"].get_latest_value().data_array.all()],
            [str(test_groups[0].id)],
        )

    def test_is_importable_data(self):
        check_data = [
            {"expect": False, "data": ["foo", "bar"]},
            {"expect": False, "data": "foo"},
            {"expect": False, "data": {"Entity": "hoge"}},
            {"expect": False, "data": {"Entity": ["hoge"]}},
            {"expect": False, "data": {"Entity": [{"attrs": {}}]}},
            {"expect": False, "data": {"Entity": [{"name": "entry"}]}},
            {
                "expect": False,
                "data": {"Entity": [{"attrs": {"foo": "bar"}, "name": 1234}]},
            },
            {
                "expect": False,
                "data": {"Entity": [{"attrs": ["foo", "bar"], "name": "entry"}]},
            },
            {
                "expect": True,
                "data": {"Entity": [{"attrs": {"foo": "bar"}, "name": "entry"}]},
            },
        ]
        for info in check_data:
            ret = Entry.is_importable_data(info["data"])

            self.assertEqual(ret, info["expect"])

    def test_remove_duplicate_attr(self):
        # initialize EntityAttr and Entry objects to test
        entity_attr = EntityAttr.objects.create(
            **{
                "name": "attr",
                "type": AttrTypeValue["object"],
                "created_user": self._user,
                "parent_entity": self._entity,
            }
        )
        self._entity.attrs.add(entity_attr)

        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=self._user)
        entry.complement_attrs(self._user)

        # Add and register duplicate Attribute after registers
        dup_attr = Attribute.objects.create(
            name=entity_attr.name,
            schema=entity_attr,
            created_user=self._user,
            parent_entry=entry,
        )
        entry.attrs.add(dup_attr)

        # checks duplicate attr is registered as expected
        self.assertEqual(entry.attrs.count(), 2)
        self.assertTrue(entry.attrs.filter(id=dup_attr.id).exists())

        # remove duplicate attribute
        entry.may_remove_duplicate_attr(dup_attr)

        # checks duplicate attr would be removed
        self.assertEqual(entry.attrs.count(), 1)
        self.assertNotEqual(entry.attrs.first().id, dup_attr)
        self.assertFalse(dup_attr.is_active)

        # checks original attr would never be removed by same method
        orig_attr = entry.attrs.first()
        entry.may_remove_duplicate_attr(orig_attr)
        self.assertEqual(entry.attrs.count(), 1)
        self.assertEqual(entry.attrs.first(), orig_attr)

    def test_restore_entry(self):
        entity = self.create_entity_with_all_type_attributes(self._user)
        ref_entry = Entry.objects.create(name="ref_entry", schema=entity, created_user=self._user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=self._user)
        entry.complement_attrs(self._user)

        attr = entry.attrs.get(schema__name="obj")
        attr.add_value(self._user, ref_entry)

        ref_entry.delete()
        ref_entry.restore()

        ref_entry.refresh_from_db()
        self.assertTrue(ref_entry.is_active)
        self.assertEqual(ref_entry.name, "ref_entry")
        self.assertTrue(all([attr.is_active for attr in ref_entry.attrs.all()]))

        ret = Entry.search_entries(self._user, [entity.id], [{"name": "obj"}])
        self.assertEqual(ret["ret_values"][0]["entry"]["name"], "entry")
        self.assertEqual(ret["ret_values"][0]["attrs"]["obj"]["value"]["name"], "ref_entry")
        self.assertEqual(ret["ret_values"][1]["entry"]["name"], "ref_entry")

    def test_restore_entry_in_chain(self):
        # initilaize referral Entries for checking processing caused
        # by setting 'is_delete_in_chain' flag
        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=self._user)
        ref_entries = [
            Entry.objects.create(name="ref-%d" % i, created_user=self._user, schema=ref_entity)
            for i in range(3)
        ]

        # initialize EntityAttrs
        attr_info = {
            "obj": {"type": AttrTypeValue["object"], "value": ref_entries[0]},
            "arr_obj": {
                "type": AttrTypeValue["array_object"],
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

            if info["type"] & AttrTypeValue["object"]:
                attr.referral.add(ref_entity)

            self._entity.attrs.add(attr)

        # initialize target entry
        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=self._user)
        entry.complement_attrs(self._user)

        for attr_name, info in attr_info.items():
            attr = entry.attrs.get(schema__name=attr_name)
            attr.add_value(self._user, info["value"])

        # delete target entry at first
        entry.delete()

        self.assertFalse(entry.is_active)
        self.assertTrue(entry.name.find("_deleted_") > 0)
        self.assertFalse(any([Entry.objects.get(id=x.id).is_active for x in ref_entries]))

        # restore target entry
        entry.restore()

        self.assertTrue(entry.is_active)
        self.assertEqual(entry.name.find("_deleted_"), -1)
        self.assertTrue(all([Entry.objects.get(id=x.id).is_active for x in ref_entries]))

    def test_to_dict_entry(self):
        user = User.objects.create(username="hoge")
        test_group = Group.objects.create(name="test-group")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)

        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        for info in self._get_attrinfo_template(ref_entry, test_group):
            attr = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["set_val"])

        # This checks all attribute values which are generated by entry.to_dict method
        ret_dict = entry.to_dict(user)
        expected_attrinfos = [
            {"name": "str", "value": "foo"},
            {"name": "text", "value": "bar"},
            {"name": "bool", "value": False},
            {"name": "arr_str", "value": ["foo", "bar", "baz"]},
            {"name": "date", "value": "2018-12-31"},
            {"name": "obj", "value": "r0"},
            {"name": "name", "value": {"bar": "r0"}},
            {"name": "arr_obj", "value": ["r0"]},
            {"name": "arr_name", "value": [{"hoge": "r0"}]},
            {"name": "group", "value": "test-group"},
            {"name": "arr_group", "value": ["test-group"]},
        ]
        for info in expected_attrinfos:
            self.assertEqual(
                [x["value"] for x in ret_dict["attrs"] if x["name"] == info["name"]],
                [info["value"]],
            )

    def test_to_dict_entry_with_metainfo_param(self):
        user = User.objects.create(username="hoge")
        test_group = Group.objects.create(name="test-group")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)

        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        for info in self._get_attrinfo_template(ref_entry, test_group):
            attr = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["set_val"])

        # This checks all attribute values which are generated by entry.to_dict method
        ret_dict = entry.to_dict(user, with_metainfo=True)
        expected_attrinfos = [
            {"name": "str", "value": {"type": AttrTypeValue["string"], "value": "foo"}},
            {"name": "text", "value": {"type": AttrTypeValue["text"], "value": "bar"}},
            {
                "name": "bool",
                "value": {"type": AttrTypeValue["boolean"], "value": False},
            },
            {
                "name": "date",
                "value": {"type": AttrTypeValue["date"], "value": "2018-12-31"},
            },
            {
                "name": "arr_str",
                "value": {
                    "type": AttrTypeValue["array_string"],
                    "value": ["foo", "bar", "baz"],
                },
            },
            {
                "name": "obj",
                "value": {
                    "type": AttrTypeValue["object"],
                    "value": {"id": ref_entry.id, "name": ref_entry.name},
                },
            },
            {
                "name": "name",
                "value": {
                    "type": AttrTypeValue["named_object"],
                    "value": {"bar": {"id": ref_entry.id, "name": ref_entry.name}},
                },
            },
            {
                "name": "arr_obj",
                "value": {
                    "type": AttrTypeValue["array_object"],
                    "value": [{"id": ref_entry.id, "name": ref_entry.name}],
                },
            },
            {
                "name": "arr_name",
                "value": {
                    "type": AttrTypeValue["array_named_object"],
                    "value": [{"hoge": {"id": ref_entry.id, "name": ref_entry.name}}],
                },
            },
            {
                "name": "group",
                "value": {
                    "type": AttrTypeValue["group"],
                    "value": {"id": test_group.id, "name": test_group.name},
                },
            },
            {
                "name": "arr_group",
                "value": {
                    "type": AttrTypeValue["array_group"],
                    "value": [{"id": test_group.id, "name": test_group.name}],
                },
            },
        ]
        for info in expected_attrinfos:
            self.assertEqual(
                [x["value"] for x in ret_dict["attrs"] if x["name"] == info["name"]],
                [info["value"]],
            )

    def test_to_dict_entry_for_checking_permission(self):
        admin_user = User.objects.create(username="admin", is_superuser=True)

        private_entity = Entity.objects.create(
            name="private_entity", created_user=admin_user, is_public=False
        )
        public_entity = Entity.objects.create(name="public_entity", created_user=admin_user)

        attr_info = [
            {"name": "attr1", "is_public": True},
            {"name": "attr2", "is_public": False},
        ]
        for info in attr_info:
            [
                e.attrs.add(
                    EntityAttr.objects.create(
                        **{
                            "type": AttrTypeValue["string"],
                            "created_user": self._user,
                            "parent_entity": self._entity,
                            "name": info["name"],
                            "is_public": info["is_public"],
                        }
                    )
                )
                for e in [private_entity, public_entity]
            ]

        # Initialize three kind of entries as below
        entry_info = [
            {"name": "e1", "schema": private_entity, "is_public": True},
            {"name": "e2", "schema": public_entity, "is_public": False},
            {"name": "e3", "schema": public_entity, "is_public": True},
        ]
        entries = [Entry.objects.create(created_user=admin_user, **info) for info in entry_info]
        for entry in entries:
            entry.complement_attrs(admin_user)

            for attr in entry.attrs.all():
                attr.add_value(admin_user, "hoge")

        # Test to_dict method of Entry
        self.assertIsNone(entries[0].to_dict(self._user))
        self.assertIsNone(entries[1].to_dict(self._user))
        self.assertEqual(
            entries[2].to_dict(self._user),
            {
                "id": entries[2].id,
                "name": entries[2].name,
                "entity": {"id": public_entity.id, "name": public_entity.name},
                "attrs": [
                    {"name": "attr1", "value": "hoge"},
                ],
            },
        )

    def test_search_entries_blank_val(self):
        user = User.objects.create(username="hoge")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(
            name="referred_entry", schema=ref_entity, created_user=user
        )
        ref_group = Group.objects.create(name="group")

        attr_info = {
            "str": {"type": AttrTypeValue["string"], "value": "foo-%d"},
            "str2": {"type": AttrTypeValue["string"], "value": "foo-%d"},
            "obj": {"type": AttrTypeValue["object"], "value": str(ref_entry.id)},
            "name": {
                "type": AttrTypeValue["named_object"],
                "value": {"name": "bar", "id": str(ref_entry.id)},
            },
            "bool": {"type": AttrTypeValue["boolean"], "value": False},
            "group": {"type": AttrTypeValue["group"], "value": str(ref_group.id)},
            "date": {"type": AttrTypeValue["date"], "value": date(2018, 12, 31)},
            "arr_str": {
                "type": AttrTypeValue["array_string"],
                "value": ["foo", "bar", "baz"],
            },
            "arr_obj": {
                "type": AttrTypeValue["array_object"],
                "value": [str(x.id) for x in Entry.objects.filter(schema=ref_entity)],
            },
            "arr_name": {
                "type": AttrTypeValue["array_named_object"],
                "value": [{"name": "hoge", "id": str(ref_entry.id)}],
            },
        }

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )

            if info["type"] & AttrTypeValue["object"]:
                attr.referral.add(ref_entity)

            entity.attrs.add(attr)

        for index in range(0, 11):
            entry = Entry.objects.create(name="e-%d" % index, schema=entity, created_user=user)
            entry.complement_attrs(user)

            for attr_name, info in attr_info.items():
                attr = entry.attrs.get(name=attr_name)
                if attr_name == "str":
                    attr.add_value(user, info["value"] % index)
                elif attr_name == "str2":
                    attr.add_value(user, info["value"] % (index + 100))
                else:
                    attr.add_value(user, info["value"])

            entry.register_es()

        # search entries with blank values
        entry = Entry.objects.create(name="", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.register_es()

        ref_entry = Entry.objects.create(
            name=CONFIG.EMPTY_SEARCH_CHARACTER, schema=ref_entity, created_user=user
        )
        ref_group = Group.objects.create(name=CONFIG.EMPTY_SEARCH_CHARACTER)

        # search entries with blank values
        entry = Entry.objects.create(
            name=CONFIG.EMPTY_SEARCH_CHARACTER, schema=entity, created_user=user
        )
        entry.complement_attrs(user)

        # search entries with back slash
        attr_info = {
            "str": {
                "type": AttrTypeValue["string"],
                "value": CONFIG.EMPTY_SEARCH_CHARACTER,
            },
            "str2": {
                "type": AttrTypeValue["string"],
                "value": CONFIG.EMPTY_SEARCH_CHARACTER,
            },
            "obj": {"type": AttrTypeValue["object"], "value": str(ref_entry.id)},
            "name": {
                "type": AttrTypeValue["named_object"],
                "value": {"name": "bar", "id": str(ref_entry.id)},
            },
            "bool": {"type": AttrTypeValue["boolean"], "value": False},
            "group": {"type": AttrTypeValue["group"], "value": str(ref_group.id)},
            "date": {"type": AttrTypeValue["date"], "value": date(2018, 12, 31)},
            "arr_str": {
                "type": AttrTypeValue["array_string"],
                "value": [CONFIG.EMPTY_SEARCH_CHARACTER],
            },
            "arr_obj": {
                "type": AttrTypeValue["array_object"],
                "value": [str(x.id) for x in Entry.objects.filter(schema=ref_entity)],
            },
            "arr_name": {
                "type": AttrTypeValue["array_named_object"],
                "value": [{"name": "hoge", "id": str(ref_entry.id)}],
            },
        }

        for attr_name, info in attr_info.items():
            attr = entry.attrs.get(name=attr_name)
            attr.add_value(user, info["value"])

        entry.register_es()

        # search entries with empty_search_character
        for attr_name, info in attr_info.items():
            ret = Entry.search_entries(
                user,
                [entity.id],
                [{"name": attr_name, "keyword": CONFIG.EMPTY_SEARCH_CHARACTER}],
            )
            if attr_name != "bool":
                self.assertEqual(ret["ret_count"], 1)
            else:
                self.assertEqual(ret["ret_count"], 0)

        # search entries with double_empty_search_character
        double_empty_search_character = (
            CONFIG.EMPTY_SEARCH_CHARACTER + CONFIG.EMPTY_SEARCH_CHARACTER
        )

        for attr_name, info in attr_info.items():
            ret = Entry.search_entries(
                user,
                [entity.id],
                [{"name": attr_name, "keyword": double_empty_search_character}],
            )
            self.assertEqual(ret["ret_count"], 0)

        # check functionallity of the 'entry_name' parameter
        ret = Entry.search_entries(user, [entity.id], entry_name=CONFIG.EMPTY_SEARCH_CHARACTER)
        self.assertEqual(ret["ret_count"], 1)

        ret = Entry.search_entries(user, [entity.id], entry_name=double_empty_search_character)
        self.assertEqual(ret["ret_count"], 0)

        # check combination of 'entry_name' and 'hint_attrs' parameter
        ret = Entry.search_entries(
            user,
            [entity.id],
            [{"name": "str", "keyword": CONFIG.EMPTY_SEARCH_CHARACTER}],
            entry_name=CONFIG.EMPTY_SEARCH_CHARACTER,
        )
        self.assertEqual(ret["ret_count"], 1)

    def test_cache_of_adding_attribute(self):
        """
        This test suite confirms that the creating cache not to remaining after
        creating Attribute instance. This indicates cache operation in the method
        of add_attribute_from_base has atomicity. It means cache value would not
        be set before and after calling this method that set cache value.
        """
        # initialize Entity an Entry
        user = User.objects.create(username="hoge")
        entity = Entity.objects.create(name="entity", created_user=user)
        attrbase = EntityAttr.objects.create(
            name="attr", type=AttrTypeValue["object"], created_user=user, parent_entity=entity
        )
        entity.attrs.add(attrbase)

        # call add_attribute_from_base method more than once
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        for _i in range(2):
            entry.add_attribute_from_base(attrbase, user)

        self.assertIsNone(entry.get_cache("add_%d" % attrbase.id))

    def test_may_append_attr(self):
        # initialize Entity an Entry
        entity = Entity.objects.create(name="entity", created_user=self._user)
        entry1 = Entry.objects.create(name="entry1", created_user=self._user, schema=entity)
        entry2 = Entry.objects.create(name="entry2", created_user=self._user, schema=entity)

        attr = self.make_attr("attr", attrtype=AttrTypeArrStr, entity=entity, entry=entry1)

        # Just after creating entries, there is no attribute in attrs member
        self.assertEqual(entry1.attrs.count(), 0)
        self.assertEqual(entry2.attrs.count(), 0)

        for entry in [entry1, entry2]:
            entry.may_append_attr(attr)

        # Attribute object should be set to appropriate entry's attrs member
        self.assertEqual(entry1.attrs.first(), attr)
        self.assertEqual(entry2.attrs.count(), 0)

    def test_search_entries_includes_and_or(self):
        user = User.objects.create(username="hoge")

        attr_info = []
        """
        testdata1 str1:foo str2:blank str3:blank arr_str:['hoge']
        testdata2 str1:foo str2:bar str3:blank arr_str:['hoge', 'fuga']
        testdata3 str1:foo str2:bar str3:baz arr_str:['hoge', 'fuga', 'piyo']
        """
        attr_info.append(
            {
                "str1": {"type": AttrTypeValue["string"], "value": "foo"},
                "str2": {"type": AttrTypeValue["string"], "value": ""},
                "str3": {"type": AttrTypeValue["string"], "value": ""},
                "arr_str": {"type": AttrTypeValue["array_string"], "value": ["hoge"]},
            }
        )
        attr_info.append(
            {
                "str1": {"type": AttrTypeValue["string"], "value": "foo"},
                "str2": {"type": AttrTypeValue["string"], "value": "bar"},
                "str3": {"type": AttrTypeValue["string"], "value": ""},
                "arr_str": {
                    "type": AttrTypeValue["array_string"],
                    "value": ["hoge", "fuga"],
                },
            }
        )
        attr_info.append(
            {
                "str1": {"type": AttrTypeValue["string"], "value": "foo"},
                "str2": {"type": AttrTypeValue["string"], "value": "bar"},
                "str3": {"type": AttrTypeValue["string"], "value": "baz"},
                "arr_str": {
                    "type": AttrTypeValue["array_string"],
                    "value": ["hoge", "fuga", "piyo"],
                },
            }
        )

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name, info in attr_info[0].items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )
            entity.attrs.add(attr)

        for i, x in enumerate(attr_info):
            entry = Entry.objects.create(name="e-%s" % i, schema=entity, created_user=user)
            entry.complement_attrs(user)

            for attr_name, info in x.items():

                attr = entry.attrs.get(name=attr_name)
                attr.add_value(user, info["value"])

            entry.register_es()

        """
        Test case that contains only 'and'
        """
        test_suites = []
        test_suites.append(
            [
                {"ret_cnt": 3, "search_word": [{"name": "str1", "keyword": "foo"}]},
                {
                    "ret_cnt": 0,
                    "search_word": [
                        {"name": "str1", "keyword": "foo&bar"},
                        {"name": "str2", "keyword": "foo&bar"},
                    ],
                },
                {
                    "ret_cnt": 0,
                    "search_word": [
                        {"name": "str1", "keyword": "foo&bar&baz"},
                        {"name": "str2", "keyword": "foo&bar&baz"},
                        {"name": "str3", "keyword": "foo&bar&baz"},
                    ],
                },
                {
                    "ret_cnt": 3,
                    "search_word": [{"name": "arr_str", "keyword": "hoge"}],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [{"name": "arr_str", "keyword": "hoge&fuga"}],
                },
                {
                    "ret_cnt": 1,
                    "search_word": [{"name": "arr_str", "keyword": "hoge&fuga&piyo"}],
                },
                {
                    "ret_cnt": 3,
                    "search_word": [
                        {"name": "str1", "keyword": "foo"},
                        {"name": "arr_str", "keyword": "hoge"},
                    ],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [
                        {"name": "str1", "keyword": "foo"},
                        {"name": "str2", "keyword": "bar"},
                        {"name": "arr_str", "keyword": "hoge&fuga"},
                    ],
                },
                {
                    "ret_cnt": 1,
                    "search_word": [
                        {"name": "str1", "keyword": "foo"},
                        {"name": "str2", "keyword": "bar"},
                        {"name": "arr_str", "keyword": "hoge&fuga&piyo"},
                    ],
                },
            ]
        )

        """
        Test case that contains only 'or'
        """
        test_suites.append(
            [
                {"ret_cnt": 3, "search_word": [{"name": "str1", "keyword": "foo|bar"}]},
                {
                    "ret_cnt": 1,
                    "search_word": [
                        {"name": "str2", "keyword": "bar|baz"},
                        {"name": "str3", "keyword": "bar|baz"},
                    ],
                },
                {
                    "ret_cnt": 1,
                    "search_word": [
                        {"name": "str1", "keyword": "foo|bar|baz"},
                        {"name": "str2", "keyword": "foo|bar|baz"},
                        {"name": "str3", "keyword": "foo|bar|baz"},
                    ],
                },
                {
                    "ret_cnt": 3,
                    "search_word": [{"name": "arr_str", "keyword": "hoge|fuga"}],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [{"name": "arr_str", "keyword": "fuga|piyo"}],
                },
                {
                    "ret_cnt": 3,
                    "search_word": [{"name": "arr_str", "keyword": "hoge|fuga|piyo"}],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [
                        {"name": "str2", "keyword": "foo|bar"},
                        {"name": "arr_str", "keyword": "hoge"},
                    ],
                },
                {
                    "ret_cnt": 1,
                    "search_word": [
                        {"name": "str2", "keyword": "foo|bar"},
                        {"name": "str3", "keyword": "bar|baz"},
                        {"name": "arr_str", "keyword": "hoge|fuga"},
                    ],
                },
                {
                    "ret_cnt": 1,
                    "search_word": [
                        {"name": "str3", "keyword": "foo|baz"},
                        {"name": "arr_str", "keyword": "hoge|fuga|piyo"},
                    ],
                },
            ]
        )

        """
        Test cases that contain 'and' and 'or'
        """
        test_suites.append(
            [
                {"ret_cnt": 3, "search_word": [{"name": "str1", "keyword": "foo|bar"}]},
                {
                    "ret_cnt": 0,
                    "search_word": [
                        {"name": "str1", "keyword": "foo&baz|bar"},
                        {"name": "str2", "keyword": "foo&baz|bar"},
                        {"name": "str3", "keyword": "foo&baz|bar"},
                    ],
                },
                {
                    "ret_cnt": 0,
                    "search_word": [
                        {"name": "str1", "keyword": "foo|bar&baz"},
                        {"name": "str2", "keyword": "foo|bar&baz"},
                        {"name": "str3", "keyword": "foo|bar&baz"},
                    ],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [{"name": "arr_str", "keyword": "hoge&piyo|fuga"}],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [{"name": "arr_str", "keyword": "piyo|hoge&fuga"}],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [
                        {"name": "str1", "keyword": "foo"},
                        {"name": "str2", "keyword": "bar|baz"},
                        {"name": "arr_str", "keyword": "hoge&piyo|fuga"},
                    ],
                },
            ]
        )

        for x in test_suites:
            for test_suite in x:
                ret = Entry.search_entries(user, [entity.id], test_suite["search_word"])
                self.assertEqual(ret["ret_count"], test_suite["ret_cnt"])

    def test_search_entries_entry_name(self):
        user = User.objects.create(username="hoge")
        entity = Entity.objects.create(name="entity", created_user=user)

        """
        testdata1 entry_name:'foo'
        testdata2 entry_name:'bar'
        testdata3 entry_name:'barbaz'
        """
        for entry_name in ["foo", "bar", "barbaz"]:
            entry = Entry.objects.create(name=entry_name, schema=entity, created_user=user)
            entry.register_es()

        search_words = {"foo": 1, "bar&baz": 1, "foo|bar": 3, "foo|bar&baz": 2}
        for word, count in search_words.items():
            ret = Entry.search_entries(user, [entity.id], entry_name=word)
            self.assertEqual(ret["ret_count"], count)

    def test_search_entries_get_regex_pattern(self):
        user = User.objects.create(username="hoge")
        entity = Entity.objects.create(name="entity", created_user=user)

        add_chars = [
            "!",
            '"',
            "#",
            "$",
            "%",
            "'",
            "(",
            ")",
            "-",
            "=",
            "^",
            "~",
            "@",
            "`",
            "[",
            "]",
            "{",
            "}",
            ";",
            "+",
            ":",
            "*",
            ",",
            "<",
            ">",
            ".",
            "/",
            "?",
            "_",
            " ",
        ]
        test_suites = []
        for i, add_char in enumerate(add_chars):
            entry_name = "test%s%s" % (add_char, i)
            entry = Entry.objects.create(name=entry_name, schema=entity, created_user=user)
            entry.register_es()

            test_suites.append(
                {"search_word": entry_name, "ret_cnt": 1, "ret_entry_name": entry_name}
            )

        for test_suite in test_suites:
            ret = Entry.search_entries(user, [entity.id], entry_name=test_suite["search_word"])
            self.assertEqual(ret["ret_count"], test_suite["ret_cnt"])
            self.assertEqual(ret["ret_values"][0]["entry"]["name"], test_suite["ret_entry_name"])

    def test_search_entries_with_is_output_all(self):
        self._entity.attrs.add(self._attr.schema)
        self._entry.attrs.add(self._attr)
        self._entry.attrs.first().add_value(self._user, "hoge")
        self._entry.register_es()
        ret = Entry.search_entries(self._user, [self._entity.id], is_output_all=True)
        self.assertEqual(
            ret["ret_values"][0]["attrs"],
            {"attr": {"value": "hoge", "is_readble": True, "type": 2}},
        )

        ret = Entry.search_entries(
            self._user,
            [self._entity.id],
            [{"name": "attr", "keyword": "^ge"}],
            is_output_all=True,
        )
        self.assertEqual(ret["ret_count"], 0)

    def test_search_entries_for_simple(self):
        self._entity.attrs.add(self._attr.schema)
        self._entry.attrs.add(self._attr)
        self._entry.attrs.first().add_value(self._user, "hoge")
        self._entry.register_es()

        # search by Entry name
        ret = Entry.search_entries_for_simple("entry")
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual(
            ret["ret_values"][0],
            {
                "id": str(self._entry.id),
                "name": self._entry.name,
                "schema": {"id": self._entry.schema.id, "name": self._entry.schema.name},
            },
        )

        # search by AttributeValue
        ret = Entry.search_entries_for_simple("hoge")
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual(
            ret["ret_values"][0],
            {
                "id": str(self._entry.id),
                "name": self._entry.name,
                "schema": {"id": self._entry.schema.id, "name": self._entry.schema.name},
                "attr": self._attr.schema.name,
            },
        )

    def test_search_entries_for_simple_with_hint_entity_name(self):
        self._entry.register_es()
        entity = Entity.objects.create(name="entity2", created_user=self._user)
        entry = Entry.objects.create(name="entry2", schema=entity, created_user=self._user)
        entry.register_es()

        ret = Entry.search_entries_for_simple("entry")
        self.assertEqual(ret["ret_count"], 2)
        self.assertEqual([x["name"] for x in ret["ret_values"]], ["entry", "entry2"])

        ret = Entry.search_entries_for_simple("entry", "entity")
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual([x["name"] for x in ret["ret_values"]], ["entry"])

    def test_search_entries_for_simple_with_exclude_entity_names(self):
        self._entry.register_es()
        entity = Entity.objects.create(name="entity2", created_user=self._user)
        entry = Entry.objects.create(name="entry2", schema=entity, created_user=self._user)
        entry.register_es()

        ret = Entry.search_entries_for_simple("entry")
        self.assertEqual(ret["ret_count"], 2)
        self.assertEqual([x["name"] for x in ret["ret_values"]], ["entry", "entry2"])

        ret = Entry.search_entries_for_simple("entry", exclude_entity_names=["entity"])
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual([x["name"] for x in ret["ret_values"]], ["entry2"])

    def test_search_entries_for_simple_with_limit_offset(self):
        for i in range(0, 10):
            entry = Entry.objects.create(
                name="e-%s" % i, schema=self._entity, created_user=self._user
            )
            entry.register_es()

        ret = Entry.search_entries_for_simple("e-", limit=5)
        self.assertEqual(ret["ret_count"], 10)
        self.assertEqual([x["name"] for x in ret["ret_values"]], ["e-%s" % x for x in range(0, 5)])

        ret = Entry.search_entries_for_simple("e-", offset=5)
        self.assertEqual(ret["ret_count"], 10)
        self.assertEqual([x["name"] for x in ret["ret_values"]], ["e-%s" % x for x in range(5, 10)])

        # param larger than max_result_window
        ret = Entry.search_entries_for_simple("e-", limit=500001)
        self.assertEqual(ret["ret_count"], 0)
        self.assertEqual(ret["ret_values"], [])

        ret = Entry.search_entries_for_simple("e-", offset=500001)
        self.assertEqual(ret["ret_count"], 0)
        self.assertEqual(ret["ret_values"], [])

    def test_get_es_document(self):
        user = User.objects.create(username="hoge")
        test_group = Group.objects.create(name="test-group")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)

        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        for info in self._get_attrinfo_template(ref_entry, test_group):
            attr = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["set_val"])

        es_registering_value = entry.get_es_document()

        # this test value that will be registered in elasticsearch
        expected_values = {
            "str": {"key": [""], "value": ["foo"], "referral_id": [""]},
            "obj": {
                "key": [""],
                "value": [ref_entry.name],
                "referral_id": [ref_entry.id],
            },
            "text": {"key": [""], "value": ["bar"], "referral_id": [""]},
            "name": {
                "key": ["bar"],
                "value": [ref_entry.name],
                "referral_id": [ref_entry.id],
            },
            "bool": {"key": [""], "value": ["False"], "referral_id": [""]},
            "group": {
                "key": [""],
                "value": [test_group.name],
                "referral_id": [test_group.id],
            },
            "date": {
                "key": [""],
                "value": [""],
                "referral_id": [""],
                "date_value": [date(2018, 12, 31)],
            },
            "arr_str": {
                "key": ["", "", ""],
                "value": ["foo", "bar", "baz"],
                "referral_id": ["", "", ""],
            },
            "arr_obj": {
                "key": [""],
                "value": [ref_entry.name],
                "referral_id": [ref_entry.id],
            },
            "arr_name": {
                "key": ["hoge"],
                "value": [ref_entry.name],
                "referral_id": [ref_entry.id],
            },
            "arr_group": {
                "key": [""],
                "value": [test_group.name],
                "referral_id": [test_group.id],
            },
        }
        # check all attributes are expected ones
        self.assertEqual(
            set([x["name"] for x in es_registering_value["attr"]]),
            set(expected_values.keys()),
        )

        # check all attribute contexts are expected ones
        for attrname, attrinfo in expected_values.items():
            attr = entry.attrs.get(schema__name=attrname)
            set_attrs = [x for x in es_registering_value["attr"] if x["name"] == attrname]

            self.assertTrue(all([x["type"] == attr.schema.type for x in set_attrs]))
            self.assertTrue(all([x["is_readble"] is True for x in set_attrs]))
            for param_name in ["key", "value", "referral_id", "date_value"]:
                if param_name in attrinfo:
                    self.assertEqual(
                        sorted([x[param_name] for x in set_attrs]),
                        sorted(attrinfo[param_name]),
                    )

    def test_get_es_document_without_attribute_value(self):
        entity = self.create_entity_with_all_type_attributes(self._user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=self._user)

        entry.register_es()
        result = Entry.search_entries(
            self._user, [entity.id], entry_name="entry", is_output_all=True
        )
        self.assertEqual(
            result["ret_values"][0],
            {
                "entity": {"id": entity.id, "name": "entity"},
                "entry": {"id": entry.id, "name": "entry"},
                "is_readble": True,
                "attrs": {
                    "bool": {"is_readble": True, "type": AttrTypeValue["boolean"], "value": ""},
                    "date": {
                        "is_readble": True,
                        "type": AttrTypeValue["date"],
                        "value": None,
                    },
                    "group": {
                        "is_readble": True,
                        "type": AttrTypeValue["group"],
                        "value": {"id": "", "name": ""},
                    },
                    "name": {"is_readble": True, "type": AttrTypeValue["named_object"]},
                    "obj": {
                        "is_readble": True,
                        "type": AttrTypeValue["object"],
                        "value": {"id": "", "name": ""},
                    },
                    "str": {"is_readble": True, "type": AttrTypeValue["string"]},
                    "text": {"is_readble": True, "type": AttrTypeValue["text"]},
                },
            },
        )

        # If the AttributeValue does not exist, permission returns the default
        self._entity.attrs.add(self._attr.schema)
        self._entry.attrs.add(self._attr)

        result = self._entry.get_es_document()
        self.assertEqual(
            result["attr"],
            [
                {
                    "name": self._attr.name,
                    "type": self._attr.schema.type,
                    "key": "",
                    "value": "",
                    "date_value": None,
                    "referral_id": "",
                    "is_readble": True,
                }
            ],
        )

    def test_get_es_document_when_referred_entry_was_deleted(self):
        # This entry refers self._entry which will be deleted later
        ref_entity = Entity.objects.create(name="", created_user=self._user)
        ref_attr = EntityAttr.objects.create(
            **{
                "name": "ref",
                "type": AttrTypeValue["object"],
                "created_user": self._user,
                "parent_entity": ref_entity,
            }
        )
        ref_attr.referral.add(self._entity)
        ref_entity.attrs.add(ref_attr)

        ref_entry = Entry.objects.create(name="ref", schema=ref_entity, created_user=self._user)
        ref_entry.complement_attrs(self._user)

        ref_entry.attrs.first().add_value(self._user, self._entry)

        result = ref_entry.get_es_document()
        self.assertEqual(result["name"], ref_entry.name)
        self.assertEqual(
            result["attr"],
            [
                {
                    "name": ref_attr.name,
                    "type": ref_attr.type,
                    "key": "",
                    "value": self._entry.name,
                    "date_value": None,
                    "referral_id": self._entry.id,
                    "is_readble": True,
                }
            ],
        )

        # Delete an entry which is referred by ref_entry
        self._entry.delete()

        # Check result of query of ref_entry after referring entry is deleted.
        result = ref_entry.get_es_document()
        self.assertEqual(result["name"], ref_entry.name)
        self.assertEqual(
            result["attr"],
            [
                {
                    "name": ref_attr.name,
                    "type": ref_attr.type,
                    "key": "",
                    "value": "",  # expected not to have information about deleted entry
                    "date_value": None,
                    "referral_id": "",  # expected not to have information about deleted entry
                    "is_readble": True,
                }
            ],
        )

    def test_get_attrv_method_of_entry(self):
        # prepare Entry and Attribute for testing Entry.get_attrv method
        user = User.objects.create(username="hoge")
        entity = Entity.objects.create(name="entity", created_user=user)

        for attrname in ["attr", "attr-deleted"]:
            entity.attrs.add(
                EntityAttr.objects.create(
                    name=attrname,
                    type=AttrTypeValue["string"],
                    created_user=user,
                    parent_entity=entity,
                )
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
            type=AttrTypeValue["string"],
            created_user=user1,
            parent_entity=entity,
            is_public=False,
        )

        # set permission for test Role instance
        role.permissions.add(entity_attr.full)

        entity.attrs.add(entity_attr)

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
        for type in ["string", "text"]:
            self.assertEqual(
                AttributeValue.validate_attr_value(AttrTypeValue[type], "hoge", False), (True, None)
            )
            self.assertEqual(
                AttributeValue.validate_attr_value(AttrTypeValue[type], "", False), (True, None)
            )
            self.assertEqual(
                AttributeValue.validate_attr_value(AttrTypeValue[type], ["hoge"], False),
                (False, "value(['hoge']) is not str"),
            )
            self.assertEqual(
                AttributeValue.validate_attr_value(
                    AttrTypeValue[type], "a" * AttributeValue.MAXIMUM_VALUE_SIZE, False
                ),
                (True, None),
            )
            self.assertEqual(
                AttributeValue.validate_attr_value(
                    AttrTypeValue[type], "a" * (AttributeValue.MAXIMUM_VALUE_SIZE + 1), False
                ),
                (
                    False,
                    "value(%s) is exceeded the limit"
                    % ("a" * (AttributeValue.MAXIMUM_VALUE_SIZE + 1)),
                ),
            )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["object"], self._entry.id, False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["object"], None, False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["object"], "", False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["object"], "hoge", False),
            (False, "value(hoge) is not int"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["object"], 9999, False),
            (False, "value(9999) is not entry id"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "hoge", "id": self._entry.id}, False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "", "id": self._entry.id}, False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "hoge", "id": ""}, False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "hoge", "id": None}, False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "", "id": ""}, False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "", "id": None}, False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": ["hoge"], "id": self._entry.id}, False
            ),
            (False, "value(['hoge']) is not str"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"],
                {"name": "a" * AttributeValue.MAXIMUM_VALUE_SIZE, "id": self._entry.id},
                False,
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"],
                {"name": "a" * (AttributeValue.MAXIMUM_VALUE_SIZE + 1), "id": self._entry.id},
                False,
            ),
            (
                False,
                "value(%s) is exceeded the limit" % ("a" * (AttributeValue.MAXIMUM_VALUE_SIZE + 1)),
            ),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "hoge", "id": "hoge"}, False
            ),
            (False, "value(hoge) is not int"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "hoge", "id": 9999}, False
            ),
            (False, "value(9999) is not entry id"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["named_object"], "hoge", False),
            (False, "value(hoge) is not dict"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"a": 1, "b": 2}, False
            ),
            (False, "value({'a': 1, 'b': 2}) is not key('name', 'id')"),
        )

        group: Group = Group.objects.create(name="group0")
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["group"], group.id, False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["group"], None, False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["group"], "", False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["group"], "hoge", False),
            (False, "value(hoge) is not int"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["group"], 9999, False),
            (False, "value(9999) is not group id"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["boolean"], True, False), (True, None)
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["boolean"], False, False), (True, None)
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["boolean"], "hoge", False),
            (False, "value(hoge) is not bool"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["date"], "2020-01-01", False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["date"], "", False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["date"], "01-01", False),
            (False, "value(01-01) is not format(YYYY-MM-DD)"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["date"], "hoge", False),
            (False, "value(hoge) is not format(YYYY-MM-DD)"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_string"], ["hoge", "fuga"], False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_string"], [], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_string"], ["hoge", ""], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_string"], "hoge", False),
            (False, "value(hoge) is not list"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_object"], [self._entry.id], False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_object"], [], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_object"], [self._entry.id, ""], False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_object"], [self._entry.id, None], False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_object"], self._entry.id, False
            ),
            (False, "value(%s) is not list" % self._entry.id),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_named_object"], [{"name": "hoge", "id": self._entry.id}], False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_named_object"], [], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_named_object"], [{"name": "", "id": ""}], False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_named_object"], [{"name": "", "id": None}], False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_named_object"],
                [{"name": "hoge", "id": self._entry.id}, {"name": "", "id": ""}],
                False,
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_named_object"],
                [{"name": "hoge", "id": self._entry.id}, {"name": "", "id": None}],
                False,
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_named_object"], {"name": "hoge", "id": self._entry.id}, False
            ),
            (False, "value({'name': 'hoge', 'id': %s}) is not list" % self._entry.id),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_group"], [group.id], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_group"], [], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_group"], [group.id, ""], False),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_group"], [group.id, None], False
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_group"], group.id, False),
            (False, "value(%s) is not list" % group.id),
        )

    def test_validate_attr_value_is_mandatory(self):
        for type in ["string", "text"]:
            self.assertEqual(
                AttributeValue.validate_attr_value(AttrTypeValue[type], "", True),
                (False, "mandatory attrs value is not specified"),
            )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["object"], None, True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["object"], "", True),
            (False, "mandatory attrs value is not specified"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "", "id": self._entry.id}, True
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "hoge", "id": ""}, True
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "hoge", "id": None}, True
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "", "id": ""}, True
            ),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["named_object"], {"name": "", "id": None}, True
            ),
            (False, "mandatory attrs value is not specified"),
        )

        group: Group = Group.objects.create(name="group0")
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["group"], None, True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["group"], "", True),
            (False, "mandatory attrs value is not specified"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["boolean"], True, True), (True, None)
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["boolean"], False, True), (True, None)
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["date"], "", True),
            (False, "mandatory attrs value is not specified"),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_string"], [], True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_string"], ["hoge", ""], True),
            (True, None),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_object"], [], True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_object"], [self._entry.id, ""], True
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_object"], [self._entry.id, None], True
            ),
            (True, None),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_named_object"], [], True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_named_object"], [{"name": "", "id": ""}], True
            ),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_named_object"], [{"name": "", "id": None}], True
            ),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_named_object"],
                [{"name": "hoge", "id": self._entry.id}, {"name": "", "id": ""}],
                True,
            ),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_named_object"],
                [{"name": "hoge", "id": self._entry.id}, {"name": "", "id": None}],
                True,
            ),
            (True, None),
        )

        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_group"], [], True),
            (False, "mandatory attrs value is not specified"),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(AttrTypeValue["array_group"], [group.id, ""], True),
            (True, None),
        )
        self.assertEqual(
            AttributeValue.validate_attr_value(
                AttrTypeValue["array_group"], [group.id, None], True
            ),
            (True, None),
        )
