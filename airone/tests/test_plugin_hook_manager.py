"""
Tests for Hook Manager

Tests the core functionality of the hook manager including registration,
execution, and priority handling.
"""

import unittest
from unittest.mock import patch

from airone.plugins.hook_manager import HookManager


class TestHookManager(unittest.TestCase):
    """Test cases for HookManager"""

    def setUp(self):
        """Set up test fixtures"""
        self.hook_manager = HookManager()

    def test_register_hook(self):
        """Test hook registration"""

        def test_handler():
            return "test"

        self.hook_manager.register_hook("test.hook", test_handler, "test-plugin")

        self.assertEqual(len(self.hook_manager._hooks["test.hook"]), 1)
        self.assertEqual(self.hook_manager._hooks["test.hook"][0]["plugin_id"], "test-plugin")
        self.assertEqual(self.hook_manager._stats["total_registered"], 1)

    def test_register_multiple_hooks(self):
        """Test registering multiple hooks for the same hook point"""

        def handler1():
            return "handler1"

        def handler2():
            return "handler2"

        self.hook_manager.register_hook("test.hook", handler1, "plugin1")
        self.hook_manager.register_hook("test.hook", handler2, "plugin2")

        self.assertEqual(len(self.hook_manager._hooks["test.hook"]), 2)

    def test_hook_priority(self):
        """Test hook execution priority"""
        results = []

        def handler_low():
            results.append("low")

        def handler_high():
            results.append("high")

        # Register with different priorities (lower number = higher priority)
        self.hook_manager.register_hook("test.hook", handler_low, "plugin1", priority=200)
        self.hook_manager.register_hook("test.hook", handler_high, "plugin2", priority=50)

        # Verify hooks are sorted by priority
        self.assertEqual(self.hook_manager._hooks["test.hook"][0]["priority"], 50)
        self.assertEqual(self.hook_manager._hooks["test.hook"][1]["priority"], 200)

    @patch("airone.plugins.hooks.normalize_hook_name")
    def test_has_hook(self, mock_normalize):
        """Test checking if hook is registered"""
        mock_normalize.return_value = "test.hook"

        def test_handler():
            pass

        # Initially no hook
        self.assertFalse(self.hook_manager.has_hook("test.hook"))

        # After registration
        self.hook_manager.register_hook("test.hook", test_handler, "test-plugin")
        self.assertTrue(self.hook_manager.has_hook("test.hook"))

    @patch("airone.plugins.hooks.normalize_hook_name")
    def test_execute_hook(self, mock_normalize):
        """Test hook execution"""
        mock_normalize.return_value = "test.hook"

        def test_handler(*args, **kwargs):
            return f"called with {args} {kwargs}"

        self.hook_manager.register_hook("test.hook", test_handler, "test-plugin")

        results = self.hook_manager.execute_hook("test.hook", "arg1", key="value")

        self.assertEqual(len(results), 1)
        self.assertIn("arg1", results[0])
        self.assertIn("value", results[0])

    @patch("airone.plugins.hooks.normalize_hook_name")
    def test_execute_hook_with_entity_name(self, mock_normalize):
        """Test hook execution with entity_name parameter for lifecycle hooks"""
        mock_normalize.return_value = "entry.after_create"

        received_args = []

        def test_handler(*args, **kwargs):
            received_args.extend(args)
            return "ok"

        self.hook_manager.register_hook("entry.after_create", test_handler, "test-plugin")

        self.hook_manager.execute_hook("entry.after_create", entity_name="TestEntity")

        # For lifecycle hooks, entity_name should be the first positional argument
        self.assertEqual(len(received_args), 1)
        self.assertEqual(received_args[0], "TestEntity")

    @patch("airone.plugins.hooks.normalize_hook_name")
    def test_execute_hook_returns_none_skipped(self, mock_normalize):
        """Test that hooks returning None are not included in results"""
        mock_normalize.return_value = "test.hook"

        def handler1():
            return "result1"

        def handler2():
            return None

        def handler3():
            return "result3"

        self.hook_manager.register_hook("test.hook", handler1, "plugin1")
        self.hook_manager.register_hook("test.hook", handler2, "plugin2")
        self.hook_manager.register_hook("test.hook", handler3, "plugin3")

        results = self.hook_manager.execute_hook("test.hook")

        self.assertEqual(len(results), 2)
        self.assertIn("result1", results)
        self.assertIn("result3", results)

    @patch("airone.plugins.hooks.normalize_hook_name")
    def test_execute_hook_error_handling(self, mock_normalize):
        """Test that hook execution errors are caught and logged"""
        mock_normalize.return_value = "test.hook"

        def failing_handler():
            raise ValueError("Test error")

        def working_handler():
            return "success"

        self.hook_manager.register_hook("test.hook", failing_handler, "bad-plugin")
        self.hook_manager.register_hook("test.hook", working_handler, "good-plugin")

        results = self.hook_manager.execute_hook("test.hook")

        # Should have one success despite one failure
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "success")
        self.assertEqual(self.hook_manager._stats["total_failed"], 1)

    def test_get_registered_hooks(self):
        """Test getting list of registered hooks"""

        def handler():
            pass

        self.hook_manager.register_hook("hook1", handler, "plugin1")
        self.hook_manager.register_hook("hook2", handler, "plugin1")

        hooks = self.hook_manager.get_registered_hooks()

        self.assertEqual(len(hooks), 2)
        self.assertIn("hook1", hooks)
        self.assertIn("hook2", hooks)

    def test_get_hooks_for_plugin(self):
        """Test getting hooks registered by specific plugin"""

        def handler():
            pass

        self.hook_manager.register_hook("hook1", handler, "plugin1")
        self.hook_manager.register_hook("hook2", handler, "plugin1")
        self.hook_manager.register_hook("hook3", handler, "plugin2")

        plugin1_hooks = self.hook_manager.get_hooks_for_plugin("plugin1")

        self.assertEqual(len(plugin1_hooks), 2)
        self.assertIn("hook1", plugin1_hooks)
        self.assertIn("hook2", plugin1_hooks)
        self.assertNotIn("hook3", plugin1_hooks)

    def test_get_statistics(self):
        """Test getting hook statistics"""

        def handler():
            return "ok"

        self.hook_manager.register_hook("hook1", handler, "plugin1")
        self.hook_manager.register_hook("hook2", handler, "plugin1")

        stats = self.hook_manager.get_statistics()

        self.assertEqual(stats["total_registered"], 2)
        self.assertEqual(stats["registered_hooks"], 2)
        self.assertIn("hook1", stats["hooks"])
        self.assertIn("hook2", stats["hooks"])

    def test_unregister_plugin_hooks(self):
        """Test unregistering all hooks for a plugin"""

        def handler():
            pass

        self.hook_manager.register_hook("hook1", handler, "plugin1")
        self.hook_manager.register_hook("hook2", handler, "plugin1")
        self.hook_manager.register_hook("hook3", handler, "plugin2")

        count = self.hook_manager.unregister_plugin_hooks("plugin1")

        self.assertEqual(count, 2)
        self.assertEqual(len(self.hook_manager.get_hooks_for_plugin("plugin1")), 0)
        self.assertEqual(len(self.hook_manager.get_hooks_for_plugin("plugin2")), 1)

    @patch("airone.plugins.hooks.normalize_hook_name")
    def test_register_hook_with_entity(self, mock_normalize):
        """Test registering hook with entity filter"""
        mock_normalize.return_value = "entry.after_create"

        def test_handler(*args, **kwargs):
            return "ok"

        self.hook_manager.register_hook(
            "entry.after_create", test_handler, "test-plugin", entity="an"
        )

        self.assertEqual(len(self.hook_manager._hooks["entry.after_create"]), 1)
        self.assertEqual(self.hook_manager._hooks["entry.after_create"][0]["entity"], "an")

    @patch("airone.plugins.hooks.normalize_hook_name")
    def test_has_hook_with_entity_filter(self, mock_normalize):
        """Test has_hook respects entity filtering"""
        mock_normalize.return_value = "entry.after_create"

        def test_handler(*args, **kwargs):
            return "ok"

        # Register hook for specific entity
        self.hook_manager.register_hook(
            "entry.after_create", test_handler, "test-plugin", entity="an"
        )

        # Should return True for matching entity
        self.assertTrue(self.hook_manager.has_hook("entry.after_create", entity_name="an"))

        # Should return False for non-matching entity
        self.assertFalse(self.hook_manager.has_hook("entry.after_create", entity_name="bn"))

        # Should return True when no entity_name specified (checking if hook exists at all)
        self.assertTrue(self.hook_manager.has_hook("entry.after_create"))

    @patch("airone.plugins.hooks.normalize_hook_name")
    def test_execute_hook_with_entity_filter(self, mock_normalize):
        """Test execute_hook filters by entity"""
        mock_normalize.return_value = "entry.after_create"

        executed_entities = []

        def handler_for_an(entity_name, *args, **kwargs):
            executed_entities.append(entity_name)
            return "an"

        def handler_for_bn(entity_name, *args, **kwargs):
            executed_entities.append(entity_name)
            return "bn"

        def handler_for_all(entity_name, *args, **kwargs):
            executed_entities.append(entity_name)
            return "all"

        # Register hooks with different entity filters
        self.hook_manager.register_hook(
            "entry.after_create", handler_for_an, "plugin1", entity="an"
        )
        self.hook_manager.register_hook(
            "entry.after_create", handler_for_bn, "plugin2", entity="bn"
        )
        self.hook_manager.register_hook(
            "entry.after_create", handler_for_all, "plugin3", entity=None
        )

        # Execute for entity 'an'
        results = self.hook_manager.execute_hook("entry.after_create", entity_name="an")

        # Should execute handler_for_an and handler_for_all, but not handler_for_bn
        self.assertEqual(len(results), 2)
        self.assertIn("an", results)
        self.assertIn("all", results)
        self.assertNotIn("bn", results)

        # Verify executed_entities
        self.assertIn("an", executed_entities)
        self.assertEqual(executed_entities.count("an"), 2)  # Once for each executed handler


if __name__ == "__main__":
    unittest.main()
