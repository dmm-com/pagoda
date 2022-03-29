from airone.lib.test import AironeViewTest
from user.models import User
from group.models import Group


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        # create Users and Groups for using this test
        for name in ['userA', 'userB']:
            User.objects.create(username=name, email='%s@example.com' % name)

        for name in ['groupA', 'groupB']:
            Group.objects.create(name=name)

    def test_get_create(self):
        user = self.guest_login()

        resp = self.client.get('/role/create')
        self.assertEqual(resp.status_code, 200)
