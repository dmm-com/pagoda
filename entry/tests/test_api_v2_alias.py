import json

from airone.lib.test import AironeViewTest
from entry.models import AliasEntry
from user.models import User


class APITest(AironeViewTest):
    def setUp(self):
        super(APITest, self).setUp()
        self.user: User = self.guest_login()

        # initialize Mdoel and Item for test
        self.model = self.create_entity(self.user, "TestModel")
        self.item = self.add_entry(self.user, "Item", self.model)

    def test_entry_alias_list(self):
        # initialize Aliases to be listed
        [self.item.add_alias(x) for x in ["foo", "bar", "baz"]]

        item2 = self.add_entry(self.user, "Item2", self.model)
        item2.add_alias("hoge")

        # create another Model, Item and Aliases to test to get only Aliases
        # that are associated with specified Item in the URL parameter.
        another_model = self.create_entity(self.user, "AnotherModel")
        another_item = self.add_entry(self.user, "Item", another_model)
        another_item.add_alias("hoge")

        # send request to list aliases
        resp = self.client.get("/entity/api/v2/%d/entries/?is_active=true" % self.model.id)
        self.assertEqual(resp.status_code, 200)

        # check this returned only Aliases that are associated with self.item
        self.assertEqual(resp.json()["count"], 2)
        self.assertEqual(
            [x["name"] for x in resp.json()["results"][0]["aliases"]], ["foo", "bar", "baz"]
        )
        self.assertEqual([x["name"] for x in resp.json()["results"][1]["aliases"]], ["hoge"])

    def test_list(self):
        # initialize Aliases to be listed
        [self.item.add_alias(x) for x in ["foo", "bar", "baz"]]

        # create another Model, Item and Aliases to test to get only Aliases
        # that are associated with specified Item in the URL parameter.
        another_model = self.create_entity(self.user, "AnotherModel")
        another_item = self.add_entry(self.user, "Item", another_model)
        another_item.add_alias("hoge")

        # send request to list aliases
        resp = self.client.get("/entry/api/v2/%d/alias/" % self.item.id)
        self.assertEqual(resp.status_code, 200)

        # check this returned only Aliases that are associated with self.item
        self.assertEqual(resp.json()["count"], 3)
        self.assertEqual([x["name"] for x in resp.json()["results"]], ["foo", "bar", "baz"])
        self.assertTrue(all([x["entry"] == self.item.id for x in resp.json()["results"]]))

    def test_create(self):
        resp = self.client.post(
            "/entry/api/v2/alias/",
            json.dumps(
                {
                    "name": "NewAlias",
                    "entry": self.item.id,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["name"], "NewAlias")
        self.assertEqual(resp.json()["entry"], self.item.id)

        # check expected Alias was created correctly
        self.assertEqual(AliasEntry.objects.filter(entry=self.item).count(), 1)

    def test_create_with_invalid_parameter(self):
        resp = self.client.post(
            "/entry/api/v2/alias/",
            json.dumps(
                {
                    "name": "NewAlias",
                    # This lucks mandatory parameter "entry"
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"entry":[{"message":"This field is required.","code":"AE-113000"}]})

    def test_create_with_duplicated_name(self):
        # create Alias that is duplicated with creation
        alias = self.item.add_alias("hoge")

        resp = self.client.post(
            "/entry/api/v2/alias/",
            json.dumps(
                {
                    "name": "hoge", # same name with other that has already been registered
                    "entry": self.item.id,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {"non_field_errors":[{"message":"A duplicated named Alias exists in this model","code":"AE-220000"}]})

    def test_delete(self):
        # create Alias to be deleted
        alias = self.item.add_alias("Deleting Alias")

        # send request to list aliases
        resp = self.client.delete("/entry/api/v2/alias/%s" % alias.id, None, "application/json")
        self.assertEqual(resp.status_code, 204)

        # check specified Alias was deleted actually
        self.assertFalse(AliasEntry.objects.filter(entry=self.item).exists())

    def test_create_bulk(self):
        model = self.create_entity(self.user, "Department")
        item = self.add_entry(self.user, "Dev", model)

        resp = self.client.post(
            "/entry/api/v2/alias/bulk/", json.dumps([
                {"name": "HOGE", "entry": item.id},
                {"name": "FUGA", "entry": item.id},
                {"name": "PUYO", "entry": item.id},
            ]), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        # check requested Aliases are created correctly
        self.assertEqual(
            sorted([x.name for x in AliasEntry.objects.filter(entry=item)]),
            sorted(["HOGE", "FUGA", "PUYO"])
        )

    def test_create_bulk_with_duplicated_name(self):
        model = self.create_entity(self.user, "Department")
        item = self.add_entry(self.user, "Dev", model)

        resp = self.client.post(
            "/entry/api/v2/alias/bulk/", json.dumps([
                {"name": "HOGE", "entry": item.id},
                {"name": "FUGA", "entry": item.id},
                {"name": "HOGE", "entry": item.id}, # This is duplicated!!
                {"name": "FUGA", "entry": item.id}, # This is duplicated!!
                {"name": "HOGE", "entry": item.id}, # This is duplicated!!
            ]), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), [{"message":"Duplicated names(['HOGE', 'FUGA']) were specified","code":"AE-220000"}])

        # check specified Aliases were not creaed
        self.assertFalse(AliasEntry.objects.filter(entry=item).exists())

    def test_create_bulk_with_duplicated_alias(self):
        model = self.create_entity(self.user, "Department")
        item = self.add_entry(self.user, "Dev", model)
        item.add_alias("PUYO")

        resp = self.client.post(
            "/entry/api/v2/alias/bulk/", json.dumps([
                {"name": "HOGE", "entry": item.id},
                {"name": "FUGA", "entry": item.id},
                {"name": "PUYO", "entry": item.id}, # PUYO has already been registered!!
            ]), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), [{},{},{"non_field_errors":[{"message":"A duplicated named Alias exists in this model","code":"AE-220000"}]}])

        # required aliases were not created
        self.assertEqual(
            sorted([x.name for x in AliasEntry.objects.filter(entry=item)]),
            sorted(["PUYO"])
        )
