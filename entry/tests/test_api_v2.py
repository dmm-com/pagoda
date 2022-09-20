import datetime
import errno
import json
from unittest import mock
from unittest.mock import Mock, patch

import yaml
from rest_framework.exceptions import ValidationError

from airone.lib.test import AironeViewTest
from airone.lib.types import (
    AttrTypeArrNamedObj,
    AttrTypeArrObj,
    AttrTypeArrStr,
    AttrTypeNamedObj,
    AttrTypeObj,
    AttrTypeStr,
    AttrTypeText,
    AttrTypeValue,
)
from entity.models import Entity, EntityAttr
from entry import tasks
from entry.models import Attribute, AttributeValue, Entry
from entry.settings import CONFIG
from group.models import Group
from job.models import Job, JobOperation
from role.models import Role
from user.models import User


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        self.user: User = self.guest_login()
        self.role: Role = Role.objects.create(name="Role")

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
                        "hoge": {
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
                            "foo": {
                                "id": self.ref_entry.id,
                                "name": self.ref_entry.name,
                                "schema": {
                                    "id": self.ref_entry.schema.id,
                                    "name": self.ref_entry.schema.name,
                                },
                            },
                        },
                        {
                            "bar": {
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
        self.role.permissions.add(self.entity.readable)
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
        self.role.permissions.add(entry.readable)
        resp = self.client.get("/entry/api/v2/%d/" % entry.id)
        self.assertEqual(resp.status_code, 200)

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
        self.assertEqual(search_result["hits"]["total"], 1)

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
        self.role.permissions.add(self.entity.readable)
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
        self.role.permissions.add(self.entity.writable)
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
        self.role.permissions.add(entry.readable)
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
        self.role.permissions.add(entry.writable)
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
        self.role.permissions.add(self.entity.readable)
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
        self.role.permissions.add(self.entity.writable)
        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission full entity
        self.role.permissions.add(self.entity.full)
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
        self.role.permissions.add(entry.readable)
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
        self.role.permissions.add(entry.writable)
        resp = self.client.delete("/entry/api/v2/%s/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission full entry
        self.role.permissions.add(entry.full)
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
        self.assertEqual(resp.content, b"")

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
        self.role.permissions.add(self.entity.readable)
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
        self.role.permissions.add(self.entity.writable)
        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission full entity
        self.role.permissions.add(self.entity.full)
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
        self.role.permissions.add(entry.readable)
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
        self.role.permissions.add(entry.writable)
        resp = self.client.post("/entry/api/v2/%s/restore/" % entry.id, None, "application/json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission full entry
        self.role.permissions.add(entry.full)
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
        self.role.permissions.add(self.entity.readable)
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
        self.role.permissions.add(self.entity.writable)
        resp = self.client.post(
            "/entry/api/v2/%s/copy/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission full entity
        self.role.permissions.add(self.entity.full)
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
        self.role.permissions.add(entry.readable)
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
        self.role.permissions.add(entry.writable)
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

        # permission full entry
        self.role.permissions.add(entry.full)
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
        self.assertEqual(results[0]["id"], entry.id)
        self.assertEqual(results[0]["name"], entry.name)

    def test_referral_unrelated_to_entry(self):
        resp = self.client.get("/entry/api/v2/%s/referral/" % 99999)  # invalid entry id
        self.assertEqual(resp.status_code, 200)

        resp_data = resp.json()
        results = resp_data["results"]
        self.assertEqual(len(results), 0)

    @patch("entry.tasks.export_entries.delay", Mock(side_effect=tasks.export_entries))
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
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY.value)
        self.assertEqual(job.status, Job.STATUS["DONE"])
        self.assertEqual(job.text, "entry_ほげ.yaml")

        obj = yaml.load(job.get_cache(), Loader=yaml.SafeLoader)
        self.assertTrue(entity.name in obj)

        self.assertEqual(len(obj[entity.name]), 1)
        entry_data = obj[entity.name][0]
        self.assertTrue(all(["name" in entry_data and "attrs" in entry_data]))

        self.assertEqual(entry_data["name"], entry.name)
        self.assertEqual(len(entry_data["attrs"]), entry.attrs.count())
        self.assertEqual(entry_data["attrs"]["foo"], "fuga")
        self.assertEqual(entry_data["attrs"]["bar"], "fuga")

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
        self.assertTrue(all([x in obj["ほげ"][0]["attrs"] for x in ["foo", "bar"]]))

        # check unpermitted attribute doesn't exist in the result
        self.assertFalse("new_attr" in obj["ほげ"][0]["attrs"])

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
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY.value)
        self.assertEqual(job.text, "entry_ほげ.yaml")
        with self.assertRaises(OSError) as e:
            raise OSError

        if e.exception.errno == errno.ENOENT:
            job.get_cache()

    @patch("entry.tasks.export_entries.delay", Mock(side_effect=tasks.export_entries))
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
        for (name, type_index) in [("grp", "group"), ("arr_group", "array_group")]:
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
            "bool": "True",
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
            "bool": "True",
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
            # "val": None,
            "vals": [],
            "ref": {"id": "", "name": ""},
            "refs": [],
            "name": {"": {"id": "", "name": ""}},
            "names": [],
            "group": {"id": "", "name": ""},
            "groups": [],
            "bool": "False",
            # "text": None,
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
        self.role.permissions.add(self.entity.readable)
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
        self.role.permissions.add(self.entity.writable)
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
