from django.test import TestCase
from group.models import Group
from user.models import User
from airone.lib.acl import ACLType
from entity.models import Entity
from role.models import Role


class ModelTest(TestCase):
    def setUp(self):
        """This test create User (user1) who belongs following hierarchical groups
        * group0
            ├──group1
            └──group2
                 └──group3 (member: user1) [deleted]
        """
        self.group0 = Group.objects.create(name="group0")
        self.group2 = Group.objects.create(name="group2", parent_group=self.group0)
        self.group3 = Group.objects.create(name="group3", parent_group=self.group2)
        Group.objects.create(name="group1", parent_group=self.group0)
        self.user = User.objects.create(username="user1")
        self.user.groups.add(self.group3)

    def test_get_all_hierarchical_superior_groups_that_user_belongs(self):
        self.assertEqual(
            sorted([g.name for g in self.user.belonging_groups()]),
            sorted(["group0", "group2", "group3"]),
        )

        # This checks behavior when 'is_direct_belonging' parameter is passed, just in case
        self.assertEqual(list(self.user.belonging_groups(is_direct_belonging=True)), [self.group3])

        # This tests user permitted to access object when parent group has permission to access it
        role = Role.objects.create(name="Role1")
        entity = Entity.objects.create(
            name="entity",
            created_user=self.user,
            is_public=False,
            default_permission=ACLType.Nothing.id,
        )
        role.permissions.add(entity.full)
        role.admin_groups.add(self.group0)
        self.assertTrue(self.user.has_permission(entity, ACLType.Full))

    def test_belonging_group_when_parent_group_has_been_deleted(self):
        """This test create User (user1) who belongs following hierarchical groups
        * group0
            ├──group1
            └──group2 [deleted]
                 └──group3 (member: user1)
        """
        self.group2.delete()
        self.assertEqual(
            sorted([g.name for g in self.user.belonging_groups()]),
            sorted(["group0", "group3"]),
        )

    def test_belonging_group_when_root_group_has_been_deleted(self):
        """This test create User (user1) who belongs following hierarchical groups
        * group0 [deleted]
            ├──group1
            └──group2
                 └──group3 (member: user1)
        """
        self.group0.delete()
        self.assertEqual(
            sorted([g.name for g in self.user.belonging_groups()]),
            sorted(["group2", "group3"]),
        )

    def test_belonging_group_when_belonging_group_has_been_deleted(self):
        """This test create User (user1) who belongs following hierarchical groups
        * group0
            ├──group1
            └──group2
                 └──group3 (member: user1) [deleted]
        """
        self.group3.delete()
        self.assertEqual(
            sorted([g.name for g in self.user.belonging_groups()]),
            sorted([]),
        )
