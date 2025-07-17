import logging
from datetime import date, datetime, timezone

from django.conf import settings

from airone.lib.elasticsearch import AttrHint, EntryFilterKey, EntryHint, FilterKey
from airone.lib.log import Logger
from airone.lib.test import AironeTestCase
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.models import Attribute, Entry
from entry.services import AdvancedSearchService
from entry.settings import CONFIG
from group.models import Group
from role.models import Role
from user.models import User


class AdvancedSearchServiceTest(AironeTestCase):
    def setUp(self):
        super(AdvancedSearchServiceTest, self).setUp()

        self._user: User = User(username="test")
        self._user.save()

        self._entity: Entity = Entity(name="entity", created_user=self._user)
        self._entity.save()

        self._entry: Entry = Entry(name="entry", created_user=self._user, schema=self._entity)
        self._entry.save()

        self._attr: Attribute = self.make_attr("attr")
        self._attr.save()

        # make auto complement user
        self._complement_user: User = User(
            username=settings.AIRONE["AUTO_COMPLEMENT_USER"],
            email="hoge@example.com",
            is_superuser=True,
        )
        self._complement_user.set_password(settings.AIRONE["AUTO_COMPLEMENT_USER"])
        self._complement_user.save()

    def create_entity_with_all_type_attributes(
        self, user: User, ref_entity: Entity | None = None
    ) -> Entity:
        """
        This is a test helper method to add attributes of all attribute-types
        to specified entity.
        """
        entity = Entity.objects.create(name="all_attr_entity", created_user=user)
        attr_info = {
            "str": AttrType.STRING,
            "text": AttrType.TEXT,
            "obj": AttrType.OBJECT,
            "name": AttrType.NAMED_OBJECT,
            "bool": AttrType.BOOLEAN,
            "group": AttrType.GROUP,
            "date": AttrType.DATE,
            "role": AttrType.ROLE,
            "num": AttrType.NUMBER,
            "datetime": AttrType.DATETIME,
            "arr_str": AttrType.ARRAY_STRING,
            "arr_obj": AttrType.ARRAY_OBJECT,
            "arr_name": AttrType.ARRAY_NAMED_OBJECT,
            "arr_group": AttrType.ARRAY_GROUP,
            "arr_role": AttrType.ARRAY_ROLE,
        }
        for attr_name, attr_type in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name, type=attr_type, created_user=user, parent_entity=entity
            )

            if attr_type & AttrType.OBJECT and ref_entity:
                attr.referral.add(ref_entity)

            entity.attrs.add(attr)

        return entity

    def make_attr(
        self,
        name: str,
        attrtype: AttrType = AttrType.STRING,
        user: User | None = None,
        entity: Entity | None = None,
        entry: Entry | None = None,
    ) -> Attribute:
        entity_attr = EntityAttr.objects.create(
            name=name,
            type=attrtype,
            created_user=(user and user or self._user),
            parent_entity=(entity and entity or self._entity),
        )

        return Attribute.objects.create(
            name=name,
            schema=entity_attr,
            created_user=(user and user or self._user),
            parent_entry=(entry and entry or self._entry),
        )

    def test_search_entries(self):
        user = User.objects.create(username="hoge")

        # create referred Entity and Entries
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        ref_entry = Entry.objects.create(
            name="referred_entry", schema=ref_entity, created_user=user
        )
        ref_group = Group.objects.create(name="group")
        ref_role = Role.objects.create(name="role")

        attr_info = {
            "str": {"type": AttrType.STRING, "value": "foo-%d"},
            "str2": {"type": AttrType.STRING, "value": "foo-%d"},
            "obj": {"type": AttrType.OBJECT, "value": str(ref_entry.id)},
            "name": {
                "type": AttrType.NAMED_OBJECT,
                "value": {"name": "bar", "id": str(ref_entry.id)},
            },
            "bool": {"type": AttrType.BOOLEAN, "value": True},
            "group": {"type": AttrType.GROUP, "value": str(ref_group.id)},
            "date": {"type": AttrType.DATE, "value": date(2018, 12, 31)},
            "role": {"type": AttrType.ROLE, "value": str(ref_role.id)},
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
            "arr_group": {"type": AttrType.ARRAY_GROUP, "value": [ref_group]},
            "arr_role": {"type": AttrType.ARRAY_ROLE, "value": [ref_role]},
            "datetime": {
                "type": AttrType.DATETIME,
                "value": datetime(2018, 12, 31, 12, 34, 56, tzinfo=timezone.utc),
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

            entity.attrs.add(attr)

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

        # search entries
        ret = AdvancedSearchService.search_entries(
            user,
            [entity.id],
            [
                AttrHint(name="str"),
                AttrHint(name="str2"),
                AttrHint(name="obj"),
                AttrHint(name="name"),
                AttrHint(name="bool"),
                AttrHint(name="group"),
                AttrHint(name="date"),
                AttrHint(name="role"),
                AttrHint(name="arr_str"),
                AttrHint(name="arr_obj"),
                AttrHint(name="arr_name"),
                AttrHint(name="arr_group"),
                AttrHint(name="arr_role"),
                AttrHint(name="datetime"),
            ],
        )
        self.assertEqual(ret.ret_count, 11)
        self.assertEqual(len(ret.ret_values), 11)

        # check returned contents is corrected
        for v in ret.ret_values:
            self.assertEqual(v.entity["id"], entity.id)
            self.assertEqual(len(v.attrs), len(attr_info))

            entry = Entry.objects.get(id=v.entry["id"])

            for attrname, attrinfo in v.attrs.items():
                attr = entry.attrs.get(schema__name=attrname)
                attrv = attr.get_latest_value()

                # checks accurate type parameters are stored
                self.assertEqual(attrinfo["type"], attrv.data_type)

                # checks accurate values are stored
                if attrname == "str" or attrname == "str2":
                    self.assertEqual(attrinfo["value"], attrv.value)

                elif attrname == "obj":
                    self.assertEqual(attrinfo["value"]["id"], attrv.referral.id)
                    self.assertEqual(attrinfo["value"]["name"], attrv.referral.name)

                elif attrname == "name":
                    key = attrv.value
                    self.assertEqual(attrinfo["value"][key]["id"], attrv.referral.id)
                    self.assertEqual(attrinfo["value"][key]["name"], attrv.referral.name)

                elif attrname == "bool":
                    self.assertEqual(attrinfo["value"], attrv.boolean)

                elif attrname == "date":
                    self.assertEqual(attrinfo["value"], str(attrv.date))

                elif attrname == "group":
                    self.assertEqual(attrinfo["value"]["id"], attrv.group.id)
                    self.assertEqual(attrinfo["value"]["name"], attrv.group.name)

                elif attrname == "role":
                    self.assertEqual(attrinfo["value"]["id"], attrv.role.id)
                    self.assertEqual(attrinfo["value"]["name"], attrv.role.name)

                elif attrname == "arr_str":
                    self.assertEqual(
                        sorted([x for x in attrinfo["value"]]),
                        sorted([x.value for x in attrv.data_array.all()]),
                    )

                elif attrname == "arr_obj":
                    self.assertEqual(
                        [x["id"] for x in attrinfo["value"]],
                        [x.referral.id for x in attrv.data_array.all()],
                    )
                    self.assertEqual(
                        [x["name"] for x in attrinfo["value"]],
                        [x.referral.name for x in attrv.data_array.all()],
                    )

                elif attrname == "arr_name":
                    for co_attrv in attrv.data_array.all():
                        _co_v = [x[co_attrv.value] for x in attrinfo["value"]]
                        self.assertTrue(_co_v)
                        self.assertEqual(_co_v[0]["id"], co_attrv.referral.id)
                        self.assertEqual(_co_v[0]["name"], co_attrv.referral.name)

                elif attrname == "arr_group":
                    self.assertEqual(
                        attrinfo["value"],
                        [{"id": ref_group.id, "name": ref_group.name}],
                    )

                elif attrname == "arr_role":
                    self.assertEqual(
                        attrinfo["value"],
                        [{"id": ref_role.id, "name": ref_role.name}],
                    )

                elif attrname == "datetime":
                    self.assertEqual(attrinfo["value"], attrv.datetime.isoformat())

                else:
                    raise "Invalid result was happend (attrname: %s)" % attrname

        # search entries with maximum entries to get
        ret = AdvancedSearchService.search_entries(user, [entity.id], [AttrHint(name="str")], 5)
        self.assertEqual(ret.ret_count, 11)
        self.assertEqual(len(ret.ret_values), 5)

        # search entries with keyword
        ret = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name="str", keyword="foo-5")]
        )
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual(ret.ret_values[0].entry["name"], "e-5")

        # search entries with keyword for Role Attribute
        for role_attrname in ["role", "arr_role"]:
            # call AdvancedSearchService.search_entries with invalid keyword
            self.assertEqual(
                AdvancedSearchService.search_entries(
                    user, [entity.id], [AttrHint(name="role", keyword="invalid-keyword")]
                ).ret_count,
                0,
            )
            # call AdvancedSearchService.search_entries with valid keyword
            self.assertEqual(
                AdvancedSearchService.search_entries(
                    user, [entity.id], [AttrHint(name="role", keyword="role")]
                ).ret_count,
                11,
            )

        # search entries with blank values
        entry = Entry.objects.create(name="entry-blank", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.register_es()

        for attrname in attr_info.keys():
            ret = AdvancedSearchService.search_entries(user, [entity.id], [AttrHint(name=attrname)])
            self.assertEqual(len([x for x in ret.ret_values if x.entry["id"] == entry.id]), 1)

        # check functionallity of the 'exact_match' parameter
        ret = AdvancedSearchService.search_entries(
            user,
            [entity.id],
            [AttrHint(name="str", keyword="foo-1")],
        )
        self.assertEqual(ret.ret_count, 2)
        ret = AdvancedSearchService.search_entries(
            user,
            [entity.id],
            [AttrHint(name="str", keyword="foo-1", exact_match=True)],
        )
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual(ret.ret_values[0].entry["name"], "e-1")

        # check functionallity of the 'entry_name' parameter
        ret = AdvancedSearchService.search_entries(user, [entity.id], entry_name="e-1")
        self.assertEqual(ret.ret_count, 2)

        # check combination of 'entry_name' and 'hint_attrs' parameter
        ret = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name="str", keyword="foo-10")], entry_name="e-1"
        )
        self.assertEqual(ret.ret_count, 1)

        # check whether keyword would be insensitive case
        ret = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name="str", keyword="FOO-10")]
        )
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual(ret.ret_values[0].entry["name"], "e-10")

        def _assert_result_full(attr, result):
            if attr.type != AttrType.BOOLEAN:
                # confirm "entry-black" Entry, which doesn't have any substantial Attribute values,
                # doesn't exist on the result.
                isin_entry_blank = any(
                    [x.entry["name"] == "entry-blank" for x in result.ret_values]
                )
                self.assertFalse(isin_entry_blank)

                # confirm Entries, which have substantial Attribute values, are returned
                self.assertEqual(result.ret_count, 11)

            else:
                # both True and False value will be matched for boolean type Attribute
                self.assertEqual(result.ret_count, 12)

        # check to get Entries that only have substantial Attribute values
        for attr in entity.attrs.filter(is_active=True):
            result = AdvancedSearchService.search_entries(
                user, [entity.id], [AttrHint(name=attr.name, keyword="*")]
            )
            _assert_result_full(attr, result)

        # check to get Entries that only have substantial Attribute values with filter_key
        for attr in entity.attrs.filter(is_active=True):
            result = AdvancedSearchService.search_entries(
                user,
                [entity.id],
                [
                    AttrHint(
                        name=attr.name,
                        keyword="*",
                        filter_key=FilterKey.TEXT_CONTAINED,
                    )
                ],
            )
            _assert_result_full(attr, result)

        # check to get Entries that only have substantial Attribute values
        # with filter_key instead of keyword
        for attr in entity.attrs.filter(is_active=True):
            result = AdvancedSearchService.search_entries(
                user,
                [entity.id],
                [AttrHint(name=attr.name, filter_key=FilterKey.NON_EMPTY)],
            )
            _assert_result_full(attr, result)

        # check to get Entries that have empty Attribute values with filter_key instead of keyword
        for attr in entity.attrs.filter(is_active=True):
            result = AdvancedSearchService.search_entries(
                user,
                [entity.id],
                [AttrHint(name=attr.name, filter_key=FilterKey.EMPTY)],
            )
            if attr.type == AttrType.BOOLEAN:
                self.assertEqual(result.ret_count, 0)
            else:
                self.assertEqual(result.ret_count, 1)
                self.assertEqual(result.ret_values[0].entry["name"], "entry-blank")

        # check to get Entries with the "CLEARED" filter_key and keyword
        for attr in entity.attrs.filter(is_active=True):
            result = AdvancedSearchService.search_entries(
                user,
                [entity.id],
                [
                    AttrHint(
                        name=attr.name, keyword="DO MATCH NOTHING", filter_key=FilterKey.CLEARED
                    )
                ],
            )

            # This expect to match anything
            self.assertEqual(
                result.ret_count, Entry.objects.filter(schema=entity, is_active=True).count()
            )

    def test_search_entries_with_duplicated_filter_key(self):
        entity = self.create_entity_with_all_type_attributes(self._user)

        # create Entries that have duplicated value at "str" attribute
        [self.add_entry(self._user, "dup-%s" % i, entity, values={"str": "hoge"}) for i in range(2)]
        [
            self.add_entry(self._user, "dup-%s" % i, entity, values={"str": "fuga"})
            for i in range(2, 4)
        ]

        # create Entries that don't have duplicated value at "str" attribute
        [
            self.add_entry(self._user, "non-dup-%d" % i, entity, values={"str": "fuga-%d" % i})
            for i in range(2)
        ]

        # create Entries that have empty value
        [self.add_entry(self._user, "empty-%d" % i, entity, values={"str": ""}) for i in range(2)]

        result = AdvancedSearchService.search_entries(
            self._user,
            [entity.id],
            [
                AttrHint(
                    name="str",
                    filter_key=FilterKey.DUPLICATED,
                )
            ],
        )
        self.assertEqual(result.ret_count, 4)
        self.assertEqual(
            [x.entry["name"] for x in result.ret_values], ["dup-%s" % i for i in range(4)]
        )

    def test_search_entries_with_duplicated_filter_key_without_duplicated_item(self):
        entity = self.create_entity_with_all_type_attributes(self._user)

        self.add_entry(self._user, "entry1", entity, values={"str": ""})
        self.add_entry(self._user, "entry2", entity, values={"str": "hoge"})
        self.add_entry(self._user, "entry3", entity, values={"str": "fuga"})

        result = AdvancedSearchService.search_entries(
            self._user,
            [entity.id],
            [
                AttrHint(
                    name="str",
                    filter_key=FilterKey.DUPLICATED,
                )
            ],
        )
        self.assertEqual(result.ret_count, 0)

    def test_search_entries_with_text_not_contained_filter_key(self):
        entity = self.create_entity_with_all_type_attributes(self._user)

        # some entries have "hoge" or "fuga" attribute value
        [
            self.add_entry(self._user, "hoge-%s" % i, entity, values={"str": "hoge"})
            for i in range(3)
        ]
        [
            self.add_entry(self._user, "fuga-%s" % i, entity, values={"str": "fuga"})
            for i in range(2)
        ]

        # filter entries have "hoge"
        result = AdvancedSearchService.search_entries(
            self._user,
            [entity.id],
            [
                AttrHint(
                    name="str",
                    keyword="hoge",
                    filter_key=FilterKey.TEXT_NOT_CONTAINED,
                )
            ],
        )

        # check the result contains only entries don't have "hoge"
        self.assertEqual(result.ret_count, 2)
        self.assertEqual(
            [x.entry["name"] for x in result.ret_values], ["fuga-%s" % i for i in range(2)]
        )

    def test_search_entries_with_hint_referral_entity(self):
        user = User.objects.create(username="hoge")

        # Initialize Entities and Entries which will be used in this test
        ref_entity = self.create_entity(user, "Ref Entity")
        ref_entry = self.add_entry(user, "Ref", ref_entity)
        entity = self.create_entity(
            user,
            "Entity",
            attrs=[
                {
                    "name": "ref",
                    "type": AttrType.OBJECT,
                }
            ],
        )
        self.add_entry(user, "Entry", entity, values={"ref": ref_entry})

        # get Entries that refer Entry which belongs to specified Entity
        result = AdvancedSearchService.search_entries(
            user,
            [x.id for x in Entity.objects.filter(is_active=True)],
            hint_referral_entity_id=entity.id,
        )
        self.assertEqual(result.ret_count, 1)
        self.assertEqual(result.ret_values[0].entry["id"], ref_entry.id)

    def test_search_entries_with_hint_referral(self):
        user = User.objects.create(username="hoge")

        # Initialize entities -- there are 2 entities as below
        # * ReferredEntity - has no attribute
        # * Entity - has an attribute that refers ReferredEntity
        ref_entity = Entity.objects.create(name="Referred Entity", created_user=user)
        entity = Entity.objects.create(name="Entity", created_user=user)
        entity_attr = EntityAttr.objects.create(
            name="attr_ref",
            type=AttrType.OBJECT,
            created_user=user,
            parent_entity=entity,
        )
        entity_attr.referral.add(ref_entity)
        entity.attrs.add(entity_attr)

        # Initialize entries as below
        ref_entries = [
            Entry.objects.create(name="ref%d" % i, schema=ref_entity, created_user=user)
            for i in range(3)
        ]
        for index in range(10):
            entry = Entry.objects.create(name="e-%d" % index, schema=entity, created_user=user)
            entry.complement_attrs(user)

            # set referral entry (ref0, ref1) alternately
            entry.attrs.first().add_value(user, ref_entries[index % 2])

        for ref_entry in ref_entries:
            ref_entry.register_es()

        # call search_entries with 'hint_referral' parameter,
        # then checks that result includes referral entries
        ret = AdvancedSearchService.search_entries(user, [ref_entity.id], [], hint_referral="")
        self.assertEqual(ret.ret_count, 3)
        self.assertEqual(
            sorted([x["id"] for x in ret.ret_values[0].referrals]),
            sorted([x.id for x in ref_entries[0].get_referred_objects()]),
        )

        # call search_entries with 'hint_referral',
        ret = AdvancedSearchService.search_entries(user, [ref_entity.id], [], hint_referral="e-")
        self.assertEqual(ret.ret_count, 2)

        # call search_entries with 'hint_referral' parameter as string,
        # then checks that result includes referral entries that match specified referral name
        ret = AdvancedSearchService.search_entries(user, [ref_entity.id], [], hint_referral="e-1")
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual([x.entry["name"] for x in ret.ret_values], ["ref1"])

        # call search_entries with 'hint_referral' parameter as name of entry
        # which is not referred from any entries.
        ret = AdvancedSearchService.search_entries(
            user, [ref_entity.id], [], hint_referral="hogefuga"
        )
        self.assertEqual(ret.ret_count, 0)

        # call search_entries with 'backslash' in the 'hint_referral' parameter as entry of name
        ret = AdvancedSearchService.search_entries(
            user, [ref_entity.id], [], hint_referral=CONFIG.EMPTY_SEARCH_CHARACTER
        )
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual([x.entry["name"] for x in ret.ret_values], ["ref2"])

        # call search_entries with 'asterisk' in the 'hint_referral' parameter as entry of name
        ret = AdvancedSearchService.search_entries(
            user, [ref_entity.id], [], hint_referral=CONFIG.EXSIT_CHARACTER
        )
        self.assertEqual(ret.ret_count, 2)

    def test_search_entries_with_exclusive_attrs(self):
        user = User.objects.create(username="hoge")
        entity_info = {
            "E1": [{"type": AttrType.STRING, "name": "foo"}],
            "E2": [{"type": AttrType.STRING, "name": "bar"}],
        }

        entity_ids = []
        for name, attrinfos in entity_info.items():
            entity = Entity.objects.create(name=name, created_user=user)
            entity_ids.append(entity.id)

            for attrinfo in attrinfos:
                entity.attrs.add(
                    EntityAttr.objects.create(
                        **{
                            "name": attrinfo["name"],
                            "type": attrinfo["type"],
                            "created_user": user,
                            "parent_entity": entity,
                        }
                    )
                )

            for i in [x for x in range(0, 5)]:
                entry = Entry.objects.create(
                    name="%s-%d" % (entity.name, i), schema=entity, created_user=user
                )
                entry.complement_attrs(user)

                for attrinfo in attrinfos:
                    attr = entry.attrs.get(schema__name=attrinfo["name"])
                    attr.add_value(user, str(i))

                entry.register_es()

        # search entries by only attribute name and keyword without entity with exclusive attrs
        ret = AdvancedSearchService.search_entries(
            user,
            entity_ids,
            [AttrHint(name="foo", keyword=""), AttrHint(name="bar", keyword="")],
        )
        self.assertEqual(ret.ret_count, 10)
        self.assertEqual(
            sorted([x.entry["name"] for x in ret.ret_values]),
            sorted(["E1-%d" % i for i in range(5)] + ["E2-%d" % i for i in range(5)]),
        )

        # search entries by only attribute name and keyword without entity
        # with exclusive attrs and one keyword
        ret = AdvancedSearchService.search_entries(
            user,
            entity_ids,
            [AttrHint(name="foo", keyword="3"), AttrHint(name="bar", keyword="")],
        )
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual(sorted([x.entry["name"] for x in ret.ret_values]), sorted(["E1-3"]))

        # search entries by only attribute name and keyword without entity
        # with exclusive hint attrs and keywords
        ret = AdvancedSearchService.search_entries(
            user,
            entity_ids,
            [AttrHint(name="foo", keyword="3"), AttrHint(name="bar", keyword="3")],
        )
        self.assertEqual(ret.ret_count, 0)

    def test_search_entries_about_insensitive_case(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="Entity", created_user=user)
        entry = Entry.objects.create(name="Foo", schema=entity, created_user=user)
        entry.register_es()

        # This checks entry_name parameter would be insensitive case
        for name in ["foo", "fOO", "OO", "f"]:
            resp = AdvancedSearchService.search_entries(user, [entity.id], entry_name=name)
            self.assertEqual(resp.ret_count, 1)
            self.assertEqual(resp.ret_values[0].entry["id"], entry.id)

    def test_search_entries_with_deleted_hint(self):
        # This call search_entries with hint_attrs that contains values which specify
        # entry name that has already deleted.

        # Initialize entities -- there are 2 entities as below
        # * ReferredEntity - has no attribute
        # * Entity - has an attribute that refers ReferredEntity
        ref_entity = Entity.objects.create(name="ReferredEntity", created_user=self._user)
        ref_entries = [
            Entry.objects.create(name="ref-%d" % i, schema=ref_entity, created_user=self._user)
            for i in range(4)
        ]

        entity = Entity.objects.create(name="Entity", created_user=self._user)
        ref_info = {
            "ref": {
                "type": AttrType.OBJECT,
                "value": ref_entries[0],
                "expected_value": {"name": "", "id": ""},
            },
            "name": {
                "type": AttrType.NAMED_OBJECT,
                "value": {"name": "hoge", "id": ref_entries[1]},
                "expected_value": {"hoge": {"name": "", "id": ""}},
            },
            "arr_ref": {
                "type": AttrType.ARRAY_OBJECT,
                "value": [ref_entries[2]],
                "expected_value": [],
            },
            "arr_name": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "value": [{"name": "hoge", "id": ref_entries[3]}],
                "expected_value": [],
            },
        }
        for attr_name, info in ref_info.items():
            entity_attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=self._user,
                parent_entity=entity,
            )
            entity_attr.referral.add(ref_entity)
            entity.attrs.add(entity_attr)

        # Initialize an entry that refers 'ref' entry which will be deleted later
        entry = Entry.objects.create(name="ent", schema=entity, created_user=self._user)
        entry.complement_attrs(self._user)
        for attr_name, info in ref_info.items():
            attr = entry.attrs.get(name=attr_name)
            attr.add_value(self._user, info["value"])

        # Finally, register this created entry to Elasticsearch
        entry.register_es()

        # delete each referred entries from 'ent' entry
        for ent in ref_entries:
            ent.delete()

        # Check search result when each referred entries which is specified in the hint still exist
        for attr_name in ref_info.keys():
            # Check search result without keyword of hint_attrs
            hint_attr = AttrHint(name=attr_name, keyword="")
            ret = AdvancedSearchService.search_entries(
                self._user, [entity.id], hint_attrs=[hint_attr]
            )
            self.assertEqual(ret.ret_count, 1)
            self.assertEqual(len(ret.ret_values[0].attrs), 1)

            for _name, _info in ret.ret_values[0].attrs.items():
                self.assertTrue(_name in ref_info)
                self.assertEqual(_info["value"], ref_info[_name]["expected_value"])

            hint_attr = AttrHint(name=attr_name, keyword="ref")
            ret = AdvancedSearchService.search_entries(
                self._user, [entity.id], hint_attrs=[hint_attr]
            )
            self.assertEqual(ret.ret_count, 0)
            self.assertEqual(ret.ret_values, [])

    def test_search_entries_for_priviledged_ones(self):
        user = User.objects.create(username="test-user")

        ref_entity = self.create_entity(user, "Ref Entity", is_public=False)
        ref_entry = self.add_entry(user, "Ref", ref_entity)
        entity = self.create_entity(
            user,
            "Entity",
            attrs=[
                {
                    "name": "ref",
                    "type": AttrType.OBJECT,
                }
            ],
            is_public=False,
        )
        entry = self.add_entry(user, "Entry", entity, values={"ref": ref_entry})

        ret = AdvancedSearchService.search_entries(user, [entity.id])
        self.assertEqual(ret.ret_count, 0)
        self.assertEqual(ret.ret_values, [])

        ret = AdvancedSearchService.search_entries(None, [entity.id])
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual(
            ret.ret_values[0].entry,
            {
                "name": entry.name,
                "id": entry.id,
            },
        )

    def test_search_entries_with_regex_hint_attrs(self):
        user = User.objects.create(username="hoge")

        entity = Entity.objects.create(name="entity", created_user=user)
        attr = EntityAttr.objects.create(
            name="attr",
            type=AttrType.STRING,
            created_user=user,
            parent_entity=entity,
        )
        entity.attrs.add(attr)

        for value in ["100", "101", "200"]:
            entry = Entry.objects.create(name=value, schema=entity, created_user=user)
            entry.complement_attrs(user)
            entry.attrs.get(schema=attr).add_value(user, value)
            entry.register_es()

        resp = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name=attr.name, keyword="^10")]
        )
        self.assertEqual(resp.ret_count, 2)
        resp = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name=attr.name, keyword="00$")]
        )
        self.assertEqual(resp.ret_count, 2)
        resp = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name=attr.name, keyword="^100$")]
        )
        self.assertEqual(resp.ret_count, 1)

    def test_search_entries_with_hint_entry(self):
        user = User.objects.create(username="hintuser")
        entity = Entity.objects.create(name="HintEntity", created_user=user)
        attr = EntityAttr.objects.create(
            name="hint_attr", type=AttrType.STRING, created_user=user, parent_entity=entity
        )
        entity.attrs.add(attr)
        entry1 = Entry.objects.create(name="foo-entry", schema=entity, created_user=user)
        entry1_attr = entry1.add_attribute_from_base(attr, user)
        entry1_attr.add_value(user, "val1")
        entry1.register_es()
        entry2 = Entry.objects.create(name="bar-entry", schema=entity, created_user=user)
        entry2_attr = entry2.add_attribute_from_base(attr, user)
        entry2_attr.add_value(user, "val2")
        entry2.register_es()

        hint_entry = EntryHint(filter_key=EntryFilterKey.TEXT_CONTAINED, keyword="foo")
        res = AdvancedSearchService.search_entries(
            user=user,
            hint_entity_ids=[entity.id],
            hint_attrs=[],
            hint_entry=hint_entry,
        )
        self.assertEqual(res.ret_count, 1)
        self.assertTrue(any("foo" in v.entry["name"] for v in res.ret_values))

        # use hint entry even if entry_name is specified
        res2 = AdvancedSearchService.search_entries(
            user=user,
            hint_entity_ids=[entity.id],
            hint_attrs=[],
            entry_name="bar-entry",
            hint_entry=hint_entry,
        )
        self.assertEqual(res2.ret_count, 1)
        self.assertTrue(any("foo" in v.entry["name"] for v in res2.ret_values))

    def test_search_entries_for_simple(self):
        self._entity.attrs.add(self._attr.schema)
        self._entry.attrs.first().add_value(self._user, "hoge")
        self._entry.register_es()

        # search by Entry name
        ret = AdvancedSearchService.search_entries_for_simple("entry")
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual(
            ret["ret_values"][0],
            {
                "id": str(self._entry.id),
                "name": self._entry.name,
                "schema": {"id": self._entry.schema.id, "name": self._entry.schema.name},
            },
        )

        # search by AttributeValue
        ret = AdvancedSearchService.search_entries_for_simple("hoge")
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual(
            ret["ret_values"][0],
            {
                "id": str(self._entry.id),
                "name": self._entry.name,
                "schema": {"id": self._entry.schema.id, "name": self._entry.schema.name},
                "attr": self._attr.schema.name,
            },
        )

    def test_search_entries_for_simple_with_special_characters(self):
        ret = AdvancedSearchService.search_entries_for_simple("&")
        self.assertEqual(ret["ret_count"], 0)

    def test_search_entries_for_simple_with_hint_entity_name(self):
        self._entry.register_es()
        entity = Entity.objects.create(name="entity2", created_user=self._user)
        entry = Entry.objects.create(name="entry2", schema=entity, created_user=self._user)
        entry.register_es()

        ret = AdvancedSearchService.search_entries_for_simple("entry")
        self.assertEqual(ret["ret_count"], 2)
        self.assertEqual([x["name"] for x in ret["ret_values"]], ["entry", "entry2"])

        ret = AdvancedSearchService.search_entries_for_simple("entry", "entity")
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual([x["name"] for x in ret["ret_values"]], ["entry"])

    def test_search_entries_for_simple_with_exclude_entity_names(self):
        self._entry.register_es()
        entity = Entity.objects.create(name="entity2", created_user=self._user)
        entry = Entry.objects.create(name="entry2", schema=entity, created_user=self._user)
        entry.register_es()

        ret = AdvancedSearchService.search_entries_for_simple("entry")
        self.assertEqual(ret["ret_count"], 2)
        self.assertEqual([x["name"] for x in ret["ret_values"]], ["entry", "entry2"])

        ret = AdvancedSearchService.search_entries_for_simple(
            "entry", exclude_entity_names=["entity"]
        )
        self.assertEqual(ret["ret_count"], 1)
        self.assertEqual([x["name"] for x in ret["ret_values"]], ["entry2"])

    def test_search_entries_for_simple_with_limit_offset(self):
        for i in range(0, 10):
            entry = Entry.objects.create(
                name="e-%s" % i, schema=self._entity, created_user=self._user
            )
            entry.register_es()

        ret = AdvancedSearchService.search_entries_for_simple("e-", limit=5)
        self.assertEqual(ret["ret_count"], 10)
        self.assertEqual([x["name"] for x in ret["ret_values"]], ["e-%s" % x for x in range(0, 5)])

        ret = AdvancedSearchService.search_entries_for_simple("e-", offset=5)
        self.assertEqual(ret["ret_count"], 10)
        self.assertEqual([x["name"] for x in ret["ret_values"]], ["e-%s" % x for x in range(5, 10)])

        # param larger than max_result_window
        ret = AdvancedSearchService.search_entries_for_simple("e-", limit=500001)
        self.assertEqual(ret["ret_count"], 0)
        self.assertEqual(ret["ret_values"], [])

        ret = AdvancedSearchService.search_entries_for_simple("e-", offset=500001)
        self.assertEqual(ret["ret_count"], 0)
        self.assertEqual(ret["ret_values"], [])

    def test_search_entries_for_simple_with_sort(self):
        entry = Entry.objects.create(name="[entry]", schema=self._entity, created_user=self._user)
        entry.register_es()
        self._entry.register_es()

        ret = AdvancedSearchService.search_entries_for_simple("entry")
        self.assertEqual(
            ret,
            {
                "ret_count": 2,
                "ret_values": [
                    {
                        "id": str(self._entry.id),
                        "name": "entry",
                        "schema": {"id": self._entity.id, "name": "entity"},
                    },
                    {
                        "id": str(entry.id),
                        "name": "[entry]",
                        "schema": {"id": self._entity.id, "name": "entity"},
                    },
                ],
            },
        )

    def test_update_documents(self):
        all_attr_entity = self.create_entity_with_all_type_attributes(self._user)
        all_attr_entry = Entry.objects.create(
            name="all_attr_entry", created_user=self._user, schema=all_attr_entity
        )
        all_attr_entry.complement_attrs(self._user)

        # register
        with self.assertLogs(logger=Logger, level=logging.WARNING) as warning_log:
            AdvancedSearchService.update_documents(all_attr_entity)

        self.assertTrue(
            warning_log.output[0],
            "WARNING:airone:Update elasticsearch document (entry_id: %s)" % all_attr_entry.id,
        )

        res = AdvancedSearchService.search_entries(
            self._user, [all_attr_entity.id], is_output_all=True
        )
        self.assertEqual(res.ret_count, 1)
        self.assertEqual(
            [x for x in res.ret_values[0].attrs.keys()],
            [x.name for x in all_attr_entity.attrs.all()],
        )

        res = AdvancedSearchService.search_entries(self._user, [self._entity.id])
        self.assertEqual(res.ret_count, 0)

        AdvancedSearchService.update_documents(self._entity, True)

        res = AdvancedSearchService.search_entries(self._user, [self._entity.id])
        self.assertEqual(res.ret_count, 1)

        #  update
        entry2 = Entry.objects.create(name="entry2", created_user=self._user, schema=self._entity)
        with self.assertLogs(logger=Logger, level=logging.WARNING) as warning_log:
            AdvancedSearchService.update_documents(self._entity)

        self.assertTrue(
            warning_log.output[0],
            "WARNING:airone:Update elasticsearch document (entry_id: %s)" % entry2.id,
        )

        res = AdvancedSearchService.search_entries(self._user, [self._entity.id])
        self.assertEqual(res.ret_count, 2)

        entry2.is_active = False
        entry2.save()

        # delete
        with self.assertLogs(logger=Logger, level=logging.WARNING) as warning_log:
            AdvancedSearchService.update_documents(self._entity)

        self.assertTrue(
            warning_log.output[0],
            "WARNING:airone:Delete elasticsearch document (entry_id: %s)" % entry2.id,
        )

        res = AdvancedSearchService.search_entries(self._user, [self._entity.id])
        self.assertEqual(res.ret_count, 1)

    def test_search_entries_allow_missing_attributes(self):
        # 1. Setup Entities
        alpha_entity = Entity.objects.create(
            name="AlphaEntityAllowMissing", created_user=self._user
        )
        beta_entity = Entity.objects.create(name="BetaEntityAllowMissing", created_user=self._user)

        # 2. Setup EntityAttrs
        # Common attribute for both AlphaEntity and BetaEntity
        common_attr_alpha_schema = EntityAttr.objects.create(
            name="common_attr",
            type=AttrType.STRING,
            created_user=self._user,
            parent_entity=alpha_entity,
        )
        common_attr_beta_schema = EntityAttr.objects.create(
            name="common_attr",
            type=AttrType.STRING,
            created_user=self._user,
            parent_entity=beta_entity,
        )

        # Attribute only for AlphaEntity
        alpha_only_attr_schema = EntityAttr.objects.create(
            name="alpha_only_attr",
            type=AttrType.STRING,
            created_user=self._user,
            parent_entity=alpha_entity,
        )

        # 3. Setup Entries and AttributeValues
        # Entry for AlphaEntity
        entry_a1 = Entry.objects.create(
            name="entryA1_allow_missing", schema=alpha_entity, created_user=self._user
        )
        attr_a1_common = entry_a1.add_attribute_from_base(common_attr_alpha_schema, self._user)
        attr_a1_common.add_value(self._user, "common_value_A")
        attr_a1_alpha_only = entry_a1.add_attribute_from_base(alpha_only_attr_schema, self._user)
        attr_a1_alpha_only.add_value(self._user, "alpha_specific_value")

        # Entry for BetaEntity (does not have alpha_only_attr)
        entry_b1 = Entry.objects.create(
            name="entryB1_allow_missing", schema=beta_entity, created_user=self._user
        )
        attr_b1_common = entry_b1.add_attribute_from_base(common_attr_beta_schema, self._user)
        attr_b1_common.add_value(self._user, "common_value_B")

        # 4. Register entries to Elasticsearch
        entry_a1.register_es()
        entry_b1.register_es()

        # 5. Perform search with allow_missing_attributes=True
        hint_attrs = [
            AttrHint(name="common_attr"),
            AttrHint(name="alpha_only_attr"),  # This attribute is missing in BetaEntity
        ]
        entity_ids_list = [alpha_entity.id, beta_entity.id]

        result = AdvancedSearchService.search_entries(
            user=self._user,
            hint_entity_ids=entity_ids_list,
            hint_attrs=hint_attrs,
            allow_missing_attributes=True,
        )

        # 6. Assertions
        self.assertEqual(result.ret_count, 2, "Should return both entries")
        self.assertEqual(len(result.ret_values), 2)

        ret_entry_names = sorted([v.entry["name"] for v in result.ret_values])
        self.assertEqual(ret_entry_names, ["entryA1_allow_missing", "entryB1_allow_missing"])

        for ret_val in result.ret_values:
            if ret_val.entry["name"] == "entryA1_allow_missing":
                self.assertEqual(ret_val.entity["name"], "AlphaEntityAllowMissing")
                self.assertIn("common_attr", ret_val.attrs)
                self.assertEqual(ret_val.attrs["common_attr"]["value"], "common_value_A")
                self.assertIn("alpha_only_attr", ret_val.attrs)
                self.assertEqual(ret_val.attrs["alpha_only_attr"]["value"], "alpha_specific_value")
            elif ret_val.entry["name"] == "entryB1_allow_missing":
                self.assertEqual(ret_val.entity["name"], "BetaEntityAllowMissing")
                self.assertIn("common_attr", ret_val.attrs)
                self.assertEqual(ret_val.attrs["common_attr"]["value"], "common_value_B")
                # BetaEntity does not have 'alpha_only_attr', so it should not be in its results.
                self.assertNotIn("alpha_only_attr", ret_val.attrs)
