import datetime
import errno
import json
from datetime import date
from unittest import mock
from unittest.mock import Mock, patch

import yaml
from django.urls import reverse
from rest_framework.exceptions import ValidationError

from airone.lib.test import AironeViewTest
from airone.lib.types import (
    AttrTypeArrNamedObj,
    AttrTypeArrObj,
    AttrTypeArrStr,
    AttrTypeDate,
    AttrTypeNamedObj,
    AttrTypeObj,
    AttrTypeStr,
    AttrTypeText,
    AttrTypeValue,
)
from dashboard import tasks as dashboard_tasks
from entity.models import Entity, EntityAttr
from entry import tasks
from entry import tasks as entry_tasks
from entry.models import Attribute, AttributeValue, Entry
from entry.settings import CONFIG
from group.models import Group
from job.models import Job, JobOperation
from role.models import Role
from user.models import User


class ViewTest(AironeViewTest):
    def _create_user(
        self,
        name,
        email="email",
        is_superuser=False,
        authenticate_type=User.AuthenticateType.AUTH_TYPE_LOCAL,
    ):
        user = User(
            username=name,
            email=email,
            is_superuser=is_superuser,
            authenticate_type=authenticate_type,
        )
        user.set_password(name)
        user.save()

        return user

    def setUp(self):
        super(ViewTest, self).setUp()

        self.user: User = self.guest_login()

        # create Entities, Entries and Group for using this test case
        self.ref_entity: Entity = self.create_entity(self.user, "ref_entity")
        self.ref_entry: Entry = self.add_entry(self.user, "r-0", self.ref_entity)
        self.group: Group = Group.objects.create(name="group0")
        self.role: Role = Role.objects.create(name="role0")

        attrs = []
        for attr_info in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY:
            if attr_info["type"] & AttrTypeValue["object"]:
                attr_info["ref"] = self.ref_entity
            attrs.append(attr_info)
        self.entity: Entity = self.create_entity(
            **{
                "user": self.user,
                "name": "test-entity",
                "attrs": attrs,
            }
        )

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
        optional_attr = EntityAttr.objects.create(
            **{
                "name": "opt",
                "type": AttrTypeValue["string"],
                "is_mandatory": False,
                "parent_entity": self.entity,
                "created_user": self.user,
            }
        )
        self.entity.attrs.add(optional_attr)

        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 200)

        resp_data = resp.json()
        self.assertEqual(resp_data["id"], entry.id)
        self.assertEqual(resp_data["name"], entry.name)
        self.assertEqual(
            resp_data["schema"],
            {"id": entry.schema.id, "name": entry.schema.name, "is_public": entry.schema.is_public},
        )

        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "val", resp_data["attrs"])),
            {
                "type": AttrTypeValue["string"],
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
                "type": AttrTypeValue["object"],
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
                "type": AttrTypeValue["named_object"],
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
                "type": AttrTypeValue["boolean"],
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
                "type": AttrTypeValue["date"],
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
                "type": AttrTypeValue["group"],
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
                "type": AttrTypeValue["array_group"],
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
                "type": AttrTypeValue["role"],
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
                "type": AttrTypeValue["array_role"],
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
                "type": AttrTypeValue["text"],
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
                "type": AttrTypeValue["array_string"],
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
            next(filter(lambda x: x["schema"]["name"] == "refs", resp_data["attrs"])),
            {
                "type": AttrTypeValue["array_object"],
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
                "type": AttrTypeValue["array_named_object"],
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
                "type": AttrTypeValue["string"],
                "value": {"as_string": AttrTypeStr.DEFAULT_VALUE},
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
                "type": AttrTypeValue["string"],
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
                "type": AttrTypeValue["string"],
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
                "type": AttrTypeValue["string"],
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
                "type": AttrTypeValue["string"],
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
        self.assertEqual(resp.json(), {"code": "AE-230000", "message": "Not found."})

    @mock.patch("custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("custom_view.call_custom")
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
                    "type": AttrTypeValue["string"],
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
                "type": AttrTypeValue["string"],
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
            {"id": entry.schema.id, "name": entry.schema.name, "is_public": entry.schema.is_public},
        )

        self.assertEqual(
            next(filter(lambda x: x["schema"]["name"] == "ref", resp_data["attrs"])),
            {
                "type": AttrTypeValue["object"],
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
                "type": AttrTypeValue["named_object"],
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
                "type": AttrTypeValue["array_object"],
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
                "type": AttrTypeValue["array_named_object"],
                "value": {
                    "as_array_named_object": [
                        {
                            "name": "foo",
                            "object": None,
                        },
                        {
                            "name": "bar",
                            "object": None,
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
            ],
        }
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            resp.json(),
            {
                "id": entry.id,
                "name": "entry-change",
            },
        )
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
        self.assertEqual(resp.status_code, 200)

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
        self.assertEqual(resp.status_code, 200)

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
        self.assertEqual(resp.status_code, 200)
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
        self.assertEqual(resp.status_code, 200)
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
        self.assertEqual(resp.json(), {"code": "AE-230000", "message": "Not found."})

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
        self.assertEqual(resp.status_code, 200)

        hoge_entry: Entry = self.add_entry(self.user, "hoge", self.entity)
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps({"name": "hoge"}), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"name": [{"code": "AE-220000", "message": "specified name(hoge) already exists"}]},
        )

        hoge_entry.delete()
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps({"name": "hoge"}), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

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

    @mock.patch("entry.tasks.notify_update_entry.delay")
    def test_update_entry_notify(self, mock_task):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps({"name": "hoge"}), "application/json"
        )

        self.assertTrue(mock_task.called)

    @mock.patch("custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("custom_view.call_custom")
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
        }

        def side_effect(handler_name, entity_name, user, *args):
            raise ValidationError("update error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), [{"code": "AE-121000", "message": "update error"}])

        def side_effect(handler_name, entity_name, user, *args):
            self.assertEqual(entity_name, self.entity.name)
            self.assertEqual(user, self.user)

            # Check specified parameters are expected
            if handler_name == "before_update_entry_v2":
                self.assertEqual(args[0], params)
                return args[0]

            if handler_name == "after_update_entry_v2":
                self.assertEqual(args[0], entry)

        mock_call_custom.side_effect = side_effect
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
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

        ret = Entry.search_entries(self.user, [self.entity.id], [{"name": "ref"}])
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual(ret["ret_values"][0]["entry"]["name"], "Entry")
        self.assertEqual(ret["ret_values"][0]["attrs"]["ref"]["value"]["name"], "ref-change")

    def test_update_entry_without_attrs(self):
        resp = self.client.put(
            "/entry/api/v2/%s/" % self.ref_entry.id, json.dumps({}), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

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
        self.assertEqual(resp.json(), {"code": "AE-230000", "message": "Not found."})

    @mock.patch("custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("custom_view.call_custom")
    def test_destroy_entry_with_custom_view(self, mock_call_custom):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        def side_effect(handler_name, entity_name, user, entry):
            raise ValidationError("delete error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), [{"code": "AE-121000", "message": "delete error"}])

        def side_effect(handler_name, entity_name, user, entry):
            self.assertTrue(handler_name in ["before_delete_entry_v2", "after_delete_entry_v2"])
            self.assertEqual(entity_name, self.entity.name)
            self.assertEqual(user, self.user)
            self.assertEqual(entry, entry)

        mock_call_custom.side_effect = side_effect
        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 204)
        self.assertTrue(mock_call_custom.called)

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
        self.assertEqual(resp.json(), {"code": "AE-230000", "message": "Not found."})

        entry = self.add_entry(self.user, "entry", self.entity)
        entry.delete()
        self.add_entry(self.user, "entry", self.entity)

        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            [{"code": "AE-220000", "message": "specified entry has already exist other"}],
        )

    @mock.patch("custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("custom_view.call_custom")
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
        self.assertEqual(resp.json(), {"code": "AE-230000", "message": "Not found."})

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
                    {"code": "AE-220000", "message": "specified name(entry) already exists"}
                ]
            },
        )

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
                    "group",
                    "groups",
                    "text",
                    "vals",
                    "refs",
                    "names",
                    "role",
                    "roles",
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
                },
                "is_active": True,
                "deleted_user": None,
                "deleted_time": None,
                "updated_time": entry.updated_time.astimezone(self.TZ_INFO).isoformat(),
            },
        )

    def test_referral_unrelated_to_entry(self):
        resp = self.client.get("/entry/api/v2/%s/referral/" % 99999)  # invalid entry id
        self.assertEqual(resp.status_code, 200)

        resp_data = resp.json()
        results = resp_data["results"]
        self.assertEqual(len(results), 0)

    @patch("entry.tasks.export_entries_v2.delay", Mock(side_effect=tasks.export_entries_v2))
    def test_post_export(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="ほげ", created_user=user)
        for name in ["foo", "bar"]:
            entity.attrs.add(
                EntityAttr.objects.create(
                    **{
                        "name": name,
                        "type": AttrTypeValue["string"],
                        "created_user": user,
                        "parent_entity": entity,
                    }
                )
            )

        entry = Entry.objects.create(name="fuga", schema=entity, created_user=user)
        entry.complement_attrs(user)
        for attr in entry.attrs.all():
            [attr.add_value(user, x) for x in ["hoge", "fuga"]]

        resp = self.client.post(
            "/entry/api/v2/%d/export/" % entity.id,
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {"result": "Succeed in registering export processing. Please check Job list."},
        )

        job = Job.objects.last()
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY_V2.value)
        self.assertEqual(job.status, Job.STATUS["DONE"])
        self.assertEqual(job.text, "entry_ほげ.yaml")

        obj = yaml.load(job.get_cache(), Loader=yaml.SafeLoader)

        self.assertEqual(len(obj), 1)
        entity_data = obj[0]
        self.assertEqual(entity_data["entity"], "ほげ")

        self.assertEqual(len(entity_data["entries"]), 1)
        entry_data = entity_data["entries"][0]
        self.assertEqual(entry_data["name"], "fuga")
        self.assertTrue("attrs" in entry_data)

        attrs_data = entry_data["attrs"]
        self.assertTrue(all(["name" in x and "value" in x for x in attrs_data]))
        self.assertEqual(len(attrs_data), entry.attrs.count())
        self.assertEqual(sorted([x["name"] for x in attrs_data]), sorted(["foo", "bar"]))
        self.assertTrue(all([x["value"] == "fuga" for x in attrs_data]))

        resp = self.client.post(
            "/entry/api/v2/%d/export/" % entity.id,
            json.dumps({"format": "CSV"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # append an unpermitted Attribute
        entity.attrs.add(
            EntityAttr.objects.create(
                **{
                    "name": "new_attr",
                    "type": AttrTypeValue["string"],
                    "created_user": user,
                    "parent_entity": entity,
                    "is_public": False,
                }
            )
        )

        # re-login with guest user
        self.guest_login("guest2")

        resp = self.client.post(
            "/entry/api/v2/%d/export/" % entity.id,
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        obj = yaml.load(Job.objects.last().get_cache(), Loader=yaml.SafeLoader)

        # check permitted attributes exist in the result
        self.assertTrue(all([x["name"] in ["foo", "bar"] for x in obj[0]["entries"][0]["attrs"]]))

        # check unpermitted attribute doesn't exist in the result
        self.assertFalse("new_attr" in obj[0]["entries"][0]["attrs"])

        ###
        # Check the case of canceling job
        ###
        with patch.object(Job, "is_canceled", return_value=True):
            resp = self.client.post(
                "/entry/api/v2/%d/export/" % entity.id,
                json.dumps({}),
                "application/json",
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {"result": "Succeed in registering export processing. Please check Job list."},
        )

        job = Job.objects.last()
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY_V2.value)
        self.assertEqual(job.text, "entry_ほげ.yaml")
        with self.assertRaises(OSError) as e:
            raise OSError

        if e.exception.errno == errno.ENOENT:
            job.get_cache()

    @patch("entry.tasks.export_entries_v2.delay", Mock(side_effect=tasks.export_entries_v2))
    def test_post_export_with_referrals(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entity_attr_object = EntityAttr.objects.create(
            **{
                "name": "object",
                "type": AttrTypeValue["object"],
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity_attr_object.referral.add(self.ref_entity)
        entity.attrs.add(entity_attr_object)
        entity_attr_array_object = EntityAttr.objects.create(
            **{
                "name": "array_object",
                "type": AttrTypeValue["array_object"],
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity_attr_array_object.referral.add(self.ref_entity)
        entity.attrs.add(entity_attr_array_object)
        entity_attr_named_object = EntityAttr.objects.create(
            **{
                "name": "named_object",
                "type": AttrTypeValue["named_object"],
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity_attr_named_object.referral.add(self.ref_entity)
        entity.attrs.add(entity_attr_named_object)
        entity_attr_named_object_without_key = EntityAttr.objects.create(
            **{
                "name": "named_object_without_key",
                "type": AttrTypeValue["named_object"],
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity_attr_named_object_without_key.referral.add(self.ref_entity)
        entity.attrs.add(entity_attr_named_object_without_key)
        entity_attr_array_named_object = EntityAttr.objects.create(
            **{
                "name": "array_named_object",
                "type": AttrTypeValue["array_named_object"],
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity_attr_array_named_object.referral.add(self.ref_entity)
        entity.attrs.add(entity_attr_array_named_object)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.attrs.get(name="object").add_value(self.user, self.ref_entry.id)
        entry.attrs.get(name="array_object").add_value(self.user, [self.ref_entry.id])
        entry.attrs.get(name="named_object").add_value(
            self.user, {"id": self.ref_entry.id, "name": "name1"}
        )
        entry.attrs.get(name="named_object_without_key").add_value(
            self.user, {"id": self.ref_entry.id, "name": ""}
        )
        entry.attrs.get(name="array_named_object").add_value(
            self.user,
            [{"id": self.ref_entry.id, "name": "name1"}, {"id": self.ref_entry.id, "name": ""}],
        )

        # delete referred entry
        self.ref_entry.delete()

        resp = self.client.post(
            "/entry/api/v2/%d/export/" % entity.id,
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {"result": "Succeed in registering export processing. Please check Job list."},
        )

        job = Job.objects.last()
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY_V2.value)
        self.assertEqual(job.status, Job.STATUS["DONE"])

        obj = yaml.load(job.get_cache(), Loader=yaml.SafeLoader)

        self.assertEqual(len(obj), 1)
        entity_data = obj[0]
        self.assertEqual(entity_data["entity"], "entity")

        self.assertEqual(len(entity_data["entries"]), 1)
        entry_data = entity_data["entries"][0]
        self.assertEqual(entry_data["name"], "entry")
        self.assertTrue("attrs" in entry_data)

        attrs_data = entry_data["attrs"]
        self.assertTrue(all(["name" in x and "value" in x for x in attrs_data]))
        self.assertEqual(len(attrs_data), entry.attrs.count())

        # object related typed value refers deleted entry follows the rule:
        # on object type, value must be None
        # on array-object type, value must not have the element
        # on named-object type, value must be {"<name>": None}
        # on array-named-object type, value must not have the element
        self.assertEqual(
            sorted(attrs_data, key=lambda e: e["name"]),
            sorted(
                [
                    {"name": "object", "value": None},
                    {"name": "array_object", "value": []},
                    {"name": "named_object", "value": {"name1": None}},
                    {"name": "named_object_without_key", "value": {}},
                    {"name": "array_named_object", "value": [{"name1": None}]},
                ],
                key=lambda e: e["name"],
            ),
        )

        resp = self.client.post(
            "/entry/api/v2/%d/export/" % entity.id,
            json.dumps({"format": "CSV"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

    @patch("entry.tasks.export_entries_v2.delay", Mock(side_effect=tasks.export_entries_v2))
    def test_get_export_csv_escape(self):
        user = self.admin_login()

        dummy_entity = Entity.objects.create(name="Dummy", created_user=user)
        dummy_entry = Entry(name='D,U"MM"Y', schema=dummy_entity, created_user=user)
        dummy_entry.save()

        CASES = [
            [AttrTypeStr, 'raison,de"tre', '"raison,de""tre"'],
            [AttrTypeObj, dummy_entry, '"D,U""MM""Y"'],
            [AttrTypeText, "1st line\r\n2nd line", '"1st line' + "\r\n" + '2nd line"'],
            [AttrTypeNamedObj, {"key": dummy_entry}, '"{\'key\': \'D,U""MM""Y\'}"'],
            [AttrTypeArrStr, ["one", "two", "three"], "\"['one', 'two', 'three']\""],
            [AttrTypeArrObj, [dummy_entry], '"[\'D,U""MM""Y\']"'],
            [
                AttrTypeArrNamedObj,
                [{"key1": dummy_entry}],
                '"[{\'key1\': \'D,U""MM""Y\'}]"',
            ],
        ]

        for case in CASES:
            type_name = case[0].__name__  # AttrTypeStr -> 'AttrTypeStr'
            attr_name = type_name + ',"ATTR"'

            test_entity = Entity.objects.create(name="TestEntity_" + type_name, created_user=user)

            test_entity_attr = EntityAttr.objects.create(
                name=attr_name,
                type=case[0],
                created_user=user,
                parent_entity=test_entity,
            )

            test_entity.attrs.add(test_entity_attr)
            test_entity.save()

            test_entry = Entry.objects.create(
                name=type_name + ',"ENTRY"', schema=test_entity, created_user=user
            )
            test_entry.save()

            test_attr = Attribute.objects.create(
                name=attr_name,
                schema=test_entity_attr,
                created_user=user,
                parent_entry=test_entry,
            )

            test_attr.save()
            test_entry.attrs.add(test_attr)
            test_entry.save()

            test_val = None

            if case[0].TYPE & AttrTypeValue["array"] == 0:
                if case[0] == AttrTypeStr:
                    test_val = AttributeValue.create(user=user, attr=test_attr, value=case[1])
                elif case[0] == AttrTypeObj:
                    test_val = AttributeValue.create(user=user, attr=test_attr, referral=case[1])
                elif case[0] == AttrTypeText:
                    test_val = AttributeValue.create(user=user, attr=test_attr, value=case[1])
                elif case[0] == AttrTypeNamedObj:
                    [(k, v)] = case[1].items()
                    test_val = AttributeValue.create(user=user, attr=test_attr, value=k, referral=v)
            else:
                test_val = AttributeValue.create(user=user, attr=test_attr)
                test_val.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
                for child in case[1]:
                    test_val_child = None
                    if case[0] == AttrTypeArrStr:
                        test_val_child = AttributeValue.create(
                            user=user, attr=test_attr, value=child
                        )
                    elif case[0] == AttrTypeArrObj:
                        test_val_child = AttributeValue.create(
                            user=user, attr=test_attr, referral=child
                        )
                    elif case[0] == AttrTypeArrNamedObj:
                        [(k, v)] = child.items()
                        test_val_child = AttributeValue.create(
                            user=user, attr=test_attr, value=k, referral=v
                        )
                    test_val.data_array.add(test_val_child)

            test_val.save()
            test_attr.values.add(test_val)
            test_attr.save()

            resp = self.client.post(
                "/entry/api/v2/%d/export/" % test_entity.id,
                json.dumps({"format": "CSV"}),
                "application/json",
            )
            self.assertEqual(resp.status_code, 200)

            content = Job.objects.last().get_cache()
            header = content.splitlines()[0]
            self.assertEqual(header, 'Name,"%s,""ATTR"""' % type_name)

            data = content.replace(header, "", 1).strip()
            self.assertEqual(data, '"%s,""ENTRY""",' % type_name + case[2])

    def test_get_attr_referrals_of_role(self):
        entity = self.create_entity(
            self.user,
            "Entity",
            attrs=[
                {"name": "role", "type": AttrTypeValue["role"]},
                {"name": "roles", "type": AttrTypeValue["array_role"]},
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
            entity.attrs.add(
                EntityAttr.objects.create(
                    **{
                        "name": name,
                        "type": AttrTypeValue[type_index],
                        "created_user": user,
                        "parent_entity": entity,
                    }
                )
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
                "type": AttrTypeValue["object"],
                "created_user": admin,
                "parent_entity": entity,
            }
        )

        entity_attr.referral.add(ref_entity)
        entity.attrs.add(entity_attr)

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
                "type": AttrTypeValue["named_object"],
                "created_user": admin,
                "parent_entity": entity,
            }
        )
        entity_attr.referral.add(ref_entity)
        entity.attrs.add(entity_attr)

        resp = self.client.get(
            "/entry/api/v2/%d/attr_referrals/" % entity_attr.id, {"keyword": "e-1"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")

        # This means e-1 and 'e-10' to 'e-19' are returned
        self.assertEqual(len(resp.json()), 11)

    @patch("entry.tasks.notify_create_entry.delay", Mock(side_effect=tasks.notify_create_entry))
    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_create_entry(self):
        fp = self.open_fixture_file("import_data_v2.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job = Job.objects.get(operation=JobOperation.IMPORT_ENTRY_V2.value)
        self.assertEqual(job.status, Job.STATUS["DONE"])
        self.assertEqual(job.text, "Imported Entry count: 1")
        self.assertEqual(
            resp.json(),
            {
                "result": {
                    "error": [],
                    "job_ids": [job.id],
                }
            },
        )

        result = Entry.search_entries(self.user, [self.entity.id], is_output_all=True)
        self.assertEqual(result["ret_count"], 1)
        self.assertEqual(result["ret_values"][0]["entry"]["name"], "test-entry")
        self.assertEqual(result["ret_values"][0]["entity"]["name"], "test-entity")
        attrs = {
            "bool": True,
            "date": "2018-12-31",
            "group": {"id": self.group.id, "name": "group0"},
            "groups": [{"id": self.group.id, "name": "group0"}],
            "name": {"foo": {"id": self.ref_entry.id, "name": "r-0"}},
            "names": [{"foo": {"id": self.ref_entry.id, "name": "r-0"}}],
            "ref": {"id": self.ref_entry.id, "name": "r-0"},
            "refs": [{"id": self.ref_entry.id, "name": "r-0"}],
            "text": "foo\nbar",
            "val": "foo",
            "vals": ["foo"],
            "role": {"id": self.role.id, "name": "role0"},
            "roles": [{"id": self.role.id, "name": "role0"}],
        }
        for attr_name in result["ret_values"][0]["attrs"]:
            self.assertEqual(result["ret_values"][0]["attrs"][attr_name]["value"], attrs[attr_name])

        entry = Entry.objects.get(name="test-entry")
        job_notify = Job.objects.get(target=entry, operation=JobOperation.NOTIFY_CREATE_ENTRY.value)
        self.assertEqual(job_notify.status, Job.STATUS["DONE"])

    @patch("entry.tasks.notify_update_entry.delay", Mock(side_effect=tasks.notify_update_entry))
    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_update_entry(self):
        entry = self.add_entry(self.user, "test-entry", self.entity)
        fp = self.open_fixture_file("import_data_v2.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job = Job.objects.get(operation=JobOperation.IMPORT_ENTRY_V2.value)
        self.assertEqual(job.status, Job.STATUS["DONE"])

        result = Entry.search_entries(self.user, [self.entity.id], is_output_all=True)
        self.assertEqual(result["ret_count"], 1)
        self.assertEqual(result["ret_values"][0]["entry"], {"id": entry.id, "name": "test-entry"})
        attrs = {
            "val": "foo",
            "vals": ["foo"],
            "ref": {"id": self.ref_entry.id, "name": "r-0"},
            "refs": [{"id": self.ref_entry.id, "name": "r-0"}],
            "name": {"foo": {"id": self.ref_entry.id, "name": "r-0"}},
            "names": [{"foo": {"id": self.ref_entry.id, "name": "r-0"}}],
            "group": {"id": self.group.id, "name": "group0"},
            "groups": [{"id": self.group.id, "name": "group0"}],
            "bool": True,
            "text": "foo\nbar",
            "date": "2018-12-31",
            "role": {"id": self.role.id, "name": "role0"},
            "roles": [{"id": self.role.id, "name": "role0"}],
        }
        for attr_name in result["ret_values"][0]["attrs"]:
            self.assertEqual(result["ret_values"][0]["attrs"][attr_name]["value"], attrs[attr_name])

        job_notify = Job.objects.get(target=entry, operation=JobOperation.NOTIFY_UPDATE_ENTRY.value)
        self.assertEqual(job_notify.status, Job.STATUS["DONE"])

        # Update only some attributes
        fp = self.open_fixture_file("import_data_v2_update_some.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job = Job.objects.filter(operation=JobOperation.IMPORT_ENTRY_V2.value).last()
        self.assertEqual(job.status, Job.STATUS["DONE"])

        result = Entry.search_entries(self.user, [self.entity.id], is_output_all=True)
        attrs["val"] = "bar"
        for attr_name in result["ret_values"][0]["attrs"]:
            self.assertEqual(result["ret_values"][0]["attrs"][attr_name]["value"], attrs[attr_name])

        # Update remove attribute value
        fp = self.open_fixture_file("import_data_v2_update_remove.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job = Job.objects.filter(operation=JobOperation.IMPORT_ENTRY_V2.value).last()
        self.assertEqual(job.status, Job.STATUS["DONE"])

        result = Entry.search_entries(self.user, [self.entity.id], is_output_all=True)
        attrs = {
            "val": "",
            "vals": [],
            "ref": {"id": "", "name": ""},
            "refs": [],
            "name": {"": {"id": "", "name": ""}},
            "names": [],
            "group": {"id": "", "name": ""},
            "groups": [],
            "bool": False,
            "text": "",
            "date": None,
            "role": {"id": "", "name": ""},
            "roles": [],
        }
        for attr_name in result["ret_values"][0]["attrs"]:
            if "value" in result["ret_values"][0]["attrs"][attr_name]:
                self.assertEqual(
                    result["ret_values"][0]["attrs"][attr_name]["value"], attrs[attr_name]
                )

    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_multi_entity(self):
        entity1 = self.create_entity(self.user, "test-entity1")
        entity2 = self.create_entity(self.user, "test-entity2")
        fp = self.open_fixture_file("import_data_v2_multi_entity.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job1 = Job.objects.get(target=entity1, operation=JobOperation.IMPORT_ENTRY_V2.value)
        job2 = Job.objects.get(target=entity2, operation=JobOperation.IMPORT_ENTRY_V2.value)
        self.assertEqual(job1.text, "Imported Entry count: 1")
        self.assertEqual(job2.text, "Imported Entry count: 1")
        self.assertEqual(
            resp.json(),
            {
                "result": {
                    "error": [],
                    "job_ids": [job1.id, job2.id],
                }
            },
        )

        result = Entry.search_entries(self.user, [entity1.id, entity2.id])
        self.assertEqual(result["ret_count"], 2)
        self.assertEqual(result["ret_values"][0]["entry"]["name"], "test-entry1")
        self.assertEqual(result["ret_values"][0]["entity"]["name"], "test-entity1")
        self.assertEqual(result["ret_values"][1]["entry"]["name"], "test-entry2")
        self.assertEqual(result["ret_values"][1]["entity"]["name"], "test-entity2")

    @patch("entry.tasks.notify_create_entry.delay", Mock(side_effect=tasks.notify_create_entry))
    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_entry_has_referrals_with_entities(self):
        fp = self.open_fixture_file("import_data_v2_with_entities.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job = Job.objects.get(operation=JobOperation.IMPORT_ENTRY_V2.value)
        self.assertEqual(job.status, Job.STATUS["DONE"])
        self.assertEqual(job.text, "Imported Entry count: 1")
        self.assertEqual(
            resp.json(),
            {
                "result": {
                    "error": [],
                    "job_ids": [job.id],
                }
            },
        )

        result = Entry.search_entries(self.user, [self.entity.id], is_output_all=True)
        self.assertEqual(result["ret_count"], 1)
        self.assertEqual(result["ret_values"][0]["entry"]["name"], "test-entry")
        self.assertEqual(result["ret_values"][0]["entity"]["name"], "test-entity")
        attrs = {
            "bool": True,
            "date": "2018-12-31",
            "group": {"id": self.group.id, "name": "group0"},
            "groups": [{"id": self.group.id, "name": "group0"}],
            "name": {"foo": {"id": self.ref_entry.id, "name": "r-0"}},
            "names": [{"foo": {"id": self.ref_entry.id, "name": "r-0"}}],
            "ref": {"id": self.ref_entry.id, "name": "r-0"},
            "refs": [{"id": self.ref_entry.id, "name": "r-0"}],
            "text": "foo\nbar",
            "val": "foo",
            "vals": ["foo"],
            "role": {"id": self.role.id, "name": "role0"},
            "roles": [{"id": self.role.id, "name": "role0"}],
        }
        for attr_name in result["ret_values"][0]["attrs"]:
            self.assertEqual(result["ret_values"][0]["attrs"][attr_name]["value"], attrs[attr_name])

        entry = Entry.objects.get(name="test-entry")
        job_notify = Job.objects.get(target=entry, operation=JobOperation.NOTIFY_CREATE_ENTRY.value)
        self.assertEqual(job_notify.status, Job.STATUS["DONE"])

    def test_import_invalid_data(self):
        # nothing data
        resp = self.client.post("/entry/api/v2/import/", None, "application/yaml")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "non_field_errors": [
                    {
                        "code": "AE-121000",
                        "message": "Expected a list of items but got type " '"dict".',
                    }
                ]
            },
        )

        # wrong content-type
        fp = self.open_fixture_file("import_data_v2.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/json")
        fp.close()
        self.assertEqual(resp.status_code, 415)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-130000",
                "message": 'Unsupported media type "application/json" in request.',
            },
        )

        # faild parse yaml
        fp = self.open_fixture_file("import_data_v2_failed_parse.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["code"], "AE-140000")
        self.assertTrue("YAML parse error" in resp.json()["message"])

        # faild scan yaml
        fp = self.open_fixture_file("import_data_v2_failed_scan.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["code"], "AE-140000")
        self.assertTrue("YAML parse error" in resp.json()["message"])

        # invalid param
        fp = self.open_fixture_file("import_data_v2_invalid_param.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()
        self.assertEqual(resp.status_code, 400)

        # invalid required param (entity, entries)
        self.assertEqual(
            resp.json()[0],
            {
                "entity": [{"code": "AE-113000", "message": "This field is required."}],
                "entries": [{"code": "AE-113000", "message": "This field is required."}],
            },
        )

        # invalid type param (entity, entries)
        self.assertEqual(
            resp.json()[1],
            {
                "entity": [{"code": "AE-121000", "message": "Not a valid string."}],
                "entries": [
                    {
                        "code": "AE-121000",
                        "message": 'Expected a list of items but got type "str".',
                    }
                ],
            },
        )

        # invalid type param (entries)
        self.assertEqual(
            resp.json()[2]["entries"]["0"],
            {
                "non_field_errors": [
                    {
                        "code": "AE-121000",
                        "message": "Invalid data. Expected a dictionary, but got str.",
                    }
                ]
            },
        )

        # invalid required param (entries)
        self.assertEqual(
            resp.json()[2]["entries"]["1"],
            {"name": [{"code": "AE-113000", "message": "This field is required."}]},
        )

        # invalid type param (name, attrs)
        self.assertEqual(
            resp.json()[2]["entries"]["2"],
            {
                "attrs": [
                    {
                        "code": "AE-121000",
                        "message": 'Expected a list of items but got type "str".',
                    }
                ],
                "name": [{"code": "AE-121000", "message": "Not a valid string."}],
            },
        )

        # invalid type param (attrs)
        self.assertEqual(
            resp.json()[2]["entries"]["3"]["attrs"]["0"],
            {
                "non_field_errors": [
                    {
                        "code": "AE-121000",
                        "message": "Invalid data. Expected a dictionary, but got str.",
                    }
                ]
            },
        )

        # invalid required param (name, value)
        self.assertEqual(
            resp.json()[2]["entries"]["3"]["attrs"]["1"],
            {
                "name": [{"code": "AE-113000", "message": "This field is required."}],
                "value": [{"code": "AE-113000", "message": "This field is required."}],
            },
        )

        # invalid type param (name)
        self.assertEqual(
            resp.json()[2]["entries"]["3"]["attrs"]["2"]["name"],
            [{"code": "AE-121000", "message": "Not a valid string."}],
        )

    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_invalid_data_value(self):
        fp = self.open_fixture_file("import_data_v2_invalid_value.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()
        job_id = resp.json()["result"]["job_ids"][0]
        job = Job.objects.get(id=job_id)
        self.assertEqual(job.status, Job.STATUS["WARNING"])
        self.assertTrue("Imported Entry count: 17" in job.text)

    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_invalid_data_entity(self):
        # not exsits entity
        fp = self.open_fixture_file("import_data_v2_invalid_entity.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json()["result"], {"job_ids": [], "error": ["no-entity: Entity does not exists."]}
        )

        # permission nothing entity
        self.entity.is_public = False
        self.entity.save()
        fp = self.open_fixture_file("import_data_v2.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json()["result"],
            {"job_ids": [], "error": ["test-entity: Entity is permission denied."]},
        )

        # permission readble entity
        self.role.users.add(self.user)
        self.entity.readable.roles.add(self.role)
        fp = self.open_fixture_file("import_data_v2.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json()["result"],
            {"job_ids": [], "error": ["test-entity: Entity is permission denied."]},
        )

        # permission writable entity
        self.role.users.add(self.user)
        self.entity.writable.roles.add(self.role)
        fp = self.open_fixture_file("import_data_v2.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()
        self.assertEqual(resp.status_code, 200)
        job = Job.objects.get(target=self.entity, operation=JobOperation.IMPORT_ENTRY_V2.value)
        self.assertEqual(resp.json()["result"], {"job_ids": [job.id], "error": []})

    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_warning(self):
        fp = self.open_fixture_file("import_data_v2_warning.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job_id = resp.json()["result"]["job_ids"][0]
        job = Job.objects.get(id=job_id)
        self.assertEqual(job.status, Job.STATUS["WARNING"])
        self.assertEqual(job.text, "Imported Entry count: 2, Failed import Entry: ['test-entry1']")
        self.assertTrue(Entry.objects.filter(name="test-entry2").exists())

    @patch.object(Job, "is_canceled", Mock(return_value=True))
    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_cancel(self):
        fp = self.open_fixture_file("import_data_v2.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job_id = resp.json()["result"]["job_ids"][0]
        job = Job.objects.get(id=job_id)
        self.assertEqual(job.status, Job.STATUS["CANCELED"])
        self.assertEqual(job.text, "Now importing... (progress: [    1/    1])")
        self.assertFalse(Entry.objects.filter(name="test-entry").exists())

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
                                        "hoge": {"id": self.ref_entry.id, "name": "r-0"}
                                    }
                                },
                            },
                            "names": {
                                "is_readable": True,
                                "type": 3073,
                                "value": {
                                    "as_array_named_object": [
                                        {"foo": {"id": self.ref_entry.id, "name": "r-0"}},
                                        {"bar": {"id": self.ref_entry.id, "name": "r-0"}},
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
                        },
                        "is_readable": True,
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
                                "value": {"as_named_object": {"": {"id": "", "name": ""}}},
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
                        },
                        "is_readable": True,
                    },
                ],
            },
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

    def test_advanced_search_with_too_long_entry_name(self):
        params = {
            "entities": [],
            "entry_name": "a" * (CONFIG.MAX_QUERY_SIZE + 1),
            "is_all_entities": True,
            "attrinfo": [],
        }

        resp = self.client.post(
            "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

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
        self.assertEqual(resp.status_code, 200)

        # restore to previous value
        resp = self.client.patch(
            "/entry/api/v2/%s/attrv_restore/" % prev_attrv.id, json.dumps({}), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        attrv = entry.attrs.get(schema=attr).get_latest_value()
        self.assertEqual(attrv.value, prev_attrv.value)

    @patch(
        "dashboard.tasks.export_search_result.delay",
        Mock(side_effect=dashboard_tasks.export_search_result),
    )
    def test_export_advanced_search_result(self):
        user = self._create_user("admin", is_superuser=True)

        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="ref_entry", schema=ref_entity, created_user=user)
        grp_entry = Group.objects.create(name="group_entry")
        role_entry = Role.objects.create(name="role_entry")
        attr_info = {
            "str": {"type": AttrTypeValue["string"], "value": "foo"},
            "text": {"type": AttrTypeValue["text"], "value": "foo"},
            "bool": {"type": AttrTypeValue["boolean"], "value": True},
            "date": {"type": AttrTypeValue["date"], "value": "2020-01-01"},
            "obj": {"type": AttrTypeValue["object"], "value": ref_entry},
            "grp": {"type": AttrTypeValue["group"], "value": grp_entry},
            "role": {"type": AttrTypeValue["role"], "value": role_entry},
            "name": {
                "type": AttrTypeValue["named_object"],
                "value": {"name": "bar", "id": ref_entry.id},
            },
            "arr_str": {"type": AttrTypeValue["array_string"], "value": ["foo"]},
            "arr_obj": {"type": AttrTypeValue["array_object"], "value": [ref_entry]},
            "arr_grp": {"type": AttrTypeValue["array_group"], "value": [grp_entry]},
            "arr_role": {"type": AttrTypeValue["array_role"], "value": [role_entry]},
            "arr_name": {
                "type": AttrTypeValue["array_named_object"],
                "value": [{"name": "hoge", "id": ref_entry.id}],
            },
        }

        entity = Entity.objects.create(name="Entity", created_user=user)
        for attr_name, info in attr_info.items():
            entity.attrs.add(
                EntityAttr.objects.create(
                    **{
                        "name": attr_name,
                        "type": info["type"],
                        "created_user": user,
                        "parent_entity": entity,
                    }
                )
            )

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        for attr_name, info in attr_info.items():
            attr = entry.attrs.get(schema__name=attr_name)
            attr.add_value(user, info["value"])

        # register entry information to the index database
        entry.register_es()

        exporting_attrs = [
            {"name": "str", "value": "foo"},
            {"name": "text", "value": "foo"},
            {"name": "bool", "value": "True"},
            {"name": "date", "value": "2020-01-01"},
            {"name": "obj", "value": "ref_entry"},
            {"name": "grp", "value": "group_entry"},
            {"name": "role", "value": "role_entry"},
            {"name": "name", "value": "bar: ref_entry"},
            {"name": "arr_str", "value": "foo"},
            {"name": "arr_obj", "value": "ref_entry"},
            {"name": "arr_grp", "value": "group_entry"},
            {"name": "arr_role", "value": "role_entry"},
            {"name": "arr_name", "value": "hoge: ref_entry"},
        ]

        # test to export_search_result without mandatory params
        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "attrinfo": [{"name": x["name"]} for x in exporting_attrs],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("entities", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("attrinfo", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"name": x["name"]} for x in exporting_attrs],
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("export_style", resp.json())

        # test to export_search_result with invalid params
        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": "hoge",
                    "attrinfo": [{"name": x["name"]} for x in exporting_attrs],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("entities", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [{"key": "value"}],
                    "attrinfo": [{"name": x["name"]} for x in exporting_attrs],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("entities", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": ["hoge"],
                    "attrinfo": [{"name": x["name"]} for x in exporting_attrs],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("entities", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [9999],
                    "attrinfo": [{"name": x["name"]} for x in exporting_attrs],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("entities", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": "hoge",
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("attrinfo", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": ["hoge"],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("attrinfo", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"hoge": "value"}],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("attrinfo", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"name": ["hoge"]}],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("attrinfo", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"name": "hoge", "keyword": ["hoge"]}],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("attrinfo", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"name": x["name"]} for x in exporting_attrs],
                    "export_style": "hoge",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("export_style", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"name": x["name"]} for x in exporting_attrs],
                    "export_style": "csv",
                    "entry_name": [],
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("entry_name", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"name": x["name"]} for x in exporting_attrs],
                    "export_style": "csv",
                    "has_referral": "hoge",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("has_referral", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"name": x["name"]} for x in exporting_attrs],
                    "export_style": "csv",
                    "referral_name": [],
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("referral_name", resp.json())

        # test to show advanced_search_result page with large param
        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"name": "attr"}],
                    "export_style": "csv",
                    "entry_name": "a" * 250,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("entry_name", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"name": "attr", "keyword": "a" * 250}],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("attrinfo", resp.json())

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"name": "attr"}],
                    "export_style": "csv",
                    "entry_name": "a" * 249,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"name": "attr", "keyword": "a" * 249}],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # send request to export data
        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [{"name": x["name"]} for x in exporting_attrs],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # verifying result has referral entry's infomations
        csv_contents = [x for x in Job.objects.last().get_cache().splitlines() if x]

        # checks all attribute are exported in order of specified sequence
        self.assertEqual(
            csv_contents[0], "Name,Entity,%s" % ",".join([x["name"] for x in exporting_attrs])
        )

        # checks all data value are exported
        self.assertEqual(
            csv_contents[1], "entry,Entity,%s" % ",".join([x["value"] for x in exporting_attrs])
        )

    @patch(
        "dashboard.tasks.export_search_result.delay",
        Mock(side_effect=dashboard_tasks.export_search_result),
    )
    def test_export_advanced_search_result_with_referral(self):
        user = self._create_user("admin", is_superuser=True)

        # initialize Entities
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        entity = Entity.objects.create(name="entity", created_user=user)
        entity_attr = EntityAttr.objects.create(
            name="attr_ref",
            type=AttrTypeValue["object"],
            created_user=user,
            parent_entity=entity,
        )
        entity_attr.referral.add(ref_entity)
        entity.attrs.add(entity_attr)

        # initialize Entries
        ref_entry = Entry.objects.create(name="ref", schema=ref_entity, created_user=user)
        ref_entry.register_es()

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.attrs.first().add_value(user, ref_entry)
        entry.register_es()

        # export with 'has_referral' parameter which has blank value
        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [ref_entity.id],
                    "attrinfo": [],
                    "has_referral": True,
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # verifying result has referral entry's infomations
        csv_contents = [x for x in Job.objects.last().get_cache().splitlines() if x]
        self.assertEqual(len(csv_contents), 2)
        self.assertEqual(csv_contents[0], "Name,Entity,Referral")
        self.assertEqual(csv_contents[1], "ref,Referred Entity,['entry / entity']")

        # export with 'has_referral' parameter which has invalid value
        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [ref_entity.id],
                    "attrinfo": [],
                    "has_referral": True,
                    "referral_name": "hogefuga",
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        csv_contents = [x for x in Job.objects.last().get_cache().splitlines() if x]
        self.assertEqual(len(csv_contents), 1)

    @patch(
        "dashboard.tasks.export_search_result.delay",
        Mock(side_effect=dashboard_tasks.export_search_result),
    )
    def test_export_advanced_search_result_with_no_permission(self):
        admin = self._create_user("admin", is_superuser=True)

        entry = Entry.objects.create(name="private", schema=self.entity, created_user=admin)
        entry.is_public = False
        entry.save(update_fields=["is_public"])
        entry.register_es()

        self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [self.entity.id],
                    "attrinfo": [{"name": "text"}],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )

        csv_contents = [x for x in Job.objects.last().get_cache().splitlines() if x]
        self.assertEqual(csv_contents[0], "Name,Entity,text")
        self.assertEqual(csv_contents[1], "private,test-entity,")

    @patch(
        "dashboard.tasks.export_search_result.delay",
        Mock(side_effect=dashboard_tasks.export_search_result),
    )
    def test_show_advanced_search_results_csv_escape(self):
        user = self._create_user("admin", is_superuser=True)

        dummy_entity = Entity.objects.create(name="Dummy", created_user=user)
        dummy_entry = Entry(name='D,U"MM"Y', schema=dummy_entity, created_user=user)
        dummy_entry.save()

        CASES = [
            [AttrTypeStr, 'raison,de"tre', '"raison,de""tre"'],
            [AttrTypeObj, dummy_entry, '"D,U""MM""Y"'],
            [AttrTypeText, "1st line\r\n2nd line", '"1st line' + "\r\n" + '2nd line"'],
            [AttrTypeNamedObj, {"key": dummy_entry}, '"key: D,U""MM""Y"'],
            [AttrTypeArrStr, ["one", "two", "three"], '"one\nthree\ntwo"'],
            [AttrTypeArrObj, [dummy_entry], '"D,U""MM""Y"'],
            [AttrTypeArrNamedObj, [{"key1": dummy_entry}], '"key1: D,U""MM""Y"'],
        ]

        for case in CASES:
            # setup data
            type_name = case[0].__name__  # AttrTypeStr -> 'AttrTypeStr'
            attr_name = type_name + ',"ATTR"'

            test_entity = Entity.objects.create(name="TestEntity_" + type_name, created_user=user)

            test_entity_attr = EntityAttr.objects.create(
                name=attr_name,
                type=case[0],
                created_user=user,
                parent_entity=test_entity,
            )

            test_entity.attrs.add(test_entity_attr)
            test_entity.save()

            test_entry = Entry.objects.create(
                name=type_name + ',"ENTRY"', schema=test_entity, created_user=user
            )
            test_entry.save()

            test_attr = Attribute.objects.create(
                name=attr_name,
                schema=test_entity_attr,
                created_user=user,
                parent_entry=test_entry,
            )

            test_attr.save()
            test_entry.attrs.add(test_attr)
            test_entry.save()

            test_val = None

            if case[0].TYPE & AttrTypeValue["array"] == 0:
                if case[0] == AttrTypeStr:
                    test_val = AttributeValue.create(user=user, attr=test_attr, value=case[1])
                elif case[0] == AttrTypeObj:
                    test_val = AttributeValue.create(user=user, attr=test_attr, referral=case[1])
                elif case[0] == AttrTypeText:
                    test_val = AttributeValue.create(user=user, attr=test_attr, value=case[1])
                elif case[0] == AttrTypeNamedObj:
                    [(k, v)] = case[1].items()
                    test_val = AttributeValue.create(user=user, attr=test_attr, value=k, referral=v)
            else:
                test_val = AttributeValue.create(user=user, attr=test_attr)
                test_val.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
                for child in case[1]:
                    test_val_child = None
                    if case[0] == AttrTypeArrStr:
                        test_val_child = AttributeValue.create(
                            user=user, attr=test_attr, value=child
                        )
                    elif case[0] == AttrTypeArrObj:
                        test_val_child = AttributeValue.create(
                            user=user, attr=test_attr, referral=child
                        )
                    elif case[0] == AttrTypeArrNamedObj:
                        [(k, v)] = child.items()
                        test_val_child = AttributeValue.create(
                            user=user, attr=test_attr, value=k, referral=v
                        )
                    test_val.data_array.add(test_val_child)

            test_val.save()
            test_attr.values.add(test_val)
            test_attr.save()

            test_entry.register_es()

            resp = self.client.post(
                "/entry/api/v2/advanced_search_result_export/",
                json.dumps(
                    {
                        "entities": [test_entity.id],
                        "attrinfo": [{"name": test_attr.name, "keyword": ""}],
                        "export_style": "csv",
                    }
                ),
                "application/json",
            )
            self.assertEqual(resp.status_code, 200)

            content = Job.objects.last().get_cache()
            header = content.splitlines()[0]
            self.assertEqual(header, 'Name,Entity,"%s,""ATTR"""' % type_name)

            data = content.replace(header, "", 1).strip()
            self.assertEqual(data, '"%s,""ENTRY""",%s,%s' % (type_name, test_entity.name, case[2]))

    @patch("entry.tasks.import_entries.delay", Mock(side_effect=entry_tasks.import_entries))
    @patch(
        "dashboard.tasks.export_search_result.delay",
        Mock(side_effect=dashboard_tasks.export_search_result),
    )
    def test_yaml_export(self):
        user = self.admin_login()

        # create entity
        entity_ref = Entity.objects.create(name="RefEntity", created_user=user)
        entry_ref = Entry.objects.create(name="ref", schema=entity_ref, created_user=user)
        entry_group = Group.objects.create(name="group")
        entry_role = Role.objects.create(name="role")

        attr_info = {
            "str": {
                "type": AttrTypeValue["string"],
                "value": "foo",
                "invalid_values": [123, entry_ref, True],
            },
            "obj": {"type": AttrTypeValue["object"], "value": str(entry_ref.id)},
            "name": {
                "type": AttrTypeValue["named_object"],
                "value": {"name": "bar", "id": str(entry_ref.id)},
            },
            "bool": {"type": AttrTypeValue["boolean"], "value": False},
            "arr_str": {
                "type": AttrTypeValue["array_string"],
                "value": ["foo", "bar", "baz"],
            },
            "arr_obj": {
                "type": AttrTypeValue["array_object"],
                "value": [str(entry_ref.id)],
            },
            "arr_name": {
                "type": AttrTypeValue["array_named_object"],
                "value": [
                    {"name": "hoge", "id": str(entry_ref.id)},
                    {"name": "fuga", "boolean": False},  # specify boolean parameter
                ],
            },
            "group": {
                "type": AttrTypeValue["group"],
                "value": str(entry_group.id),
            },
            "arr_group": {
                "type": AttrTypeValue["array_group"],
                "value": [str(entry_group.id)],
            },
            "role": {
                "type": AttrTypeValue["role"],
                "value": str(entry_role.id),
            },
            "arr_role": {
                "type": AttrTypeValue["array_role"],
                "value": [str(entry_role.id)],
            },
            "date": {"type": AttrTypeValue["date"], "value": date(2020, 1, 1)},
        }
        entities = []
        for index in range(2):
            entity = Entity.objects.create(name="Entity-%d" % index, created_user=user)
            for attr_name, info in attr_info.items():
                attr = EntityAttr.objects.create(
                    name=attr_name,
                    type=info["type"],
                    created_user=user,
                    parent_entity=entity,
                )

                if info["type"] & AttrTypeValue["object"]:
                    attr.referral.add(entity_ref)

                entity.attrs.add(attr)

            # create an entry of Entity
            for e_index in range(2):
                entry = Entry.objects.create(
                    name="e-%d" % e_index, schema=entity, created_user=user
                )
                entry.complement_attrs(user)

                for attr_name, info in attr_info.items():
                    attr = entry.attrs.get(name=attr_name)
                    attrv = attr.add_value(user, info["value"])

                entry.register_es()

            entities.append(entity)

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [x.id for x in Entity.objects.filter(name__regex="^Entity-")],
                    "attrinfo": [{"name": x, "keyword": ""} for x in attr_info.keys()],
                    "export_style": "yaml",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        resp_data = yaml.load(Job.objects.last().get_cache(), Loader=yaml.FullLoader)
        for index in range(2):
            entity = Entity.objects.get(name="Entity-%d" % index)
            e_data = resp_data[entity.name]

            self.assertEqual(
                len(resp_data[entity.name]), Entry.objects.filter(schema=entity).count()
            )
            for e_data in resp_data[entity.name]:
                self.assertTrue(e_data["name"] in ["e-0", "e-1"])
                self.assertTrue(all([x in attr_info.keys() for x in e_data["attrs"]]))

        self.assertEqual(
            resp_data["Entity-0"][0]["attrs"],
            {
                "str": "foo",
                "obj": "ref",
                "name": {"bar": "ref"},
                "bool": False,
                "arr_str": ["foo", "bar", "baz"],
                "arr_obj": ["ref"],
                "arr_name": [
                    {"hoge": "ref"},
                    {"fuga": ""},
                ],
                "group": "group",
                "arr_group": ["group"],
                "role": "role",
                "arr_role": ["role"],
                "date": "2020-01-01",
            },
        )

        # Checked to be able to import exported data
        entry_another_ref = Entry.objects.create(
            name="another_ref", schema=entity_ref, created_user=user
        )
        new_group = Group.objects.create(name="new_group")
        new_role = Role.objects.create(name="new_role")
        new_attr_values = {
            "str": "bar",
            "obj": "another_ref",
            "name": {"hoge": "another_ref"},
            "bool": True,
            "arr_str": ["hoge", "fuga"],
            "arr_obj": ["another_ref"],
            "arr_name": [{"foo": "another_ref"}, {"bar": "ref"}],
            "group": "new_group",
            "arr_group": ["new_group"],
            "role": "new_role",
            "arr_role": ["new_role"],
            "date": "1999-01-01",
        }
        resp_data["Entity-1"][0]["attrs"] = new_attr_values

        mockio = mock.mock_open(read_data=yaml.dump(resp_data))
        with mock.patch("builtins.open", mockio):
            with open("hogefuga.yaml") as fp:
                resp = self.client.post(
                    reverse("entry:do_import", args=[entities[1].id]), {"file": fp}
                )
                self.assertEqual(resp.status_code, 303)

        self.assertEqual(entry_another_ref.get_referred_objects().count(), 1)

        updated_entry = entry_another_ref.get_referred_objects().first()
        self.assertEqual(updated_entry.name, resp_data["Entity-1"][0]["name"])

        for attr_name, value_info in new_attr_values.items():
            attrv = updated_entry.attrs.get(name=attr_name).get_latest_value()

            if attr_name == "str":
                self.assertEqual(attrv.value, value_info)
            elif attr_name == "obj":
                self.assertEqual(attrv.referral.id, entry_another_ref.id)
            elif attr_name == "name":
                self.assertEqual(attrv.value, list(value_info.keys())[0])
                self.assertEqual(attrv.referral.id, entry_another_ref.id)
            elif attr_name == "bool":
                self.assertTrue(attrv.boolean)
            elif attr_name == "arr_str":
                self.assertEqual(
                    sorted([x.value for x in attrv.data_array.all()]),
                    sorted(value_info),
                )
            elif attr_name == "arr_obj":
                self.assertEqual(
                    [x.referral.id for x in attrv.data_array.all()],
                    [entry_another_ref.id],
                )
            elif attr_name == "arr_name":
                self.assertEqual(
                    sorted([x.value for x in attrv.data_array.all()]),
                    sorted([list(x.keys())[0] for x in value_info]),
                )
                self.assertEqual(
                    sorted([x.referral.name for x in attrv.data_array.all()]),
                    sorted([list(x.values())[0] for x in value_info]),
                )
            elif attr_name == "group":
                self.assertEqual(int(attrv.value), new_group.id)
            elif attr_name == "arr_group":
                self.assertEqual(
                    [int(x.value) for x in attrv.data_array.all()],
                    [new_group.id],
                )
            elif attr_name == "role":
                self.assertEqual(int(attrv.value), new_role.id)
            elif attr_name == "arr_role":
                self.assertEqual(
                    [int(x.value) for x in attrv.data_array.all()],
                    [new_role.id],
                )
            elif attr_name == "date":
                self.assertEqual(attrv.date, date(1999, 1, 1))

    @patch(
        "dashboard.tasks.export_search_result.delay",
        Mock(side_effect=dashboard_tasks.export_search_result),
    )
    def test_duplicate_export(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="Entity", created_user=user)
        export_params = {
            "entities": [entity.id],
            "attrinfo": [{"name": "attr", "keyword": "data-5"}],
            "is_all_entities": False,
            "export_style": "csv",
        }

        # create a job to export search result
        job = Job.new_export(user, params=export_params)

        # A request with same parameter which is under execution will be denied
        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(export_params, sort_keys=True),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)

        # A request with another condition will be accepted
        new_export_params = dict(export_params, **{"export_style": "yaml"})
        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(new_export_params, sort_keys=True),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # When the job is finished, the processing is passed.
        job.status = Job.STATUS["DONE"]
        job.save(update_fields=["status"])
        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(export_params, sort_keys=True),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

    @patch(
        "dashboard.tasks.export_search_result.delay",
        Mock(side_effect=dashboard_tasks.export_search_result),
    )
    def test_export_with_hint_entry_name(self):
        admin = self._create_user("admin", is_superuser=True)

        entity = Entity.objects.create(name="Entity", created_user=admin)
        for name in ["foo", "bar", "baz"]:
            Entry.objects.create(name=name, schema=entity, created_user=admin).register_es()

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [],
                    "entry_name": "ba",
                    "export_style": "yaml",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        resp_data = yaml.load(Job.objects.last().get_cache(), Loader=yaml.FullLoader)
        self.assertEqual(len(resp_data["Entity"]), 2)
        self.assertEqual([x["name"] for x in resp_data["Entity"]], ["bar", "baz"])

    @patch(
        "dashboard.tasks.export_search_result.delay",
        Mock(side_effect=dashboard_tasks.export_search_result),
    )
    def test_yaml_export_with_referral(self):
        user = self._create_user("admin", is_superuser=True)

        # initialize Entities
        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=user)
        entity = Entity.objects.create(name="entity", created_user=user)
        entity_attr = EntityAttr.objects.create(
            name="attr_ref",
            type=AttrTypeValue["object"],
            created_user=user,
            parent_entity=entity,
        )
        entity_attr.referral.add(ref_entity)
        entity.attrs.add(entity_attr)

        # initialize Entries
        ref_entry = Entry.objects.create(name="ref", schema=ref_entity, created_user=user)
        ref_entry.register_es()

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.attrs.first().add_value(user, ref_entry)
        entry.register_es()

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [ref_entity.id],
                    "attrinfo": [],
                    "export_style": "yaml",
                    "has_referral": True,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        resp_data = yaml.load(Job.objects.last().get_cache(), Loader=yaml.FullLoader)
        self.assertEqual(len(resp_data["ReferredEntity"]), 1)
        referrals = resp_data["ReferredEntity"][0]["referrals"]
        self.assertEqual(len(referrals), 1)
        self.assertEqual(referrals[0]["entity"], "entity")
        self.assertEqual(referrals[0]["entry"], "entry")

    @patch(
        "dashboard.tasks.export_search_result.delay",
        Mock(side_effect=dashboard_tasks.export_search_result),
    )
    def test_export_advanced_search_result_with_no_value(self):
        admin = self._create_user("admin", is_superuser=True)

        entity: Entity = self.create_entity(
            **{
                "user": admin,
                "name": "test-entity",
                "attrs": self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY,
            }
        )
        entry = Entry.objects.create(name="test-entry", schema=entity, created_user=admin)
        entry.complement_attrs(admin)
        entry.register_es()

        results = [
            {"column": "val", "csv": "", "yaml": ""},
            {"column": "vals", "csv": "", "yaml": []},
            {"column": "ref", "csv": "", "yaml": ""},
            {"column": "refs", "csv": "", "yaml": []},
            {"column": "name", "csv": ": ", "yaml": {"": ""}},
            {"column": "names", "csv": "", "yaml": []},
            {"column": "group", "csv": "", "yaml": ""},
            {"column": "groups", "csv": "", "yaml": []},
            {"column": "bool", "csv": "False", "yaml": False},
            {"column": "text", "csv": "", "yaml": ""},
            {"column": "date", "csv": "", "yaml": None},
            {"column": "role", "csv": "", "yaml": ""},
            {"column": "roles", "csv": "", "yaml": []},
        ]

        # send request to export data
        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [
                        {"name": x["name"]} for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
                    ],
                    "export_style": "csv",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # verifying result
        csv_contents = [x for x in Job.objects.last().get_cache().splitlines() if x]
        self.assertEqual(
            csv_contents[0], "Name,Entity,%s" % ",".join([x["column"] for x in results])
        )
        self.assertEqual(
            csv_contents[1], "test-entry,test-entity,%s" % ",".join([x["csv"] for x in results])
        )

        # send request to export data
        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [entity.id],
                    "attrinfo": [
                        {"name": x["name"]} for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
                    ],
                    "export_style": "yaml",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # verifying result
        yaml_contents = yaml.load(Job.objects.last().get_cache(), Loader=yaml.FullLoader)
        self.assertEqual(
            yaml_contents["test-entity"][0]["attrs"], {x["column"]: x["yaml"] for x in results}
        )

    @patch(
        "dashboard.tasks.export_search_result.delay",
        Mock(side_effect=dashboard_tasks.export_search_result),
    )
    def test_export_with_all_entities(self):
        self.add_entry(self.user, "Entry", self.entity, values={"val": "hoge"})

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [],
                    "attrinfo": [{"name": "hoge"}],
                    "is_all_entities": "true",
                    "export_style": "yaml",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "non_field_errors": [
                    {
                        "code": "AE-121000",
                        "message": "Invalid value for attribute parameter",
                    }
                ]
            },
        )

        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(
                {
                    "entities": [],
                    "attrinfo": [{"name": "val"}],
                    "is_all_entities": "true",
                    "export_style": "yaml",
                }
            ),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        resp_data = yaml.load(Job.objects.last().get_cache(), Loader=yaml.FullLoader)
        self.assertEqual(resp_data, {"test-entity": [{"attrs": {"val": "hoge"}, "name": "Entry"}]})

    def test_entry_history(self):
        values = {
            "val": {"value": "hoge", "result": {"as_string": "hoge"}},
            "vals": {"value": ["foo", "bar"], "result": {"as_array_string": ["foo", "bar"]}},
            "ref": {
                "value": self.ref_entry.id,
                "result": {
                    "as_object": {
                        "id": self.ref_entry.id,
                        "name": self.ref_entry.name,
                        "schema": {
                            "id": self.ref_entry.schema.id,
                            "name": self.ref_entry.schema.name,
                        },
                    },
                },
            },
            "refs": {
                "value": [self.ref_entry.id],
                "result": {
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
            },
            "name": {
                "value": {"name": "hoge", "id": self.ref_entry.id},
                "result": {
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
            },
            "names": {
                "value": [{"name": "foo", "id": self.ref_entry.id}],
                "result": {
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
                    ]
                },
            },
            "group": {
                "value": self.group.id,
                "result": {
                    "as_group": {
                        "id": self.group.id,
                        "name": self.group.name,
                    },
                },
            },
            "groups": {
                "value": [self.group.id],
                "result": {
                    "as_array_group": [
                        {
                            "id": self.group.id,
                            "name": self.group.name,
                        }
                    ]
                },
            },
            "role": {
                "value": self.role.id,
                "result": {
                    "as_role": {
                        "id": self.role.id,
                        "name": self.role.name,
                    },
                },
            },
            "roles": {
                "value": [self.role.id],
                "result": {
                    "as_array_role": [
                        {
                            "id": self.role.id,
                            "name": self.role.name,
                        }
                    ]
                },
            },
            "text": {"value": "fuga", "result": {"as_string": "fuga"}},
            "bool": {"value": False, "result": {"as_boolean": False}},
            "date": {"value": "2018-12-31", "result": {"as_string": "2018-12-31"}},
        }
        entry = self.add_entry(
            self.user, "Entry", self.entity, values={x: values[x]["value"] for x in values.keys()}
        )
        resp = self.client.get("/entry/api/v2/%s/histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 18)
        attrv = entry.get_attrv("date")
        self.assertEqual(
            resp.json()["results"][0],
            {
                "created_time": attrv.created_time.astimezone(self.TZ_INFO).isoformat(),
                "created_user": "guest",
                "curr_value": {"as_string": "2018-12-31"},
                "id": attrv.id,
                "parent_attr": {"id": attrv.parent_attr.id, "name": "date"},
                "prev_id": None,
                "prev_value": None,
                "type": AttrTypeDate.TYPE,
            },
        )

        for name in values.keys():
            attr: Attribute = entry.attrs.get(schema__name=name)
            attrv: AttributeValue = attr.get_latest_value()
            self.assertEqual(
                next(filter(lambda x: x["id"] == attrv.id, resp.json()["results"]))["curr_value"],
                values[name]["result"],
            )

        # check order by created_time
        attr = entry.attrs.get(schema__name="vals")
        attr.add_value(self.user, ["hoge", "fuga"])

        resp = self.client.get("/entry/api/v2/%s/histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 19)
        self.assertEqual(resp.json()["results"][0]["parent_attr"]["name"], "vals")
        self.assertEqual(
            resp.json()["results"][0]["curr_value"]["as_array_string"], ["hoge", "fuga"]
        )
        self.assertEqual(resp.json()["results"][0]["prev_value"]["as_array_string"], ["foo", "bar"])

    def test_entry_history_without_permission(self):
        entry = self.add_entry(self.user, "Entry", self.entity, {}, False)

        # permission nothing entry
        resp = self.client.get("/entry/api/v2/%s/histories/" % entry.id)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readble entry
        self.role.users.add(self.user)
        entry.readable.roles.add(self.role)
        resp = self.client.get("/entry/api/v2/%d/histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)

        # permission nothing entity attr
        entity_attr: EntityAttr = self.entity.attrs.get(name="val")
        entity_attr.is_public = False
        entity_attr.save()
        resp = self.client.get("/entry/api/v2/%d/histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(
            any(
                [
                    x["parent_attr"]["name"] == "val"
                    for x in [result for result in resp.json()["results"]]
                ]
            )
        )

        # permission nothing entity attr
        entity_attr.readable.roles.add(self.role)
        resp = self.client.get("/entry/api/v2/%d/histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            any(
                [
                    x["parent_attr"]["name"] == "val"
                    for x in [result for result in resp.json()["results"]]
                ]
            )
        )

    def test_destroy_entries(self):
        entry1: Entry = self.add_entry(self.user, "entry1", self.entity)
        entry2: Entry = self.add_entry(self.user, "entry2", self.entity)

        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s&ids=%s" % (entry1.id, entry2.id),
            None,
            "application/json",
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        entry1.refresh_from_db()
        entry2.refresh_from_db()
        self.assertRegex(entry1.name, "entry1_deleted_")
        self.assertFalse(entry1.is_active)
        self.assertEqual(entry1.deleted_user, self.user)
        self.assertIsNotNone(entry1.deleted_time)
        self.assertRegex(entry2.name, "entry2_deleted_")
        self.assertFalse(entry2.is_active)
        self.assertEqual(entry2.deleted_user, self.user)
        self.assertIsNotNone(entry2.deleted_time)

        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s&ids=%s" % (entry1.id, entry2.id),
            None,
            "application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_destroy_entries_without_permission(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        # permission nothing entity
        self.entity.is_public = False
        self.entity.save()
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 403)

        # permission readable entity
        self.role.users.add(self.user)
        self.entity.readable.roles.add(self.role)
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 403)

        # permission writable entity
        self.entity.writable.roles.add(self.role)
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)

        entry.restore()

        # permission nothing entry
        entry.is_public = False
        entry.save()
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 403)

        # permission readable entry
        entry.readable.roles.add(self.role)
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 403)

        # permission writable entry
        entry.writable.roles.add(self.role)
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)

    def test_destory_entries_with_invalid_param(self):
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % "hoge", None, "application/json"
        )
        self.assertEqual(resp.status_code, 400)

        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % 9999, None, "application/json"
        )
        self.assertEqual(resp.status_code, 404)

    @mock.patch("custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("custom_view.call_custom")
    def test_destroy_entries_with_custom_view(self, mock_call_custom):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        def side_effect(handler_name, entity_name, user, entry):
            raise ValidationError("delete error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), [{"code": "AE-121000", "message": "delete error"}])

        def side_effect(handler_name, entity_name, user, entry):
            self.assertTrue(handler_name in ["before_delete_entry_v2", "after_delete_entry_v2"])
            self.assertEqual(entity_name, self.entity.name)
            self.assertEqual(user, self.user)
            self.assertEqual(entry, entry)

        mock_call_custom.side_effect = side_effect
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)
        self.assertTrue(mock_call_custom.called)

    @mock.patch("entry.tasks.notify_delete_entry.delay")
    def test_destroy_entries_notify(self, mock_task):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        self.client.delete("/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json")

        self.assertTrue(mock_task.called)
