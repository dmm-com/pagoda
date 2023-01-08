import json

from acl.models import ACLBase
from airone.lib.acl import ACLType
from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue
from role.models import Role


class ACLAPITest(AironeViewTest):
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
                    "current_permission": 0,
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

        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps(
                {
                    "name": acl.name,
                    "is_public": False,
                    "default_permission": str(ACLType.Nothing.id),
                    "objtype": acl.objtype,
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
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(role.is_permitted(acl, ACLType.Full))

    def test_update_by_others(self):
        user = self.guest_login()
        role = Role.objects.create(name="role")

        acl = ACLBase.objects.create(name="test", created_user=user)

        # send request to update ACL of Role that is not permitted to be edited
        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps(
                {
                    "name": acl.name,
                    "is_public": False,
                    "default_permission": str(ACLType.Nothing.id),
                    "objtype": acl.objtype,
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
                    "name": acl.name,
                    "is_public": False,
                    "default_permission": str(ACLType.Nothing.id),
                    "objtype": acl.objtype,
                    "acl": [
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
                "message": "Inadmissible setting.By this change you will never change this ACL",
            },
        )

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
                    "name": acl.name,
                    "is_public": False,
                    "default_permission": str(ACLType.Nothing.id),
                    "objtype": acl.objtype,
                    "acl": [
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

        # This tries to set ACL of object that user doesn't have permission (even through to read)
        acl = ACLBase.objects.create(name="test", created_user=user, is_public=False)
        resp = self.client.put(
            "/acl/api/v2/acls/%s" % acl.id,
            json.dumps(
                {
                    "name": acl.name,
                    "is_public": True,
                    "default_permission": str(ACLType.Nothing.id),
                    "objtype": acl.objtype,
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
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )
        self.assertFalse(role.is_permitted(acl, ACLType.Full))
