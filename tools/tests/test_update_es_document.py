import logging
from unittest.mock import Mock, patch

from airone.lib.log import Logger
from airone.lib.test import AironeTestCase
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.models import Entry
from entry.services import AdvancedSearchService
from entry.tasks import update_es_documents
from tools.initialize_es_document import initialize_es_document
from tools.update_es_document import update_es_document
from user.models import User


class UpdateESDocuemntlTest(AironeTestCase):
    def setUp(self):
        super(UpdateESDocuemntlTest, self).setUp()

        self.user = User(username="test")
        self.user.save()

        # create entity
        self.entity1 = Entity.objects.create(name="Entity1", created_user=self.user)
        self.entity1.attrs.add(
            EntityAttr.objects.create(
                **{
                    "name": "attr",
                    "type": AttrType.STRING,
                    "created_user": self.user,
                    "parent_entity": self.entity1,
                }
            )
        )
        self.entity2 = Entity.objects.create(name="Entity2", created_user=self.user)

        # create entry
        self.entries = []
        for index in range(3):
            entry = Entry.objects.create(
                name="entry-%d" % index, created_user=self.user, schema=self.entity1
            )

            entry.complement_attrs(self.user)
            entry.attrs.first().add_value(self.user, "value-%d" % index)

            self.entries.append(entry)

        self.entry2 = Entry.objects.create(
            name="entry2", created_user=self.user, schema=self.entity2
        )

    @patch("entry.tasks.update_es_documents.delay", Mock(side_effect=update_es_documents))
    def test_initialize_entries(self):
        ret = AdvancedSearchService.search_entries(self.user, [self.entity1.id, self.entity2.id])
        self.assertEqual(ret.ret_count, 0)

        initialize_es_document([])

        ret = AdvancedSearchService.search_entries(self.user, [self.entity1.id])
        self.assertEqual(ret.ret_count, 3)
        self.assertTrue(all([x.entity["id"] == self.entity1.id for x in ret.ret_values]))
        self.assertTrue(
            all([x.entry["id"] in [y.id for y in self.entries] for x in ret.ret_values])
        )
        ret = AdvancedSearchService.search_entries(self.user, [self.entity2.id])
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual(ret.ret_values[0].entity["id"], self.entity2.id)
        self.assertEqual(ret.ret_values[0].entry["id"], self.entry2.id)

        # recreate index, specified entity
        initialize_es_document([self.entity2.name])
        ret = AdvancedSearchService.search_entries(self.user, [self.entity1.id, self.entity2.id])
        self.assertEqual(ret.ret_count, 1)

    @patch("entry.tasks.update_es_documents.delay", Mock(side_effect=update_es_documents))
    def test_update_entry(self):
        initialize_es_document([])

        # update entry-0
        entry = self.entries[0]
        entry.attrs.first().add_value(self.user, "new-attr-value")
        entry.save()

        # specified other entity, no update
        update_es_document([self.entity2.name])

        ret = AdvancedSearchService.search_entries(self.user, [self.entity1.id], [{"name": "attr"}])
        self.assertEqual(ret.ret_count, 3)

        entry_info = [x for x in ret.ret_values if x.entry["id"] == entry.id][0]
        self.assertEqual(entry_info.attrs["attr"]["value"], "value-0")

        with self.assertLogs(logger=Logger, level=logging.WARNING) as warning_log:
            # update es document
            update_es_document([])
            self.assertTrue(
                warning_log.output[0],
                "WARNING:airone:Update elasticsearch document (entry_id: %s)" % entry.id,
            )

        ret = AdvancedSearchService.search_entries(self.user, [self.entity1.id], [{"name": "attr"}])
        self.assertEqual(ret.ret_count, 3)

        entry_info = [x for x in ret.ret_values if x.entry["id"] == entry.id][0]
        self.assertEqual(entry_info.attrs["attr"]["value"], "new-attr-value")

    @patch("entry.tasks.update_es_documents.delay", Mock(side_effect=update_es_documents))
    def test_delete_entry(self):
        initialize_es_document([])

        # delete entry-0
        entry = self.entries[0]
        entry.is_active = False
        entry.save()

        # specified other entity, no update
        update_es_document([self.entity2.name])
        ret = AdvancedSearchService.search_entries(self.user, [self.entity1.id])

        self.assertEqual(ret.ret_count, 3)

        with self.assertLogs(logger=Logger, level=logging.WARNING) as warning_log:
            # update es document
            update_es_document([])
            self.assertTrue(
                warning_log.output[0],
                "WARNING:airone:Delete elasticsearch document (entry_id: %s)" % entry.id,
            )

        ret = AdvancedSearchService.search_entries(self.user, [self.entity1.id])

        self.assertEqual(ret.ret_count, 2)
