from unittest import mock

from django.conf import settings

from airone.lib.acl import ACLType
from airone.lib.elasticsearch import AttrHint
from airone.lib.types import AttrType
from entity.models import Entity
from entry.services import AdvancedSearchService
from group.models import Group
from role import tasks
from role.models import Role

from .base import RoleTestBase


class ModelTest(RoleTestBase):
    def test_is_belonged_to_registered_in_users(self):
        # set userA belongs to test Role as users member
        self.role.users.add(self.users["userA"])

        self.assertTrue(self.role.is_belonged_to(self.users["userA"]))
        self.assertFalse(self.role.is_belonged_to(self.users["userB"]))
        self.assertTrue(self.role.is_belonged_to(self.users["userA"], as_member=True))

    def test_is_belonged_to_registered_in_groups(self):
        # set userA belongs to groupA as groups member
        self.users["userA"].groups.add(self.groups["groupA"])

        # set groupA belongs to test Role as groups member
        self.role.groups.add(self.groups["groupA"])

        self.assertTrue(self.role.is_belonged_to(self.users["userA"]))
        self.assertFalse(self.role.is_belonged_to(self.users["userB"]))
        self.assertTrue(self.role.is_belonged_to(self.users["userA"], as_member=True))

    def test_is_belonged_to_registered_in_admin_users(self):
        # set userA belongs to test Role as admin user
        self.role.admin_users.add(self.users["userA"])

        self.assertTrue(self.role.is_belonged_to(self.users["userA"]))
        self.assertFalse(self.role.is_belonged_to(self.users["userB"]))
        self.assertFalse(self.role.is_belonged_to(self.users["userA"], as_member=True))

    def test_is_belonged_to_registered_in_admin_groups(self):
        # set userA belongs to groupA as groups member
        self.users["userA"].groups.add(self.groups["groupA"])

        # set groupA belongs to test Role as admin group
        self.role.admin_groups.add(self.groups["groupA"])

        self.assertTrue(self.role.is_belonged_to(self.users["userA"]))
        self.assertFalse(self.role.is_belonged_to(self.users["userB"]))
        self.assertFalse(self.role.is_belonged_to(self.users["userA"], as_member=True))

    def test_is_belonged_to_parent_group(self):
        """This test create Role (role1) that belongs following hierarchical groups
        === Group ===
        * Parent
            └──groupA (member: userA)
                 └──groupB (member: userB)
        === Role ===
        * test_role
          - groups: groupA
          - admin_groups: groupB
        """
        parent_group = Group.objects.create(name="Parent")
        self.groups["groupA"].parent_group = parent_group
        self.groups["groupA"].save(update_fields=["parent_group"])
        self.groups["groupB"].parent_group = self.groups["groupA"]
        self.groups["groupB"].save(update_fields=["parent_group"])
        self.users["userA"].groups.add(self.groups["groupA"])
        self.users["userB"].groups.add(self.groups["groupB"])

        # set "parent_group" to member of the test_role
        self.role.groups.add(parent_group)

        # check both userA and userB belong to the test_role
        for user in self.users.values():
            self.assertTrue(self.role.is_belonged_to(user))

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

    def test_is_editable_when_parent_group_is_set(self):
        """This test creates following group tree
        * Parent
            └──groupA (member: userA)
        """
        parent_group = Group.objects.create(name="Parent")
        self.users["userA"].groups.add(self.groups["groupA"])
        self.groups["groupA"].parent_group = parent_group
        self.groups["groupA"].save(update_fields=["parent_group"])

        # set parent group as an administrative one
        self.role.admin_groups.add(parent_group)

        # check subordinates group member can edit its role
        self.assertTrue(self.role.is_editable(self.users["userA"]))

    def test_to_create_role_that_has_same_name_with_group(self):
        role = Role.objects.create(name="groupA")
        self.assertEqual(role.name, self.groups["groupA"].name)

    def test_set_permission(self):
        # create ACLBase object to set ACL
        user = self.users["userA"]
        entity = Entity.objects.create(name="Entity", created_user=user, is_public=False)

        # set permission for created Entity
        permission = entity.writable
        permission.roles.add(self.role)

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

    def test_get_referred_entries(self):
        user = self.users["userA"]
        entity = self.create_entity(
            **{
                "user": user,
                "name": "entity",
                "attrs": [
                    {
                        "name": "role",
                        "type": AttrType.ROLE,
                    }
                ],
            }
        )

        self.add_entry(user, "e-1", entity, values={"role": self.role})

        self.assertEqual([e.name for e in self.role.get_referred_entries()], ["e-1"])

    def test_get_referred_entries_from_array(self):
        user = self.users["userA"]
        entity = self.create_entity(
            **{
                "user": user,
                "name": "entity",
                "attrs": [
                    {
                        "name": "roles",
                        "type": AttrType.ARRAY_ROLE,
                    }
                ],
            }
        )
        role2 = Role.objects.create(name="test2")

        roles = [self.role, role2]
        self.add_entry(user, "e-1", entity, values={"roles": roles})
        for role in roles:
            self.assertEqual([e.name for e in role.get_referred_entries()], ["e-1"])

    def test_max_roles(self):
        Role.objects.all().delete()

        max_roles = 10
        Role.objects.bulk_create([Role(name=f"role-{i}") for i in range(max_roles)])

        # if the limit exceeded, RuntimeError should be raised
        settings.MAX_ROLES = max_roles
        with self.assertRaises(RuntimeError):
            Role.objects.create(name=f"role-{max_roles}")

        # if the limit is not set, RuntimeError should not be raised
        settings.MAX_ROLES = None
        Role.objects.create(name=f"role-{max_roles}")

    @mock.patch(
        "role.tasks.edit_role_referrals.delay", mock.Mock(side_effect=tasks.edit_role_referrals)
    )
    def test_es_update_on_entry_delete(self):
        user = self.users["userA"]
        entity = self.create_entity(
            **{
                "user": user,
                "name": "entity",
                "attrs": [
                    {
                        "name": "role",
                        "type": AttrType.ROLE,
                    }
                ],
            }
        )

        self.add_entry(user, "e-1", entity, values={"role": self.role})
        self.role.delete()

        resp1 = AdvancedSearchService.search_entries(user, [entity.id], [AttrHint(name="role")])
        self.assertEqual(resp1.ret_values[0].attrs["role"]["value"]["name"], "")
