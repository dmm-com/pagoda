"""
Tests for the override_manager module.

These tests verify the OverrideRegistry functionality for plugin
entry operation overrides using ID-based entity registration.
"""

import unittest
from unittest.mock import MagicMock

from airone.plugins.override_manager import (
    OperationType,
    OverrideConflictError,
    OverrideRegistration,
    OverrideRegistry,
)


class TestOperationType(unittest.TestCase):
    """Tests for OperationType enum."""

    def test_operation_types_exist(self):
        """Verify all expected operation types exist."""
        self.assertEqual(OperationType.CREATE.value, "create")
        self.assertEqual(OperationType.RETRIEVE.value, "retrieve")
        self.assertEqual(OperationType.UPDATE.value, "update")
        self.assertEqual(OperationType.DELETE.value, "delete")
        self.assertEqual(OperationType.LIST.value, "list")

    def test_from_string_valid(self):
        """Test converting valid strings to OperationType."""
        self.assertEqual(OperationType.from_string("create"), OperationType.CREATE)
        self.assertEqual(OperationType.from_string("CREATE"), OperationType.CREATE)
        self.assertEqual(OperationType.from_string("Update"), OperationType.UPDATE)

    def test_from_string_invalid(self):
        """Test converting invalid string raises ValueError."""
        with self.assertRaises(ValueError) as context:
            OperationType.from_string("invalid")
        self.assertIn("Invalid operation type", str(context.exception))


class TestOverrideRegistration(unittest.TestCase):
    """Tests for OverrideRegistration dataclass."""

    def test_registration_creation(self):
        """Test creating an OverrideRegistration."""
        handler = MagicMock()
        reg = OverrideRegistration(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
            params={"config_id": 99},
            priority=10,
        )

        self.assertEqual(reg.entity_id, 42)
        self.assertEqual(reg.operation, OperationType.CREATE)
        self.assertEqual(reg.handler, handler)
        self.assertEqual(reg.plugin_id, "test-plugin")
        self.assertEqual(reg.params, {"config_id": 99})
        self.assertEqual(reg.priority, 10)

    def test_registration_default_params(self):
        """Test registration with default empty params."""
        handler = MagicMock()
        reg = OverrideRegistration(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
        )
        self.assertEqual(reg.params, {})

    def test_registration_repr(self):
        """Test registration string representation."""
        handler = MagicMock()
        reg = OverrideRegistration(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
        )
        repr_str = repr(reg)
        self.assertIn("42", repr_str)
        self.assertIn("create", repr_str)
        self.assertIn("test-plugin", repr_str)


class TestOverrideRegistry(unittest.TestCase):
    """Tests for OverrideRegistry class."""

    def setUp(self):
        """Set up a fresh registry for each test."""
        self.registry = OverrideRegistry()

    def test_register_single_handler(self):
        """Test registering a single override handler."""
        handler = MagicMock()
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
        )

        registration = self.registry.get_registration(42, OperationType.CREATE)
        self.assertIsNotNone(registration)
        self.assertEqual(registration.handler, handler)

    def test_register_with_params(self):
        """Test registering handler with params."""
        handler = MagicMock()
        params = {"configuration_entity_id": 99, "cascade_delete": True}
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
            params=params,
        )

        registration = self.registry.get_registration(42, OperationType.CREATE)
        self.assertIsNotNone(registration)
        self.assertEqual(registration.params, params)

    def test_register_multiple_operations_same_entity(self):
        """Test registering multiple operations for same entity."""
        create_handler = MagicMock()
        update_handler = MagicMock()

        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=create_handler,
            plugin_id="test-plugin",
        )
        self.registry.register(
            entity_id=42,
            operation=OperationType.UPDATE,
            handler=update_handler,
            plugin_id="test-plugin",
        )

        create_reg = self.registry.get_registration(42, OperationType.CREATE)
        update_reg = self.registry.get_registration(42, OperationType.UPDATE)
        self.assertEqual(create_reg.handler, create_handler)
        self.assertEqual(update_reg.handler, update_handler)

    def test_register_same_operation_different_entities(self):
        """Test registering same operation for different entities."""
        handler_42 = MagicMock()
        handler_99 = MagicMock()

        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler_42,
            plugin_id="plugin-a",
        )
        self.registry.register(
            entity_id=99,
            operation=OperationType.CREATE,
            handler=handler_99,
            plugin_id="plugin-b",
        )

        reg_42 = self.registry.get_registration(42, OperationType.CREATE)
        reg_99 = self.registry.get_registration(99, OperationType.CREATE)
        self.assertEqual(reg_42.handler, handler_42)
        self.assertEqual(reg_99.handler, handler_99)

    def test_register_conflict_raises_error(self):
        """Test that registering conflicting handler raises error."""
        handler1 = MagicMock()
        handler2 = MagicMock()

        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler1,
            plugin_id="plugin-a",
        )

        with self.assertRaises(OverrideConflictError) as context:
            self.registry.register(
                entity_id=42,
                operation=OperationType.CREATE,
                handler=handler2,
                plugin_id="plugin-b",
            )

        error = context.exception
        self.assertEqual(error.entity_id, 42)
        self.assertEqual(error.operation, "create")
        self.assertEqual(error.existing_plugin, "plugin-a")
        self.assertEqual(error.new_plugin, "plugin-b")

    def test_get_registration(self):
        """Test getting full registration info."""
        handler = MagicMock()
        params = {"key": "value"}
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
            params=params,
            priority=5,
        )

        reg = self.registry.get_registration(42, OperationType.CREATE)
        self.assertIsNotNone(reg)
        self.assertEqual(reg.entity_id, 42)
        self.assertEqual(reg.operation, OperationType.CREATE)
        self.assertEqual(reg.plugin_id, "test-plugin")
        self.assertEqual(reg.params, params)
        self.assertEqual(reg.priority, 5)

    def test_get_registration_not_found(self):
        """Test getting registration for non-existent entity returns None."""
        result = self.registry.get_registration(999, OperationType.CREATE)
        self.assertIsNone(result)

    def test_get_registration_entity_exists_operation_not(self):
        """Test getting registration when entity exists but operation doesn't."""
        handler = MagicMock()
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
        )

        result = self.registry.get_registration(42, OperationType.UPDATE)
        self.assertIsNone(result)

    def test_clear(self):
        """Test clearing all registrations."""
        handler = MagicMock()
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
        )

        self.registry.clear()

        self.assertIsNone(self.registry.get_registration(42, OperationType.CREATE))


class TestOverrideConflictError(unittest.TestCase):
    """Tests for OverrideConflictError exception."""

    def test_error_message(self):
        """Test error message contains all relevant info."""
        error = OverrideConflictError(
            entity_id=42,
            operation="create",
            existing_plugin="plugin-a",
            new_plugin="plugin-b",
        )

        message = str(error)
        self.assertIn("42", message)
        self.assertIn("create", message)
        self.assertIn("plugin-a", message)
        self.assertIn("plugin-b", message)

    def test_error_attributes(self):
        """Test error has correct attributes."""
        error = OverrideConflictError(
            entity_id=42,
            operation="create",
            existing_plugin="plugin-a",
            new_plugin="plugin-b",
        )

        self.assertEqual(error.entity_id, 42)
        self.assertEqual(error.operation, "create")
        self.assertEqual(error.existing_plugin, "plugin-a")
        self.assertEqual(error.new_plugin, "plugin-b")


class TestLoadFromSettings(unittest.TestCase):
    """Tests for load_from_settings functionality."""

    def setUp(self):
        """Set up a fresh registry for each test."""
        self.registry = OverrideRegistry()

    def test_load_from_settings_basic(self):
        """Test loading registrations from settings config."""
        # Mock plugin registry
        mock_plugin = MagicMock()
        mock_plugin.validate_params.return_value = {"config_id": 99}
        mock_handler = MagicMock()
        mock_plugin.get_handler.return_value = mock_handler

        mock_plugin_registry = MagicMock()
        mock_plugin_registry.get.return_value = mock_plugin

        settings_config = {
            "42": {
                "plugin": "cross-entity-sample",
                "operations": ["create", "update"],
                "params": {"config_id": 99},
            }
        }

        self.registry.load_from_settings(settings_config, mock_plugin_registry)

        # Verify registrations were created
        create_reg = self.registry.get_registration(42, OperationType.CREATE)
        update_reg = self.registry.get_registration(42, OperationType.UPDATE)
        self.assertIsNotNone(create_reg)
        self.assertIsNotNone(update_reg)

    def test_load_from_settings_missing_plugin(self):
        """Test load_from_settings handles missing plugin gracefully."""
        mock_plugin_registry = MagicMock()
        mock_plugin_registry.get.return_value = None

        settings_config = {
            "42": {
                "plugin": "nonexistent-plugin",
                "operations": ["create"],
            }
        }

        # Should not raise, just log warning
        self.registry.load_from_settings(settings_config, mock_plugin_registry)
        self.assertIsNone(self.registry.get_registration(42, OperationType.CREATE))

    def test_load_from_settings_invalid_entity_id(self):
        """Test load_from_settings handles invalid entity ID gracefully."""
        mock_plugin_registry = MagicMock()

        settings_config = {
            "not-a-number": {
                "plugin": "test-plugin",
                "operations": ["create"],
            }
        }

        # Should not raise, just log warning
        self.registry.load_from_settings(settings_config, mock_plugin_registry)
        # No registrations should exist
        self.assertIsNone(self.registry.get_registration(42, OperationType.CREATE))


if __name__ == "__main__":
    unittest.main()
