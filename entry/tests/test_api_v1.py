import json
from datetime import date

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue
from entity.models import Entity, EntityAttr
from entry.models import Entry
from entry.settings import CONFIG
from group.models import Group


class ViewTest(AironeViewTest):
    def test_get_entries(self):
        admin = self.admin_login()

        # create Entity & Entries
        entity = Entity.objects.create(name="Entity", created_user=admin)
        for index in range(0, CONFIG.MAX_LIST_ENTRIES + 1):
            name = "e-%s" % index
            Entry.objects.create(name=name, schema=entity, created_user=admin)

        # send request without keyword
        resp = self.client.get("/entry/api/v1/get_entries/%d/" % entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")

        self.assertTrue("results" in resp.json())
        self.assertEqual(len(resp.json()["results"]), CONFIG.MAX_LIST_ENTRIES)

        # send request with empty keyword
        resp = self.client.get("/entry/api/v1/get_entries/%d/" % entity.id, {"keyword": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("results" in resp.json())
        self.assertEqual(len(resp.json()["results"]), CONFIG.MAX_LIST_ENTRIES)

        # send request with keyword parameter
        resp = self.client.get("/entry/api/v1/get_entries/%d/" % entity.id, {"keyword": "10"})
        self.assertEqual(resp.status_code, 200)

        self.assertTrue("results" in resp.json())
        self.assertEqual(len(resp.json()["results"]), 2)
        self.assertTrue(
            all([x["name"] == "e-10" or x["name"] == "e-100" for x in resp.json()["results"]])
        )

        # send request with invalid keyword parameter
        resp = self.client.get(
            "/entry/api/v1/get_entries/%d/" % entity.id, {"keyword": "invalid-keyword"}
        )
        self.assertEqual(resp.status_code, 200)

        self.assertTrue("results" in resp.json())
        self.assertEqual(len(resp.json()["results"]), 0)

        # send request to check keyword would be insensitive case
        resp = self.client.get("/entry/api/v1/get_entries/%d/" % entity.id, {"keyword": "E-0"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 1)
        self.assertTrue(resp.json()["results"][0]["name"], "e-0")

        """
        Check for cases with special characters
        """
        add_chars = [
            "!",
            '"',
            "#",
            "$",
            "%",
            "'",
            "(",
            ")",
            "-",
            "=",
            "^",
            "~",
            "@",
            "`",
            "[",
            "]",
            "{",
            "}",
            ";",
            "+",
            ":",
            "*",
            ",",
            "<",
            ">",
            ".",
            "/",
            "?",
            "_",
            " " "&",
            "|",
        ]
        test_suites = []
        for i, add_char in enumerate(add_chars):
            entry_name = "test%s%s" % (i, add_char)
            entry = Entry.objects.create(name=entry_name, schema=entity, created_user=admin)
            entry.register_es()

            test_suites.append(
                {"search_word": add_char, "ret_cnt": 1, "ret_entry_name": entry_name}
            )

        for test_suite in test_suites:
            resp = self.client.get(
                "/entry/api/v1/get_entries/%s/" % entity.id,
                {"keyword": test_suite["search_word"]},
            )
            ret_cnt = (
                test_suite["ret_cnt"]
                if test_suite["search_word"] != "-"
                else CONFIG.MAX_LIST_ENTRIES
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(resp.json()["results"]), ret_cnt)
            self.assertEqual(resp.json()["results"][0]["name"], test_suite["ret_entry_name"])

    def test_get_entries_with_multiple_ids(self):
        admin = self.admin_login()

        # create Entities & Entries
        for entity_name in ["Entity1", "Entity2"]:
            entity = Entity.objects.create(name="Entity", created_user=admin)
            for index in range(0, 10):
                name = "e-%s" % index
                Entry.objects.create(name=name, schema=entity, created_user=admin)

        # specify multiple IDs of Entity
        entity_ids = "%s,%s" % (Entity.objects.first().id, Entity.objects.last().id)
        resp = self.client.get("/entry/api/v1/get_entries/%s/" % (entity_ids))
        self.assertEqual(resp.status_code, 200)

        self.assertTrue("results" in resp.json())
        self.assertEqual(len(resp.json()["results"]), 20)

        # specify multiple IDs including invalid ones
        # this expects that the only entries of valid id will be returned.
        entity_ids = ",,,%s,,,,,9999" % Entity.objects.first().id
        resp = self.client.get("/entry/api/v1/get_entries/%s/" % entity_ids)
        self.assertEqual(resp.status_code, 200)

        self.assertTrue("results" in resp.json())
        self.assertEqual(len(resp.json()["results"]), 10)

    def test_get_entries_with_multiple_entities(self):
        admin = self.admin_login()

        # create Entity&Entries
        for entity_name in ["Entity1", "Entity2"]:
            entity = Entity.objects.create(name=entity_name, created_user=admin)
            for index in range(0, 5):
                name = "e-%s" % index
                Entry.objects.create(name=name, schema=entity, created_user=admin)

        entity_ids = ",".join([str(x.id) for x in Entity.objects.all()])
        resp = self.client.get("/entry/api/v1/get_entries/%s/" % entity_ids)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertTrue("results" in resp.json())
        self.assertEqual(len(resp.json()["results"]), 10)

    def test_get_entries_with_inactive_parameter(self):
        user = self.guest_login()

        # create entries, then delete them to search inactive entries
        entity = Entity.objects.create(name="Entity", created_user=user)
        for name in ["foo", "bar", "baz"]:
            entry = Entry.objects.create(name=name, schema=entity, created_user=user)
            entry.delete()

        # confirms that there is no active entry in this entity
        resp = self.client.get("/entry/api/v1/get_entries/%d/" % entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(resp.json()["results"], [])

        # confirms that deleted entries are got when 'is_active=False' is specified
        resp = self.client.get(
            "/entry/api/v1/get_entries/%d/" % entity.id,
            {
                "keyword": "ba",
                "is_active": False,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(len(resp.json()["results"]), 2)

    def test_get_referrals(self):
        admin = self.admin_login()

        # create Entity&Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=admin)
        ref_entry = Entry.objects.create(
            name="Referred Entry", schema=ref_entity, created_user=admin
        )

        entity = Entity.objects.create(name="Entity", created_user=admin)
        entity.attrs.add(
            EntityAttr.objects.create(
                **{
                    "name": "Refer",
                    "type": AttrTypeValue["object"],
                    "created_user": admin,
                    "parent_entity": entity,
                }
            )
        )

        for index in range(0, CONFIG.MAX_LIST_REFERRALS + 1):
            name = "e-%s" % index
            e = Entry.objects.create(name=name, schema=entity, created_user=admin)
            e.complement_attrs(admin)

            ref_attr = e.attrs.get(name="Refer")
            ref_attr.add_value(admin, ref_entry)

        # send request without keyword
        resp = self.client.get("/entry/api/v1/get_referrals/%d/" % ref_entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")

        self.assertEqual(resp.json()["total_count"], CONFIG.MAX_LIST_REFERRALS + 1)
        self.assertEqual(resp.json()["found_count"], CONFIG.MAX_LIST_REFERRALS)
        self.assertTrue(
            all(["id" in x and "name" in x and "entity" in x for x in resp.json()["entries"]])
        )

        # send request with keyword parameter
        resp = self.client.get(
            "/entry/api/v1/get_referrals/%d/" % ref_entry.id, {"keyword": "e-10"}
        )
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.json()["total_count"], CONFIG.MAX_LIST_REFERRALS + 1)
        self.assertEqual(resp.json()["found_count"], 1)

        # send request with invalid keyword parameter
        resp = self.client.get(
            "/entry/api/v1/get_referrals/%d/" % ref_entry.id,
            {"keyword": "invalid_keyword"},
        )
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.json()["total_count"], CONFIG.MAX_LIST_REFERRALS + 1)
        self.assertEqual(resp.json()["found_count"], 0)

    def test_get_attr_referrals_of_group(self):
        user = self.guest_login()

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
            resp = self.client.get("/entry/api/v1/get_attr_referrals/%d/" % attr.id)
            self.assertEqual(resp.status_code, 200)

            # This expects results has all groups information.
            self.assertEqual(
                sorted(resp.json()["results"], key=lambda x: x["id"]),
                sorted(
                    [{"id": g.id, "name": g.name} for g in Group.objects.all()],
                    key=lambda x: x["id"],
                ),
            )

        # test to get groups which are only active and matched with keyword
        groups[2].delete()
        for attr in entity.attrs.all():
            resp = self.client.get(
                "/entry/api/v1/get_attr_referrals/%d/" % attr.id, {"keyword": "ba"}
            )
            self.assertEqual(resp.status_code, 200)

            # This expects results has only information of 'g-bar' because 'g-foo' is
            # not matched with keyword and 'g-baz' has already been deleted.
            self.assertEqual(resp.json()["results"], [{"id": groups[1].id, "name": groups[1].name}])

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
        resp = self.client.get("/entry/api/v1/get_attr_referrals/%s/" % attr.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), CONFIG.MAX_LIST_REFERRALS)

        # specify invalid Attribute ID
        resp = self.client.get("/entry/api/v1/get_attr_referrals/9999/")
        self.assertEqual(resp.status_code, 400)

        # speify valid Attribute ID and a enalbed keyword
        resp = self.client.get("/entry/api/v1/get_attr_referrals/%s/" % attr.id, {"keyword": "e-1"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertTrue("results" in resp.json())

        # This means e-1 and 'e-10' to 'e-19' are returned
        self.assertEqual(len(resp.json()["results"]), 11)

        # speify valid Attribute ID and a unabailabe keyword
        resp = self.client.get(
            "/entry/api/v1/get_attr_referrals/%s/" % attr.id, {"keyword": "hoge"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 0)

        # Add new data
        for index in [101, 111, 100, 110]:
            Entry.objects.create(name="e-%s" % index, schema=ref_entity, created_user=admin)

        # Run with 'e-1' as keyword
        resp = self.client.get("/entry/api/v1/get_attr_referrals/%s/" % attr.id, {"keyword": "e-1"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertTrue("results" in resp.json())

        # Check the number of return values
        self.assertEqual(len(resp.json()["results"]), 15)

        # Check if it is sorted in the expected order
        targets = [1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 100, 101, 110, 111]
        for i, res in enumerate(resp.json()["results"]):
            self.assertEqual(res["name"], "e-%s" % targets[i])

        # send request with keywords that hit more than MAX_LIST_REFERRALS
        Entry.objects.create(name="e", schema=ref_entity, created_user=admin)

        resp = self.client.get("/entry/api/v1/get_attr_referrals/%d/" % attr.id, {"keyword": "e"})
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.json()["results"][0]["name"], "e")

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
            "/entry/api/v1/get_attr_referrals/%s/" % entity_attr.id, {"keyword": "e-1"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertTrue("results" in resp.json())

        # This means e-1 and 'e-10' to 'e-19' are returned
        self.assertEqual(len(resp.json()["results"]), 11)

    def test_advanced_search(self):
        admin = self.admin_login()

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=admin)
        for index in range(0, 20):
            Entry.objects.create(name="r-%s" % index, schema=ref_entity, created_user=admin)

        attr_infos = [
            {"name": "attr_ref", "type": AttrTypeValue["object"], "ref": ref_entity},
            {"name": "attr_val", "type": AttrTypeValue["string"]},
        ]
        entity = Entity.objects.create(name="Entity", created_user=admin)

        for attr_info in attr_infos:
            entity_attr = EntityAttr.objects.create(
                **{
                    "name": attr_info["name"],
                    "type": attr_info["type"],
                    "created_user": admin,
                    "parent_entity": entity,
                }
            )
            if "ref" in attr_info:
                entity_attr.referral.add(attr_info["ref"])

            entity.attrs.add(entity_attr)

        for index in range(0, 20):
            entry = Entry.objects.create(name="e-%d" % index, schema=entity, created_user=admin)
            entry.complement_attrs(admin)
            for attr_name in ["attr_ref", "attr_val"]:
                attr = entry.attrs.get(name=attr_name)

                if attr.schema.type & AttrTypeValue["string"]:
                    attr.add_value(admin, str(index))

                elif attr.schema.type & AttrTypeValue["object"]:
                    attr.add_value(admin, Entry.objects.get(name="r-%d" % index))

        # checks the the API request to get entries with 'or' cond_link parameter
        params = {
            "cond_link": "or",
            "cond_params": [
                {"type": "text", "value": "5"},
                {"type": "entry", "value": str(Entry.objects.get(name="r-6").id)},
            ],
        }
        resp = self.client.post(
            "/entry/api/v1/search_entries/%s" % entity.id,
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(len(resp.json()["results"]), 3)
        self.assertTrue(any([x for x in resp.json()["results"] if x["name"] == "e-5"]))
        self.assertTrue(any([x for x in resp.json()["results"] if x["name"] == "e-15"]))
        self.assertTrue(any([x for x in resp.json()["results"] if x["name"] == "e-6"]))

        # checks the the API request to not get entries with 'or' cond_link parameter
        params = {
            "cond_link": "or",
            "cond_params": [
                {"type": "text", "value": "abcd"},
            ],
        }
        resp = self.client.post(
            "/entry/api/v1/search_entries/%s" % entity.id,
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(len(resp.json()["results"]), 0)

        # checks the the API request to get entries with 'and' cond_link parameter
        params = {
            "cond_link": "and",
            "cond_params": [
                {"type": "text", "value": "5"},
                {"type": "entry", "value": str(Entry.objects.get(name="r-5").id)},
            ],
        }
        resp = self.client.post(
            "/entry/api/v1/search_entries/%s" % entity.id,
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(len(resp.json()["results"]), 1)
        self.assertTrue(any([x for x in resp.json()["results"] if x["name"] == "e-5"]))

        # checks the the API request to not get entries with 'and' cond_link parameter
        params = {
            "cond_link": "and",
            "cond_params": [
                {"type": "text", "value": "5"},
                {"type": "entry", "value": str(Entry.objects.get(name="r-6").id)},
            ],
        }
        resp = self.client.post(
            "/entry/api/v1/search_entries/%s" % entity.id,
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(len(resp.json()["results"]), 0)

        # checks the the API request to get entries without cond_link parameter
        params = {
            "cond_params": [
                {"type": "text", "value": "5"},
                {"type": "text", "value": "6"},
            ],
        }
        resp = self.client.post(
            "/entry/api/v1/search_entries/%s" % entity.id,
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(len(resp.json()["results"]), 4)
        self.assertTrue(any([x for x in resp.json()["results"] if x["name"] == "e-5"]))
        self.assertTrue(any([x for x in resp.json()["results"] if x["name"] == "e-15"]))
        self.assertTrue(any([x for x in resp.json()["results"] if x["name"] == "e-6"]))
        self.assertTrue(any([x for x in resp.json()["results"] if x["name"] == "e-16"]))

        # checks the the API request to get entries with regex pattern and 'and' cond_link
        params = {
            "cond_link": "and",
            "cond_params": [
                {"type": "text", "value": "1"},
                {"type": "text", "value": "2"},
            ],
        }
        resp = self.client.post(
            "/entry/api/v1/search_entries/%s" % entity.id,
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(len(resp.json()["results"]), 1)
        self.assertTrue(any([x for x in resp.json()["results"] if x["name"] == "e-12"]))

        # checks the the API request to get entries with regex pattern and 'or' cond_link
        params = {
            "cond_link": "or",
            "cond_params": [
                {"type": "text", "value": "1"},
                {"type": "text", "value": "2"},
            ],
        }
        resp = self.client.post(
            "/entry/api/v1/search_entries/%s" % entity.id,
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(len(resp.json()["results"]), 12)

    def test_get_entry_history(self):
        def _get_exp_value(attr, attr_value):
            if attr.schema.type & AttrTypeValue["named"]:
                return {
                    "value": attr_value["name"],
                    "referral": {
                        "id": attr_value["id"].id,
                        "name": attr_value["id"].name,
                    },
                }
            elif (
                attr.schema.type & AttrTypeValue["object"]
                or attr.schema.type & AttrTypeValue["group"]
            ):
                return {"id": attr_value.id, "name": attr_value.name}
            elif attr.schema.type & AttrTypeValue["date"]:
                return str(attr_value)
            else:
                return attr_value

        user = self.guest_login()

        # initialize Entity and Entry for this test
        ref_entity = Entity.objects.create(name="Entity", created_user=user)
        ref_entries = [
            Entry.objects.create(name=x, created_user=user, schema=ref_entity) for x in ["r0", "r1"]
        ]
        groups = [Group.objects.create(name=x) for x in ["g0", "g1"]]
        attrinfo = {
            "string": {"values": ["foo", "bar"]},
            "object": {"values": [ref_entries[0], ref_entries[1]]},
            "named_object": {"values": [{"name": x.name, "id": x} for x in ref_entries]},
            "array_object": {"values": [[ref_entries[0]], [ref_entries[1]]]},
            "array_string": {"values": [["foo"], ["bar"]]},
            "array_named_object": {
                "values": [
                    [{"name": "foo", "id": ref_entries[0]}],
                    [{"name": "bar", "id": ref_entries[1]}],
                ]
            },
            "array_group": {"values": [[groups[0]], [groups[1]]]},
            "text": {"values": ["hoge", "fuga"]},
            "boolean": {"values": [True, False]},
            "group": {"values": [groups[0], groups[1]]},
            "date": {"values": [date(2020, 1, 1), date(2021, 1, 1)]},
        }
        entity = Entity.objects.create(name="Entity", created_user=user)
        for name in attrinfo.keys():
            entity.attrs.add(
                EntityAttr.objects.create(
                    **{
                        "name": name,
                        "type": AttrTypeValue[name],
                        "created_user": user,
                        "parent_entity": entity,
                    }
                )
            )

        entry = Entry.objects.create(name="Entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        # set registering value for checking AttributeValue history
        for attrname, info in attrinfo.items():
            attr = entry.attrs.get(schema__name=attrname)
            for value in info["values"]:
                attr.add_value(user, value)

        # test sending request for the API endpoint of get_entry_history
        resp = self.client.get("/entry/api/v1/get_entry_history/%d/" % entry.id, {"count": 100})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")

        resp_data = resp.json()["results"]
        self.assertIsInstance(resp_data, list)

        # This checks returned data has expected one
        for attrname, info in attrinfo.items():
            attr = entry.attrs.get(schema__name=attrname)
            attr_value_history = [x for x in resp_data if x["attr_name"] == attrname]

            if attr.schema.type & AttrTypeValue["array"]:
                exp_curr_value = [_get_exp_value(attr, x) for x in info["values"][1]]
                exp_prev_value = [_get_exp_value(attr, x) for x in info["values"][0]]
            else:
                exp_curr_value = _get_exp_value(attr, info["values"][1])
                exp_prev_value = _get_exp_value(attr, info["values"][0])

            self.assertTrue(all([x["attr_id"] == attr.id for x in attr_value_history]))

            # check order of former value and previous value
            for (index, history_value) in enumerate(attr_value_history):
                if (
                    attr.schema.type & AttrTypeValue["array"]
                    and not history_value["curr"]["value"]
                    and not history_value["prev"]
                ):
                    continue

                if not history_value["prev"] or not history_value["prev"]["value"]:
                    # The oldest update history
                    self.assertEqual(history_value["curr"]["value"], exp_prev_value)
                    if attr.schema.type & AttrTypeValue["array"]:
                        self.assertEqual(history_value["prev"]["value"], [])
                    else:
                        self.assertEqual(history_value["prev"], None)

                else:
                    # The latest update history
                    self.assertEqual(history_value["curr"]["value"], exp_curr_value)
                    self.assertEqual(history_value["prev"]["value"], exp_prev_value)

    def test_get_entry_info(self):
        user = self.guest_login()

        # initialize Entity and Entry
        entity = Entity.objects.create(name="Entity", created_user=user)
        entity.attrs.add(
            EntityAttr.objects.create(
                **{
                    "name": "attr",
                    "type": AttrTypeValue["string"],
                    "created_user": user,
                    "parent_entity": entity,
                }
            )
        )

        entry = Entry.objects.create(name="Entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.attrs.first().add_value(user, "hoge")

        # send request with invalid entry_id
        resp = self.client.get("/entry/api/v1/get_entry_info/9999")
        self.assertEqual(resp.status_code, 400)

        # send request with valid entry_id
        resp = self.client.get("/entry/api/v1/get_entry_info/%d" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], entry.id)

        # check context for attributes
        for attrinfo in resp.json()["attrs"]:
            self.assertEqual(
                sorted(attrinfo.keys()),
                sorted(["id", "name", "type", "index", "value"]),
            )

    def test_create_entry_attr(self):
        user = self.guest_login()

        # initialize Entity and Entry
        entity = Entity.objects.create(name="Entity", created_user=user)
        entity_attr = EntityAttr.objects.create(
            **{
                "name": "attr",
                "type": AttrTypeValue["string"],
                "created_user": user,
                "parent_entity": entity,
            }
        )
        entity.attrs.add(entity_attr)
        entry = Entry.objects.create(name="Entry", schema=entity, created_user=user)

        # Attribute does not exist
        params = {
            "entity_attr_id": entity_attr.id,
        }
        resp = self.client.post(
            "/entry/api/v1/create_entry_attr/%s" % entry.id,
            json.dumps(params),
            "application/json",
        )
        attr = entry.attrs.get(schema=entity_attr, is_active=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], attr.id)

        # Attribute exists
        resp = self.client.post(
            "/entry/api/v1/create_entry_attr/%s" % entry.id,
            json.dumps(params),
            "application/json",
        )
        attr = entry.attrs.get(schema=entity_attr, is_active=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], attr.id)

    def test_create_entry_attr_without_param(self):
        user = self.guest_login()

        # initialize Entity and Entry
        entity = Entity.objects.create(name="Entity", created_user=user)
        entry = Entry.objects.create(name="Entry", schema=entity, created_user=user)

        # specify EntityAttr that does not int
        params = {
            "entity_attr_id": "hoge",
        }
        resp = self.client.post(
            "/entry/api/v1/create_entry_attr/%s" % entry.id,
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"Invalid parameters are specified")

        # specify EntityAttr that does not exist
        params = {
            "entity_attr_id": 999999,
        }
        resp = self.client.post(
            "/entry/api/v1/create_entry_attr/%s" % entry.id,
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.content, b"There is no EntityAttr which is specified by entity_attr_id"
        )

        # specify Entry that does not exist
        resp = self.client.post(
            "/entry/api/v1/create_entry_attr/999999",
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"There is no Entry which is specified by entry_id")
