import json

from .base import RoleTestBase
from role.models import Role


class ModelTest(RoleTestBase):

    def test_get_create(self):
        user = self.guest_login()

        resp = self.client.get('/role/create/')
        self.assertEqual(resp.status_code, 200)

    def test_post_create(self):
        user = self.guest_login()

        params = {
            'name': 'Creating Role',
            'users': [{'id': self.users['userA'].id}],
            'groups': [{'id': self.groups['groupA'].id}],
            'admin_users': [{'id': self.users['userB'].id}],
            'admin_groups': [{'id': self.groups['groupB'].id}],
        }
        resp = self.client.post('/role/do_create/', json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {
            'msg': 'Succeeded in creating new Role "Creating Role"'
        })

        # check new Role instance was created
        role = Role.objects.get(name='Creating Role', is_active=True)
        self.assertEqual([x.username for x in role.users.all()], ['userA'])
        self.assertEqual([x.username for x in role.administrative_users.all()], ['userB'])
        self.assertEqual([x.name for x in role.groups.all()], ['groupA'])
        self.assertEqual([x.name for x in role.administrative_groups.all()], ['groupB'])

    def test_get_edit(self):
        user = self.guest_login()
        role = Role.objects.create(name='Role')

        # set test user as an administrative one
        role.administrative_users.add(user)

        resp = self.client.get('/role/edit/%d/' % role.id)
        self.assertEqual(resp.status_code, 200)

    def test_get_edit_without_permission(self):
        user = self.guest_login()
        role = Role.objects.create(name='Role')

        resp = self.client.get('/role/edit/%d/' % role.id)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'),
                         'You do not have permission to change this role')

    def test_post_role(self):
        user = self.guest_login()
        role = Role.objects.create(name='Role')

        # set test user as an administrative one
        role.administrative_users.add(user)

        # register userA and groupA as initialized users and groups
        role.users.add(self.users['userA'])
        role.groups.add(self.groups['groupA'])
        role.administrative_users.add(self.users['userA'])
        role.administrative_groups.add(self.groups['groupA'])

        # send a request to reigster userB and groupB as members of the "Role"
        params = {
            'name': 'Edited Role',
            'users': [{'id': self.users['userB'].id}],
            'groups': [{'id': self.groups['groupB'].id}],
            'admin_users': [{'id': self.users['userB'].id}],
            'admin_groups': [{'id': self.groups['groupB'].id}],
        }
        resp = self.client.post('/role/do_edit/%d/' % role.id,
                                json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 200)

        # check role attributes are updated expectedly
        role.refresh_from_db()
        self.assertEqual(role.name, 'Edited Role')
        self.assertEqual([x.username for x in role.users.all()], ['userB'])
        self.assertEqual([x.username for x in role.administrative_users.all()], ['userB'])
        self.assertEqual([x.name for x in role.groups.all()], ['groupB'])
        self.assertEqual([x.name for x in role.administrative_groups.all()], ['groupB'])
