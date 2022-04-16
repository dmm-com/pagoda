from airone.lib.test import AironeViewTest

from role.models import Role
from user.models import User
from group.models import Group


class RoleTestBase(AironeViewTest):
    def setUp(self):
        super(RoleTestBase, self).setUp()

        # create Users and Groups for using this test
        self.users = {n: User.objects.create(username=n, email='%s@example.com' % n)
                      for n in ['userA', 'userB']}
        self.groups = {n: Group.objects.create(name=n) for n in ['groupA', 'groupB']}

        # create test Role instance
        self.role = Role.objects.create(name='test_role')
