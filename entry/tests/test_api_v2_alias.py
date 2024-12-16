from airone.lib.test import AironeViewTest
from entity.models import Entity, EntityAttr
from entry.models import Attribute, AttributeValue, Entry, AliasEntry
from user.models import User


class APITest(AironeViewTest):
    def setUp(self):
        super(APITest, self).setUp()
        self.user: User = self.guest_login()

        # initialize Mdoel and Item for test
        self.model = self.create_entity(self.user, "TestModel")
        self.item = self.add_entry(self.user, "Item", self.model)

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
        self.assertTrue(all([x["entry"]["id"] == self.item.id for x in resp.json()["results"]]))

    def test_update(self):
        pass

    def test_delete(self):
        pass
