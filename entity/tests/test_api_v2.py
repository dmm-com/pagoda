import datetime
import json
import logging
from datetime import timezone
from unittest import mock

import requests
import yaml
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError

from acl.models import ACLBase
from airone.lib.log import Logger
from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from entity import tasks
from entity.models import Entity, EntityAttr
from entry.models import Entry
from entry.tasks import create_entry_v2
from group.models import Group
from role.models import Role
from trigger import tasks as trigger_tasks
from trigger.models import TriggerCondition
from user.models import History, User
from webhook.models import Webhook


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

        self.entity: Entity = self.create_entity(
            **{
                "user": self.user,
                "name": "test-entity",
                "attrs": self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY,
                "webhooks": [{"url": "http://airone.com/"}],
            }
        )

    def _send_request_item_creation(self, model, params, expected_http_response_code):
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % model.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, expected_http_response_code)

        return resp

    def test_retrieve_entity(self):
        self.entity.attrs.all().delete()
        self.entity.webhooks.all().delete()
        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {
                "id": self.entity.id,
                "is_toplevel": False,
                "item_name_pattern": "",
                "name": "test-entity",
                "note": "",
                "status": 0,
                "attrs": [],
                "webhooks": [],
                "is_public": True,
                "has_ongoing_changes": False,
            },
        )

        self.entity.note = "hoge"
        self.entity.status = Entity.STATUS_TOP_LEVEL
        self.entity.save()

        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.json()["note"], "hoge")
        self.assertEqual(resp.json()["is_toplevel"], True)

    def test_retrieve_entity_with_attr(self):
        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, 200)
        self.maxDiff = None
        self.assertEqual(
            resp.json()["attrs"],
            [
                {
                    "id": self.entity.attrs.get(name="val").id,
                    "index": 0,
                    "name": "val",
                    "type": AttrType.STRING,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="vals").id,
                    "index": 1,
                    "name": "vals",
                    "type": AttrType.ARRAY_STRING,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="ref").id,
                    "index": 2,
                    "name": "ref",
                    "type": AttrType.OBJECT,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="refs").id,
                    "index": 3,
                    "name": "refs",
                    "type": AttrType.ARRAY_OBJECT,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="name").id,
                    "index": 4,
                    "name": "name",
                    "type": AttrType.NAMED_OBJECT,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="names").id,
                    "index": 5,
                    "name": "names",
                    "type": AttrType.ARRAY_NAMED_OBJECT,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="group").id,
                    "index": 6,
                    "name": "group",
                    "type": AttrType.GROUP,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="groups").id,
                    "index": 7,
                    "name": "groups",
                    "type": AttrType.ARRAY_GROUP,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="bool").id,
                    "index": 8,
                    "name": "bool",
                    "type": AttrType.BOOLEAN,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="text").id,
                    "index": 9,
                    "name": "text",
                    "type": AttrType.TEXT,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="date").id,
                    "index": 10,
                    "name": "date",
                    "type": AttrType.DATE,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="role").id,
                    "index": 11,
                    "name": "role",
                    "type": AttrType.ROLE,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="roles").id,
                    "index": 12,
                    "name": "roles",
                    "type": AttrType.ARRAY_ROLE,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="datetime").id,
                    "index": 13,
                    "name": "datetime",
                    "type": AttrType.DATETIME,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="num").id,
                    "index": 14,
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "name": "num",
                    "referral": [],
                    "type": AttrType.NUMBER,
                    "note": "",
                    "default_value": None,
                },
                {
                    "id": self.entity.attrs.get(name="nums").id,
                    "index": 15,
                    "name": "nums",
                    "type": AttrType.ARRAY_NUMBER,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "is_summarized": False,
                    "is_writable": True,
                    "referral": [],
                    "note": "",
                    "default_value": None,
                },
            ],
        )

        entity_attr: EntityAttr = self.entity.attrs.get(name="refs")
        entity_attr.index = 16
        entity_attr.is_delete_in_chain = True
        entity_attr.is_mandatory = True
        entity_attr.referral.add(self.ref_entity)
        entity_attr.save()

        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(
            resp.json()["attrs"][-1],
            {
                "id": entity_attr.id,
                "index": 16,
                "name": "refs",
                "type": AttrType.ARRAY_OBJECT,
                "is_mandatory": True,
                "is_delete_in_chain": True,
                "is_summarized": False,
                "is_writable": True,
                "referral": [
                    {
                        "id": self.ref_entity.id,
                        "name": "ref_entity",
                    }
                ],
                "note": "",
                "default_value": None,
            },
        )

    def test_retrieve_entity_with_webhook(self):
        webhook: Webhook = self.entity.webhooks.first()

        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.json()["webhooks"],
            [
                {
                    "id": webhook.id,
                    "url": "http://airone.com/",
                    "is_enabled": True,
                    "is_verified": True,
                    "verification_error_details": None,
                    "label": "hoge",
                    "headers": [],
                }
            ],
        )

        webhook.is_enabled = True
        webhook.is_verified = True
        webhook.label = "hoge"
        webhook.headers = [
            {"header_key": "key1", "header_value": "value1"},
            {"header_key": "key2", "header_value": "value2"},
        ]
        webhook.save()

        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(
            resp.json()["webhooks"],
            [
                {
                    "id": webhook.id,
                    "url": "http://airone.com/",
                    "is_enabled": True,
                    "is_verified": True,
                    "verification_error_details": None,
                    "label": "hoge",
                    "headers": [
                        {"header_key": "key1", "header_value": "value1"},
                        {"header_key": "key2", "header_value": "value2"},
                    ],
                }
            ],
        )

    def test_retrieve_entity_with_invalid_param(self):
        resp = self.client.get("/entity/api/v2/%d/" % 9999)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Entity matches the given query."}
        )

        resp = self.client.get("/entity/api/v2/%s/" % "hoge")
        self.assertEqual(resp.status_code, 404)

        self.entity.delete()
        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Entity matches the given query."}
        )

    def test_retrieve_entity_without_permission(self):
        # permission nothing entity
        self.entity.is_public = False
        self.entity.save()
        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
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
        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, 200)

        # permission nothing EntityAttr
        self.entity.writable.roles.add(self.role)
        entity_attr: EntityAttr = self.entity.attrs.first()
        entity_attr.is_public = False
        entity_attr.save()

        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["attrs"][0]["is_writable"])

        # permission readble EntityAttr update
        entity_attr.readable.roles.add(self.role)
        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["attrs"][0]["is_writable"])

        # permission writable EntityAttr
        entity_attr.writable.roles.add(self.role)
        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["attrs"][0]["is_writable"])

    @mock.patch("airone.lib.custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("airone.lib.custom_view.call_custom")
    def test_retrieve_entity_with_customview(self, mock_call_custom):
        def side_effect(handler_name, entity_name, entity, entity_attrs):
            self.assertEqual(handler_name, "get_entity_attr")
            self.assertEqual(entity_name, "test-entity")
            self.assertEqual(entity, self.entity)
            self.assertEqual(len(entity_attrs), len(self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY))

            # add attribute
            entity_attrs.append(
                {
                    "id": 0,
                    "name": "hoge",
                    "index": 11,
                    "type": AttrType.STRING,
                    "is_mandatory": False,
                    "is_delete_in_chain": False,
                    "referral": [],
                }
            )

            return entity_attrs

        mock_call_custom.side_effect = side_effect

        resp = self.client.get("/entity/api/v2/%s/" % self.entity.id)
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            len(resp.json()["attrs"]), len(self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY) + 1
        )
        self.assertEqual(
            resp.json()["attrs"][-1],
            {
                "id": 0,
                "name": "hoge",
                "index": 11,
                "type": AttrType.STRING,
                "is_mandatory": False,
                "is_delete_in_chain": False,
                "referral": [],
            },
        )

    def test_list_entity(self):
        resp = self.client.get("/entity/api/v2/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": self.ref_entity.id,
                        "is_toplevel": False,
                        "item_name_pattern": "",
                        "name": "ref_entity",
                        "note": "",
                        "status": 0,
                    },
                    {
                        "id": self.entity.id,
                        "is_toplevel": False,
                        "item_name_pattern": "",
                        "name": "test-entity",
                        "note": "",
                        "status": 0,
                    },
                ],
            },
        )

    def test_list_entity_with_is_toplevel(self):
        self.entity.status = Entity.STATUS_TOP_LEVEL
        self.entity.save()

        resp = self.client.get("/entity/api/v2/?is_toplevel=true")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()["results"][0]["id"], self.entity.id)

    def test_list_entity_with_deleted_entity(self):
        self.entity.delete()

        resp = self.client.get("/entity/api/v2/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()["results"][0]["id"], self.ref_entity.id)

    def test_list_entity_with_search(self):
        for search in ["ref", "REF"]:
            resp = self.client.get("/entity/api/v2/?search=%s" % search)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["count"], 1)
            self.assertEqual(resp.json()["results"][0]["id"], self.ref_entity.id)

    def test_list_entity_with_ordering_name(self):
        resp = self.client.get("/entity/api/v2/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([x["name"] for x in resp.json()["results"]], ["ref_entity", "test-entity"])

    def test_list_entity_without_permission(self):
        self.entity.is_public = False
        self.entity.save()
        self.ref_entity.is_public = False
        self.ref_entity.save()

        resp = self.client.get("/entity/api/v2/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 2)

    @mock.patch(
        "entity.tasks.create_entity_v2.delay", mock.Mock(side_effect=tasks.create_entity_v2)
    )
    def test_create_entity(self):
        params = {
            "name": "entity1",
            "note": "hoge",
            "is_toplevel": True,
            "attrs": [
                {
                    "name": "attr1",
                    "index": 1,
                    "type": AttrType.OBJECT,
                    "referral": [self.ref_entity.id],
                    "is_mandatory": True,
                    "is_delete_in_chain": True,
                    "is_summarized": True,
                    "note": "attr1 note",
                }
            ],
            "webhooks": [
                {
                    "url": "http://airone.com",
                    "label": "hoge",
                    "is_enabled": True,
                    "headers": [{"header_key": "Content-Type", "header_value": "application/json"}],
                }
            ],
        }

        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        entity: Entity = Entity.objects.get(name=params["name"])
        self.assertEqual(entity.name, "entity1")
        self.assertEqual(entity.note, "hoge")
        self.assertEqual(entity.status, Entity.STATUS_TOP_LEVEL)
        self.assertEqual(entity.created_user, self.user)

        self.assertEqual(entity.attrs.count(), 1)
        entity_attr: EntityAttr = entity.attrs.first()
        self.assertEqual(entity_attr.name, "attr1")
        self.assertEqual(entity_attr.index, 1)
        self.assertEqual(entity_attr.type, AttrType.OBJECT)
        self.assertEqual(entity_attr.referral.count(), 1)
        self.assertEqual(entity_attr.referral.first().id, self.ref_entity.id)
        self.assertEqual(entity_attr.is_mandatory, True)
        self.assertEqual(entity_attr.is_delete_in_chain, True)
        self.assertEqual(entity_attr.is_summarized, True)
        self.assertEqual(entity_attr.created_user, self.user)
        self.assertEqual(entity_attr.note, "attr1 note")

        self.assertEqual(entity.webhooks.count(), 1)
        webhook: Webhook = entity.webhooks.first()
        self.assertEqual(webhook.url, "http://airone.com")
        self.assertEqual(webhook.label, "hoge")
        self.assertEqual(webhook.is_enabled, True)
        self.assertEqual(
            webhook.headers, [{"header_key": "Content-Type", "header_value": "application/json"}]
        )

        history: History = History.objects.get(target_obj=entity)
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.operation, History.ADD_ENTITY)
        self.assertEqual(history.details.count(), 1)
        self.assertEqual(history.details.first().target_obj, entity_attr.aclbase_ptr)

    def test_create_entity_with_invalid_param(self):
        params = {}
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), {"name": [{"code": "AE-113000", "message": "This field is required."}]}
        )

        # name param
        params = {"name": ["hoge"]}
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), {"name": [{"code": "AE-121000", "message": "Not a valid string."}]}
        )

        params = {"name": "a" * (Entity._meta.get_field("name").max_length + 1)}
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
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

        params = {"name": "test-entity"}
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "name": [
                    {
                        "code": "AE-220000",
                        "message": "Duplication error. There is same named Entity",
                    }
                ]
            },
        )

        # note param
        params = {
            "name": "hoge",
            "note": ["hoge"],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), {"note": [{"code": "AE-121000", "message": "Not a valid string."}]}
        )

        params = {
            "name": "hoge",
            "note": "a" * (Entity._meta.get_field("note").max_length + 1),
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "note": [
                    {
                        "code": "AE-122000",
                        "message": "Ensure this field has no more than 200 characters.",
                    }
                ]
            },
        )

        # is_toplevel param
        params = {
            "name": "hoge",
            "is_toplevel": "hoge",
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"is_toplevel": [{"code": "AE-121000", "message": "Must be a valid boolean."}]},
        )

    def test_create_entity_with_invalid_param_attrs(self):
        params = {
            "name": "hoge",
            "attrs": "hoge",
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": [
                    {
                        "code": "AE-121000",
                        "message": 'Expected a list of items but got type "str".',
                    }
                ]
            },
        )

        params = {
            "name": "hoge",
            "attrs": ["hoge"],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
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
        )

        params = {
            "name": "hoge",
            "attrs": [{}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "name": [{"code": "AE-113000", "message": "This field is required."}],
                        "type": [{"code": "AE-113000", "message": "This field is required."}],
                    }
                }
            },
        )

        # name param
        params = {
            "name": "hoge",
            "attrs": [{"name": ["hoge"], "type": AttrType.STRING}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"name": [{"code": "AE-121000", "message": "Not a valid string."}]}}},
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "a" * (EntityAttr._meta.get_field("name").max_length + 1),
                    "type": AttrType.STRING,
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "name": [
                            {
                                "code": "AE-122000",
                                "message": "Ensure this field has no more than 200 characters.",
                            }
                        ]
                    }
                }
            },
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrType.STRING,
                },
                {
                    "name": "hoge",
                    "type": AttrType.STRING,
                },
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": [
                    {"code": "AE-220000", "message": "Duplicated attribute names are not allowed"}
                ]
            },
        )

        # type param
        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "hoge",
                    "type": "hoge",
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "type": [{"code": "AE-121000", "message": "A valid integer is required."}]
                    }
                }
            },
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "hoge",
                    "type": 9999,
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "type": [
                            {"code": "AE-230000", "message": "attrs type(9999) does not exist"}
                        ]
                    }
                }
            },
        )

        # index param
        params = {
            "name": "hoge",
            "attrs": [{"name": "hoge", "type": AttrType.OBJECT, "index": "hoge"}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "index": [{"code": "AE-121000", "message": "A valid integer is required."}]
                    }
                }
            },
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrType.OBJECT,
                    "index": 2**32,
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "index": [
                            {
                                "code": "AE-122000",
                                "message": "Ensure this value is less than or equal to 2147483647.",
                            }
                        ]
                    }
                }
            },
        )

        # is_mandatory, is_summarized, is_delete_in_chain param
        for param in ["is_mandatory", "is_summarized", "is_delete_in_chain"]:
            params = {
                "name": "hoge",
                "attrs": [
                    {
                        "name": "hoge",
                        "type": AttrType.OBJECT,
                        param: "hoge",
                    }
                ],
            }
            resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.json(),
                {
                    "attrs": {
                        "0": {param: [{"code": "AE-121000", "message": "Must be a valid boolean."}]}
                    }
                },
            )

        # referral param
        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrType.OBJECT,
                    "referral": "hoge",
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "referral": [
                            {
                                "code": "AE-121000",
                                "message": 'Expected a list of items but got type "str".',
                            }
                        ]
                    }
                }
            },
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrType.OBJECT,
                    "referral": ["hoge"],
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "referral": [
                            {
                                "code": "AE-121000",
                                "message": "Incorrect type. Expected pk value, received str.",
                            }
                        ]
                    }
                }
            },
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrType.OBJECT,
                    "referral": [9999],
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "referral": [
                            {
                                "code": "AE-230000",
                                "message": 'Invalid pk "9999" - object does not exist.',
                            }
                        ]
                    }
                }
            },
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": all_attr["name"],
                    "type": all_attr["type"],
                }
                for all_attr in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        attrs = {}
        for index, all_attr in enumerate(self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY):
            if all_attr["type"] & AttrType.OBJECT:
                attrs[str(index)] = {
                    "non_field_errors": [
                        {
                            "code": "AE-113000",
                            "message": "When specified object type, referral field is required",
                        }
                    ]
                }
        self.assertEqual(
            resp.json(),
            {"attrs": attrs},
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": all_attr["name"],
                    "type": all_attr["type"],
                    "referral": [],
                }
                for all_attr in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        attrs = {}
        for index, all_attr in enumerate(self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY):
            if all_attr["type"] & AttrType.OBJECT:
                attrs[str(index)] = {
                    "non_field_errors": [
                        {
                            "code": "AE-113000",
                            "message": "When specified object type, referral field is required",
                        }
                    ]
                }
        self.assertEqual(
            resp.json(),
            {"attrs": attrs},
        )

    def test_create_entity_with_invalid_param_webhooks(self):
        params = {
            "name": "hoge",
            "webhooks": "hoge",
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": {
                    "non_field_errors": [
                        {
                            "code": "AE-121000",
                            "message": 'Expected a list of items but got type "str".',
                        }
                    ]
                }
            },
        )

        params = {
            "name": "hoge",
            "webhooks": ["hoge"],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "non_field_errors": [
                            {
                                "code": "AE-121000",
                                "message": "Invalid data. Expected a dictionary, but got str.",
                            }
                        ]
                    }
                ]
            },
        )

        params = {
            "name": "hoge",
            "webhooks": [{}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "non_field_errors": [
                            {"code": "AE-113000", "message": "id or url field is required"}
                        ]
                    }
                ]
            },
        )

        # url param
        params = {
            "name": "hoge",
            "webhooks": [{"url": "hoge"}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {"non_field_errors": [{"code": "AE-121000", "message": "Enter a valid URL."}]}
                ]
            },
        )

        params = {
            "name": "hoge",
            "webhooks": [
                {"url": "http://airone.com/" + "a" * Webhook._meta.get_field("url").max_length}
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "url": [
                            {
                                "code": "AE-122000",
                                "message": "Ensure this field has no more than 200 characters.",
                            }
                        ]
                    }
                ]
            },
        )

        # label param
        params = {
            "name": "hoge",
            "webhooks": [{"url": "http://airone.com/", "label": ["hoge"]}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"webhooks": [{"label": [{"code": "AE-121000", "message": "Not a valid string."}]}]},
        )

        # is_enabled param
        params = {
            "name": "hoge",
            "webhooks": [{"url": "http://airone.com/", "is_enabled": "hoge"}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {"is_enabled": [{"code": "AE-121000", "message": "Must be a valid boolean."}]}
                ]
            },
        )

        # headers param
        params = {
            "name": "hoge",
            "webhooks": [{"url": "http://airone.com/", "headers": "hoge"}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "headers": [
                            {
                                "code": "AE-121000",
                                "message": 'Expected a list of items but got type "str".',
                            }
                        ]
                    }
                ]
            },
        )

        params = {
            "name": "hoge",
            "webhooks": [{"url": "http://airone.com/", "headers": ["hoge"]}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "headers": {
                            "0": {
                                "non_field_errors": [
                                    {
                                        "code": "AE-121000",
                                        "message": "Invalid data. Expected a dictionary, "
                                        + "but got str.",
                                    }
                                ]
                            }
                        }
                    }
                ]
            },
        )

        params = {
            "name": "hoge",
            "webhooks": [{"url": "http://airone.com/", "headers": [{}]}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "headers": {
                            "0": {
                                "header_key": [
                                    {
                                        "code": "AE-113000",
                                        "message": "This field is required.",
                                    }
                                ],
                                "header_value": [
                                    {
                                        "code": "AE-113000",
                                        "message": "This field is required.",
                                    }
                                ],
                            }
                        }
                    }
                ]
            },
        )

        params = {
            "name": "hoge",
            "webhooks": [
                {
                    "url": "http://airone.com/",
                    "headers": [{"header_key": ["hoge"], "header_value": ["hoge"]}],
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "headers": {
                            "0": {
                                "header_key": [
                                    {"code": "AE-121000", "message": "Not a valid string."}
                                ],
                                "header_value": [
                                    {"code": "AE-121000", "message": "Not a valid string."}
                                ],
                            }
                        }
                    }
                ]
            },
        )

    @mock.patch(
        "entity.tasks.create_entity_v2.delay", mock.Mock(side_effect=tasks.create_entity_v2)
    )
    def test_create_entity_with_attrs_referral(self):
        params = {
            "name": "entity1",
            "attrs": [
                {
                    "name": all_attr["name"],
                    "index": 1,
                    "type": all_attr["type"],
                    "referral": [self.ref_entity.id],
                }
                for all_attr in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
            ],
        }

        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        entity: Entity = Entity.objects.get(name=params["name"])
        for entity_attr in entity.attrs.all():
            if entity_attr.type & AttrType.OBJECT:
                self.assertEqual([x.id for x in entity_attr.referral.all()], [self.ref_entity.id])
            else:
                self.assertEqual([x.id for x in entity_attr.referral.all()], [])

    @mock.patch(
        "entity.tasks.create_entity_v2.delay", mock.Mock(side_effect=tasks.create_entity_v2)
    )
    @mock.patch("requests.post")
    def test_create_entity_with_webhook_is_verified(self, mock_post):
        def mock_post_side_effect(url, *args, **kwargs):
            if url == "http://example.net/":
                mock_response = mock.Mock()
                mock_response.status_code = 200
                return mock_response
            return requests.post(url, *args, **kwargs)

        mock_post.side_effect = mock_post_side_effect

        params = {
            "name": "entity1",
            "webhooks": [{"url": "http://example.net/"}, {"url": "http://hoge.hoge/"}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        entity: Entity = Entity.objects.get(name=params["name"])
        self.assertEqual([x.is_verified for x in entity.webhooks.all()], [True, False])

    @mock.patch(
        "entity.tasks.create_entity_v2.delay", mock.Mock(side_effect=tasks.create_entity_v2)
    )
    @mock.patch("airone.lib.custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("airone.lib.custom_view.call_custom")
    def test_create_entity_with_customview(self, mock_call_custom):
        params = {"name": "hoge"}

        def side_effect(handler_name, entity_name, user, *args):
            raise ValidationError("create error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(mock_call_custom.called)

        def side_effect(handler_name, entity_name, user, *args):
            # Check specified parameters are expected
            self.assertIsNone(entity_name)
            self.assertEqual(user, self.user)

            if handler_name == "before_create_entity_v2":
                self.assertDictEqual(
                    args[0],
                    {
                        "name": "hoge",
                        "is_toplevel": False,
                        "attrs": [],
                        "webhooks": [],
                        "created_user": self.user,
                    },
                )
                return args[0]

            if handler_name == "after_create_entity_v2":
                entity = Entity.objects.get(name="hoge", is_active=True)
                self.assertEqual(args[0], entity)

        mock_call_custom.side_effect = side_effect
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(mock_call_custom.called)

    def test_create_entity_with_webhook_is_disabled(self):
        params = {
            "name": "entity1",
            "note": "hoge",
            "is_toplevel": True,
            "attrs": [],
            "webhooks": [
                {
                    "url": "http://airone.com",
                    "label": "hoge",
                    "is_enabled": True,
                    "headers": [{"header_key": "Content-Type", "header_value": "application/json"}],
                }
            ],
        }
        try:
            settings.AIRONE_FLAGS = {"WEBHOOK": False}
            resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.json(), {"webhooks": [{"code": "AE-121000", "message": "webhook is disabled"}]}
            )
        finally:
            settings.AIRONE_FLAGS = {"WEBHOOK": True}

    @mock.patch("entity.tasks.edit_entity_v2.delay", mock.Mock(side_effect=tasks.edit_entity_v2))
    def test_update_entity(self):
        entity: Entity = self.create_entity(
            **{
                "user": self.user,
                "name": "entity1",
                "attrs": [
                    {
                        "name": "attr1",
                        "type": AttrType.OBJECT,
                    }
                ],
                "webhooks": [
                    {
                        "url": "http://airone.com/",
                    }
                ],
            }
        )
        entity_attr: EntityAttr = entity.attrs.first()
        webhook: Webhook = entity.webhooks.first()
        params = {
            "id": entity.id,
            "name": "change-entity1",
            "note": "change-hoge",
            "is_toplevel": True,
            "attrs": [
                {
                    "id": entity_attr.id,
                    "name": "change-attr1",
                    "index": 1,
                    "type": AttrType.OBJECT,
                    "referral": [self.ref_entity.id],
                    "is_mandatory": True,
                    "is_delete_in_chain": True,
                    "is_summarized": True,
                    "note": "change-attr1 note",
                }
            ],
            "webhooks": [
                {
                    "id": webhook.id,
                    "url": "http://change-airone.com",
                    "label": "change-hoge",
                    "is_enabled": False,
                    "headers": [{"header_key": "Content-Type", "header_value": "application/json"}],
                }
            ],
        }

        resp = self.client.put(
            "/entity/api/v2/%d/" % entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        entity.refresh_from_db()
        self.assertEqual(entity.name, "change-entity1")
        self.assertEqual(entity.note, "change-hoge")
        self.assertEqual(entity.status, Entity.STATUS_TOP_LEVEL)
        self.assertEqual(entity.created_user, self.user)

        self.assertEqual(entity.attrs.count(), 1)
        entity_attr.refresh_from_db()
        self.assertEqual(entity_attr.name, "change-attr1")
        self.assertEqual(entity_attr.index, 1)
        self.assertEqual(entity_attr.type, AttrType.OBJECT)
        self.assertEqual(entity_attr.referral.count(), 1)
        self.assertEqual(entity_attr.referral.first().id, self.ref_entity.id)
        self.assertEqual(entity_attr.is_mandatory, True)
        self.assertEqual(entity_attr.is_delete_in_chain, True)
        self.assertEqual(entity_attr.is_summarized, True)
        self.assertEqual(entity_attr.created_user, self.user)
        self.assertEqual(entity_attr.note, "change-attr1 note")

        self.assertEqual(entity.webhooks.count(), 1)
        webhook.refresh_from_db()
        self.assertEqual(webhook.url, "http://change-airone.com")
        self.assertEqual(webhook.label, "change-hoge")
        self.assertEqual(webhook.is_enabled, False)
        self.assertEqual(
            webhook.headers, [{"header_key": "Content-Type", "header_value": "application/json"}]
        )

        history: History = History.objects.get(target_obj=entity)
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.operation, History.MOD_ENTITY)
        self.assertEqual(history.details.count(), 1)
        self.assertEqual(history.details.first().target_obj, entity_attr.aclbase_ptr)

        # unset toplevel attribute
        params = {
            "id": entity.id,
            "is_toplevel": False,
        }
        self.client.put("/entity/api/v2/%d/" % entity.id, json.dumps(params), "application/json")
        entity.refresh_from_db()
        self.assertEqual(entity.status, 0)

    def test_update_entity_with_invalid_url(self):
        params = {}
        resp = self.client.put(
            "/entity/api/v2/%s/" % "hoge", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 404)

        params = {}
        resp = self.client.put("/entity/api/v2/%d/" % 9999, json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Entity matches the given query."}
        )

        self.entity.delete()
        params = {}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Entity matches the given query."}
        )

    def test_update_entity_with_invalid_param(self):
        # name param
        params = {"name": ["hoge"]}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), {"name": [{"code": "AE-121000", "message": "Not a valid string."}]}
        )

        params = {"name": "a" * (Entity._meta.get_field("name").max_length + 1)}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
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

        params = {"name": "test-entity"}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.ref_entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "name": [
                    {
                        "code": "AE-220000",
                        "message": "Duplication error. There is same named Entity",
                    }
                ]
            },
        )

        # note param
        params = {
            "name": "hoge",
            "note": ["hoge"],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), {"note": [{"code": "AE-121000", "message": "Not a valid string."}]}
        )

        params = {
            "name": "hoge",
            "note": "a" * (Entity._meta.get_field("note").max_length + 1),
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "note": [
                    {
                        "code": "AE-122000",
                        "message": "Ensure this field has no more than 200 characters.",
                    }
                ]
            },
        )

        # is_toplevel param
        params = {
            "name": "hoge",
            "is_toplevel": "hoge",
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"is_toplevel": [{"code": "AE-121000", "message": "Must be a valid boolean."}]},
        )

    @mock.patch("entity.tasks.edit_entity_v2.delay", mock.Mock(side_effect=tasks.edit_entity_v2))
    def test_update_entity_with_invalid_param_attrs(self):
        params = {
            "attrs": "hoge",
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": [
                    {
                        "code": "AE-121000",
                        "message": 'Expected a list of items but got type "str".',
                    }
                ]
            },
        )

        params = {
            "attrs": ["hoge"],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
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
        )

        params = {
            "attrs": [{}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "non_field_errors": [
                            {
                                "code": "AE-113000",
                                "message": "id or (name and type) field is required",
                            }
                        ]
                    }
                }
            },
        )

        # id param
        params = {
            "attrs": [{"id": "hoge"}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {"id": [{"code": "AE-121000", "message": "A valid integer is required."}]}
                }
            },
        )

        params = {
            "attrs": [{"id": 9999}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "id": [
                            {
                                "code": "AE-230000",
                                "message": "Invalid id(%s) object does not exist" % 9999,
                            }
                        ]
                    }
                }
            },
        )

        entity_attr: EntityAttr = self.entity.attrs.first()
        entity_attr.delete()
        params = {
            "attrs": [{"id": entity_attr.id}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "id": [
                            {
                                "code": "AE-230000",
                                "message": "Invalid id(%s) object does not exist" % entity_attr.id,
                            }
                        ]
                    }
                }
            },
        )
        entity_attr.restore()

        # name param
        params = {
            "attrs": [{"name": ["hoge"], "type": AttrType.STRING}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"name": [{"code": "AE-121000", "message": "Not a valid string."}]}}},
        )

        params = {
            "attrs": [
                {
                    "name": "a" * (EntityAttr._meta.get_field("name").max_length + 1),
                    "type": AttrType.STRING,
                }
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "name": [
                            {
                                "code": "AE-122000",
                                "message": "Ensure this field has no more than 200 characters.",
                            }
                        ]
                    }
                }
            },
        )

        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrType.STRING,
                },
                {
                    "name": "hoge",
                    "type": AttrType.STRING,
                },
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": [
                    {"code": "AE-220000", "message": "Duplicated attribute names are not allowed"}
                ]
            },
        )

        params = {
            "attrs": [
                {
                    "name": "val",
                    "type": AttrType.STRING,
                },
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": [
                    {"code": "AE-220000", "message": "Duplicated attribute names are not allowed"}
                ]
            },
        )

        # type param
        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": "hoge",
                }
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "type": [{"code": "AE-121000", "message": "A valid integer is required."}]
                    }
                }
            },
        )

        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": 9999,
                }
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "type": [
                            {"code": "AE-230000", "message": "attrs type(9999) does not exist"}
                        ]
                    }
                }
            },
        )

        params = {
            "attrs": [{"id": entity_attr.id, "type": AttrType.ARRAY_STRING}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "non_field_errors": [
                            {"code": "AE-121000", "message": "type cannot be changed"}
                        ]
                    }
                }
            },
        )

        # index param
        params = {
            "attrs": [{"name": "hoge", "type": AttrType.OBJECT, "index": "hoge"}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "index": [{"code": "AE-121000", "message": "A valid integer is required."}]
                    }
                }
            },
        )

        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrType.OBJECT,
                    "index": 2**32,
                }
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "index": [
                            {
                                "code": "AE-122000",
                                "message": "Ensure this value is less than or equal to 2147483647.",
                            }
                        ]
                    }
                }
            },
        )

        # is_mandatory, is_summarized, is_delete_in_chain param
        for param in ["is_mandatory", "is_summarized", "is_delete_in_chain"]:
            params = {
                "attrs": [
                    {
                        "name": "hoge",
                        "type": AttrType.OBJECT,
                        param: "hoge",
                    }
                ],
            }
            resp = self.client.put(
                "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
            )
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.json(),
                {
                    "attrs": {
                        "0": {param: [{"code": "AE-121000", "message": "Must be a valid boolean."}]}
                    }
                },
            )

        # referral param
        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrType.OBJECT,
                    "referral": "hoge",
                }
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "referral": [
                            {
                                "code": "AE-121000",
                                "message": 'Expected a list of items but got type "str".',
                            }
                        ]
                    }
                }
            },
        )

        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrType.OBJECT,
                    "referral": ["hoge"],
                }
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "referral": [
                            {
                                "code": "AE-121000",
                                "message": "Incorrect type. Expected pk value, received str.",
                            }
                        ]
                    }
                }
            },
        )

        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrType.OBJECT,
                    "referral": [9999],
                }
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "referral": [
                            {
                                "code": "AE-230000",
                                "message": 'Invalid pk "9999" - object does not exist.',
                            }
                        ]
                    }
                }
            },
        )

        params = {
            "attrs": [
                {
                    "name": all_attr["name"],
                    "type": all_attr["type"],
                }
                for all_attr in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        attrs = {}
        for index, all_attr in enumerate(self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY):
            if all_attr["type"] & AttrType.OBJECT:
                attrs[str(index)] = {
                    "non_field_errors": [
                        {
                            "code": "AE-113000",
                            "message": "When specified object type, referral field is required",
                        }
                    ]
                }
        self.assertEqual(
            resp.json(),
            {"attrs": attrs},
        )

        params = {
            "attrs": [
                {
                    "name": all_attr["name"],
                    "type": all_attr["type"],
                    "referral": [],
                }
                for all_attr in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        attrs = {}
        for index, all_attr in enumerate(self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY):
            if all_attr["type"] & AttrType.OBJECT:
                attrs[str(index)] = {
                    "non_field_errors": [
                        {
                            "code": "AE-113000",
                            "message": "When specified object type, referral field is required",
                        }
                    ]
                }
        self.assertEqual(
            resp.json(),
            {"attrs": attrs},
        )

        # When a new attribute parameter includes "is_deleted",
        # it's acceptable but this attribute won't be created.
        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrType.STRING,
                    "is_deleted": True,
                }
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(
            all(["hoge" not in x.name for x in self.entity.attrs.filter(is_active=True)])
        )

        entity_attr.refresh_from_db()
        params = {
            "attrs": [
                {
                    "id": entity_attr.id,
                    "is_deleted": "hoge",
                }
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "attrs": {
                    "0": {
                        "is_deleted": [{"code": "AE-121000", "message": "Must be a valid boolean."}]
                    }
                }
            },
        )

        entity_attr.refresh_from_db()
        params = {
            "attrs": [
                {
                    "id": entity_attr.id,
                    "is_deleted": True,
                },
                {
                    "name": entity_attr.name,
                    "type": AttrType.STRING,
                },
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

    def test_update_entity_with_invalid_param_webhooks(self):
        params = {
            "webhooks": "hoge",
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": {
                    "non_field_errors": [
                        {
                            "code": "AE-121000",
                            "message": 'Expected a list of items but got type "str".',
                        }
                    ]
                }
            },
        )

        params = {
            "webhooks": ["hoge"],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "non_field_errors": [
                            {
                                "code": "AE-121000",
                                "message": "Invalid data. Expected a dictionary, but got str.",
                            }
                        ]
                    }
                ]
            },
        )

        params = {
            "webhooks": [{}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "non_field_errors": [
                            {"code": "AE-113000", "message": "id or url field is required"}
                        ]
                    }
                ]
            },
        )

        # id param
        params = {
            "webhooks": [{"id": "hoge"}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {"id": [{"code": "AE-121000", "message": "A valid integer is required."}]}
                ]
            },
        )

        params = {
            "webhooks": [{"id": 9999}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "id": [
                            {
                                "code": "AE-230000",
                                "message": "Invalid id(%s) object does not exist" % 9999,
                            }
                        ]
                    }
                ]
            },
        )

        # url param
        params = {
            "webhooks": [{"url": "hoge"}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {"non_field_errors": [{"code": "AE-121000", "message": "Enter a valid URL."}]}
                ]
            },
        )

        params = {
            "webhooks": [
                {"url": "http://airone.com/" + "a" * Webhook._meta.get_field("url").max_length}
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "url": [
                            {
                                "code": "AE-122000",
                                "message": "Ensure this field has no more than 200 characters.",
                            }
                        ]
                    }
                ]
            },
        )

        # label param
        params = {
            "webhooks": [{"url": "http://airone.com/", "label": ["hoge"]}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"webhooks": [{"label": [{"code": "AE-121000", "message": "Not a valid string."}]}]},
        )

        # is_enabled param
        params = {
            "webhooks": [{"url": "http://airone.com/", "is_enabled": "hoge"}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {"is_enabled": [{"code": "AE-121000", "message": "Must be a valid boolean."}]}
                ]
            },
        )

        # headers param
        params = {
            "webhooks": [{"url": "http://airone.com/", "headers": "hoge"}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "headers": [
                            {
                                "code": "AE-121000",
                                "message": 'Expected a list of items but got type "str".',
                            }
                        ]
                    }
                ]
            },
        )

        params = {
            "webhooks": [{"url": "http://airone.com/", "headers": ["hoge"]}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "headers": {
                            "0": {
                                "non_field_errors": [
                                    {
                                        "code": "AE-121000",
                                        "message": "Invalid data. Expected a dictionary, "
                                        + "but got str.",
                                    }
                                ]
                            }
                        }
                    }
                ]
            },
        )

        params = {
            "webhooks": [{"url": "http://airone.com/", "headers": [{}]}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "headers": {
                            "0": {
                                "header_key": [
                                    {
                                        "code": "AE-113000",
                                        "message": "This field is required.",
                                    }
                                ],
                                "header_value": [
                                    {
                                        "code": "AE-113000",
                                        "message": "This field is required.",
                                    }
                                ],
                            }
                        }
                    }
                ]
            },
        )

        params = {
            "webhooks": [
                {
                    "url": "http://airone.com/",
                    "headers": [{"header_key": ["hoge"], "header_value": ["hoge"]}],
                }
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "webhooks": [
                    {
                        "headers": {
                            "0": {
                                "header_key": [
                                    {"code": "AE-121000", "message": "Not a valid string."}
                                ],
                                "header_value": [
                                    {"code": "AE-121000", "message": "Not a valid string."}
                                ],
                            }
                        }
                    }
                ]
            },
        )

    @mock.patch("entity.tasks.edit_entity_v2.delay", mock.Mock(side_effect=tasks.edit_entity_v2))
    def test_update_entity_with_attrs_referral(self):
        self.entity.attrs.all().delete()
        params = {
            "attrs": [
                {
                    "name": all_attr["name"],
                    "index": 1,
                    "type": all_attr["type"],
                    "referral": [self.ref_entity.id],
                }
                for all_attr in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
            ],
        }

        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        for entity_attr in self.entity.attrs.all():
            if entity_attr.type & AttrType.OBJECT:
                self.assertEqual([x.id for x in entity_attr.referral.all()], [self.ref_entity.id])
            else:
                self.assertEqual([x.id for x in entity_attr.referral.all()], [])

    @mock.patch("entity.tasks.edit_entity_v2.delay", mock.Mock(side_effect=tasks.edit_entity_v2))
    @mock.patch("requests.post")
    def test_update_entity_with_webhook_is_verified(self, mock_post):
        def mock_post_side_effect(url, *args, **kwargs):
            if url == "http://example.net/":
                mock_response = mock.Mock()
                mock_response.status_code = 200
                return mock_response
            return requests.post(url, *args, **kwargs)

        mock_post.side_effect = mock_post_side_effect

        self.entity.webhooks.all().delete()
        params = {
            "name": "entity1",
            "webhooks": [{"url": "http://example.net/"}, {"url": "http://hoge.hoge/"}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        self.assertEqual([x.is_verified for x in self.entity.webhooks.all()], [True, False])

    @mock.patch("entity.tasks.edit_entity_v2.delay", mock.Mock(side_effect=tasks.edit_entity_v2))
    @mock.patch("airone.lib.custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("airone.lib.custom_view.call_custom")
    def test_update_entity_with_customview(self, mock_call_custom):
        params = {"name": "hoge"}

        def side_effect(handler_name, entity_name, user, *args):
            raise ValidationError("update error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(mock_call_custom.called)

        def side_effect(handler_name, entity_name, user, *args):
            # Check specified parameters are expected
            self.assertIsNone(entity_name)
            self.assertEqual(user, self.user)

            if handler_name == "before_update_entity_v2":
                self.assertEqual(
                    args[0],
                    {
                        "name": "hoge",
                        "attrs": [],
                        "webhooks": [],
                    },
                )
                self.assertEqual(args[1], self.entity)
                return args[0]

            if handler_name == "after_update_entity_v2":
                self.assertEqual(args[0], self.entity)

        mock_call_custom.side_effect = side_effect
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(mock_call_custom.called)

    @mock.patch("entity.tasks.edit_entity_v2.delay", mock.Mock(side_effect=tasks.edit_entity_v2))
    def test_update_entry_with_specified_only_param(self):
        self.entity.note = "hoge"
        self.entity.status = Entity.STATUS_TOP_LEVEL
        self.entity.save()

        attr_count = self.entity.attrs.filter(is_active=True).count()
        webhook_count = self.entity.webhooks.count()

        params = {
            "name": "change-entity",
            "attr": [],
            "webhooks": [],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        self.entity.refresh_from_db()
        changed_attr_count = self.entity.attrs.filter(is_active=True).count()
        changed_webhook_count = self.entity.webhooks.count()
        self.assertEqual(self.entity.name, "change-entity")
        self.assertEqual(self.entity.note, "hoge")
        self.assertEqual(self.entity.status, Entity.STATUS_TOP_LEVEL)
        self.assertEqual(attr_count, changed_attr_count)
        self.assertEqual(webhook_count, changed_webhook_count)

    @mock.patch("entity.tasks.edit_entity_v2.delay", mock.Mock(side_effect=tasks.edit_entity_v2))
    def test_update_entity_without_permission(self):
        self.role.users.add(self.user)

        # permission nothing Entity
        self.entity.is_public = False
        self.entity.save()
        paramas = {}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(paramas), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readble Entity
        self.entity.readable.roles.add(self.role)
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(paramas), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission writable Entity
        self.entity.writable.roles.add(self.role)
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(paramas), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # permission nothing EntityAttr update
        self.entity.is_public = True
        self.entity.save()
        entity_attr: EntityAttr = self.entity.attrs.first()
        entity_attr.is_public = False
        entity_attr.save()
        params = {"attrs": [{"id": entity_attr.id}]}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {"code": "AE-210000", "message": "Does not have permission to update"},
        )

        # permission readble EntityAttr update
        entity_attr.readable.roles.add(self.role)
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {"code": "AE-210000", "message": "Does not have permission to update"},
        )

        # permission writable EntityAttr update
        entity_attr.writable.roles.add(self.role)
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # permission writable EntityAttr delete
        params = {"attrs": [{"id": entity_attr.id, "is_deleted": True}]}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {"code": "AE-210000", "message": "Does not have permission to delete"},
        )

        # permission full EntityAttr delete
        entity_attr.full.roles.add(self.role)
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

    @mock.patch("entity.tasks.edit_entity_v2.delay", mock.Mock(side_effect=tasks.edit_entity_v2))
    def test_update_entity_with_other_created_user(self):
        self.admin_login()

        params = {
            "id": self.entity.id,
            "name": "change-entity",
            "note": "change-hoge",
        }

        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        self.entity.refresh_from_db()
        self.assertEqual(self.entity.name, "change-entity")
        self.assertEqual(self.entity.note, "change-hoge")

    def test_update_entity_with_webhook_is_disabled(self):
        entity: Entity = self.create_entity(
            **{
                "user": self.user,
                "name": "entity1",
                "attrs": [],
                "webhooks": [],
            }
        )
        params = {
            "name": "entity1",
            "note": "hoge",
            "is_toplevel": True,
            "attrs": [],
            "webhooks": [
                {
                    "url": "http://airone.com",
                    "label": "hoge",
                    "is_enabled": True,
                    "headers": [{"header_key": "Content-Type", "header_value": "application/json"}],
                }
            ],
        }
        try:
            settings.AIRONE_FLAGS = {"WEBHOOK": False}
            resp = self.client.put(
                "/entity/api/v2/%d/" % entity.id, json.dumps(params), "application/json"
            )
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.json(), {"webhooks": [{"code": "AE-121000", "message": "webhook is disabled"}]}
            )
        finally:
            settings.AIRONE_FLAGS = {"WEBHOOK": True}

    @mock.patch(
        "entity.tasks.delete_entity_v2.delay", mock.Mock(side_effect=tasks.delete_entity_v2)
    )
    def test_delete_entity(self):
        resp = self.client.delete("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        self.entity.refresh_from_db()
        self.assertFalse(self.entity.is_active)
        self.assertFalse(self.entity.attrs.filter(is_active=True).exists())
        history: History = History.objects.get(target_obj=self.entity)
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.operation, History.DEL_ENTITY)
        self.assertEqual(history.details.count(), self.entity.attrs.count())
        self.assertEqual(history.details.first().target_obj, self.entity.attrs.first().aclbase_ptr)

    @mock.patch(
        "entity.tasks.delete_entity_v2.delay", mock.Mock(side_effect=tasks.delete_entity_v2)
    )
    @mock.patch("airone.lib.custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("airone.lib.custom_view.call_custom")
    def test_delete_entity_with_customview(self, mock_call_custom):
        def side_effect(handler_name, entity_name, user, entity):
            raise ValidationError("delete error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.delete("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(mock_call_custom.called)

        def side_effect(handler_name, entity_name, user, entity):
            # Check specified parameters are expected
            self.assertTrue(handler_name in ["before_delete_entity_v2", "after_delete_entity_v2"])
            self.assertIsNone(entity_name)
            self.assertEqual(user, self.user)
            self.assertEqual(entity, self.entity)

        mock_call_custom.side_effect = side_effect
        resp = self.client.delete("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(mock_call_custom.called)

    def test_delete_entity_with_invalid_param(self):
        resp = self.client.delete("/entity/api/v2/%s/" % "hoge", None, "application/json")
        self.assertEqual(resp.status_code, 404)

        resp = self.client.delete("/entity/api/v2/%d/" % 9999, None, "application/json")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Entity matches the given query."}
        )

        self.entity.delete()
        resp = self.client.delete("/entity/api/v2/%d/" % self.entity.id, None, "application/json")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Entity matches the given query."}
        )

    def test_delete_entity_with_exist_entry(self):
        self.add_entry(self.user, "entry", self.entity)
        resp = self.client.delete("/entity/api/v2/%s/" % self.entity.id, None, "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            [
                {
                    "code": "AE-121000",
                    "message": "cannot delete Entity because one or more Entries are not deleted",
                }
            ],
        )

    def test_list_entry(self):
        entries = []
        for index in range(2):
            entries.append(self.add_entry(self.user, "e-%d" % index, self.entity))

        resp = self.client.get("/entity/api/v2/%d/entries/" % self.entity.id)
        self.assertEqual(resp.status_code, 200)

        resp_results = resp.json()["results"]
        self.assertEqual([x["name"] for x in resp_results], ["e-0", "e-1"])
        self.assertTrue(all([x["is_active"] for x in resp_results]))
        self.assertTrue(all([x["deleted_time"] is None for x in resp_results]))
        self.assertTrue(all([x["deleted_user"] is None for x in resp_results]))
        self.assertTrue(
            all(
                [
                    x["schema"]
                    == {
                        "id": self.entity.id,
                        "name": "test-entity",
                        "is_public": self.entity.is_public,
                    }
                    for x in resp_results
                ]
            )
        )
        for info in resp_results:
            entry = [e for e in entries if e.id == info["id"]][0]
            self.assertEqual(
                info["updated_time"], entry.updated_time.astimezone(self.TZ_INFO).isoformat()
            )

        # check result with ordering parameter
        resp = self.client.get("/entity/api/v2/%d/entries/?ordering=-updated_time" % self.entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([x["name"] for x in resp.json()["results"]], ["e-1", "e-0"])

    def test_list_entry_with_param_is_active(self):
        entries = []
        for index in range(2):
            entries.append(self.add_entry(self.user, "e-%d" % index, self.entity))

        entries[0].delete()

        resp = self.client.get("/entity/api/v2/%d/entries/?is_active=true" % self.entity.id)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()["results"][0]["name"], "e-1")

        resp = self.client.get("/entity/api/v2/%d/entries/?is_active=false" % self.entity.id)
        self.assertEqual(resp.json()["count"], 1)
        self.assertRegex(resp.json()["results"][0]["name"], "e-0")

    def test_list_entry_with_param_serach(self):
        for index in range(2):
            self.add_entry(self.user, "e-%d" % index, self.entity)

        resp = self.client.get("/entity/api/v2/%d/entries/?search=-0" % self.entity.id)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()["results"][0]["name"], "e-0")

    def test_list_entry_with_ordering(self):
        self.add_entry(self.user, "e-2", self.entity)
        self.add_entry(self.user, "e-3", self.entity)
        self.add_entry(self.user, "e-1", self.entity)

        resp = self.client.get("/entity/api/v2/%d/entries/?" % self.entity.id)
        self.assertEqual([x["name"] for x in resp.json()["results"]], ["e-2", "e-3", "e-1"])

        resp = self.client.get("/entity/api/v2/%d/entries/?ordering=name" % self.entity.id)
        self.assertEqual([x["name"] for x in resp.json()["results"]], ["e-1", "e-2", "e-3"])

        resp = self.client.get("/entity/api/v2/%d/entries/?ordering=-name" % self.entity.id)
        self.assertEqual([x["name"] for x in resp.json()["results"]], ["e-3", "e-2", "e-1"])

    def test_list_entry_without_permission(self):
        self.entity.is_public = False
        self.entity.save()

        resp = self.client.get("/entity/api/v2/%d/entries/" % self.entity.id)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        self.entity.readable.roles.add(self.role)
        self.role.users.add(self.user)

        resp = self.client.get("/entity/api/v2/%d/entries/" % self.entity.id)
        self.assertEqual(resp.status_code, 200)

    def test_list_entry_with_invalid_param(self):
        resp = self.client.get("/entity/api/v2/%s/entries/" % "hoge")
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get("/entity/api/v2/%s/entries/" % 9999)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json(), {"code": "AE-230000", "message": "Not found."})

    def test_list_entry_when_alias_is_related(self):
        # create items and set alias at one of them
        ALIAS_NAME = "test alias"
        items = [self.add_entry(self.user, "e-%i" % i, self.entity) for i in range(3)]
        items[0].add_alias(ALIAS_NAME)

        # search item by alias name
        resp = self.client.get(
            "/entity/api/v2/%d/entries/?search=%s&with_alias=1" % (self.entity.id, ALIAS_NAME)
        )
        self.assertEqual(resp.status_code, 200)

        # then only item that alias is set was returned
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()["results"][0]["name"], "e-0")
        self.assertEqual(resp.json()["results"][0]["aliases"][0]["name"], ALIAS_NAME)

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=create_entry_v2))
    def test_create_entry(self):
        attr = {}
        for attr_name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)

        params = {
            "name": "entry1",
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
                {"id": attr["num"].id, "value": 123.45},
                {"id": attr["nums"].id, "value": [123.45, 678.90]},
                {"id": attr["datetime"].id, "value": "2018-12-31T00:00Z"},
            ],
        }
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        entry: Entry = Entry.objects.get(name=params["name"], is_active=True)
        self.assertEqual(entry.schema, self.entity)
        self.assertEqual(entry.created_user, self.user)
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
                "num": 123.45,
                "nums": [123.45, 678.90],
                "ref": "r-0",
                "refs": ["r-0"],
                "text": "hoge\nfuga",
                "val": "hoge",
                "vals": ["hoge", "fuga"],
                "role": "role0",
                "roles": ["role0"],
                "datetime": datetime.datetime(2018, 12, 31, 0, 0, tzinfo=timezone.utc),
            },
        )
        search_result = self._es.search(body={"query": {"term": {"name": entry.name}}})
        self.assertEqual(search_result["hits"]["total"]["value"], 1)

    def test_create_entry_when_duplicated_alias_exists(self):
        # make an Item and Alias to prevent to creating another Item
        entry: Entry = self.add_entry(self.user, "Everest", self.entity)
        entry.add_alias("Chomolungma")

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({"name": "Chomolungma"}),
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

    def test_create_entry_without_permission_entity(self):
        params = {
            "name": "entry1",
        }

        # permission nothing
        self.entity.is_public = False
        self.entity.save()
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readable
        self.entity.readable.roles.add(self.role)
        self.role.users.add(self.user)
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission writable
        self.entity.writable.roles.add(self.role)
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=create_entry_v2))
    def test_create_entry_without_permission_entity_attr(self):
        attr = {}
        for attr_name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)

        params = {
            "attrs": [
                {"id": attr["val"].id, "value": "hoge"},
                {"id": attr["vals"].id, "value": ["hoge"]},
            ]
        }

        attr["vals"].is_public = False
        attr["vals"].save()
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({**params, "name": "entry1"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        entry: Entry = Entry.objects.get(name="entry1", is_active=True)
        self.assertEqual(entry.attrs.get(schema=attr["val"]).get_latest_value().get_value(), "hoge")
        self.assertEqual(entry.attrs.get(schema=attr["vals"]).get_latest_value().get_value(), [])

        attr["vals"].is_mandatory = True
        attr["vals"].save()
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({**params, "name": "entry2"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "mandatory attrs id(%s) is permission denied" % attr["vals"].id,
            },
        )

    def test_create_entry_with_invalid_param_entity_id(self):
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % "hoge",
            json.dumps({"name": "entry1"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 404)

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % 9999, json.dumps({"name": "entry1"}), "application/json"
        )
        self.assertEqual(
            resp.json(),
            {
                "schema": [
                    {
                        "code": "AE-230000",
                        "message": 'Invalid pk "9999" - object does not exist.',
                    }
                ]
            },
        )

    def test_create_entry_with_invalid_param_name(self):
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
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

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({"name": "a" * (Entry._meta.get_field("name").max_length)}),
            "application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        entry = self.add_entry(self.user, "hoge", self.entity)
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({"name": "hoge"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"name": [{"code": "AE-220000", "message": "specified name(hoge) already exists"}]},
        )

        entry.delete()
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({"name": "hoge"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

    def test_create_entry_with_invalid_param_attrs(self):
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
            params = {"name": "entry1", "attrs": test_value["input"]}
            resp = self.client.post(
                "/entity/api/v2/%s/entries/" % self.entity.id,
                json.dumps(params),
                "application/json",
            )
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.json(), test_value["error_msg"])

        params = {"name": "entry1", "attrs": []}

        attr["val"].is_mandatory = True
        attr["val"].save()

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {
                "non_field_errors": [
                    {
                        "code": "AE-113000",
                        "message": "mandatory attrs id(%s) is not specified" % attr["val"].id,
                    }
                ]
            },
        )

        attr["val"].is_public = False
        attr["val"].save()

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "mandatory attrs id(%s) is permission denied" % attr["val"].id,
            },
        )

        attr["val"].delete()
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=create_entry_v2))
    @mock.patch("entry.tasks.notify_create_entry.delay")
    def test_create_entry_notify(self, mock_task):
        self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({"name": "hoge"}),
            "application/json",
        )

        self.assertTrue(mock_task.called)

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=create_entry_v2))
    @mock.patch("airone.lib.custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("airone.lib.custom_view.call_custom")
    def test_create_entry_with_customview(self, mock_call_custom):
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
            raise ValidationError("create error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(mock_call_custom.called)

        def side_effect(handler_name, entity_name, user, *args):
            # Check specified parameters are expected
            self.assertEqual(entity_name, self.entity.name)
            self.assertEqual(user, self.user)

            if handler_name == "validate_entry":
                self.assertEqual(args[0], self.entity.name)
                self.assertEqual(args[1], params["name"])
                self.assertEqual(args[2], params["attrs"])
                self.assertIsNone(args[3])

            if handler_name == "before_create_entry_v2":
                self.assertEqual(
                    args[0], {**params, "schema": self.entity, "created_user": self.user}
                )
                return args[0]

            if handler_name == "after_create_entry":
                entry = Entry.objects.get(name="hoge", is_active=True)
                self.assertEqual(args[0], entry)

        mock_call_custom.side_effect = side_effect
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(mock_call_custom.called)

    @mock.patch("entity.tasks.create_entity.delay", mock.Mock(side_effect=tasks.create_entity))
    def test_history(self):
        params = {
            "name": "hoge",
            "note": "fuga",
            "is_toplevel": True,
            "attrs": [
                {
                    "name": "foo",
                    "type": str(AttrType.STRING),
                    "is_delete_in_chain": False,
                    "is_mandatory": True,
                    "row_index": "1",
                },
                {
                    "name": "bar",
                    "type": str(AttrType.TEXT),
                    "is_delete_in_chain": False,
                    "is_mandatory": True,
                    "row_index": "2",
                },
                {
                    "name": "baz",
                    "type": str(AttrType.ARRAY_STRING),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "3",
                },
                {
                    "name": "attr_bool",
                    "type": str(AttrType.BOOLEAN),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "4",
                },
                {
                    "name": "attr_group",
                    "type": str(AttrType.GROUP),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "5",
                },
                {
                    "name": "attr_date",
                    "type": str(AttrType.DATE),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "6",
                },
                {
                    "name": "attr_datetime",
                    "type": str(AttrType.DATETIME),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "7",
                },
            ],
        }
        resp = self.client.post(reverse("entity:do_create"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        entity = Entity.objects.filter(name="hoge", is_active=True).first()

        resp = self.client.get("/entity/api/v2/history/%s" % entity.id)
        self.assertEqual(resp.status_code, 200)

        histories = resp.json()
        self.assertEqual(len(histories), 1)
        self.assertEqual(len(histories[0]["details"]), 7)

    def test_import(self):
        self.admin_login()

        self.ref_entity.delete()
        self.entity.attrs.all().delete()
        self.entity.delete()

        user = User.objects.get(username="admin")
        ACLBase.objects.create(id=1000, name="entity1", created_user=user)

        fp = self.open_fixture_file("entity.yaml")
        resp = self.client.post("/entity/api/v2/import", fp.read(), content_type="application/yaml")
        self.assertEqual(resp.status_code, 200)
        fp.close()

        # checks each objects are created safety
        self.assertEqual(Entity.objects.filter(is_active=True).count(), 3)
        self.assertEqual(EntityAttr.objects.filter(is_active=True).count(), 4)

        # checks keeping the correspondence relationship with id and name
        self.assertEqual(Entity.objects.get(id="1001").name, "entity1")
        self.assertEqual(EntityAttr.objects.get(id="1005").name, "attr-obj")

        # checks contains required attributes (for Entity)
        entity = Entity.objects.get(name="entity")
        self.assertEqual(entity.note, "note1")
        self.assertTrue(entity.status & Entity.STATUS_TOP_LEVEL)

        entity1 = Entity.objects.get(name="entity1")
        self.assertEqual(entity1.note, "")
        self.assertFalse(entity1.status & Entity.STATUS_TOP_LEVEL)

        # checks contains required attributes (for EntityAttr)
        self.assertEqual(entity.attrs.count(), 4)
        self.assertEqual(entity.attrs.get(name="attr-str").type, AttrType.STRING)
        self.assertEqual(entity.attrs.get(name="attr-obj").type, AttrType.OBJECT)
        self.assertEqual(entity.attrs.get(name="attr-arr-str").type, AttrType.ARRAY_STRING)
        self.assertEqual(entity.attrs.get(name="attr-arr-obj").type, AttrType.ARRAY_OBJECT)
        self.assertFalse(entity.attrs.get(name="attr-str").is_mandatory)
        self.assertTrue(entity.attrs.get(name="attr-obj").is_mandatory)
        self.assertEqual(entity.attrs.get(name="attr-obj").referral.count(), 1)
        self.assertEqual(entity.attrs.get(name="attr-arr-obj").referral.count(), 2)

    def test_import_with_unnecessary_param(self):
        self.admin_login()

        self.ref_entity.delete()
        self.entity.attrs.all().delete()
        self.entity.delete()

        fp = self.open_fixture_file("entity_with_unnecessary_param.yaml")
        resp = self.client.post("/entity/api/v2/import", fp.read(), content_type="application/yaml")
        self.assertEqual(resp.status_code, 200)
        fp.close()

        # unnecessary params are simply ignored
        self.assertEqual(Entity.objects.filter(is_active=True).count(), 3)
        self.assertEqual(EntityAttr.objects.filter(is_active=True).count(), 4)

    def test_import_without_mandatory_param(self):
        self.admin_login()

        self.ref_entity.delete()
        self.entity.attrs.all().delete()
        self.entity.delete()

        fp = self.open_fixture_file("entity_without_mandatory_param.yaml")
        with self.assertLogs(logger=Logger, level=logging.WARNING) as warning_log:
            resp = self.client.post(
                "/entity/api/v2/import", fp.read(), content_type="application/yaml"
            )
            self.assertEqual(resp.status_code, 200)

            # checks that warning messagees were outputted
            self.assertEqual(len(warning_log.output), 3)
            self.assertRegex(warning_log.output[0], "Entity.*Mandatory key doesn't exist$")
            self.assertRegex(
                warning_log.output[1],
                "The parameter 'type' is mandatory when a new EntityAtter create$",
            )
            self.assertRegex(warning_log.output[2], "refer to invalid entity object$")
        fp.close()

        # checks not to create EntityAttr that refers invalid object
        self.assertEqual(Entity.objects.filter(is_active=True).count(), 2)
        self.assertEqual(EntityAttr.objects.filter(is_active=True).count(), 2)
        self.assertEqual(EntityAttr.objects.filter(name="attr-arr-obj").count(), 0)

    def test_import_with_spoofing_user(self):
        self.admin_login()

        self.ref_entity.delete()
        self.entity.attrs.all().delete()
        self.entity.delete()

        # A user who creates original mock object
        user = User.objects.create(username="test-user")
        Entity.objects.create(id=1003, name="baz-original", created_user=user)

        fp = self.open_fixture_file("entity.yaml")
        with self.assertLogs(logger=Logger, level=logging.WARNING) as warning_log:
            resp = self.client.post(
                "/entity/api/v2/import", fp.read(), content_type="application/yaml"
            )
            self.assertEqual(resp.status_code, 200)

            # checks to show warning messages
            self.assertEqual(len(warning_log.output), 4)
            for warn_msg in warning_log.output:
                self.assertRegex(warn_msg, "failed to identify entity object$")
        fp.close()

        # checks that import data doens't appied
        entity = Entity.objects.get(id=1003)
        self.assertEqual(entity.name, "baz-original")

        # checks that the EntityAttr objects which refers invalid Entity won't create
        self.assertEqual(entity.attrs.count(), 0)
        self.assertEqual(EntityAttr.objects.filter(name="attr-str").count(), 0)

    def test_export(self):
        self.admin_login()

        resp = self.client.get("/entity/api/v2/export")
        self.assertEqual(resp.status_code, 200)

        obj = yaml.load(resp.content, Loader=yaml.SafeLoader)
        self.assertTrue(isinstance(obj, dict))
        self.assertEqual(sorted(obj.keys()), ["Entity", "EntityAttr"])
        self.assertEqual(len(obj["EntityAttr"]), self.entity.attrs.count())
        self.assertEqual(len(obj["Entity"]), 2)

    def test_get_entity_attr_names(self):
        user = self.admin_login()

        self.ref_entity.delete()
        self.entity.attrs.all().delete()
        self.entity.delete()

        entity_info = {
            "test_entity1": ["foo", "bar", "fuga"],
            "test_entity2": ["bar", "hoge", "fuga"],
        }
        for i, (entity_name, attrnames) in enumerate(entity_info.items()):
            entity = Entity.objects.create(name=entity_name, created_user=user)

            for j, attrname in enumerate(attrnames):
                is_object = attrname == "bar"
                attrtype = AttrType.OBJECT if is_object else AttrType.STRING

                attr = EntityAttr.objects.create(
                    name=attrname,
                    type=attrtype.value,
                    created_user=user,
                    parent_entity=entity,
                )
                if is_object:
                    attr.referral.add(entity)

        entities = Entity.objects.filter(name__contains="test_entity")

        entity3 = self.create_entity(
            user,
            "test_entity3",
            [
                {
                    "name": "puyo",
                    "type": AttrType.OBJECT,
                    "ref": entities.first(),
                }
            ],
        )

        # get partially
        resp = self.client.get(
            "/entity/api/v2/attrs?entity_ids=%s" % ",".join([str(x.id) for x in entities[:2]])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), ["bar", "foo", "fuga", "hoge"])

        resp = self.client.get(
            "/entity/api/v2/attrs?entity_ids=%s&referral_attr=%s" % (entity3.id, "puyo")
        )
        self.assertEqual(resp.status_code, 200)
        # order in the list is non-deterministic and it's not necessary
        self.assertEqual(sorted(resp.json()), sorted(["foo", "bar", "fuga"]))

        # get all attribute infomations are returned collectly
        resp = self.client.get("/entity/api/v2/attrs")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), ["bar", "foo", "fuga", "hoge", "puyo"])

        # invalid entity_id(s)
        resp = self.client.get("/entity/api/v2/attrs?entity_ids=9999")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "Target Entity doesn't exist"}
        )

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=create_entry_v2))
    @mock.patch(
        "trigger.tasks.may_invoke_trigger.delay",
        mock.Mock(side_effect=trigger_tasks.may_invoke_trigger),
    )
    def test_create_entry_when_trigger_is_set(self):
        attr = {}
        for attr_name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)

        # register Trigger and Action that specify "fuga" at text attribute
        # when value "hoge" is set to the Attribute "val".
        TriggerCondition.register(
            self.entity,
            [{"attr_id": attr["val"].id, "cond": "hoge"}],
            [{"attr_id": attr["vals"].id, "values": ["fuga", "piyo"]}],
        )
        TriggerCondition.register(
            self.entity,
            [{"attr_id": attr["vals"].id, "cond": "fuga"}],
            [{"attr_id": attr["text"].id, "value": "hogefuga"}],
        )

        # send request to create an Entry that have "hoge" at the Attribute "val".
        params = {
            "name": "entry1",
            "attrs": [{"id": attr["val"].id, "value": "hoge"}],
        }
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # check Attribute "vals", which is specified by TriggerCondition, was changed as expected
        entry: Entry = Entry.objects.get(name=params["name"], is_active=True)
        self.assertEqual(entry.get_attrv("text").value, "hogefuga")
        self.assertEqual(
            [x.value for x in entry.get_attrv("vals").data_array.all()], ["fuga", "piyo"]
        )

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=create_entry_v2))
    def test_create_entry_when_pattern_is_set(self):
        # helper method to create item
        def _send_request(item_name, expected_status):
            return self._send_request_item_creation(
                model, {"name": item_name, "attrs": []}, expected_status
            )

        model: Entity = self.create_entity(
            **{
                "user": self.user,
                "name": "VM",
                "attrs": self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY,
                "item_name_pattern": "^vm[0-9]+$|^template-.*",
            }
        )

        # send request to create an Entry that complies with item_name_pattern
        for item_name in ["vm1234", "template-vm-hoge"]:
            _send_request(item_name, status.HTTP_202_ACCEPTED)

        # send request to create an Entry that doesn't comply with item_name_pattern
        for item_name in ["Incompatible Item", "vm1234-hoge"]:
            resp = _send_request(item_name, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                resp.json()["name"][0]["message"],
                'Specified name doesn\'t match configured pattern "%s"' % model.item_name_pattern,
            )

    @mock.patch(
        "entity.tasks.create_entity_v2.delay", mock.Mock(side_effect=tasks.create_entity_v2)
    )
    def test_create_entity_with_attr_default_values(self):
        """Test creating an entity with attributes that have default values"""
        params = {
            "name": "entity_with_defaults",
            "note": "test entity with default values",
            "attrs": [
                {
                    "name": "string_attr",
                    "type": AttrType.STRING,
                    "default_value": "default string value",
                    "index": 1,
                },
                {
                    "name": "text_attr",
                    "type": AttrType.TEXT,
                    "default_value": "default\nmultiline\ntext",
                    "index": 2,
                },
                {
                    "name": "bool_attr",
                    "type": AttrType.BOOLEAN,
                    "default_value": True,
                    "index": 3,
                },
                {
                    "name": "bool_false_attr",
                    "type": AttrType.BOOLEAN,
                    "default_value": False,
                    "index": 4,
                },
            ],
        }

        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Verify entity was created
        try:
            entity = Entity.objects.get(name="entity_with_defaults")
            self.assertEqual(entity.note, "test entity with default values")
        except Entity.DoesNotExist:
            # Check what entities exist
            entities = Entity.objects.filter(name__contains="entity_with_defaults")
            entity_names = list(entities.values_list("name", flat=True))
            self.fail(
                f"Entity 'entity_with_defaults' was not created. Existing entities: {entity_names}"
            )

        # Verify attributes have correct default values
        string_attr = entity.attrs.get(name="string_attr")
        self.assertEqual(string_attr.default_value, "default string value")

        text_attr = entity.attrs.get(name="text_attr")
        self.assertEqual(text_attr.default_value, "default\nmultiline\ntext")

        bool_attr = entity.attrs.get(name="bool_attr")
        self.assertEqual(bool_attr.default_value, True)

        bool_false_attr = entity.attrs.get(name="bool_false_attr")
        self.assertEqual(bool_false_attr.default_value, False)

    def test_create_entity_with_invalid_default_values(self):
        """Test creating entity with invalid default values should fail"""
        params = {
            "name": "entity_with_invalid_defaults",
            "attrs": [
                {
                    "name": "string_attr",
                    "type": AttrType.STRING,
                    "default_value": 123,  # Invalid: number for string type
                    "index": 1,
                }
            ],
        }

        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Default value must be a string", str(resp.json()))

    @mock.patch(
        "entity.tasks.create_entity_v2.delay", mock.Mock(side_effect=tasks.create_entity_v2)
    )
    def test_create_entity_with_unsupported_type_default_value(self):
        """Test that unsupported types clear default_value"""
        params = {
            "name": "entity_with_unsupported_default",
            "attrs": [
                {
                    "name": "object_attr",
                    "type": AttrType.OBJECT,
                    "default_value": "some value",  # Should be cleared
                    "referral": [self.ref_entity.id],
                    "index": 1,
                }
            ],
        }

        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Verify entity was created and default_value was cleared
        entity = Entity.objects.get(name="entity_with_unsupported_default")
        object_attr = entity.attrs.get(name="object_attr")
        self.assertIsNone(object_attr.default_value)

    @mock.patch("entity.tasks.edit_entity_v2.delay", mock.Mock(side_effect=tasks.edit_entity_v2))
    def test_update_entity_attr_default_values(self):
        """Test updating entity attributes with default values"""
        # First create an entity with some attributes
        entity = Entity.objects.create(name="update_test_entity", created_user=self.user)
        string_attr = EntityAttr.objects.create(
            name="string_attr",
            type=AttrType.STRING,
            created_user=self.user,
            parent_entity=entity,
            default_value="original value",
        )
        bool_attr = EntityAttr.objects.create(
            name="bool_attr",
            type=AttrType.BOOLEAN,
            created_user=self.user,
            parent_entity=entity,
            default_value=False,
        )

        # Update the entity with new default values
        params = {
            "id": entity.id,
            "name": "update_test_entity",
            "attrs": [
                {
                    "id": string_attr.id,
                    "name": "string_attr",
                    "type": AttrType.STRING,
                    "default_value": "updated string value",
                    "index": 1,
                },
                {
                    "id": bool_attr.id,
                    "name": "bool_attr",
                    "type": AttrType.BOOLEAN,
                    "default_value": True,  # Use boolean value
                    "index": 2,
                },
            ],
        }

        resp = self.client.put(
            f"/entity/api/v2/{entity.id}/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Verify default values were updated
        string_attr.refresh_from_db()
        bool_attr.refresh_from_db()

        self.assertEqual(string_attr.default_value, "updated string value")
        self.assertEqual(bool_attr.default_value, True)

    def test_retrieve_entity_includes_default_values(self):
        """Test that entity retrieval includes default_value in response"""
        # Create entity with attributes that have default values
        entity = Entity.objects.create(name="retrieve_test_entity", created_user=self.user)
        EntityAttr.objects.create(
            name="string_attr",
            type=AttrType.STRING,
            created_user=self.user,
            parent_entity=entity,
            default_value="test default",
        )
        EntityAttr.objects.create(
            name="bool_attr",
            type=AttrType.BOOLEAN,
            created_user=self.user,
            parent_entity=entity,
            default_value=True,
        )
        EntityAttr.objects.create(
            name="no_default_attr", type=AttrType.TEXT, created_user=self.user, parent_entity=entity
        )

        resp = self.client.get(f"/entity/api/v2/{entity.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Find the attributes in the response
        attrs = resp.json()["attrs"]
        string_attr_data = next(attr for attr in attrs if attr["name"] == "string_attr")
        bool_attr_data = next(attr for attr in attrs if attr["name"] == "bool_attr")
        no_default_attr_data = next(attr for attr in attrs if attr["name"] == "no_default_attr")

        # Verify default values are included in response
        self.assertEqual(string_attr_data["default_value"], "test default")
        self.assertEqual(bool_attr_data["default_value"], True)
        self.assertIsNone(no_default_attr_data["default_value"])

    @mock.patch(
        "entity.tasks.create_entity_v2.delay", mock.Mock(side_effect=tasks.create_entity_v2)
    )
    def test_boolean_edge_cases_api(self):
        """Test that string and numeric values are rejected for boolean type through API"""
        # All these should be rejected now
        invalid_cases = [
            "false",
            "FALSE",
            "0",
            0,
            "1",
            1,
        ]

        for i, input_value in enumerate(invalid_cases):
            params = {
                "name": f"bool_test_entity_{i}",
                "attrs": [
                    {
                        "name": "bool_attr",
                        "type": AttrType.BOOLEAN,
                        "default_value": input_value,
                        "index": 1,
                    }
                ],
            }

            resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
            self.assertEqual(
                resp.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"Should have rejected: {input_value}",
            )

        # Test with valid boolean values
        for i, bool_value in enumerate([True, False]):
            params = {
                "name": f"valid_bool_test_{i}",
                "attrs": [
                    {
                        "name": "bool_attr",
                        "type": AttrType.BOOLEAN,
                        "default_value": bool_value,
                        "index": 1,
                    }
                ],
            }

            resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
            self.assertEqual(
                resp.status_code, status.HTTP_202_ACCEPTED, f"Should accept boolean: {bool_value}"
            )

    def test_boolean_invalid_values_api(self):
        """Test that invalid boolean values are rejected through API"""
        invalid_values = ["yes", "no", "invalid", 2, -1, 1.5]

        for i, invalid_value in enumerate(invalid_values):
            params = {
                "name": f"invalid_bool_test_{i}",
                "attrs": [
                    {
                        "name": "bool_attr",
                        "type": AttrType.BOOLEAN,
                        "default_value": invalid_value,
                        "index": 1,
                    }
                ],
            }

            resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
            self.assertEqual(
                resp.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"Should have failed for invalid value: {invalid_value}",
            )
            # Check that the error message indicates boolean type issue
            error_msg = str(resp.json())
            self.assertTrue(
                "Default value must be a boolean for BOOLEAN type" in error_msg
                or "boolean" in error_msg.lower(),
                f"Error message doesn't indicate boolean type issue: {error_msg}",
            )
