from .base import RoleTestBase

from role.models import Role


class ModelTest(RoleTestBase):

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

    def test_permit_to_edit_by_super_user(self):
        super_user = self.admin_login()

        # Suser-user has permission to edit any role without registering
        # administrative Users and Groups.
        self.assertFalse(self.role.administrative_users.filter(id=super_user.id).exists())
        self.assertFalse(bool(set([g.id for g in super_user.groups.all()]) &
                              set([g.id for g in self.role.administrative_groups.all()])))
        self.assertTrue(self.role.permit_to_edit(super_user))
