import datetime
import json
from unittest import mock

from django.urls import reverse

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeArrStr, AttrTypeStr, AttrTypeText, AttrTypeValue
from entity import tasks
from entity.models import Entity, EntityAttr
from entry.models import Entry
from group.models import Group
from role.models import Role
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

        self.entity: Entity = self.create_entity(
            **{
                "user": self.user,
                "name": "test-entity",
                "attrs": self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY,
                "webhooks": [{"url": "http://airone.com/"}],
            }
        )

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
                "name": "test-entity",
                "note": "",
                "status": 0,
                "attrs": [],
                "webhooks": [],
                "is_public": True,
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
        self.assertEqual(
            resp.json()["attrs"],
            [
                {
                    "id": self.entity.attrs.get(name="val").id,
                    "index": 0,
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "name": "val",
                    "referral": [],
                    "type": AttrTypeValue["string"],
                },
                {
                    "id": self.entity.attrs.get(name="vals").id,
                    "index": 1,
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "name": "vals",
                    "referral": [],
                    "type": AttrTypeValue["array_string"],
                },
                {
                    "id": self.entity.attrs.get(name="ref").id,
                    "index": 2,
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "name": "ref",
                    "referral": [],
                    "type": AttrTypeValue["object"],
                },
                {
                    "id": self.entity.attrs.get(name="refs").id,
                    "index": 3,
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "name": "refs",
                    "referral": [],
                    "type": AttrTypeValue["array_object"],
                },
                {
                    "id": self.entity.attrs.get(name="name").id,
                    "index": 4,
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "name": "name",
                    "referral": [],
                    "type": AttrTypeValue["named_object"],
                },
                {
                    "id": self.entity.attrs.get(name="names").id,
                    "index": 5,
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "name": "names",
                    "referral": [],
                    "type": AttrTypeValue["array_named_object"],
                },
                {
                    "id": self.entity.attrs.get(name="group").id,
                    "index": 6,
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "name": "group",
                    "referral": [],
                    "type": AttrTypeValue["group"],
                },
                {
                    "id": self.entity.attrs.get(name="groups").id,
                    "index": 7,
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "name": "groups",
                    "referral": [],
                    "type": AttrTypeValue["array_group"],
                },
                {
                    "id": self.entity.attrs.get(name="bool").id,
                    "index": 8,
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "name": "bool",
                    "referral": [],
                    "type": AttrTypeValue["boolean"],
                },
                {
                    "id": self.entity.attrs.get(name="text").id,
                    "index": 9,
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "name": "text",
                    "referral": [],
                    "type": AttrTypeValue["text"],
                },
                {
                    "id": self.entity.attrs.get(name="date").id,
                    "index": 10,
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "name": "date",
                    "referral": [],
                    "type": AttrTypeValue["date"],
                },
            ],
        )

        entity_attr: EntityAttr = self.entity.attrs.get(name="refs")
        entity_attr.index = 11
        entity_attr.is_delete_in_chain = True
        entity_attr.is_mandatory = True
        entity_attr.referral.add(self.ref_entity)
        entity_attr.save()

        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(
            resp.json()["attrs"][-1],
            {
                "id": entity_attr.id,
                "index": 11,
                "is_delete_in_chain": True,
                "is_mandatory": True,
                "name": "refs",
                "referral": [
                    {
                        "id": self.ref_entity.id,
                        "name": "ref_entity",
                    }
                ],
                "type": AttrTypeValue["array_object"],
            },
        )

    def test_retrieve_entity_with_webhook(self):
        webhook: Webhook = self.entity.webhooks.first()

        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(
            resp.json()["webhooks"],
            [
                {
                    "id": webhook.id,
                    "url": "http://airone.com/",
                    "is_enabled": True,
                    "is_verified": True,
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
        self.assertEqual(resp.json(), {"detail": "Not found."})

        resp = self.client.get("/entity/api/v2/%s/" % "hoge")
        self.assertEqual(resp.status_code, 404)

        self.entity.delete()
        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json(), {"detail": "Not found."})

    def test_retrieve_entity_without_permission(self):
        # permission nothing entity
        self.entity.is_public = False
        self.entity.save()
        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(), {"detail": "You do not have permission to perform this action."}
        )

        # permission readble entity
        self.role.users.add(self.user)
        self.role.permissions.add(self.entity.readable)
        resp = self.client.get("/entity/api/v2/%d/" % self.entity.id)
        self.assertEqual(resp.status_code, 200)

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
                        "name": "ref_entity",
                        "note": "",
                        "status": 0,
                    },
                    {
                        "id": self.entity.id,
                        "is_toplevel": False,
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

    def test_create_entity(self):
        params = {
            "name": "entity1",
            "note": "hoge",
            "is_toplevel": True,
            "attrs": [
                {
                    "name": "attr1",
                    "index": 1,
                    "type": AttrTypeValue["object"],
                    "referral": [self.ref_entity.id],
                    "is_mandatory": True,
                    "is_delete_in_chain": True,
                    "is_summarized": True,
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
        self.assertEqual(resp.status_code, 201)

        entity: Entity = Entity.objects.get(id=resp.json()["id"])
        self.assertEqual(
            resp.json(),
            {
                "id": entity.id,
                "name": "entity1",
            },
        )
        self.assertEqual(entity.name, "entity1")
        self.assertEqual(entity.note, "hoge")
        self.assertEqual(entity.status, Entity.STATUS_TOP_LEVEL)
        self.assertEqual(entity.created_user, self.user)

        self.assertEqual(entity.attrs.count(), 1)
        entity_attr: EntityAttr = entity.attrs.first()
        self.assertEqual(entity_attr.name, "attr1")
        self.assertEqual(entity_attr.index, 1)
        self.assertEqual(entity_attr.type, AttrTypeValue["object"])
        self.assertEqual(entity_attr.referral.count(), 1)
        self.assertEqual(entity_attr.referral.first().id, self.ref_entity.id)
        self.assertEqual(entity_attr.is_mandatory, True)
        self.assertEqual(entity_attr.is_delete_in_chain, True)
        self.assertEqual(entity_attr.is_summarized, True)
        self.assertEqual(entity_attr.created_user, self.user)

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
        self.assertEqual(resp.json(), {"name": ["This field is required."]})

        # name param
        params = {"name": ["hoge"]}
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"name": ["Not a valid string."]})

        params = {"name": "a" * (Entity._meta.get_field("name").max_length + 1)}
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), {"name": ["Ensure this field has no more than 200 characters."]}
        )

        params = {"name": "test-entity"}
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"name": ["Duplication error. There is same named Entity"]})

        # note param
        params = {
            "name": "hoge",
            "note": ["hoge"],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"note": ["Not a valid string."]})

        params = {
            "name": "hoge",
            "note": "a" * (Entity._meta.get_field("note").max_length + 1),
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), {"note": ["Ensure this field has no more than 200 characters."]}
        )

        # is_toplevel param
        params = {
            "name": "hoge",
            "is_toplevel": "hoge",
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"is_toplevel": ["Must be a valid boolean."]})

    def test_create_entity_with_invalid_param_attrs(self):
        params = {
            "name": "hoge",
            "attrs": "hoge",
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"attrs": ['Expected a list of items but got type "str".']})

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
                    "0": {"non_field_errors": ["Invalid data. Expected a dictionary, but got str."]}
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
                    "0": {"name": ["This field is required."], "type": ["This field is required."]}
                }
            },
        )

        # name param
        params = {
            "name": "hoge",
            "attrs": [{"name": ["hoge"], "type": AttrTypeValue["string"]}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"name": ["Not a valid string."]}}},
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "a" * (EntityAttr._meta.get_field("name").max_length + 1),
                    "type": AttrTypeValue["string"],
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"name": ["Ensure this field has no more than 200 characters."]}}},
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrTypeValue["string"],
                },
                {
                    "name": "hoge",
                    "type": AttrTypeValue["string"],
                },
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": ["Duplicated attribute names are not allowed"]},
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
            {"attrs": {"0": {"type": ["A valid integer is required."]}}},
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
            {"attrs": {"0": {"type": ["attrs type(9999) does not exist"]}}},
        )

        # index param
        params = {
            "name": "hoge",
            "attrs": [{"name": "hoge", "type": AttrTypeValue["object"], "index": "hoge"}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"index": ["A valid integer is required."]}}},
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrTypeValue["object"],
                    "index": 2**32,
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"index": ["Ensure this value is less than or equal to 2147483647."]}}},
        )

        # is_mandatory, is_summarized, is_delete_in_chain param
        for param in ["is_mandatory", "is_summarized", "is_delete_in_chain"]:
            params = {
                "name": "hoge",
                "attrs": [
                    {
                        "name": "hoge",
                        "type": AttrTypeValue["object"],
                        param: "hoge",
                    }
                ],
            }
            resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.json(),
                {"attrs": {"0": {param: ["Must be a valid boolean."]}}},
            )

        # referral param
        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrTypeValue["object"],
                    "referral": "hoge",
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"referral": ['Expected a list of items but got type "str".']}}},
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrTypeValue["object"],
                    "referral": ["hoge"],
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"referral": ["Incorrect type. Expected pk value, received str."]}}},
        )

        params = {
            "name": "hoge",
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrTypeValue["object"],
                    "referral": [9999],
                }
            ],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"referral": ['Invalid pk "9999" - object does not exist.']}}},
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
            if all_attr["type"] & AttrTypeValue["object"]:
                attrs[str(index)] = {
                    "non_field_errors": ["When specified object type, referral field is required"]
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
            if all_attr["type"] & AttrTypeValue["object"]:
                attrs[str(index)] = {
                    "non_field_errors": ["When specified object type, referral field is required"]
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
            {"webhooks": {"non_field_errors": ['Expected a list of items but got type "str".']}},
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
                    {"non_field_errors": ["Invalid data. Expected a dictionary, but got str."]}
                ]
            },
        )

        params = {
            "name": "hoge",
            "webhooks": [{}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"webhooks": [{"non_field_errors": ["Enter a valid URL."]}]})

        # url param
        params = {
            "name": "hoge",
            "webhooks": [{"url": "hoge"}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"webhooks": [{"non_field_errors": ["Enter a valid URL."]}]})

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
            {"webhooks": [{"url": ["Ensure this field has no more than 200 characters."]}]},
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
            {"webhooks": [{"label": ["Not a valid string."]}]},
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
            {"webhooks": [{"is_enabled": ["Must be a valid boolean."]}]},
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
            {"webhooks": [{"headers": ['Expected a list of items but got type "str".']}]},
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
                                    "Invalid data. Expected a dictionary, but got str."
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
                                "header_key": ["This field is required."],
                                "header_value": ["This field is required."],
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
                                "header_key": ["Not a valid string."],
                                "header_value": ["Not a valid string."],
                            }
                        }
                    }
                ]
            },
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

        entity: Entity = Entity.objects.get(id=resp.json()["id"])
        for entity_attr in entity.attrs.all():
            if entity_attr.type & AttrTypeValue["object"]:
                self.assertEqual([x.id for x in entity_attr.referral.all()], [self.ref_entity.id])
            else:
                self.assertEqual([x.id for x in entity_attr.referral.all()], [])

    def test_create_entity_with_webhook_is_verified(self):
        params = {
            "name": "entity1",
            "webhooks": [{"url": "http://example.net/"}, {"url": "http://hoge.hoge/"}],
        }
        resp = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        entity: Entity = Entity.objects.get(id=resp.json()["id"])
        self.assertEqual([x.is_verified for x in entity.webhooks.all()], [True, False])

    @mock.patch("custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("custom_view.call_custom")
    def test_create_entity_with_customview(self, mock_call_custom):
        def side_effect(handler_name, entity_name, validated_data):
            # Check specified parameters are expected
            self.assertEqual(handler_name, "before_create_entity")
            self.assertIsNone(entity_name)
            self.assertEqual(
                validated_data,
                {
                    "name": "hoge",
                    "is_toplevel": False,
                    "attrs": [],
                    "webhooks": [],
                    "created_user": self.user,
                },
            )

        mock_call_custom.side_effect = side_effect

        params = {
            "name": "hoge",
        }
        self.client.post("/entity/api/v2/", json.dumps(params), "application/json")

        self.assertTrue(mock_call_custom.called)

    def test_update_entity(self):
        entity: Entity = self.create_entity(
            **{
                "user": self.user,
                "name": "entity1",
                "attrs": [
                    {
                        "name": "attr1",
                        "type": AttrTypeValue["object"],
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
                    "type": AttrTypeValue["object"],
                    "referral": [self.ref_entity.id],
                    "is_mandatory": True,
                    "is_delete_in_chain": True,
                    "is_summarized": True,
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
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            resp.json(),
            {
                "id": entity.id,
                "name": "change-entity1",
            },
        )
        entity.refresh_from_db()
        self.assertEqual(entity.name, "change-entity1")
        self.assertEqual(entity.note, "change-hoge")
        self.assertEqual(entity.status, Entity.STATUS_TOP_LEVEL)
        self.assertEqual(entity.created_user, self.user)

        self.assertEqual(entity.attrs.count(), 1)
        entity_attr.refresh_from_db()
        self.assertEqual(entity_attr.name, "change-attr1")
        self.assertEqual(entity_attr.index, 1)
        self.assertEqual(entity_attr.type, AttrTypeValue["object"])
        self.assertEqual(entity_attr.referral.count(), 1)
        self.assertEqual(entity_attr.referral.first().id, self.ref_entity.id)
        self.assertEqual(entity_attr.is_mandatory, True)
        self.assertEqual(entity_attr.is_delete_in_chain, True)
        self.assertEqual(entity_attr.is_summarized, True)
        self.assertEqual(entity_attr.created_user, self.user)

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

    def test_update_entity_with_invalid_url(self):
        params = {}
        resp = self.client.put(
            "/entity/api/v2/%s/" % "hoge", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 404)

        params = {}
        resp = self.client.put("/entity/api/v2/%d/" % 9999, json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json(), {"detail": "Not found."})

        self.entity.delete()
        params = {}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json(), {"detail": "Not found."})

    def test_update_entity_with_invalid_param(self):
        # name param
        params = {"name": ["hoge"]}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"name": ["Not a valid string."]})

        params = {"name": "a" * (Entity._meta.get_field("name").max_length + 1)}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), {"name": ["Ensure this field has no more than 200 characters."]}
        )

        params = {"name": "test-entity"}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.ref_entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"name": ["Duplication error. There is same named Entity"]})

        # note param
        params = {
            "name": "hoge",
            "note": ["hoge"],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"note": ["Not a valid string."]})

        params = {
            "name": "hoge",
            "note": "a" * (Entity._meta.get_field("note").max_length + 1),
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), {"note": ["Ensure this field has no more than 200 characters."]}
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
        self.assertEqual(resp.json(), {"is_toplevel": ["Must be a valid boolean."]})

    def test_update_entity_with_invalid_param_attrs(self):
        params = {
            "attrs": "hoge",
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"attrs": ['Expected a list of items but got type "str".']})

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
                    "0": {"non_field_errors": ["Invalid data. Expected a dictionary, but got str."]}
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
            {"attrs": {"0": {"non_field_errors": ["id or (name and type) field is required"]}}},
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
            {"attrs": {"0": {"id": ["A valid integer is required."]}}},
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
            {"attrs": {"0": {"id": ["Invalid id(%s) object does not exist" % 9999]}}},
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
            {"attrs": {"0": {"id": ["Invalid id(%s) object does not exist" % entity_attr.id]}}},
        )
        entity_attr.restore()

        # name param
        params = {
            "attrs": [{"name": ["hoge"], "type": AttrTypeValue["string"]}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"name": ["Not a valid string."]}}},
        )

        params = {
            "attrs": [
                {
                    "name": "a" * (EntityAttr._meta.get_field("name").max_length + 1),
                    "type": AttrTypeValue["string"],
                }
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"name": ["Ensure this field has no more than 200 characters."]}}},
        )

        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrTypeValue["string"],
                },
                {
                    "name": "hoge",
                    "type": AttrTypeValue["string"],
                },
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": ["Duplicated attribute names are not allowed"]},
        )

        params = {
            "attrs": [
                {
                    "name": "val",
                    "type": AttrTypeValue["string"],
                },
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": ["Duplicated attribute names are not allowed"]},
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
            {"attrs": {"0": {"type": ["A valid integer is required."]}}},
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
            {"attrs": {"0": {"type": ["attrs type(9999) does not exist"]}}},
        )

        params = {
            "attrs": [{"id": entity_attr.id, "type": AttrTypeValue["array_string"]}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"non_field_errors": ["type cannot be changed"]}}},
        )

        # index param
        params = {
            "attrs": [{"name": "hoge", "type": AttrTypeValue["object"], "index": "hoge"}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"attrs": {"0": {"index": ["A valid integer is required."]}}},
        )

        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrTypeValue["object"],
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
            {"attrs": {"0": {"index": ["Ensure this value is less than or equal to 2147483647."]}}},
        )

        # is_mandatory, is_summarized, is_delete_in_chain param
        for param in ["is_mandatory", "is_summarized", "is_delete_in_chain"]:
            params = {
                "attrs": [
                    {
                        "name": "hoge",
                        "type": AttrTypeValue["object"],
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
                {"attrs": {"0": {param: ["Must be a valid boolean."]}}},
            )

        # referral param
        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrTypeValue["object"],
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
            {"attrs": {"0": {"referral": ['Expected a list of items but got type "str".']}}},
        )

        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrTypeValue["object"],
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
            {"attrs": {"0": {"referral": ["Incorrect type. Expected pk value, received str."]}}},
        )

        params = {
            "attrs": [
                {
                    "name": "hoge",
                    "type": AttrTypeValue["object"],
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
            {"attrs": {"0": {"referral": ['Invalid pk "9999" - object does not exist.']}}},
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
            if all_attr["type"] & AttrTypeValue["object"]:
                attrs[str(index)] = {
                    "non_field_errors": ["When specified object type, referral field is required"]
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
            if all_attr["type"] & AttrTypeValue["object"]:
                attrs[str(index)] = {
                    "non_field_errors": ["When specified object type, referral field is required"]
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
                    "type": AttrTypeValue["string"],
                    "is_deleted": True,
                }
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
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
            {"attrs": {"0": {"is_deleted": ["Must be a valid boolean."]}}},
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
                    "type": AttrTypeValue["string"],
                },
            ],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

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
            {"webhooks": {"non_field_errors": ['Expected a list of items but got type "str".']}},
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
                    {"non_field_errors": ["Invalid data. Expected a dictionary, but got str."]}
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
            {"webhooks": [{"non_field_errors": ["id or url field is required"]}]},
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
            {"webhooks": [{"id": ["A valid integer is required."]}]},
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
            {"webhooks": [{"id": ["Invalid id(%s) object does not exist" % 9999]}]},
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
            {"webhooks": [{"non_field_errors": ["Enter a valid URL."]}]},
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
            {"webhooks": [{"url": ["Ensure this field has no more than 200 characters."]}]},
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
            {"webhooks": [{"label": ["Not a valid string."]}]},
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
            {"webhooks": [{"is_enabled": ["Must be a valid boolean."]}]},
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
            {"webhooks": [{"headers": ['Expected a list of items but got type "str".']}]},
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
                                    "Invalid data. Expected a dictionary, but got str."
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
                                "header_key": ["This field is required."],
                                "header_value": ["This field is required."],
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
                                "header_key": ["Not a valid string."],
                                "header_value": ["Not a valid string."],
                            }
                        }
                    }
                ]
            },
        )

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
        self.assertEqual(resp.status_code, 200)

        for entity_attr in self.entity.attrs.all():
            if entity_attr.type & AttrTypeValue["object"]:
                self.assertEqual([x.id for x in entity_attr.referral.all()], [self.ref_entity.id])
            else:
                self.assertEqual([x.id for x in entity_attr.referral.all()], [])

    def test_update_entity_with_webhook_is_verified(self):
        self.entity.webhooks.all().delete()
        params = {
            "name": "entity1",
            "webhooks": [{"url": "http://example.net/"}, {"url": "http://hoge.hoge/"}],
        }
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        self.assertEqual([x.is_verified for x in self.entity.webhooks.all()], [True, False])

    @mock.patch("custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("custom_view.call_custom")
    def test_update_entity_with_customview(self, mock_call_custom):
        def side_effect(handler_name, entity_name, validated_data, entity):
            # Check specified parameters are expected
            self.assertEqual(handler_name, "before_update_entity")
            self.assertIsNone(entity_name)
            self.assertEqual(
                validated_data,
                {
                    "name": "hoge",
                    "attrs": [],
                    "webhooks": [],
                },
            )
            self.assertEqual(entity, self.entity)

        mock_call_custom.side_effect = side_effect

        params = {"name": "hoge"}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(mock_call_custom.called)

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
        self.assertEqual(resp.status_code, 200)

        self.entity.refresh_from_db()
        changed_attr_count = self.entity.attrs.filter(is_active=True).count()
        changed_webhook_count = self.entity.webhooks.count()
        self.assertEqual(self.entity.name, "change-entity")
        self.assertEqual(self.entity.note, "hoge")
        self.assertEqual(self.entity.status, Entity.STATUS_TOP_LEVEL)
        self.assertEqual(attr_count, changed_attr_count)
        self.assertEqual(webhook_count, changed_webhook_count)

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
            resp.json(), {"detail": "You do not have permission to perform this action."}
        )

        # permission readble Entity
        self.role.permissions.add(self.entity.readable)
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(paramas), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(), {"detail": "You do not have permission to perform this action."}
        )

        # permission writable Entity
        self.role.permissions.add(self.entity.writable)
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(paramas), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

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
        self.assertEqual(resp.json(), {"detail": "Does not have permission to update"})

        # permission readble EntityAttr update
        self.role.permissions.add(entity_attr.readable)
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json(), {"detail": "Does not have permission to update"})

        # permission writable EntityAttr update
        self.role.permissions.add(entity_attr.writable)
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        # permission writable EntityAttr delete
        params = {"attrs": [{"id": entity_attr.id, "is_deleted": True}]}
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json(), {"detail": "Does not have permission to delete"})

        # permission full EntityAttr delete
        self.role.permissions.add(entity_attr.full)
        resp = self.client.put(
            "/entity/api/v2/%d/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

    def test_delete_entity(self):
        resp = self.client.delete("/entity/api/v2/%d/" % self.entity.id, None, "application/json")
        self.assertEqual(resp.status_code, 204)

        self.entity.refresh_from_db()
        self.assertFalse(self.entity.is_active)
        self.assertFalse(self.entity.attrs.filter(is_active=True).exists())
        history: History = History.objects.get(target_obj=self.entity)
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.operation, History.DEL_ENTITY)
        self.assertEqual(history.details.count(), self.entity.attrs.count())
        self.assertEqual(history.details.first().target_obj, self.entity.attrs.first().aclbase_ptr)

    def test_delete_entity_with_invalid_param(self):
        resp = self.client.delete("/entity/api/v2/%s/" % "hoge", None, "application/json")
        self.assertEqual(resp.status_code, 404)

        resp = self.client.delete("/entity/api/v2/%d/" % 9999, None, "application/json")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json(), {"detail": "Not found."})

        self.entity.delete()
        resp = self.client.delete("/entity/api/v2/%d/" % self.entity.id, None, "application/json")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json(), {"detail": "Not found."})

    def test_delete_entity_with_exist_entry(self):
        self.add_entry(self.user, "entry", self.entity)
        resp = self.client.delete("/entity/api/v2/%s/" % self.entity.id, None, "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            ["cannot delete Entity because one or more Entries are not deleted"],
        )

    def test_list_entry(self):
        entries = []
        for index in range(2):
            entries.append(self.add_entry(self.user, "e-%d" % index, self.entity))

        resp = self.client.get("/entity/api/v2/%d/entries/" % self.entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json()["results"],
            [
                {
                    "id": entries[0].id,
                    "name": "e-0",
                    "schema": {"id": self.entity.id, "name": "test-entity"},
                    "is_active": True,
                    "deleted_time": None,
                    "deleted_user": None,
                },
                {
                    "id": entries[1].id,
                    "name": "e-1",
                    "schema": {"id": self.entity.id, "name": "test-entity"},
                    "is_active": True,
                    "deleted_time": None,
                    "deleted_user": None,
                },
            ],
        )

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
            resp.json(), {"detail": "You do not have permission to perform this action."}
        )

        self.role.permissions.add(self.entity.readable)
        self.role.users.add(self.user)

        resp = self.client.get("/entity/api/v2/%d/entries/" % self.entity.id)
        self.assertEqual(resp.status_code, 200)

    def test_list_entry_with_invalid_param(self):
        resp = self.client.get("/entity/api/v2/%s/entries/" % "hoge")
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get("/entity/api/v2/%s/entries/" % 9999)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json(), {"detail": "Not found."})

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
            ],
        }
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 201)

        entry: Entry = Entry.objects.get(id=resp.json()["id"], is_active=True)
        self.assertEqual(
            resp.json(),
            {
                "id": entry.id,
                "name": "entry1",
            },
        )
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
                "ref": "r-0",
                "refs": ["r-0"],
                "text": "hoge\nfuga",
                "val": "hoge",
                "vals": ["hoge", "fuga"],
            },
        )
        search_result = self._es.search(body={"query": {"term": {"name": entry.name}}})
        self.assertEqual(search_result["hits"]["total"], 1)

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
            resp.json(), {"detail": "You do not have permission to perform this action."}
        )

        # permission readable
        self.role.permissions.add(self.entity.readable)
        self.role.users.add(self.user)
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(), {"detail": "You do not have permission to perform this action."}
        )

        # permission writable
        self.role.permissions.add(self.entity.writable)
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 201)

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
        self.assertEqual(resp.status_code, 201)

        entry: Entry = Entry.objects.get(id=resp.json()["id"], is_active=True)
        self.assertEqual(entry.attrs.get(schema=attr["val"]).get_latest_value().get_value(), "hoge")
        self.assertEqual(entry.attrs.get(schema=attr["vals"]).get_latest_value().get_value(), [])

        attr["vals"].is_mandatory = True
        attr["vals"].save()
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({**params, "name": "entry2"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"non_field_errors": ["mandatory attrs id(%s) is permission denied" % attr["vals"].id]},
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
        self.assertEqual(resp.json(), {"schema": ['Invalid pk "9999" - object does not exist.']})

    def test_create_entry_with_invalid_param_name(self):
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({"name": "a" * (Entry._meta.get_field("name").max_length + 1)}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), {"name": ["Ensure this field has no more than 200 characters."]}
        )

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({"name": "a" * (Entry._meta.get_field("name").max_length)}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 201)

        entry = self.add_entry(self.user, "hoge", self.entity)
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({"name": "hoge"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"non_field_errors": ["specified name(hoge) already exists"]})

        entry.delete()
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({"name": "hoge"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 201)

    def test_create_entry_with_invalid_param_attrs(self):
        attr = {}
        for attr_name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)

        test_values = [
            {
                "input": "hoge",
                "error_msg": {"attrs": ['Expected a list of items but got type "str".']},
            },
            {
                "input": ["hoge"],
                "error_msg": {
                    "attrs": {
                        "0": {
                            "non_field_errors": [
                                "Invalid data. Expected a dictionary, but got str."
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
                            "id": ["This field is required."],
                            "value": ["This field is required."],
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
                "error_msg": {"attrs": {"0": {"id": ["A valid integer is required."]}}},
            },
            {
                "input": [
                    {
                        "id": 9999,
                        "value": "hoge",
                    }
                ],
                "error_msg": {"non_field_errors": ["attrs id(9999) does not exist"]},
            },
            {
                "input": [
                    {
                        "id": attr["ref"].id,
                        "value": "hoge",
                    }
                ],
                "error_msg": {
                    "non_field_errors": ["attrs id(%s) - value(hoge) is not int" % attr["ref"].id]
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
            {"non_field_errors": ["mandatory attrs id(%s) is not specified" % attr["val"].id]},
        )

        attr["val"].is_public = False
        attr["val"].save()

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"non_field_errors": ["mandatory attrs id(%s) is permission denied" % attr["val"].id]},
        )

        attr["val"].delete()
        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 201)

    @mock.patch("entry.tasks.notify_create_entry.delay")
    def test_create_entry_notify(self, mock_task):
        self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id,
            json.dumps({"name": "hoge"}),
            "application/json",
        )

        self.assertTrue(mock_task.called)

    @mock.patch("custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("custom_view.call_custom")
    def test_create_entry_with_customview(self, mock_call_custom):
        def side_effect(handler_name, entity_name, user, *args):
            # Check specified parameters are expected
            self.assertEqual(entity_name, self.entity.name)
            self.assertEqual(user, self.user)

            if handler_name == "before_create_entry":
                self.assertEqual(
                    args[0], {**params, "schema": self.entity, "created_user": self.user}
                )

            if handler_name == "after_create_entry":
                entry = Entry.objects.get(name="hoge", is_active=True)
                self.assertEqual(args[0], params["attrs"])
                self.assertEqual(args[1], entry)

        mock_call_custom.side_effect = side_effect

        attr = {}
        for attr_name in [x["name"] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)
        params = {
            "name": "hoge",
            "attrs": [
                {"id": attr["val"].id, "value": "fuga"},
            ],
        }
        self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )

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
                    "type": str(AttrTypeStr),
                    "is_delete_in_chain": False,
                    "is_mandatory": True,
                    "row_index": "1",
                },
                {
                    "name": "bar",
                    "type": str(AttrTypeText),
                    "is_delete_in_chain": False,
                    "is_mandatory": True,
                    "row_index": "2",
                },
                {
                    "name": "baz",
                    "type": str(AttrTypeArrStr),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "3",
                },
                {
                    "name": "attr_bool",
                    "type": str(AttrTypeValue["boolean"]),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "4",
                },
                {
                    "name": "attr_group",
                    "type": str(AttrTypeValue["group"]),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "5",
                },
                {
                    "name": "attr_date",
                    "type": str(AttrTypeValue["date"]),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "6",
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
        self.assertEqual(len(histories[0]["details"]), 6)
