from airone.lib.acl import ACLType
from airone.lib.http import DRFRequest
from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from entry.api_v2.serializers import (
    EntrySelfHistoryRestoreSerializer,
    EntrySelfHistorySerializer,
    PrivilegedEntryCreateSerializer,
    PrivilegedEntryUpdateSerializer,
)
from user.models import User


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        user: User = User.objects.create(username="userA")

        # create Entity that has "secret" Attribute user couldn't update
        self.schema = self.create_entity(
            user,
            "Entity",
            attrs=[
                {"name": "secret", "type": AttrType.STRING},
            ],
        )
        attr = self.schema.attrs.last()
        attr.is_public = False
        attr.default_permission = ACLType.Nothing.id
        attr.save()

    def test_create_entry_without_permission_leagally(self):
        login_user: User = self.guest_login()

        # create Entry using Serializer by user who doesn't have permission to
        # update "secret" Attribute.
        setting_data = {
            "schema": self.schema,
            "name": "Entry0",
            "attrs": [
                {
                    "id": self.schema.attrs.get(name="secret").id,
                    "value": "caput draconis",
                }
            ],
            "created_user": login_user,
        }
        serializer = PrivilegedEntryCreateSerializer(
            data=setting_data, context={"request": DRFRequest(login_user)}
        )
        self.assertIsNotNone(serializer)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()

        # check created Entry has proper Attribute value
        self.assertEqual(entry.name, "Entry0")
        self.assertEqual(entry.get_attrv("secret").value, "caput draconis")

    def test_update_entry_without_permission_leagally(self):
        # create Entry to update in this test
        another_user: User = User.objects.create(username="userB")
        entry = self.add_entry(another_user, "e0", self.schema)

        login_user: User = self.guest_login()

        # update Entry using Serializer by user who doesn't have permission to
        # update "secret" Attribute.
        setting_data = {
            "id": entry.id,
            "name": "e0 changed",
            "attrs": [
                {
                    "id": self.schema.attrs.get(name="secret").id,
                    "value": "caput draconis",
                }
            ],
        }
        serializer = PrivilegedEntryUpdateSerializer(
            instance=entry, data=setting_data, context={"request": DRFRequest(login_user)}
        )

        self.assertIsNotNone(serializer)
        serializer.is_valid(raise_exception=True)
        changed_entry = serializer.save()

        # check created Entry has proper Attribute value
        self.assertEqual(changed_entry.name, "e0 changed")
        self.assertEqual(changed_entry.get_attrv("secret").value, "caput draconis")


class EntrySelfHistorySerializerTest(AironeViewTest):
    def setUp(self):
        super().setUp()

        # Create a test user
        self.user = User.objects.create(username="test_user")

        # Create entity and entry for testing
        self.entity = self.create_entity(
            self.user,
            "TestEntity",
            attrs=[
                {"name": "attr1", "type": AttrType.STRING},
            ],
        )
        self.entry = self.add_entry(self.user, "TestEntry", self.entity)

    def test_serializer_fields(self):
        """Test that all expected fields are present in the serialized data"""
        # Get historical record
        history_record = self.entry.history.first()

        # Serialize the data
        serializer = EntrySelfHistorySerializer(history_record)
        data = serializer.data

        # Check that all expected fields are present
        expected_fields = {
            "history_id",
            "name",
            "prev_name",
            "history_date",
            "history_user",
            "history_type",
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_username_conversion(self):
        """Test that history_user is properly converted to username"""
        # Update entry to ensure history_user is set
        self.entry.name = "Updated"
        self.entry._history_user = self.user
        self.entry.save()

        # Get the updated history record
        history_record = self.entry.history.first()

        # Serialize with actual user
        serializer = EntrySelfHistorySerializer(history_record)
        data = serializer.data
        self.assertEqual(data["history_user"], self.user.username)

        # Test with None user (should use default "システム")
        history_record.history_user = None
        serializer = EntrySelfHistorySerializer(history_record)
        data = serializer.data
        self.assertEqual(data["history_user"], "システム")

    def test_prev_name_with_prefetched_data(self):
        """Test prev_name calculation with prefetched data"""
        # Update entry to create multiple history records
        self.entry.name = "UpdatedEntry"
        self.entry._history_user = self.user
        self.entry.save()

        # Get the latest history record
        latest_history = self.entry.history.first()

        # Simulate prefetched data
        latest_history._prefetched_prev_name = "TestEntry"

        serializer = EntrySelfHistorySerializer(latest_history)
        data = serializer.data

        self.assertEqual(data["prev_name"], "TestEntry")

    def test_prev_name_without_prefetched_data(self):
        """Test prev_name calculation without prefetched data"""
        history_record = self.entry.history.first()

        # Should return None for the first record
        serializer = EntrySelfHistorySerializer(history_record)
        data = serializer.data

        self.assertIsNone(data["prev_name"])

    def test_serializer_with_actual_entry_data(self):
        """Test serializer with real entry data"""
        # Update the entry to create more history
        self.entry.name = "Updated Name"
        self.entry._history_user = self.user
        self.entry.save()

        # Get history records
        history_records = list(self.entry.history.all())

        # Test each record (only check the updated record which has user)
        latest_record = history_records[0]  # Most recent record with user
        serializer = EntrySelfHistorySerializer(latest_record)
        data = serializer.data

        # Verify basic fields
        self.assertIsInstance(data["history_id"], int)
        self.assertIsInstance(data["name"], str)
        self.assertEqual(data["history_user"], self.user.username)
        self.assertIn(data["history_type"], ["+", "~", "-"])  # Creation, Update, Deletion


class EntrySelfHistoryListSerializerTest(AironeViewTest):
    def setUp(self):
        super().setUp()

        # Create a test user
        self.user = User.objects.create(username="test_user")

        # Create entity and entry for testing
        self.entity = self.create_entity(
            self.user,
            "TestEntity",
            attrs=[
                {"name": "attr1", "type": AttrType.STRING},
            ],
        )
        self.entry = self.add_entry(self.user, "Original", self.entity)

    def test_prev_name_calculation_with_multiple_histories(self):
        """Test prev_name calculation across multiple history records"""
        # Create multiple updates to generate history
        updates = ["Updated1", "Updated2", "Updated3"]

        for name in updates:
            self.entry.name = name
            self.entry._history_user = self.user
            self.entry.save()

        # Get all history records and serialize them
        history_records = list(self.entry.history.all().order_by("-history_date"))
        serializer = EntrySelfHistorySerializer(history_records, many=True)
        data = serializer.data

        # Verify prev_name calculations
        # Latest record should have prev_name = "Updated2"
        self.assertEqual(data[0]["prev_name"], "Updated2")
        # Second latest should have prev_name = "Updated1"
        self.assertEqual(data[1]["prev_name"], "Updated1")
        # Third latest should have prev_name = "Original"
        self.assertEqual(data[2]["prev_name"], "Original")
        # Oldest should have no prev_name
        self.assertIsNone(data[3]["prev_name"])

    def test_date_sorting_and_prefetch_behavior(self):
        """Test that records are sorted by date and prefetch works correctly"""
        # Create updates at different times
        names = ["First", "Second", "Third"]

        for name in names:
            self.entry.name = name
            self.entry._history_user = self.user
            self.entry.save()

        # Get all history records (unsorted initially)
        history_records = list(self.entry.history.all())

        # Use the serializer with many=True to trigger the list serializer
        serializer = EntrySelfHistorySerializer(history_records, many=True)
        data = serializer.data

        # Verify that the list serializer processed the data correctly
        # The data should be sorted by history_date and have prev_name calculated
        self.assertEqual(len(data), len(history_records))

        # Check that prev_name is calculated correctly based on sorted order
        # (this indirectly tests the list serializer's sorting and prefetching)
        for i, item in enumerate(data):
            if i < len(data) - 1:  # Not the oldest record
                # Should have a prev_name from the previous record in chronological order
                self.assertIsNotNone(item.get("prev_name"))
            else:  # Oldest record
                self.assertIsNone(item["prev_name"])

    def test_empty_queryset_handling(self):
        """Test handling of empty querysets"""
        empty_queryset = self.entry.history.none()

        # Should not raise any errors
        serializer = EntrySelfHistorySerializer(empty_queryset, many=True)
        data = serializer.data

        self.assertEqual(len(data), 0)


class EntrySelfHistoryRestoreSerializerTest(AironeViewTest):
    def setUp(self):
        super().setUp()

        # Create a test user
        self.user = User.objects.create(username="test_user")

        # Create entity and entry for testing
        self.entity = self.create_entity(
            self.user,
            "TestEntity",
            attrs=[
                {"name": "attr1", "type": AttrType.STRING},
            ],
        )

    def test_history_id_required(self):
        """Test that history_id is required"""
        serializer = EntrySelfHistoryRestoreSerializer(data={})

        self.assertFalse(serializer.is_valid())
        self.assertIn("history_id", serializer.errors)

    def test_history_id_validation(self):
        """Test history_id validation"""
        # Test with valid integer
        serializer = EntrySelfHistoryRestoreSerializer(data={"history_id": 123})
        self.assertTrue(serializer.is_valid())

        # Test with invalid data types
        invalid_values = [
            "not_a_number",
            None,
            [],
            {},
            "abc123",
        ]

        for invalid_value in invalid_values:
            serializer = EntrySelfHistoryRestoreSerializer(data={"history_id": invalid_value})
            self.assertFalse(serializer.is_valid())
            self.assertIn("history_id", serializer.errors)

    def test_valid_history_id_values(self):
        """Test various valid history_id values"""
        valid_values = [0, 1, 999999, -1]  # Negative might be allowed depending on use case

        for valid_value in valid_values:
            serializer = EntrySelfHistoryRestoreSerializer(data={"history_id": valid_value})
            self.assertTrue(serializer.is_valid(), f"history_id {valid_value} should be valid")

    def test_serializer_data_structure(self):
        """Test the expected data structure after validation"""
        test_id = 12345
        serializer = EntrySelfHistoryRestoreSerializer(data={"history_id": test_id})

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["history_id"], test_id)

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored"""
        data = {"history_id": 123, "extra_field": "should_be_ignored", "another_field": 456}

        serializer = EntrySelfHistoryRestoreSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Only history_id should be in validated_data
        self.assertEqual(set(serializer.validated_data.keys()), {"history_id"})
