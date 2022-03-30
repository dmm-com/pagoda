import json

from airone.lib.test import AironeViewTest
from role.models import Role
from user.models import User
from group.models import Group


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        # create Users and Groups for using this test
        self._users = {n: User.objects.create(username=n, email='%s@example.com' % n)
                       for n in ['userA', 'userB']}
        self._groups = {n: Group.objects.create(name=n) for n in ['groupA', 'groupB']}

    def test_get_create(self):
        user = self.guest_login()

        resp = self.client.get('/role/create')
        self.assertEqual(resp.status_code, 200)

    def test_post_create(self):
        user = self.guest_login()

        params = {
            'name': 'Creating Role',
            'users': [{'id': self._users['userA'].id}],
            'groups': [{'id': self._groups['groupA'].id}],
            'admin_users': [{'id': self._users['userB'].id}],
            'admin_groups': [{'id': self._groups['groupB'].id}],
        }
        resp = self.client.post('/role/do_create', json.dumps(params), 'application/json')
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
