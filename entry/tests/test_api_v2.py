import datetime
import errno
import json
import logging
import math
from datetime import date
from unittest import mock
from unittest.mock import Mock, patch

import yaml
from rest_framework import status
from rest_framework.exceptions import ValidationError

from acl.models import ACLType
from airone.lib.elasticsearch import AttrHint, EntryFilterKey, FilterKey
from airone.lib.log import Logger
from airone.lib.test import AironeViewTest
from airone.lib.types import (
    AttrDefaultValue,
    AttrType,
    AttrTypeValue,
)
from entity.models import Entity, EntityAttr
from entry import tasks
from entry.models import Attribute, AttributeValue, Entry
from entry.services import AdvancedSearchService
from entry.settings import CONFIG
from group.models import Group
from job.models import Job, JobOperation, JobStatus
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

    @patch("entry.tasks.export_entries_v2.delay", Mock(side_effect=tasks.export_entries_v2))
    def test_post_export(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="ほげ", created_user=user)
        for name in ["foo", "bar"]:
            EntityAttr.objects.create(
                **{
                    "name": name,
                    "type": AttrType.STRING,
                    "created_user": user,
                    "parent_entity": entity,
                }
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
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY_V2)
        self.assertEqual(job.status, JobStatus.DONE)
        self.assertEqual(job.text, "entry_ほげ.yaml")

        obj = yaml.load(job.get_cache(), Loader=yaml.SafeLoader)

        self.assertEqual(len(obj), 1)
        entity_data = obj[0]
        self.assertEqual(entity_data["entity"], "ほげ")

        self.assertEqual(len(entity_data["entries"]), 1)
        entry_data = entity_data["entries"][0]
        self.assertEqual(entry_data["name"], "fuga")
        self.assertEqual(entry_data["id"], entry.id)
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
        EntityAttr.objects.create(
            **{
                "name": "new_attr",
                "type": AttrType.STRING,
                "created_user": user,
                "parent_entity": entity,
                "is_public": False,
            }
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
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY_V2)
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
                "type": AttrType.OBJECT,
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity_attr_object.referral.add(self.ref_entity)
        entity_attr_array_object = EntityAttr.objects.create(
            **{
                "name": "array_object",
                "type": AttrType.ARRAY_OBJECT,
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity_attr_array_object.referral.add(self.ref_entity)
        entity_attr_named_object = EntityAttr.objects.create(
            **{
                "name": "named_object",
                "type": AttrType.NAMED_OBJECT,
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity_attr_named_object.referral.add(self.ref_entity)
        entity_attr_named_object_without_key = EntityAttr.objects.create(
            **{
                "name": "named_object_without_key",
                "type": AttrType.NAMED_OBJECT,
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity_attr_named_object_without_key.referral.add(self.ref_entity)
        entity_attr_array_named_object = EntityAttr.objects.create(
            **{
                "name": "array_named_object",
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity_attr_array_named_object.referral.add(self.ref_entity)

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

        job = Job.objects.filter(target=entity).last()
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY_V2)
        self.assertEqual(job.status, JobStatus.DONE)

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
    def test_post_export_with_all_attribute(self):
        self.add_entry(
            self.user,
            "Entry",
            self.entity,
            values={
                "val": "hoge",
                "ref": self.ref_entry.id,
                "name": {"name": "hoge", "id": self.ref_entry.id},
                "bool": False,
                "date": "2018-12-31",
                "datetime": "2018-12-31T00:00:00+00:00",
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
                "num": 123,
                "nums": [456, 789],
            },
        )

        resp = self.client.post(
            "/entry/api/v2/%d/export/" % self.entity.id,
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        job = Job.objects.filter(target=self.entity).last()
        obj = yaml.load(job.get_cache(), Loader=yaml.SafeLoader)
        self.assertEqual(
            obj[0]["entries"][0]["attrs"],
            [
                {"name": "val", "value": "hoge"},
                {"name": "vals", "value": ["foo", "bar"]},
                {"name": "ref", "value": {"entity": "ref_entity", "name": "r-0"}},
                {"name": "refs", "value": [{"entity": "ref_entity", "name": "r-0"}]},
                {"name": "name", "value": {"hoge": {"entity": "ref_entity", "name": "r-0"}}},
                {
                    "name": "names",
                    "value": [
                        {"foo": {"entity": "ref_entity", "name": "r-0"}},
                        {"bar": {"entity": "ref_entity", "name": "r-0"}},
                    ],
                },
                {"name": "group", "value": "group0"},
                {"name": "groups", "value": ["group0"]},
                {"name": "bool", "value": False},
                {"name": "text", "value": "fuga"},
                {"name": "date", "value": datetime.date(2018, 12, 31)},
                {"name": "role", "value": "role0"},
                {"name": "roles", "value": ["role0"]},
                {
                    "name": "datetime",
                    "value": datetime.datetime(2018, 12, 31, 0, 0, 0, tzinfo=datetime.timezone.utc),
                },
                {"name": "num", "value": 123},
                {"name": "nums", "value": [456, 789]},
            ],
        )

    @patch("entry.tasks.export_entries_v2.delay", Mock(side_effect=tasks.export_entries_v2))
    def test_get_export_csv_escape(self):
        user = self.admin_login()

        dummy_entity = Entity.objects.create(name="Dummy", created_user=user)
        dummy_entry = Entry(name='D,U"MM"Y', schema=dummy_entity, created_user=user)
        dummy_entry.save()

        CASES = [
            [AttrType.STRING, 'raison,de"tre', '"raison,de""tre"'],
            [AttrType.OBJECT, dummy_entry, '"D,U""MM""Y"'],
            [AttrType.TEXT, "1st line\r\n2nd line", '"1st line' + "\r\n" + '2nd line"'],
            [AttrType.NAMED_OBJECT, {"key": dummy_entry}, '"{\'key\': \'D,U""MM""Y\'}"'],
            [AttrType.ARRAY_STRING, ["one", "two", "three"], "\"['one', 'two', 'three']\""],
            [AttrType.ARRAY_OBJECT, [dummy_entry], '"[\'D,U""MM""Y\']"'],
            [
                AttrType.ARRAY_NAMED_OBJECT,
                [{"key1": dummy_entry}],
                '"[{\'key1\': \'D,U""MM""Y\'}]"',
            ],
        ]

        for type, value, expected in CASES:
            type_name = type.name
            attr_name = type_name + ',"ATTR"'

            test_entity = Entity.objects.create(name="TestEntity_" + type_name, created_user=user)

            test_entity_attr = EntityAttr.objects.create(
                name=attr_name,
                type=type,
                created_user=user,
                parent_entity=test_entity,
            )

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

            test_val = None

            if type & AttrType._ARRAY == 0:
                match type:
                    case AttrType.STRING:
                        test_val = AttributeValue.create(user=user, attr=test_attr, value=value)
                    case AttrType.OBJECT:
                        test_val = AttributeValue.create(user=user, attr=test_attr, referral=value)
                    case AttrType.TEXT:
                        test_val = AttributeValue.create(user=user, attr=test_attr, value=value)
                    case AttrType.NAMED_OBJECT:
                        [(k, v)] = value.items()
                        test_val = AttributeValue.create(
                            user=user, attr=test_attr, value=k, referral=v
                        )
            else:
                test_val = AttributeValue.create(user=user, attr=test_attr)
                test_val.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
                for child in value:
                    match type:
                        case AttrType.ARRAY_STRING:
                            AttributeValue.create(
                                user=user, attr=test_attr, value=child, parent_attrv=test_val
                            )
                        case AttrType.ARRAY_OBJECT:
                            AttributeValue.create(
                                user=user,
                                attr=test_attr,
                                referral=child,
                                parent_attrv=test_val,
                            )
                        case AttrType.ARRAY_NAMED_OBJECT:
                            [(k, v)] = child.items()
                            AttributeValue.create(
                                user=user,
                                attr=test_attr,
                                value=k,
                                referral=v,
                                parent_attrv=test_val,
                            )

            test_val.save()
            test_attr.values.add(test_val)
            test_attr.save()

            resp = self.client.post(
                "/entry/api/v2/%d/export/" % test_entity.id,
                json.dumps({"format": "CSV"}),
                "application/json",
            )
            self.assertEqual(resp.status_code, 200)

            content = Job.objects.filter(target=test_entity).last().get_cache()
            header = content.splitlines()[0]
            self.assertEqual(header, 'Name,"%s,""ATTR"""' % type_name)

            data = content.replace(header, "", 1).strip()
            self.assertEqual(data, '"%s,""ENTRY""",' % type_name + expected)

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

    @patch("entry.tasks.notify_create_entry.delay", Mock(side_effect=tasks.notify_create_entry))
    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_create_entry(self):
        fp = self.open_fixture_file("import_data_v2.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job = Job.objects.get(operation=JobOperation.IMPORT_ENTRY_V2)
        self.assertEqual(job.status, JobStatus.DONE)
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

        result = AdvancedSearchService.search_entries(
            self.user, [self.entity.id], is_output_all=True
        )
        self.assertEqual(result.ret_count, 1)
        self.assertEqual(result.ret_values[0].entry["name"], "test-entry")
        self.assertEqual(result.ret_values[0].entity["name"], "test-entity")
        attrs = {
            "bool": True,
            "date": "2018-12-31",
            "datetime": "2018-12-31T00:00:00+00:00",
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
            "num": 123.45,
            "nums": [123.45, 67.89, -45.67],
        }
        for attr_name in result.ret_values[0].attrs:
            self.assertEqual(result.ret_values[0].attrs[attr_name]["value"], attrs[attr_name])

        entry = Entry.objects.get(name="test-entry")
        job_notify = Job.objects.get(target=entry, operation=JobOperation.NOTIFY_CREATE_ENTRY)
        self.assertEqual(job_notify.status, JobStatus.DONE)

    @patch("entry.tasks.notify_update_entry.delay", Mock(side_effect=tasks.notify_update_entry))
    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_update_entry(self):
        entry = self.add_entry(self.user, "test-entry", self.entity)
        fp = self.open_fixture_file("import_data_v2.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job = Job.objects.get(operation=JobOperation.IMPORT_ENTRY_V2)
        self.assertEqual(job.status, JobStatus.DONE)

        result = AdvancedSearchService.search_entries(
            self.user, [self.entity.id], is_output_all=True
        )
        self.assertEqual(result.ret_count, 1)
        self.assertEqual(result.ret_values[0].entry, {"id": entry.id, "name": "test-entry"})
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
            "num": 123.45,
            "nums": [123.45, 67.89, -45.67],
            "datetime": "2018-12-31T00:00:00+00:00",
        }
        for attr_name in result.ret_values[0].attrs:
            self.assertEqual(result.ret_values[0].attrs[attr_name]["value"], attrs[attr_name])

        job_notify = Job.objects.get(target=entry, operation=JobOperation.NOTIFY_UPDATE_ENTRY)
        self.assertEqual(job_notify.status, JobStatus.DONE)

        # Update only some attributes
        fp = self.open_fixture_file("import_data_v2_update_some.yaml")
        resp = self.client.post("/entry/api/v2/import/?force=true", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job = Job.objects.filter(operation=JobOperation.IMPORT_ENTRY_V2).last()
        self.assertEqual(job.status, JobStatus.DONE)

        result = AdvancedSearchService.search_entries(
            self.user, [self.entity.id], is_output_all=True
        )
        attrs["val"] = "bar"
        for attr_name in result.ret_values[0].attrs:
            self.assertEqual(result.ret_values[0].attrs[attr_name]["value"], attrs[attr_name])

        # Update remove attribute value
        fp = self.open_fixture_file("import_data_v2_update_remove.yaml")
        resp = self.client.post("/entry/api/v2/import/?force=true", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job = Job.objects.filter(operation=JobOperation.IMPORT_ENTRY_V2).last()
        self.assertEqual(job.status, JobStatus.DONE)

        result = AdvancedSearchService.search_entries(
            self.user, [self.entity.id], is_output_all=True
        )
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
            "num": 123.45,  # Should remain unchanged from first import
            "nums": [123.45, 67.89, -45.67],  # Should remain unchanged from first import
            "datetime": None,
        }
        for attr_name in result.ret_values[0].attrs:
            if "value" in result.ret_values[0].attrs[attr_name]:
                self.assertEqual(result.ret_values[0].attrs[attr_name]["value"], attrs[attr_name])

    @patch("entry.tasks.notify_update_entry.delay", Mock(side_effect=tasks.notify_update_entry))
    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    @patch("entry.tasks.export_entries_v2.delay", Mock(side_effect=tasks.export_entries_v2))
    def test_import_update_entry_with_id(self):
        """
        This tests updating processing works correctly when entry ID is specified in import data.
        """
        # create initial item
        model = self.create_entity(
            self.user, "TestModel", attrs=[{"name": "val", "type": AttrType.STRING}]
        )
        item = self.add_entry(self.user, "OriginalItem", model, values={"val": "initial value"})

        # export Items that includes the created one
        resp = self.client.post(
            "/entry/api/v2/%d/export/" % model.id, json.dumps({}), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        exported_data = yaml.load(Job.objects.last().get_cache(), Loader=yaml.SafeLoader)

        # then, change the "item" that would be updated by subsequent import processing
        item.name = "ChangedItem"
        item.attrs.get(name="val").add_value(self.user, "changed value")
        item.save()

        # import exported data again
        resp = self.client.post(
            "/entry/api/v2/import/?force=true", exported_data, "application/yaml"
        )
        self.assertEqual(resp.status_code, 200)

        # There is no created item, and only one item has been updated
        self.assertEqual(Entry.objects.filter(schema=model, is_active=True).count(), 1)

        # check importing job was done successfully
        job = Job.objects.filter(operation=JobOperation.IMPORT_ENTRY_V2).last()
        self.assertEqual(job.status, JobStatus.DONE)

        # check target item has been updated back to the exported state
        item.refresh_from_db()
        self.assertEqual(item.name, "OriginalItem")
        self.assertEqual(item.get_attrv("val").value, "initial value")

    @patch("entry.tasks.notify_update_entry.delay", Mock(side_effect=tasks.notify_update_entry))
    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    @patch("entry.tasks.export_entries_v2.delay", Mock(side_effect=tasks.export_entries_v2))
    def test_import_update_entry_with_id_prevent_duplicated_name(self):
        """
        This tests import processing to update item as duplicated name is prevented.
        """
        # create initial item
        model = self.create_entity(
            self.user, "TestModel", attrs=[{"name": "val", "type": AttrType.STRING}]
        )
        [self.add_entry(self.user, "item-%s" % x, model) for x in range(2)]

        # export Items that includes the created one
        resp = self.client.post(
            "/entry/api/v2/%d/export/" % model.id, json.dumps({}), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        exported_data = yaml.load(Job.objects.last().get_cache(), Loader=yaml.SafeLoader)

        # update exported data to make duplicated name situation on import processing
        exported_data[0]["entries"][0]["name"] = "item-1"  # same as items[1].name

        # import exported data again
        resp = self.client.post(
            "/entry/api/v2/import/?force=true", exported_data, "application/yaml"
        )
        self.assertEqual(resp.status_code, 200)

        # Check importing job was failed due to duplicated name
        job = Job.objects.filter(operation=JobOperation.IMPORT_ENTRY_V2).last()
        self.assertEqual(job.status, JobStatus.WARNING)
        self.assertEqual(job.text, "Imported Entry count: 2, Failed import Entry: ['item-1']")

        # Check each Items have individual names has after importing processing
        self.assertEqual(
            [x.name for x in Entry.objects.filter(schema=model, is_active=True)],
            ["item-0", "item-1"],
        )

    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_multi_entity(self):
        entity1 = self.create_entity(self.user, "test-entity1")
        entity2 = self.create_entity(self.user, "test-entity2")
        fp = self.open_fixture_file("import_data_v2_multi_entity.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job1 = Job.objects.get(target=entity1, operation=JobOperation.IMPORT_ENTRY_V2)
        job2 = Job.objects.get(target=entity2, operation=JobOperation.IMPORT_ENTRY_V2)
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

        result = AdvancedSearchService.search_entries(self.user, [entity1.id, entity2.id])
        self.assertEqual(result.ret_count, 2)
        self.assertEqual(result.ret_values[0].entry["name"], "test-entry1")
        self.assertEqual(result.ret_values[0].entity["name"], "test-entity1")
        self.assertEqual(result.ret_values[1].entry["name"], "test-entry2")
        self.assertEqual(result.ret_values[1].entity["name"], "test-entity2")

    @patch("entry.tasks.notify_create_entry.delay", Mock(side_effect=tasks.notify_create_entry))
    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_entry_has_referrals_with_entities(self):
        ref_entity2: Entity = self.create_entity(self.user, "ref_entity2")
        attr: EntityAttr = self.entity.attrs.get(name="ref")
        attr.referral.add(ref_entity2)

        fp = self.open_fixture_file("import_data_v2_with_entities.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job = Job.objects.get(operation=JobOperation.IMPORT_ENTRY_V2)
        self.assertEqual(job.status, JobStatus.DONE)
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

        result = AdvancedSearchService.search_entries(
            self.user, [self.entity.id], is_output_all=True
        )
        self.assertEqual(result.ret_count, 1)
        self.assertEqual(result.ret_values[0].entry["name"], "test-entry")
        self.assertEqual(result.ret_values[0].entity["name"], "test-entity")
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
            "num": 123.45,
            "nums": [],
            "datetime": "2018-12-31T00:00:00+00:00",
        }
        for attr_name in result.ret_values[0].attrs:
            self.assertEqual(result.ret_values[0].attrs[attr_name]["value"], attrs[attr_name])

        entry = Entry.objects.get(name="test-entry")
        job_notify = Job.objects.get(target=entry, operation=JobOperation.NOTIFY_CREATE_ENTRY)
        self.assertEqual(job_notify.status, JobStatus.DONE)

        with self.assertLogs(logger=Logger, level=logging.WARNING) as warning_log:
            fp = self.open_fixture_file("import_data_v2.yaml")
            resp = self.client.post(
                "/entry/api/v2/import/?force=true", fp.read(), "application/yaml"
            )
            fp.close()
            self.assertEqual(
                warning_log.output,
                [
                    "WARNING:airone:ambiguous object given: entry name(r-0), "
                    "entity names(['ref_entity', 'ref_entity2'])"
                ],
            )

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
                        "message": 'Expected a list of items but got type "dict".',
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
        self.assertEqual(job.status, JobStatus.WARNING)
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
        job = Job.objects.get(target=self.entity, operation=JobOperation.IMPORT_ENTRY_V2)
        self.assertEqual(resp.json()["result"], {"job_ids": [job.id], "error": []})

    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_warning(self):
        fp = self.open_fixture_file("import_data_v2_warning.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()

        self.assertEqual(resp.status_code, 200)
        job_id = resp.json()["result"]["job_ids"][0]
        job = Job.objects.get(id=job_id)
        self.assertEqual(job.status, JobStatus.WARNING)
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
        self.assertEqual(job.status, JobStatus.CANCELED)
        self.assertEqual(job.text, "Now importing... (progress: [    1/    1])")
        self.assertFalse(Entry.objects.filter(name="test-entry").exists())

    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_frequent_jobs(self):
        fp = self.open_fixture_file("import_data_v2.yaml")
        resp = self.client.post("/entry/api/v2/import/", fp.read(), "application/yaml")
        fp.close()
        self.assertEqual(resp.status_code, 200)

        # without force param, it should exceed the limit
        fp = self.open_fixture_file("import_data_v2.yaml")
        resp = self.client.post("/entry/api/v2/import/?force=false", fp.read(), "application/yaml")
        fp.close()
        self.assertEqual(resp.status_code, 400)

        # with force param, it should ignore the limit
        fp = self.open_fixture_file("import_data_v2.yaml")
        resp = self.client.post("/entry/api/v2/import/?force=true", fp.read(), "application/yaml")
        fp.close()
        self.assertEqual(resp.status_code, 200)

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
    def test_export_advanced_search_result(self):
        user = self._create_user("admin", is_superuser=True)

        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="ref_entry", schema=ref_entity, created_user=user)
        grp_entry = Group.objects.create(name="group_entry")
        role_entry = Role.objects.create(name="role_entry")
        attr_info = {
            "str": {"type": AttrType.STRING, "value": "foo"},
            "text": {"type": AttrType.TEXT, "value": "foo"},
            "bool": {"type": AttrType.BOOLEAN, "value": True},
            "date": {"type": AttrType.DATE, "value": "2020-01-01"},
            "obj": {"type": AttrType.OBJECT, "value": ref_entry},
            "grp": {"type": AttrType.GROUP, "value": grp_entry},
            "role": {"type": AttrType.ROLE, "value": role_entry},
            "name": {
                "type": AttrType.NAMED_OBJECT,
                "value": {"name": "bar", "id": ref_entry.id},
            },
            "arr_str": {"type": AttrType.ARRAY_STRING, "value": ["foo"]},
            "arr_obj": {"type": AttrType.ARRAY_OBJECT, "value": [ref_entry]},
            "arr_grp": {"type": AttrType.ARRAY_GROUP, "value": [grp_entry]},
            "arr_role": {"type": AttrType.ARRAY_ROLE, "value": [role_entry]},
            "arr_name": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "value": [{"name": "hoge", "id": ref_entry.id}],
            },
        }

        entity = Entity.objects.create(name="Entity", created_user=user)
        for attr_name, info in attr_info.items():
            EntityAttr.objects.create(
                **{
                    "name": attr_name,
                    "type": info["type"],
                    "created_user": user,
                    "parent_entity": entity,
                }
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
                    "hint_entry": [],  # invalid type
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("hint_entry", resp.json())

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
                    "hint_entry": {
                        "filter_key": EntryFilterKey.TEXT_CONTAINED,
                        "keyword": "a" * 250,
                    },
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("hint_entry", resp.json())

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
                    "hint_entry": {
                        "filter_key": EntryFilterKey.TEXT_CONTAINED,
                        "keyword": "a" * 249,
                    },
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
        "entry.tasks.export_search_result_v2.delay", Mock(side_effect=tasks.export_search_result_v2)
    )
    def test_export_advanced_search_result_with_referral(self):
        user = self._create_user("admin", is_superuser=True)

        # initialize Entities
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        entity = Entity.objects.create(name="entity", created_user=user)
        entity_attr = EntityAttr.objects.create(
            name="attr_ref",
            type=AttrType.OBJECT,
            created_user=user,
            parent_entity=entity,
        )
        entity_attr.referral.add(ref_entity)

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
        "entry.tasks.export_search_result_v2.delay", Mock(side_effect=tasks.export_search_result_v2)
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
        self.assertEqual(len(csv_contents), 2)
        self.assertEqual(csv_contents[0], "Name,Entity,text")
        self.assertEqual(csv_contents[1], "private,test-entity,")

    @patch(
        "entry.tasks.export_search_result_v2.delay", Mock(side_effect=tasks.export_search_result_v2)
    )
    def test_show_advanced_search_results_csv_escape(self):
        user = self._create_user("admin", is_superuser=True)

        dummy_entity = Entity.objects.create(name="Dummy", created_user=user)
        dummy_entry = Entry(name='D,U"MM"Y', schema=dummy_entity, created_user=user)
        dummy_entry.save()

        CASES = [
            [AttrType.STRING, 'raison,de"tre', '"raison,de""tre"'],
            [AttrType.OBJECT, dummy_entry, '"D,U""MM""Y"'],
            [AttrType.TEXT, "1st line\r\n2nd line", '"1st line' + "\r\n" + '2nd line"'],
            [AttrType.NAMED_OBJECT, {"key": dummy_entry}, '"key: D,U""MM""Y"'],
            [AttrType.ARRAY_STRING, ["one", "two", "three"], '"one\nthree\ntwo"'],
            [AttrType.ARRAY_OBJECT, [dummy_entry], '"D,U""MM""Y"'],
            [AttrType.ARRAY_NAMED_OBJECT, [{"key1": dummy_entry}], '"key1: D,U""MM""Y"'],
        ]

        for type, value, expected in CASES:
            # setup data
            type_name = type.name
            attr_name = type_name + ',"ATTR"'

            test_entity = Entity.objects.create(name="TestEntity_" + type_name, created_user=user)

            test_entity_attr = EntityAttr.objects.create(
                name=attr_name,
                type=type,
                created_user=user,
                parent_entity=test_entity,
            )

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

            test_val = None

            if type & AttrType._ARRAY == 0:
                match type:
                    case AttrType.STRING:
                        test_val = AttributeValue.create(user=user, attr=test_attr, value=value)
                    case AttrType.OBJECT:
                        test_val = AttributeValue.create(user=user, attr=test_attr, referral=value)
                    case AttrType.TEXT:
                        test_val = AttributeValue.create(user=user, attr=test_attr, value=value)
                    case AttrType.NAMED_OBJECT:
                        [(k, v)] = value.items()
                        test_val = AttributeValue.create(
                            user=user, attr=test_attr, value=k, referral=v
                        )
            else:
                test_val = AttributeValue.create(user=user, attr=test_attr)
                test_val.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
                for child in value:
                    match type:
                        case AttrType.ARRAY_STRING:
                            AttributeValue.create(
                                user=user,
                                attr=test_attr,
                                value=child,
                                parent_attrv=test_val,
                            )
                        case AttrType.ARRAY_OBJECT:
                            AttributeValue.create(
                                user=user,
                                attr=test_attr,
                                referral=child,
                                parent_attrv=test_val,
                            )
                        case AttrType.ARRAY_NAMED_OBJECT:
                            [(k, v)] = child.items()
                            AttributeValue.create(
                                user=user,
                                attr=test_attr,
                                value=k,
                                referral=v,
                                parent_attrv=test_val,
                            )

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
            self.assertEqual(data, '"%s,""ENTRY""",%s,%s' % (type_name, test_entity.name, expected))

    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    @patch(
        "entry.tasks.export_search_result_v2.delay", Mock(side_effect=tasks.export_search_result_v2)
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
                "type": AttrType.STRING,
                "value": "foo",
                "invalid_values": [123, entry_ref, True],
            },
            "obj": {"type": AttrType.OBJECT, "value": str(entry_ref.id)},
            "name": {
                "type": AttrType.NAMED_OBJECT,
                "value": {"name": "bar", "id": str(entry_ref.id)},
            },
            "bool": {"type": AttrType.BOOLEAN, "value": False},
            "arr_str": {
                "type": AttrType.ARRAY_STRING,
                "value": ["foo", "bar", "baz"],
            },
            "arr_obj": {
                "type": AttrType.ARRAY_OBJECT,
                "value": [str(entry_ref.id)],
            },
            "arr_name": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "value": [
                    {"name": "hoge", "id": str(entry_ref.id)},
                    {"name": "fuga", "boolean": False},  # specify boolean parameter
                ],
            },
            "group": {
                "type": AttrType.GROUP,
                "value": str(entry_group.id),
            },
            "arr_group": {
                "type": AttrType.ARRAY_GROUP,
                "value": [str(entry_group.id)],
            },
            "role": {
                "type": AttrType.ROLE,
                "value": str(entry_role.id),
            },
            "arr_role": {
                "type": AttrType.ARRAY_ROLE,
                "value": [str(entry_role.id)],
            },
            "date": {"type": AttrType.DATE, "value": date(2020, 1, 1)},
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

                if info["type"] & AttrType.OBJECT:
                    attr.referral.add(entity_ref)

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
            found = next(filter(lambda x: x["entity"] == entity.name, resp_data), None)
            self.assertEqual(len(found["entries"]), Entry.objects.filter(schema=entity).count())
            for e_data in found["entries"]:
                self.assertTrue(e_data["name"] in ["e-0", "e-1"])
                self.assertTrue(all([a["name"] in attr_info.keys() for a in e_data["attrs"]]))

        self.assertEqual(
            next(filter(lambda x: x["entity"] == "Entity-0", resp_data), None)["entries"][0][
                "attrs"
            ],
            [
                {"name": "str", "value": "foo"},
                {"name": "obj", "value": {"entity": "RefEntity", "name": "ref"}},
                {"name": "name", "value": {"bar": {"entity": "RefEntity", "name": "ref"}}},
                {"name": "bool", "value": False},
                {"name": "arr_str", "value": ["foo", "bar", "baz"]},
                {"name": "arr_obj", "value": [{"entity": "RefEntity", "name": "ref"}]},
                {
                    "name": "arr_name",
                    "value": [
                        {"hoge": {"entity": "RefEntity", "name": "ref"}},
                        {"fuga": None},
                    ],
                },
                {"name": "group", "value": "group"},
                {"name": "arr_group", "value": ["group"]},
                {"name": "role", "value": "role"},
                {"name": "arr_role", "value": ["role"]},
                {"name": "date", "value": "2020-01-01"},
            ],
        )

        # Checked to be able to import exported data
        entry_another_ref = Entry.objects.create(
            name="another_ref", schema=entity_ref, created_user=user
        )
        new_group = Group.objects.create(name="new_group")
        new_role = Role.objects.create(name="new_role")
        new_attr_values = [
            {"name": "str", "value": "bar"},
            {"name": "obj", "value": {"entity": "RefEntity", "name": "another_ref"}},
            {"name": "name", "value": {"hoge": {"entity": "RefEntity", "name": "another_ref"}}},
            {"name": "bool", "value": True},
            {"name": "arr_str", "value": ["hoge", "fuga"]},
            {"name": "arr_obj", "value": [{"entity": "RefEntity", "name": "another_ref"}]},
            {
                "name": "arr_name",
                "value": [
                    {"foo": {"entity": "RefEntity", "name": "another_ref"}},
                    {"bar": {"entity": "RefEntity", "name": "ref"}},
                ],
            },
            {"name": "group", "value": "new_group"},
            {"name": "arr_group", "value": ["new_group"]},
            {"name": "role", "value": "new_role"},
            {"name": "arr_role", "value": ["new_role"]},
            {"name": "date", "value": "1999-01-01"},
        ]
        resp_data = [
            next(filter(lambda x: x["entity"] == "Entity-0", resp_data), {}),
            {
                "entity": "Entity-1",
                "entries": [
                    {
                        "attrs": new_attr_values,
                        "name": "e-100",
                    },
                ],
            },
        ]

        resp = self.client.post("/entry/api/v2/import/", yaml.dump(resp_data), "application/yaml")
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(entry_another_ref.get_referred_objects().count(), 1)

        updated_entry = entry_another_ref.get_referred_objects().first()
        entity1 = next(filter(lambda x: x["entity"] == "Entity-1", resp_data), None)
        self.assertIsNotNone(entity1)
        self.assertEqual(updated_entry.name, entity1["entries"][0]["name"])

        for attr in new_attr_values:
            attr_name, value_info = attr["name"], attr["value"]
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
                    sorted([list([xx["name"] for xx in x.values()])[0] for x in value_info]),
                )
            elif attr_name == "group":
                self.assertEqual(attrv.group, new_group)
            elif attr_name == "arr_group":
                self.assertEqual(
                    [x.group for x in attrv.data_array.all().select_related("group")],
                    [new_group],
                )
            elif attr_name == "role":
                self.assertEqual(attrv.role, new_role)
            elif attr_name == "arr_role":
                self.assertEqual(
                    [x.role for x in attrv.data_array.all().select_related("role")],
                    [new_role],
                )
            elif attr_name == "date":
                self.assertEqual(attrv.date, date(1999, 1, 1))

    @patch(
        "entry.tasks.export_search_result_v2.delay", Mock(side_effect=tasks.export_search_result_v2)
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
        job.status = JobStatus.DONE
        job.save(update_fields=["status"])
        resp = self.client.post(
            "/entry/api/v2/advanced_search_result_export/",
            json.dumps(export_params, sort_keys=True),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

    @patch(
        "entry.tasks.export_search_result_v2.delay", Mock(side_effect=tasks.export_search_result_v2)
    )
    def test_export_with_hint_entry(self):
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
                    "hint_entry": {"filter_key": EntryFilterKey.TEXT_CONTAINED, "keyword": "ba"},
                    "export_style": "yaml",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        resp_data = yaml.load(Job.objects.last().get_cache(), Loader=yaml.FullLoader)
        self.assertEqual(len(resp_data[0]["entries"]), 2)
        self.assertEqual([x["name"] for x in resp_data[0]["entries"]], ["bar", "baz"])

    @patch(
        "entry.tasks.export_search_result_v2.delay", Mock(side_effect=tasks.export_search_result_v2)
    )
    def test_yaml_export_with_referral(self):
        user = self._create_user("admin", is_superuser=True)

        # initialize Entities
        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=user)
        entity = Entity.objects.create(name="entity", created_user=user)
        entity_attr = EntityAttr.objects.create(
            name="attr_ref",
            type=AttrType.OBJECT,
            created_user=user,
            parent_entity=entity,
        )
        entity_attr.referral.add(ref_entity)

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
        referred_entity = next(filter(lambda x: x["entity"] == "ReferredEntity", resp_data), None)
        self.assertIsNotNone(referred_entity)
        referrals = referred_entity["entries"][0]["referrals"]
        self.assertEqual(len(referrals), 1)
        self.assertEqual(referrals[0]["entity"], "entity")
        self.assertEqual(referrals[0]["entry"], "entry")

    @patch(
        "entry.tasks.export_search_result_v2.delay", Mock(side_effect=tasks.export_search_result_v2)
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
            {"column": "ref", "csv": "", "yaml": None},
            {"column": "refs", "csv": "", "yaml": []},
            {"column": "name", "csv": ": ", "yaml": {}},
            {"column": "names", "csv": "", "yaml": []},
            {"column": "group", "csv": "", "yaml": None},
            {"column": "groups", "csv": "", "yaml": []},
            {"column": "bool", "csv": "False", "yaml": False},
            {"column": "text", "csv": "", "yaml": ""},
            {"column": "date", "csv": "", "yaml": None},
            {"column": "role", "csv": "", "yaml": None},
            {"column": "roles", "csv": "", "yaml": []},
            {"column": "datetime", "csv": "", "yaml": None},
            {"column": "num", "csv": "", "yaml": None},
            {"column": "nums", "csv": "", "yaml": []},
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
            yaml_contents[0]["entries"][0]["attrs"],
            [{"name": x["column"], "value": x["yaml"]} for x in results],
        )

    @patch(
        "entry.tasks.export_search_result_v2.delay", Mock(side_effect=tasks.export_search_result_v2)
    )
    def test_export_with_all_entities(self):
        test_item = self.add_entry(self.user, "Entry", self.entity, values={"val": "hoge"})

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
        self.assertEqual(
            resp_data,
            [
                {
                    "entity": "ref_entity",
                    "entries": [
                        {
                            "id": self.ref_entry.id,
                            "name": "r-0",
                            "attrs": [{"name": "val", "value": ""}],
                            "referrals": None,
                        }
                    ],
                },
                {
                    "entity": "test-entity",
                    "entries": [
                        {
                            "id": test_item.id,
                            "name": "Entry",
                            "attrs": [{"name": "val", "value": "hoge"}],
                            "referrals": None,
                        }
                    ],
                },
            ],
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
            "num": {"value": 456, "result": {"as_number": 456.0}},
            "nums": {
                "value": [123, 456, 789],
                "result": {"as_array_number": [123.0, 456.0, 789.0]},
            },
            "datetime": {
                "value": "2018-12-31T00:00:00+00:00",
                "result": {"as_string": "2018-12-31T00:00:00Z"},
            },
        }
        entry = self.add_entry(
            self.user, "Entry", self.entity, values={x: values[x]["value"] for x in values.keys()}
        )
        resp = self.client.get("/entry/api/v2/%s/histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 22)
        attrv = entry.get_attrv("datetime")
        self.assertEqual(
            resp.json()["results"][0],
            {
                "created_time": attrv.created_time.astimezone(self.TZ_INFO).isoformat(),
                "created_user": "guest",
                "curr_value": {"as_string": "2018-12-31T00:00:00Z"},
                "id": attrv.id,
                "parent_attr": {"id": attrv.parent_attr.id, "name": "datetime"},
                "prev_id": None,
                "prev_value": None,
                "type": AttrType.DATETIME,
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
        self.assertEqual(resp.json()["count"], 23)
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

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
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

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    @mock.patch("airone.lib.custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("airone.lib.custom_view.call_custom")
    def test_destroy_entries_with_custom_view(self, mock_call_custom):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        def side_effect(handler_name, entity_name, user, entry):
            raise ValidationError("delete error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(mock_call_custom.called)

        entry = self.add_entry(self.user, "entry2", self.entity)

        def side_effect(handler_name, entity_name, user, entry):
            self.assertTrue(handler_name in ["before_delete_entry_v2", "after_delete_entry_v2"])
            self.assertEqual(entity_name, self.entity.name)
            self.assertEqual(user, self.user)
            self.assertEqual(entry, entry)

        mock_call_custom.side_effect = side_effect
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(mock_call_custom.called)

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    @mock.patch("entry.tasks.notify_delete_entry.delay")
    def test_destroy_entries_notify(self, mock_task):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        self.client.delete("/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json")

        self.assertTrue(mock_task.called)

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    def test_delete_entries_without_all_parameter(self):
        # create test Items that would be deleted in this test
        items = [self.add_entry(self.user, "item-%d" % i, self.entity) for i in range(5)]

        # send request to delete only items[0]
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % items[0].id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        # check only items[0] was deleted and rest of items are still alive.
        [x.refresh_from_db() for x in items]
        self.assertFalse(items[0].is_active)
        self.assertTrue(all(x.is_active for x in items[1:]))

        # send request to delete all items
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s&isAll=false" % items[1].id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        # check only items[0] and items[1] are delete, and rest of items are still alived
        [x.refresh_from_db() for x in items]
        self.assertFalse(all(x.is_active for x in items[:2]))
        self.assertTrue(all(x.is_active for x in items[2:]))

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    def test_delete_entries_with_all_parameter(self):
        # create test Items that would be deleted in this test
        items = [self.add_entry(self.user, "item-%d" % i, self.entity) for i in range(5)]

        # send request to delete only items[0]
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % items[0].id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        # check only items[0] was deleted and rest of items are still alive.
        [x.refresh_from_db() for x in items]
        self.assertFalse(items[0].is_active)
        self.assertTrue(all(x.is_active for x in items[1:]))

        # send request to delete all items
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s&isAll=true" % items[1].id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        # check all items were deleted.
        [x.refresh_from_db() for x in items]
        self.assertFalse(any(x.is_active for x in items))

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    def test_delete_entries_with_all_parameter_and_attrinfo(self):
        # create test Items that would be deleted in this test
        items = [
            self.add_entry(
                self.user,
                "item-%d" % i,
                self.entity,
                values={
                    "val": "hoge" if i < 3 else "fuga",
                },
            )
            for i in range(5)
        ]

        # send request to delete all items with attrinfo
        attrinfo_as_str = json.dumps(
            [
                {"name": "ref", "keyword": "", "filterKey": "0"},
                {"name": "val", "keyword": "hoge", "filterKey": "3"},
            ]
        )
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s&isAll=true&attrinfo=%s"
            % (
                items[0].id,
                attrinfo_as_str,
            ),
            None,
            "application/json",
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        # check only items, which are matched with "val=hoge", were deleted.
        [x.refresh_from_db() for x in items]
        self.assertFalse(any(x.is_active for x in items[:3]))
        self.assertTrue(any(x.is_active for x in items[3:]))

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=tasks.create_entry_v2))
    def test_create_entry_with_default_values(self):
        """Test entries are created with default values from EntityAttr when no value provided"""
        # Create entity with attributes that have default values
        entity = self.create_entity(
            self.user,
            "TestEntity",
            attrs=[
                {"name": "string_with_default", "type": AttrType.STRING},
                {"name": "bool_with_default", "type": AttrType.BOOLEAN},
                {"name": "text_with_default", "type": AttrType.TEXT},
                {"name": "number_with_default", "type": AttrType.NUMBER},
                {"name": "string_no_default", "type": AttrType.STRING},
            ],
        )

        # Set default values for some attributes
        string_attr = entity.attrs.get(name="string_with_default")
        string_attr.default_value = "default string value"
        string_attr.save()

        bool_attr = entity.attrs.get(name="bool_with_default")
        bool_attr.default_value = True
        bool_attr.save()

        text_attr = entity.attrs.get(name="text_with_default")
        text_attr.default_value = "default text value"
        text_attr.save()

        number_attr = entity.attrs.get(name="number_with_default")
        number_attr.default_value = 42.5
        number_attr.save()

        # Create entry without providing values for attributes with defaults
        params = {
            "name": "test_entry",
            "attrs": [
                # Only provide value for one attribute, others should use defaults
                {"id": entity.attrs.get(name="string_no_default").id, "value": "provided value"}
            ],
        }

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Wait for entry creation job to complete
        job = Job.objects.filter(operation=JobOperation.CREATE_ENTRY_V2).last()
        self.assertEqual(job.status, JobStatus.DONE)

        # Verify entry was created with default values
        entry = Entry.objects.get(name="test_entry", schema=entity)
        self.assertIsNotNone(entry)

        # Check that attributes with default values were created with those defaults
        string_attr_value = entry.attrs.get(schema=string_attr)
        self.assertEqual(string_attr_value.get_latest_value().get_value(), "default string value")

        bool_attr_value = entry.attrs.get(schema=bool_attr)
        self.assertEqual(bool_attr_value.get_latest_value().get_value(), True)

        text_attr_value = entry.attrs.get(schema=text_attr)
        self.assertEqual(text_attr_value.get_latest_value().get_value(), "default text value")

        number_attr_value = entry.attrs.get(schema=number_attr)
        self.assertEqual(number_attr_value.get_latest_value().get_value(), 42.5)

        # Check that attribute without default was not created (no value provided)
        string_no_default_attr = entity.attrs.get(name="string_no_default")
        string_no_default_value = entry.attrs.get(schema=string_no_default_attr)
        self.assertEqual(string_no_default_value.get_latest_value().get_value(), "provided value")

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=tasks.create_entry_v2))
    def test_create_entry_provided_value_overrides_default(self):
        """Test that provided values override default values from EntityAttr"""
        # Create entity with attribute that has default value
        entity = self.create_entity(
            self.user,
            "TestEntity",
            attrs=[
                {"name": "string_attr", "type": AttrType.STRING},
                {"name": "bool_attr", "type": AttrType.BOOLEAN},
                {"name": "number_attr", "type": AttrType.NUMBER},
            ],
        )

        # Set default values
        string_attr = entity.attrs.get(name="string_attr")
        string_attr.default_value = "default value"
        string_attr.save()

        bool_attr = entity.attrs.get(name="bool_attr")
        bool_attr.default_value = True
        bool_attr.save()

        number_attr = entity.attrs.get(name="number_attr")
        number_attr.default_value = 123.456
        number_attr.save()

        # Create entry providing values that should override defaults
        params = {
            "name": "test_entry_override",
            "attrs": [
                {"id": string_attr.id, "value": "provided value"},
                {"id": bool_attr.id, "value": False},
                {"id": number_attr.id, "value": 999.999},
            ],
        }

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Wait for entry creation job to complete
        job = Job.objects.filter(operation=JobOperation.CREATE_ENTRY_V2).last()
        self.assertEqual(job.status, JobStatus.DONE)

        # Verify entry was created with provided values, not defaults
        entry = Entry.objects.get(name="test_entry_override", schema=entity)

        string_attr_value = entry.attrs.get(schema=string_attr)
        self.assertEqual(
            string_attr_value.get_latest_value().get_value(), "provided value"
        )  # Not default

        bool_attr_value = entry.attrs.get(schema=bool_attr)
        self.assertEqual(
            bool_attr_value.get_latest_value().get_value(), False
        )  # Not default (True)

        number_attr_value = entry.attrs.get(schema=number_attr)
        self.assertEqual(
            number_attr_value.get_latest_value().get_value(), 999.999
        )  # Not default (123.456)

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=tasks.create_entry_v2))
    def test_create_entry_unsupported_type_no_default(self):
        """Test that unsupported types don't get default values applied"""
        # Create reference entity
        ref_entity = self.create_entity(self.user, "RefEntity", attrs=[])

        # Create entity with unsupported type attribute that has default_value
        entity = self.create_entity(
            self.user,
            "TestEntity",
            attrs=[
                {"name": "object_attr", "type": AttrType.OBJECT, "referral": [ref_entity]},
                {"name": "date_attr", "type": AttrType.DATE},
            ],
        )

        # Try to set default values (should be ignored for unsupported types)
        object_attr = entity.attrs.get(name="object_attr")
        object_attr.default_value = "ignored value"
        object_attr.save()

        date_attr = entity.attrs.get(name="date_attr")
        date_attr.default_value = "2023-01-01"
        date_attr.save()

        # Create entry without providing values
        params = {
            "name": "test_entry_unsupported",
            "attrs": [],
        }

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Wait for entry creation job to complete
        job = Job.objects.filter(operation=JobOperation.CREATE_ENTRY_V2).last()
        self.assertEqual(job.status, JobStatus.DONE)

        # Verify entry was created but unsupported types should use type defaults, not custom
        entry = Entry.objects.get(name="test_entry_unsupported", schema=entity)

        # Since unsupported types don't apply default_value, these attributes should either
        # not have AttributeValues created or use the hardcoded type defaults
        object_attr_values = entry.attrs.filter(schema=object_attr)
        date_attr_values = entry.attrs.filter(schema=date_attr)

        # For unsupported types, no custom default should be applied
        # The behavior should be the same as before (either no value or type default)
        if object_attr_values.exists():
            object_attr_value = object_attr_values.first()
            # Should not be the custom default "ignored value"
            self.assertNotEqual(object_attr_value.get_latest_value().get_value(), "ignored value")

        if date_attr_values.exists():
            date_attr_value = date_attr_values.first()
            # Should not be the custom default "2023-01-01"
            self.assertNotEqual(date_attr_value.get_latest_value().get_value(), "2023-01-01")

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=tasks.create_entry_v2))
    def test_create_entry_number_default_value_scenarios(self):
        """Test Number type default value scenarios (integer, float, zero, negative)"""
        # Create entity with number attributes
        entity = self.create_entity(
            self.user,
            "NumberTestEntity",
            attrs=[
                {"name": "number_int", "type": AttrType.NUMBER},
                {"name": "number_float", "type": AttrType.NUMBER},
                {"name": "number_zero", "type": AttrType.NUMBER},
                {"name": "number_negative", "type": AttrType.NUMBER},
            ],
        )

        # Set different number default values
        number_int_attr = entity.attrs.get(name="number_int")
        number_int_attr.default_value = 42
        number_int_attr.save()

        number_float_attr = entity.attrs.get(name="number_float")
        number_float_attr.default_value = 3.14159
        number_float_attr.save()

        number_zero_attr = entity.attrs.get(name="number_zero")
        number_zero_attr.default_value = 0
        number_zero_attr.save()

        number_negative_attr = entity.attrs.get(name="number_negative")
        number_negative_attr.default_value = -123.45
        number_negative_attr.save()

        # Create entry without providing values for number attributes
        params = {
            "name": "test_entry_number_defaults",
            "attrs": [],
        }

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Wait for entry creation job to complete
        job = Job.objects.filter(operation=JobOperation.CREATE_ENTRY_V2).last()
        self.assertEqual(job.status, JobStatus.DONE)

        # Verify entry was created with number default values
        entry = Entry.objects.get(name="test_entry_number_defaults", schema=entity)
        self.assertIsNotNone(entry)

        # Check integer default
        number_int_value = entry.attrs.get(schema=number_int_attr)
        self.assertEqual(number_int_value.get_latest_value().get_value(), 42)

        # Check float default
        number_float_value = entry.attrs.get(schema=number_float_attr)
        self.assertAlmostEqual(number_float_value.get_latest_value().get_value(), 3.14159, places=5)

        # Check zero default
        number_zero_value = entry.attrs.get(schema=number_zero_attr)
        self.assertEqual(number_zero_value.get_latest_value().get_value(), 0)

        # Check negative default
        number_negative_value = entry.attrs.get(schema=number_negative_attr)
        self.assertEqual(number_negative_value.get_latest_value().get_value(), -123.45)

    @patch("entry.tasks.create_entry_v2.delay", Mock(side_effect=tasks.create_entry_v2))
    def test_create_and_retrieve_entry_with_number_attr(self):
        entry_name = "test_entry_with_number"
        number_value = 123.45
        # Ensure 'num' attribute exists in self.entity, created via
        # ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
        num_entity_attr = self.entity.attrs.get(name="num")

        payload = {
            "name": entry_name,
            "schema": self.entity.id,
            "attrs": [{"id": num_entity_attr.id, "value": number_value}],
        }

        # Create Entry with Number attribute
        resp_create = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload, "application/json"
        )
        self.assertEqual(resp_create.status_code, status.HTTP_202_ACCEPTED, resp_create.content)

        # Wait for job to complete and get the created entry
        created_entry = Entry.objects.filter(name=entry_name, schema=self.entity).first()
        self.assertIsNotNone(created_entry, "Entry was not created")
        created_entry_id = created_entry.id

        # Retrieve the created entry
        resp_get = self.client.get(f"/entry/api/v2/{created_entry_id}/")
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.content)
        retrieved_data = resp_get.json()
        self.assertEqual(retrieved_data["name"], entry_name)

        # Check 'num' attribute in retrieval response
        num_attr_retrieved = None
        for attr in retrieved_data.get("attrs", []):
            if attr["schema"]["name"] == "num":
                num_attr_retrieved = attr
                break
        self.assertIsNotNone(num_attr_retrieved, "'num' attribute not found in retrieval response")
        # Verify the value of the 'num' attribute - check for as_number format
        self.assertAlmostEqual(num_attr_retrieved["value"]["as_number"], number_value, places=5)

        # Test with None value for number
        entry_name_none = "test_entry_with_number_none"
        payload_none = {
            "name": entry_name_none,
            "schema": self.entity.id,
            "attrs": [{"id": num_entity_attr.id, "value": None}],
        }
        resp_create_none = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload_none, "application/json"
        )
        self.assertEqual(
            resp_create_none.status_code, status.HTTP_202_ACCEPTED, resp_create_none.content
        )

        # Wait for job to complete and get the created entry
        created_entry_none = Entry.objects.filter(name=entry_name_none, schema=self.entity).first()
        self.assertIsNotNone(created_entry_none, "Entry with None value was not created")
        created_entry_id_none = created_entry_none.id

        resp_get_none = self.client.get(f"/entry/api/v2/{created_entry_id_none}/")
        self.assertEqual(resp_get_none.status_code, status.HTTP_200_OK, resp_get_none.content)
        retrieved_data_none = resp_get_none.json()
        num_attr_retrieved_none = None
        for attr in retrieved_data_none.get("attrs", []):
            if attr["schema"]["name"] == "num":
                num_attr_retrieved_none = attr
                break
        self.assertIsNotNone(num_attr_retrieved_none)
        self.assertIsNone(num_attr_retrieved_none["value"]["as_number"])

        # Test with invalid number value
        entry_name_invalid = "test_entry_with_invalid_number"
        payload_invalid = {
            "name": entry_name_invalid,
            "schema": self.entity.id,
            "attrs": [
                {
                    "id": num_entity_attr.id,
                    "value": "not-a-number",  # Invalid string for number
                }
            ],
        }
        resp_create_invalid = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload_invalid, "application/json"
        )
        self.assertEqual(
            resp_create_invalid.status_code,
            status.HTTP_400_BAD_REQUEST,
            resp_create_invalid.content,
        )

    @patch("entry.tasks.create_entry_v2.delay", Mock(side_effect=tasks.create_entry_v2))
    def test_create_and_retrieve_entry_with_array_number_attr(self):
        """Test array number functionality including creation, retrieval, and validation"""
        entry_name = "test_entry_with_array_number"
        number_values = [123.45, 67.89, 0.123, -45.67]

        # Ensure 'nums' attribute exists in self.entity
        nums_entity_attr = self.entity.attrs.get(name="nums")

        payload = {
            "name": entry_name,
            "schema": self.entity.id,
            "attrs": [{"id": nums_entity_attr.id, "value": number_values}],
        }

        # Create Entry with Array Number attribute
        resp_create = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload, "application/json"
        )
        self.assertEqual(resp_create.status_code, status.HTTP_202_ACCEPTED, resp_create.content)

        # Wait for job to complete and get the created entry
        created_entry = Entry.objects.filter(name=entry_name, schema=self.entity).first()
        self.assertIsNotNone(created_entry, "Entry was not created")
        created_entry_id = created_entry.id

        # Retrieve the created entry
        resp_get = self.client.get(f"/entry/api/v2/{created_entry_id}/")
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.content)
        retrieved_data = resp_get.json()
        self.assertEqual(retrieved_data["name"], entry_name)

        # Check 'nums' attribute in retrieval response
        nums_attr_retrieved = None
        for attr in retrieved_data.get("attrs", []):
            if attr["schema"]["name"] == "nums":
                nums_attr_retrieved = attr
                break
        self.assertIsNotNone(
            nums_attr_retrieved, "'nums' attribute not found in retrieval response"
        )

        # Verify the values of the 'nums' attribute - check for as_array_number format
        retrieved_values = nums_attr_retrieved["value"]["as_array_number"]
        self.assertEqual(len(retrieved_values), len(number_values))
        for i, expected_val in enumerate(number_values):
            self.assertAlmostEqual(retrieved_values[i], expected_val, places=5)

    @patch("entry.tasks.create_entry_v2.delay", Mock(side_effect=tasks.create_entry_v2))
    def test_array_number_with_null_values(self):
        """Test array number with null/None values"""
        entry_name = "test_entry_array_number_with_nulls"
        number_values = [123.45, None, 67.89, None, 0.0]

        nums_entity_attr = self.entity.attrs.get(name="nums")

        payload = {
            "name": entry_name,
            "schema": self.entity.id,
            "attrs": [{"id": nums_entity_attr.id, "value": number_values}],
        }

        resp_create = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload, "application/json"
        )
        self.assertEqual(resp_create.status_code, status.HTTP_202_ACCEPTED, resp_create.content)

        created_entry = Entry.objects.filter(name=entry_name, schema=self.entity).first()
        self.assertIsNotNone(created_entry, "Entry was not created")

        resp_get = self.client.get(f"/entry/api/v2/{created_entry.id}/")
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.content)
        retrieved_data = resp_get.json()

        nums_attr_retrieved = None
        for attr in retrieved_data.get("attrs", []):
            if attr["schema"]["name"] == "nums":
                nums_attr_retrieved = attr
                break
        self.assertIsNotNone(nums_attr_retrieved)

        retrieved_values = nums_attr_retrieved["value"]["as_array_number"]
        expected_values = [123.45, None, 67.89, None, 0.0]
        self.assertEqual(len(retrieved_values), len(expected_values))

        for i, expected_val in enumerate(expected_values):
            if expected_val is None:
                self.assertIsNone(retrieved_values[i])
            else:
                self.assertAlmostEqual(retrieved_values[i], expected_val, places=5)

    @patch("entry.tasks.create_entry_v2.delay", Mock(side_effect=tasks.create_entry_v2))
    def test_array_number_empty_array(self):
        """Test array number with empty array"""
        entry_name = "test_entry_array_number_empty"
        number_values = []

        nums_entity_attr = self.entity.attrs.get(name="nums")

        payload = {
            "name": entry_name,
            "schema": self.entity.id,
            "attrs": [{"id": nums_entity_attr.id, "value": number_values}],
        }

        resp_create = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload, "application/json"
        )
        self.assertEqual(resp_create.status_code, status.HTTP_202_ACCEPTED, resp_create.content)

        created_entry = Entry.objects.filter(name=entry_name, schema=self.entity).first()
        self.assertIsNotNone(created_entry, "Entry was not created")

        resp_get = self.client.get(f"/entry/api/v2/{created_entry.id}/")
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.content)
        retrieved_data = resp_get.json()

        nums_attr_retrieved = None
        for attr in retrieved_data.get("attrs", []):
            if attr["schema"]["name"] == "nums":
                nums_attr_retrieved = attr
                break
        self.assertIsNotNone(nums_attr_retrieved)

        retrieved_values = nums_attr_retrieved["value"]["as_array_number"]
        self.assertEqual(retrieved_values, [])

    @patch("entry.tasks.create_entry_v2.delay", Mock(side_effect=tasks.create_entry_v2))
    def test_array_number_edge_case_values(self):
        """Test array number with edge case values like large numbers, small numbers, etc."""
        entry_name = "test_entry_array_number_edge_cases"
        # Test with various edge case numbers
        number_values = [
            0,
            -0,
            1e10,  # Large positive number
            -1e10,  # Large negative number
            1e-10,  # Very small positive number
            -1e-10,  # Very small negative number
            math.pi,  # Irrational number
            math.e,  # Euler's number
        ]

        nums_entity_attr = self.entity.attrs.get(name="nums")

        payload = {
            "name": entry_name,
            "schema": self.entity.id,
            "attrs": [{"id": nums_entity_attr.id, "value": number_values}],
        }

        resp_create = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload, "application/json"
        )
        self.assertEqual(resp_create.status_code, status.HTTP_202_ACCEPTED, resp_create.content)

        created_entry = Entry.objects.filter(name=entry_name, schema=self.entity).first()
        self.assertIsNotNone(created_entry, "Entry was not created")

        resp_get = self.client.get(f"/entry/api/v2/{created_entry.id}/")
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.content)
        retrieved_data = resp_get.json()

        nums_attr_retrieved = None
        for attr in retrieved_data.get("attrs", []):
            if attr["schema"]["name"] == "nums":
                nums_attr_retrieved = attr
                break
        self.assertIsNotNone(nums_attr_retrieved)

        retrieved_values = nums_attr_retrieved["value"]["as_array_number"]
        self.assertEqual(len(retrieved_values), len(number_values))

        for i, expected_val in enumerate(number_values):
            self.assertAlmostEqual(retrieved_values[i], expected_val, places=10)

    def test_array_number_invalid_values(self):
        """Test array number with invalid string values"""
        entry_name = "test_entry_array_number_invalid"
        # Mix of valid numbers and invalid strings
        invalid_values = [123.45, "not-a-number", 67.89, "invalid", ""]

        nums_entity_attr = self.entity.attrs.get(name="nums")

        payload = {
            "name": entry_name,
            "schema": self.entity.id,
            "attrs": [{"id": nums_entity_attr.id, "value": invalid_values}],
        }

        resp_create = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload, "application/json"
        )
        # This should return a validation error
        self.assertEqual(
            resp_create.status_code,
            status.HTTP_400_BAD_REQUEST,
            resp_create.content,
        )

    def test_list_self_histories(self):
        """Test list self histories endpoint - normal case"""
        # Create an entry with initial name
        initial_name = "initial_entry"
        entry = self.add_entry(self.user, initial_name, self.entity)

        # Update the entry name to create history records
        entry.name = "updated_entry_1"
        entry.save()

        entry.name = "updated_entry_2"
        entry.save()

        # Make API request to list self histories
        resp = self.client.get("/entry/api/v2/%s/self_histories/" % entry.id)

        # Check response status and structure
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("count", data)
        self.assertIn("results", data)

        # Should have 3 history records (initial creation + 2 updates)
        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["results"]), 3)

        # Debug: print all records to understand the order
        for i, record in enumerate(data["results"]):
            print(f"DEBUG: record[{i}] = {record}")

        # Check the most recent record (should be at index 0 due to ordering by -history_date)
        latest_record = data["results"][0]
        self.assertEqual(latest_record["name"], "updated_entry_2")
        self.assertEqual(latest_record["history_type"], "~")  # update

        # Since simple_history doesn't automatically track users in tests,
        # it will be None and serializer will return default value "システム"
        self.assertEqual(latest_record["history_user"], "システム")
        self.assertIn("history_id", latest_record)
        self.assertIn("history_date", latest_record)

        # Check second record
        second_record = data["results"][1]
        self.assertEqual(second_record["name"], "updated_entry_1")
        self.assertEqual(second_record["prev_name"], "initial_entry")

        # Check first record (creation)
        first_record = data["results"][2]
        self.assertEqual(first_record["name"], initial_name)
        self.assertEqual(first_record["history_type"], "+")  # creation

    def test_list_self_histories_without_permission(self):
        """Test list self histories endpoint - permission check"""
        # Create entry without permission
        entry = self.add_entry(self.user, "test_entry", self.entity, {}, False)

        # Test without any permission
        resp = self.client.get("/entry/api/v2/%s/self_histories/" % entry.id)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # Grant read permission
        self.role.users.add(self.user)
        entry.readable.roles.add(self.role)

        # Should now work
        resp = self.client.get("/entry/api/v2/%s/self_histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)

    def test_list_self_histories_with_invalid_entry_id(self):
        """Test list self histories endpoint - non-existent entry"""
        non_existent_id = 9999999
        resp = self.client.get("/entry/api/v2/%s/self_histories/" % non_existent_id)
        self.assertEqual(resp.status_code, 404)

    def test_restore_self_history(self):
        """Test restore self history endpoint - normal case"""
        # Create an entry with initial name
        initial_name = "original_name"
        entry = self.add_entry(self.user, initial_name, self.entity)

        # Update the entry name to create history
        entry.name = "modified_name"
        entry.save()

        # Get the history record for the original name
        history_records = entry.history.all().order_by("-history_date")
        original_history = None
        for record in history_records:
            if record.name == initial_name:
                original_history = record
                break

        self.assertIsNotNone(original_history)

        # Restore to original name using API
        payload = {"history_id": original_history.history_id}
        resp = self.client.post(
            "/entry/api/v2/%s/restore_self_history/" % entry.id,
            payload,
            "application/json",
        )

        # Check response
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("message", data)
        self.assertEqual(data["restored_name"], initial_name)

        # Verify entry name was restored
        entry.refresh_from_db()
        self.assertEqual(entry.name, initial_name)

    def test_restore_self_history_without_permission(self):
        """Test restore self history endpoint - permission check"""
        # Create entry without write permission
        entry = self.add_entry(self.user, "test_entry", self.entity, {}, False)

        # Grant only read permission
        self.role.users.add(self.user)
        entry.readable.roles.add(self.role)

        # Get a history record
        history_record = entry.history.first()

        # Try to restore without write permission
        payload = {"history_id": history_record.history_id}
        resp = self.client.post(
            "/entry/api/v2/%s/restore_self_history/" % entry.id,
            payload,
            "application/json",
        )

        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

    def test_restore_self_history_with_invalid_history_id(self):
        """Test restore self history endpoint - non-existent history ID"""
        entry = self.add_entry(self.user, "test_entry", self.entity)

        # Use invalid history ID
        payload = {"history_id": 9999999}
        resp = self.client.post(
            "/entry/api/v2/%s/restore_self_history/" % entry.id,
            payload,
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        response_data = resp.json()
        self.assertIsInstance(response_data, list)
        self.assertEqual(len(response_data), 1)
        self.assertIn("指定された履歴が見つかりません", response_data[0]["message"])

    def test_restore_self_history_with_duplicate_name(self):
        """Test restore self history endpoint - duplicate name error"""
        # Create two entries
        entry1 = self.add_entry(self.user, "entry_1", self.entity)
        entry2 = self.add_entry(self.user, "entry_2", self.entity)

        # Update entry1 name
        entry1.name = "entry_1_modified"
        entry1.save()

        # Get history record for original entry1 name
        history_records = entry1.history.all()
        original_history = None
        for record in history_records:
            if record.name == "entry_1":
                original_history = record
                break

        # Now change entry2 name to "entry_1"
        entry2.name = "entry_1"
        entry2.save()

        # Try to restore entry1 to "entry_1" - should fail due to duplicate
        payload = {"history_id": original_history.history_id}
        resp = self.client.post(
            "/entry/api/v2/%s/restore_self_history/" % entry1.id,
            payload,
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        response_data = resp.json()
        self.assertIsInstance(response_data, list)
        self.assertEqual(len(response_data), 1)
        self.assertIn("既に使用されています", response_data[0]["message"])

    def test_restore_self_history_with_alias_conflict(self):
        """Test restore self history endpoint - alias name conflict error"""
        from entry.models import AliasEntry

        # Create an entry
        entry = self.add_entry(self.user, "original_name", self.entity)

        # Update entry name
        entry.name = "modified_name"
        entry.save()

        # Create alias with the original name
        AliasEntry.objects.create(name="original_name", entry=entry)

        # Get history record for the original name
        history_records = entry.history.all()
        original_history = None
        for record in history_records:
            if record.name == "original_name":
                original_history = record
                break

        # Try to restore to original name - should fail due to alias conflict
        payload = {"history_id": original_history.history_id}
        resp = self.client.post(
            "/entry/api/v2/%s/restore_self_history/" % entry.id,
            payload,
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        response_data = resp.json()
        self.assertIsInstance(response_data, list)
        self.assertEqual(len(response_data), 1)
        self.assertIn("エイリアスで使用されています", response_data[0]["message"])

    @patch("entry.tasks.bulk_update_entries.delay", Mock(side_effect=tasks.bulk_update_entries))
    def test_bulk_update_items(self):
        # Create items for bulk updating
        for index, str_val in enumerate(["foo", "bar", "baz"]):
            self.add_entry(
                self.user,
                "item-%s" % index,
                self.entity,
                values={
                    "val": str_val,
                },
            )

        # Make parameters for sending server
        updating_attr = self.entity.attrs.get(name="val")

        params = {
            "value": {"id": updating_attr.id, "value": "updated"},
            "modelid": self.entity.id,
            "attrinfo": [{"name": "val", "filter_key": FilterKey.TEXT_CONTAINED, "keyword": "ba"}],
            "hint_entry": {"filter_key": EntryFilterKey.TEXT_CONTAINED, "keyword": "item"},
        }
        resp = self.client.put(
            "/entry/api/v2/bulk/",
            params,
            "application/json",
        )
        self.assertEqual(resp.status_code, 202)

        # Check items are pudate expectedly
        expected_values = [
            ("item-0", "foo"),
            ("item-1", "updated"),  # this one should be updated from bar to updated
            ("item-2", "updated"),  # this one should be updated from baz to updated
        ]

        for itemname, expected_value in expected_values:
            item = Entry.objects.get(name=itemname, schema=self.entity)
            self.assertEqual(item.get_attrv("val").value, expected_value)

    @patch("entry.tasks.bulk_update_entries.delay", Mock(side_effect=tasks.bulk_update_entries))
    def test_bulk_update_items_with_referral_name_filter(self):
        """
        This tests bulk update when referral_name filter is used for advanced search.
        """
        # Create items that are referred by other items
        target_items = [self.add_entry(self.user, f"item-{i}", self.entity) for i in range(3)]
        [
            self.add_entry(
                self.user, "refering-item-%s" % v, self.entity, values={"ref": target_items[i]}
            )
            for (i, v) in enumerate(["foo", "bar", "baz"])
        ]

        # Make parameters for sending server
        updating_attr = self.entity.attrs.get(name="val")
        params = {
            "value": {"id": updating_attr.id, "value": "updated"},
            "modelid": self.entity.id,
            "referral_name": "ba",  # this would be matched with "bar" and "baz"
        }
        resp = self.client.put(
            "/entry/api/v2/bulk/",
            params,
            "application/json",
        )
        self.assertEqual(resp.status_code, 202)

        # Check items are pudate expectedly
        expected_values = [
            ("item-0", ""),
            ("item-1", "updated"),  # this one should be updated from bar to updated
            ("item-2", "updated"),  # this one should be updated from baz to updated
        ]

        for itemname, expected_value in expected_values:
            item = Entry.objects.get(name=itemname, schema=self.entity)
            self.assertEqual(item.get_attrv("val").value, expected_value)

    @patch.object(Job, "is_canceled", Mock(return_value=True))
    @patch("entry.tasks.bulk_update_entries.delay", Mock(side_effect=tasks.bulk_update_entries))
    def test_bulk_update_items_with_canceled(self):
        """
        This tests bulk update when the job is canceled during processing.
        """
        # Create items for bulk updating
        for index, str_val in enumerate(["foo", "bar", "baz"]):
            self.add_entry(
                self.user,
                "item-%s" % index,
                self.entity,
                values={
                    "val": str_val,
                },
            )

        # Make parameters for sending server
        updating_attr = self.entity.attrs.get(name="val")

        params = {
            "value": {"id": updating_attr.id, "value": "updated"},
            "modelid": self.entity.id,
            "attrinfo": [],
        }
        resp = self.client.put(
            "/entry/api/v2/bulk/",
            params,
            "application/json",
        )
        self.assertEqual(resp.status_code, 202)

        # Check items are not updated due to cancellation
        expected_values = [
            # These won't be updated because the job is canceled
            ("item-0", "foo"),
            ("item-1", "bar"),
            ("item-2", "baz"),
        ]
        for itemname, expected_value in expected_values:
            item = Entry.objects.get(name=itemname, schema=self.entity)
            self.assertEqual(item.get_attrv("val").value, expected_value)

        # check job text shows expected message
        job = Job.objects.filter(operation=JobOperation.BULK_EDIT_ENTRY).last()
        self.assertEqual(job.text, "Now updating... (progress: [    1/    3])")
