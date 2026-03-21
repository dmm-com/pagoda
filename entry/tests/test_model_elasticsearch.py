from datetime import date

from django.conf import settings
from elasticsearch import NotFoundError

from acl.models import ACLBase
from airone.lib.elasticsearch import AdvancedSearchResultRecord, AttrHint
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.models import Attribute, Entry
from entry.services import AdvancedSearchService
from entry.settings import CONFIG
from entry.tests.test_model import BaseModelTest
from group.models import Group
from role.models import Role
from user.models import User


class ModelElasticsearchTest(BaseModelTest):
    def test_export_entry(self):
        user = User.objects.create(username="hoge")

        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        attr_info = {
            "str1": {"type": AttrType.STRING, "is_public": True},
            "str2": {"type": AttrType.STRING, "is_public": True},
            "obj": {"type": AttrType.OBJECT, "is_public": True},
            "invisible": {"type": AttrType.STRING, "is_public": False},
        }

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
                is_public=info["is_public"],
            )

            if info["type"] & AttrType.OBJECT:
                attr.referral.add(ref_entity)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.attrs.get(name="str1").add_value(user, "hoge")

        entry.attrs.get(name="str2").add_value(user, "foo")
        # update AttributeValue of Attribute 'str2'
        entry.attrs.get(name="str2").add_value(user, "bar")

        exported_data = entry.export(user)
        self.assertEqual(exported_data["name"], entry.name)
        self.assertEqual(
            len(exported_data["attrs"]),
            len([x for x in attr_info.values() if x["is_public"]]),
        )

        self.assertEqual(exported_data["attrs"]["str1"], "hoge")
        self.assertEqual(exported_data["attrs"]["str2"], "bar")
        self.assertIsNone(exported_data["attrs"]["obj"])

        # change the name of EntityAttr then export entry
        NEW_ATTR_NAME = "str1 (changed)"
        entity_attr = entry.schema.attrs.get(name="str1")
        entity_attr.name = NEW_ATTR_NAME
        entity_attr.save()

        exported_data = entry.export(user)
        self.assertTrue(NEW_ATTR_NAME in exported_data["attrs"])
        self.assertEqual(exported_data["attrs"][NEW_ATTR_NAME], "hoge")

        # Add an Attribute after creating entry
        EntityAttr.objects.create(
            **{
                "name": "new_attr",
                "type": AttrType.STRING,
                "created_user": user,
                "parent_entity": entity,
            }
        )
        exported_data = entry.export(user)
        self.assertTrue("new_attr" in exported_data["attrs"])

    def test_export_entry_v2(self):
        user = User.objects.create(username="hoge")

        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        attr_info = {
            "str1": {"type": AttrType.STRING, "is_public": True},
            "str2": {"type": AttrType.STRING, "is_public": True},
            "obj": {"type": AttrType.OBJECT, "is_public": True},
            "invisible": {"type": AttrType.STRING, "is_public": False},
        }

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
                is_public=info["is_public"],
            )

            if info["type"] & AttrType.OBJECT:
                attr.referral.add(ref_entity)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.attrs.get(name="str1").add_value(user, "hoge")

        entry.attrs.get(name="str2").add_value(user, "foo")
        # update AttributeValue of Attribute 'str2'
        entry.attrs.get(name="str2").add_value(user, "bar")

        exported_data = entry.export_v2(user)
        self.assertEqual(exported_data["name"], entry.name)
        self.assertEqual(
            len(exported_data["attrs"]),
            len([x for x in attr_info.values() if x["is_public"]]),
        )
        self.assertIn({"name": "str1", "value": "hoge"}, exported_data["attrs"])
        self.assertIn({"name": "str2", "value": "bar"}, exported_data["attrs"])
        self.assertIn({"name": "obj", "value": None}, exported_data["attrs"])

        # change the name of EntityAttr then export entry
        NEW_ATTR_NAME = "str1 (changed)"
        entity_attr = entry.schema.attrs.get(name="str1")
        entity_attr.name = NEW_ATTR_NAME
        entity_attr.save()

        exported_data = entry.export_v2(user)
        self.assertIn({"name": NEW_ATTR_NAME, "value": "hoge"}, exported_data["attrs"])
        self.assertNotIn({"name": "str1", "value": "hoge"}, exported_data["attrs"])

        # Add an Attribute after creating entry
        EntityAttr.objects.create(
            **{
                "name": "new_attr",
                "type": AttrType.STRING,
                "created_user": user,
                "parent_entity": entity,
            }
        )
        exported_data = entry.export_v2(user)
        self.assertIn({"name": "new_attr", "value": ""}, exported_data["attrs"])

    def test_register_entry_to_elasticsearch(self):
        ENTRY_COUNTS = 10
        user = User.objects.create(username="hoge")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)

        ref_entry1 = Entry.objects.create(
            name="referred_entry1", schema=ref_entity, created_user=user
        )
        Entry.objects.create(name="referred_entry2", schema=ref_entity, created_user=user)

        ref_group = Group.objects.create(name="group")

        attr_info = {
            "str": {
                "type": AttrType.STRING,
                "value": "foo",
            },
            "obj": {
                "type": AttrType.OBJECT,
                "value": str(ref_entry1.id),
            },
            "name": {
                "type": AttrType.NAMED_OBJECT,
                "value": {"name": "bar", "id": str(ref_entry1.id)},
            },
            "bool": {
                "type": AttrType.BOOLEAN,
                "value": False,
            },
            "date": {
                "type": AttrType.DATE,
                "value": date(2018, 1, 1),
            },
            "group": {
                "type": AttrType.GROUP,
                "value": str(ref_group.id),
            },
            "arr_str": {
                "type": AttrType.ARRAY_STRING,
                "value": ["foo", "bar", "baz"],
            },
            "arr_obj": {
                "type": AttrType.ARRAY_OBJECT,
                "value": [str(x.id) for x in Entry.objects.filter(schema=ref_entity)],
            },
            "arr_name": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "value": [
                    {"name": "hoge", "id": str(x.id)}
                    for x in Entry.objects.filter(schema=ref_entity)
                ],
            },
        }

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )

            if info["type"] & AttrType.OBJECT:
                attr.referral.add(ref_entity)

        for index in range(0, ENTRY_COUNTS):
            entry = Entry.objects.create(name="e-%d" % index, schema=entity, created_user=user)
            entry.complement_attrs(user)

            for attr_name, info in attr_info.items():
                attr = entry.attrs.get(name=attr_name)
                attr.add_value(user, info["value"])

            entry.register_es()

        # checks that all entries are registered to the ElasticSearch.
        res = AdvancedSearchService.get_all_es_docs()
        self.assertEqual(res["hits"]["total"]["value"], ENTRY_COUNTS + 2)

        # checks that all registered entries can be got from Elasticsearch
        for entry in Entry.objects.filter(schema=entity):
            res = self._es.get(index=settings.ES_CONFIG["INDEX_NAME"], id=entry.id)
            self.assertTrue(res["found"])

            # This checks whether returned results have all values of attributes
            self.assertEqual(
                set([x["name"] for x in res["_source"]["attr"]]),
                set(k for k in attr_info.keys()),
            )

            for k, v in attr_info.items():
                value = [x for x in res["_source"]["attr"] if x["name"] == k]

                self.assertTrue(all([x["type"] == v["type"] for x in value]))
                if k == "str":
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0]["value"], "foo")

                elif k == "obj":
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0]["value"], ref_entry1.name)
                    self.assertEqual(value[0]["referral_id"], ref_entry1.id)

                elif k == "name":
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0]["key"], "bar")
                    self.assertEqual(value[0]["value"], ref_entry1.name)
                    self.assertEqual(value[0]["referral_id"], ref_entry1.id)

                elif k == "bool":
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0]["value"], False)

                elif k == "date":
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0]["date_value"], "2018-01-01")

                elif k == "group":
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0]["value"], ref_group.name)
                    self.assertEqual(value[0]["referral_id"], ref_group.id)

                elif k == "arr_str":
                    self.assertEqual(len(value), 3)
                    self.assertEqual(
                        sorted([x["value"] for x in value]),
                        sorted(["foo", "bar", "baz"]),
                    )

                elif k == "arr_obj":
                    self.assertEqual(len(value), Entry.objects.filter(schema=ref_entity).count())
                    self.assertEqual(
                        sorted([x["value"] for x in value]),
                        sorted([x.name for x in Entry.objects.filter(schema=ref_entity)]),
                    )
                    self.assertEqual(
                        sorted([x["referral_id"] for x in value]),
                        sorted([x.id for x in Entry.objects.filter(schema=ref_entity)]),
                    )

                elif k == "arr_name":
                    self.assertEqual(len(value), Entry.objects.filter(schema=ref_entity).count())
                    self.assertEqual(
                        sorted([x["value"] for x in value]),
                        sorted([x.name for x in Entry.objects.filter(schema=ref_entity)]),
                    )
                    self.assertEqual(
                        sorted([x["referral_id"] for x in value]),
                        sorted([x.id for x in Entry.objects.filter(schema=ref_entity)]),
                    )
                    self.assertTrue(all([x["key"] == "hoge" for x in value]))

        # checks delete entry and checks deleted entry will also be removed from Elasticsearch
        entry = Entry.objects.filter(schema=entity).last()
        entry.delete()

        # Total count is one less than initial value.
        res = AdvancedSearchService.get_all_es_docs()
        self.assertEqual(res["hits"]["total"]["value"], ENTRY_COUNTS + 1)
        with self.assertRaises(NotFoundError):
            self._es.get(index=settings.ES_CONFIG["INDEX_NAME"], id=entry.id)

    def test_unregister_entry_to_elasticsearch(self):
        user = User.objects.create(username="hoge")

        # initialize Entity and Entry to test
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        # register entry information to the Elasticsearch
        entry.register_es()

        ret = AdvancedSearchService.search_entries(user, [entity.id], [])
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual(
            [x.entry for x in ret.ret_values],
            [{"name": entry.name, "id": entry.id}],
        )

        # unregister entry information from the Elasticsearch
        entry.unregister_es()

        ret = AdvancedSearchService.search_entries(user, [entity.id], [])
        self.assertEqual(ret.ret_count, 0)
        self.assertEqual(ret.ret_values, [])

    def test_update_elasticsearch_field(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="entity", created_user=user)
        entity_attr = EntityAttr.objects.create(
            name="attr",
            type=AttrType.STRING,
            created_user=user,
            parent_entity=entity,
        )

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        attr = entry.attrs.get(schema=entity_attr)
        attr.add_value(user, "hoge")

        # register entry to the Elasticsearch
        entry.register_es()

        # checks registered value is corrected
        res = self._es.get(index=settings.ES_CONFIG["INDEX_NAME"], id=entry.id)
        self.assertEqual(res["_source"]["attr"][0]["name"], entity_attr.name)
        self.assertEqual(res["_source"]["attr"][0]["type"], entity_attr.type)
        self.assertEqual(res["_source"]["attr"][0]["value"], "hoge")

        # update latest value of Attribute 'attr'
        attr.add_value(user, "fuga")
        entry.register_es()

        # checks registered value was also updated
        res = self._es.get(index=settings.ES_CONFIG["INDEX_NAME"], id=entry.id)
        self.assertEqual(res["_source"]["attr"][0]["value"], "fuga")

    def test_search_entries_from_elasticsearch(self):
        user = User.objects.create(username="hoge")

        entities = []
        for ename in ["eitnty1", "entity2"]:
            entity = Entity.objects.create(name=ename, created_user=user)

            entities.append(entity)
            for index in range(0, 2):
                EntityAttr.objects.create(
                    name="attr-%s" % index,
                    type=AttrType.STRING,
                    created_user=user,
                    parent_entity=entity,
                )

            EntityAttr.objects.create(
                name="ほげ",
                type=AttrType.STRING,
                created_user=user,
                parent_entity=entity,
            )

            EntityAttr.objects.create(
                name="attr-arr",
                type=AttrType.ARRAY_STRING,
                created_user=user,
                parent_entity=entity,
            )

            EntityAttr.objects.create(
                name="attr-date",
                type=AttrType.DATE,
                created_user=user,
                parent_entity=entity,
            )

        entry_info = {
            "entry1": {
                "attr-0": "2018/01/01",
                "attr-1": "bar",
                "ほげ": "ふが",
                "attr-date": date(2018, 1, 2),
                "attr-arr": ["hoge", "fuga"],
            },
            "entry2": {
                "attr-0": "hoge",
                "attr-1": "bar",
                "ほげ": "ふが",
                "attr-date": None,
                "attr-arr": ["2018/01/01"],
            },
            "entry3": {
                "attr-0": "0123-45-6789",  # This is date format but not date value
                "attr-1": "hoge",
                "ほげ": "fuga",
                "attr-date": None,
                "attr-arr": [],
            },
        }

        for entity in entities:
            for name, attrinfo in entry_info.items():
                entry = Entry.objects.create(name=name, schema=entity, created_user=user)
                entry.complement_attrs(user)

                for attr in entry.attrs.all():
                    attr.add_value(user, attrinfo[attr.schema.name])

                entry.register_es()

        # search entries of entity1 from Elasticsearch and checks that the entreis of non entity1
        # are not returned.
        resp = AdvancedSearchService.search_entries(
            user, [entities[0].id], [AttrHint(name="attr-0")]
        )
        self.assertEqual(resp.ret_count, 3)
        self.assertTrue(all([x.entity["id"] == entities[0].id for x in resp.ret_values]))

        # checks the value which is non date but date format was registered correctly
        self.assertEqual(
            [entry_info["entry3"]["attr-0"]],
            [x.attrs["attr-0"]["value"] for x in resp.ret_values if x.entry["name"] == "entry3"],
        )

        # checks ret_count counts number of entries whatever attribute contidion was changed
        resp = AdvancedSearchService.search_entries(
            user, [entities[0].id], [AttrHint(name="attr-0"), AttrHint(name="attr-1")]
        )
        self.assertEqual(resp.ret_count, 3)
        resp = AdvancedSearchService.search_entries(
            user, [entities[0].id, entities[1].id], [AttrHint(name="attr-0")]
        )
        self.assertEqual(resp.ret_count, 6)

        # checks results that contain multi-byte values could be got
        resp = AdvancedSearchService.search_entries(
            user, [entities[0].id], [AttrHint(name="ほげ", keyword="ふが")]
        )
        self.assertEqual(resp.ret_count, 2)
        self.assertEqual(
            sorted([x.entry["name"] for x in resp.ret_values]),
            sorted(["entry1", "entry2"]),
        )

        # search entries with date keyword parameter in string type from Elasticsearch
        resp = AdvancedSearchService.search_entries(
            user, [entities[0].id], [AttrHint(name="attr-0", keyword="2018/01/01")]
        )
        self.assertEqual(resp.ret_count, 1)
        self.assertEqual(resp.ret_values[0].entry["name"], "entry1")
        self.assertEqual(resp.ret_values[0].attrs["attr-0"]["value"], "2018/01/01")

        # search entries with date keyword parameter in date type from Elasticsearch
        for x in ["2018-01-02", "2018/01/02", "2018-1-2", "2018-01-2", "2018-1-02"]:
            resp = AdvancedSearchService.search_entries(
                user, [entities[0].id], [AttrHint(name="attr-date", keyword=x)]
            )
            self.assertEqual(resp.ret_count, 1)
            self.assertEqual(resp.ret_values[0].entry["name"], "entry1")
            self.assertEqual(resp.ret_values[0].attrs["attr-date"]["value"], "2018-01-02")

        # search entries with date keyword parameter in string array type from Elasticsearch
        resp = AdvancedSearchService.search_entries(
            user, [entities[0].id], [AttrHint(name="attr-arr", keyword="2018/01/01")]
        )
        self.assertEqual(resp.ret_count, 1)
        self.assertEqual(resp.ret_values[0].entry["name"], "entry2")
        self.assertEqual(resp.ret_values[0].attrs["attr-arr"]["value"], ["2018/01/01"])

        # search entries with keyword parameter that other entry has same value in untarget attr
        resp = AdvancedSearchService.search_entries(
            user, [entities[0].id], [AttrHint(name="attr-0", keyword="hoge")]
        )
        self.assertEqual(resp.ret_count, 1)
        self.assertEqual(resp.ret_values[0].entry["name"], "entry2")

        # search entries with keyword parameter which is array type
        resp = AdvancedSearchService.search_entries(
            user, [entities[0].id], [AttrHint(name="attr-arr", keyword="hoge")]
        )
        self.assertEqual(resp.ret_count, 1)
        self.assertEqual(resp.ret_values[0].entry["name"], "entry1")
        self.assertEqual(
            sorted(resp.ret_values[0].attrs["attr-arr"]["value"]),
            sorted(["hoge", "fuga"]),
        )

        # search entries with an invalid or unmatch date keyword parameter in date type
        # from Elasticsearch
        for x in ["2018/02/01", "hoge"]:
            resp = AdvancedSearchService.search_entries(
                user, [entities[0].id], [AttrHint(name="attr-date", keyword=x)]
            )
            self.assertEqual(resp.ret_count, 0)

    def test_search_result_count(self):
        """
        This tests that ret_count of search_entries will be equal with actual count of entries.
        """
        user = User.objects.create(username="hoge")

        ref_entity = Entity.objects.create(name="ref_entity", created_user=user)
        ref_entry = Entry.objects.create(name="ref", schema=ref_entity, created_user=user)

        entity = Entity.objects.create(name="entity", created_user=user)
        for name in ["foo", "bar"]:
            attr = EntityAttr.objects.create(
                name=name,
                type=AttrType.OBJECT,
                created_user=user,
                parent_entity=entity,
            )
            attr.referral.add(ref_entity)

        for i in range(0, 20):
            entry = Entry.objects.create(name="e%3d" % i, schema=entity, created_user=user)
            entry.complement_attrs(user)

            if i < 10:
                entry.attrs.get(schema__name="foo").add_value(user, ref_entry)
            else:
                entry.attrs.get(schema__name="bar").add_value(user, ref_entry)

            entry.register_es()

        resp = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name="foo", keyword="ref")], limit=5
        )
        self.assertEqual(resp.ret_count, 10)
        self.assertEqual(len(resp.ret_values), 5)

    def test_search_entities_have_individual_attrs(self):
        user = User.objects.create(username="hoge")

        entity_info = {"entity1": ["foo", "bar"], "entity2": ["bar", "hoge"]}

        entities = []
        for entity_name, attrnames in entity_info.items():
            entity = Entity.objects.create(name=entity_name, created_user=user)
            entities.append(entity.id)

            for attrname in attrnames:
                EntityAttr.objects.create(
                    name=attrname,
                    type=AttrType.STRING,
                    created_user=user,
                    parent_entity=entity,
                )

            # create entries for this entity
            for i in range(0, 5):
                e = Entry.objects.create(name="entry-%d" % i, created_user=user, schema=entity)
                e.register_es()

        resp = AdvancedSearchService.search_entries(user, entities, [AttrHint(name="foo")])
        self.assertEqual(resp.ret_count, 5)

        resp = AdvancedSearchService.search_entries(
            user, entities, [AttrHint(name=x) for x in ["foo", "hoge"]]
        )
        self.assertEqual(resp.ret_count, 10)

        resp = AdvancedSearchService.search_entries(
            user, entities, [AttrHint(name=x) for x in ["bar"]]
        )
        self.assertEqual(resp.ret_count, 10)
        for name in entity_info.keys():
            self.assertEqual(len([x for x in resp.ret_values if x.entity["name"] == name]), 5)

    def test_search_entries_sorted_result(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="EntityA", created_user=user)
        entity.save()

        # register AAA5, AAA0, AAA4, AAA1, AAA3, AAA2 in this order
        for i in range(3):
            e1 = Entry.objects.create(name="AAA%d" % (5 - i), schema=entity, created_user=user)
            e1.save()
            e1.register_es()

            e2 = Entry.objects.create(name="AAA%d" % i, schema=entity, created_user=user)
            e2.save()
            e2.register_es()

        # search
        resp = AdvancedSearchService.search_entries(user, [entity.id], entry_name="AAA")

        # 6 results should be returned
        self.assertEqual(resp.ret_count, 6)
        # 6 results should be sorted
        for i in range(6):
            self.assertEqual(resp.ret_values[i].entry["name"], "AAA%d" % i)

    def test_search_entries_with_date(self):
        user = User.objects.create(username="hoge")

        # initialize Entity
        entity = Entity.objects.create(name="entity", created_user=user)
        EntityAttr.objects.create(
            name="date",
            type=AttrType.DATE,
            created_user=user,
            parent_entity=entity,
        )

        # Initialize to create following Entries
        # (entry name) : (value in Attribute date)
        #   - entry-1  :  2018-01-01
        #   - entry-2  :  2018-02-01
        #   - entry-3  :  2018-03-01
        for month in range(1, 4):
            entry = Entry.objects.create(name="entry-%d" % month, schema=entity, created_user=user)
            entry.complement_attrs(user)

            attr = entry.attrs.first()
            attr.add_value(user, "2018-%02d-01" % month)

            entry.register_es()

        # search entry that have AttributeValue exact matches with specified date.
        ret = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name="date", keyword="2018/01/01")]
        )
        self.assertEqual(len(ret.ret_values), 1)
        self.assertEqual(ret.ret_values[0].entry["name"], "entry-1")

        # The case of using condition 'less thatn',
        # this expects that entry-2 and entry-3 are matched
        ret = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name="date", keyword=">2018-01-01")]
        )
        self.assertEqual(len(ret.ret_values), 2)
        self.assertEqual(
            sorted([x.entry["name"] for x in ret.ret_values]),
            ["entry-2", "entry-3"],
        )

        # The case of using condition 'greater thatn',
        # this expects that entry-1 and entry-2 are matched
        ret = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name="date", keyword="<2018-03-01")]
        )
        self.assertEqual(len(ret.ret_values), 2)
        self.assertEqual(
            sorted([x.entry["name"] for x in ret.ret_values]),
            ["entry-1", "entry-2"],
        )

        # The case of using both conditions, this expects that only entry-2 is matched
        ret = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name="date", keyword="<2018-03-01 >2018-01-01")]
        )
        self.assertEqual(len(ret.ret_values), 1)
        self.assertEqual(ret.ret_values[0].entry["name"], "entry-2")

        # The same case of before one, but date format of keyward was changed
        ret = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name="date", keyword="<2018/03/01 >2018/01/01")]
        )
        self.assertEqual(len(ret.ret_values), 1)
        self.assertEqual(ret.ret_values[0].entry["name"], "entry-2")

    def test_get_last_value(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="entity", created_user=user)
        for name in ["foo", "bar"]:
            EntityAttr.objects.create(
                name=name,
                type=AttrType.STRING,
                created_user=user,
                parent_entity=entity,
            )

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        # the case of creating default empty AttributeValue
        attr = entry.attrs.get(schema__name="foo")
        self.assertEqual(attr.values.count(), 0)

        attrv = attr.get_last_value()
        self.assertIsNotNone(attrv)
        self.assertEqual(attrv.value, "")
        self.assertEqual(attrv, attr.get_latest_value())
        self.assertEqual(attr.values.count(), 1)

        # the case of creating specified AttributeValue
        attr = entry.attrs.get(schema__name="bar")
        self.assertEqual(attr.values.count(), 0)

        attr.add_value(user, "hoge")
        attrv = attr.get_last_value()
        self.assertIsNotNone(attrv)
        self.assertEqual(attrv.value, "hoge")
        self.assertEqual(attrv, attr.get_latest_value())
        self.assertEqual(attr.values.count(), 1)

    def test_get_latest_value_with_readonly(self):
        user = User.objects.create(username="hoge")
        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        for entity_attr in entity.attrs.all():
            entry.add_attribute_from_base(entity_attr, user)

        for attr in entry.attrs.all():
            self.assertIsNone(attr.get_latest_value(is_readonly=True))

    def test_get_value_with_is_active_false(self):
        user = User.objects.create(username="hoge")
        entity = self.create_entity_with_all_type_attributes(user)

        # create referred Entity and Entries
        test_ref = Entry.objects.create(name="r0", schema=entity, created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        attr_info = [
            {"name": "obj", "set_val": str(test_ref.id), "exp_val": test_ref.name},
            {"name": "obj", "set_val": test_ref.id, "exp_val": test_ref.name},
            {"name": "obj", "set_val": test_ref, "exp_val": test_ref.name},
            {
                "name": "name",
                "set_val": {"name": "bar", "id": str(test_ref.id)},
                "exp_val": {"bar": test_ref.name},
            },
            {
                "name": "name",
                "set_val": {"name": "bar", "id": test_ref.id},
                "exp_val": {"bar": test_ref.name},
            },
            {
                "name": "name",
                "set_val": {"name": "bar", "id": test_ref},
                "exp_val": {"bar": test_ref.name},
            },
            {
                "name": "arr_obj",
                "set_val": [str(test_ref.id)],
                "exp_val": [test_ref.name],
            },
            {"name": "arr_obj", "set_val": [test_ref.id], "exp_val": [test_ref.name]},
            {"name": "arr_obj", "set_val": [test_ref], "exp_val": [test_ref.name]},
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": str(test_ref.id)}],
                "exp_val": [{"hoge": test_ref.name}],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": test_ref.id}],
                "exp_val": [{"hoge": test_ref.name}],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": test_ref}],
                "exp_val": [{"hoge": test_ref.name}],
            },
        ]

        for info in attr_info:
            attr = entry.attrs.get(name=info["name"])
            attr.add_value(user, info["set_val"])
            attrv = attr.get_latest_value()

            # test return value of get_value method
            self.assertEqual(attrv.get_value(is_active=False), info["exp_val"])

            # test return value of get_value method with 'with_metainfo' parameter
            expected_value = {"type": attr.schema.type, "value": info["exp_val"]}
            if attr.is_array():
                if attr.schema.type & AttrType._NAMED:
                    expected_value["value"] = [{"hoge": {"id": test_ref.id, "name": test_ref.name}}]
                elif attr.schema.type & AttrType.OBJECT:
                    expected_value["value"] = [{"id": test_ref.id, "name": test_ref.name}]
            elif attr.schema.type & AttrType._NAMED:
                expected_value["value"] = {"bar": {"id": test_ref.id, "name": test_ref.name}}
            elif attr.schema.type & AttrType.OBJECT:
                expected_value["value"] = {"id": test_ref.id, "name": test_ref.name}

            self.assertEqual(attrv.get_value(with_metainfo=True, is_active=False), expected_value)

    def test_get_value_deleted_entry_with_is_active_false(self):
        user = User.objects.create(username="hoge")
        entity = self.create_entity_with_all_type_attributes(user)

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        test_ref = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        attr_info = [
            {"name": "obj", "set_val": str(test_ref.id), "exp_val": test_ref.id},
            {"name": "obj", "set_val": test_ref.id, "exp_val": test_ref.id},
            {"name": "obj", "set_val": test_ref, "exp_val": test_ref.id},
            {
                "name": "arr_obj",
                "set_val": [str(test_ref.id)],
                "exp_val": [test_ref.id],
            },
            {"name": "arr_obj", "set_val": [test_ref.id], "exp_val": [test_ref.id]},
            {"name": "arr_obj", "set_val": [test_ref], "exp_val": [test_ref.id]},
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": str(test_ref.id)}],
                "exp_val": [{"hoge": test_ref.id}],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": test_ref.id}],
                "exp_val": [{"hoge": test_ref.id}],
            },
            {
                "name": "arr_name",
                "set_val": [{"name": "hoge", "id": test_ref.id}],
                "exp_val": [{"hoge": test_ref.id}],
            },
        ]

        for info in attr_info:
            attr = entry.attrs.get(name=info["name"])
            attr.add_value(user, info["set_val"])
            test_ref.delete()
            attrv = attr.get_latest_value()

            # test return value of get_value method with
            # 'with_metainfo, is_active=False' parameter

            expected_value = {"type": attr.schema.type, "value": info["exp_val"]}
            if attr.is_array():
                if attr.schema.type & AttrType._NAMED:
                    expected_value["value"] = [{"hoge": {"id": test_ref.id, "name": test_ref.name}}]
                elif attr.schema.type & AttrType.OBJECT:
                    expected_value["value"] = [{"id": test_ref.id, "name": test_ref.name}]
            elif attr.schema.type & AttrType._NAMED:
                expected_value["value"] = {"bar": {"id": test_ref.id, "name": test_ref.name}}
            elif attr.schema.type & AttrType.OBJECT:
                expected_value["value"] = {"id": test_ref.id, "name": test_ref.name}

            self.assertEqual(attrv.get_value(with_metainfo=True, is_active=False), expected_value)
            test_ref.restore()

    def test_add_to_attrv(self):
        user = User.objects.create(username="hoge")
        entity_ref = Entity.objects.create(name="Ref", created_user=user)
        entity = self.create_entity_with_all_type_attributes(user, entity_ref)

        # create test groups but g2 is deleted
        test_groups = [Group.objects.create(name=x) for x in ["g0", "g1", "g2-deleted"]]
        test_groups[2].delete()

        # initialize test entry
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry_refs = [
            Entry.objects.create(name="ref-%d" % i, schema=entity_ref, created_user=user)
            for i in range(2)
        ]

        set_attrinfo = [
            {"name": "arr_str", "value": ["foo"]},
            {"name": "arr_obj", "value": [entry_refs[0]]},
            {"name": "arr_name", "value": [{"id": entry_refs[0], "name": "foo"}]},
            {"name": "arr_group", "value": [test_groups[0]]},
        ]
        attrs = {}
        for info in set_attrinfo:
            attr = attrs[info["name"]] = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["value"])

        # test added invalid values
        attrs["arr_str"].add_to_attrv(user, value="")
        self.assertEqual(
            [x.value for x in attrs["arr_str"].get_latest_value().data_array.all()],
            ["foo"],
        )
        attrs["arr_obj"].add_to_attrv(user, referral=None)
        self.assertEqual(
            [x.referral for x in attrs["arr_obj"].get_latest_value().data_array.all()],
            [ACLBase.objects.get(id=entry_refs[0].id)],
        )
        attrs["arr_name"].add_to_attrv(user, value="", referral=None)
        self.assertEqual(
            [
                (x.value, x.referral.name)
                for x in attrs["arr_name"].get_latest_value().data_array.all()
            ],
            [("foo", "ref-0")],
        )
        attrs["arr_group"].add_to_attrv(user, value=test_groups[2])
        self.assertEqual(
            [x.group for x in attrs["arr_group"].get_latest_value().data_array.all()],
            [test_groups[0]],
        )

        # test append attrv
        attrs["arr_str"].add_to_attrv(user, value="bar")
        attrv = attrs["arr_str"].get_latest_value()
        self.assertEqual(attrv.data_array.count(), 2)
        self.assertEqual(sorted([x.value for x in attrv.data_array.all()]), sorted(["foo", "bar"]))

        attrs["arr_obj"].add_to_attrv(user, referral=entry_refs[1])
        attrv = attrs["arr_obj"].get_latest_value()
        self.assertEqual(attrv.data_array.count(), 2)
        self.assertEqual(
            sorted([x.referral.name for x in attrv.data_array.all()]),
            sorted(["ref-0", "ref-1"]),
        )

        attrs["arr_name"].add_to_attrv(user, referral=entry_refs[1], value="baz", boolean=True)
        attrv = attrs["arr_name"].get_latest_value()
        self.assertEqual(attrv.data_array.count(), 2)
        self.assertEqual(sorted([x.value for x in attrv.data_array.all()]), sorted(["foo", "baz"]))
        self.assertEqual(
            sorted([x.referral.name for x in attrv.data_array.all()]),
            sorted(["ref-0", "ref-1"]),
        )
        self.assertEqual([x.boolean for x in attrv.data_array.filter(value="baz")], [True])

        attrs["arr_group"].add_to_attrv(user, value=test_groups[1])
        self.assertEqual(
            [x.group for x in attrs["arr_group"].get_latest_value().data_array.all()],
            [test_groups[0], test_groups[1]],
        )

    def test_remove_from_attrv(self):
        user = User.objects.create(username="hoge")
        entity_ref = Entity.objects.create(name="Ref", created_user=user)
        entity = self.create_entity_with_all_type_attributes(user, entity_ref)

        # create test groups but g1 is deleted
        test_groups = [Group.objects.create(name=x) for x in ["g0", "g1", "g2-deleted"]]

        # initialize test entry
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry_refs = [
            Entry.objects.create(name="ref-%d" % i, schema=entity_ref, created_user=user)
            for i in range(2)
        ]

        set_attrinfo = [
            {"name": "arr_str", "value": ["foo", "bar"]},
            {"name": "arr_obj", "value": entry_refs},
            {
                "name": "arr_name",
                "value": [
                    {"id": entry_refs[0], "name": "foo"},
                    {"id": entry_refs[1], "name": "bar"},
                ],
            },
            {"name": "arr_group", "value": test_groups},
        ]
        attrs = {}
        for info in set_attrinfo:
            attr = attrs[info["name"]] = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["value"])

        # remove group2 after registering
        test_groups[2].delete()

        # test remove_from_attrv with invalid value
        attrs["arr_str"].remove_from_attrv(user, value=None)
        attrv = attrs["arr_str"].get_latest_value()
        self.assertEqual(sorted([x.value for x in attrv.data_array.all()]), sorted(["foo", "bar"]))

        attrs["arr_obj"].remove_from_attrv(user, referral=None)
        attrv = attrs["arr_obj"].get_latest_value()
        self.assertEqual(
            sorted([x.referral.name for x in attrv.data_array.all()]),
            sorted(["ref-0", "ref-1"]),
        )

        param_list = [
            {
                "referral": None,
                "value": "",
            },
            {
                "referral": entry_refs[0],
                "value": "",
            },
            {
                "referral": None,
                "value": "foo",
            },
        ]
        for param in param_list:
            attrs["arr_name"].remove_from_attrv(
                user, referral=param["referral"], value=param["value"]
            )
            attrv = attrs["arr_name"].get_latest_value()
            self.assertEqual(
                sorted([x.value for x in attrv.data_array.all()]), sorted(["foo", "bar"])
            )
            self.assertEqual(
                sorted([x.referral.name for x in attrv.data_array.all()]),
                sorted(["ref-0", "ref-1"]),
            )

        attrs["arr_group"].remove_from_attrv(user, value=None)
        self.assertEqual(
            [
                x.group
                for x in attrs["arr_group"]
                .get_latest_value()
                .data_array.all()
                .select_related("group")
            ],
            test_groups,
        )

        # test remove_from_attrv with valid value
        attrs["arr_str"].remove_from_attrv(user, value="foo")
        attrv = attrs["arr_str"].get_latest_value()
        self.assertEqual(sorted([x.value for x in attrv.data_array.all()]), sorted(["bar"]))

        attrs["arr_obj"].remove_from_attrv(user, referral=entry_refs[0])
        attrv = attrs["arr_obj"].get_latest_value()
        self.assertEqual(
            sorted([x.referral.name for x in attrv.data_array.all()]), sorted(["ref-1"])
        )

        attrs["arr_name"].remove_from_attrv(user, referral=entry_refs[0], value="foo")
        attrv = attrs["arr_name"].get_latest_value()
        self.assertEqual(sorted([x.value for x in attrv.data_array.all()]), sorted(["bar"]))
        self.assertEqual(
            sorted([x.referral.name for x in attrv.data_array.all()]), sorted(["ref-1"])
        )

        # This checks that both specified group and invalid groups are removed
        attrs["arr_group"].remove_from_attrv(user, value=test_groups[1])
        self.assertEqual(
            [
                x.group
                for x in attrs["arr_group"]
                .get_latest_value()
                .data_array.all()
                .select_related("group")
                if x.group and x.group.is_active
            ],
            [test_groups[0]],
        )

    def test_is_importable_data(self):
        check_data = [
            {"expect": False, "data": ["foo", "bar"]},
            {"expect": False, "data": "foo"},
            {"expect": False, "data": {"Entity": "hoge"}},
            {"expect": False, "data": {"Entity": ["hoge"]}},
            {"expect": False, "data": {"Entity": [{"attrs": {}}]}},
            {"expect": False, "data": {"Entity": [{"name": "entry"}]}},
            {
                "expect": False,
                "data": {"Entity": [{"attrs": {"foo": "bar"}, "name": 1234}]},
            },
            {
                "expect": False,
                "data": {"Entity": [{"attrs": ["foo", "bar"], "name": "entry"}]},
            },
            {
                "expect": True,
                "data": {"Entity": [{"attrs": {"foo": "bar"}, "name": "entry"}]},
            },
        ]
        for info in check_data:
            ret = Entry.is_importable_data(info["data"])

            self.assertEqual(ret, info["expect"])

    def test_restore_entry(self):
        entity = self.create_entity_with_all_type_attributes(self._user)
        ref_entry = Entry.objects.create(name="ref_entry", schema=entity, created_user=self._user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=self._user)
        entry.complement_attrs(self._user)

        attr = entry.attrs.get(schema__name="obj")
        attr.add_value(self._user, ref_entry)

        ref_entry.delete()
        ref_entry.restore()

        ref_entry.refresh_from_db()
        self.assertTrue(ref_entry.is_active)
        self.assertEqual(ref_entry.name, "ref_entry")
        self.assertTrue(all([attr.is_active for attr in ref_entry.attrs.all()]))

        ret = AdvancedSearchService.search_entries(self._user, [entity.id], [AttrHint(name="obj")])
        self.assertEqual(ret.ret_values[0].entry["name"], "entry")
        self.assertEqual(ret.ret_values[0].attrs["obj"]["value"]["name"], "ref_entry")
        self.assertEqual(ret.ret_values[1].entry["name"], "ref_entry")

    def test_restore_entry_in_chain(self):
        # initilaize referral Entries for checking processing caused
        # by setting 'is_delete_in_chain' flag
        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=self._user)
        ref_entries = [
            Entry.objects.create(name="ref-%d" % i, created_user=self._user, schema=ref_entity)
            for i in range(3)
        ]

        # initialize EntityAttrs
        attr_info = {
            "obj": {"type": AttrType.OBJECT, "value": ref_entries[0]},
            "arr_obj": {
                "type": AttrType.ARRAY_OBJECT,
                "value": ref_entries[1:],
            },
        }
        for attr_name, info in attr_info.items():
            # create EntityAttr object with is_delete_in_chain object
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                is_delete_in_chain=True,
                created_user=self._user,
                parent_entity=self._entity,
            )

            if info["type"] & AttrType.OBJECT:
                attr.referral.add(ref_entity)

        # initialize target entry
        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=self._user)
        entry.complement_attrs(self._user)

        for attr_name, info in attr_info.items():
            attr = entry.attrs.get(schema__name=attr_name)
            attr.add_value(self._user, info["value"])

        # delete target entry at first
        entry.delete()

        self.assertFalse(entry.is_active)
        self.assertTrue(entry.name.find("_deleted_") > 0)
        self.assertFalse(any([Entry.objects.get(id=x.id).is_active for x in ref_entries]))

        # restore target entry
        entry.restore()

        self.assertTrue(entry.is_active)
        self.assertEqual(entry.name.find("_deleted_"), -1)
        self.assertTrue(all([Entry.objects.get(id=x.id).is_active for x in ref_entries]))

    def test_to_dict_entry(self):
        user = User.objects.create(username="hoge")
        test_group = Group.objects.create(name="test-group")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)

        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        for info in self._get_attrinfo_template(ref_entry, test_group):
            attr = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["set_val"])

        # This checks all attribute values which are generated by entry.to_dict method
        ret_dict = entry.to_dict(user)
        expected_attrinfos = [
            {"name": "str", "value": "foo"},
            {"name": "text", "value": "bar"},
            {"name": "bool", "value": False},
            {"name": "arr_str", "value": ["foo", "bar", "baz"]},
            {"name": "date", "value": "2018-12-31"},
            {"name": "obj", "value": "r0"},
            {"name": "name", "value": {"bar": "r0"}},
            {"name": "arr_obj", "value": ["r0"]},
            {"name": "arr_name", "value": [{"hoge": "r0"}]},
            {"name": "group", "value": "test-group"},
            {"name": "arr_group", "value": ["test-group"]},
        ]
        for info in expected_attrinfos:
            self.assertEqual(
                [x["value"] for x in ret_dict["attrs"] if x["name"] == info["name"]],
                [info["value"]],
            )

    def test_to_dict_entry_with_metainfo_param(self):
        user = User.objects.create(username="hoge")
        test_group = Group.objects.create(name="test-group")
        test_role = Role.objects.create(name="test-role")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)

        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        for info in self._get_attrinfo_template(ref_entry, test_group, test_role):
            attr = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["set_val"])

        # This checks all attribute values which are generated by entry.to_dict method
        ret_dict = entry.to_dict(user, with_metainfo=True)
        expected_attrinfos = [
            {"name": "str", "value": {"type": AttrType.STRING, "value": "foo"}},
            {"name": "text", "value": {"type": AttrType.TEXT, "value": "bar"}},
            {
                "name": "bool",
                "value": {"type": AttrType.BOOLEAN, "value": False},
            },
            {
                "name": "date",
                "value": {"type": AttrType.DATE, "value": "2018-12-31"},
            },
            {
                "name": "arr_str",
                "value": {
                    "type": AttrType.ARRAY_STRING,
                    "value": ["foo", "bar", "baz"],
                },
            },
            {
                "name": "obj",
                "value": {
                    "type": AttrType.OBJECT,
                    "value": {"id": ref_entry.id, "name": ref_entry.name},
                },
            },
            {
                "name": "name",
                "value": {
                    "type": AttrType.NAMED_OBJECT,
                    "value": {"bar": {"id": ref_entry.id, "name": ref_entry.name}},
                },
            },
            {
                "name": "arr_obj",
                "value": {
                    "type": AttrType.ARRAY_OBJECT,
                    "value": [{"id": ref_entry.id, "name": ref_entry.name}],
                },
            },
            {
                "name": "arr_name",
                "value": {
                    "type": AttrType.ARRAY_NAMED_OBJECT,
                    "value": [{"hoge": {"id": ref_entry.id, "name": ref_entry.name}}],
                },
            },
            {
                "name": "group",
                "value": {
                    "type": AttrType.GROUP,
                    "value": {"id": test_group.id, "name": test_group.name},
                },
            },
            {
                "name": "arr_group",
                "value": {
                    "type": AttrType.ARRAY_GROUP,
                    "value": [{"id": test_group.id, "name": test_group.name}],
                },
            },
            {
                "name": "role",
                "value": {
                    "type": AttrType.ROLE,
                    "value": {"id": test_role.id, "name": test_role.name},
                },
            },
            {
                "name": "arr_role",
                "value": {
                    "type": AttrType.ARRAY_ROLE,
                    "value": [{"id": test_role.id, "name": test_role.name}],
                },
            },
            {
                "name": "datetime",
                "value": {"type": AttrType.DATETIME, "value": "2018-12-31T12:34:56+00:00"},
            },
        ]
        for info in expected_attrinfos:
            ret_attr_infos = [x for x in ret_dict["attrs"] if x["name"] == info["name"]]
            self.assertEqual(len(ret_attr_infos), 1)
            self.assertEqual(ret_attr_infos[0]["value"], info["value"])
            self.assertIn("id", ret_attr_infos[0])
            self.assertIn("schema_id", ret_attr_infos[0])

        # non attrv case
        entry = Entry.objects.create(name="non_attrv_entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        ret_dict = entry.to_dict(user, with_metainfo=True)
        expected_attrinfos = [
            {"name": "str", "value": {"type": AttrType.STRING, "value": ""}},
            {"name": "text", "value": {"type": AttrType.TEXT, "value": ""}},
            {
                "name": "bool",
                "value": {"type": AttrType.BOOLEAN, "value": False},
            },
            {
                "name": "date",
                "value": {"type": AttrType.DATE, "value": None},
            },
            {
                "name": "arr_str",
                "value": {
                    "type": AttrType.ARRAY_STRING,
                    "value": [],
                },
            },
            {
                "name": "obj",
                "value": {
                    "type": AttrType.OBJECT,
                    "value": None,
                },
            },
            {
                "name": "name",
                "value": {
                    "type": AttrType.NAMED_OBJECT,
                    "value": {"": None},
                },
            },
            {
                "name": "arr_obj",
                "value": {
                    "type": AttrType.ARRAY_OBJECT,
                    "value": [],
                },
            },
            {
                "name": "arr_name",
                "value": {
                    "type": AttrType.ARRAY_NAMED_OBJECT,
                    "value": [],
                },
            },
            {
                "name": "group",
                "value": {
                    "type": AttrType.GROUP,
                    "value": None,
                },
            },
            {
                "name": "arr_group",
                "value": {
                    "type": AttrType.ARRAY_GROUP,
                    "value": [],
                },
            },
            {
                "name": "role",
                "value": {
                    "type": AttrType.ROLE,
                    "value": None,
                },
            },
            {
                "name": "arr_role",
                "value": {
                    "type": AttrType.ARRAY_ROLE,
                    "value": [],
                },
            },
            {
                "name": "datetime",
                "value": {"type": AttrType.DATETIME, "value": None},
            },
        ]
        for info in expected_attrinfos:
            ret_attr_infos = [x for x in ret_dict["attrs"] if x["name"] == info["name"]]
            self.assertEqual(len(ret_attr_infos), 1)
            self.assertEqual(ret_attr_infos[0]["value"], info["value"])
            self.assertIn("id", ret_attr_infos[0])
            self.assertIn("schema_id", ret_attr_infos[0])

    def test_to_dict_entry_for_checking_permission(self):
        admin_user = User.objects.create(username="admin", is_superuser=True)

        private_entity = Entity.objects.create(
            name="private_entity", created_user=admin_user, is_public=False
        )
        public_entity = Entity.objects.create(name="public_entity", created_user=admin_user)

        attr_info = [
            {"name": "attr1", "is_public": True},
            {"name": "attr2", "is_public": False},
        ]
        for info in attr_info:
            [
                EntityAttr.objects.create(
                    **{
                        "type": AttrType.STRING,
                        "created_user": self._user,
                        "parent_entity": e,
                        "name": info["name"],
                        "is_public": info["is_public"],
                    }
                )
                for e in [private_entity, public_entity]
            ]

        # Initialize three kind of entries as below
        entry_info = [
            {"name": "e1", "schema": private_entity, "is_public": True},
            {"name": "e2", "schema": public_entity, "is_public": False},
            {"name": "e3", "schema": public_entity, "is_public": True},
        ]
        entries = [Entry.objects.create(created_user=admin_user, **info) for info in entry_info]
        for entry in entries:
            entry.complement_attrs(admin_user)

            for attr in entry.attrs.all():
                attr.add_value(admin_user, "hoge")

        # Test to_dict method of Entry
        self.assertIsNone(entries[0].to_dict(self._user))
        self.assertIsNone(entries[1].to_dict(self._user))
        self.assertEqual(
            entries[2].to_dict(self._user),
            {
                "id": entries[2].id,
                "name": entries[2].name,
                "entity": {"id": public_entity.id, "name": public_entity.name},
                "attrs": [
                    {
                        "id": entries[2].attrs.get(schema__name="attr1").id,
                        "schema_id": entries[2].attrs.get(schema__name="attr1").schema.id,
                        "name": "attr1",
                        "value": "hoge",
                    },
                ],
            },
        )

    def test_search_entries_blank_val(self):
        user = User.objects.create(username="hoge")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(
            name="referred_entry", schema=ref_entity, created_user=user
        )
        ref_group = Group.objects.create(name="group")

        attr_info = {
            "str": {"type": AttrType.STRING, "value": "foo-%d"},
            "str2": {"type": AttrType.STRING, "value": "foo-%d"},
            "obj": {"type": AttrType.OBJECT, "value": str(ref_entry.id)},
            "name": {
                "type": AttrType.NAMED_OBJECT,
                "value": {"name": "bar", "id": str(ref_entry.id)},
            },
            "bool": {"type": AttrType.BOOLEAN, "value": False},
            "group": {"type": AttrType.GROUP, "value": str(ref_group.id)},
            "date": {"type": AttrType.DATE, "value": date(2018, 12, 31)},
            "arr_str": {
                "type": AttrType.ARRAY_STRING,
                "value": ["foo", "bar", "baz"],
            },
            "arr_obj": {
                "type": AttrType.ARRAY_OBJECT,
                "value": [str(x.id) for x in Entry.objects.filter(schema=ref_entity)],
            },
            "arr_name": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "value": [{"name": "hoge", "id": str(ref_entry.id)}],
            },
        }

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )

            if info["type"] & AttrType.OBJECT:
                attr.referral.add(ref_entity)

        for index in range(0, 11):
            entry = Entry.objects.create(name="e-%d" % index, schema=entity, created_user=user)
            entry.complement_attrs(user)

            for attr_name, info in attr_info.items():
                attr = entry.attrs.get(name=attr_name)
                if attr_name == "str":
                    attr.add_value(user, info["value"] % index)
                elif attr_name == "str2":
                    attr.add_value(user, info["value"] % (index + 100))
                else:
                    attr.add_value(user, info["value"])

            entry.register_es()

        # search entries with blank values
        entry = Entry.objects.create(name="", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.register_es()

        ref_entry = Entry.objects.create(
            name=CONFIG.EMPTY_SEARCH_CHARACTER, schema=ref_entity, created_user=user
        )
        ref_group = Group.objects.create(name=CONFIG.EMPTY_SEARCH_CHARACTER)

        # search entries with blank values
        entry = Entry.objects.create(
            name=CONFIG.EMPTY_SEARCH_CHARACTER, schema=entity, created_user=user
        )
        entry.complement_attrs(user)

        # search entries with back slash
        attr_info = {
            "str": {
                "type": AttrType.STRING,
                "value": CONFIG.EMPTY_SEARCH_CHARACTER,
            },
            "str2": {
                "type": AttrType.STRING,
                "value": CONFIG.EMPTY_SEARCH_CHARACTER,
            },
            "obj": {"type": AttrType.OBJECT, "value": str(ref_entry.id)},
            "name": {
                "type": AttrType.NAMED_OBJECT,
                "value": {"name": "bar", "id": str(ref_entry.id)},
            },
            "bool": {"type": AttrType.BOOLEAN, "value": False},
            "group": {"type": AttrType.GROUP, "value": str(ref_group.id)},
            "date": {"type": AttrType.DATE, "value": date(2018, 12, 31)},
            "arr_str": {
                "type": AttrType.ARRAY_STRING,
                "value": [CONFIG.EMPTY_SEARCH_CHARACTER],
            },
            "arr_obj": {
                "type": AttrType.ARRAY_OBJECT,
                "value": [str(x.id) for x in Entry.objects.filter(schema=ref_entity)],
            },
            "arr_name": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "value": [{"name": "hoge", "id": str(ref_entry.id)}],
            },
        }

        for attr_name, info in attr_info.items():
            attr = entry.attrs.get(name=attr_name)
            attr.add_value(user, info["value"])

        entry.register_es()

        # search entries with empty_search_character
        for attr_name, info in attr_info.items():
            ret = AdvancedSearchService.search_entries(
                user,
                [entity.id],
                [AttrHint(name=attr_name, keyword=CONFIG.EMPTY_SEARCH_CHARACTER)],
            )
            if attr_name != "bool":
                self.assertEqual(ret.ret_count, 1)
            else:
                self.assertEqual(ret.ret_count, 0)

        # search entries with double_empty_search_character
        double_empty_search_character = (
            CONFIG.EMPTY_SEARCH_CHARACTER + CONFIG.EMPTY_SEARCH_CHARACTER
        )

        for attr_name, info in attr_info.items():
            ret = AdvancedSearchService.search_entries(
                user,
                [entity.id],
                [AttrHint(name=attr_name, keyword=double_empty_search_character)],
            )
            self.assertEqual(ret.ret_count, 0)

        # check functionallity of the 'entry_name' parameter
        ret = AdvancedSearchService.search_entries(
            user, [entity.id], entry_name=CONFIG.EMPTY_SEARCH_CHARACTER
        )
        self.assertEqual(ret.ret_count, 1)

        ret = AdvancedSearchService.search_entries(
            user, [entity.id], entry_name=double_empty_search_character
        )
        self.assertEqual(ret.ret_count, 0)

        # check combination of 'entry_name' and 'hint_attrs' parameter
        ret = AdvancedSearchService.search_entries(
            user,
            [entity.id],
            [AttrHint(name="str", keyword=CONFIG.EMPTY_SEARCH_CHARACTER)],
            entry_name=CONFIG.EMPTY_SEARCH_CHARACTER,
        )
        self.assertEqual(ret.ret_count, 1)

    def test_search_entries_includes_and_or(self):
        user = User.objects.create(username="hoge")

        attr_info = []
        """
        testdata1 str1:foo str2:blank str3:blank arr_str:['hoge']
        testdata2 str1:foo str2:bar str3:blank arr_str:['hoge', 'fuga']
        testdata3 str1:foo str2:bar str3:baz arr_str:['hoge', 'fuga', 'piyo']
        """
        attr_info.append(
            {
                "str1": {"type": AttrType.STRING, "value": "foo"},
                "str2": {"type": AttrType.STRING, "value": ""},
                "str3": {"type": AttrType.STRING, "value": ""},
                "arr_str": {"type": AttrType.ARRAY_STRING, "value": ["hoge"]},
            }
        )
        attr_info.append(
            {
                "str1": {"type": AttrType.STRING, "value": "foo"},
                "str2": {"type": AttrType.STRING, "value": "bar"},
                "str3": {"type": AttrType.STRING, "value": ""},
                "arr_str": {
                    "type": AttrType.ARRAY_STRING,
                    "value": ["hoge", "fuga"],
                },
            }
        )
        attr_info.append(
            {
                "str1": {"type": AttrType.STRING, "value": "foo"},
                "str2": {"type": AttrType.STRING, "value": "bar"},
                "str3": {"type": AttrType.STRING, "value": "baz"},
                "arr_str": {
                    "type": AttrType.ARRAY_STRING,
                    "value": ["hoge", "fuga", "piyo"],
                },
            }
        )

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name, info in attr_info[0].items():
            EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )

        for i, x in enumerate(attr_info):
            entry = Entry.objects.create(name="e-%s" % i, schema=entity, created_user=user)
            entry.complement_attrs(user)

            for attr_name, info in x.items():
                attr = entry.attrs.get(name=attr_name)
                attr.add_value(user, info["value"])

            entry.register_es()

        """
        Test case that contains only 'and'
        """
        test_suites = []
        test_suites.append(
            [
                {"ret_cnt": 3, "search_word": [AttrHint(name="str1", keyword="foo")]},
                {
                    "ret_cnt": 0,
                    "search_word": [
                        AttrHint(name="str1", keyword="foo&bar"),
                        AttrHint(name="str2", keyword="foo&bar"),
                    ],
                },
                {
                    "ret_cnt": 0,
                    "search_word": [
                        AttrHint(name="str1", keyword="foo&bar&baz"),
                        AttrHint(name="str2", keyword="foo&bar&baz"),
                        AttrHint(name="str3", keyword="foo&bar&baz"),
                    ],
                },
                {
                    "ret_cnt": 3,
                    "search_word": [AttrHint(name="arr_str", keyword="hoge")],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [AttrHint(name="arr_str", keyword="hoge&fuga")],
                },
                {
                    "ret_cnt": 1,
                    "search_word": [AttrHint(name="arr_str", keyword="hoge&fuga&piyo")],
                },
                {
                    "ret_cnt": 3,
                    "search_word": [
                        AttrHint(name="str1", keyword="foo"),
                        AttrHint(name="arr_str", keyword="hoge"),
                    ],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [
                        AttrHint(name="str1", keyword="foo"),
                        AttrHint(name="str2", keyword="bar"),
                        AttrHint(name="arr_str", keyword="hoge&fuga"),
                    ],
                },
                {
                    "ret_cnt": 1,
                    "search_word": [
                        AttrHint(name="str1", keyword="foo"),
                        AttrHint(name="str2", keyword="bar"),
                        AttrHint(name="arr_str", keyword="hoge&fuga&piyo"),
                    ],
                },
            ]
        )

        """
        Test case that contains only 'or'
        """
        test_suites.append(
            [
                {"ret_cnt": 3, "search_word": [AttrHint(name="str1", keyword="foo|bar")]},
                {
                    "ret_cnt": 1,
                    "search_word": [
                        AttrHint(name="str2", keyword="bar|baz"),
                        AttrHint(name="str3", keyword="bar|baz"),
                    ],
                },
                {
                    "ret_cnt": 1,
                    "search_word": [
                        AttrHint(name="str1", keyword="foo|bar|baz"),
                        AttrHint(name="str2", keyword="foo|bar|baz"),
                        AttrHint(name="str3", keyword="foo|bar|baz"),
                    ],
                },
                {
                    "ret_cnt": 3,
                    "search_word": [AttrHint(name="arr_str", keyword="hoge|fuga")],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [AttrHint(name="arr_str", keyword="fuga|piyo")],
                },
                {
                    "ret_cnt": 3,
                    "search_word": [AttrHint(name="arr_str", keyword="hoge|fuga|piyo")],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [
                        AttrHint(name="str2", keyword="foo|bar"),
                        AttrHint(name="arr_str", keyword="hoge"),
                    ],
                },
                {
                    "ret_cnt": 1,
                    "search_word": [
                        AttrHint(name="str2", keyword="foo|bar"),
                        AttrHint(name="str3", keyword="bar|baz"),
                        AttrHint(name="arr_str", keyword="hoge|fuga"),
                    ],
                },
                {
                    "ret_cnt": 1,
                    "search_word": [
                        AttrHint(name="str3", keyword="foo|baz"),
                        AttrHint(name="arr_str", keyword="hoge|fuga|piyo"),
                    ],
                },
            ]
        )

        """
        Test cases that contain 'and' and 'or'
        """
        test_suites.append(
            [
                {"ret_cnt": 3, "search_word": [AttrHint(name="str1", keyword="foo|bar")]},
                {
                    "ret_cnt": 0,
                    "search_word": [
                        AttrHint(name="str1", keyword="foo&baz|bar"),
                        AttrHint(name="str2", keyword="foo&baz|bar"),
                        AttrHint(name="str3", keyword="foo&baz|bar"),
                    ],
                },
                {
                    "ret_cnt": 0,
                    "search_word": [
                        AttrHint(name="str1", keyword="foo|bar&baz"),
                        AttrHint(name="str2", keyword="foo|bar&baz"),
                        AttrHint(name="str3", keyword="foo|bar&baz"),
                    ],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [AttrHint(name="arr_str", keyword="hoge&piyo|fuga")],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [AttrHint(name="arr_str", keyword="piyo|hoge&fuga")],
                },
                {
                    "ret_cnt": 2,
                    "search_word": [
                        AttrHint(name="str1", keyword="foo"),
                        AttrHint(name="str2", keyword="bar|baz"),
                        AttrHint(name="arr_str", keyword="hoge&piyo|fuga"),
                    ],
                },
            ]
        )

        for x in test_suites:
            for test_suite in x:
                ret = AdvancedSearchService.search_entries(
                    user, [entity.id], test_suite["search_word"]
                )
                self.assertEqual(ret.ret_count, test_suite["ret_cnt"])

    def test_search_entries_entry_name(self):
        user = User.objects.create(username="hoge")
        entity = Entity.objects.create(name="entity", created_user=user)

        """
        testdata1 entry_name:'foo'
        testdata2 entry_name:'bar'
        testdata3 entry_name:'barbaz'
        """
        for entry_name in ["foo", "bar", "barbaz"]:
            entry = Entry.objects.create(name=entry_name, schema=entity, created_user=user)
            entry.register_es()

        search_words = {"foo": 1, "bar&baz": 1, "foo|bar": 3, "foo|bar&baz": 2, "": 3}
        for word, count in search_words.items():
            ret = AdvancedSearchService.search_entries(user, [entity.id], entry_name=word)
            self.assertEqual(ret.ret_count, count)

    def test_search_entries_get_regex_pattern(self):
        user = User.objects.create(username="hoge")
        entity = Entity.objects.create(name="entity", created_user=user)

        add_chars = [
            "!",
            '"',
            "#",
            "$",
            "%",
            "'",
            "(",
            ")",
            "-",
            "=",
            "^",
            "~",
            "@",
            "`",
            "[",
            "]",
            "{",
            "}",
            ";",
            "+",
            ":",
            "*",
            ",",
            "<",
            ">",
            ".",
            "/",
            "?",
            "_",
            " ",
        ]
        test_suites = []
        for i, add_char in enumerate(add_chars):
            entry_name = "test%s%s" % (add_char, i)
            entry = Entry.objects.create(name=entry_name, schema=entity, created_user=user)
            entry.register_es()

            test_suites.append(
                {"search_word": entry_name, "ret_cnt": 1, "ret_entry_name": entry_name}
            )

        for test_suite in test_suites:
            ret = AdvancedSearchService.search_entries(
                user, [entity.id], entry_name=test_suite["search_word"]
            )
            self.assertEqual(ret.ret_count, test_suite["ret_cnt"])
            self.assertEqual(ret.ret_values[0].entry["name"], test_suite["ret_entry_name"])

    def test_search_entries_with_is_output_all(self):
        self._entry.attrs.first().add_value(self._user, "hoge")
        self._entry.register_es()
        ret = AdvancedSearchService.search_entries(
            self._user, [self._entity.id], is_output_all=True
        )
        self.assertEqual(
            ret.ret_values[0].attrs,
            {"attr": {"value": "hoge", "is_readable": True, "type": 2}},
        )

        ret = AdvancedSearchService.search_entries(
            self._user,
            [self._entity.id],
            [AttrHint(name="attr", keyword="^ge")],
            is_output_all=True,
        )
        self.assertEqual(ret.ret_count, 0)

        # multi entity case
        test_entity = self.create_entity(
            self._user, "test_entity", [{"name": "attr", "type": AttrType.STRING}]
        )
        self.add_entry(self._user, "test_entry", test_entity, {"attr": "fuga"})
        ret = AdvancedSearchService.search_entries(
            self._user, [self._entity.id, test_entity.id], is_output_all=True
        )
        self.assertEqual(
            ret.ret_values[0].attrs,
            {"attr": {"value": "hoge", "is_readable": True, "type": 2}},
        )
        self.assertEqual(
            ret.ret_values[1].attrs,
            {"attr": {"value": "fuga", "is_readable": True, "type": 2}},
        )

    def test_search_entries_with_offset(self):
        entities = []
        for i in range(3):
            entity = self.create_entity(
                self._user,
                "Entity%d" % i,
                [
                    {
                        "name": "test",
                        "type": AttrType.STRING,
                    }
                ],
            )
            entities.append(entity.id)
            for num in range(5):
                self.add_entry(self._user, "Entry%d" % num, entity)

        ret = AdvancedSearchService.search_entries(
            self._user, [entities[0]], [AttrHint(name="test")], limit=2, offset=2
        )
        self.assertEqual(ret.ret_count, 5)
        self.assertEqual(
            [{x.entity["name"]: x.entry["name"]} for x in ret.ret_values],
            [{"Entity0": "Entry2"}, {"Entity0": "Entry3"}],
        )

        ret = AdvancedSearchService.search_entries(
            self._user, entities, [AttrHint(name="test")], limit=2, offset=4
        )
        self.assertEqual(ret.ret_count, 15)
        self.assertEqual(
            [{x.entity["name"]: x.entry["name"]} for x in ret.ret_values],
            [{"Entity0": "Entry4"}, {"Entity1": "Entry0"}],
        )

    def test_get_es_document(self):
        user = User.objects.create(username="hoge")
        test_group = Group.objects.create(name="test-group")
        test_role = Role.objects.create(name="test-role")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(name="r0", schema=ref_entity, created_user=user)

        entity = self.create_entity_with_all_type_attributes(user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        for info in self._get_attrinfo_template(ref_entry, test_group, test_role):
            attr = entry.attrs.get(schema__name=info["name"])
            attr.add_value(user, info["set_val"])

        es_registering_value = entry.get_es_document()

        # this test value that will be registered in elasticsearch
        expected_values = {
            "str": {"key": [""], "value": ["foo"], "referral_id": [""]},
            "obj": {
                "key": [""],
                "value": [ref_entry.name],
                "referral_id": [ref_entry.id],
            },
            "text": {"key": [""], "value": ["bar"], "referral_id": [""]},
            "name": {
                "key": ["bar"],
                "value": [ref_entry.name],
                "referral_id": [ref_entry.id],
            },
            "bool": {"key": [""], "value": [False], "referral_id": [""]},
            "group": {
                "key": [""],
                "value": [test_group.name],
                "referral_id": [test_group.id],
            },
            "role": {
                "key": [""],
                "value": [test_role.name],
                "referral_id": [test_role.id],
            },
            "date": {
                "key": [""],
                "value": [""],
                "referral_id": [""],
                "date_value": ["2018-12-31"],
            },
            "arr_str": {
                "key": ["", "", ""],
                "value": ["foo", "bar", "baz"],
                "referral_id": ["", "", ""],
            },
            "arr_obj": {
                "key": [""],
                "value": [ref_entry.name],
                "referral_id": [ref_entry.id],
            },
            "arr_name": {
                "key": ["hoge"],
                "value": [ref_entry.name],
                "referral_id": [ref_entry.id],
            },
            "arr_group": {
                "key": [""],
                "value": [test_group.name],
                "referral_id": [test_group.id],
            },
            "arr_role": {
                "key": [""],
                "value": [test_role.name],
                "referral_id": [test_role.id],
            },
            "datetime": {
                "key": [""],
                "value": [""],
                "referral_id": [""],
                "date_value": ["2018-12-31T12:34:56+00:00"],
            },
            "num": {"key": [""], "value": [123.45], "referral_id": [""]},
            "arr_num": {
                "key": ["", "", "", ""],
                "value": [123.45, 67.89, 0.123, -45.67],
                "referral_id": ["", "", "", ""],
            },
        }
        # check all attributes are expected ones
        self.assertEqual(
            set([x["name"] for x in es_registering_value["attr"]]),
            set(expected_values.keys()),
        )

        # check all attribute contexts are expected ones
        for attrname, attrinfo in expected_values.items():
            attr = entry.attrs.get(schema__name=attrname)
            set_attrs = [x for x in es_registering_value["attr"] if x["name"] == attrname]

            self.assertTrue(all([x["type"] == attr.schema.type for x in set_attrs]))
            self.assertTrue(all([x["is_readable"] is True for x in set_attrs]))
            for param_name in ["key", "value", "referral_id", "date_value"]:
                if param_name in attrinfo:
                    self.assertEqual(
                        sorted([x[param_name] for x in set_attrs]),
                        sorted(attrinfo[param_name]),
                    )

    def test_get_es_document_without_attribute_value(self):
        entity = self.create_entity_with_all_type_attributes(self._user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=self._user)

        entry.register_es()
        result = AdvancedSearchService.search_entries(
            self._user, [entity.id], entry_name="entry", is_output_all=True
        )
        self.assertEqual(
            result.ret_values[0],
            AdvancedSearchResultRecord(
                entity={"id": entity.id, "name": "all_attr_entity"},
                entry={"id": entry.id, "name": "entry"},
                is_readable=True,
                attrs={
                    "bool": {"is_readable": True, "type": AttrType.BOOLEAN, "value": False},
                    "date": {
                        "is_readable": True,
                        "type": AttrType.DATE,
                        "value": None,
                    },
                    "group": {
                        "is_readable": True,
                        "type": AttrType.GROUP,
                        "value": {"id": "", "name": ""},
                    },
                    "role": {
                        "is_readable": True,
                        "type": AttrType.ROLE,
                        "value": {"id": "", "name": ""},
                    },
                    "name": {
                        "is_readable": True,
                        "type": AttrType.NAMED_OBJECT,
                        "value": {"": {"id": "", "name": ""}},
                    },
                    "obj": {
                        "is_readable": True,
                        "type": AttrType.OBJECT,
                        "value": {"id": "", "name": ""},
                    },
                    "str": {"is_readable": True, "type": AttrType.STRING, "value": ""},
                    "text": {"is_readable": True, "type": AttrType.TEXT, "value": ""},
                    "arr_str": {
                        "is_readable": True,
                        "type": AttrType.ARRAY_STRING,
                        "value": [],
                    },
                    "arr_obj": {
                        "is_readable": True,
                        "type": AttrType.ARRAY_OBJECT,
                        "value": [],
                    },
                    "arr_name": {
                        "is_readable": True,
                        "type": AttrType.ARRAY_NAMED_OBJECT,
                        "value": [],
                    },
                    "arr_group": {
                        "is_readable": True,
                        "type": AttrType.ARRAY_GROUP,
                        "value": [],
                    },
                    "arr_role": {
                        "is_readable": True,
                        "type": AttrType.ARRAY_ROLE,
                        "value": [],
                    },
                    "datetime": {
                        "is_readable": True,
                        "type": AttrType.DATETIME,
                        "value": None,
                    },
                    "num": {
                        "is_readable": True,
                        "type": AttrType.NUMBER,
                        "value": None,
                    },
                    "arr_num": {
                        "is_readable": True,
                        "type": AttrType.ARRAY_NUMBER,
                        "value": [],
                    },
                },
            ),
        )

        result = self._entry.get_es_document()
        self.assertEqual(
            result["attr"],
            [
                {
                    "name": self._attr.name,
                    "type": self._attr.schema.type,
                    "key": "",
                    "value": "",
                    "date_value": None,
                    "referral_id": "",
                    "is_readable": True,
                }
            ],
        )

    def test_get_es_document_when_referred_entry_was_deleted(self):
        # This entry refers self._entry which will be deleted later
        ref_entity = Entity.objects.create(name="", created_user=self._user)
        ref_attr = EntityAttr.objects.create(
            **{
                "name": "ref",
                "type": AttrType.OBJECT,
                "created_user": self._user,
                "parent_entity": ref_entity,
            }
        )
        ref_attr.referral.add(self._entity)

        ref_entry = Entry.objects.create(name="ref", schema=ref_entity, created_user=self._user)
        ref_entry.complement_attrs(self._user)

        ref_entry.attrs.first().add_value(self._user, self._entry)

        result = ref_entry.get_es_document()
        self.assertEqual(result["name"], ref_entry.name)
        self.assertEqual(
            result["attr"],
            [
                {
                    "name": ref_attr.name,
                    "type": ref_attr.type,
                    "key": "",
                    "value": self._entry.name,
                    "date_value": None,
                    "referral_id": self._entry.id,
                    "is_readable": True,
                }
            ],
        )

        # Delete an entry which is referred by ref_entry
        self._entry.delete()

        # Check result of query of ref_entry after referring entry is deleted.
        result = ref_entry.get_es_document()
        self.assertEqual(result["name"], ref_entry.name)
        self.assertEqual(
            result["attr"],
            [
                {
                    "name": ref_attr.name,
                    "type": ref_attr.type,
                    "key": "",
                    "value": "",  # expected not to have information about deleted entry
                    "date_value": None,
                    "referral_id": "",  # expected not to have information about deleted entry
                    "is_readable": True,
                }
            ],
        )

        # array_named_entry case
        self._entry.restore()
        ref_entity2 = Entity.objects.create(name="", created_user=self._user)
        ref_attr2 = EntityAttr.objects.create(
            **{
                "name": "ref_array_named_object",
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "created_user": self._user,
                "parent_entity": ref_entity2,
            }
        )
        ref_attr2.referral.add(self._entity)

        ref_entry2 = Entry.objects.create(name="ref2", schema=ref_entity2, created_user=self._user)
        ref_entry2.complement_attrs(self._user)
        ref_entry_attr2: Attribute = ref_entry2.attrs.get(schema__name="ref_array_named_object")
        ref_entry_attr2.add_value(
            self._user, [{"name": "hoge", "id": self._entry.id}, {"name": "fuga", "id": ""}]
        )

        result = ref_entry2.get_es_document()
        self.assertEqual(
            result["attr"],
            [
                {
                    "name": ref_attr2.name,
                    "type": ref_attr2.type,
                    "key": "hoge",
                    "value": self._entry.name,
                    "date_value": None,
                    "referral_id": self._entry.id,
                    "is_readable": True,
                },
                {
                    "name": ref_attr2.name,
                    "type": ref_attr2.type,
                    "key": "fuga",
                    "value": "",
                    "date_value": None,
                    "referral_id": "",
                    "is_readable": True,
                },
            ],
        )

        self._entry.delete()
        result = ref_entry2.get_es_document()
        self.assertEqual(
            result["attr"],
            [
                {
                    "name": ref_attr2.name,
                    "type": ref_attr2.type,
                    "key": "",
                    "value": "",
                    "date_value": None,
                    "referral_id": "",
                    "is_readable": True,
                },
                {
                    "name": ref_attr2.name,
                    "type": ref_attr2.type,
                    "key": "fuga",
                    "value": "",
                    "date_value": None,
                    "referral_id": "",
                    "is_readable": True,
                },
            ],
        )
