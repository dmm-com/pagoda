import json

from acl.models import ACLBase
from role.models import Role
from airone.lib.acl import ACLType
from airone.lib.test import AironeViewTest


class ACLAPITest(AironeViewTest):

    def test_retrieve(self):
        user = self.admin_login()

        acl = ACLBase(name='test', created_user=user)
        acl.save()

        resp = self.client.get('/acl/api/v2/acls/%s' % acl.id)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body['id'], acl.id)
        self.assertEqual(body['name'], acl.name)

    def test_retrieve_by_others(self):
        user = self.admin_login()

        acl = ACLBase(name='test', created_user=user, is_public=False)
        acl.save()

        self.guest_login()
        resp = self.client.get('/acl/api/v2/acls/%s' % acl.id)
        self.assertEqual(resp.status_code, 403)

    def test_update(self):
        user = self.guest_login()
        role = Role.objects.create(name='role')
        role.admin_users.add(user)

        acl = ACLBase(name='test', created_user=user)
        acl.save()


        resp = self.client.put('/acl/api/v2/acls/%s' % acl.id, json.dumps({
            'name': acl.name,
            'is_public': False,
            'default_permission': str(ACLType.Nothing.id),
            'objtype': acl.objtype,
            'acl': [
                {
                    'member_id': str(role.id),
                    'value': str(ACLType.Writable.id),
                },
            ],
        }), 'application/json;charset=utf-8')
        self.assertEqual(resp.status_code, 200)

    def test_update_by_others(self):
        user = self.guest_login()
        role = Role.objects.create(name='role')

        acl = ACLBase(name='test', created_user=user)
        acl.save()

        # send request to update ACL of Role that is not permitted to be edited
        resp = self.client.put('/acl/api/v2/acls/%s' % acl.id, json.dumps({
            'name': acl.name,
            'is_public': False,
            'default_permission': str(ACLType.Nothing.id),
            'objtype': acl.objtype,
            'acl': [
                {
                    'member_id': str(role.id),
                    'value': str(ACLType.Writable.id),
                },
            ],
        }), 'application/json;charset=utf-8')
        self.assertEqual(resp.status_code, 400)
