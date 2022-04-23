from airone.lib.test import AironeTestCase
from airone.lib.types import AttrTypeValue

from entity.models import Entity, EntityAttr
from entry.models import Entry
from user.models import User

from tools.update_es_document import register_documents
from tools.update_es_document import delete_unnecessary_documents


class UpdateESDocuemntlTest(AironeTestCase):
    def setUp(self):
        super(UpdateESDocuemntlTest, self).setUp()

        self.user = User(username="test")
        self.user.save()

        # create entity
        self.entity = Entity.objects.create(name="Entity", created_user=self.user)
        self.entity.attrs.add(
            EntityAttr.objects.create(
                **{
                    "name": "attr",
                    "type": AttrTypeValue["string"],
                    "created_user": self.user,
                    "parent_entity": self.entity,
                }
            )
        )

        # create entry
        self.entries = []
        for index in range(3):
            entry = Entry.objects.create(
                name="entry-%d" % index, created_user=self.user, schema=self.entity
            )

            entry.complement_attrs(self.user)
            entry.attrs.first().add_value(self.user, "value-%d" % index)

            self.entries.append(entry)

    def test_register_entries(self):
        ret = Entry.search_entries(self.user, [self.entity.id])
        self.assertEqual(ret["ret_count"], 0)
        self.assertEqual(ret["ret_values"], [])

        register_documents(self._es, self._es._index)

        ret = Entry.search_entries(self.user, [self.entity.id])
        self.assertEqual(ret["ret_count"], 3)
        self.assertTrue(
            all([x["entity"]["id"] == self.entity.id for x in ret["ret_values"]])
        )
        self.assertTrue(
            all(
                [
                    x["entry"]["id"] in [y.id for y in self.entries]
                    for x in ret["ret_values"]
                ]
            )
        )

    def test_update_entry(self):
        register_documents(self._es, self._es._index)

        # update entry-0
        entry = self.entries[0]
        entry.attrs.first().add_value(self.user, "new-attr-value")
        entry.name = "new-entry-name"
        entry.save()

        register_documents(self._es, self._es._index)

        ret = Entry.search_entries(self.user, [self.entity.id], [{"name": "attr"}])
        self.assertEqual(ret["ret_count"], 3)

        entry_info = [x for x in ret["ret_values"] if x["entry"]["id"] == entry.id][0]
        self.assertEqual(entry_info["entry"]["name"], "new-entry-name")
        self.assertEqual(entry_info["attrs"]["attr"]["value"], "new-attr-value")

    def test_delete_entry(self):
        register_documents(self._es, self._es._index)

        # delete entry-0
        entry = self.entries[0]
        Entry.objects.filter(id=entry.id).delete()

        delete_unnecessary_documents(self._es, self._es._index)
        ret = Entry.search_entries(self.user, [self.entity.id])

        self.assertEqual(ret["ret_count"], 2)
        self.assertFalse(any(x["entry"]["id"] == entry.id for x in ret["ret_values"]))
