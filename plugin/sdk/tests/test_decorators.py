"""
Tests for plugin decorators
"""

import unittest

from pagoda_plugin_sdk import Plugin
from pagoda_plugin_sdk.decorators import entity_hook, entry_hook, get_attrs_hook, validation_hook


class TestDecorators(unittest.TestCase):
    """Test cases for plugin decorators"""

    def test_entry_hook_decorator(self):
        """Test entry_hook decorator adds metadata"""

        @entry_hook("after_create", entity="test_entity", priority=50)
        def test_handler(self):
            return "test"

        self.assertTrue(hasattr(test_handler, "_hook_metadata"))
        metadata = test_handler._hook_metadata
        self.assertEqual(metadata["hook_name"], "entry.after_create")
        self.assertEqual(metadata["entity"], "test_entity")
        self.assertEqual(metadata["priority"], 50)

    def test_entity_hook_decorator(self):
        """Test entity_hook decorator adds metadata"""

        @entity_hook("after_create", priority=100)
        def test_handler(self):
            return "test"

        self.assertTrue(hasattr(test_handler, "_hook_metadata"))
        metadata = test_handler._hook_metadata
        self.assertEqual(metadata["hook_name"], "entity.after_create")
        self.assertEqual(metadata["priority"], 100)
        self.assertIsNone(metadata["entity"])

    def test_validation_hook_decorator(self):
        """Test validation_hook decorator adds metadata"""

        @validation_hook(entity="test_entity")
        def test_handler(self):
            return "test"

        self.assertTrue(hasattr(test_handler, "_hook_metadata"))
        metadata = test_handler._hook_metadata
        self.assertEqual(metadata["hook_name"], "entry.validate")
        self.assertEqual(metadata["entity"], "test_entity")

    def test_get_attrs_hook_decorator(self):
        """Test get_attrs_hook decorator adds metadata"""

        @get_attrs_hook("entry")
        def test_handler(self):
            return "test"

        self.assertTrue(hasattr(test_handler, "_hook_metadata"))
        metadata = test_handler._hook_metadata
        self.assertEqual(metadata["hook_name"], "entry.get_attrs")

    def test_decorated_method_still_callable(self):
        """Test that decorated methods can still be called"""

        @entry_hook("after_create")
        def test_handler(arg1, arg2):
            return f"{arg1}_{arg2}"

        result = test_handler("hello", "world")
        self.assertEqual(result, "hello_world")

    def test_plugin_auto_detection(self):
        """Test that Plugin.__init_subclass__ auto-detects decorated methods"""

        class TestPlugin(Plugin):
            id = "test-plugin"
            name = "Test Plugin"

            @entry_hook("after_create", entity="an")
            def hook1(self):
                return "hook1"

            @entry_hook("before_update", entity="bn", priority=50)
            def hook2(self):
                return "hook2"

            @entity_hook("after_create")
            def hook3(self):
                return "hook3"

        # Check that _hook_handlers was created
        self.assertTrue(hasattr(TestPlugin, "_hook_handlers"))
        handlers = TestPlugin._hook_handlers

        # Should have 3 handlers
        self.assertEqual(len(handlers), 3)

        # Check first handler
        handler1 = next(h for h in handlers if h["method_name"] == "hook1")
        self.assertEqual(handler1["hook_name"], "entry.after_create")
        self.assertEqual(handler1["entity"], "an")
        self.assertEqual(handler1["priority"], 100)

        # Check second handler
        handler2 = next(h for h in handlers if h["method_name"] == "hook2")
        self.assertEqual(handler2["hook_name"], "entry.before_update")
        self.assertEqual(handler2["entity"], "bn")
        self.assertEqual(handler2["priority"], 50)

        # Check third handler
        handler3 = next(h for h in handlers if h["method_name"] == "hook3")
        self.assertEqual(handler3["hook_name"], "entity.after_create")
        self.assertIsNone(handler3["entity"])

    def test_plugin_get_info_includes_hooks(self):
        """Test that Plugin.get_info() includes hooks from decorators"""

        class TestPlugin(Plugin):
            id = "test-plugin"
            name = "Test Plugin"

            @entry_hook("after_create")
            def hook1(self):
                pass

            @entity_hook("after_update")
            def hook2(self):
                pass

        plugin = TestPlugin()
        info = plugin.get_info()

        self.assertIn("hooks", info)
        self.assertEqual(len(info["hooks"]), 2)
        self.assertIn("entry.after_create", info["hooks"])
        self.assertIn("entity.after_update", info["hooks"])


if __name__ == "__main__":
    unittest.main()
