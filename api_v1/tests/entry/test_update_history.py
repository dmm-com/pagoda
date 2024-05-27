from datetime import date, datetime, timedelta

import pytz
from django.conf import settings

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.models import Entry
from entry.settings import CONFIG as CONFIG_ENTRY
from group.models import Group


class APITest(AironeViewTest):
    def setUp(self):
        super(APITest, self).setUp()

        self.user = self.guest_login()
        self.group = Group.objects.create(name="group")

        ref_entity = Entity.objects.create(name="Referred Entity", created_user=self.user)
        ref_entry = Entry.objects.create(
            name="referred_entry", schema=ref_entity, created_user=self.user
        )

        self.entity = Entity.objects.create(name="entity", created_user=self.user)
        self.test_attrs = {
            "str": {
                "type": AttrType.STRING,
                # These values will be saved as each different AttributeValue for checking
                # result order of update history API response.
                "set_values": ["1", "2", "3"],
                "ret_values": ["3", "2", "1"],
            },
            "obj": {
                "type": AttrType.OBJECT,
                "set_values": [ref_entry],
                "ret_values": [{"id": ref_entry.id, "name": ref_entry.name}],
            },
            "map": {
                "type": AttrType.NAMED_OBJECT,
                "set_values": [{"name": "hoge", "id": ref_entry}],
                "ret_values": [{"hoge": {"id": ref_entry.id, "name": ref_entry.name}}],
            },
            "arr_str": {
                "type": AttrType.ARRAY_STRING,
                "set_values": [["foo", "bar"]],
                "ret_values": [["foo", "bar"], []],
            },
            "arr_obj": {
                "type": AttrType.ARRAY_OBJECT,
                "set_values": [[ref_entry]],
                "ret_values": [[{"id": ref_entry.id, "name": ref_entry.name}], []],
            },
            "arr_map": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "set_values": [[{"name": "foo", "id": ref_entry}]],
                "ret_values": [
                    [{"foo": {"id": ref_entry.id, "name": ref_entry.name}}],
                    [],
                ],
            },
            "group": {
                "type": AttrType.GROUP,
                "set_values": [str(self.group.id)],
                "ret_values": [{"id": self.group.id, "name": self.group.name}],
            },
            "bool": {
                "type": AttrType.BOOLEAN,
                "set_values": [True],
                "ret_values": [True],
            },
            "text": {
                "type": AttrType.TEXT,
                "set_values": ["text"],
                "ret_values": ["text"],
            },
            "date": {
                "type": AttrType.DATE,
                "set_values": [date(2020, 1, 1)],
                "ret_values": ["2020-01-01"],
            },
        }

        # register all attributes which are declared as test_attrs
        for name, info in self.test_attrs.items():
            attr = EntityAttr.objects.create(
                name=name,
                type=info["type"],
                created_user=self.user,
                parent_entity=self.entity,
            )

            if info["type"] & AttrType.OBJECT:
                attr.referral.add(ref_entity)

            self.entity.attrs.add(attr)

    def test_with_fully_set_value(self):
        # create test entry and set each values
        entry = Entry.objects.create(name="entry", schema=self.entity, created_user=self.user)
        entry.complement_attrs(self.user)

        for name, info in self.test_attrs.items():
            # set values for each attributes
            attr = entry.attrs.get(schema__name=name)
            for value in info["set_values"]:
                attr.add_value(self.user, value)

            resp = self.client.get(
                "/api/v1/entry/update_history",
                {
                    "attribute": name,
                    "entry": entry.name,
                },
            )

            self.assertEqual(resp.status_code, 200)
            retdata = resp.json()

            # check resp data has expected parameters
            self.assertEqual(len(retdata), 1)
            self.assertEqual(retdata[0]["entity"], {"id": self.entity.id, "name": self.entity.name})
            self.assertEqual(retdata[0]["entry"], {"id": entry.id, "name": entry.name})
            self.assertEqual(retdata[0]["attribute"]["id"], attr.id)
            self.assertEqual(retdata[0]["attribute"]["name"], attr.name)

            # check values has expected parameters
            attr_history = retdata[0]["attribute"]["history"]

            # This confirms each types result has expected values
            self.assertEqual([x["value"] for x in attr_history], info["ret_values"])

            # This confirms each value results has following metadata
            metadatas = ["updated_at", "updated_username", "updated_userid"]
            self.assertTrue(all([(k in x for k in metadatas) for x in attr_history]))

            # Check result of specifying 'entry-id' would be same with the one of specyfing 'entry'
            resp_alter = self.client.get(
                "/api/v1/entry/update_history",
                {
                    "attribute": name,
                    "entry_id": entry.id,
                },
            )
            self.assertEqual(retdata, resp_alter.json())

    def test_without_set_value(self):
        # create test entry and set each values
        entry = Entry.objects.create(name="entry", schema=self.entity, created_user=self.user)
        entry.complement_attrs(self.user)

        for name, info in self.test_attrs.items():
            resp = self.client.get(
                "/api/v1/entry/update_history",
                {
                    "attribute": name,
                    "entry": entry.name,
                },
            )

            self.assertEqual(resp.status_code, 200)
            retdata = resp.json()

            # check resp data has expected parameters
            attr = entry.attrs.get(schema__name=name)
            self.assertEqual(len(retdata), 1)
            self.assertEqual(retdata[0]["entity"], {"id": self.entity.id, "name": self.entity.name})
            self.assertEqual(retdata[0]["entry"], {"id": entry.id, "name": entry.name})
            self.assertEqual(retdata[0]["attribute"]["id"], attr.id)
            self.assertEqual(retdata[0]["attribute"]["name"], attr.name)

            # check values has expected parameters
            attr_history = retdata[0]["attribute"]["history"]
            if info["type"] & AttrType._ARRAY:
                self.assertEqual(len(attr_history), 1)
                self.assertEqual(attr_history[0]["value"], [])
                self.assertEqual(attr_history[0]["updated_username"], self.user.username)
                self.assertEqual(attr_history[0]["updated_userid"], self.user.id)
            else:
                self.assertEqual(attr_history, [])

    def test_without_mandatory_params(self):
        # call update_history API without attribute parameter
        resp = self.client.get("/api/v1/entry/update_history")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(str(resp.content, "utf-8"), "\"'attribute' parameter is required\"")

        # call update_history API without both entry and entryid parameters
        resp = self.client.get("/api/v1/entry/update_history", {"attribute": "test-attribute"})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            str(resp.content, "utf-8"),
            "\"Either 'entries' or 'entry_ids' parameter is required\"",
        )

    def test_with_invalid_params(self):
        # create a test entry to use this test-suite
        entry = Entry.objects.create(name="entry", schema=self.entity, created_user=self.user)
        entry.complement_attrs(self.user)

        # call API request with invalid entry
        resp = self.client.get(
            "/api/v1/entry/update_history",
            {
                "attribute": "test-attr",
                "entry": "invalid-entry-name",
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            str(resp.content, "utf-8"),
            '"There is no entry with which matches specified parameters"',
        )

        # call API request with invalid attribute
        resp = self.client.get(
            "/api/v1/entry/update_history",
            {
                "attribute": "invalid-attribute",
                "entry": entry.name,
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            str(resp.content, "utf-8"),
            '"There is no attribute(invalid-attribute) in entry(entry)"',
        )

    def test_with_entity_params(self):
        # create a test entry to use this test-suite
        entry = Entry.objects.create(name="entry", schema=self.entity, created_user=self.user)
        entry.complement_attrs(self.user)

        # This creates another entity that has same name attribute with 'entity'
        # which is created in setUp method. And this test will create same name entry with
        # 'entry' which is created before.
        another_entity = Entity.objects.create(name="AnotherEntity", created_user=self.user)
        another_entity.attrs.add(
            EntityAttr.objects.create(
                **{
                    "name": "str",
                    "type": AttrType.STRING,
                    "created_user": self.user,
                    "parent_entity": another_entity,
                }
            )
        )
        another_entry = Entry.objects.create(
            name="entry", schema=another_entity, created_user=self.user
        )
        another_entry.complement_attrs(self.user)

        # call API request without entity parameter at first to check
        # both entries' information would be returned.
        resp = self.client.get(
            "/api/v1/entry/update_history",
            {
                "attribute": "str",
                "entry": "entry",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            [x["entity"] for x in resp.json()],
            [
                {"id": self.entity.id, "name": self.entity.name},
                {"id": another_entity.id, "name": another_entity.name},
            ],
        )

        # call API request with entity parameter to check reuslt would be filterd
        resp = self.client.get(
            "/api/v1/entry/update_history",
            {
                "entity": another_entity.name,
                "attribute": "str",
                "entry": "entry",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            [x["entity"] for x in resp.json()],
            [
                {"id": another_entity.id, "name": another_entity.name},
            ],
        )

    def test_maximum_number_of_history(self):
        entry = Entry.objects.create(name="entry", schema=self.entity, created_user=self.user)
        entry.complement_attrs(self.user)

        # set attribute value which is overflowing number of CONFIG_ENTRY['MAX_HISTORY_COUNT']
        attr = entry.attrs.get(schema__name="str")
        for i in range(CONFIG_ENTRY.MAX_HISTORY_COUNT + 1):
            attr.add_value(self.user, str(i))

        resp = self.client.get(
            "/api/v1/entry/update_history",
            {
                "attribute": "str",
                "entry": entry.name,
            },
        )
        self.assertEqual(resp.status_code, 200)
        attr_history = resp.json()[0]["attribute"]["history"]

        # check the number of returning attribute values are fewer than the number of its
        # which is stored in database because it's over CONFIG_ENTRY.MAX_HISTORY_COUNT.
        self.assertEqual(attr.values.count(), CONFIG_ENTRY.MAX_HISTORY_COUNT + 1)
        self.assertEqual(len(attr_history), CONFIG_ENTRY.MAX_HISTORY_COUNT)

    def test_narrow_down_time_range_to_get(self):
        entry = Entry.objects.create(name="entry", schema=self.entity, created_user=self.user)
        entry.complement_attrs(self.user)

        attr = entry.attrs.get(schema__name="str")

        attrvs = [attr.add_value(self.user, x) for x in ["initial value", "second value"]]

        # This is test processing to pretend that both Values are set at different times.
        reference_time = datetime.now().replace(tzinfo=pytz.timezone(settings.TIME_ZONE))
        attrvs[0].created_time = reference_time - timedelta(seconds=5)
        attrvs[1].created_time = reference_time + timedelta(seconds=5)
        for attrv in attrvs:
            attrv.save(update_fields=["created_time"])

        # This tests that only former AttributeValue would be returned by setting older_than param
        resp = self.client.get(
            "/api/v1/entry/update_history",
            {
                "attribute": "str",
                "entry": entry.name,
                "older_than": reference_time.strftime(CONFIG_ENTRY.TIME_FORMAT),
            },
        )
        self.assertEqual(resp.status_code, 200)
        attr_history = resp.json()[0]["attribute"]["history"]
        self.assertEqual(len(attr_history), 1)
        self.assertEqual(attr_history[0]["value"], "initial value")

        # This tests that only latter AttributeValue would be returned by setting newer_than param
        resp = self.client.get(
            "/api/v1/entry/update_history",
            {
                "attribute": "str",
                "entry": entry.name,
                "newer_than": reference_time.strftime(CONFIG_ENTRY.TIME_FORMAT),
            },
        )
        self.assertEqual(resp.status_code, 200)
        attr_history = resp.json()[0]["attribute"]["history"]
        self.assertEqual(len(attr_history), 1)
        self.assertEqual(attr_history[0]["value"], "second value")
