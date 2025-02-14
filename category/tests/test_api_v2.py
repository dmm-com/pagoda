import json
from typing import List

from airone.lib.acl import ACLType
from airone.lib.test import AironeViewTest
from category.models import Category
from entity.models import Entity
from user.models import User


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        self.user: User = self.guest_login()

    def test_list(self):
        # initialize Model and Categories for testing API processing
        model: Entity = self.create_entity(self.user, "Model")
        categories: List[Category] = [
            self.create_category(self.user, "Category-%d" % n, "Note-%d" % n, [model])
            for n in range(3)
        ]

        # get all Categories
        resp = self.client.get("/category/api/v2/")
        self.assertEqual(resp.status_code, 200)

        # check returned data has expected values
        self.assertEqual(resp.json()["count"], 3)
        self.assertEqual(
            resp.json()["results"],
            [
                {
                    "id": x.id,
                    "name": x.name,
                    "note": x.note,
                    "models": [{"id": model.id, "name": model.name, "is_public": True}],
                    "priority": x.priority,
                }
                for x in categories
            ],
        )

    def test_list_unauthorized_categories(self):
        # initialize Model and Categories for testing API processing
        model: Entity = self.create_entity(self.user, "Model")
        categories: List[Category] = [
            self.create_category(self.user, "Category-%d" % n, "Note-%d" % n, [model])
            for n in range(3)
        ]

        # set categories[0] unreadable
        categories[0].is_public = False
        categories[0].save()
        self.assertFalse(self.user.has_permission(categories[0], ACLType.Readable))

        # get all Categories which are authorized to user
        resp = self.client.get("/category/api/v2/")
        self.assertEqual(resp.status_code, 200)

        # check returned data has expected values
        self.assertEqual(resp.json()["count"], 2)
        self.assertEqual(
            [x["id"] for x in resp.json()["results"]],
            [categories[i].id for i in [1, 2]],
        )

    def test_get(self):
        # initialize Models and Categories for testing API processing
        models: List[Entity] = [self.create_entity(self.user, "Model-%d" % n) for n in range(3)]
        category: Category = self.create_category(self.user, "Category", "note", models)

        # get specified Category
        resp = self.client.get("/category/api/v2/%d/" % category.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {
                "id": category.id,
                "name": category.name,
                "note": category.note,
                "models": [{"id": x.id, "name": x.name, "is_public": True} for x in models],
                "priority": category.priority,
            },
        )

    def test_get_include_deleted_model(self):
        pass

    def test_create(self):
        # initialize Models for testing API processing
        models: List[Entity] = [self.create_entity(self.user, "Model-%d" % n) for n in range(3)]

        # send request to create a Category
        params = {
            "name": "New Category",
            "note": "Hoge",
            "models": [{"id": x.id, "name": x.name} for x in models],
            "priority": 100,
        }
        resp = self.client.post("/category/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 201)

        # check Category item is created and has expected attribute values
        category = Category.objects.last()
        self.assertEqual(category.id, resp.json()["id"])
        self.assertEqual(category.name, resp.json()["name"])
        self.assertEqual(category.note, resp.json()["note"])
        self.assertEqual(category.priority, resp.json()["priority"])
        self.assertEqual(category.models.count(), 3)
        self.assertEqual(list(category.models.all()), models)

    def test_delete(self):
        # create Category instance that will be deleted in this test
        category: Category = self.create_category(self.user, "Category", "note")

        # send request to delete target Category
        resp = self.client.delete("/category/api/v2/%d/" % category.id)
        self.assertEqual(resp.status_code, 204)

        # check target category instance is existed but inactivated
        self.assertTrue(Category.objects.filter(id=category.id).exists())
        self.assertFalse(Category.objects.filter(id=category.id, is_active=True).exists())

    def test_delete_unauthorized_category(self):
        # initialize Models and Categories for testing API processing
        category: Category = self.create_category(self.user, "Category", "note")

        # set category unauthorized to update from current user
        category.is_public = False
        category.save()
        self.assertFalse(self.user.has_permission(category, ACLType.Full))

        # send request to delete target Category, then failed to do it.
        resp = self.client.delete("/category/api/v2/%d/" % category.id)
        self.assertEqual(resp.status_code, 404)

        # check Category item, which was specified in deleting reqeust
        self.assertTrue(category.is_active)

    def test_update(self):
        """
        Initially, there are 3 models (M0, M1, M2) and Category has M0 and M1
        Then, this test sends a request to change its beloning category to M1 and M2.
        """
        models: List[Entity] = [self.create_entity(self.user, "M%d" % n) for n in range(3)]
        category: Category = self.create_category(
            self.user, "Category", "note", [models[0], models[1]]
        )
        self.assertEqual(list(category.models.all()), [models[0], models[1]])

        params = {
            "name": "Updated Category",
            "note": "Updated Note",
            "models": [{"id": models[i].id, "name": models[i].name} for i in [1, 2]],
            "priority": 100,
        }
        resp = self.client.put(
            "/category/api/v2/%s/" % category.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        # check all data is updated expectedly
        self.assertEqual(list(category.models.all()), [models[1], models[2]])

    def test_update_unauthorized_category(self):
        # initialize Models and Categories for testing API processing
        category: Category = self.create_category(self.user, "Category", "note")

        # set category unauthorized to update from current user
        category.is_public = False
        category.save()
        self.assertFalse(self.user.has_permission(category, ACLType.Full))

        # send request to update target Category, then failed to do it.
        params = {
            "name": "Updated Category",
            "note": "Updated Note",
            "models": [],
            "priority": 100,
        }
        resp = self.client.put(
            "/category/api/v2/%s/" % category.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 404)

        # check Category item, which was specified in deleting reqeust
        self.assertEqual(category.name, "Category")
        self.assertEqual(category.note, "note")
