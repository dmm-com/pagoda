import json
from unittest.mock import Mock, patch

from rest_framework import status

from acl.models import ACLType
from airone.lib.types import (
    AttrType,
    AttrTypeValue,
)
from entity.models import Entity, EntityAttr
from entry import tasks
from entry.models import Entry
from entry.settings import CONFIG
from entry.tests.test_api_v2 import BaseViewTest
from group.models import Group
from role.models import Role


class ViewTest(BaseViewTest):
    def test_serach_entry(self):
        ref_entry4 = self.add_entry(self.user, "hoge4", self.ref_entity)
        ref_entry5 = self.add_entry(self.user, "hoge5", self.ref_entity)
        ref_entry6 = self.add_entry(self.user, "hoge6", self.ref_entity)
        ref_entry7 = self.add_entry(self.user, "hoge7", self.ref_entity)

        self.add_entry(
            self.user,
            "entry1",
            self.entity,
            values={
                "val": "hoge1",
            },
        )
        self.add_entry(
            self.user,
            "entry2",
            self.entity,
            values={
                "vals": ["hoge2", "fuga2"],
            },
        )
        self.add_entry(
            self.user,
            "entry3",
            self.entity,
            values={
                "text": "hoge3",
            },
        )
        self.add_entry(
            self.user,
            "entry4",
            self.entity,
            values={
                "ref": ref_entry4.id,
            },
        )
        self.add_entry(
            self.user,
            "entry5",
            self.entity,
            values={
                "refs": [ref_entry5.id],
            },
        )
        self.add_entry(
            self.user,
            "entry6",
            self.entity,
            values={
                "name": {"name": "index6", "id": ref_entry6.id},
            },
        )
        self.add_entry(
            self.user,
            "entry7",
            self.entity,
            values={"names": [{"name": "index7", "id": ref_entry7.id}]},
        )

        # test value attribute
        for x in range(1, 3):
            resp = self.client.get("/entry/api/v2/search/?query=hoge%s" % x)
            self.assertEqual(resp.status_code, 200)
            resp_data = resp.json()
            self.assertEqual(len(resp_data), 1)
            entry: Entry = Entry.objects.get(name="entry%s" % x)
            self.assertEqual(resp_data[0]["id"], entry.id)
            self.assertEqual(resp_data[0]["name"], entry.name)

        # test object attribute
        for x in range(4, 4):
            resp = self.client.get("/entry/api/v2/search/?query=hoge%s" % x)
            self.assertEqual(resp.status_code, 200)
            resp_data = resp.json()
            self.assertEqual(len(resp_data), 2)
            ref_entry: Entry = Entry.objects.get(name="hoge%s" % x)
            entry: Entry = Entry.objects.get(name="entry%s" % x)
            self.assertEqual(resp_data[0]["id"], ref_entry.id)
            self.assertEqual(resp_data[0]["name"], ref_entry.name)
            self.assertEqual(resp_data[1]["id"], entry.id)
            self.assertEqual(resp_data[1]["name"], entry.name)

        # test named_object attribute
        for x in range(6, 2):
            resp = self.client.get("/entry/api/v2/search/?query=index%s" % x)
            self.assertEqual(resp.status_code, 200)
            resp_data = resp.json()
            self.assertEqual(len(resp_data), 1)
            entry: Entry = Entry.objects.get(name="entry%s" % x)
            self.assertEqual(resp_data[0]["id"], entry.id)
            self.assertEqual(resp_data[0]["name"], entry.name)

    def test_serach_entry_with_regexp(self):
        entry: Entry = self.add_entry(
            self.user,
            "entry",
            self.entity,
            values={
                "val": "hoge",
                "ref": self.ref_entry.id,
            },
        )

        resp = self.client.get("/entry/api/v2/search/?query=Og")
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(len(resp_data), 1)
        self.assertEqual(resp_data[0]["id"], entry.id)
        self.assertEqual(resp_data[0]["name"], entry.name)

        resp = self.client.get("/entry/api/v2/search/?query=R-")
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(len(resp_data), 2)
        self.assertEqual(resp_data[0]["id"], self.ref_entry.id)
        self.assertEqual(resp_data[0]["name"], self.ref_entry.name)
        self.assertEqual(resp_data[1]["id"], entry.id)
        self.assertEqual(resp_data[1]["name"], entry.name)

    def test_serach_entry_multi_match(self):
        entry: Entry = self.add_entry(
            self.user,
            "hoge",
            self.entity,
            values={
                "val": "hoge",
            },
        )

        resp = self.client.get("/entry/api/v2/search/?query=hoge")
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(len(resp_data), 1)
        self.assertEqual(resp_data[0]["id"], entry.id)
        self.assertEqual(resp_data[0]["name"], entry.name)

    def test_serach_entry_order_by(self):
        self.add_entry(self.user, "z_hoge", self.entity)
        self.add_entry(self.user, "a_hoge", self.entity)
        self.add_entry(
            self.user,
            "a_entry",
            self.entity,
            values={
                "val": "z_hoge",
            },
        )
        self.add_entry(
            self.user,
            "z_entry",
            self.entity,
            values={
                "val": "a_hoge",
            },
        )

        # Entry name match has high priority
        resp = self.client.get("/entry/api/v2/search/?query=hoge")
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(len(resp_data), 4)
        for i, entry_name in enumerate(["a_hoge", "z_hoge", "a_entry", "z_entry"]):
            entry: Entry = Entry.objects.get(name=entry_name)
            self.assertEqual(resp_data[i]["id"], entry.id)
            self.assertEqual(resp_data[i]["name"], entry.name)

    def test_serach_entry_deleted_entry(self):
        entry1 = self.add_entry(
            self.user,
            "entry1",
            self.entity,
            values={
                "val": "hoge1",
                "ref": self.ref_entry.id,
            },
        )
        entry1.delete()

        self.add_entry(
            self.user,
            "entry2",
            self.entity,
            values={
                "ref": self.ref_entry.id,
            },
        )
        self.ref_entry.delete()

        for query in ["entry1", "hoge", "ref_entry"]:
            resp = self.client.get("/entry/api/v2/search/?query=%s" % query)
            self.assertEqual(resp.status_code, 200)
            resp_data = resp.json()
            self.assertEqual(len(resp_data), 0)

    def test_serach_entry_update_attrv(self):
        ref_entry1 = self.add_entry(self.user, "ref_entry1", self.ref_entity)
        ref_entry2 = self.add_entry(self.user, "ref_entry2", self.ref_entity)
        entry: Entry = self.add_entry(
            self.user,
            "entry",
            self.entity,
            values={
                "val": "hoge",
                "vals": ["hoge"],
                "ref": ref_entry1.id,
                "refs": [ref_entry1.id],
            },
        )
        entry.attrs.get(name="val").add_value(self.user, "fuga")
        entry.attrs.get(name="vals").add_value(self.user, ["fuga"])
        entry.attrs.get(name="ref").add_value(self.user, ref_entry2.id)
        entry.attrs.get(name="refs").add_value(self.user, [ref_entry2.id])
        entry.register_es()

        resp = self.client.get("/entry/api/v2/search/?query=hoge")
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(len(resp_data), 0)

        resp = self.client.get("/entry/api/v2/search/?query=ref_entry1")
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(len(resp_data), 1)
        self.assertEqual(resp_data[0]["id"], ref_entry1.id)
        self.assertEqual(resp_data[0]["name"], ref_entry1.name)

    def test_entry_after_entity_attr_was_deleted(self):
        entry: Entry = self.add_entry(self.user, "Entry", self.entity)

        # delete EntityAttr, then check it won't be returned in response
        self.entity.attrs.get(name="val", is_active=True).delete()

        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted([attr["schema"]["name"] for attr in resp.json()["attrs"]]),
            sorted(
                [
                    "ref",
                    "name",
                    "bool",
                    "date",
                    "datetime",
                    "group",
                    "groups",
                    "text",
                    "vals",
                    "refs",
                    "names",
                    "role",
                    "roles",
                    "num",
                    "nums",
                ]
            ),
        )

    def test_referral(self):
        entry = self.add_entry(
            self.user,
            "Entry",
            self.entity,
            values={
                "ref": self.ref_entry.id,
            },
        )

        resp = self.client.get("/entry/api/v2/%s/referral/" % self.ref_entry.id)
        self.assertEqual(resp.status_code, 200)

        resp_data = resp.json()
        results = resp_data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0],
            {
                "id": entry.id,
                "name": entry.name,
                "schema": {
                    "id": entry.schema.id,
                    "name": entry.schema.name,
                    "is_public": True,
                    "permission": ACLType.Full.value,
                },
                "aliases": [],
                "is_active": True,
                "deleted_user": None,
                "deleted_time": None,
                "updated_time": entry.updated_time.astimezone(self.TZ_INFO).isoformat(),
                "permission": ACLType.Full.value,
            },
        )

    def test_referral_unrelated_to_entry(self):
        resp = self.client.get("/entry/api/v2/%s/referral/" % 99999)  # invalid entry id
        self.assertEqual(resp.status_code, 200)

        resp_data = resp.json()
        results = resp_data["results"]
        self.assertEqual(len(results), 0)

    def test_get_attr_referrals_of_role(self):
        entity = self.create_entity(
            self.user,
            "Entity",
            attrs=[
                {"name": "role", "type": AttrType.ROLE},
                {"name": "roles", "type": AttrType.ARRAY_ROLE},
            ],
        )

        # test to get groups through API calling of get_attr_referrals
        for attr in entity.attrs.all():
            resp = self.client.get("/entry/api/v2/%d/attr_referrals/" % attr.id)
            self.assertEqual(resp.status_code, 200)

            # This expects results has all role information.
            self.assertEqual(
                sorted(resp.json(), key=lambda x: x["id"]),
                sorted(
                    [{"id": r.id, "name": r.name} for r in Role.objects.filter(is_active=True)],
                    key=lambda x: x["id"],
                ),
            )

    def test_get_attr_referrals_of_group(self):
        user = self.guest_login("guest2")

        # initialize instances to be used in this test case
        groups = [Group.objects.create(name=x) for x in ["g-foo", "g-bar", "g-baz"]]
        entity = Entity.objects.create(name="Entity", created_user=user)
        for name, type_index in [("grp", "group"), ("arr_group", "array_group")]:
            EntityAttr.objects.create(
                **{
                    "name": name,
                    "type": AttrTypeValue[type_index],
                    "created_user": user,
                    "parent_entity": entity,
                }
            )

        # test to get groups through API calling of get_attr_referrals
        for attr in entity.attrs.all():
            resp = self.client.get("/entry/api/v2/%d/attr_referrals/" % attr.id)
            self.assertEqual(resp.status_code, 200)

            # This expects results has all groups information.
            self.assertEqual(
                sorted(resp.json(), key=lambda x: x["id"]),
                sorted(
                    [{"id": g.id, "name": g.name} for g in Group.objects.all()],
                    key=lambda x: x["id"],
                ),
            )

        # test to get groups which are only active and matched with keyword
        groups[2].delete()
        for attr in entity.attrs.all():
            resp = self.client.get("/entry/api/v2/%d/attr_referrals/" % attr.id, {"keyword": "ba"})
            self.assertEqual(resp.status_code, 200)

            # This expects results has only information of 'g-bar' because 'g-foo' is
            # not matched with keyword and 'g-baz' has already been deleted.
            self.assertEqual(resp.json(), [{"id": groups[1].id, "name": groups[1].name}])

    def test_get_attr_referrals_of_entry(self):
        admin = self.admin_login()

        # create Entity&Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=admin)

        entity = Entity.objects.create(name="Entity", created_user=admin)
        entity_attr = EntityAttr.objects.create(
            **{
                "name": "Refer",
                "type": AttrType.OBJECT,
                "created_user": admin,
                "parent_entity": entity,
            }
        )

        entity_attr.referral.add(ref_entity)

        for index in range(CONFIG.MAX_LIST_REFERRALS, -1, -1):
            Entry.objects.create(name="e-%s" % index, schema=ref_entity, created_user=admin)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=admin)

        # get Attribute object after complement them in the entry
        entry.complement_attrs(admin)
        attr = entry.attrs.get(name="Refer")

        # try to get entries without keyword
        resp = self.client.get("/entry/api/v2/%d/attr_referrals/" % attr.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), CONFIG.MAX_LIST_REFERRALS)

        # specify invalid Attribute ID
        resp = self.client.get("/entry/api/v2/9999/attr_referrals/")
        self.assertEqual(resp.status_code, 404)

        # speify valid Attribute ID and a enalbed keyword
        resp = self.client.get("/entry/api/v2/%d/attr_referrals/" % attr.id, {"keyword": "e-1"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")

        # This means e-1 and 'e-10' to 'e-19' are returned
        self.assertEqual(len(resp.json()), 11)

        # speify valid Attribute ID and a unabailabe keyword
        resp = self.client.get("/entry/api/v2/%d/attr_referrals/" % attr.id, {"keyword": "hoge"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 0)

        # Add new data
        for index in [101, 111, 100, 110]:
            Entry.objects.create(name="e-%s" % index, schema=ref_entity, created_user=admin)

        # Run with 'e-1' as keyword
        resp = self.client.get("/entry/api/v2/%d/attr_referrals/" % attr.id, {"keyword": "e-1"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")

        # Check the number of return values
        self.assertEqual(len(resp.json()), 15)

        # TODO support natural sort?
        # Check if it is sorted in the expected order
        # targets = [1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 100, 101, 110, 111]
        # for i, res in enumerate(resp.json()):
        #     self.assertEqual(res["name"], "e-%s" % targets[i])

        # send request with keywords that hit more than MAX_LIST_REFERRALS
        Entry.objects.create(name="e", schema=ref_entity, created_user=admin)

        resp = self.client.get("/entry/api/v2/%d/attr_referrals/" % attr.id, {"keyword": "e"})
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.json()[0]["name"], "e")

    def test_get_attr_referrals_with_entity_attr(self):
        """
        This test is needed because the get_attr_referrals API will receive an ID
        of Attribute from entry.edit view, but also receive an EntityAttr's one
        from entry.create view.
        """
        admin = self.admin_login()

        # create Entity&Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=admin)
        for index in range(0, CONFIG.MAX_LIST_REFERRALS + 1):
            Entry.objects.create(name="e-%s" % index, schema=ref_entity, created_user=admin)

        entity = Entity.objects.create(name="Entity", created_user=admin)
        entity_attr = EntityAttr.objects.create(
            **{
                "name": "Refer",
                "type": AttrType.NAMED_OBJECT,
                "created_user": admin,
                "parent_entity": entity,
            }
        )
        entity_attr.referral.add(ref_entity)

        resp = self.client.get(
            "/entry/api/v2/%d/attr_referrals/" % entity_attr.id, {"keyword": "e-1"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")

        # This means e-1 and 'e-10' to 'e-19' are returned
        self.assertEqual(len(resp.json()), 11)

    def test_advanced_search(self):
        entry1: Entry = self.add_entry(
            self.user,
            "Entry1",
            self.entity,
            values={
                "val": "hoge",
                "ref": self.ref_entry.id,
                "name": {"name": "hoge", "id": self.ref_entry.id},
                "bool": False,
                "date": "2018-12-31",
                "group": self.group.id,
                "groups": [self.group.id],
                "text": "fuga",
                "vals": ["foo", "bar"],
                "refs": [self.ref_entry.id],
                "names": [
                    {"name": "foo", "id": self.ref_entry.id},
                    {"name": "bar", "id": self.ref_entry.id},
                ],
                "role": self.role.id,
                "roles": [self.role.id],
                "datetime": "2018-12-31T00:00:00+00:00",
            },
        )

        entry2: Entry = self.add_entry(
            self.user,
            "Entry2",
            self.entity,
        )

        params = {
            "entities": [self.entity.id],
            "attrinfo": [],
        }

        resp = self.client.post(
            "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {
                "count": 2,
                "total_count": 2,
                "values": [
                    {
                        "entity": {"id": self.entity.id, "name": "test-entity"},
                        "entry": {"id": entry1.id, "name": "Entry1"},
                        "attrs": {
                            "val": {
                                "is_readable": True,
                                "type": 2,
                                "value": {"as_string": "hoge"},
                            },
                            "vals": {
                                "is_readable": True,
                                "type": 1026,
                                "value": {"as_array_string": ["foo", "bar"]},
                            },
                            "ref": {
                                "is_readable": True,
                                "type": 1,
                                "value": {"as_object": {"id": self.ref_entry.id, "name": "r-0"}},
                            },
                            "refs": {
                                "is_readable": True,
                                "type": 1025,
                                "value": {
                                    "as_array_object": [{"id": self.ref_entry.id, "name": "r-0"}]
                                },
                            },
                            "name": {
                                "is_readable": True,
                                "type": 2049,
                                "value": {
                                    "as_named_object": {
                                        "name": "hoge",
                                        "object": {"id": self.ref_entry.id, "name": "r-0"},
                                    }
                                },
                            },
                            "names": {
                                "is_readable": True,
                                "type": 3073,
                                "value": {
                                    "as_array_named_object": [
                                        {
                                            "name": "foo",
                                            "object": {"id": self.ref_entry.id, "name": "r-0"},
                                        },
                                        {
                                            "name": "bar",
                                            "object": {"id": self.ref_entry.id, "name": "r-0"},
                                        },
                                    ]
                                },
                            },
                            "group": {
                                "is_readable": True,
                                "type": 16,
                                "value": {"as_group": {"id": self.group.id, "name": "group0"}},
                            },
                            "groups": {
                                "is_readable": True,
                                "type": 1040,
                                "value": {
                                    "as_array_group": [{"id": self.group.id, "name": "group0"}]
                                },
                            },
                            "bool": {
                                "is_readable": True,
                                "type": 8,
                                "value": {"as_boolean": False},
                            },
                            "text": {
                                "is_readable": True,
                                "type": 4,
                                "value": {"as_string": "fuga"},
                            },
                            "date": {
                                "is_readable": True,
                                "type": 32,
                                "value": {"as_string": "2018-12-31"},
                            },
                            "role": {
                                "is_readable": True,
                                "type": 64,
                                "value": {"as_role": {"id": self.role.id, "name": "role0"}},
                            },
                            "roles": {
                                "is_readable": True,
                                "type": 1088,
                                "value": {"as_array_role": [{"id": self.role.id, "name": "role0"}]},
                            },
                            "datetime": {
                                "is_readable": True,
                                "type": AttrType.DATETIME,
                                "value": {"as_string": "2018-12-31T00:00:00+00:00"},
                            },
                            "num": {
                                "is_readable": True,
                                "type": AttrType.NUMBER,
                                "value": {"as_number": None},
                            },
                            "nums": {
                                "is_readable": True,
                                "type": AttrType.ARRAY_NUMBER,
                                "value": {"as_array_number": []},
                            },
                        },
                        "is_readable": True,
                        "referrals": None,
                    },
                    {
                        "entity": {"id": self.entity.id, "name": "test-entity"},
                        "entry": {"id": entry2.id, "name": "Entry2"},
                        "attrs": {
                            "val": {"is_readable": True, "type": 2, "value": {"as_string": ""}},
                            "vals": {
                                "is_readable": True,
                                "type": 1026,
                                "value": {"as_array_string": []},
                            },
                            "ref": {
                                "is_readable": True,
                                "type": 1,
                                "value": {"as_object": {"id": "", "name": ""}},
                            },
                            "refs": {
                                "is_readable": True,
                                "type": 1025,
                                "value": {"as_array_object": []},
                            },
                            "name": {
                                "is_readable": True,
                                "type": 2049,
                                "value": {
                                    "as_named_object": {
                                        "name": "",
                                        "object": {"id": "", "name": ""},
                                    }
                                },
                            },
                            "names": {
                                "is_readable": True,
                                "type": 3073,
                                "value": {"as_array_named_object": []},
                            },
                            "group": {
                                "is_readable": True,
                                "type": 16,
                                "value": {"as_group": {"id": "", "name": ""}},
                            },
                            "groups": {
                                "is_readable": True,
                                "type": 1040,
                                "value": {"as_array_group": []},
                            },
                            "bool": {
                                "is_readable": True,
                                "type": 8,
                                "value": {"as_boolean": False},
                            },
                            "text": {"is_readable": True, "type": 4, "value": {"as_string": ""}},
                            "date": {
                                "is_readable": True,
                                "type": 32,
                                "value": {"as_string": ""},
                            },
                            "role": {
                                "is_readable": True,
                                "type": 64,
                                "value": {"as_role": {"id": "", "name": ""}},
                            },
                            "roles": {
                                "is_readable": True,
                                "type": 1088,
                                "value": {"as_array_role": []},
                            },
                            "datetime": {
                                "is_readable": True,
                                "type": AttrType.DATETIME,
                                "value": {"as_string": ""},
                            },
                            "num": {
                                "is_readable": True,
                                "type": AttrType.NUMBER,
                                "value": {"as_number": None},
                            },
                            "nums": {
                                "is_readable": True,
                                "type": AttrType.ARRAY_NUMBER,
                                "value": {"as_array_number": []},
                            },
                        },
                        "is_readable": True,
                        "referrals": None,
                    },
                ],
            },
        )

    def test_advanced_search_with_exclude_referrals(self):
        # create test Models
        models = [
            self.create_entity(
                user=self.user,
                name=name,
                attrs=[
                    {"name": "refs", "type": AttrType.ARRAY_OBJECT},
                ],
            )
            for name in ["ModelA", "ModelB", "ModelC", "ModelD"]
        ]
        # create Items that is referred by other items
        ref_items = [
            self.add_entry(self.user, name, schema)
            for (name, schema) in [
                ("r01", models[0]),
                ("r02", models[0]),
                ("r03", models[0]),
            ]
        ]
        # create items that refers ref_items
        [
            self.add_entry(self.user, name, schema, values={"refs": value})
            for (name, schema, value) in [
                ("item01", models[1], [ref_items[0]]),
                ("item02", models[2], [ref_items[0], ref_items[1]]),
                ("item03", models[3], [ref_items[1], ref_items[2]]),
            ]
        ]

        # This doesn't return items that are referred by models[1]
        REQUEST_AND_RESULTS = [
            ([models[1].id], [ref_items[1], ref_items[2]]),
            ([models[1].id, models[2].id], [ref_items[2]]),
            ([models[1].id, models[2].id, models[3].id], []),
        ]
        for exclude_referrals, expected_items in REQUEST_AND_RESULTS:
            params = {
                "entities": [models[0].id],
                "attrinfo": [],
                "has_referral": True,
                "referral_name": "",
                "exclude_referrals": exclude_referrals,
            }
            resp = self.client.post(
                "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
            )
            self.assertEqual(resp.status_code, 200)

            self.assertEqual(resp.json()["count"], len(expected_items))
            self.assertEqual(
                [x["entry"] for x in resp.json()["values"]],
                [{"id": x.id, "name": x.name} for x in expected_items],
            )

    def test_advanced_search_with_include_referrals(self):
        # create test Models
        models = [
            self.create_entity(
                user=self.user,
                name=name,
                attrs=[
                    {"name": "refs", "type": AttrType.ARRAY_OBJECT},
                ],
            )
            for name in ["ModelA", "ModelB", "ModelC", "ModelD"]
        ]
        # create Items that is referred by other items
        ref_items = [
            self.add_entry(self.user, name, schema)
            for (name, schema) in [
                ("r01", models[0]),
                ("r02", models[0]),
                ("r03", models[0]),
            ]
        ]
        # create items that refers ref_items
        [
            self.add_entry(self.user, name, schema, values={"refs": value})
            for (name, schema, value) in [
                ("item01", models[1], [ref_items[0]]),
                ("item02", models[2], [ref_items[1]]),
                ("item03", models[3], [ref_items[1], ref_items[2]]),
            ]
        ]

        # This returns only referred by specific item's Model
        REQUEST_AND_RESULTS = [
            ([models[1].id], [ref_items[0]]),
            ([models[1].id, models[2].id], [ref_items[0], ref_items[1]]),
            ([models[1].id, models[2].id, models[3].id], ref_items),
            ([models[3].id], [ref_items[1], ref_items[2]]),
        ]
        for include_referrals, expected_items in REQUEST_AND_RESULTS:
            params = {
                "entities": [models[0].id],
                "attrinfo": [],
                "has_referral": True,
                "referral_name": "",
                "include_referrals": include_referrals,
            }
            resp = self.client.post(
                "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
            )
            self.assertEqual(resp.status_code, 200)

            self.assertEqual(resp.json()["count"], len(expected_items))
            self.assertEqual(
                [x["entry"] for x in resp.json()["values"]],
                [{"id": x.id, "name": x.name} for x in expected_items],
            )

    def test_advanced_search_all_entities(self):
        params = {
            "entities": [],
            "is_all_entities": True,
            "attrinfo": [{"name": self.entity.attrs.first().name}],
        }

        resp = self.client.post(
            "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        # TODO assert result

    def test_advanced_search_with_too_long_keyword(self):
        params = {
            "entities": [],
            "is_all_entities": True,
            "attrinfo": [{"name": "a" * (CONFIG.MAX_QUERY_SIZE + 1)}],
        }

        resp = self.client.post(
            "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_advanced_search_with_too_long_hint_entry_keyword(self):
        params = {
            "entities": [],
            "is_all_entities": True,
            "hint_entry": [{"keyword": "a" * (CONFIG.MAX_QUERY_SIZE + 1)}],
        }

        resp = self.client.post(
            "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_advanced_search_results_multiple_entities_different_attrs(self):
        alpha_entity_api = Entity.objects.create(
            name="AlphaEntityAPIResults", created_user=self.user
        )
        beta_entity_api = Entity.objects.create(name="BetaEntityAPIResults", created_user=self.user)

        # common attribute for both entities
        common_attr_alpha_schema = EntityAttr.objects.create(
            name="common_attr_api",
            type=AttrType.STRING,
            created_user=self.user,
            parent_entity=alpha_entity_api,
        )
        common_attr_beta_schema = EntityAttr.objects.create(
            name="common_attr_api",
            type=AttrType.STRING,
            created_user=self.user,
            parent_entity=beta_entity_api,
        )
        # attribute only for alpha entity
        alpha_only_attr_schema = EntityAttr.objects.create(
            name="alpha_only_attr_api",
            type=AttrType.STRING,
            created_user=self.user,
            parent_entity=alpha_entity_api,
        )

        entry_alpha_api = Entry.objects.create(
            name="entryAlphaAPIResults1", schema=alpha_entity_api, created_user=self.user
        )
        attr_alpha_common = entry_alpha_api.add_attribute_from_base(
            common_attr_alpha_schema, self.user
        )
        attr_alpha_common.add_value(self.user, "common_value_Alpha_API")
        attr_alpha_only = entry_alpha_api.add_attribute_from_base(alpha_only_attr_schema, self.user)
        attr_alpha_only.add_value(self.user, "alpha_specific_value_API")

        entry_beta_api = Entry.objects.create(
            name="entryBetaAPIResults1", schema=beta_entity_api, created_user=self.user
        )
        attr_beta_common = entry_beta_api.add_attribute_from_base(
            common_attr_beta_schema, self.user
        )
        attr_beta_common.add_value(self.user, "common_value_Beta_API")

        entry_alpha_api.register_es()
        entry_beta_api.register_es()

        params = {
            "entities": [str(alpha_entity_api.id), str(beta_entity_api.id)],
            "attrinfo": [
                {"name": "common_attr_api"},
                {"name": "alpha_only_attr_api"},
            ],
            "is_output_all": True,
            "is_all_entities": False,
            "entry_limit": 10,
            "entry_offset": 0,
        }

        resp = self.client.post(
            "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        response_data = resp.json()
        self.assertEqual(response_data["count"], 2)
        self.assertEqual(len(response_data["values"]), 2)

        ret_values_sorted = sorted(response_data["values"], key=lambda x: x["entry"]["name"])

        entry_alpha_result = ret_values_sorted[0]
        self.assertEqual(entry_alpha_result["entry"]["name"], "entryAlphaAPIResults1")
        self.assertEqual(entry_alpha_result["entity"]["name"], "AlphaEntityAPIResults")
        self.assertIn("common_attr_api", entry_alpha_result["attrs"])
        self.assertEqual(
            entry_alpha_result["attrs"]["common_attr_api"]["value"],
            {"as_string": "common_value_Alpha_API"},
        )
        self.assertIn("alpha_only_attr_api", entry_alpha_result["attrs"])
        self.assertEqual(
            entry_alpha_result["attrs"]["alpha_only_attr_api"]["value"],
            {"as_string": "alpha_specific_value_API"},
        )

        entry_beta_result = ret_values_sorted[1]
        self.assertEqual(entry_beta_result["entry"]["name"], "entryBetaAPIResults1")
        self.assertEqual(entry_beta_result["entity"]["name"], "BetaEntityAPIResults")
        self.assertIn("common_attr_api", entry_beta_result["attrs"])
        self.assertEqual(
            entry_beta_result["attrs"]["common_attr_api"]["value"],
            {"as_string": "common_value_Beta_API"},
        )
        self.assertNotIn("alpha_only_attr_api", entry_beta_result["attrs"])

    @patch(
        "entry.tasks.export_search_result_v2.delay", Mock(side_effect=tasks.export_search_result_v2)
    )
    def test_advanced_search_chain(self):
        ref_entry = self.add_entry(self.user, "RefEntry", self.ref_entity, values={"val": "hoge"})
        entry = self.add_entry(
            self.user,
            "Entry",
            self.entity,
            values={
                "ref": ref_entry.id,
            },
        )

        params = {
            "entities": [self.entity.id],
            "attrs": [{"name": "ref", "attrs": [{"name": "val", "value": "hoge"}]}],
        }
        resp = self.client.post(
            "/entry/api/v2/advanced_search_chain/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            [
                {
                    "id": entry.id,
                    "name": "Entry",
                    "schema": {
                        "id": entry.schema.id,
                        "name": "test-entity",
                        "is_public": True,
                        "permission": ACLType.Nothing.value,
                    },
                    "aliases": [],
                    "is_active": True,
                    "deleted_user": None,
                    "deleted_time": None,
                    "updated_time": entry.updated_time.astimezone(self.TZ_INFO).isoformat(),
                    "permission": ACLType.Nothing.value,
                },
            ],
        )

        # empty result case
        params = {
            "entities": [self.entity.id],
            "attrs": [{"name": "ref", "attrs": [{"name": "val", "value": "fuga"}]}],
        }
        resp = self.client.post(
            "/entry/api/v2/advanced_search_chain/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

        # bad request case
        params = {
            "entities": [self.entity.id],
            "attrs": [{"name": "ref", "attrs": [{"value": "fuga"}]}],
        }
        resp = self.client.post(
            "/entry/api/v2/advanced_search_chain/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "non_field_errors": [
                    {
                        "code": "AE-121000",
                        "message": "Invalid condition({'value': 'fuga'}) was specified",
                    }
                ]
            },
        )

    def test_advanced_search_chain_with_hint_item_name(self):
        # This creates following items
        #   * [hoge] item0 --> ref0
        #   * [hoge] item1 --> ref0
        #   * [fuga] item2 --> ref0
        #   * [fuga] item3 --> ref1  (note: referring item is different)
        item_refs = [self.add_entry(self.user, "ref%d" % i, self.ref_entity) for i in range(2)]
        for item_index, (prefix, ref_index) in enumerate(
            [("hoge", 0), ("hoge", 0), ("fuga", 0), ("fuga", 1)]
        ):
            self.add_entry(
                self.user,
                "[%s] item%d" % (prefix, item_index),
                self.entity,
                values={
                    "ref": item_refs[ref_index],
                },
            )

        # send search-chain request by ordinary parameter
        params = {
            "entities": [self.entity.id],
            "attrs": [{"name": "ref", "value": "ref0"}],
        }
        resp = self.client.post(
            "/entry/api/v2/advanced_search_chain/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            [x["name"] for x in resp.json()], ["[hoge] item0", "[hoge] item1", "[fuga] item2"]
        )

        # send search-chain request with hint_item_name
        params = {
            "entities": [self.entity.id],
            "hint_item_name": "hoge",
            "attrs": [{"name": "ref", "value": "ref0"}],
        }
        resp = self.client.post(
            "/entry/api/v2/advanced_search_chain/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([x["name"] for x in resp.json()], ["[hoge] item0", "[hoge] item1"])
