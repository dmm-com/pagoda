import json

import yaml
from django.urls import reverse

from airone.lib.test import AironeViewTest
from group.models import Group
from user.models import User


class ViewTest(AironeViewTest):
    def test_index_without_login(self):
        resp = self.client.get(reverse("group:index"))
        self.assertEqual(resp.status_code, 303)

    def test_index(self):
        self.admin_login()

        resp = self.client.get(reverse("group:index"))
        self.assertEqual(resp.status_code, 200)

    def test_index_with_objects(self):
        self.admin_login()

        user = self._create_user("fuga")
        group = self._create_group("hoge")

        user.groups.add(group)

        resp = self.client.get(reverse("group:index"))
        self.assertEqual(resp.status_code, 200)

    def test_index_with_inactive_user(self):
        self.admin_login()

        group = self._create_group("hoge")
        user1 = self._create_user("user1")
        user1.groups.add(group)
        user1.save()

        user2 = self._create_user("user2")
        user2.groups.add(group)
        user2.delete()
        user2.save()

        resp = self.client.get(reverse("group:index"))
        self.assertEqual(resp.status_code, 200)

    def test_create_get(self):
        self.admin_login()

        resp = self.client.get(reverse("group:create"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["groups"]), 1)
        self.assertEqual(resp.context["groups"][0]["id"], 0)
        self.assertEqual(resp.context["groups"][0]["name"], "-- ALL --")
        self.assertEqual(
            list(resp.context["groups"][0]["members"]),
            list(User.objects.filter(is_active=True)),
        )

    def test_create_post_without_login(self):
        resp = self.client.post(reverse("group:do_create"), json.dumps({}), "application/json")
        self.assertEqual(resp.status_code, 401)

    def test_create_post(self):
        self.admin_login()

        group_count = self._get_group_count()

        user1 = self._create_user("hoge")
        user2 = self._create_user("fuga")

        params = {
            "name": "test-group",
            "users": [user1.id, user2.id],
        }
        resp = self.client.post(reverse("group:do_create"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            self._get_group_count(),
            group_count + 1,
            "group should be created after post",
        )
        created_group = Group.objects.last()
        self.assertEqual(
            created_group.name,
            "test-group",
            "name of created group should be 'test-group'",
        )
        self.assertIsNone(created_group.parent_group)
        self.assertTrue(user1.groups.filter(pk=created_group.id).exists())
        self.assertTrue(user2.groups.filter(pk=created_group.id).exists())

    def test_create_post_without_users(self):
        self.admin_login()

        params = {
            "name": "test-group",
            "users": [],
        }
        resp = self.client.post(reverse("group:do_create"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)

        created_group = Group.objects.last()
        self.assertEqual(
            created_group.name,
            "test-group",
            "name of created group should be 'test-group'",
        )
        self.assertIsNone(created_group.parent_group)

    def test_create_post_with_parent_group_param(self):
        self.admin_login()

        parent_group = self._create_group("parent_group")
        params = {
            "name": "test-group",
            "users": [self._create_user("hoge").id],
            "parent_group": str(parent_group.id),
        }
        resp = self.client.post(reverse("group:do_create"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)

        created_group = Group.objects.last()
        self.assertEqual(created_group.name, "test-group")
        self.assertEqual(created_group.parent_group, parent_group)

    def test_create_without_users(self):
        self.admin_login()

        group_count = self._get_group_count()
        params = {
            "name": "test-group",
            "users": [],
        }
        resp = self.client.post(reverse("group:do_create"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._get_group_count(), group_count + 1)

        created_group = Group.objects.last()
        self.assertEqual(created_group.name, "test-group")
        self.assertFalse(User.objects.filter(groups__name="test-group").exists())

    def test_create_port_with_invalid_params(self):
        self.admin_login()

        group_count = self._get_group_count()

        params = {
            "name": "test-group",
            "users": [1999, 2999],
        }
        resp = self.client.post(reverse("group:do_create"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self._get_group_count(), group_count, "group should not be created")

    def test_create_duplicate_name_of_group(self):
        self.admin_login()

        duplicated_name = "hoge"

        # create group in advance
        group = self._create_group(name=duplicated_name)
        user1 = self._create_user("hoge")
        user1.groups.add(group)

        group_count = self._get_group_count()

        # try to create group with same name
        params = {
            "name": duplicated_name,
            "users": [user1.id],
        }
        resp = self.client.post(reverse("group:do_create"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self._get_group_count(), group_count, "group should not be created")

    def test_delete_group(self):
        self.admin_login()

        group1 = self._create_group("group1")
        group2 = self._create_group("group2")

        group_count = self._get_group_count()

        user1 = self._create_user("user1")
        user1.groups.add(group1)
        user1.groups.add(group2)

        user2 = self._create_user("user2")
        user2.groups.add(group1)

        resp = self.client.post(
            reverse("group:do_delete", args=[group1.id]),
            json.dumps({}),
            "application/json",
        )

        user1 = User.objects.get(username="user1")
        user2 = User.objects.get(username="user2")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            self._get_group_count(),
            group_count,
            "group should not be decreased because of soft-delete",
        )
        self.assertEqual(Group.objects.filter(name="group1").count(), 0, "group1 should not exist")
        self.assertEqual(Group.objects.filter(name="group2").count(), 1, "group2 should exist")
        self.assertEqual(user1.groups.count(), 1, "user1 should have 1 group")
        self.assertEqual(user2.groups.count(), 0, "user2 should have 0 group")

    def test_export(self):
        self.admin_login()

        group1 = self._create_group("group1")
        group2 = self._create_group("group2")

        user1 = self._create_user("user1")
        user1.groups.add(group1)
        user1.groups.add(group2)

        user2 = self._create_user("user2")
        user2.groups.add(group1)

        resp = self.client.get(reverse("group:export"))
        self.assertEqual(resp.status_code, 200)

        obj = yaml.load(resp.content, Loader=yaml.SafeLoader)
        self.assertTrue(isinstance(obj, dict))

        self.assertEqual(len(obj["User"]), 3)
        self.assertEqual(len(obj["Group"]), 2)

    def test_export_deleted_group(self):
        self.admin_login()

        groups = []
        users = []

        # create 3 group and 3 user
        for i in range(3):
            groups.append(self._create_group("group%d" % (i + 1)))
            users.append(self._create_user("user%d" % (i + 1)))

        # delete 1 group
        groups[-1].delete()
        groups[-1].save()

        # delete 1 user
        users[-1].delete()
        users[-1].save()

        resp = self.client.get(reverse("group:export"))
        self.assertEqual(resp.status_code, 200)

        obj = yaml.load(resp.content, Loader=yaml.SafeLoader)

        self.assertEqual(len(obj["User"]), self._get_active_user_count())
        self.assertEqual(len(obj["Group"]), 2)

    def test_create_group_by_guest_user(self):
        user = self.guest_login()

        params = {
            "name": "test-group",
            "users": [user.id],
        }
        resp = self.client.post(reverse("group:do_create"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Group.objects.filter(name="test-group").count(), 0)

    def test_delete_group_by_guest_user(self):
        user = self.guest_login()
        group = self._create_group("test-group")

        user.groups.add(group)

        resp = self.client.post(
            reverse("group:do_delete", args=[group.id]),
            json.dumps({}),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Group.objects.filter(name="test-group").count(), 1)
        self.assertTrue(user.groups.filter(name="test-group").count(), 1)

    def test_get_edit_page(self):
        self.admin_login()

        group = self._create_group("testg")

        resp = self.client.get(reverse("group:edit", args=[group.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_edit_page_by_guest(self):
        self.guest_login()

        group = self._create_group("testg")

        resp = self.client.get(reverse("group:edit", args=[group.id]))
        self.assertEqual(resp.status_code, 400)

    def test_post_edit(self):
        user = self.admin_login()

        # initialize group and user
        group = self._create_group("testg")
        user1 = self._create_user("user1")
        user1.groups.add(group)

        params = {
            "name": "testg-update",
            "users": [user.id],
        }
        resp = self.client.post(
            reverse("group:do_edit", args=[group.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # get updated group object from database
        group.refresh_from_db()
        self.assertEqual(group.name, "testg-update")
        self.assertIsNone(group.parent_group)

        # checks being have added/deleted group from user and user1 information
        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user1.groups.count(), 0)
        self.assertTrue(user.groups.filter(id=group.id).exists())
        self.assertFalse(user1.groups.filter(id=group.id).exists())

    def test_post_edit_without_users(self):
        user = self.admin_login()

        # initialize group and user
        group = self._create_group("testg")
        user.groups.add(group)

        params = {
            "name": "testg-update",
            "users": [],
        }
        resp = self.client.post(
            reverse("group:do_edit", args=[group.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # get updated group object from database
        group.refresh_from_db()
        self.assertEqual(group.name, "testg-update")
        self.assertIsNone(group.parent_group)
        self.assertFalse(user.groups.filter(pk=group.id).exists())

    def test_post_edit_with_parent_group_param(self):
        user = self.admin_login()

        # initialize group and user
        parent_group = self._create_group("parent_group")
        group = self._create_group("testg")
        params = {"name": "testg-update", "users": [user.id], "parent_group": str(parent_group.id)}
        resp = self.client.post(
            reverse("group:do_edit", args=[group.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # get updated group object from database
        group.refresh_from_db()
        self.assertEqual(group.name, "testg-update")
        self.assertEqual(group.parent_group, parent_group)

    def test_post_edit_to_duplicate_name(self):
        self.admin_login()

        # initialize group and user
        group1 = self._create_group("testg1")
        self._create_group("testg2")

        params = {
            "name": "testg2",  # This is same with group2, so it may cause an error.
            "users": [],
        }
        resp = self.client.post(
            reverse("group:do_edit", args=[group1.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)

        # checks group name is not changed
        self.assertEqual(Group.objects.get(id=group1.id).name, group1.name)

    def test_post_edit_with_invalid_group_id(self):
        self.admin_login()

        params = {
            "name": "testg",
            "users": [],
        }
        # send request with an invalid group-id
        resp = self.client.post(
            reverse("group:do_edit", args=[12345]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)

    def test_post_edit_by_guest(self):
        self.guest_login()

        # initialize group to update
        group = self._create_group("testg")
        params = {
            "name": "testg-update",
            "users": [],
        }
        resp = self.client.post(
            reverse("group:do_edit", args=[group.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)

    def test_import_user_and_group(self):
        self.admin_login()

        fp = self.open_fixture_file("import_user_and_group.yaml")
        resp = self.client.post(reverse("group:do_import_user_and_group"), {"file": fp})

        self.assertEqual(resp.status_code, 303)

        self.assertEqual(Group.objects.filter(name="Group1").count(), 1)
        self.assertEqual(Group.objects.filter(name="Group2").count(), 1)

        user1 = User.objects.filter(username="User1").first()

        self.assertEqual(user1.email, "user1@example.com")
        self.assertEqual(user1.groups.count(), 2)

    # utility functions
    def _create_user(self, name):
        return User.objects.create(username=name)

    def _create_group(self, name):
        return Group.objects.create(name=name)

    def _get_user_count(self):
        return User.objects.count()

    def _get_active_user_count(self):
        return User.objects.filter(is_active=True).count()

    def _get_group_count(self):
        return Group.objects.count()
