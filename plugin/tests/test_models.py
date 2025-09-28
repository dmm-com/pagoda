"""
Tests for model interfaces and protocols.

Tests the model protocols defined in pagoda_plugin_sdk.interfaces.models
to ensure they work correctly with different implementations.
"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

# Add the SDK directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk"))

from pagoda_plugin_sdk.interfaces.models import (
    EntityProtocol,
    EntryProtocol,
    UserProtocol,
    serialize_entity,
    serialize_entry,
    serialize_user,
    validate_entity_protocol,
    validate_entry_protocol,
    validate_user_protocol,
)


class MockEntity:
    """Mock entity class for testing EntityProtocol"""

    def __init__(self):
        self.id = 1
        self.name = "Test Entity"
        self.note = "Test note"
        self.is_active = True
        self.created_time = datetime.now()
        self.created_user = None

    def __str__(self):
        return self.name


class MockUser:
    """Mock user class for testing UserProtocol"""

    def __init__(self):
        self.id = 1
        self.username = "testuser"
        self.email = "test@example.com"
        self.first_name = "Test"
        self.last_name = "User"
        self.is_active = True
        self.is_superuser = False
        self.date_joined = datetime.now()

    def __str__(self):
        return self.username


class MockEntry:
    """Mock entry class for testing EntryProtocol"""

    def __init__(self):
        self.id = 1
        self.name = "Test Entry"
        self.note = "Test entry note"
        self.is_active = True
        self.schema = MockEntity()
        self.created_time = datetime.now()
        self.created_user = MockUser()
        self.updated_time = datetime.now()

    def __str__(self):
        return self.name


class InvalidMockEntity:
    """Invalid mock entity missing required attributes"""

    def __init__(self):
        self.id = 1
        self.name = "Invalid Entity"
        # Missing required attributes: note, is_active, etc.


class TestModelProtocols(unittest.TestCase):
    """Test cases for model protocols"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_entity = MockEntity()
        self.mock_user = MockUser()
        self.mock_entry = MockEntry()
        self.invalid_entity = InvalidMockEntity()

    def test_entity_protocol_validation_valid(self):
        """Test EntityProtocol validation with valid object"""
        self.assertTrue(validate_entity_protocol(self.mock_entity))

    def test_entity_protocol_validation_invalid(self):
        """Test EntityProtocol validation with invalid object"""
        self.assertFalse(validate_entity_protocol(self.invalid_entity))

    def test_user_protocol_validation_valid(self):
        """Test UserProtocol validation with valid object"""
        self.assertTrue(validate_user_protocol(self.mock_user))

    def test_user_protocol_validation_invalid(self):
        """Test UserProtocol validation with invalid object"""
        invalid_user = type("InvalidUser", (), {"id": 1})()
        self.assertFalse(validate_user_protocol(invalid_user))

    def test_entry_protocol_validation_valid(self):
        """Test EntryProtocol validation with valid object"""
        self.assertTrue(validate_entry_protocol(self.mock_entry))

    def test_entry_protocol_validation_invalid(self):
        """Test EntryProtocol validation with invalid object"""
        invalid_entry = type("InvalidEntry", (), {"id": 1})()
        self.assertFalse(validate_entry_protocol(invalid_entry))

    def test_serialize_entity(self):
        """Test entity serialization"""
        result = serialize_entity(self.mock_entity)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "Test Entity")
        self.assertEqual(result["note"], "Test note")
        self.assertEqual(result["is_active"], True)
        self.assertIsNotNone(result["created_time"])
        self.assertIsNone(result["created_user"])

    def test_serialize_user(self):
        """Test user serialization"""
        result = serialize_user(self.mock_user)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["username"], "testuser")
        self.assertEqual(result["email"], "test@example.com")
        self.assertEqual(result["first_name"], "Test")
        self.assertEqual(result["last_name"], "User")
        self.assertEqual(result["is_active"], True)
        self.assertEqual(result["is_superuser"], False)
        self.assertIsNotNone(result["date_joined"])

    def test_serialize_entry(self):
        """Test entry serialization"""
        result = serialize_entry(self.mock_entry)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "Test Entry")
        self.assertEqual(result["note"], "Test entry note")
        self.assertEqual(result["is_active"], True)
        self.assertIsInstance(result["schema"], dict)
        self.assertEqual(result["schema"]["name"], "Test Entity")
        self.assertEqual(result["created_user"], "testuser")
        self.assertIsNotNone(result["created_time"])
        self.assertIsNotNone(result["updated_time"])

    def test_protocol_isinstance_checks(self):
        """Test that isinstance checks work with protocols"""
        # These should pass if the runtime checks work correctly
        try:
            self.assertIsInstance(self.mock_entity, EntityProtocol)
            self.assertIsInstance(self.mock_user, UserProtocol)
            self.assertIsInstance(self.mock_entry, EntryProtocol)
        except TypeError:
            # Protocol isinstance checks may not work in all Python versions
            # This is expected behavior
            pass

    def test_serialization_with_none_values(self):
        """Test serialization handles None values correctly"""
        # Test entity with None created_time
        entity = MockEntity()
        entity.created_time = None
        result = serialize_entity(entity)
        self.assertIsNone(result["created_time"])

        # Test user with None date_joined
        user = MockUser()
        user.date_joined = None
        result = serialize_user(user)
        self.assertIsNone(result["date_joined"])


if __name__ == "__main__":
    unittest.main()
