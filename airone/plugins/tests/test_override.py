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

        retrieved = self.registry.get_handler(42, OperationType.CREATE)
        self.assertEqual(retrieved, handler)

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

        self.assertEqual(
            self.registry.get_handler(42, OperationType.CREATE),
            create_handler,
        )
        self.assertEqual(
            self.registry.get_handler(42, OperationType.UPDATE),
            update_handler,
        )

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

        self.assertEqual(
            self.registry.get_handler(42, OperationType.CREATE),
            handler_42,
        )
        self.assertEqual(
            self.registry.get_handler(99, OperationType.CREATE),
            handler_99,
        )

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

    def test_get_handler_not_found(self):
        """Test getting handler for non-existent registration."""
        result = self.registry.get_handler(999, OperationType.CREATE)
        self.assertIsNone(result)

    def test_get_handler_entity_exists_operation_not(self):
        """Test getting handler when entity exists but operation doesn't."""
        handler = MagicMock()
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
        )

        result = self.registry.get_handler(42, OperationType.UPDATE)
        self.assertIsNone(result)

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

    def test_has_override_entity_level(self):
        """Test checking if entity has any overrides."""
        self.assertFalse(self.registry.has_override(42))

        handler = MagicMock()
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
        )

        self.assertTrue(self.registry.has_override(42))

    def test_has_override_operation_level(self):
        """Test checking if specific operation has override."""
        handler = MagicMock()
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
        )

        self.assertTrue(self.registry.has_override(42, OperationType.CREATE))
        self.assertFalse(self.registry.has_override(42, OperationType.UPDATE))

    def test_unregister_success(self):
        """Test unregistering an override."""
        handler = MagicMock()
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
        )

        result = self.registry.unregister(42, OperationType.CREATE, "test-plugin")
        self.assertTrue(result)
        self.assertIsNone(self.registry.get_handler(42, OperationType.CREATE))

    def test_unregister_wrong_plugin(self):
        """Test unregistering with wrong plugin ID fails."""
        handler = MagicMock()
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="plugin-a",
        )

        result = self.registry.unregister(42, OperationType.CREATE, "plugin-b")
        self.assertFalse(result)
        # Original handler should still be there
        self.assertEqual(
            self.registry.get_handler(42, OperationType.CREATE),
            handler,
        )

    def test_unregister_not_found(self):
        """Test unregistering non-existent override."""
        result = self.registry.unregister(999, OperationType.CREATE, "test")
        self.assertFalse(result)

    def test_unregister_plugin(self):
        """Test unregistering all overrides for a plugin."""
        handler1 = MagicMock()
        handler2 = MagicMock()
        handler3 = MagicMock()

        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler1,
            plugin_id="plugin-a",
        )
        self.registry.register(
            entity_id=42,
            operation=OperationType.UPDATE,
            handler=handler2,
            plugin_id="plugin-a",
        )
        self.registry.register(
            entity_id=99,
            operation=OperationType.CREATE,
            handler=handler3,
            plugin_id="plugin-b",
        )

        count = self.registry.unregister_plugin("plugin-a")
        self.assertEqual(count, 2)

        self.assertIsNone(self.registry.get_handler(42, OperationType.CREATE))
        self.assertIsNone(self.registry.get_handler(42, OperationType.UPDATE))
        self.assertEqual(
            self.registry.get_handler(99, OperationType.CREATE),
            handler3,
        )

    def test_get_overridden_entity_ids(self):
        """Test getting all entity IDs with overrides."""
        self.assertEqual(self.registry.get_overridden_entity_ids(), set())

        handler = MagicMock()
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="test-plugin",
        )
        self.registry.register(
            entity_id=99,
            operation=OperationType.UPDATE,
            handler=handler,
            plugin_id="test-plugin",
        )

        entity_ids = self.registry.get_overridden_entity_ids()
        self.assertEqual(entity_ids, {42, 99})

    def test_get_plugin_overrides(self):
        """Test getting all overrides for a specific plugin."""
        handler = MagicMock()
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="plugin-a",
        )
        self.registry.register(
            entity_id=42,
            operation=OperationType.UPDATE,
            handler=handler,
            plugin_id="plugin-a",
        )
        self.registry.register(
            entity_id=99,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="plugin-b",
        )

        overrides = self.registry.get_plugin_overrides("plugin-a")
        self.assertEqual(len(overrides), 2)
        self.assertTrue(all(o.plugin_id == "plugin-a" for o in overrides))

    def test_get_all_registrations(self):
        """Test getting all registrations."""
        handler = MagicMock()
        self.registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=handler,
            plugin_id="plugin-a",
        )
        self.registry.register(
            entity_id=99,
            operation=OperationType.UPDATE,
            handler=handler,
            plugin_id="plugin-b",
        )

        all_regs = self.registry.get_all_registrations()
        self.assertEqual(len(all_regs), 2)

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

        self.assertIsNone(self.registry.get_handler(42, OperationType.CREATE))
        self.assertEqual(self.registry.get_overridden_entity_ids(), set())


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
        self.assertTrue(self.registry.has_override(42, OperationType.CREATE))
        self.assertTrue(self.registry.has_override(42, OperationType.UPDATE))
        self.assertEqual(len(self.registry.get_all_registrations()), 2)

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
        self.assertEqual(len(self.registry.get_all_registrations()), 0)

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
        self.assertEqual(len(self.registry.get_all_registrations()), 0)


if __name__ == "__main__":
    unittest.main()
