from datetime import date, datetime, timezone

from django.conf import settings

from airone.lib.acl import ACLType
from airone.lib.test import ESLessAironeTestCase
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.models import Attribute, AttributeValue, Entry
from group.models import Group
from user.models import User


class ModelESLessTest(ESLessAironeTestCase):
    def setUp(self):
        super(ModelESLessTest, self).setUp()

        self._user: User = User(username="test")
        self._user.save()

        self._entity: Entity = Entity(name="entity", created_user=self._user)
        self._entity.save()

        self._entry: Entry = Entry(name="entry", created_user=self._user, schema=self._entity)
        self._entry.save()

        # set EntityAttr for the test Entity object
        self._entity_attr = EntityAttr(
            name="test",
            type=AttrType.STRING,
            is_mandatory=True,
            created_user=self._user,
            parent_entity=self._entity,
        )
        self._entity_attr.save()

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
                "name": "date",
                "set_val": date(2018, 12, 31),
                "exp_val": date(2018, 12, 31),
            },
            {
                "name": "datetime",
                "set_val": datetime(2018, 12, 31, 12, 34, 56, tzinfo=timezone.utc),
                "exp_val": datetime(2018, 12, 31, 12, 34, 56, tzinfo=timezone.utc),
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
        if role:
            attrinfo.append({"name": "role", "set_val": role, "exp_val": role})
            attrinfo.append({"name": "arr_role", "set_val": [role], "exp_val": [role]})

        return attrinfo

    def create_entity_with_all_type_attributes(self, user, ref_entity=None):
        """
        This is a test helper method to add attributes of all attribute-types
        to specified entity.
        """
        entity = Entity.objects.create(name="all_attr_entity", created_user=user)
        attr_info = {
            "str": {"type": AttrType.STRING, "value": "foo"},
            "text": {"type": AttrType.TEXT, "value": "bar"},
            "obj": {"type": AttrType.OBJECT, "value": str(self._entry.id) if self._entry else ""},
            "name": {"type": AttrType.NAMED_OBJECT, "value": {"name": "bar", "id": self._entry}},
            "bool": {"type": AttrType.BOOLEAN, "value": False},
            "group": {"type": AttrType.GROUP, "value": ""},
            "date": {"type": AttrType.DATE, "value": "2018-12-31"},
            "role": {"type": AttrType.ROLE, "value": ""},
            "datetime": {"type": AttrType.DATETIME, "value": "2020-01-01T00:00:00+00:00"},
            "arr_str": {"type": AttrType.ARRAY_STRING, "value": ["foo", "bar"]},
            "arr_obj": {"type": AttrType.ARRAY_OBJECT, "value": [str(self._entry.id)]},
            "arr_name": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "value": [{"name": "hoge", "id": self._entry}],
            },
            "arr_group": {"type": AttrType.ARRAY_GROUP, "value": []},
            "arr_role": {"type": AttrType.ARRAY_ROLE, "value": []},
        }
        for name, info in attr_info.items():
            entity_attr = EntityAttr.objects.create(
                name=name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )

            if ref_entity and info["type"] & AttrType.OBJECT:
                entity_attr.referral.add(ref_entity)

        return entity

    def make_attr(self, name, attrtype=AttrType.STRING, user=None, entity=None, entry=None):
        if not user:
            user = self._user
        if not entity:
            entity = self._entity
        if not entry:
            entry = self._entry

        entity_attr = EntityAttr.objects.create(
            name=name,
            type=attrtype,
            created_user=user,
            parent_entity=entity,
        )

        return Attribute.objects.create(
            name=name,
            schema=entity_attr,
            created_user=user,
            parent_entry=entry,
        )

    def test_make_attribute_value(self):
        # check values of created test objects
        self.assertEqual(self._entity.name, "entity")
        self.assertEqual(self._entry.name, "entry")
        self.assertEqual(self._attr.name, "attr")

        # check that newly made attribute is child of registered entry
        self.assertEqual(self._attr.parent_entry, self._entry)

    def test_make_attribute(self):
        attr = self.make_attr("hoge")
        attr.save()

        self.assertEqual(attr.name, "hoge")
        self.assertEqual(attr.parent_entry, self._entry)

    def test_make_entry(self):
        entry = Entry.objects.create(name="baz", schema=self._entity, created_user=self._user)

        self.assertEqual(entry.name, "baz")
        self.assertEqual(entry.schema, self._entity)
        self.assertEqual(entry.created_user, self._user)

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
        entity = Entity.objects.create(name="entity", created_user=user)
        attrbase = EntityAttr.objects.create(
            name="attrbase",
            type=AttrType.STRING,
            created_user=user,
            parent_entity=entity,
        )
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        attr = entry.add_attribute_from_base(attrbase, user)
        self.assertTrue(entry.attrs.filter(id=attr.id).exists())
        self.assertEqual(entry.attrs.count(), 1)

    def test_status_update_methods_of_attribute_value(self):
        value = AttributeValue(value="hoge", created_user=self._user, parent_attr=self._attr)
        value.save()
        self.assertFalse(value.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT))
        value.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
        self.assertTrue(value.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT))
        value.del_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
        self.assertFalse(value.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT))

    def test_for_boolean_attr_and_value(self):
        attr = self.make_attr("attr_bool", AttrType.BOOLEAN)
        attrv = attr.get_latest_value()
        self.assertIsNotNone(attrv)
        self.assertIsNone(attrv.referral)
        self.assertIsNone(attrv.date)
        attr.values.add(AttributeValue.objects.create(created_user=self._user, parent_attr=attr))
        self.assertIsNotNone(attr.get_latest_value())
        self.assertFalse(attr.get_latest_value().boolean)
        self.assertFalse(attr.is_updated(False))
        self.assertTrue(attr.is_updated(True))

    def test_for_date_attr_and_value(self):
        attr = self.make_attr("attr_date", AttrType.DATE)
        attr.values.add(AttributeValue.objects.create(created_user=self._user, parent_attr=attr))
        self.assertIsNotNone(attr.get_latest_value())
        self.assertIsNone(attr.get_latest_value().date)
        self.assertTrue(attr.is_updated(date(9999, 12, 31)))
        self.assertTrue(attr.is_updated("9999-12-31"))
        self.assertFalse(attr.is_updated(""))
        self.assertFalse(attr.is_updated("2022-01-99"))
        attr.add_value(self._user, date(2022, 7, 7))
        self.assertTrue(attr.is_updated(""))
