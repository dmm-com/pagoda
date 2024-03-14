import json

from mock import mock

from acl.models import ACLBase
from airone.lib.acl import ACLType
from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue
from entity import tasks
from entity.models import Entity, EntityAttr
from role.models import Role


class ViewTest(AironeViewTest):
    def initialization_for_retrieve_test(self):
        self.user = self.admin_login()
        self.role = Role.objects.create(name="role")
        self.role.users.add(self.user)
        self.role.description = "for Test"
        self.role.save()

    def test_retrieve(self):
        self.initialization_for_retrieve_test()

        acl = ACLBase.objects.create(name="test", created_user=self.user)

        resp = self.client.get("/acl/api/v2/acls/%s" % acl.id)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["id"], acl.id)
        self.assertEqual(body["name"], acl.name)
        self.assertEqual(
            body["roles"],
            [
                {
                    "id": self.role.id,
                    "name": self.role.name,
                    "description": self.role.description,
                    "current_permission": 1,
                }
            ],
        )

    def test_retrieve_for_EntityAttr(self):
        self.initialization_for_retrieve_test()

        # create Enttiy and EntityAttr for test
        entity = self.create_entity(
            self.user,
            "entity",
            attrs=[
                {
                    "name": "attr01",
                    "type": AttrTypeValue["string"],
                }
            ],
        )
        entity_attr = entity.attrs.first()

        # check response has expected parent parameter
        resp = self.client.get("/acl/api/v2/acls/%s" % entity_attr.id)
        body = resp.json()
        self.assertEqual(
            body.get("parent"),
            {
                "id": entity.id,
                "name": entity.name,
                "is_public": entity.is_public,
            },
        )

    def test_retrieve_for_Entry(self):
        self.initialization_for_retrieve_test()

        # create Enttiy and Entry for test
        entity = self.create_entity(self.user, "entity")
        entry = self.add_entry(self.user, "entry", entity)

        # check response has expected parent parameter
        resp = self.client.get("/acl/api/v2/acls/%s" % entry.id)
        body = resp.json()
        self.assertEqual(
            body.get("parent"),
            {
                "id": entity.id,
                "name": entity.name,
                "is_public": entity.is_public,
            },
        )

    def test_retrieve_for_Attribute(self):
        self.initialization_for_retrieve_test()

        # create Enttiy, EntityAttr, Entry and Attribute for test
        entity = self.create_entity(
            self.user,
            "entity",
            attrs=[
                {
                    "name": "attr01",
                    "type": AttrTypeValue["string"],
                }
            ],
        )
        entry = self.add_entry(self.user, "entry", entity)
        attr = entry.attrs.first()

        # check response has expected parent parameter
        resp = self.client.get("/acl/api/v2/acls/%s" % attr.id)
        body = resp.json()
        self.assertEqual(
            body.get("parent"),
            {
                "id": entry.id,
                "name": entry.name,
                "is_public": entry.is_public,
            },
        )

    def test_retrieve_by_others(self):
        user = self.admin_login()

        acl = ACLBase.objects.create(name="test", created_user=user, is_public=False)

        self.guest_login()
        resp = self.client.get("/acl/api/v2/acls/%s" % acl.id)
        self.assertEqual(resp.status_code, 403)

    def test_update(self):
        user = self.guest_login()
        role = Role.objects.create(name="role")
        role.users.add(user)
        role.admin_users.add(user)

        acl = ACLBase.objects.create(name="test", created_user=user)

        param = {
            "is_public": False,
            "default_permission": str(ACLType.Nothing.id),
            "acl_settings": [
                {
                    "member_id": str(role.id),
                    "value": str(ACLType.Full.id),
                },
            ],
        }
        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id, json.dumps(param), "application/json;charset=utf-8"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(acl.is_public, False)
        self.assertTrue(acl.default_permission, ACLType.Nothing)
        self.assertTrue(role.is_permitted(acl, ACLType.Full))

        param = {"is_public": True}
        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id, json.dumps(param), "application/json;charset=utf-8"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(acl.is_public, True)
        self.assertTrue(acl.default_permission, ACLType.Nothing)
        self.assertTrue(acl.full.roles.filter(id=role.id).exists())

        param = {"default_permission": ACLType.Full.id}
        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id, json.dumps(param), "application/json;charset=utf-8"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(acl.is_public, True)
        self.assertTrue(acl.default_permission, ACLType.Full)
        self.assertTrue(acl.full.roles.filter(id=role.id).exists())

        param = {
            "acl_settings": [
                {
                    "member_id": str(role.id),
                    "value": str(ACLType.Nothing.id),
                },
            ],
        }
        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id, json.dumps(param), "application/json;charset=utf-8"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(acl.is_public, True)
        self.assertTrue(acl.default_permission, ACLType.Full)
        self.assertFalse(acl.full.roles.filter(id=role.id).exists())

    def test_update_by_others(self):
        user = self.guest_login()
        role = Role.objects.create(name="role")

        acl = ACLBase.objects.create(name="test", created_user=user)

        # send request to update ACL of Role that is not permitted to be edited
        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps(
                {
                    "is_public": False,
                    "default_permission": str(ACLType.Nothing.id),
                    "acl": [
                        {
                            "member_id": str(role.id),
                            "value": str(ACLType.Writable.id),
                        },
                    ],
                }
            ),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 403)

    def test_update_acl_to_nobody_control(self):
        user = self.guest_login()
        role = Role.objects.create(name="role")
        role.admin_users.add(user)

        acl = ACLBase.objects.create(name="test", created_user=user)
        # set role to full permission object
        acl.full.roles.add(role)

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps(
                {
                    "is_public": False,
                    "default_permission": str(ACLType.Nothing.id),
                    "acl_settings": [
                        {
                            "member_id": str(role.id),
                            "value": str(ACLType.Nothing.id),
                        },
                    ],
                }
            ),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "Inadmissible setting. By this change you will never change this ACL",
            },
        )

        resp = self.client.put("/acl/api/v2/acls/%s" % acl.id, {}, "application/json;charset=utf-8")
        self.assertEqual(resp.status_code, 200)

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps({"is_public": False}),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 200)
        acl.refresh_from_db()
        self.assertEqual(acl.is_public, False)

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps({"is_public": True}),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 200)
        acl.refresh_from_db()
        self.assertEqual(acl.is_public, True)

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps({"default_permission": str(ACLType.Nothing.id)}),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 200)
        acl.refresh_from_db()
        self.assertEqual(acl.default_permission, ACLType.Nothing)

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps({"default_permission": str(ACLType.Full.id)}),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 200)
        acl.refresh_from_db()
        self.assertEqual(acl.default_permission, ACLType.Full)

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps(
                {
                    "acl_settings": [
                        {
                            "member_id": str(role.id),
                            "value": str(ACLType.Nothing.id),
                        }
                    ]
                }
            ),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(acl.full.roles.filter(id=role.id).exists(), False)

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps(
                {
                    "acl_settings": [
                        {
                            "member_id": str(role.id),
                            "value": str(ACLType.Full.id),
                        }
                    ]
                }
            ),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(acl.full.roles.filter(id=role.id).exists(), True)

        acl.default_permission = ACLType.Nothing.id
        acl.save()
        acl.full.roles.remove(role)

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps({"is_public": False}),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 403)

        acl.is_public = False
        acl.default_permission = ACLType.Full.id
        acl.save()

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps({"default_permission": str(ACLType.Nothing.id)}),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 403)

        acl.default_permission = ACLType.Nothing.id
        acl.save()
        acl.full.roles.add(role)

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps(
                {
                    "acl_settings": [
                        {
                            "member_id": str(role.id),
                            "value": str(ACLType.Nothing.id),
                        }
                    ]
                }
            ),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 403)

        role2 = Role.objects.create(name="role2")

        acl.is_public = True
        acl.save()
        acl.full.roles.remove(role)
        acl.full.roles.add(role2)

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps(
                {
                    "is_public": False,
                    "acl_settings": [
                        {
                            "member_id": str(role.id),
                            "value": str(ACLType.Full.id),
                        }
                    ],
                }
            ),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 200)

    def test_remove_acl_when_administrative_role_is_left(self):
        user = self.guest_login()
        acl = ACLBase.objects.create(name="test", created_user=user)

        roles = [Role.objects.create(name="role-%d" % i) for i in range(2)]
        for role in roles:
            role.admin_users.add(user)
            acl.full.roles.add(role)

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps(
                {
                    "is_public": False,
                    "default_permission": str(ACLType.Nothing.id),
                    "acl_settings": [
                        {
                            "member_id": str(roles[0].id),
                            "value": str(ACLType.Nothing.id),
                        },
                    ],
                }
            ),
            "application/json;charset=utf-8",
        )
        self.assertEqual(resp.status_code, 200)

    def test_update_acl_without_permission(self):
        user = self.guest_login()
        role = Role.objects.create(name="role")
        role.users.add(user)
        role.admin_users.add(user)

        def _put_acl():
            return self.client.put(
                "/acl/api/v2/acls/%s" % acl.id,
                json.dumps(
                    {
                        "is_public": True,
                        "default_permission": str(ACLType.Full.id),
                        "acl": [
                            {
                                "member_id": str(role.id),
                                "value": str(ACLType.Full.id),
                            },
                        ],
                    }
                ),
                "application/json;charset=utf-8",
            )

        # This tries to set ACL of object that user doesn't have permission (even through to read)
        acl = ACLBase.objects.create(name="test", created_user=user, is_public=False)
        resp = _put_acl()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )
        self.assertFalse(role.is_permitted(acl, ACLType.Full))

        acl.readable.roles.add(role)
        resp = _put_acl()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )
        self.assertFalse(role.is_permitted(acl, ACLType.Full))

        acl.writable.roles.add(role)
        resp = _put_acl()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )
        self.assertFalse(role.is_permitted(acl, ACLType.Full))

        acl.full.roles.add(role)
        resp = _put_acl()
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(role.is_permitted(acl, ACLType.Full))

    @mock.patch(
        "entity.tasks.create_entity_v2.delay", mock.Mock(side_effect=tasks.create_entity_v2)
    )
    def test_list_history(self):
        self.initialization_for_retrieve_test()
        self.client.post("/entity/api/v2/", json.dumps({"name": "test"}), "application/json")

        entity = Entity.objects.get(name="test", is_active=True)
        history = entity.history.first()

        resp = self.client.get("/acl/api/v2/acls/%s/history" % entity.id)
        self.assertEqual(resp.status_code, 200)

        # initial values should be recorded
        self.assertEqual(
            resp.json(),
            [
                {
                    "name": "test",
                    "user": {"id": self.user.id, "username": "admin"},
                    "time": history.history_date.astimezone(self.TZ_INFO).isoformat(),
                    "changes": [
                        {"action": "create", "target": "is_public", "before": None, "after": True},
                        {
                            "action": "create",
                            "target": "default_permission",
                            "before": None,
                            "after": ACLType.Nothing.id,
                        },
                    ],
                }
            ],
        )

        # some changes
        entity.is_public = False
        entity.default_permission = ACLType.Readable.id
        entity.save()

        resp = self.client.get("/acl/api/v2/acls/%s/history" % entity.id)
        self.assertEqual(resp.status_code, 200)

        # 2 changed values should be recorded
        self.assertEqual(len(resp.json()), 2)
        self.assertIn(
            {
                "action": "update",
                "target": "is_public",
                "before": True,
                "after": False,
            },
            resp.json()[0]["changes"],
        )
        self.assertIn(
            {
                "action": "update",
                "target": "default_permission",
                "before": ACLType.Nothing.id,
                "after": ACLType.Readable.id,
            },
            resp.json()[0]["changes"],
        )

    def test_list_history_with_role(self):
        self.initialization_for_retrieve_test()
        entity = Entity.objects.create(name="test", created_user=self.user)

        param = {
            "acl_settings": [
                {
                    "member_id": str(self.role.id),
                    "value": str(ACLType.Writable.id),
                },
            ],
        }
        self.client.put("/acl/api/v2/acls/%d" % entity.id, json.dumps(param), "application/json")
        history = entity.writable.history.first()

        resp = self.client.get("/acl/api/v2/acls/%s/history" % entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)
        self.assertEqual(
            resp.json()[0],
            {
                "name": "test",
                "user": {"id": self.user.id, "username": "admin"},
                "time": history.history_date.astimezone(self.TZ_INFO).isoformat(),
                "changes": [
                    {
                        "action": "create",
                        "target": "role",
                        "before": ACLType.Nothing.id,
                        "after": ACLType.Writable.id,
                    }
                ],
            },
        )

        param = {
            "acl_settings": [
                {
                    "member_id": str(self.role.id),
                    "value": str(ACLType.Readable.id),
                },
            ],
        }
        self.client.put("/acl/api/v2/acls/%d" % entity.id, json.dumps(param), "application/json")

        resp = self.client.get("/acl/api/v2/acls/%s/history" % entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 3)
        self.assertEqual(
            resp.json()[0]["changes"],
            [
                {
                    "action": "update",
                    "target": "role",
                    "before": ACLType.Writable.id,
                    "after": ACLType.Readable.id,
                }
            ],
        )

    @mock.patch(
        "entity.tasks.create_entity_v2.delay", mock.Mock(side_effect=tasks.create_entity_v2)
    )
    def test_list_history_with_entity_attr(self):
        self.initialization_for_retrieve_test()

        param = {
            "name": "test",
            "attrs": [
                {
                    "name": "string",
                    "type": AttrTypeValue["string"],
                }
            ],
        }

        self.client.post("/entity/api/v2/", json.dumps(param), "application/json")

        entity = Entity.objects.get(name="test", is_active=True)
        entity_attr: EntityAttr = entity.attrs.get(name="string", is_active=True)
        entity_attr.writable.roles.add(self.role)

        resp = self.client.get("/acl/api/v2/acls/%s/history" % entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 3)
        self.assertEqual([h["name"] for h in resp.json()], ["string", "string", "test"])
        self.assertEqual(
            resp.json()[0]["changes"],
            [
                {
                    "action": "create",
                    "target": "role",
                    "before": ACLType.Nothing.id,
                    "after": ACLType.Writable.id,
                }
            ],
        )
        self.assertEqual(
            resp.json()[1]["changes"],
            [
                {
                    "action": "create",
                    "target": "is_public",
                    "before": None,
                    "after": True,
                },
                {
                    "action": "create",
                    "target": "default_permission",
                    "before": None,
                    "after": ACLType.Nothing.id,
                },
            ],
        )
