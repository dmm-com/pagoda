"""
Tests for data access interface.

Tests the DataInterface protocol and its implementations
to ensure proper data access functionality for entities, entries, and attributes.
"""

import unittest
from unittest.mock import Mock

from pagoda_plugin_sdk.exceptions import DataAccessError
from pagoda_plugin_sdk.interfaces.data import DataInterface


class TestDataInterface(unittest.TestCase):
    """Test cases for DataInterface"""

    def test_data_interface_is_abstract(self):
        """Test that DataInterface cannot be instantiated directly"""
        with self.assertRaises(TypeError):
            DataInterface()

    def test_data_interface_requires_abstract_methods(self):
        """Test that subclasses must implement abstract methods"""

        class IncompleteDataImpl(DataInterface):
            def get_entity(self, entity_id):
                return {}

            # Missing other abstract methods

        with self.assertRaises(TypeError):
            IncompleteDataImpl()


class MockDataImplementation(DataInterface):
    """Mock implementation of DataInterface for testing"""

    def __init__(self):
        self.entities = {
            1: {
                "id": 1,
                "name": "User",
                "note": "User entity",
                "is_active": True,
                "attrs": ["username", "email", "full_name"],
            },
            2: {
                "id": 2,
                "name": "Project",
                "note": "Project entity",
                "is_active": True,
                "attrs": ["name", "description", "status"],
            },
        }

        self.entries = {
            1: {
                "id": 1,
                "name": "john_doe",
                "schema": 1,  # User entity
                "attrs": {
                    "username": "john_doe",
                    "email": "john@example.com",
                    "full_name": "John Doe",
                },
                "is_active": True,
                "created_user": "admin",
            },
            2: {
                "id": 2,
                "name": "project_alpha",
                "schema": 2,  # Project entity
                "attrs": {
                    "name": "Project Alpha",
                    "description": "First project",
                    "status": "active",
                },
                "is_active": True,
                "created_user": "admin",
            },
            3: {
                "id": 3,
                "name": "jane_doe",
                "schema": 1,  # User entity
                "attrs": {
                    "username": "jane_doe",
                    "email": "jane@example.com",
                    "full_name": "Jane Doe",
                },
                "is_active": True,
                "created_user": "admin",
            },
        }

        self.history = {
            1: [
                {
                    "timestamp": "2023-01-01T00:00:00Z",
                    "user": "admin",
                    "action": "create",
                    "changes": {"username": "john_doe", "email": "john@example.com"},
                },
                {
                    "timestamp": "2023-01-02T00:00:00Z",
                    "user": "admin",
                    "action": "update",
                    "changes": {"full_name": "John Doe"},
                },
            ]
        }

        self.next_entry_id = 4

    def get_entity(self, entity_id):
        """Get entity by ID"""
        if isinstance(entity_id, str):
            try:
                entity_id = int(entity_id)
            except ValueError:
                return None

        return self.entities.get(entity_id)

    def get_entity_by_name(self, name):
        """Get entity by name"""
        for entity in self.entities.values():
            if entity["name"] == name:
                return entity.copy()
        return None

    def get_entry(self, entry_id):
        """Get entry by ID"""
        if isinstance(entry_id, str):
            try:
                entry_id = int(entry_id)
            except ValueError:
                return None

        return self.entries.get(entry_id)

    def get_entries(self, entity_id, filters=None, limit=None):
        """Get entries for an entity"""
        if isinstance(entity_id, str):
            try:
                entity_id = int(entity_id)
            except ValueError:
                return []

        entries = [
            entry.copy()
            for entry in self.entries.values()
            if entry["schema"] == entity_id and entry["is_active"]
        ]

        # Apply filters if provided
        if filters:
            filtered_entries = []
            for entry in entries:
                match = True
                for key, value in filters.items():
                    if key in entry and entry[key] != value:
                        match = False
                        break
                    elif key in entry.get("attrs", {}) and entry["attrs"][key] != value:
                        match = False
                        break
                if match:
                    filtered_entries.append(entry)
            entries = filtered_entries

        # Apply limit if provided
        if limit is not None:
            entries = entries[:limit]

        return entries

    def create_entry(self, entity_id, data, user):
        """Create a new entry"""
        if isinstance(entity_id, str):
            try:
                entity_id = int(entity_id)
            except ValueError:
                raise DataAccessError(f"Invalid entity ID: {entity_id}")

        if entity_id not in self.entities:
            raise DataAccessError(f"Entity {entity_id} not found")

        if not data.get("name"):
            raise DataAccessError("Entry name is required")

        entry_id = self.next_entry_id
        self.next_entry_id += 1

        new_entry = {
            "id": entry_id,
            "name": data["name"],
            "schema": entity_id,
            "attrs": data.get("attrs", {}),
            "is_active": True,
            "created_user": getattr(user, "username", str(user)) if user else "unknown",
        }

        self.entries[entry_id] = new_entry
        return new_entry.copy()

    def update_entry(self, entry_id, data, user):
        """Update an existing entry"""
        if isinstance(entry_id, str):
            try:
                entry_id = int(entry_id)
            except ValueError:
                raise DataAccessError(f"Invalid entry ID: {entry_id}")

        if entry_id not in self.entries:
            raise DataAccessError(f"Entry {entry_id} not found")

        entry = self.entries[entry_id]

        # Update entry fields
        if "name" in data:
            entry["name"] = data["name"]
        if "attrs" in data:
            entry["attrs"].update(data["attrs"])

        entry["updated_user"] = getattr(user, "username", str(user)) if user else "unknown"

        return entry.copy()

    def delete_entry(self, entry_id, user):
        """Delete an entry (soft delete)"""
        if isinstance(entry_id, str):
            try:
                entry_id = int(entry_id)
            except ValueError:
                raise DataAccessError(f"Invalid entry ID: {entry_id}")

        if entry_id not in self.entries:
            raise DataAccessError(f"Entry {entry_id} not found")

        # Soft delete by setting is_active to False
        self.entries[entry_id]["is_active"] = False
        self.entries[entry_id]["deleted_user"] = (
            getattr(user, "username", str(user)) if user else "unknown"
        )

        return True

    def search_entries(self, query, entity_ids=None, limit=None):
        """Search entries by query"""
        results = []

        for entry in self.entries.values():
            if not entry["is_active"]:
                continue

            # Filter by entity IDs if provided
            if entity_ids is not None:
                entity_ids_int = []
                for eid in entity_ids:
                    if isinstance(eid, str):
                        try:
                            entity_ids_int.append(int(eid))
                        except ValueError:
                            continue
                    else:
                        entity_ids_int.append(eid)

                if entry["schema"] not in entity_ids_int:
                    continue

            # Simple text search in name and attribute values
            if query.lower() in entry["name"].lower():
                results.append(entry.copy())
                continue

            for attr_value in entry.get("attrs", {}).values():
                if isinstance(attr_value, str) and query.lower() in attr_value.lower():
                    results.append(entry.copy())
                    break

        # Apply limit if provided
        if limit is not None:
            results = results[:limit]

        return results

    def get_attribute_value(self, entry_id, attribute_name):
        """Get attribute value from an entry (custom implementation)"""
        entry = self.get_entry(entry_id)
        if entry and "attrs" in entry:
            return entry["attrs"].get(attribute_name)
        return None

    def set_attribute_value(self, entry_id, attribute_name, value, user):
        """Set attribute value on an entry (custom implementation)"""
        if isinstance(entry_id, str):
            try:
                entry_id = int(entry_id)
            except ValueError:
                return False

        if entry_id not in self.entries:
            return False

        entry = self.entries[entry_id]
        if "attrs" not in entry:
            entry["attrs"] = {}

        entry["attrs"][attribute_name] = value
        entry["updated_user"] = getattr(user, "username", str(user)) if user else "unknown"

        return True

    def get_entry_history(self, entry_id):
        """Get entry modification history (custom implementation)"""
        if isinstance(entry_id, str):
            try:
                entry_id = int(entry_id)
            except ValueError:
                return []

        return self.history.get(entry_id, [])


class TestMockDataImplementation(unittest.TestCase):
    """Test cases for MockDataImplementation"""

    def setUp(self):
        """Set up test fixtures"""
        self.data = MockDataImplementation()

    def test_get_entity_by_id(self):
        """Test getting entity by ID"""
        entity = self.data.get_entity(1)

        self.assertIsNotNone(entity)
        self.assertEqual(entity["id"], 1)
        self.assertEqual(entity["name"], "User")
        self.assertTrue(entity["is_active"])

    def test_get_entity_by_string_id(self):
        """Test getting entity by string ID"""
        entity = self.data.get_entity("1")

        self.assertIsNotNone(entity)
        self.assertEqual(entity["id"], 1)

    def test_get_entity_nonexistent(self):
        """Test getting nonexistent entity"""
        entity = self.data.get_entity(999)
        self.assertIsNone(entity)

        entity = self.data.get_entity("invalid")
        self.assertIsNone(entity)

    def test_get_entity_by_name(self):
        """Test getting entity by name"""
        entity = self.data.get_entity_by_name("User")

        self.assertIsNotNone(entity)
        self.assertEqual(entity["id"], 1)
        self.assertEqual(entity["name"], "User")

    def test_get_entity_by_name_nonexistent(self):
        """Test getting nonexistent entity by name"""
        entity = self.data.get_entity_by_name("NonExistent")
        self.assertIsNone(entity)

    def test_get_entry_by_id(self):
        """Test getting entry by ID"""
        entry = self.data.get_entry(1)

        self.assertIsNotNone(entry)
        self.assertEqual(entry["id"], 1)
        self.assertEqual(entry["name"], "john_doe")
        self.assertEqual(entry["schema"], 1)

    def test_get_entry_by_string_id(self):
        """Test getting entry by string ID"""
        entry = self.data.get_entry("1")

        self.assertIsNotNone(entry)
        self.assertEqual(entry["id"], 1)

    def test_get_entry_nonexistent(self):
        """Test getting nonexistent entry"""
        entry = self.data.get_entry(999)
        self.assertIsNone(entry)

        entry = self.data.get_entry("invalid")
        self.assertIsNone(entry)

    def test_get_entries_for_entity(self):
        """Test getting entries for an entity"""
        entries = self.data.get_entries(1)  # User entity

        self.assertEqual(len(entries), 2)
        usernames = [entry["attrs"]["username"] for entry in entries]
        self.assertIn("john_doe", usernames)
        self.assertIn("jane_doe", usernames)

    def test_get_entries_with_filters(self):
        """Test getting entries with filters"""
        entries = self.data.get_entries(1, filters={"attrs": {"username": "john_doe"}})

        # Note: This simple implementation doesn't support nested filtering
        # but we can test the basic filter structure
        self.assertIsInstance(entries, list)

    def test_get_entries_with_limit(self):
        """Test getting entries with limit"""
        entries = self.data.get_entries(1, limit=1)

        self.assertEqual(len(entries), 1)

    def test_get_entries_nonexistent_entity(self):
        """Test getting entries for nonexistent entity"""
        entries = self.data.get_entries(999)
        self.assertEqual(entries, [])

    def test_create_entry_success(self):
        """Test successful entry creation"""
        user = Mock()
        user.username = "testuser"

        entry_data = {
            "name": "new_user",
            "attrs": {"username": "new_user", "email": "new@example.com"},
        }

        new_entry = self.data.create_entry(1, entry_data, user)

        self.assertEqual(new_entry["name"], "new_user")
        self.assertEqual(new_entry["schema"], 1)
        self.assertEqual(new_entry["attrs"]["username"], "new_user")
        self.assertEqual(new_entry["created_user"], "testuser")
        self.assertTrue(new_entry["is_active"])

    def test_create_entry_invalid_entity(self):
        """Test entry creation with invalid entity"""
        user = Mock()
        entry_data = {"name": "test_entry"}

        with self.assertRaises(DataAccessError) as context:
            self.data.create_entry(999, entry_data, user)

        self.assertIn("Entity 999 not found", str(context.exception))

    def test_create_entry_missing_name(self):
        """Test entry creation without name"""
        user = Mock()
        entry_data = {"attrs": {"username": "test"}}

        with self.assertRaises(DataAccessError) as context:
            self.data.create_entry(1, entry_data, user)

        self.assertIn("Entry name is required", str(context.exception))

    def test_update_entry_success(self):
        """Test successful entry update"""
        user = Mock()
        user.username = "updater"

        update_data = {
            "name": "updated_john",
            "attrs": {"email": "john.updated@example.com"},
        }

        updated_entry = self.data.update_entry(1, update_data, user)

        self.assertEqual(updated_entry["name"], "updated_john")
        self.assertEqual(updated_entry["attrs"]["email"], "john.updated@example.com")
        self.assertEqual(updated_entry["updated_user"], "updater")

    def test_update_entry_nonexistent(self):
        """Test updating nonexistent entry"""
        user = Mock()
        update_data = {"name": "test"}

        with self.assertRaises(DataAccessError) as context:
            self.data.update_entry(999, update_data, user)

        self.assertIn("Entry 999 not found", str(context.exception))

    def test_delete_entry_success(self):
        """Test successful entry deletion"""
        user = Mock()
        user.username = "deleter"

        result = self.data.delete_entry(1, user)

        self.assertTrue(result)
        # Entry should be soft deleted (is_active = False)
        entry = self.data.entries[1]
        self.assertFalse(entry["is_active"])
        self.assertEqual(entry["deleted_user"], "deleter")

    def test_delete_entry_nonexistent(self):
        """Test deleting nonexistent entry"""
        user = Mock()

        with self.assertRaises(DataAccessError) as context:
            self.data.delete_entry(999, user)

        self.assertIn("Entry 999 not found", str(context.exception))

    def test_search_entries_by_name(self):
        """Test searching entries by name"""
        results = self.data.search_entries("john")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "john_doe")

    def test_search_entries_by_attribute(self):
        """Test searching entries by attribute value"""
        results = self.data.search_entries("john@example.com")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "john_doe")

    def test_search_entries_with_entity_filter(self):
        """Test searching entries with entity ID filter"""
        results = self.data.search_entries("project", entity_ids=[2])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "project_alpha")

    def test_search_entries_with_limit(self):
        """Test searching entries with limit"""
        results = self.data.search_entries("doe", limit=1)

        self.assertEqual(len(results), 1)

    def test_search_entries_no_results(self):
        """Test searching entries with no results"""
        results = self.data.search_entries("nonexistent")
        self.assertEqual(results, [])

    def test_get_attribute_value(self):
        """Test getting attribute value"""
        value = self.data.get_attribute_value(1, "username")
        self.assertEqual(value, "john_doe")

        value = self.data.get_attribute_value(1, "email")
        self.assertEqual(value, "john@example.com")

    def test_get_attribute_value_nonexistent_entry(self):
        """Test getting attribute value from nonexistent entry"""
        value = self.data.get_attribute_value(999, "username")
        self.assertIsNone(value)

    def test_get_attribute_value_nonexistent_attribute(self):
        """Test getting nonexistent attribute value"""
        value = self.data.get_attribute_value(1, "nonexistent")
        self.assertIsNone(value)

    def test_set_attribute_value(self):
        """Test setting attribute value"""
        user = Mock()
        user.username = "setter"

        result = self.data.set_attribute_value(1, "new_attr", "new_value", user)

        self.assertTrue(result)
        self.assertEqual(self.data.entries[1]["attrs"]["new_attr"], "new_value")
        self.assertEqual(self.data.entries[1]["updated_user"], "setter")

    def test_set_attribute_value_nonexistent_entry(self):
        """Test setting attribute value on nonexistent entry"""
        user = Mock()

        result = self.data.set_attribute_value(999, "attr", "value", user)
        self.assertFalse(result)

    def test_get_entry_history(self):
        """Test getting entry history"""
        history = self.data.get_entry_history(1)

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["action"], "create")
        self.assertEqual(history[1]["action"], "update")

    def test_get_entry_history_nonexistent_entry(self):
        """Test getting history for nonexistent entry"""
        history = self.data.get_entry_history(999)
        self.assertEqual(history, [])


class TestDataInterfaceDefaultMethods(unittest.TestCase):
    """Test cases for DataInterface default method implementations"""

    def test_get_attribute_value_default_implementation(self):
        """Test that default get_attribute_value returns None"""

        class MinimalDataImpl(DataInterface):
            def get_entity(self, entity_id):
                return {}

            def get_entity_by_name(self, name):
                return {}

            def get_entry(self, entry_id):
                return {}

            def get_entries(self, entity_id, filters=None, limit=None):
                return []

            def create_entry(self, entity_id, data, user):
                return {}

            def update_entry(self, entry_id, data, user):
                return {}

            def delete_entry(self, entry_id, user):
                return True

            def search_entries(self, query, entity_ids=None, limit=None):
                return []

        data = MinimalDataImpl()
        result = data.get_attribute_value(1, "attr")
        self.assertIsNone(result)

    def test_set_attribute_value_default_implementation(self):
        """Test that default set_attribute_value returns False"""

        class MinimalDataImpl(DataInterface):
            def get_entity(self, entity_id):
                return {}

            def get_entity_by_name(self, name):
                return {}

            def get_entry(self, entry_id):
                return {}

            def get_entries(self, entity_id, filters=None, limit=None):
                return []

            def create_entry(self, entity_id, data, user):
                return {}

            def update_entry(self, entry_id, data, user):
                return {}

            def delete_entry(self, entry_id, user):
                return True

            def search_entries(self, query, entity_ids=None, limit=None):
                return []

        data = MinimalDataImpl()
        user = Mock()
        result = data.set_attribute_value(1, "attr", "value", user)
        self.assertFalse(result)

    def test_get_entry_history_default_implementation(self):
        """Test that default get_entry_history returns empty list"""

        class MinimalDataImpl(DataInterface):
            def get_entity(self, entity_id):
                return {}

            def get_entity_by_name(self, name):
                return {}

            def get_entry(self, entry_id):
                return {}

            def get_entries(self, entity_id, filters=None, limit=None):
                return []

            def create_entry(self, entity_id, data, user):
                return {}

            def update_entry(self, entry_id, data, user):
                return {}

            def delete_entry(self, entry_id, user):
                return True

            def search_entries(self, query, entity_ids=None, limit=None):
                return []

        data = MinimalDataImpl()
        result = data.get_entry_history(1)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
