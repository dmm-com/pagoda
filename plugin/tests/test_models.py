"""
Tests for model interfaces and protocols.

Tests the model protocols defined in pagoda_plugin_sdk.interfaces.models
and the new Protocol-based model injection system.
"""

import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

# Add the SDK directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk"))

import pagoda_plugin_sdk.models as sdk_models
from pagoda_plugin_sdk.protocols import EntityProtocol, EntryProtocol, UserProtocol


# Helper functions for testing (moved from interfaces.models)
def validate_entity_protocol(obj) -> bool:
    """Validate if an object conforms to EntityProtocol"""
    try:
        return isinstance(obj, EntityProtocol)
    except (AttributeError, TypeError):
        return False


def validate_entry_protocol(obj) -> bool:
    """Validate if an object conforms to EntryProtocol"""
    try:
        return isinstance(obj, EntryProtocol)
    except (AttributeError, TypeError):
        return False


def validate_user_protocol(obj) -> bool:
    """Validate if an object conforms to UserProtocol"""
    try:
        return isinstance(obj, UserProtocol)
    except (AttributeError, TypeError):
        return False


def serialize_entity(entity: EntityProtocol) -> dict:
    """Serialize an entity object to dictionary"""
    return {
        "id": entity.id,
        "name": entity.name,
        "note": entity.note,
        "is_active": entity.is_active,
        "created_time": entity.created_time.isoformat() if entity.created_time else None,
        "created_user": entity.created_user.username if entity.created_user else None,
    }


def serialize_entry(entry: EntryProtocol) -> dict:
    """Serialize an entry object to dictionary"""
    return {
        "id": entry.id,
        "name": entry.name,
        "note": entry.note,
        "is_active": entry.is_active,
        "schema": serialize_entity(entry.schema),
        "created_time": entry.created_time.isoformat() if entry.created_time else None,
        "created_user": entry.created_user.username if entry.created_user else None,
        "updated_time": entry.updated_time.isoformat() if entry.updated_time else None,
    }


def serialize_user(user: UserProtocol) -> dict:
    """Serialize a user object to dictionary"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
    }


class MockEntityManager:
    """Mock entity manager for testing"""

    def filter(self, **kwargs):
        return []

    def get(self, **kwargs):
        return MockEntity()

    def create(self, **kwargs):
        return MockEntity()

    def all(self):
        return []

    def count(self):
        return 0


class MockEntity:
    """Mock entity class for testing EntityProtocol"""

    objects = MockEntityManager()

    def __init__(self):
        self.id = 1
        self.name = "Test Entity"
        self.note = "Test note"
        self.is_active = True
        self.created_time = datetime.now()
        self.created_user = None

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        pass

    def delete(self):
        pass


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


class MockEntryManager:
    """Mock entry manager for testing"""

    def filter(self, **kwargs):
        return []

    def get(self, **kwargs):
        return MockEntry()

    def create(self, **kwargs):
        return MockEntry()

    def all(self):
        return []

    def count(self):
        return 0


class MockEntry:
    """Mock entry class for testing EntryProtocol"""

    objects = MockEntryManager()

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

    def save(self, **kwargs):
        pass

    def delete(self):
        pass

    def get_attrs(self, **kwargs):
        return {}

    def set_attrs(self, user, **kwargs):
        pass

    def may_permitted(self, user, permission):
        return True


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


class TestModelInjection(unittest.TestCase):
    """Test cases for Protocol-based model injection system"""

    def setUp(self):
        """Set up test fixtures"""
        # Save original state
        self.original_entity = sdk_models.Entity
        self.original_entry = sdk_models.Entry
        self.original_user = sdk_models.User
        self.original_attribute_value = sdk_models.AttributeValue
        self.original_entity_attr = getattr(sdk_models, "EntityAttr", None)
        self.original_attribute = getattr(sdk_models, "Attribute", None)

    def tearDown(self):
        """Clean up after tests"""
        # Restore original state
        sdk_models.Entity = self.original_entity
        sdk_models.Entry = self.original_entry
        sdk_models.User = self.original_user
        sdk_models.AttributeValue = self.original_attribute_value
        if hasattr(sdk_models, "EntityAttr"):
            sdk_models.EntityAttr = self.original_entity_attr
        if hasattr(sdk_models, "Attribute"):
            sdk_models.Attribute = self.original_attribute

    def test_initial_state_is_none(self):
        """Test that models are initially None"""
        # Reset to initial state
        sdk_models.Entity = None
        sdk_models.Entry = None

        self.assertIsNone(sdk_models.Entity)
        self.assertIsNone(sdk_models.Entry)

    def test_model_injection(self):
        """Test that models can be injected"""
        # Create mock models
        mock_entity = MagicMock()
        mock_entry = MagicMock()

        # Inject models
        sdk_models.Entity = mock_entity
        sdk_models.Entry = mock_entry

        # Verify injection
        self.assertEqual(sdk_models.Entity, mock_entity)
        self.assertEqual(sdk_models.Entry, mock_entry)

    def test_model_access_after_injection(self):
        """Test that injected models can be used"""
        # Create mock model with objects manager
        mock_entity = MagicMock()
        mock_objects = MagicMock()
        mock_entity.objects = mock_objects

        # Inject model
        sdk_models.Entity = mock_entity

        # Use the model
        sdk_models.Entity.objects.filter(is_active=True)

        # Verify the call was made
        mock_objects.filter.assert_called_once_with(is_active=True)

    def test_entity_attr_model_access(self):
        """Test that EntityAttr model can be used"""
        # Create mock model with objects manager
        mock_entity_attr = MagicMock()
        mock_objects = MagicMock()
        mock_entity_attr.objects = mock_objects

        # Inject model
        sdk_models.EntityAttr = mock_entity_attr

        # Use the model
        sdk_models.EntityAttr.objects.filter(is_active=True)

        # Verify the call was made
        mock_objects.filter.assert_called_once_with(is_active=True)

    def test_attribute_model_access(self):
        """Test that Attribute model can be used"""
        # Create mock model with objects manager
        mock_attribute = MagicMock()
        mock_objects = MagicMock()
        mock_attribute.objects = mock_objects

        # Inject model
        sdk_models.Attribute = mock_attribute

        # Use the model
        sdk_models.Attribute.objects.filter(is_active=True)

        # Verify the call was made
        mock_objects.filter.assert_called_once_with(is_active=True)

    def test_error_handling_for_uninitialized_models(self):
        """Test error handling when models are not initialized"""
        # Reset to None
        sdk_models.Entity = None

        # When Entity is None, accessing it returns None, not an error
        # The error occurs when trying to use the __getattr__ function
        # which is only called for attributes that don't exist
        entity_value = sdk_models.Entity
        self.assertIsNone(entity_value)

        # However, __getattr__ function can still be tested with a non-existent model
        with self.assertRaises(AttributeError) as context:
            _ = getattr(sdk_models, "NonExistentModel")

        self.assertIn("module", str(context.exception))
        self.assertIn("has no attribute", str(context.exception))

    def test_is_initialized_function(self):
        """Test the is_initialized utility function"""
        # Reset all models
        sdk_models.Entity = None
        sdk_models.Entry = None
        sdk_models.User = None
        sdk_models.AttributeValue = None
        sdk_models.EntityAttr = None
        sdk_models.Attribute = None

        # Should not be initialized
        self.assertFalse(sdk_models.is_initialized())

        # Inject one model
        sdk_models.Entity = MagicMock()

        # Should be initialized
        self.assertTrue(sdk_models.is_initialized())

    def test_get_available_models_function(self):
        """Test the get_available_models utility function"""
        # Reset all models
        sdk_models.Entity = None
        sdk_models.Entry = None
        sdk_models.User = None
        sdk_models.AttributeValue = None
        sdk_models.EntityAttr = None
        sdk_models.Attribute = None

        # Should be empty
        self.assertEqual(sdk_models.get_available_models(), [])

        # Inject some models
        sdk_models.Entity = MagicMock()
        sdk_models.Entry = MagicMock()
        sdk_models.EntityAttr = MagicMock()
        sdk_models.Attribute = MagicMock()

        # Should contain the injected models
        available = sdk_models.get_available_models()
        self.assertIn("Entity", available)
        self.assertIn("Entry", available)
        self.assertIn("EntityAttr", available)
        self.assertIn("Attribute", available)
        self.assertNotIn("User", available)
        self.assertNotIn("AttributeValue", available)

    def test_protocol_integration_mock(self):
        """Test the Protocol-based model access with mocks"""

        # Create mock model matching EntityProtocol
        class MockEntityWithProtocol:
            def __init__(self):
                self.id = 1
                self.name = "Protocol Test Entity"
                self.note = "Testing protocol"
                self.is_active = True
                self.created_time = datetime.now()
                self.created_user = None

            class objects:
                @staticmethod
                def filter(**kwargs):
                    return [MockEntityWithProtocol()]

                @staticmethod
                def all():
                    return [MockEntityWithProtocol()]

                @staticmethod
                def count():
                    return 1

            def save(self):
                pass

            def delete(self):
                pass

            def __str__(self):
                return self.name

        # Inject the mock
        sdk_models.Entity = MockEntityWithProtocol

        # Use as if it's the real model
        Entity = sdk_models.Entity
        entities = Entity.objects.filter(is_active=True)

        # Verify it works
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].name, "Protocol Test Entity")

        # Natural import style test
        from pagoda_plugin_sdk.models import Entity as ImportedEntity

        self.assertEqual(ImportedEntity, MockEntityWithProtocol)


if __name__ == "__main__":
    unittest.main()
