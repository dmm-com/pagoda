from airone.exceptions.group import GroupOperationException
from django.test import TestCase
from group.models import Group
from user.models import User


class ModelTest(TestCase):
    # helper methods to craete User and Group
    def _create_user(self, name):
        return User.objects.create(username=name)

    def _create_group(self, name, parent=None):
        return Group.objects.create(name=name, parent_group=parent)

    def setUp(self):
        """This test create User (user1) who belongs following hierarchical groups
        * group0
            ├──group1
            └──group2
                 └──group3(member: user1)
        """
        super(ModelTest, self).setUp()

        self.group0 = self._create_group("group0")
        self.group1 = self._create_group("group1", self.group0)
        self.group2 = self._create_group("group2", self.group0)
        self.group3 = self._create_group("group3", self.group2)
        self.user1 = self._create_user("user1")
        self.user1.groups.add(self.group3)

    def test_delete_edge_group(self):
        self.group1.delete()

        self.assertFalse(self.group1.is_active)
        self.assertEqual(self.group1.name.find("group1_deleted_"), 0)

    def test_delete_parent_group(self):
        """This try to delete Group that has subordinates.
        This expects to fail to delete parent one.
        """
        for group in [self.group0, self.group2]:
            with self.assertRaises(GroupOperationException) as cm:
                group.delete()

            self.assertEqual(cm.exception.args[0], "You can't delete group that has subordinates")

    def test_delete_parent_lonely_group(self):
        """This try to delete Group that all subordinates have already been deleted.
        This expects to success to delete parent one.
        """
        deleting_groups = [self.group1, self.group3]
        for group in deleting_groups:
            group.delete()

            self.assertFalse(group.is_active)
            self.assertGreater(group.name.find("_deleted_"), 0)
