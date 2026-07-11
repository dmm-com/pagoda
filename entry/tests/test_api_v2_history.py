import json
from datetime import timedelta
from unittest import mock
from unittest.mock import Mock, patch

from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError

from airone.lib.types import (
    AttrType,
)
from entity.models import EntityAttr
from entry import tasks
from entry.models import Attribute, AttributeValue, Entry
from entry.tests.test_api_v2 import BaseViewTest


class ViewTest(BaseViewTest):
    def test_entry_history(self):
        values = {
            "val": {"value": "hoge", "result": {"as_string": "hoge"}},
            "vals": {"value": ["foo", "bar"], "result": {"as_array_string": ["foo", "bar"]}},
            "ref": {
                "value": self.ref_entry.id,
                "result": {
                    "as_object": {
                        "id": self.ref_entry.id,
                        "name": self.ref_entry.name,
                        "schema": {
                            "id": self.ref_entry.schema.id,
                            "name": self.ref_entry.schema.name,
                        },
                    },
                },
            },
            "refs": {
                "value": [self.ref_entry.id],
                "result": {
                    "as_array_object": [
                        {
                            "id": self.ref_entry.id,
                            "name": self.ref_entry.name,
                            "schema": {
                                "id": self.ref_entry.schema.id,
                                "name": self.ref_entry.schema.name,
                            },
                        }
                    ]
                },
            },
            "name": {
                "value": {"name": "hoge", "id": self.ref_entry.id},
                "result": {
                    "as_named_object": {
                        "name": "hoge",
                        "object": {
                            "id": self.ref_entry.id,
                            "name": self.ref_entry.name,
                            "schema": {
                                "id": self.ref_entry.schema.id,
                                "name": self.ref_entry.schema.name,
                            },
                        },
                    },
                },
            },
            "names": {
                "value": [{"name": "foo", "id": self.ref_entry.id}],
                "result": {
                    "as_array_named_object": [
                        {
                            "name": "foo",
                            "object": {
                                "id": self.ref_entry.id,
                                "name": self.ref_entry.name,
                                "schema": {
                                    "id": self.ref_entry.schema.id,
                                    "name": self.ref_entry.schema.name,
                                },
                            },
                        },
                    ]
                },
            },
            "group": {
                "value": self.group.id,
                "result": {
                    "as_group": {
                        "id": self.group.id,
                        "name": self.group.name,
                    },
                },
            },
            "groups": {
                "value": [self.group.id],
                "result": {
                    "as_array_group": [
                        {
                            "id": self.group.id,
                            "name": self.group.name,
                        }
                    ]
                },
            },
            "role": {
                "value": self.role.id,
                "result": {
                    "as_role": {
                        "id": self.role.id,
                        "name": self.role.name,
                    },
                },
            },
            "roles": {
                "value": [self.role.id],
                "result": {
                    "as_array_role": [
                        {
                            "id": self.role.id,
                            "name": self.role.name,
                        }
                    ]
                },
            },
            "text": {"value": "fuga", "result": {"as_string": "fuga"}},
            "bool": {"value": False, "result": {"as_boolean": False}},
            "date": {"value": "2018-12-31", "result": {"as_string": "2018-12-31"}},
            "num": {"value": 456, "result": {"as_number": 456.0}},
            "nums": {
                "value": [123, 456, 789],
                "result": {"as_array_number": [123.0, 456.0, 789.0]},
            },
            "datetime": {
                "value": "2018-12-31T00:00:00+00:00",
                "result": {"as_string": "2018-12-31T00:00:00+00:00"},
            },
        }
        entry = self.add_entry(
            self.user, "Entry", self.entity, values={x: values[x]["value"] for x in values.keys()}
        )
        resp = self.client.get("/entry/api/v2/%s/histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 22)
        attrv = entry.get_attrv("datetime")
        self.assertEqual(
            resp.json()["results"][0],
            {
                "created_time": attrv.created_time.astimezone(self.TZ_INFO).isoformat(),
                "created_user": "guest",
                "curr_value": {"as_string": "2018-12-31T00:00:00+00:00"},
                "id": attrv.id,
                "parent_attr": {"id": attrv.parent_attr.id, "name": "datetime"},
                "prev_id": None,
                "prev_value": None,
                "type": AttrType.DATETIME,
            },
        )

        for name in values.keys():
            attr: Attribute = entry.attrs.get(schema__name=name)
            attrv: AttributeValue = attr.get_latest_value()
            self.assertEqual(
                next(filter(lambda x: x["id"] == attrv.id, resp.json()["results"]))["curr_value"],
                values[name]["result"],
            )

        # check order by created_time
        attr = entry.attrs.get(schema__name="vals")
        attr.add_value(self.user, ["hoge", "fuga"])

        resp = self.client.get("/entry/api/v2/%s/histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 23)
        self.assertEqual(resp.json()["results"][0]["parent_attr"]["name"], "vals")
        self.assertEqual(
            resp.json()["results"][0]["curr_value"]["as_array_string"], ["hoge", "fuga"]
        )
        self.assertEqual(resp.json()["results"][0]["prev_value"]["as_array_string"], ["foo", "bar"])

    def test_entry_history_without_permission(self):
        entry = self.add_entry(self.user, "Entry", self.entity, {}, False)

        # permission nothing entry
        resp = self.client.get("/entry/api/v2/%s/histories/" % entry.id)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # permission readble entry
        self.role.users.add(self.user)
        entry.readable.roles.add(self.role)
        resp = self.client.get("/entry/api/v2/%d/histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)

        # permission nothing entity attr
        entity_attr: EntityAttr = self.entity.attrs.get(name="val")
        entity_attr.is_public = False
        entity_attr.save()
        resp = self.client.get("/entry/api/v2/%d/histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(
            any(
                [
                    x["parent_attr"]["name"] == "val"
                    for x in [result for result in resp.json()["results"]]
                ]
            )
        )

        # permission nothing entity attr
        entity_attr.readable.roles.add(self.role)
        resp = self.client.get("/entry/api/v2/%d/histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            any(
                [
                    x["parent_attr"]["name"] == "val"
                    for x in [result for result in resp.json()["results"]]
                ]
            )
        )

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    def test_destroy_entries(self):
        entry1: Entry = self.add_entry(self.user, "entry1", self.entity)
        entry2: Entry = self.add_entry(self.user, "entry2", self.entity)

        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s&ids=%s" % (entry1.id, entry2.id),
            None,
            "application/json",
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        entry1.refresh_from_db()
        entry2.refresh_from_db()
        self.assertRegex(entry1.name, "entry1_deleted_")
        self.assertFalse(entry1.is_active)
        self.assertEqual(entry1.deleted_user, self.user)
        self.assertIsNotNone(entry1.deleted_time)
        self.assertRegex(entry2.name, "entry2_deleted_")
        self.assertFalse(entry2.is_active)
        self.assertEqual(entry2.deleted_user, self.user)
        self.assertIsNotNone(entry2.deleted_time)

        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s&ids=%s" % (entry1.id, entry2.id),
            None,
            "application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_destroy_entries_without_permission(self):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        # permission nothing entity
        self.entity.is_public = False
        self.entity.save()
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 403)

        # permission readable entity
        self.role.users.add(self.user)
        self.entity.readable.roles.add(self.role)
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 403)

        # permission writable entity
        self.entity.writable.roles.add(self.role)
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)

        entry.restore()

        # permission nothing entry
        entry.is_public = False
        entry.save()
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 403)

        # permission readable entry
        entry.readable.roles.add(self.role)
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 403)

        # permission writable entry
        entry.writable.roles.add(self.role)
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)

    def test_destory_entries_with_invalid_param(self):
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % "hoge", None, "application/json"
        )
        self.assertEqual(resp.status_code, 400)

        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % 9999, None, "application/json"
        )
        self.assertEqual(resp.status_code, 404)

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    @mock.patch("airone.lib.custom_view.is_custom", mock.Mock(return_value=True))
    @mock.patch("airone.lib.custom_view.call_custom")
    def test_destroy_entries_with_custom_view(self, mock_call_custom):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)

        def side_effect(handler_name, entity_name, user, entry):
            raise ValidationError("delete error")

        mock_call_custom.side_effect = side_effect
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(mock_call_custom.called)

        entry = self.add_entry(self.user, "entry2", self.entity)

        def side_effect(handler_name, entity_name, user, entry):
            self.assertTrue(handler_name in ["before_delete_entry_v2", "after_delete_entry_v2"])
            self.assertEqual(entity_name, self.entity.name)
            self.assertEqual(user, self.user)
            self.assertEqual(entry, entry)

        mock_call_custom.side_effect = side_effect
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(mock_call_custom.called)

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    @mock.patch("entry.tasks.notify_delete_entry.delay")
    def test_destroy_entries_notify(self, mock_task):
        entry: Entry = self.add_entry(self.user, "entry", self.entity)
        self.client.delete("/entry/api/v2/bulk_delete/?ids=%s" % entry.id, None, "application/json")

        self.assertTrue(mock_task.called)

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    def test_delete_entries_without_all_parameter(self):
        # create test Items that would be deleted in this test
        items = [self.add_entry(self.user, "item-%d" % i, self.entity) for i in range(5)]

        # send request to delete only items[0]
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % items[0].id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        # check only items[0] was deleted and rest of items are still alive.
        [x.refresh_from_db() for x in items]
        self.assertFalse(items[0].is_active)
        self.assertTrue(all(x.is_active for x in items[1:]))

        # send request to delete all items
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s&isAll=false" % items[1].id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        # check only items[0] and items[1] are delete, and rest of items are still alived
        [x.refresh_from_db() for x in items]
        self.assertFalse(all(x.is_active for x in items[:2]))
        self.assertTrue(all(x.is_active for x in items[2:]))

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    def test_delete_entries_with_all_parameter(self):
        # create test Items that would be deleted in this test
        items = [self.add_entry(self.user, "item-%d" % i, self.entity) for i in range(5)]

        # send request to delete only items[0]
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s" % items[0].id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        # check only items[0] was deleted and rest of items are still alive.
        [x.refresh_from_db() for x in items]
        self.assertFalse(items[0].is_active)
        self.assertTrue(all(x.is_active for x in items[1:]))

        # send request to delete all items
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s&isAll=true" % items[1].id, None, "application/json"
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        # check all items were deleted.
        [x.refresh_from_db() for x in items]
        self.assertFalse(any(x.is_active for x in items))

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    def test_delete_entries_with_all_parameter_and_attrinfo(self):
        # create test Items that would be deleted in this test
        items = [
            self.add_entry(
                self.user,
                "item-%d" % i,
                self.entity,
                values={
                    "val": "hoge" if i < 3 else "fuga",
                },
            )
            for i in range(5)
        ]

        # send request to delete all items with attrinfo
        attrinfo_as_str = json.dumps(
            [
                {"name": "ref", "keyword": "", "filterKey": "0"},
                {"name": "val", "keyword": "hoge", "filterKey": "3"},
            ]
        )
        resp = self.client.delete(
            "/entry/api/v2/bulk_delete/?ids=%s&isAll=true&attrinfo=%s"
            % (
                items[0].id,
                attrinfo_as_str,
            ),
            None,
            "application/json",
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        # check only items, which are matched with "val=hoge", were deleted.
        [x.refresh_from_db() for x in items]
        self.assertFalse(any(x.is_active for x in items[:3]))
        self.assertTrue(any(x.is_active for x in items[3:]))

    def test_list_self_histories(self):
        """Test list self histories endpoint - normal case"""
        # Create an entry with initial name
        initial_name = "initial_entry"
        entry = self.add_entry(self.user, initial_name, self.entity)

        # Update the entry name to create history records
        entry.name = "updated_entry_1"
        entry.save()

        entry.name = "updated_entry_2"
        entry.save()

        # Make API request to list self histories
        resp = self.client.get("/entry/api/v2/%s/self_histories/" % entry.id)

        # Check response status and structure
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("count", data)
        self.assertIn("results", data)

        # Should have 3 history records (initial creation + 2 updates)
        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["results"]), 3)

        # Check the most recent record (should be at index 0 due to ordering by -history_date)
        latest_record = data["results"][0]
        self.assertEqual(latest_record["name"], "updated_entry_2")
        self.assertEqual(latest_record["history_type"], "~")  # update

        # Since simple_history doesn't automatically track users in tests,
        # it will be None and serializer will return default value "システム"
        self.assertEqual(latest_record["history_user"], "システム")
        self.assertIn("history_id", latest_record)
        self.assertIn("history_date", latest_record)

        # Check second record
        second_record = data["results"][1]
        self.assertEqual(second_record["name"], "updated_entry_1")
        self.assertEqual(second_record["prev_name"], "initial_entry")

        # Check first record (creation)
        first_record = data["results"][2]
        self.assertEqual(first_record["name"], initial_name)
        self.assertEqual(first_record["history_type"], "+")  # creation

    def test_list_self_histories_prev_name_across_pagination_boundary(self):
        """Test that prev_name is correct even when history spans multiple pages.

        The list endpoint paginates with a page size of 30. The previous name
        of each record must be derived from the chronologically preceding record
        regardless of which page that record falls on. This verifies the record
        sitting at the page boundary still resolves its previous name correctly.
        """
        # Create an entry, then rename it enough times to exceed one page (30).
        # 1 creation + 30 updates == 31 history records.
        entry = self.add_entry(self.user, "name_v0", self.entity)
        for i in range(1, 31):
            entry.name = "name_v%d" % i
            entry.save()

        # Assign deterministic, strictly increasing history_date values so that
        # ordering is stable (consecutive save() calls can collide otherwise).
        base_time = timezone.now() - timedelta(hours=1)
        for i, hist in enumerate(entry.history.order_by("history_id")):
            hist.history_date = base_time + timedelta(minutes=i)
            hist.save()

        # First page (newest 30 records, ordered by -history_date).
        resp = self.client.get("/entry/api/v2/%s/self_histories/?offset=0&limit=30" % entry.id)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()

        self.assertEqual(data["count"], 31)
        self.assertEqual(len(data["results"]), 30)

        # The newest record's previous name resolves within the page.
        self.assertEqual(data["results"][0]["name"], "name_v30")
        self.assertEqual(data["results"][0]["prev_name"], "name_v29")

        # The last record on this page (name_v1) was renamed from name_v0, which
        # lives on the *next* page. Its prev_name must still be "name_v0".
        boundary_record = data["results"][29]
        self.assertEqual(boundary_record["name"], "name_v1")
        self.assertEqual(boundary_record["prev_name"], "name_v0")

        # Second page holds the creation record; its prev_name is genuinely None.
        resp2 = self.client.get("/entry/api/v2/%s/self_histories/?offset=30&limit=30" % entry.id)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        data2 = resp2.json()
        self.assertEqual(len(data2["results"]), 1)
        self.assertEqual(data2["results"][0]["name"], "name_v0")
        self.assertEqual(data2["results"][0]["history_type"], "+")  # creation
        self.assertIsNone(data2["results"][0]["prev_name"])

    def test_list_self_histories_rename_via_update_fields(self):
        """Reproduce the production rename path: Entry.save(update_fields=['name']).

        The real update flow (EntryUpdateSerializer) renames an entry via
        ``entry.save(update_fields=["name"])``. This verifies a history record is
        created for the rename and that its previous name is resolved correctly,
        which is the case the user reports as showing "-" for the previous name.
        """
        entry = self.add_entry(self.user, "old_name", self.entity)

        entry.name = "new_name"
        entry.save(update_fields=["name"])

        resp = self.client.get("/entry/api/v2/%s/self_histories/" % entry.id)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()

        # creation + rename == 2 records
        self.assertEqual(data["count"], 2)

        # newest record is the rename; its previous name must be "old_name"
        latest = data["results"][0]
        self.assertEqual(latest["name"], "new_name")
        self.assertEqual(latest["history_type"], "~")
        self.assertEqual(latest["prev_name"], "old_name")

    @patch("entry.tasks.edit_entry_v2.delay", Mock(side_effect=tasks.edit_entry_v2))
    def test_list_self_histories_rename_without_creation_record(self):
        """Renaming a history-less entry must still preserve its previous name.

        Entries created before simple-history was introduced (2022-12-08) have no
        creation history record, and ``populate_history`` is never run. When such
        an entry is later renamed, the rename would become the oldest (and only)
        history record, so the previous name (derived from the preceding record)
        used to resolve to None and the UI showed '-'.

        ``EntryUpdateSerializer.update`` now snapshots the current state before
        renaming a history-less entry, so the previous name ("original_name") is
        preserved in history and reported here.
        """
        entry = self.add_entry(self.user, "original_name", self.entity)

        # Simulate an entry with no creation history (predates simple-history).
        entry.history.all().delete()
        self.assertEqual(entry.history.count(), 0)

        # Rename through the production API path so the serializer fix runs.
        params = {"name": "renamed", "attrs": []}
        resp = self.client.put(
            "/entry/api/v2/%s/" % entry.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        resp = self.client.get("/entry/api/v2/%s/self_histories/" % entry.id)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()

        # A baseline snapshot ("original_name") plus the rename == 2 records.
        self.assertEqual(data["count"], 2)
        latest = data["results"][0]
        self.assertEqual(latest["name"], "renamed")
        self.assertEqual(latest["history_type"], "~")  # update
        self.assertEqual(latest["prev_name"], "original_name")

    def test_list_self_histories_without_permission(self):
        """Test list self histories endpoint - permission check"""
        # Create entry without permission
        entry = self.add_entry(self.user, "test_entry", self.entity, {}, False)

        # Test without any permission
        resp = self.client.get("/entry/api/v2/%s/self_histories/" % entry.id)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

        # Grant read permission
        self.role.users.add(self.user)
        entry.readable.roles.add(self.role)

        # Should now work
        resp = self.client.get("/entry/api/v2/%s/self_histories/" % entry.id)
        self.assertEqual(resp.status_code, 200)

    def test_list_self_histories_with_invalid_entry_id(self):
        """Test list self histories endpoint - non-existent entry"""
        non_existent_id = 9999999
        resp = self.client.get("/entry/api/v2/%s/self_histories/" % non_existent_id)
        self.assertEqual(resp.status_code, 404)

    def test_restore_self_history(self):
        """Test restore self history endpoint - normal case"""
        # Create an entry with initial name
        initial_name = "original_name"
        entry = self.add_entry(self.user, initial_name, self.entity)

        # Update the entry name to create history
        entry.name = "modified_name"
        entry.save()

        # Get the history record for the original name
        history_records = entry.history.all().order_by("-history_date")
        original_history = None
        for record in history_records:
            if record.name == initial_name:
                original_history = record
                break

        self.assertIsNotNone(original_history)

        # Restore to original name using API
        payload = {"history_id": original_history.history_id}
        resp = self.client.post(
            "/entry/api/v2/%s/restore_self_history/" % entry.id,
            payload,
            "application/json",
        )

        # Check response
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("message", data)
        self.assertEqual(data["restored_name"], initial_name)

        # Verify entry name was restored
        entry.refresh_from_db()
        self.assertEqual(entry.name, initial_name)

    def test_restore_self_history_without_permission(self):
        """Test restore self history endpoint - permission check"""
        # Create entry without write permission
        entry = self.add_entry(self.user, "test_entry", self.entity, {}, False)

        # Grant only read permission
        self.role.users.add(self.user)
        entry.readable.roles.add(self.role)

        # Get a history record
        history_record = entry.history.first()

        # Try to restore without write permission
        payload = {"history_id": history_record.history_id}
        resp = self.client.post(
            "/entry/api/v2/%s/restore_self_history/" % entry.id,
            payload,
            "application/json",
        )

        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )

    def test_restore_self_history_with_invalid_history_id(self):
        """Test restore self history endpoint - non-existent history ID"""
        entry = self.add_entry(self.user, "test_entry", self.entity)

        # Use invalid history ID
        payload = {"history_id": 9999999}
        resp = self.client.post(
            "/entry/api/v2/%s/restore_self_history/" % entry.id,
            payload,
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        response_data = resp.json()
        self.assertIsInstance(response_data, list)
        self.assertEqual(len(response_data), 1)
        self.assertIn("指定された履歴が見つかりません", response_data[0]["message"])

    def test_restore_self_history_with_duplicate_name(self):
        """Test restore self history endpoint - duplicate name error"""
        # Create two entries
        entry1 = self.add_entry(self.user, "entry_1", self.entity)
        entry2 = self.add_entry(self.user, "entry_2", self.entity)

        # Update entry1 name
        entry1.name = "entry_1_modified"
        entry1.save()

        # Get history record for original entry1 name
        history_records = entry1.history.all()
        original_history = None
        for record in history_records:
            if record.name == "entry_1":
                original_history = record
                break

        # Now change entry2 name to "entry_1"
        entry2.name = "entry_1"
        entry2.save()

        # Try to restore entry1 to "entry_1" - should fail due to duplicate
        payload = {"history_id": original_history.history_id}
        resp = self.client.post(
            "/entry/api/v2/%s/restore_self_history/" % entry1.id,
            payload,
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        response_data = resp.json()
        self.assertIsInstance(response_data, list)
        self.assertEqual(len(response_data), 1)
        self.assertIn("既に使用されています", response_data[0]["message"])

    def test_restore_self_history_with_alias_conflict(self):
        """Test restore self history endpoint - alias name conflict error"""
        from entry.models import AliasEntry

        # Create an entry
        entry = self.add_entry(self.user, "original_name", self.entity)

        # Update entry name
        entry.name = "modified_name"
        entry.save()

        # Create alias with the original name
        AliasEntry.objects.create(name="original_name", entry=entry)

        # Get history record for the original name
        history_records = entry.history.all()
        original_history = None
        for record in history_records:
            if record.name == "original_name":
                original_history = record
                break

        # Try to restore to original name - should fail due to alias conflict
        payload = {"history_id": original_history.history_id}
        resp = self.client.post(
            "/entry/api/v2/%s/restore_self_history/" % entry.id,
            payload,
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        response_data = resp.json()
        self.assertIsInstance(response_data, list)
        self.assertEqual(len(response_data), 1)
        self.assertIn("エイリアスで使用されています", response_data[0]["message"])
