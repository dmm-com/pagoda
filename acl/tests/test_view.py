import json

from django.urls import reverse

from acl.models import ACLBase
from airone.lib.acl import ACLType
from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue
from entity.models import Entity, EntityAttr
from entry.models import Attribute, Entry
from role.models import Role
from user.models import User


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        # create test Role instance which is used in this test
        self._role = Role.objects.create(name="TestRole", description="Hoge")

    # override 'admin_login' method to create initial ACLBase objects
    def admin_login(self):
        user = super(ViewTest, self).admin_login()

        self._aclobj = ACLBase(name="test", created_user=user)
        self._aclobj.save()

        return user

    def send_set_request(self, aclobj, role, aclid=ACLType.Writable.id):
        params = {
            "object_id": str(aclobj.id),
            "object_type": str(aclobj.objtype),
            "acl": [
                {"role_id": str(role.id), "value": str(aclid)},
            ],
            "default_permission": str(ACLType.Nothing.id),
        }
        return self.client.post(reverse("acl:set"), json.dumps(params), "application/json")

    def test_index_without_login(self):
        resp = self.client.get(reverse("acl:index", args=[0]))
        self.assertEqual(resp.status_code, 303)

    def test_index_by_admin(self):
        self.admin_login()

        # create Roles to be listed
        for name in ["r1", "r2"]:
            Role.objects.create(name=name)

        resp = self.client.get(reverse("acl:index", args=[self._aclobj.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted([x["name"] for x in resp.context["roles"]]), sorted(["TestRole", "r1", "r2"])
        )

    def test_index_by_guest(self):
        """This checks Roles, which only login-user belongs to, will be shown on the Role list."""
        user = self.guest_login()
        self._role.users.add(user)

        # create Roles, but these are not shown at the list because user doesn't belong to them.
        for name in ["r1", "r2"]:
            Role.objects.create(name=name)

        aclobj = ACLBase.objects.create(name="ACLObj", created_user=user)
        resp = self.client.get(reverse("acl:index", args=[aclobj.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(sorted([x["name"] for x in resp.context["roles"]]), sorted(["TestRole"]))

    def test_get_acl_set(self):
        self.admin_login()

        resp = self.client.get(reverse("acl:set"))
        self.assertEqual(resp.status_code, 400)

    def test_post_acl_set_without_login(self):
        user = User(username="hoge")
        user.save()

        aclobj = ACLBase(name="hoge", created_user=user)

        params = {
            "object_id": str(aclobj.id),
            "object_type": str(aclobj.objtype),
            "acl": [
                {
                    "role_id": str(self._role.id),
                    "value": str(ACLType.Writable.id),
                },
            ],
            "default_permission": str(ACLType.Nothing.id),
        }
        resp = self.client.post(reverse("acl:set"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 401)

    def test_post_acl_set(self):
        self.admin_login()
        resp = self.send_set_request(self._aclobj, self._role)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._role.permissions.count(), 1)
        self.assertEqual(self._role.permissions.last(), self._aclobj.writable)
        self.assertFalse(ACLBase.objects.get(id=self._aclobj.id).is_public)

    def test_post_acl_set_attrbase(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        attrbase = EntityAttr.objects.create(
            name="hoge", type=AttrTypeValue["object"], created_user=user, parent_entity=entity
        )
        resp = self.send_set_request(attrbase, self._role)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["redirect_url"], "/entity/edit/%s" % entity.id)
        self.assertEqual(self._role.permissions.last(), attrbase.writable)
        self.assertFalse(EntityAttr.objects.get(id=attrbase.id).is_public)

    def test_post_acl_set_entity(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="hoge", created_user=user)
        resp = self.send_set_request(entity, self._role)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["redirect_url"], "/entity/")
        self.assertEqual(self._role.permissions.last(), entity.writable)
        self.assertFalse(Entity.objects.get(id=entity.id).is_public)

    def test_post_acl_set_attribute(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="hoge", created_user=user)
        entry = Entry.objects.create(name="hoge", created_user=user, schema=entity)
        attrbase = EntityAttr.objects.create(
            name="hoge", type=AttrTypeValue["object"], created_user=user, parent_entity=entity
        )
        entity.attrs.add(attrbase)
        attr = entry.add_attribute_from_base(attrbase, user)

        resp = self.send_set_request(attr, self._role)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["redirect_url"], "/entry/edit/%s" % entry.id)
        self.assertEqual(self._role.permissions.last(), attr.writable)
        self.assertFalse(Attribute.objects.get(id=attr.id).is_public)
        search_result = self._es.search(body={"query": {"term": {"name": entry.name}}})
        self.assertFalse(search_result["hits"]["hits"][0]["_source"]["attr"][0]["is_readable"])

    def test_post_acl_set_entry(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="hoge", created_user=user)
        entry = Entry.objects.create(name="fuga", created_user=user, schema=entity)
        resp = self.send_set_request(entry, self._role)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["redirect_url"], "/entry/show/%s" % entry.id)
        self.assertEqual(self._role.permissions.last(), entry.writable)
        self.assertFalse(Entry.objects.get(id=entry.id).is_public)
        search_result = self._es.search(body={"query": {"term": {"name": entry.name}}})
        self.assertFalse(search_result["hits"]["hits"][0]["_source"]["is_readable"])

    def test_post_acl_set_nothing(self):
        self.admin_login()
        params = {
            "object_id": str(self._aclobj.id),
            "object_type": str(self._aclobj.objtype),
            "is_public": "on",
            "acl": [
                {"role_id": str(self._role.id), "value": str(ACLType.Nothing.id)},
            ],
            "default_permission": str(ACLType.Nothing.id),
        }
        resp = self.client.post(reverse("acl:set"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._role.permissions.count(), 0)

    def test_update_acl(self):
        self.admin_login()

        # set ACL object in advance, there are two members in the full parameter
        self._aclobj.full.roles.add(self._role)

        params = {
            "object_id": str(self._aclobj.id),
            "object_type": str(self._aclobj.objtype),
            "acl": [{"role_id": str(self._role.id), "value": str(ACLType.Readable.id)}],
            "default_permission": str(ACLType.Nothing.id),
        }
        resp = self.client.post(reverse("acl:set"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._role.permissions.count(), 1)
        self.assertEqual(self._role.permissions.last(), self._aclobj.readable)
        self.assertFalse(ACLBase.objects.get(id=self._aclobj.id).is_public)

    def test_update_acl_to_nothing(self):
        self.admin_login()

        # set ACL object in advance, there are two members in the full parameter
        self._aclobj.full.roles.add(self._role)

        params = {
            "object_id": str(self._aclobj.id),
            "object_type": str(self._aclobj.objtype),
            "acl": [{"role_id": str(self._role.id), "value": str(ACLType.Nothing.id)}],
            "default_permission": str(ACLType.Nothing.id),
        }
        resp = self.client.post(reverse("acl:set"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._role.permissions.count(), 0)

    def test_post_acl_set_without_object_id(self):
        self.admin_login()
        params = {
            "acl": [
                {"role_id": str(self._role.id), "value": str(ACLType.Writable)},
            ]
        }
        resp = self.client.post(reverse("acl:set"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 400)

    def test_post_acl_set_without_acl_params(self):
        self.admin_login()
        params = {"object_id": str(self._aclobj.id)}
        resp = self.client.post(reverse("acl:set"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 400)

    def test_post_acl_set_with_invalid_role_id(self):
        self.admin_login()
        params = {
            "object_id": str(self._aclobj.id),
            "acl": [
                {"role_id": "999999", "value": str(ACLType.Writable)},
            ],
        }
        resp = self.client.post(reverse("acl:set"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 400)

    def test_post_acl_set_with_invalid_acl(self):
        self.admin_login()
        params = {
            "object_id": str(self._aclobj.id),
            "acl": [
                {"role_id": str(self._role.id), "value": "abcd"},
            ],
        }
        resp = self.client.post(reverse("acl:set"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 400)

    def test_check_entry_permission_by_setting_permission_of_entity(self):
        guest = User.objects.create(username="guest", is_superuser=False)
        user = self.admin_login()

        entity = Entity.objects.create(name="hoge", created_user=user)
        entry = Entry.objects.create(name="fuga", created_user=user, schema=entity)

        resp = self.send_set_request(entity, self._role, ACLType.Readable.id)

        # reflesh object with latest DB data
        entity.refresh_from_db()
        entry.refresh_from_db()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._role.permissions.count(), 1)
        self.assertEqual(self._role.permissions.last(), entity.readable)
        self.assertEqual(entity.default_permission, ACLType.Nothing)
        self.assertFalse(entity.is_public)

        # check that Role doesn't have permission to access Entry
        # that schema's acl is set
        self.assertTrue(entry.is_public)
        self.assertFalse(guest.has_permission(entry, ACLType.Readable))

    def test_check_attribute_permission_by_setting_permission_of_entityattr(self):
        guest = User.objects.create(username="guest", is_superuser=False)
        user = self.admin_login()

        entity = Entity.objects.create(name="hoge", created_user=user)
        attrbase = EntityAttr.objects.create(
            name="attr1", type=AttrTypeValue["object"], created_user=user, parent_entity=entity
        )

        entry = Entry.objects.create(name="fuga", created_user=user, schema=entity)
        attr = entry.add_attribute_from_base(attrbase, user)

        resp = self.send_set_request(attrbase, self._role, ACLType.Full.id)

        # reflesh object with latest DB data
        attrbase.refresh_from_db()
        attr.refresh_from_db()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._role.permissions.count(), 1)
        self.assertEqual(self._role.permissions.last(), attrbase.full)
        self.assertFalse(attrbase.is_public)
        self.assertEqual(attrbase.default_permission, ACLType.Nothing)

        # check that Role doesn't have permission to access Entry
        # that schema's acl is set
        self.assertTrue(attr.is_public)
        self.assertFalse(guest.has_permission(attr, ACLType.Full))

    def test_access_to_no_permission_object(self):
        user = self.guest_login()
        obj = ACLBase.objects.create(name="obj", created_user=user, is_public=False)

        # When normal user access to the ACL setting page of object which user doens't
        # have ACLType.Full, AirOne returns http-staus 400.
        resp = self.client.get(reverse("acl:index", args=[obj.id]))
        self.assertEqual(resp.status_code, 400)

        # While user has no permission of object, admin user can access to it.
        self.admin_login()
        resp = self.client.get(reverse("acl:index", args=[obj.id]))
        self.assertEqual(resp.status_code, 200)

    def test_clear_permission(self):
        user = self.guest_login()
        aclobj = ACLBase.objects.create(name="obj", created_user=user)

        params = {
            "object_id": str(aclobj.id),
            "object_type": str(aclobj.objtype),
            "is_public": "",
            "acl": [],
            "default_permission": str(ACLType.Nothing.id),
        }
        resp = self.client.post(reverse("acl:set"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.content.decode("utf-8"),
            "Inadmissible setting. By this change you will never change this ACL",
        )

    def test_clear_permission_when_there_is_available_role(self):
        """This test remove last role permission. It is expected that processing
        won't be accepted to prevent making object no-one can control.
        """
        user = self.guest_login()
        self._role.admin_users.add(user)

        # make another role to remove permission
        another_role = Role.objects.create(name="Another Role")
        another_role.admin_users.add(user)

        # create an aclobj and set full-permission to operate aclobj to the test Role
        aclobj = ACLBase.objects.create(name="obj", created_user=user)
        aclobj.full.roles.add(self._role)
        aclobj.full.roles.add(another_role)

        params = {
            "object_id": str(aclobj.id),
            "object_type": str(aclobj.objtype),
            "is_public": "",
            "acl": [
                {
                    "role_id": str(another_role.id),
                    "value": str(ACLType.Nothing.id),
                },
            ],
            "default_permission": str(ACLType.Nothing.id),
        }
        resp = self.client.post(reverse("acl:set"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)

    def test_set_acl_of_uneditable_role(self):
        """This test try to change ACL of Role that logined-user isn't belonged to
        as an administrative member.
        """
        # initialize role member and it's permitted to fully control the aclobj
        user = self.guest_login()
        self._role.admin_users.add(user)

        aclobj = ACLBase.objects.create(name="obj", created_user=user, is_public=False)
        aclobj.full.roles.add(self._role)

        # create another role that is not irrelevant with "user"
        irrelevant_role = Role.objects.create(name="AnotherRole")

        # try to set ACL that includes irrelevant role configuration
        params = {
            "object_id": str(aclobj.id),
            "object_type": str(aclobj.objtype),
            "acl": [
                {"role_id": str(irrelevant_role.id), "value": str(ACLType.Full.id)},
            ],
            "default_permission": str(ACLType.Nothing.id),
        }
        resp = self.client.post(reverse("acl:set"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.content.decode("utf-8"),
            "Inadmissible setting. By this change you will never change this ACL",
        )

        # check Role, which user belongs to administrative members, can set ACL
        self.assertTrue(self._role.is_permitted(aclobj, ACLType.Full))
        self.assertFalse(irrelevant_role.is_permitted(aclobj, ACLType.Full))
