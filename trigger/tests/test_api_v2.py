import json

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue
from trigger.models import (
    TriggerAction,
    TriggerActionValue,
    TriggerCondition,
    TriggerParent,
)


class APITest(AironeViewTest):
    def setUp(self):
        super(APITest, self).setUp()

        self.user = self.guest_login()

        # create Entities that are used for each tests
        self.entity_currency = self.create_entity(self.user, "Currency")
        self.entity_people = self.create_entity(
            self.user,
            "people",
            attrs=[
                {"name": "address", "type": AttrTypeValue["string"]},
                {"name": "is_orphan", "type": AttrTypeValue["boolean"]},
            ],
        )
        self.entity_book = self.create_entity(
            self.user,
            "book",
            attrs=[
                {"name": "title", "type": AttrTypeValue["string"]},
                {"name": "borrowed_by", "type": AttrTypeValue["object"]},
                {"name": "isbn", "type": AttrTypeValue["string"]},
                {"name": "is_overdue", "type": AttrTypeValue["boolean"]},
                {"name": "in_preparation", "type": AttrTypeValue["boolean"]},
                {"name": "memo", "type": AttrTypeValue["string"]},
                {"name": "authors", "type": AttrTypeValue["array_string"]},
                {"name": "recommended_by", "type": AttrTypeValue["array_object"]},
                {"name": "price", "type": AttrTypeValue["named_object"], "ref": self.entity_currency},
                {"name": "history", "type": AttrTypeValue["array_named_object"]},
            ],
        )

        # create Entity and TriggerConditions to be retrieved
        self.entry_tom = self.add_entry(self.user, "Tom", self.entity_people)
        self.entry_yen = self.add_entry(self.user, "YEN", self.entity_currency)

        self.FULL_CONDITION_PARAMS = [
            {
                "attr_id": self.entity_book.attrs.get(name="title").id,
                "cond": "Harry Potter and the Philosopher's Stone",
            },
            {
                "attr_id": self.entity_book.attrs.get(name="borrowed_by").id,
                "cond": str(self.entry_tom.id),
            },
            {
                "attr_id": self.entity_book.attrs.get(name="is_overdue").id,
                "cond": str(True),
            },
            {
                "attr_id": self.entity_book.attrs.get(name="price").id,
                "cond": str(self.entry_yen.id),
                "hint": "entry",
            },
            {
                "attr_id": self.entity_book.attrs.get(name="price").id,
                "cond": "1000",
            },
            {
                "attr_id": self.entity_book.attrs.get(name="history").id,
                "cond": str(self.entry_tom.id),
                "hint": "entry",
            },
            {
                "attr_id": self.entity_book.attrs.get(name="history").id,
                "cond": "2024-01-01",
            },
        ]

        self.FULL_CONDITION_PARAMS_WITH_EMPTY = [
            {
                "attr_id": self.entity_book.attrs.get(name="title").id,
                "cond": "",
            },
            {
                "attr_id": self.entity_book.attrs.get(name="borrowed_by").id,
                "cond": "",
            },
            {
                "attr_id": self.entity_book.attrs.get(name="is_overdue").id,
                "cond": "",
            },
            {
                "attr_id": self.entity_book.attrs.get(name="price").id,
                "cond": "",
            },
            {
                "attr_id": self.entity_book.attrs.get(name="history").id,
                "cond": "",
            },
        ]

    def _assert_resp_results_of_action_values(self, resp_action_values, ref_entry):
        ref_action_values = [
            x
            for x in sum(
                [x["values"] for x in resp_action_values if x["attr"]["name"] == "borrowed_by"], []
            )
        ]
        self.assertEqual(
            [x for x in ref_action_values if x["ref_cond"] is not None][0]["ref_cond"],
            {
                "id": ref_entry.id,
                "name": ref_entry.name,
                "schema": {
                    "id": ref_entry.schema.id,
                    "name": ref_entry.schema.name,
                },
            },
        )
        bool_action_values = [
            x
            for x in sum(
                [x["values"] for x in resp_action_values if x["attr"]["name"] == "is_overdue"], []
            )
        ]
        self.assertTrue(all([x["bool_cond"] for x in bool_action_values]))

    def test_list_trigger_condition_and_action(self):

        # create TriggerCondition for test_entity
        settingTriggerActions = [
            {
                "attr_id": self.entity_book.attrs.get(name="isbn").id,
                "value": "978-4915512377",
            },
            {
                "attr_id": self.entity_book.attrs.get(name="borrowed_by").id,
                "value": self.entry_tom,
            },
            {
                "attr_id": self.entity_book.attrs.get(name="is_overdue").id,
                "value": str(True),
            },
        ]
        TriggerCondition.register(
            self.entity_book,
            [
                {
                    "attr_id": self.entity_book.attrs.get(name="title").id,
                    "cond": "book",
                },
                {
                    "attr_id": self.entity_book.attrs.get(name="borrowed_by").id,
                    "cond": self.entry_tom,
                },
            ],
            settingTriggerActions,
        )
        TriggerCondition.register(
            self.entity_book,
            [
                {
                    "attr_id": self.entity_book.attrs.get(name="borrowed_by").id,
                    "cond": self.entry_tom,
                }
            ],
            settingTriggerActions,
        )

        # create TriggerCondition for another entity
        TriggerCondition.register(
            self.entity_people,
            [
                {
                    "attr_id": self.entity_people.attrs.get(name="is_orphan").id,
                    "cond": True,
                }
            ],
            [{"attr_id": self.entity_people.attrs.get(name="address").id, "value": ""}],
        )

        # list all trigger has expected values
        resp = self.client.get("/trigger/api/v2/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted([t["entity"]["name"] for t in resp.json()["results"]]),
            sorted(
                [
                    self.entity_book.name,
                    self.entity_book.name,
                    self.entity_people.name,
                ]
            ),
        )

        # check ref_cond value format is correctly in the conditions
        elem_ref_cond = [
            x["ref_cond"]
            for x in sum([t["conditions"] for t in resp.json()["results"]], [])
            if x["ref_cond"] is not None
        ][0]
        self.assertEqual(
            elem_ref_cond,
            {
                "id": self.entry_tom.id,
                "name": self.entry_tom.name,
                "schema": {
                    "id": self.entry_tom.schema.id,
                    "name": self.entry_tom.schema.name,
                },
            },
        )

        # list specified Entity's triggers
        resp = self.client.get("/trigger/api/v2/?entity_id=%s" % self.entity_book.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            [t["entity"]["name"] for t in resp.json()["results"]],
            [
                self.entity_book.name,
                self.entity_book.name,
            ],
        )

        # check ref_cond value format is correctly in the actions
        self._assert_resp_results_of_action_values(
            sum([t["actions"] for t in resp.json()["results"]], []),
            self.entry_tom,
        )

    def test_create_trigger_condition_with_wrong_params_in_conditions(self):
        # send request with parameter that EnttiyAttr in conditions is incompatible with Entity
        params = {
            "entity_id": self.entity_book.id,
            "conditions": [
                {
                    "attr_id": self.entity_people.attrs.get(name="address").id,
                    "cond": "1600 Pennsylvania Avenue",
                },
            ],
            "actions": [],
        }
        resp = self.client.post("/trigger/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

    def test_create_trigger_condition_with_wrong_params_in_actions(self):
        # send request with parameter that EnttiyAttr in conditions is incompatible with Entity
        params = {
            "entity_id": self.entity_book.id,
            "conditions": [
                {
                    "attr_id": self.entity_book.attrs.get(name="title").id,
                    "cond": "The Little Prince",
                },
            ],
            "actions": [
                {
                    "attr_id": self.entity_people.attrs.get(name="is_orphan").id,
                    "value": "True",
                }
            ],
        }
        resp = self.client.post("/trigger/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

    def test_create_trigger_condition_without_element_in_conditions(self):
        # send request any conditions
        params = {
            "entity_id": self.entity_book.id,
            "conditions": [],
            "actions": [
                {
                    "attr_id": self.entity_book.attrs.get(name="memo").id,
                    "value": "non-value",
                }
            ],
        }
        resp = self.client.post("/trigger/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

    def test_create_trigger_condition_with_invalid_entity_attr_in_actions_param(self):
        # send request any conditions
        params = {
            "entity_id": self.entity_book.id,
            "conditions": [
                {
                    "attr_id": self.entity_book.attrs.get(name="title").id,
                    "cond": "Harry Potter and the Philosopher's Stone",
                },
            ],
            "actions": [
                {
                    "attr_id": -1,  # invalid ID of EntityAttr
                    "value": "value",
                }
            ],
        }
        resp = self.client.post("/trigger/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()["non_field_errors"][0]["message"],
            "actions.attr_id contains non EntityAttr of specified Entity",
        )

    def test_create_trigger_condition_without_element_in_actions(self):
        # send request any conditions
        params = {
            "entity_id": self.entity_book.id,
            "conditions": [
                {
                    "attr_id": self.entity_book.attrs.get(name="title").id,
                    "cond": "Harry Potter and the Philosopher's Stone",
                },
            ],
            "actions": [],
        }
        resp = self.client.post("/trigger/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

    def test_create_trigger_condition_with_full_params(self):
        entry_jerry = self.add_entry(self.user, "Jerry", self.entity_people)
        params = {
            "entity_id": self.entity_book.id,
            "conditions": self.FULL_CONDITION_PARAMS,
            "actions": [
                {
                    "attr_id": self.entity_book.attrs.get(name="memo").id,
                    "value": "deploy a staff to the Tom's house!",
                },
                {
                    "attr_id": self.entity_book.attrs.get(name="authors").id,
                    "values": ["hoge", "fuga"],
                },
                {
                    "attr_id": self.entity_book.attrs.get(name="borrowed_by").id,
                    "value": str(self.entry_tom.id),
                },
                {
                    "attr_id": self.entity_book.attrs.get(name="recommended_by").id,
                    "value": [self.entry_tom, entry_jerry.id],
                },
                {
                    "attr_id": self.entity_book.attrs.get(name="in_preparation").id,
                    "value": "True",
                },
            ],
        }
        resp = self.client.post("/trigger/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 201)

        # test to handle request to create TriggerCondition that is exactly same with others
        err_resp = self.client.post("/trigger/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(err_resp.status_code, 400)
        self.assertEqual(
            err_resp.json()[0]["message"],
            "There is condition that have same condition with specified one",
        )

        # This checks expected Conditions are created properly
        created_trigger = TriggerParent.objects.get(id=resp.json()["id"])
        self.assertEqual(created_trigger.entity, self.entity_book)
        self.assertEqual(
            [
                (x.attr.name, x.str_cond, x.ref_cond, x.bool_cond)
                for x in created_trigger.conditions.all()
            ],
            [
                ("title", "Harry Potter and the Philosopher's Stone", None, False),
                ("borrowed_by", "", self.entry_tom, False),
                ("is_overdue", "", None, True),
                ("price", "", self.entry_yen, False),
                ("price", "1000", None, False),
                ("history", "", self.entry_tom, False),
                ("history", "2024-01-01", None, False),
            ],
        )

        # This checks expected Actions are created properly
        self.assertEqual(
            [
                (
                    a.attr.name,
                    [(v.str_cond, v.ref_cond, v.bool_cond) for v in a.values.all()],
                )
                for a in created_trigger.actions.all()
            ],
            [
                ("memo", [("deploy a staff to the Tom's house!", None, False)]),
                ("authors", [("hoge", None, False), ("fuga", None, False)]),
                ("borrowed_by", [("", self.entry_tom, False)]),
                ("recommended_by", [("", self.entry_tom, False), ("", entry_jerry, False)]),
                ("in_preparation", [("", None, True)]),
            ],
        )

    def test_create_trigger_condition_with_empty_params(self):
        params = {
            "entity_id": self.entity_book.id,
            "conditions": self.FULL_CONDITION_PARAMS_WITH_EMPTY,
            "actions": [
                {
                    "attr_id": self.entity_book.attrs.get(name="memo").id,
                    "value": "deploy a staff to the Tom's house!",
                }
            ],
        }
        resp = self.client.post("/trigger/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 201)

        # test to handle request to create TriggerCondition that is exactly same with others
        err_resp = self.client.post("/trigger/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(err_resp.status_code, 400)
        self.assertEqual(
            err_resp.json()[0]["message"],
            "There is condition that have same condition with specified one",
        )

        # This checks expected Conditions are created properly
        created_trigger = TriggerParent.objects.get(id=resp.json()["id"])
        self.assertEqual(created_trigger.entity, self.entity_book)
        self.assertEqual(
            [
                (x.attr.name, x.str_cond, x.ref_cond, x.bool_cond)
                for x in created_trigger.conditions.all()
            ],
            [
                ("title", "", None, False),
                ("borrowed_by", "", None, False),
                ("is_overdue", "", None, False),
                ("price", "", None, False),
                ("history", "", None, False),
            ],
        )

        # This checks expected Actions are created properly
        self.assertEqual(
            [
                (
                    a.attr.name,
                    [(v.str_cond, v.ref_cond, v.bool_cond) for v in a.values.all()],
                )
                for a in created_trigger.actions.all()
            ],
            [("memo", [("deploy a staff to the Tom's house!", None, False)])],
        )

    def test_create_conditions_with_empty_value(self):
        entry_john = self.add_entry(self.user, "John Doe", self.entity_people)
        test_cases = [
            (self.entity_book.attrs.get(name="title").id, {"value": "-- DEFAULT TITLE --"}),
            (
                self.entity_book.attrs.get(name="authors").id,
                {"values": ["John Doe"]},
            ),
            (self.entity_book.attrs.get(name="in_preparation").id, {"value": "True"}),
            (
                self.entity_book.attrs.get(name="recommended_by").id,
                {"values": [str(entry_john.id)]},
            ),
        ]
        for attr_id, value_param in test_cases:
            params = {
                "entity_id": self.entity_book.id,
                "conditions": [{"attr_id": attr_id, "cond": ""}],
                "actions": [dict(**value_param, **{"attr_id": attr_id})],
            }
            resp = self.client.post("/trigger/api/v2/", json.dumps(params), "application/json")
            self.assertEqual(resp.status_code, 201)

    def test_update_trigger_condition(self):
        trigger_parent = TriggerCondition.register(
            entity=self.entity_book,
            conditions=[
                {
                    "attr_id": self.entity_book.attrs.get(name="title").id,
                    "cond": "The Little Prince",
                }
            ],
            actions=[
                {
                    "attr_id": self.entity_book.attrs.get(name="memo").id,
                    "value": "memo is updated by TriggerAction",
                }
            ],
        )

        params = {
            "entity_id": self.entity_book.id,
            "conditions": [
                {
                    "attr_id": self.entity_book.attrs.get(name="title").id,
                    "cond": "Harry Potter and the Philosopher's Stone",
                },
                {
                    "attr_id": self.entity_book.attrs.get(name="borrowed_by").id,
                    "cond": str(self.entry_tom.id),
                },
                {
                    "attr_id": self.entity_book.attrs.get(name="is_overdue").id,
                    "cond": str(True),
                },
            ],
            "actions": [
                {
                    "attr_id": self.entity_book.attrs.get(name="memo").id,
                    "value": "deploy a staff to the Tom's house!",
                },
                {
                    "attr_id": self.entity_book.attrs.get(name="history").id,
                    "named_valued": [{"id": str(self.entry_tom.id), "name": "tom"}],
                },
            ],
        }
        resp = self.client.put(
            "/trigger/api/v2/%s" % trigger_parent.id,
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # This checks expected Conditions are created properly
        created_trigger = TriggerParent.objects.get(id=resp.json()["id"])
        self.assertEqual(created_trigger.entity, self.entity_book)
        self.assertEqual(
            [
                (x.attr.name, x.str_cond, x.ref_cond, x.bool_cond)
                for x in created_trigger.conditions.all()
            ],
            [
                ("title", "Harry Potter and the Philosopher's Stone", None, False),
                ("borrowed_by", "", self.entry_tom, False),
                ("is_overdue", "", None, True),
            ],
        )

        # This checks expected Actions are created properly
        self.assertEqual(
            [
                (
                    a.attr.name,
                    [(v.str_cond, v.ref_cond, v.bool_cond) for v in a.values.all()],
                )
                for a in created_trigger.actions.all()
            ],
            [("memo", [("deploy a staff to the Tom's house!", None, False)]), ("history", [])],
        )

    def test_delete_trigger_condition(self):
        trigger_parent = TriggerCondition.register(
            entity=self.entity_book,
            conditions=[
                {
                    "attr_id": self.entity_book.attrs.get(name="title").id,
                    "cond": "The Little Prince",
                }
            ],
            actions=[
                {
                    "attr_id": self.entity_book.attrs.get(name="memo").id,
                    "value": "memo is updated by TriggerAction",
                }
            ],
        )
        resp = self.client.delete(
            "/trigger/api/v2/%s" % trigger_parent.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)

        # This checks associated instances are also removed by this request.
        self.assertFalse(TriggerParent.objects.filter(entity=self.entity_book).exists())
        self.assertEqual(TriggerCondition.objects.count(), 0)
        self.assertEqual(TriggerAction.objects.count(), 0)
        self.assertEqual(TriggerActionValue.objects.count(), 0)


    def test_create_trigger_with_all_typed_for_action(self):
        params = {
            "entity_id": self.entity_book.id,
            "conditions": [
                {
                    "attr_id": self.entity_book.attrs.get(name="title").id,
                    "cond": "",
                },
            ],
            "actions": [
                {
                    "attr_id": self.entity_book.attrs.get(name="title").id,
                    "value": "default title",
                },
            ],
        }
        resp = self.client.post("/trigger/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 201)
