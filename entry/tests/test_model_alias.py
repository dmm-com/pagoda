from airone.lib.test import AironeTestCase

from entity.models import Entity
from entry.models import Entry, AliasEntry
from user.models import User


class ModelTest(AironeTestCase):
  def setUp(self)
    super(ModelTest, self).setUp()

    # create common Instances in this test
    self.user: User = User(username="test")
    self.model = self.create_entity(self.user, "Kingdom")
    self.item = self.add_entry(self.user, "Shin", self.model)

  def test_create_alias():
    # add alias for this item
    self.item.add_alias("Li Shin")

    # check added alias item was actually created
    self.assertTrue(AliasEntry.objects.filter(alias="Li Shin", entry=self.item).exists())

  def test_delete_alias():
    # add alias for this item
    AliasEntry.objects.create(alias="Li Shin", entry=self.item)

    # check deleted alias item was actually deleted
    self.assertFalse(AliasEntry.objects.filter(alias="Li Shin", entry=self.item).exists())

  def test_list_alias():
    pass