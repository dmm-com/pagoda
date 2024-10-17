import json

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.models import Entry


class APITest(AironeViewTest):
    def test_search_invalid_param(self):
        self.admin_login()
        valid_params = {
            "entities": [1],
            "attrinfo": [],
        }
        invalid_params = [
            {"entities": "hoge"},
            {"entry_name": ["hoge"]},
            {"attrinfo": "hoge"},
            {"is_output_all": "hoge"},
            {"referral": ["hoge"]},
            {"entry_limit": "hoge"},
        ]
        resp = self.client.post("/api/v1/entry/search", [], "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'"parameter must be in dictionary format"')

        for invalid_param in invalid_params:
            params = {**valid_params, **invalid_param}
            resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
            self.assertEqual(resp.status_code, 400)

        params = {**valid_params, **{"attrinfo": [{"hoge": "value"}]}}
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"\"The type of parameter 'attrinfo' is incorrect\"")

        params = {**valid_params, **{"attrinfo": [{"name": ["hoge"]}]}}
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"\"The type of parameter 'attrinfo' is incorrect\"")

        params = {
            **valid_params,
            **{"attrinfo": [{"name": "value", "keyword": ["hoge"]}]},
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"\"The type of parameter 'attrinfo' is incorrect\"")

    def test_narrow_down_advanced_search_results(self):
        user = self.admin_login()

        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(
            name="referred_entry", schema=ref_entity, created_user=user
        )
        ref_entry.register_es()

        for entity_index in range(0, 2):
            entity = Entity.objects.create(name="entity-%d" % entity_index, created_user=user)
            EntityAttr.objects.create(
                **{
                    "name": "attr",
                    "type": AttrType.STRING,
                    "created_user": user,
                    "parent_entity": entity,
                }
            )

            attr_ref = EntityAttr.objects.create(
                **{
                    "name": "attr_ref",
                    "type": AttrType.OBJECT,
                    "created_user": user,
                    "parent_entity": entity,
                }
            )
            attr_ref.referral.add(ref_entry)

            for entry_index in range(0, 10):
                entry = Entry.objects.create(
                    name="entry-%d" % (entry_index), schema=entity, created_user=user
                )
                entry.complement_attrs(user)

                # add an AttributeValue
                entry.attrs.get(schema__name="attr").add_value(user, "data-%d" % entry_index)
                entry.attrs.get(schema__name="attr_ref").add_value(user, ref_entry)

                # register entry to the Elasticsearch
                entry.register_es()

        # send request without mandatory parameter
        resp = self.client.post("/api/v1/entry/search")
        self.assertEqual(resp.status_code, 400)

        # send request with invalid parameters (entities and attrinfo require value of list but
        # but specify other typed ones)
        params = {
            "entities": "entity-1",
            "attrinfo": {"name": "attr", "keyword": "data-5"},
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

        # send search request and checks returned values are valid with several format of parameter,
        # This tests specifing informations of entity both id and name.
        hint_entities = [
            [x.id for x in Entity.objects.filter(name__regex="^entity-")],
            ["entity-%d" % i for i in range(0, 2)],
        ]
        for hint_entity in hint_entities:
            params = {
                "entities": hint_entity,
                "attrinfo": [{"name": "attr", "keyword": "data-5"}],
                "is_output_all": False,
            }
            resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")

            self.assertEqual(resp.status_code, 200)

            result = resp.json()["result"]
            self.assertEqual(result["ret_count"], 2)

        # send search request with 'hint_referral' parameter
        params = {
            "entities": [ref_entity.id],
            "attrinfo": [],
            "referral": "",
            "is_output_all": False,
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)

        result = resp.json()["result"]
        self.assertEqual(result["ret_count"], 1)
        self.assertEqual(
            sorted([x["id"] for x in result["ret_values"][0]["referrals"]]),
            sorted([x.id for x in ref_entry.get_referred_objects()]),
        )

        params = {
            "entities": [ref_entity.id],
            "attrinfo": [],
            "referral": "hogefuga",  # this is invalid referral name
            "is_output_all": False,
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["result"]["ret_count"], 0)

    def test_api_referred_entry(self):
        user = self.guest_login()

        entity_ref = Entity.objects.create(name="ref", created_user=user)
        entity = Entity.objects.create(name="E", created_user=user)
        entity2 = Entity.objects.create(name="E2", created_user=user)

        # set EntityAttr that refers entity_ref
        attr_info = [
            {"name": "r0", "type": AttrType.OBJECT},
            {"name": "r1", "type": AttrType.NAMED_OBJECT},
            {"name": "r2", "type": AttrType.ARRAY_OBJECT},
            {"name": "r3", "type": AttrType.ARRAY_NAMED_OBJECT},
        ]
        for info in attr_info:
            attr = EntityAttr.objects.create(
                **{
                    "name": info["name"],
                    "type": info["type"],
                    "created_user": user,
                    "parent_entity": entity,
                }
            )
            attr.referral.add(entity_ref)
            attr2 = EntityAttr.objects.create(
                **{
                    "name": info["name"],
                    "type": info["type"],
                    "created_user": user,
                    "parent_entity": entity2,
                }
            )
            attr2.referral.add(entity_ref)

        # create referred entries
        refs = [
            Entry.objects.create(name="r%d" % i, schema=entity_ref, created_user=user)
            for i in range(0, 5)
        ]

        # create referring entries and set values for each Attribute
        entry = Entry.objects.create(name="e", schema=entity, created_user=user)
        entry.complement_attrs(user)

        entry.attrs.get(name="r0").add_value(user, refs[0])
        entry.attrs.get(name="r1").add_value(user, {"name": "foo", "id": refs[1]})
        entry.attrs.get(name="r2").add_value(user, [refs[2]])
        entry.attrs.get(name="r3").add_value(user, [{"name": "bar", "id": refs[3]}])

        entry2 = Entry.objects.create(name="e2", schema=entity2, created_user=user)
        entry2.complement_attrs(user)

        entry2.attrs.get(name="r0").add_value(user, refs[0])
        entry2.attrs.get(name="r1").add_value(user, {"name": "foo", "id": refs[1]})
        entry2.attrs.get(name="r2").add_value(user, [refs[2]])
        entry2.attrs.get(name="r3").add_value(user, [{"name": "bar", "id": refs[3]}])

        # send request without entry parameter
        resp = self.client.get("/api/v1/entry/referral")
        self.assertEqual(resp.status_code, 400)

        # send request with invalid entry parameter
        resp = self.client.get("/api/v1/entry/referral?entry=hoge")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"result": []})

        # check to be able to get referred object no matter whether AttributeType
        for index in range(0, 4):
            resp = self.client.get("/api/v1/entry/referral?entry=%s" % refs[index].name)
            self.assertEqual(resp.status_code, 200)

            result = resp.json()["result"]
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], refs[index].id)
            self.assertEqual(result[0]["entity"], {"id": entity_ref.id, "name": entity_ref.name})
            self.assertEqual(
                result[0]["referral"],
                [
                    {
                        "id": entry.id,
                        "name": entry.name,
                        "entity": {"id": entity.id, "name": entity.name},
                    },
                    {
                        "id": entry2.id,
                        "name": entry2.name,
                        "entity": {"id": entity2.id, "name": entity2.name},
                    },
                ],
            )

        # check the case of no referred object
        resp = self.client.get("/api/v1/entry/referral?entry=%s" % refs[4].name)
        self.assertEqual(resp.status_code, 200)

        result = resp.json()["result"]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], refs[4].id)
        self.assertEqual(result[0]["referral"], [])

        # check the case of entity param exists
        for index in range(0, 4):
            resp = self.client.get(
                "/api/v1/entry/referral?entry=%s&entity=%s" % (refs[index].name, entity_ref.name)
            )
            self.assertEqual(resp.status_code, 200)

            result = resp.json()["result"]
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], refs[index].id)
            self.assertEqual(result[0]["entity"], {"id": entity_ref.id, "name": entity_ref.name})
            self.assertEqual(
                result[0]["referral"],
                [
                    {
                        "id": entry.id,
                        "name": entry.name,
                        "entity": {"id": entity.id, "name": entity.name},
                    },
                    {
                        "id": entry2.id,
                        "name": entry2.name,
                        "entity": {"id": entity2.id, "name": entity2.name},
                    },
                ],
            )

        # check the case of target entity param exists
        for index in range(0, 4):
            resp = self.client.get(
                "/api/v1/entry/referral?entry=%s&target_entity=%s"
                % (refs[index].name, entity2.name)
            )
            self.assertEqual(resp.status_code, 200)

            result = resp.json()["result"]
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], refs[index].id)
            self.assertEqual(result[0]["entity"], {"id": entity_ref.id, "name": entity_ref.name})
            self.assertEqual(
                result[0]["referral"],
                [
                    {
                        "id": entry2.id,
                        "name": entry2.name,
                        "entity": {"id": entity2.id, "name": entity2.name},
                    }
                ],
            )

        # check the case of quiet param exists
        for index in range(0, 4):
            resp = self.client.get("/api/v1/entry/referral?entry=%s&quiet=1" % refs[index].name)
            self.assertEqual(resp.status_code, 200)

            result = resp.json()["result"]
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], refs[index].id)
            self.assertEqual(result[0]["entity"], {"id": entity_ref.id, "name": entity_ref.name})
            self.assertEqual(
                result[0]["referral"],
                [
                    {"id": entry.id, "name": entry.name, "entity": {}},
                    {"id": entry2.id, "name": entry2.name, "entity": {}},
                ],
            )

    def test_search_with_large_size_parameter(self):
        self.admin_login()

        params = {
            "entities": ["entity-1"],
            "attrinfo": [{"name": "attr", "keyword": "A" * 250}],
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'"Sending parameter is too large"')

        params = {
            "entities": ["entity-1"],
            "attrinfo": [{"name": "attr"}],
            "entry_name": "A" * 250,
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'"Sending parameter is too large"')

        params = {
            "entities": ["entity-1"],
            "attrinfo": [{"name": "attr", "keyword": "A" * 249}],
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)

        params = {
            "entities": ["entity-1"],
            "attrinfo": [{"name": "attr"}],
            "entry_name": "A" * 249,
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)

    def test_search_with_hint_entry_name(self):
        user = self.guest_login()

        # Initialize Entity and Entries, then register created entries to the Elasticsearch
        entity = Entity.objects.create(name="entity", created_user=user)
        for name in ["foo", "bar", "baz"]:
            Entry.objects.create(name=name, schema=entity, created_user=user).register_es()

        # send search request with a part of name of entries
        params = {"entities": ["entity"], "entry_name": "ba", "attrinfo": []}
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["result"]["ret_count"], 2)
        self.assertEqual(
            [x["entry"]["name"] for x in resp.json()["result"]["ret_values"]],
            ["bar", "baz"],
        )

        # send search request with non-existed name
        params = {
            "entities": ["entity"],
            "entry_name": "non-existed-entry",
            "attrinfo": [],
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["result"]["ret_count"], 0)
        self.assertEqual(resp.json()["result"]["ret_values"], [])

    def test_search_with_entry_limit(self):
        user = self.guest_login()

        # Initialize Entity and Entries, then register created entries to the Elasticsearch
        entity = Entity.objects.create(name="entity", created_user=user)
        for name in ["foo", "bar", "baz"]:
            Entry.objects.create(name=name, schema=entity, created_user=user).register_es()

        # send search request with a part of name of entries
        params = {
            "entities": ["entity"],
            "entry_name": "ba",
            "attrinfo": [],
            "entry_limit": 1,
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["result"]["ret_count"], 2)
        self.assertEqual(len([x for x in resp.json()["result"]["ret_values"]]), 1)

    def test_search_with_no_permission_entity(self):
        user = self.guest_login()

        # Initialize Entity and Entries, then register created entries to the Elasticsearch
        entity = Entity.objects.create(name="entity", created_user=user)
        for name in ["foo", "bar", "baz"]:
            Entry.objects.create(name=name, schema=entity, created_user=user).register_es()

        # Initialize no permission Entity
        no_entity = Entity.objects.create(name="no_entity", created_user=user, is_public=False)
        for name in ["foo", "bar", "baz"]:
            Entry.objects.create(name=name, schema=no_entity, created_user=user).register_es()

        # send search request with a part of name of entries
        params = {
            "entities": ["entity", "no_entity"],
            "entry_name": "ba",
            "attrinfo": [],
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["result"]["ret_count"], 2)
        self.assertEqual(len([x for x in resp.json()["result"]["ret_values"]]), 2)
        self.assertEqual(
            [x["entity"]["name"] for x in resp.json()["result"]["ret_values"]],
            ["entity", "entity"],
        )

    def test_search_without_is_output_all(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)
        EntityAttr.objects.create(
            **{
                "name": "attr1",
                "type": AttrType.STRING,
                "created_user": user,
                "parent_entity": entity,
            }
        )
        EntityAttr.objects.create(
            **{
                "name": "attr2",
                "type": AttrType.STRING,
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.attrs.get(schema__name="attr1").add_value(user, "value1")
        entry.attrs.get(schema__name="attr2").add_value(user, "value2")
        entry.register_es()

        # is_output_all false
        params = {
            "entities": [entity.id],
            "attrinfo": [{"name": "attr1"}],
            "is_output_all": False,
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 200)
        result = resp.json()["result"]
        self.assertEqual(list(result["ret_values"][0]["attrs"].keys()), ["attr1"])

        # is_output_all is default true
        params = {
            "entities": [entity.id],
            "attrinfo": [{"name": "attr1"}],
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 200)
        result = resp.json()["result"]
        self.assertEqual(list(result["ret_values"][0]["attrs"].keys()), ["attr1", "attr2"])

    def test_search_with_invalid_entity_param(self):
        self.guest_login()

        params = {
            "entities": [],
            "attrinfo": [{"name": "attr"}],
        }
        resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'"The entities parameters are required"')

    def test_search_boolean_type_value(self):
        user = self.guest_login()

        test_entity = self.create_entity(
            user,
            "TestEntity",
            attrs=[
                {
                    "name": "boolean",
                    "type": AttrType.BOOLEAN,
                }
            ],
        )

        entry = self.add_entry(user, "Entry", test_entity)
        attr = entry.attrs.last()

        # This checks boolean typed results of advanced search are expected value and expected type
        for value in [True, False]:
            attr.add_value(user, value)
            entry.register_es()

            params = {
                "entities": [test_entity.id],
                "attrinfo": [{"name": "boolean"}],
            }
            resp = self.client.post("/api/v1/entry/search", json.dumps(params), "application/json")
            self.assertEqual(
                resp.json()["result"]["ret_values"][0]["attrs"]["boolean"]["value"], value
            )
