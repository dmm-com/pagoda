from airone.lib.test import AironeTestCase

from role.models import Role
from user.models import User
from group.models import Group


class ModelTest(AironeTestCase):
    def setUp(self):
        super(ModelTest, self).setUp()

        # create Users and Groups for using this test
        self.users = {n: User.objects.create(username=n, email='%s@example.com' % n)
                      for n in ['userA', 'userB']}
        self.groups = {n: Group.objects.create(name=n) for n in ['groupA', 'groupB']}

        self.role = Role.objects.create(name='test_role')

    def test_is_belonged_to_registered_by_user(self):
        # set userA belongs to groupA as groups member
        self.users['userA'].groups.add(self.groups['groupA'])

        # set userA belongs to test Role as users member
        self.role.users.add(self.users['userA'])

        self.assertTrue(self.role.is_belonged_to(self.users['userA']))
        self.assertFalse(self.role.is_belonged_to(self.users['userB']))

    def test_is_belonged_to_registered_by_group(self):
        # set userA belongs to groupA as groups member
        self.users['userA'].groups.add(self.groups['groupA'])

        # set groupA belongs to test Role as groups member
        self.role.groups.add(self.groups['groupA'])

        self.assertTrue(self.role.is_belonged_to(self.users['userA']))
        self.assertFalse(self.role.is_belonged_to(self.users['userB']))

    def test_permit_to_edit_registered_by_user(self):
        # set userA belongs to groupA as administrative_groups member
        self.users['userA'].groups.add(self.groups['groupA'])

        # set userA belongs to test Role as administrative_users member
        self.role.administrative_users.add(self.users['userA'])

        self.assertTrue(self.role.permit_to_edit(self.users['userA']))
        self.assertFalse(self.role.permit_to_edit(self.users['userB']))

    def test_permit_to_edit_registered_by_group(self):
        # set userA belongs to groupA as administrative_groups member
        self.users['userA'].groups.add(self.groups['groupA'])

        # set groupA belongs to test Role as users member as administrative_groups member
        self.role.administrative_groups.add(self.groups['groupA'])

        self.assertTrue(self.role.permit_to_edit(self.users['userA']))
        self.assertFalse(self.role.permit_to_edit(self.users['userB']))
