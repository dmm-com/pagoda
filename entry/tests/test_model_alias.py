from airone.lib.test import AironeTestCase
from entry.models import AliasEntry


class ModelTest(AironeTestCase):
    def setUp(self):
        super(ModelTest, self).setUp()

        # create common Instances in this test
        self.user = self.admin_login()
        self.model = self.create_entity(self.user, "Kingdom")
        self.item = self.add_entry(self.user, "Shin", self.model)

    def test_create_alias(self):
        # add alias for this item
        self.item.add_alias("Li Shin")

        # check added alias item was actually created
        self.assertTrue(AliasEntry.objects.filter(name="Li Shin", entry=self.item).exists())

    def test_create_alias_with_other_item(self):
        # add alias for this item
        AliasEntry.objects.create(name="Li Shin", entry=self.item)
        AliasEntry.objects.create(name="Captain", entry=self.item)

        # add alias for other item
        other_item = self.add_entry(self.user, "Hyou", self.model)
        with self.assertRaises(ValueError) as e:
            other_item.add_alias("Captain")
            self.assertEqual(str(e), "Specified name has already been used by other Item or Alias")

        with self.assertRaises(ValueError) as e:
            other_item.add_alias("Shin")
            self.assertEqual(str(e), "Specified name has already been used by other Item or Alias")

    def test_create_alias_with_other_entity(self):
        # add alias for this item
        AliasEntry.objects.create(name="Captain", entry=self.item)

        # add alias for other entity
        other_model = self.create_entity(self.user, "Country")
        other_item = self.add_entry(self.user, "China", other_model)
        other_item.add_alias("Captain")

        # check added alias item was actually created
        self.assertEqual(other_item.aliases.filter(name="Captain").count(), 1)

    def test_delete_alias(self):
        # add alias for this item
        AliasEntry.objects.create(name="Li Shin", entry=self.item)

        # delete alias for this item
        self.item.delete_alias("Li Shin")

        # check deleted alias item was actually deleted
        self.assertFalse(AliasEntry.objects.filter(name="Li Shin", entry=self.item).exists())

    def test_list_alias(self):
        # add alias for this item
        AliasEntry.objects.create(name="Li Shin", entry=self.item)
        AliasEntry.objects.create(name="Captain", entry=self.item)

        # check list alias
        self.assertEqual(self.item.aliases.count(), 2)
        self.assertEqual(["Li Shin", "Captain"], [alias.name for alias in self.item.aliases.all()])
