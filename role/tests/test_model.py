from .base import RoleTestBase

from airone.lib.acl import ACLType
from entity.models import Entity
from role.models import Role


class ModelTest(RoleTestBase):
    def test_is_belonged_to_registered_by_user(self):
        # set userA belongs to groupA as groups member
        self.users["userA"].groups.add(self.groups["groupA"])

        # set userA belongs to test Role as users member
        self.role.users.add(self.users["userA"])

        self.assertTrue(self.role.is_belonged_to(self.users["userA"]))
        self.assertFalse(self.role.is_belonged_to(self.users["userB"]))

    def test_is_belonged_to_registered_by_group(self):
        # set userA belongs to groupA as groups member
        self.users["userA"].groups.add(self.groups["groupA"])

        # set groupA belongs to test Role as groups member
        self.role.groups.add(self.groups["groupA"])

        self.assertTrue(self.role.is_belonged_to(self.users["userA"]))
        self.assertFalse(self.role.is_belonged_to(self.users["userB"]))

    def test_is_editable_registered_by_user(self):
        # set userA belongs to groupA as admin_groups member
        self.users["userA"].groups.add(self.groups["groupA"])

        # set userA belongs to test Role as admin_users member
        self.role.admin_users.add(self.users["userA"])

        self.assertTrue(self.role.is_editable(self.users["userA"]))
        self.assertFalse(self.role.is_editable(self.users["userB"]))

    def test_is_editable_registered_by_group(self):
        # set userA belongs to groupA as admin_groups member
        self.users["userA"].groups.add(self.groups["groupA"])

        # set groupA belongs to test Role as users member as admin_groups member
        self.role.admin_groups.add(self.groups["groupA"])

        self.assertTrue(self.role.is_editable(self.users["userA"]))
        self.assertFalse(self.role.is_editable(self.users["userB"]))

    def test_is_editable_by_super_user(self):
        super_user = self.admin_login()

        # Suser-user has permission to edit any role without registering
        # administrative Users and Groups.
        self.assertFalse(self.role.admin_users.filter(id=super_user.id).exists())
        self.assertFalse(
            bool(
                set([g.id for g in super_user.groups.all()])
                & set([g.id for g in self.role.admin_groups.all()])
            )
        )
        self.assertTrue(self.role.is_editable(super_user))

    def test_to_create_role_that_has_same_name_with_group(self):
        role = Role.objects.create(name="groupA")
        self.assertEqual(role.name, self.groups["groupA"].name)

    def test_set_permission(self):
        # create ACLBase object to set ACL
        user = self.users["userA"]
        entity = Entity.objects.create(name="Entity", created_user=user, is_public=False)

        # set permission for created Entity
        self.role.permissions.add(entity.writable)

        # check permission check processing would be worked well
        self.assertTrue(self.role.is_permitted(entity, ACLType.Readable))
        self.assertTrue(self.role.is_permitted(entity, ACLType.Writable))
        self.assertFalse(self.role.is_permitted(entity, ACLType.Full))

    def test_delete(self):
        self.role.delete()

        deleted_role = Role.objects.filter(id=self.role.id).first()
        self.assertEqual(deleted_role, self.role)
        self.assertFalse(deleted_role.is_active)
        self.assertIn("test_role", deleted_role.name)
