from airone.lib.test import AironeTestCase
from airone.lib.types import AttrTypeValue
from entry.models import Entry
from group.models import Group
from user.models import User


class ModelTest(AironeTestCase):
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
        This expects to replace parent_group member of subordinates
        """
        self.group2.delete()
        self.group3.refresh_from_db()
        self.assertEqual(self.group3.parent_group, self.group0)

    def test_delete_parent_lonely_group(self):
        """This try to delete Group that all subordinates have already been deleted.
        This expects to success to delete parent one.
        """
        deleting_groups = [self.group1, self.group3]
        for group in deleting_groups:
            group.delete()

            self.assertFalse(group.is_active)
            self.assertGreater(group.name.find("_deleted_"), 0)

    def test_get_referred_entries_through_group_attr(self):
        for index in range(3):
            entity = self.create_entity(
                **{
                    "user": self.user1,
                    "name": "Entity%d" % index,
                    "attrs": [{"name": "group", "type": AttrTypeValue["group"]}],
                }
            )
            self.add_entry(
                self.user1,
                "e-%d" % index,
                entity,
                values={
                    "group": self.group1,
                },
            )

        # check Group.get_referred_entries()
        self.assertFalse(self.group0.get_referred_entries().exists())
        self.assertEqual(
            [e.name for e in self.group1.get_referred_entries()], ["e-0", "e-1", "e-2"]
        )

        # check Group.get_referred_entries() with entity-name
        self.assertEqual(
            [e.name for e in self.group1.get_referred_entries(entity_name="Entity1")], ["e-1"]
        )

        # check Group.get_referred_entries() after deleting Entry
        entry = Entry.objects.filter(schema__name="Entity1", is_active=True).first()
        entry.delete()
        self.assertFalse(self.group1.get_referred_entries(entity_name="Entity1").exists())

    def test_get_referred_entries_through_array_group_attr(self):
        for index in range(3):
            entity = self.create_entity(
                **{
                    "user": self.user1,
                    "name": "Entity%d" % index,
                    "attrs": [{"name": "groups", "type": AttrTypeValue["array_group"]}],
                }
            )
            self.add_entry(
                self.user1,
                "e-%d" % index,
                entity,
                values={
                    "groups": [self.group1, self.group2],
                },
            )

        for group in [self.group1, self.group2]:
            # check Group.get_referred_entries()
            self.assertEqual([e.name for e in group.get_referred_entries()], ["e-0", "e-1", "e-2"])

            # check Group.get_referred_entries() with entity-name
            self.assertEqual(
                [e.name for e in group.get_referred_entries(entity_name="Entity1")], ["e-1"]
            )
