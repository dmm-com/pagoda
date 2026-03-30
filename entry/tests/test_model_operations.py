from datetime import date, datetime, timezone
from unittest import skip

from django.conf import settings
from django.db.models import Q
from elasticsearch import NotFoundError

from acl.models import ACLBase
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.models import Attribute, AttributeValue, Entry
from entry.tests.test_model import BaseModelTest
from group.models import Group
from role.models import Role
from user.models import User


class ModelOperationsTest(BaseModelTest):
    def test_get_attribute_value_during_updating(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="entity", created_user=user)
        EntityAttr.objects.create(
            name="attr",
            type=AttrType.STRING,
            created_user=user,
            parent_entity=entity,
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

        attr = self.make_attr("attr_ref", attrtype=AttrType.OBJECT)

        # this attribute is needed to check not only get referral from normal object attribute,
        # but also from an attribute that refers array referral objects
        arr_attr = self.make_attr("attr_arr_ref", attrtype=AttrType.ARRAY_OBJECT)

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

        # This function checks that this get_referred_objects method only get
        # unique reference objects except for the self referred object.
        for entry in [entry1, entry2]:
            referred_entries = entry.get_referred_objects()
            self.assertEqual(referred_entries.count(), 1)
            self.assertEqual(list(referred_entries), [self._entry])

    def test_get_referred_entries_classmethod(self):
        user = User.objects.create(username="hoge")

        # Initialize Entities and Entries which will be used in this test
        model_nw = self.create_entity(
            user, "NW", attrs=[{"name": "parent", "type": AttrType.OBJECT}]
        )
        nw0 = self.add_entry(user, "10.0.0.0/16", model_nw)
        nw1 = self.add_entry(user, "10.0.1.0/24", model_nw, values={"parent": nw0})
        nw2 = self.add_entry(user, "10.0.2.0/24", model_nw, values={"parent": nw0})

        model_ip = self.create_entity(
            user, "IPaddr", attrs=[{"name": "nw", "type": AttrType.OBJECT}]
        )
        for name, nw in [("10.0.1.1", nw1), ("10.0.1.2", nw1), ("10.0.2.1", nw2)]:
            self.add_entry(user, name, model_ip, values={"nw": nw})

        # get Entries that refer ne0 ~ nw1
        entries = Entry.get_referred_entries([nw0.id, nw1.id, nw2.id], filter_entities=["IPaddr"])
        self.assertEqual([x.name for x in entries.all()], ["10.0.1.1", "10.0.1.2", "10.0.2.1"])

    def test_get_referred_objects_after_deleting_entity_attr(self):
        user = User.objects.create(username="hoge")

        # Initialize Entities and Entries which will be used in this test
        ref_entity = self.create_entity(user, "Ref Entity")
        ref_entry = self.add_entry(user, "Ref", ref_entity)
        entity = self.create_entity(
            user,
            "Entity",
            attrs=[
                {
                    "name": "ref",
                    "type": AttrType.OBJECT,
                }
            ],
        )
        self.add_entry(user, "Entry", entity, values={"ref": ref_entry})

        # delete EntityAttr that refers Entity "Ref Entity"
        entity_attr = entity.attrs.get(name="ref")
        self.assertTrue(entity_attr.is_active)
        entity_attr.delete()

        # check the results of Entry.get_referred_objects() will be reflected by
        # deleting EntityAttr
        self.assertFalse(ref_entry.get_referred_objects().exists())

    def test_get_referred_objects_with_entity_param(self):
        for i in range(3, 6):
            entity = Entity.objects.create(name="Entity" + str(i), created_user=self._user)
            entry = Entry.objects.create(
                name="entry" + str(i), created_user=self._user, schema=entity
            )

            attr = self.make_attr(
                "attr_ref" + str(i),
                attrtype=AttrType.OBJECT,
                entity=entity,
                entry=entry,
            )

            # make a reference 'entry' object
            attr.values.add(
                AttributeValue.objects.create(
                    created_user=self._user, parent_attr=attr, referral=self._entry
                )
            )

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
            type=AttrType.STRING,
            created_user=self._user,
            parent_entity=self._entity,
        )

        # create new attributes which are appended after creation of Entity
        self._entry.complement_attrs(self._user)

        self.assertEqual(self._entry.attrs.count(), 2)
        self.assertEqual(self._entry.attrs.last().schema, newattr)

    def test_get_value_history(self):
        EntityAttr.objects.create(
            **{
                "name": "attr",
                "type": AttrType.STRING,
                "created_user": self._user,
                "parent_entity": self._entity,
            }
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

        attr = self.make_attr("attr_ref", attrtype=AttrType.OBJECT)

        # make a self reference value
        attr.values.add(
            AttributeValue.objects.create(created_user=self._user, parent_attr=attr, referral=entry)
        )

        # set referral cache
        self.assertEqual(list(entry.get_referred_objects()), [self._entry])

        # register entry to the Elasticsearch to check that will be deleted
        deleting_entry_id = self._entry.id
        self._entry.register_es()
        res = self._es.get(index=settings.ES_CONFIG["INDEX_NAME"], id=deleting_entry_id)
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
        with self.assertRaises(NotFoundError):
            self._es.get(index=settings.ES_CONFIG["INDEX_NAME"], id=deleting_entry_id)

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
            "obj": {"type": AttrType.OBJECT, "value": ref_entries[0]},
            "arr_obj": {"type": AttrType.ARRAY_OBJECT, "value": ref_entries},
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

    def test_may_remove_referral(self):
        entity: Entity = self.create_entity_with_all_type_attributes(self._user, self._entity)
        entry: Entry = Entry.objects.create(name="e1", schema=entity, created_user=self._user)
        entry.complement_attrs(self._user)

        attr_info = [
            {"name": "obj", "val": self._entry, "del": ""},
            {
                "name": "name",
                "val": {"name": "new_value", "id": self._entry},
                "del": {"name": "", "id": ""},
            },
            {"name": "arr_obj", "val": [self._entry], "del": []},
            {"name": "arr_name", "val": [{"name": "new_value", "id": self._entry}], "del": []},
        ]
        for info in attr_info:
            entity_attr: EntityAttr = entity.attrs.get(name=info["name"])
            entity_attr.is_delete_in_chain = True
            entity_attr.save()

            attr: Attribute = entry.attrs.get(schema=entity_attr)
            attr.add_value(self._user, info["val"])
            attr.may_remove_referral()

            self._entry.refresh_from_db()
            self.assertFalse(self._entry.is_active)

            # restore to pre-test state
            attr.add_value(self._user, info["del"])
            self._entry.restore()

    def test_order_of_array_named_ref_entries(self):
        ref_entity = Entity.objects.create(name="referred_entity", created_user=self._user)
        ref_entry = Entry.objects.create(
            name="referred_entry", created_user=self._user, schema=ref_entity
        )

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
            AttributeValue.objects.create(value=str(i), parent_attrv=attrv, **basic_params)

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

        attr = self.make_attr(name="attr", attrtype=AttrType.ARRAY_STRING)
        attr.is_public = False
        attr.save()
        self.assertIsNone(attr.clone(unknown_user))

    def test_clone_attribute_typed_string(self):
        attr = self.make_attr(name="attr", attrtype=AttrType.STRING)
        attr.add_value(self._user, "hoge")
        copy_entry = Entry.objects.create(
            schema=self._entity, name="copy_entry", created_user=self._user
        )
        cloned_attr = attr.clone(self._user, parent_entry=copy_entry)

        self.assertIsNotNone(cloned_attr)
        self.assertNotEqual(cloned_attr.id, attr.id)
        self.assertEqual(cloned_attr.name, attr.name)
        self.assertEqual(attr.parent_entry, self._entry)
        self.assertEqual(cloned_attr.parent_entry, copy_entry)
        self.assertEqual(cloned_attr.values.count(), attr.values.count())
        self.assertNotEqual(cloned_attr.values.last(), attr.values.last())

    def test_clone_attribute_typed_array_string(self):
        attr = self.make_attr(name="attr", attrtype=AttrType.ARRAY_STRING)
        attr.add_value(self._user, [str(i) for i in range(10)])
        copy_entry = Entry.objects.create(
            schema=self._entity, name="copy_entry", created_user=self._user
        )
        cloned_attr = attr.clone(self._user, parent_entry=copy_entry)

        self.assertIsNotNone(cloned_attr)
        self.assertNotEqual(cloned_attr.id, attr.id)
        self.assertEqual(cloned_attr.name, attr.name)
        self.assertEqual(attr.parent_entry, self._entry)
        self.assertEqual(cloned_attr.parent_entry, copy_entry)
        self.assertEqual(cloned_attr.values.count(), attr.values.count())
        self.assertNotEqual(cloned_attr.values.last(), attr.values.last())

        # checks that AttributeValues that parent_attr has also be cloned
        orig_attrv = attr.values.last()
        cloned_attrv = cloned_attr.values.last()

        self.assertEqual(orig_attrv.data_array.count(), cloned_attrv.data_array.count())
        for v1, v2 in zip(orig_attrv.data_array.all(), cloned_attrv.data_array.all()):
            self.assertNotEqual(v1, v2)
            self.assertEqual(v1.value, v2.value)

    def test_clone_attribute_typed_array_number(self):
        attr = self.make_attr(name="attr", attrtype=AttrType.ARRAY_NUMBER)
        attr.add_value(self._user, [float(i) + 0.5 for i in range(10)])
        copy_entry = Entry.objects.create(
            schema=self._entity, name="copy_entry", created_user=self._user
        )
        cloned_attr = attr.clone(self._user, parent_entry=copy_entry)

        self.assertIsNotNone(cloned_attr)
        self.assertNotEqual(cloned_attr.id, attr.id)
        self.assertEqual(cloned_attr.name, attr.name)
        self.assertEqual(attr.parent_entry, self._entry)
        self.assertEqual(cloned_attr.parent_entry, copy_entry)
        self.assertEqual(cloned_attr.values.count(), attr.values.count())
        self.assertNotEqual(cloned_attr.values.last(), attr.values.last())

        # checks that AttributeValues that parent_attr has also be cloned
        orig_attrv = attr.values.last()
        cloned_attrv = cloned_attr.values.last()

        self.assertEqual(orig_attrv.data_array.count(), cloned_attrv.data_array.count())
        for v1, v2 in zip(orig_attrv.data_array.all(), cloned_attrv.data_array.all()):
            self.assertNotEqual(v1, v2)
            # For number values, we need to handle float comparison properly
            orig_val = v1.get_value()
            cloned_val = v2.get_value()
            if orig_val is None and cloned_val is None:
                pass  # Both None, which is correct
            elif orig_val is None or cloned_val is None:
                self.fail(f"One value is None but the other isn't: {orig_val} vs {cloned_val}")
            else:
                self.assertAlmostEqual(orig_val, cloned_val, places=10)

    def test_clone_entry(self):
        test_entity = Entity.objects.create(name="E0", created_user=self._user)
        EntityAttr.objects.create(
            **{
                "name": "string",
                "type": AttrType.STRING,
                "created_user": self._user,
                "parent_entity": test_entity,
            }
        )

        EntityAttr.objects.create(
            **{
                "name": "arrobj",
                "type": AttrType.ARRAY_OBJECT,
                "created_user": self._user,
                "parent_entity": test_entity,
            }
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
        for original_attr, cloned_attr in [
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
            EntityAttr.objects.create(
                **{
                    "type": AttrType.STRING,
                    "created_user": self._user,
                    "parent_entity": self._entity,
                    "name": info["name"],
                    "is_public": info["is_public"],
                }
            )

        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=self._user)
        entry.complement_attrs(self._user)

        # set Attribute's is not public except attr1
        entry.attrs.filter(~Q(schema__name="attr1")).update(is_public=False)

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
        entry.readable.roles.add(role)
        role.users.add(unknown_user)
        self.assertIsNotNone(entry.clone(unknown_user))

    def test_set_value_method(self):
        user = User.objects.create(username="hoge")
        test_groups = [Group.objects.create(name=x) for x in ["g1", "g2"]]
        test_roles = [Role.objects.create(name=x) for x in ["r1", "r2"]]

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
            {"name": "arr_role", "val": test_roles},
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
            [x.group for x in latest_value.data_array.all().select_related("group")],
            test_groups,
        )

        latest_value = entry.attrs.get(name="arr_role").get_latest_value()
        self.assertEqual(
            [x.role for x in latest_value.data_array.all().select_related("role")],
            test_roles,
        )

    def test_get_available_attrs(self):
        user = User.objects.create(username="hoge")
        test_group = Group.objects.create(name="test-group")
        test_role = Role.objects.create(name="test-role")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)
        aclbase_ref = ACLBase.objects.get(id=ref_entry.id)

        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        # set initial values for entry
        attrinfo = {}
        for info in self._get_attrinfo_template(ref_entry, test_group, test_role):
            attr = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["set_val"])

            if info["name"] not in attrinfo:
                attrinfo[info["name"]] = {}

            attrinfo[info["name"]]["attr"] = attr
            if attr.schema.type == AttrType.NAMED_OBJECT:
                attrinfo[info["name"]]["exp_val"] = {
                    "value": "bar",
                    "id": aclbase_ref.id,
                    "name": aclbase_ref.name,
                }
            elif attr.schema.type == AttrType.OBJECT:
                attrinfo[info["name"]]["exp_val"] = aclbase_ref
            elif attr.schema.type == AttrType.ARRAY_NAMED_OBJECT:
                attrinfo[info["name"]]["exp_val"] = [
                    {
                        "value": "hoge",
                        "id": aclbase_ref.id,
                        "name": aclbase_ref.name,
                    }
                ]
            elif attr.schema.type == AttrType.ARRAY_OBJECT:
                attrinfo[info["name"]]["exp_val"] = [aclbase_ref]
            elif attr.schema.type == AttrType.GROUP:
                attrinfo[info["name"]]["exp_val"] = test_group
            elif attr.schema.type == AttrType.ARRAY_GROUP:
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
            self.assertEqual(result["is_readable"], True)
            self.assertEqual(result["last_value"], attrinfo[attr.name]["exp_val"])

    def test_get_available_attrs_with_multi_attribute_value(self):
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
        EntityAttr.objects.create(
            **{
                "name": "attr",
                "type": AttrType.OBJECT,
                "created_user": user,
                "parent_entity": entity,
            }
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
        EntityAttr.objects.create(
            **{
                "name": "attr",
                "type": AttrType.STRING,
                "created_user": user,
                "parent_entity": entity,
            }
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
        self.assertEqual(AttributeValue.objects.get(id=attrv.id).data_type, AttrType.STRING)

    def test_get_deleted_referred_attrs(self):
        user = User.objects.create(username="hoge")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=user)
        ref_entry = Entry.objects.create(name="ReferredEntry", schema=ref_entity, created_user=user)

        attr_info = {
            "obj": {"type": AttrType.OBJECT, "value": ref_entry},
            "name": {
                "type": AttrType.NAMED_OBJECT,
                "value": {"name": "hoge", "id": ref_entry},
            },
            "arr_obj": {"type": AttrType.ARRAY_OBJECT, "value": [ref_entry]},
            "arr_name": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
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
                self.assertEqual([x for x in attr["last_value"]], [])
                self.assertFalse(any([x in attr["last_value"] for x in ["id", "name"]]))

    def test_get_available_attrs_with_empty_referral(self):
        user = User.objects.create(username="hoge")

        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=user)
        entity = Entity.objects.create(name="entity", created_user=user)
        attr_info = {
            "obj": {"type": AttrType.OBJECT, "value": None},
            "name": {
                "type": AttrType.NAMED_OBJECT,
                "value": {"name": "hoge", "id": None},
            },
            "arr_obj": {"type": AttrType.ARRAY_OBJECT, "value": []},
            "arr_name": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
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
        test_role = Role.objects.create(name="test-role")

        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

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
            {"name": "role", "set_val": str(test_role.id), "exp_val": test_role.name},
            {"name": "role", "set_val": test_role.id, "exp_val": test_role.name},
            {"name": "role", "set_val": test_role, "exp_val": test_role.name},
            {
                "name": "arr_role",
                "set_val": [str(test_role.id)],
                "exp_val": [test_role.name],
            },
            {"name": "arr_role", "set_val": [test_role.id], "exp_val": [test_role.name]},
            {"name": "arr_role", "set_val": [test_role], "exp_val": [test_role.name]},
            {
                "name": "datetime",
                "set_val": datetime(2018, 12, 31, 12, 34, 56, tzinfo=timezone.utc),
                "exp_val": datetime(2018, 12, 31, 12, 34, 56, tzinfo=timezone.utc),
            },
        ]
        for info in attr_info:
            attr = entry.attrs.get(name=info["name"])
            attr.add_value(user, info["set_val"])
            attrv = attr.get_latest_value()

            # test return value of get_value method
            self.assertEqual(attrv.get_value(), info["exp_val"])

            # test return value of get_value method with 'with_metainfo' parameter
            expected_value = {"type": attr.schema.type, "value": info["exp_val"]}
            if attr.is_array():
                if attr.schema.type & AttrType._NAMED:
                    expected_value["value"] = [{"hoge": {"id": test_ref.id, "name": test_ref.name}}]
                elif attr.schema.type & AttrType.OBJECT:
                    expected_value["value"] = [{"id": test_ref.id, "name": test_ref.name}]
                elif attr.schema.type & AttrType.GROUP:
                    expected_value["value"] = [{"id": test_grp.id, "name": test_grp.name}]
                elif attr.schema.type & AttrType.ROLE:
                    expected_value["value"] = [{"id": test_role.id, "name": test_role.name}]

            elif attr.schema.type & AttrType._NAMED:
                expected_value["value"] = {"bar": {"id": test_ref.id, "name": test_ref.name}}
            elif attr.schema.type & AttrType.OBJECT:
                expected_value["value"] = {"id": test_ref.id, "name": test_ref.name}
            elif attr.schema.type & AttrType.GROUP:
                expected_value["value"] = {"id": test_grp.id, "name": test_grp.name}
            elif attr.schema.type & AttrType.ROLE:
                expected_value["value"] = {"id": test_role.id, "name": test_role.name}

            self.assertEqual(attrv.get_value(with_metainfo=True), expected_value)

    def test_get_value_with_serialize_parameter(self):
        # Craete Attribute instance and set test Date value
        date_value = date(2021, 6, 8)
        attr_date = self.make_attr("date", attrtype=AttrType.DATE)
        attr_date.add_value(self._user, date_value)

        # test retrieved value by get_value method with serialize parameter is expected
        self.assertEqual(attr_date.get_latest_value().get_value(), date_value)
        self.assertEqual(attr_date.get_latest_value().get_value(serialize=True), str(date_value))

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
        role = Role.objects.create(name="Role")
        deleted_role = Role.objects.create(name="Deleted Role")
        deleted_role.delete()

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
            {"attr": "role", "input": role, "checker": lambda x: x == str(role.id)},
            {"attr": "role", "input": role.id, "checker": lambda x: x == str(role.id)},
            {"attr": "role", "input": str(role.name), "checker": lambda x: x == str(role.id)},
            {"attr": "role", "input": deleted_role, "checker": lambda x: x is None},
            {
                "attr": "arr_role",
                "input": ["Role"],
                "checker": lambda x: x == [str(role.id)],
            },
            {
                "attr": "arr_role",
                "input": [str(role.id)],
                "checker": lambda x: x == [str(role.id)],
            },
            {
                "attr": "arr_role",
                "input": [role.id],
                "checker": lambda x: x == [str(role.id)],
            },
            {
                "attr": "arr_role",
                "input": [role],
                "checker": lambda x: x == [str(role.id)],
            },
            {
                "attr": "arr_role",
                "input": [deleted_role],
                "checker": lambda x: x == [],
            },
        ]
        for info in checklist:
            attr = entry.attrs.get(name=info["attr"])

            converted_data = attr.convert_value_to_register(info["input"])

            self.assertTrue(info["checker"](converted_data))

            # create AttributeValue using converted value
            attr.add_value(user, converted_data)

            self.assertIsNotNone(attr.get_latest_value())
