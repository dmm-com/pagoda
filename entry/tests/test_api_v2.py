import datetime
import json
from unittest import mock
from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.exceptions import ValidationError

from acl.models import ACLType
from airone.lib.elasticsearch import AttrHint
from airone.lib.test import AironeViewTest
from airone.lib.types import (
    AttrDefaultValue,
    AttrType,
)
from entity.models import Entity, EntityAttr, ItemNameType
from entry import tasks
from entry.models import Entry
from entry.services import AdvancedSearchService
from group.models import Group
from role.models import Role
from trigger import tasks as trigger_tasks
from trigger.models import TriggerCondition
from user.models import User


class BaseViewTest(AironeViewTest):
    def setUp(self):
        super(BaseViewTest, self).setUp()

        self.user: User = self.guest_login()

        # create Entities, Entries and Group for using this test case
        self.ref_entity: Entity = self.create_entity(
            self.user,
            "ref_entity",
            attrs=self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY,
        )
        for attr in self.ref_entity.attrs.all():
            if attr.type & AttrType.OBJECT:
                attr.referral.add(self.ref_entity)

        self.ref_entry: Entry = self.add_entry(self.user, "r-0", self.ref_entity)
        self.group: Group = Group.objects.create(name="group0")
        self.role: Role = Role.objects.create(name="role0")

        attrs = []
        for attr_info in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY:
            if attr_info["type"] & AttrType.OBJECT:
                attr_info["ref"] = self.ref_entity
            attrs.append(attr_info)
        self.entity: Entity = self.create_entity(
            **{
                "user": self.user,
                "name": "test-entity",
                "attrs": attrs,
            }
        )


class ViewTest(BaseViewTest):
    def _create_lb_models_for_autoname(self):
        """
        This is a helper function to create LB and LBServiceGroup models for autoname tests.
        """
        model_lb = self.create_entity(self.user, "LB")
        model_sg = self.create_entity(
            self.user,
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

        return (model_lb, model_sg)

    def test_retrieve_entry(self):
        entry: Entry = self.add_entry(
            self.user,
            "Entry",
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
                "nums": [1.5, 2.3, 3.7],
                "refs": [self.ref_entry.id],
                "names": [
                    {"name": "foo", "id": self.ref_entry.id},
                    {"name": "bar", "id": self.ref_entry.id},
                ],
                "role": self.role.id,
                "roles": [self.role.id],
            },
        )
        # add an optional attribute after creating entry
        EntityAttr.objects.create(
            **{
                "name": "opt",
                "type": AttrType.STRING,
                "is_mandatory": False,
                "parent_entity": self.entity,
                "created_user": self.user,
            }
        )

        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 200)

        resp_data = resp.json()
        self.assertEqual(resp_data["id"], entry.id)
        self.assertEqual(resp_data["name"], entry.name)
        self.assertEqual(
            resp_data["schema"],
            {
                "id": entry.schema.id,
                "name": entry.schema.name,
                "is_public": entry.schema.is_public,
                "permission": ACLType.Full.value,
            },
        )

        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "val", resp_data["attrs"])),
            {
                "type": AttrType.STRING,
                "value": {"as_string": "hoge"},
                "id": entry.attrs.get(schema__name="val").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="val").schema.id,
                    "name": "val",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "ref", resp_data["attrs"])),
            {
                "type": AttrType.OBJECT,
                "value": {
                    "as_object": {
                        "id": self.ref_entry.id,
                        "name": self.ref_entry.name,
                        "schema": {
                            "id": self.ref_entry.schema.id,
                            "name": self.ref_entry.schema.name,
                        },
                    },
                },
                "id": entry.attrs.get(schema__name="ref").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="ref").schema.id,
                    "name": "ref",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "name", resp_data["attrs"])),
            {
                "type": AttrType.NAMED_OBJECT,
                "value": {
                    "as_named_object": {
                        "name": "hoge",
                        "object": {
                            "id": self.ref_entry.id,
                            "name": self.ref_entry.name,
                            "schema": {
                                "id": self.ref_entry.schema.id,
                                "name": self.ref_entry.schema.name,
                            },
                        },
                    },
                },
                "id": entry.attrs.get(schema__name="name").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="name").schema.id,
                    "name": "name",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "bool", resp_data["attrs"])),
            {
                "type": AttrType.BOOLEAN,
                "value": {"as_boolean": False},
                "id": entry.attrs.get(schema__name="bool").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="bool").schema.id,
                    "name": "bool",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "date", resp_data["attrs"])),
            {
                "type": AttrType.DATE,
                "value": {"as_string": "2018-12-31"},
                "id": entry.attrs.get(schema__name="date").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="date").schema.id,
                    "name": "date",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "group", resp_data["attrs"])),
            {
                "type": AttrType.GROUP,
                "value": {
                    "as_group": {
                        "id": self.group.id,
                        "name": self.group.name,
                    },
                },
                "id": entry.attrs.get(schema__name="group").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="group").schema.id,
                    "name": "group",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "groups", resp_data["attrs"])),
            {
                "type": AttrType.ARRAY_GROUP,
                "value": {
                    "as_array_group": [
                        {
                            "id": self.group.id,
                            "name": self.group.name,
                        }
                    ]
                },
                "id": entry.attrs.get(schema__name="groups").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="groups").schema.id,
                    "name": "groups",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "role", resp_data["attrs"])),
            {
                "type": AttrType.ROLE,
                "value": {
                    "as_role": {
                        "id": self.role.id,
                        "name": self.role.name,
                    },
                },
                "id": entry.attrs.get(schema__name="role").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="role").schema.id,
                    "name": "role",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "roles", resp_data["attrs"])),
            {
                "type": AttrType.ARRAY_ROLE,
                "value": {
                    "as_array_role": [
                        {
                            "id": self.role.id,
                            "name": self.role.name,
                        }
                    ]
                },
                "id": entry.attrs.get(schema__name="roles").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="roles").schema.id,
                    "name": "roles",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "text", resp_data["attrs"])),
            {
                "type": AttrType.TEXT,
                "value": {"as_string": "fuga"},
                "id": entry.attrs.get(schema__name="text").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="text").schema.id,
                    "name": "text",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "vals", resp_data["attrs"])),
            {
                "type": AttrType.ARRAY_STRING,
                "value": {"as_array_string": ["foo", "bar"]},
                "id": entry.attrs.get(schema__name="vals").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="vals").schema.id,
                    "name": "vals",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "nums", resp_data["attrs"])),
            {
                "type": AttrType.ARRAY_NUMBER,
                "value": {"as_array_number": [1.5, 2.3, 3.7]},
                "id": entry.attrs.get(schema__name="nums").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="nums").schema.id,
                    "name": "nums",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "refs", resp_data["attrs"])),
            {
                "type": AttrType.ARRAY_OBJECT,
                "value": {
                    "as_array_object": [
                        {
                            "id": self.ref_entry.id,
                            "name": self.ref_entry.name,
                            "schema": {
                                "id": self.ref_entry.schema.id,
                                "name": self.ref_entry.schema.name,
                            },
                        }
                    ]
                },
                "id": entry.attrs.get(schema__name="refs").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="refs").schema.id,
                    "name": "refs",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "names", resp_data["attrs"])),
            {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "value": {
                    "as_array_named_object": [
                        {
                            "name": "foo",
                            "object": {
                                "id": self.ref_entry.id,
                                "name": self.ref_entry.name,
                                "schema": {
                                    "id": self.ref_entry.schema.id,
                                    "name": self.ref_entry.schema.name,
                                },
                            },
                        },
                        {
                            "name": "bar",
                            "object": {
                                "id": self.ref_entry.id,
                                "name": self.ref_entry.name,
                                "schema": {
                                    "id": self.ref_entry.schema.id,
                                    "name": self.ref_entry.schema.name,
                                },
                            },
                        },
                    ]
                },
                "id": entry.attrs.get(schema__name="names").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="names").schema.id,
                    "name": "names",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "opt", resp_data["attrs"])),
            {
                "type": AttrType.STRING,
                "value": {"as_string": AttrDefaultValue[AttrType.STRING]},
                "id": None,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": self.entity.attrs.get(name="opt").id,
                    "name": "opt",
                },
            },
        )

    def test_retrieve_entry_without_permission(self):
        entry: Entry = self.add_entry(self.user, "test-entry", self.entity)

        # permission nothing entity
        self.entity.is_public = False
        self.entity.save()
        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readble entity
        self.role.users.add(self.user)
        self.entity.readable.roles.add(self.role)
        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 200)

        # permission nothing entry
        entry.is_public = False
        entry.save()
        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readble entry
        entry.readable.roles.add(self.role)
        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 200)

        # permission nothing entity attr
        entity_attr = entry.attrs.get(schema__name="val").schema
        entity_attr.is_public = False
        entity_attr.save()
        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "val", resp.json()["attrs"])),
            {
                "type": AttrType.STRING,
                "value": {"as_string": ""},
                "id": entry.attrs.get(schema__name="val").id,
                "is_mandatory": False,
                "is_readable": False,
                "schema": {
                    "id": entry.attrs.get(schema__name="val").schema.id,
                    "name": "val",
                },
            },
        )

        # permission readable entity attr
        entity_attr.readable.roles.add(self.role)
        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "val", resp.json()["attrs"])),
            {
                "type": AttrType.STRING,
                "value": {"as_string": ""},
                "id": entry.attrs.get(schema__name="val").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="val").schema.id,
                    "name": "val",
                },
            },
        )

        # permission nothing attr
        attr = entry.attrs.get(schema=entity_attr)
        attr.is_public = False
        attr.save()
        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "val", resp.json()["attrs"])),
            {
                "type": AttrType.STRING,
                "value": {"as_string": ""},
                "id": entry.attrs.get(schema__name="val").id,
                "is_mandatory": False,
                "is_readable": False,
                "schema": {
                    "id": entry.attrs.get(schema__name="val").schema.id,
                    "name": "val",
                },
            },
        )

        # permission readable attr
        attr.readable.roles.add(self.role)
        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "val", resp.json()["attrs"])),
            {
                "type": AttrType.STRING,
                "value": {"as_string": ""},
                "id": entry.attrs.get(schema__name="val").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="val").schema.id,
                    "name": "val",
                },
            },
        )

    def test_retrieve_entry_with_invalid_param(self):
        resp = self.client.get("/entry/api/v2/%s/" % "hoge")
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get("/entry/api/v2/%s/" % 9999)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Entry matches the given query."}
        )

    @mock.patch("airone.lib.custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("airone.lib.custom_view.call_custom")
    def test_retrieve_entry_with_customview(self, mock_call_custom):
        def side_effect(handler_name, entity_name, entry, entry_attrs, is_v2):
            self.assertEqual(handler_name, "get_entry_attr")
            self.assertEqual(entity_name, "test-entity")
            self.assertEqual(entry.name, "test-entry")
            self.assertEqual(len(entry_attrs), len(self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY))
            self.assertEqual(is_v2, True)

            # add attribute
            entry_attrs.append(
                {
                    "id": 0,
                    "type": AttrType.STRING,
                    "value": "hoge",
                    "schema": {
                        "id": 0,
                        "name": "fuga",
                    },
                }
            )

            return entry_attrs

        mock_call_custom.side_effect = side_effect

        entry: Entry = self.add_entry(self.user, "test-entry", self.entity)

        resp = self.client.get("/entry/api/v2/%s/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            len(resp.json()["attrs"]), len(self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY) + 1
        )
        self.assertEqual(
            resp.json()["attrs"][-1],
            {
                "id": 0,
                "type": AttrType.STRING,
                "value": "hoge",
                "schema": {
                    "id": 0,
                    "name": "fuga",
                },
            },
        )

    def test_retrieve_entry_with_deleted_referrals(self):
        entry: Entry = self.add_entry(
            self.user,
            "Entry",
            self.entity,
            values={
                "ref": self.ref_entry.id,
                "name": {"name": "hoge", "id": self.ref_entry.id},
                "refs": [self.ref_entry.id],
                "names": [
                    {"name": "foo", "id": self.ref_entry.id},
                    {"name": "bar", "id": self.ref_entry.id},
                ],
            },
        )
        # delete referring entry
        self.ref_entry.delete()

        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 200)

        resp_data = resp.json()
        self.assertEqual(resp_data["id"], entry.id)
        self.assertEqual(resp_data["name"], entry.name)
        self.assertEqual(
            resp_data["schema"],
            {
                "id": entry.schema.id,
                "name": entry.schema.name,
                "is_public": entry.schema.is_public,
                "permission": ACLType.Full.value,
            },
        )

        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "ref", resp_data["attrs"])),
            {
                "type": AttrType.OBJECT,
                "value": {
                    "as_object": None,
                },
                "id": entry.attrs.get(schema__name="ref").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="ref").schema.id,
                    "name": "ref",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "name", resp_data["attrs"])),
            {
                "type": AttrType.NAMED_OBJECT,
                "value": {
                    "as_named_object": {
                        "name": "hoge",
                        "object": None,
                    },
                },
                "id": entry.attrs.get(schema__name="name").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="name").schema.id,
                    "name": "name",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "refs", resp_data["attrs"])),
            {
                "type": AttrType.ARRAY_OBJECT,
                "value": {"as_array_object": []},
                "id": entry.attrs.get(schema__name="refs").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="refs").schema.id,
                    "name": "refs",
                },
            },
        )
        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "names", resp_data["attrs"])),
            {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "value": {"as_array_named_object": []},
                "id": entry.attrs.get(schema__name="names").id,
                "is_mandatory": False,
                "is_readable": True,
                "schema": {
                    "id": entry.attrs.get(schema__name="names").schema.id,
                    "name": "names",
                },
            },
        )

    @patch("entry.tasks.edit_entry_v2.delay", Mock(side_effect=tasks.edit_entry_v2))
    def test_update_entry(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        attr = {}
        for attr_name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)

        params = {
            "name": "entry-change",
            "attrs": [
                {"id": attr["val"].id, "value": "hoge"},
                {"id": attr["vals"].id, "value": ["hoge", "fuga"]},
                {"id": attr["ref"].id, "value": self.ref_entry.id},
                {"id": attr["refs"].id, "value": [self.ref_entry.id]},
                {"id": attr["name"].id, "value": {"name": "hoge", "id": self.ref_entry.id}},
                {"id": attr["names"].id, "value": [{"name": "hoge", "id": self.ref_entry.id}]},
                {"id": attr["group"].id, "value": self.group.id},
                {"id": attr["groups"].id, "value": [self.group.id]},
                {"id": attr["text"].id, "value": "hoge\nfuga"},
                {"id": attr["bool"].id, "value": True},
                {"id": attr["date"].id, "value": "2018-12-31"},
                {"id": attr["role"].id, "value": self.role.id},
                {"id": attr["roles"].id, "value": [self.role.id]},
                {"id": attr["num"].id, "value": 42},
                {"id": attr["nums"].id, "value": [10, 20, 30]},
                {"id": attr["datetime"].id, "value": "2018-12-31T00:00:00+00:00"},
            ],
        }
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        self.assertEqual(entry.status, 0)
        self.assertEqual(
            {
                attrv.parent_attr.name: attrv.get_value()
                for attrv in [attr.get_latest_value() for attr in entry.attrs.all()]
            },
            {
                "bool": True,
                "date": datetime.date(2018, 12, 31),
                "group": "group0",
                "groups": ["group0"],
                "name": {"hoge": "r-0"},
                "names": [{"hoge": "r-0"}],
                "ref": "r-0",
                "refs": ["r-0"],
                "text": "hoge\nfuga",
                "val": "hoge",
                "vals": ["hoge", "fuga"],
                "role": "role0",
                "roles": ["role0"],
                "num": 42,
                "nums": [10, 20, 30],
                "datetime": datetime.datetime(2018, 12, 31, 0, 0, 0, tzinfo=datetime.timezone.utc),
            },
        )
        search_result = self._es.search(body={"query": {"term": {"name": "entry-change"}}})
        self.assertEqual(search_result["hits"]["total"]["value"], 1)

    def test_update_entry_without_permission(self):
        params = {
            "name": "entry-change",
        }
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        # permission nothing entity
        self.entity.is_public = False
        self.entity.save()
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readable entity
        self.role.users.add(self.user)
        self.entity.readable.roles.add(self.role)
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission writable entity
        self.entity.writable.roles.add(self.role)
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # permission nothing entry
        entry.is_public = False
        entry.save()
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readable entry
        entry.readable.roles.add(self.role)
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission writable entry
        entry.writable.roles.add(self.role)
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

    @patch("entry.tasks.edit_entry_v2.delay", Mock(side_effect=tasks.edit_entry_v2))
    def test_update_entry_without_permission_attr(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        entity_attr = {}
        attr = {}
        for attr_name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            entity_attr[attr_name] = self.entity.attrs.get(name=attr_name)
            attr[attr_name] = entry.attrs.get(schema__name=attr_name)

        params = {
            "attrs": [
                {"id": entity_attr["val"].id, "value": "hoge"},
                {"id": entity_attr["vals"].id, "value": ["hoge"]},
            ]
        }

        entity_attr["vals"].is_public = False
        entity_attr["vals"].save()
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(attr["val"].get_latest_value().get_value(), "hoge")
        self.assertEqual(attr["vals"].get_latest_value().get_value(), [])

        params = {
            "attrs": [
                {"id": entity_attr["val"].id, "value": "fuga"},
                {"id": entity_attr["vals"].id, "value": ["fuga"]},
            ]
        }

        entity_attr["vals"].is_public = True
        entity_attr["vals"].save()
        attr["vals"].is_public = False
        attr["vals"].save()
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(attr["val"].get_latest_value().get_value(), "fuga")
        self.assertEqual(attr["vals"].get_latest_value().get_value(), [])

    def test_update_entry_with_invalid_param_entry_id(self):
        resp = self.client.put(
            "/entry/api/v2/%s/" % "hoge", json.dumps({"name": "entry1"}), "application/json"
        )
        self.assertEqual(resp.status_code, 404)

        resp = self.client.put(
            "/entry/api/v2/%s/" % 9999, json.dumps({"name": "entry1"}), "application/json"
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Entry matches the given query."}
        )

    def test_update_entry_with_invalid_param_name(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id,
            json.dumps({"name": "a" * (Entry._meta.get_field("name").max_length + 1)}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "name": [
                    {
                        "code": "AE-122000",
                        "message": "Ensure this field has no more than 200 characters.",
                    }
                ]
            },
        )

        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id,
            json.dumps({"name": "a" * (Entry._meta.get_field("name").max_length)}),
            "application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        hoge_entry: Entry = self.add_entry(self.user, "hoge", self.entity)
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps({"name": "hoge"}), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"name": [{"code": "AE-220000", "message": "specified name(hoge) already exists"}]},
        )

        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id,
            json.dumps({"name": "hoge\thoge"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "name": [
                    {
                        "code": "AE-250000",
                        "message": "Names containing tab characters cannot be specified.",
                    }
                ]
            },
        )

        hoge_entry.delete()
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps({"name": "hoge"}), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

    def test_update_entry_when_duplicated_alias_exists(self):
        # make an Item and Alias to prevent to updating another Item
        entry: Entry = self.add_entry(self.user, "Everest", self.entity)
        entry.add_alias("Chomolungma")

        entry: Entry = self.add_entry(self.user, "The highest mountain in the world", self.entity)
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id,
            json.dumps({"name": "Chomolungma"}),  # This is same name with other Alias
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "non_field_errors": [
                    {
                        "message": "A duplicated named Alias exists in this model",
                        "code": "AE-220000",
                    }
                ]
            },
        )

    def test_update_entry_with_invalid_param_attrs(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        attr = {}
        for attr_name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)

        test_values = [
            {
                "input": "hoge",
                "error_msg": {
                    "attrs": [
                        {
                            "code": "AE-121000",
                            "message": 'Expected a list of items but got type "str".',
                        }
                    ]
                },
            },
            {
                "input": ["hoge"],
                "error_msg": {
                    "attrs": {
                        "0": {
                            "non_field_errors": [
                                {
                                    "code": "AE-121000",
                                    "message": "Invalid data. Expected a dictionary, but got str.",
                                }
                            ]
                        }
                    }
                },
            },
            {
                "input": [{"attr1": "hoge"}],
                "error_msg": {
                    "attrs": {
                        "0": {
                            "id": [{"code": "AE-113000", "message": "This field is required."}],
                            "value": [{"code": "AE-113000", "message": "This field is required."}],
                        }
                    }
                },
            },
            {
                "input": [
                    {
                        "id": "hoge",
                        "value": "hoge",
                    }
                ],
                "error_msg": {
                    "attrs": {
                        "0": {
                            "id": [{"code": "AE-121000", "message": "A valid integer is required."}]
                        }
                    }
                },
            },
            {
                "input": [
                    {
                        "id": 9999,
                        "value": "hoge",
                    }
                ],
                "error_msg": {
                    "non_field_errors": [
                        {"code": "AE-230000", "message": "attrs id(9999) does not exist"}
                    ]
                },
            },
            {
                "input": [
                    {
                        "id": attr["ref"].id,
                        "value": "hoge",
                    }
                ],
                "error_msg": {
                    "non_field_errors": [
                        {
                            "code": "AE-121000",
                            "message": "attrs id(%s) - value(hoge) is not int" % attr["ref"].id,
                        }
                    ]
                },
            },
        ]

        for test_value in test_values:
            params = {"attrs": test_value["input"]}
            resp = self.client.put(
                "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
            )
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.json(), test_value["error_msg"])

    @patch("entry.tasks.edit_entry_v2.delay", Mock(side_effect=tasks.edit_entry_v2))
    @mock.patch("entry.tasks.notify_update_entry.delay")
    def test_update_entry_notify(self, mock_task):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps({"name": "hoge"}), "application/json"
        )

        self.assertTrue(mock_task.called)

    @patch("entry.tasks.edit_entry_v2.delay", Mock(side_effect=tasks.edit_entry_v2))
    @mock.patch("airone.lib.custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("airone.lib.custom_view.call_custom")
    def test_update_entry_with_customview(self, mock_call_custom):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        attr = {}
        for attr_name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)
        params = {
            "name": "hoge",
            "attrs": [
                {"id": attr["val"].id, "value": "fuga"},
            ],
            "delay_trigger": True,
        }

        def side_effect(handler_name, entity_name, user, *args):
            raise ValidationError("update error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(mock_call_custom.called)

        def side_effect(handler_name, entity_name, user, *args):
            self.assertEqual(entity_name, self.entity.name)
            self.assertEqual(user, self.user)

            # Check specified parameters are expected
            if handler_name == "validate_entry":
                self.assertEqual(args[0], self.entity.name)
                self.assertEqual(args[1], params["name"])
                self.assertEqual(args[2], params["attrs"])
                self.assertEqual(args[3], entry)

            if handler_name == "before_update_entry_v2":
                self.assertEqual(args[0], params)
                return args[0]

            if handler_name == "after_update_entry_v2":
                self.assertEqual(args[0], entry)

        mock_call_custom.side_effect = side_effect
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(mock_call_custom.called)

    @mock.patch("entry.tasks.notify_update_entry.delay")
    def test_update_entry_with_no_update(self, mock_task):
        entry: Entry = self.add_entry(
            self.user,
            "Entry",
            self.entity,
            values={
                "val": "hoge",
                "vals": ["hoge"],
            },
        )
        entity_attr = {}
        attr = {}
        for attr_name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            entity_attr[attr_name] = self.entity.attrs.get(name=attr_name)
            attr[attr_name] = entry.attrs.get(schema__name=attr_name)

        params = {
            "attrs": [
                {"id": entity_attr["val"].id, "value": "hoge"},
                {"id": entity_attr["vals"].id, "value": ["fuga"]},
            ]
        }
        self.client.put(
            "/entry/api/v2/%s/" % self.ref_entry.id, json.dumps(params), "application/json"
        )

        self.assertEqual(attr["val"].values.count(), 1)
        self.assertEqual(attr["vals"].values.count(), 2)
        self.assertFalse(mock_task.called)

    @mock.patch(
        "entry.tasks.register_referrals.delay", mock.Mock(side_effect=tasks.register_referrals)
    )
    @patch("entry.tasks.edit_entry_v2.delay", Mock(side_effect=tasks.edit_entry_v2))
    def test_update_entry_with_referral(self):
        self.add_entry(
            self.user,
            "Entry",
            self.entity,
            values={
                "ref": self.ref_entry.id,
            },
        )
        params = {
            "name": "ref-change",
        }
        self.client.put(
            "/entry/api/v2/%s/" % self.ref_entry.id, json.dumps(params), "application/json"
        )

        ret = AdvancedSearchService.search_entries(
            self.user, [self.entity.id], [AttrHint(name="ref")]
        )
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual(ret.ret_values[0].entry["name"], "Entry")
        self.assertEqual(ret.ret_values[0].attrs["ref"]["value"]["name"], "ref-change")

    def test_update_entry_without_attrs(self):
        resp = self.client.put(
            "/entry/api/v2/%s/" % self.ref_entry.id, json.dumps({}), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

    @patch("entry.tasks.edit_entry_v2.delay", Mock(side_effect=tasks.edit_entry_v2))
    @mock.patch(
        "trigger.tasks.may_invoke_trigger.delay",
        mock.Mock(side_effect=trigger_tasks.may_invoke_trigger),
    )
    def test_update_entry_when_trigger_is_set(self):
        # create Entry to be updated in this test
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        attr = {}
        for attr_name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)

        # register Trigger and Action that specify "fuga" at text attribute
        # when value "hoge" is set to the Attribute "val".
        TriggerCondition.register(
            self.entity,
            [
                {"attr_id": self.entity.attrs.get(name="val").id, "cond": "hoge"},
            ],
            [
                {"attr_id": self.entity.attrs.get(name="text").id, "value": "fuga"},
            ],
        )

        # send request to update Entry
        params = {
            "name": "entry-change",
            "attrs": [
                {"id": attr["val"].id, "value": "hoge"},
            ],
        }
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # check Attribute "text", which is specified by TriggerCondition, was changed to "fuga"
        self.assertEqual(entry.get_attrv("text").value, "fuga")

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    def test_destroy_entry(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        entry.refresh_from_db()
        self.assertRegex(entry.name, "entry_deleted_")
        self.assertFalse(entry.is_active)
        self.assertEqual(entry.deleted_user, self.user)
        self.assertIsNotNone(entry.deleted_time)

        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            [{"code": "AE-230000", "message": "specified entry has already been deleted"}],
        )

    def test_destroy_entry_without_permission(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        # permission nothing entity
        self.entity.is_public = False
        self.entity.save()
        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readable entity
        self.role.users.add(self.user)
        self.entity.readable.roles.add(self.role)
        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission writable entity
        self.entity.writable.roles.add(self.role)
        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 204)

        entry.restore()

        # permission nothing entry
        entry.is_public = False
        entry.save()
        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readable entry
        entry.readable.roles.add(self.role)
        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission writable entry
        entry.writable.roles.add(self.role)
        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 204)

    def test_destory_entry_with_invalid_param(self):
        resp = self.client.delete("/entry/api/v2/%s/" % "hoge", None, "application/json")
        self.assertEqual(resp.status_code, 404)

        resp = self.client.delete("/entry/api/v2/%s/" % 9999, None, "application/json")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Entry matches the given query."}
        )

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    @mock.patch("airone.lib.custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("airone.lib.custom_view.call_custom")
    def test_destroy_entry_with_custom_view(self, mock_call_custom):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        def side_effect(handler_name, entity_name, user, entry):
            raise ValidationError("delete error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(mock_call_custom.called)

        def side_effect(handler_name, entity_name, user, entry):
            self.assertTrue(handler_name in ["before_delete_entry_v2", "after_delete_entry_v2"])
            self.assertEqual(entity_name, self.entity.name)
            self.assertEqual(user, self.user)
            self.assertEqual(entry, entry)

        mock_call_custom.side_effect = side_effect
        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(mock_call_custom.called)

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    @mock.patch("entry.tasks.notify_delete_entry.delay")
    def test_destroy_entry_notify(self, mock_task):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")

        self.assertTrue(mock_task.called)

    def test_restore_entry(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        entry.delete()

        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.content, b"{}")

        entry.refresh_from_db()
        self.assertRegex(entry.name, "entry")
        self.assertTrue(entry.is_active)
        self.assertEqual(entry.status, 0)

        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), [{"code": "AE-230000", "message": "specified entry has not deleted"}]
        )

    def test_restore_entry_without_permission(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        entry.delete()

        # permission nothing entity
        self.entity.is_public = False
        self.entity.save()
        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readable entity
        self.role.users.add(self.user)
        self.entity.readable.roles.add(self.role)
        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission writable entity
        self.entity.writable.roles.add(self.role)
        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 201)

        entry.delete()

        # permission nothing entry
        entry.is_public = False
        entry.save()
        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readable entry
        entry.readable.roles.add(self.role)
        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission writable entry
        entry.writable.roles.add(self.role)
        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 201)

    def test_restore_entry_with_invalid_param(self):
        resp = self.client.post("/entry/api/v2/%s/restore/" % "hoge", None, "application/json")
        self.assertEqual(resp.status_code, 404)

        resp = self.client.post("/entry/api/v2/%s/restore/" % 9999, None, "application/json")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Entry matches the given query."}
        )

        entry = self.add_entry(self.user, "entry", self.entity)
        entry.delete()
        self.add_entry(self.user, "entry", self.entity)

        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            [{"code": "AE-220000", "message": "specified entry has already exist other"}],
        )

        entry2 = self.add_entry(self.user, "entry2", self.entity)
        entry2.delete()
        other_entry = self.add_entry(self.user, "other_entry", self.entity)
        other_entry.add_alias("entry2")

        resp = self.client.post("/entry/api/v2/%s/restore/" % entry2.id, None, "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            [{"code": "AE-220000", "message": "specified entry has already exist alias"}],
        )

    @mock.patch("airone.lib.custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("airone.lib.custom_view.call_custom")
    def test_restore_entry_with_custom_view(self, mock_call_custom):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        entry.delete()

        def side_effect(handler_name, entity_name, user, entry):
            raise ValidationError("restore error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), [{"code": "AE-121000", "message": "restore error"}])

        def side_effect(handler_name, entity_name, user, entry):
            self.assertTrue(handler_name in ["before_restore_entry_v2", "after_restore_entry_v2"])
            self.assertEqual(entity_name, self.entity.name)
            self.assertEqual(user, self.user)
            self.assertEqual(entry, entry)

        mock_call_custom.side_effect = side_effect
        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(mock_call_custom.called)

    @mock.patch("entry.tasks.notify_create_entry.delay")
    def test_restore_entry_notify(self, mock_task):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        entry.delete()
        self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")

        self.assertTrue(mock_task.called)

    @patch("entry.tasks.edit_entry_v2.delay", Mock(side_effect=tasks.edit_entry_v2))
    def test_restore_entry_attribute_value(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        attr = self.entity.attrs.get(name="val")
        prev_attrv = entry.attrs.get(schema=attr).get_latest_value()

        # update
        params = {
            "name": "entry-change",
            "attrs": [
                {"id": attr.id, "value": "updated"},
            ],
        }
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # restore to previous value
        resp = self.client.patch(
            "/entry/api/v2/%s/attrv_restore/" % prev_attrv.id, json.dumps({}), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        attrv = entry.attrs.get(schema=attr).get_latest_value()
        self.assertEqual(attrv.value, prev_attrv.value)

    @patch("entry.tasks.edit_entry_v2.delay", Mock(side_effect=tasks.edit_entry_v2))
    def test_restore_entry_attribute_value_all_types(self):
        """Test restoring entry attribute values for all attribute types"""
        # Create entry with all typed attributes
        entry: Entry = self.add_entry(
            self.user,
            "entry",
            self.entity,
            values={
                "val": "initial_string",
                "ref": self.ref_entry.id,
                "name": {"name": "initial_name", "id": self.ref_entry.id},
                "bool": True,
                "date": "2020-01-01",
                "group": self.group.id,
                "groups": [self.group.id],
                "text": "initial_text",
                "vals": ["initial1", "initial2"],
                "nums": [1.1, 2.2],
                "refs": [self.ref_entry.id],
                "names": [
                    {"name": "initial_name1", "id": self.ref_entry.id},
                    {"name": "initial_name2", "id": self.ref_entry.id},
                ],
                "role": self.role.id,
                "roles": [self.role.id],
                "datetime": "2020-01-01T00:00:00",
                "num": 42.0,
            },
        )

        # Store original attribute values for later comparison
        original_values = {}
        for attr_name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr = entry.attrs.get(schema__name=attr_name)
            original_values[attr_name] = attr.get_latest_value()

        # Update all attributes with new values
        attr_schemas = {
            name: self.entity.attrs.get(name=name)
            for name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]
        }

        # Create a second reference entry for updating
        ref_entry2: Entry = self.add_entry(self.user, "r-1", self.ref_entity)
        group2: Group = Group.objects.create(name="group1")
        role2: Role = Role.objects.create(name="role1")

        update_params = {
            "name": "entry-updated",
            "attrs": [
                {"id": attr_schemas["val"].id, "value": "updated_string"},
                {"id": attr_schemas["ref"].id, "value": ref_entry2.id},
                {
                    "id": attr_schemas["name"].id,
                    "value": {"name": "updated_name", "id": ref_entry2.id},
                },
                {"id": attr_schemas["bool"].id, "value": False},
                {"id": attr_schemas["date"].id, "value": "2021-12-31"},
                {"id": attr_schemas["group"].id, "value": group2.id},
                {"id": attr_schemas["groups"].id, "value": [group2.id]},
                {"id": attr_schemas["text"].id, "value": "updated_text"},
                {"id": attr_schemas["vals"].id, "value": ["updated1", "updated2", "updated3"]},
                {"id": attr_schemas["nums"].id, "value": [3.3, 4.4, 5.5]},
                {"id": attr_schemas["refs"].id, "value": [ref_entry2.id]},
                {
                    "id": attr_schemas["names"].id,
                    "value": [
                        {"name": "updated_name1", "id": ref_entry2.id},
                        {"name": "updated_name2", "id": ref_entry2.id},
                        {"name": "updated_name3", "id": ref_entry2.id},
                    ],
                },
                {"id": attr_schemas["role"].id, "value": role2.id},
                {"id": attr_schemas["roles"].id, "value": [role2.id]},
                {"id": attr_schemas["datetime"].id, "value": "2021-12-31T23:59:59"},
                {"id": attr_schemas["num"].id, "value": 84.0},
            ],
        }
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(update_params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Now restore each attribute type and verify the restoration
        failed_attrs = []

        for attr_name, prev_attrv in original_values.items():
            attr = entry.attrs.get(schema__name=attr_name)
            attr_type = attr.schema.type

            try:
                # Restore to previous value
                resp = self.client.patch(
                    "/entry/api/v2/%s/attrv_restore/" % prev_attrv.id,
                    json.dumps({}),
                    "application/json",
                )

                if resp.status_code != 200:
                    failed_attrs.append(f"{attr_name} (type: {attr_type}): HTTP {resp.status_code}")
                    continue

                # Verify the value was restored correctly by comparing get_value() results
                prev_display_value = prev_attrv.get_value(with_metainfo=False)
                restored_value = attr.get_latest_value()
                restored_display_value = restored_value.get_value(with_metainfo=False)

                if prev_display_value != restored_display_value:
                    failed_attrs.append(
                        f"{attr_name} (type: {attr_type}): "
                        f"expected {prev_display_value}, got {restored_display_value}"
                    )

            except Exception as e:
                failed_attrs.append(f"{attr_name} (type: {attr_type}): Exception - {str(e)}")

        # Report all failures at once
        if failed_attrs:
            self.fail(
                f"Restoration failed for {len(failed_attrs)} attributes:\n"
                + "\n".join(f"  - {failure}" for failure in failed_attrs)
            )

    @patch("entry.tasks.edit_entry_v2.delay", Mock(side_effect=tasks.edit_entry_v2))
    def test_restore_entry_attribute_value_with_none_referral(self):
        """Test restoring NamedObject with None referral"""
        # Create entry with NamedObject attribute without referral
        entry: Entry = self.add_entry(
            self.user,
            "entry",
            self.entity,
            values={
                "name": {"name": "name_without_ref", "id": None},
            },
        )

        # Store original value
        name_attr = entry.attrs.get(schema__name="name")
        prev_attrv = name_attr.get_latest_value()

        # Update with a referral
        update_params = {
            "attrs": [
                {
                    "id": self.entity.attrs.get(name="name").id,
                    "value": {"name": "name_with_ref", "id": self.ref_entry.id},
                },
            ],
        }
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(update_params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Restore to previous value (without referral)
        resp = self.client.patch(
            "/entry/api/v2/%s/attrv_restore/" % prev_attrv.id, json.dumps({}), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        # Verify restoration
        restored_value = name_attr.get_latest_value()
        self.assertEqual(restored_value.value, "name_without_ref")
        self.assertIsNone(restored_value.referral)

    @mock.patch("entry.tasks.copy_entry.delay", mock.Mock(side_effect=tasks.copy_entry))
    def test_copy_entry(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        params = {"copy_entry_names": ["copy1", "copy2"]}

        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Entry.objects.filter(name="copy1", schema=self.entity, is_active=True).exists()
        )
        self.assertTrue(
            Entry.objects.filter(name="copy2", schema=self.entity, is_active=True).exists()
        )

    @mock.patch("entry.tasks.copy_entry.delay", mock.Mock(side_effect=tasks.copy_entry))
    def test_copy_entry_for_autoname(self):
        (model_lb, model_sg) = self._create_lb_models_for_autoname()

        item_lb = self.add_entry(self.user, "LB0001", model_lb)
        item_sg = self.add_entry(
            self.user,
            "ChangingName",
            model_sg,
            values={
                "lb": item_lb.id,
                "domain": "test.example.com",
                "port": "10000",
            },
        )
        item_sg.save_autoname()

        # copy 2 Items from item_sg
        params = {"copy_entry_names": ["copy1", "copy2"]}
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % item_sg.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            Entry.objects.filter(name=item_sg.autoname, schema=model_sg, is_active=True).count(), 1
        )
        self.assertEqual(
            Entry.objects.filter(name=item_sg.autoname, schema=model_sg, is_active=True).first().id,
            item_sg.id,
        )
        self.assertEqual(
            Entry.objects.filter(
                name__contains="%s -- duplicate of ID:%s --" % (item_sg.autoname, item_sg.id),
                schema=model_sg,
                is_active=True,
            ).count(),
            2,
        )

    def test_copy_entry_without_permission(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        params = {"copy_entry_names": ["copy1"]}

        # permission nothing entity
        self.entity.is_public = False
        self.entity.save()
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readable entity
        self.role.users.add(self.user)
        self.entity.readable.roles.add(self.role)
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission writable entity
        self.entity.writable.roles.add(self.role)
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        params = {"copy_entry_names": ["copy2"]}

        # permission nothing entry
        entry.is_public = False
        entry.save()
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readable entry
        entry.readable.roles.add(self.role)
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission writable entry
        entry.writable.roles.add(self.role)
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

    def test_copy_entry_with_invalid_param(self):
        params = {"copy_entry_names": ["copy1"]}

        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % "hoge", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 404)

        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % 9999, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Entry matches the given query."}
        )

        entry = self.add_entry(self.user, "entry", self.entity)

        params = {}
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"copy_entry_names": [{"code": "AE-113000", "message": "This field is required."}]},
        )

        params = {"copy_entry_names": "hoge"}
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "copy_entry_names": [
                    {
                        "code": "AE-121000",
                        "message": 'Expected a list of items but got type "str".',
                    }
                ]
            },
        )

        params = {"copy_entry_names": [{}]}
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"copy_entry_names": {"0": [{"code": "AE-121000", "message": "Not a valid string."}]}},
        )

        params = {"copy_entry_names": []}
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"copy_entry_names": [{"code": "AE-123000", "message": "This list may not be empty."}]},
        )

        params = {"copy_entry_names": ["entry"]}
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "copy_entry_names": [
                    {"code": "AE-220000", "message": "specified names(entry) already exists"}
                ]
            },
        )

    @patch("entry.tasks.copy_entry.delay", Mock(side_effect=tasks.copy_entry))
    @mock.patch("airone.lib.custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("airone.lib.custom_view.call_custom")
    def test_copy_entry_with_customview(self, mock_call_custom):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        params = {"copy_entry_names": ["copy1", "copy2"]}

        def side_effect(handler_name, entity_name, user, *args):
            raise ValidationError("copy error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(mock_call_custom.called)

        def side_effect(handler_name, entity_name, user, *args):
            self.assertEqual(entity_name, self.entity.name)
            self.assertEqual(user, self.user)

            # Check specified parameters are expected
            if handler_name == "validate_entry":
                self.assertEqual(args[0], self.entity.name)
                self.assertIn(args[1], params["copy_entry_names"])
                self.assertEqual(args[2], [])
                self.assertIsNone(args[3])

            if handler_name == "after_copy_entry":
                self.assertEqual(args[0], entry)
                self.assertIn(args[1].name, params["copy_entry_names"])
                self.assertEqual(args[2], params)

        mock_call_custom.side_effect = side_effect
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(mock_call_custom.called)
