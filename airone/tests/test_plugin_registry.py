"""
Tests for Plugin Registry

Tests plugin registration, retrieval, and management functionality.
"""

import unittest
from unittest.mock import patch

from pagoda_plugin_sdk import Plugin
from pagoda_plugin_sdk.decorators import entry_hook
from pagoda_plugin_sdk.exceptions import PluginError

from airone.plugins.registry import PluginRegistry


class TestPluginRegistry(unittest.TestCase):
    """Test cases for PluginRegistry"""

    def setUp(self):
        """Set up test fixtures"""
        self.registry = PluginRegistry()

    def test_register_plugin(self):
        """Test basic plugin registration"""

        class TestPlugin(Plugin):
            id = "test-plugin"
            name = "Test Plugin"
            version = "1.0.0"

        plugin = self.registry.register(TestPlugin)

        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.id, "test-plugin")
        self.assertEqual(len(self.registry.get_all_plugins()), 1)

    def test_register_duplicate_plugin(self):
        """Test registering duplicate plugin raises error"""

        class TestPlugin(Plugin):
            id = "test-plugin"
            name = "Test Plugin"

        self.registry.register(TestPlugin)

        # Try to register again with same ID
        with self.assertRaises(PluginError) as ctx:
            self.registry.register(TestPlugin)

        self.assertIn("already registered", str(ctx.exception))

    @patch("airone.plugins.registry.hook_manager")
    def test_register_plugin_with_hooks(self, mock_hook_manager):
        """Test registering plugin with decorator-based hooks"""

        class TestPluginWithHooks(Plugin):
            id = "test-plugin-hooks"
            name = "Test Plugin with Hooks"

            @entry_hook("after_create", entity="test")
            def test_hook(self, entity_name, user, entry, **kwargs):
                return "test"

        self.registry.register(TestPluginWithHooks)

        # Verify hook was registered
        self.assertTrue(mock_hook_manager.register_hook.called)
        call_args = mock_hook_manager.register_hook.call_args
        self.assertEqual(call_args[0][0], "entry.after_create")
        self.assertEqual(call_args[1]["entity"], "test")

    def test_get_plugin_by_id(self):
        """Test retrieving plugin by ID"""

        class TestPlugin(Plugin):
            id = "test-plugin"
            name = "Test Plugin"

        self.registry.register(TestPlugin)

        plugin = self.registry.get("test-plugin")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.id, "test-plugin")

    def test_get_plugin_not_found(self):
        """Test retrieving non-existent plugin returns None"""
        plugin = self.registry.get("non-existent")
        self.assertIsNone(plugin)

    def test_get_all_plugins(self):
        """Test getting all registered plugins"""

        class Plugin1(Plugin):
            id = "plugin1"
            name = "Plugin 1"

        class Plugin2(Plugin):
            id = "plugin2"
            name = "Plugin 2"

        self.registry.register(Plugin1)
        self.registry.register(Plugin2)

        plugins = self.registry.get_all_plugins()
        self.assertEqual(len(plugins), 2)
        plugin_ids = [p.id for p in plugins]
        self.assertIn("plugin1", plugin_ids)
        self.assertIn("plugin2", plugin_ids)

    def test_get_enabled_plugins(self):
        """Test getting enabled plugins (currently all plugins are enabled)"""

        class TestPlugin(Plugin):
            id = "test-plugin"
            name = "Test Plugin"

        self.registry.register(TestPlugin)

        enabled = self.registry.get_enabled_plugins()
        self.assertEqual(len(enabled), 1)
        self.assertEqual(enabled[0].id, "test-plugin")

    def test_get_installed_apps(self):
        """Test getting Django apps from plugins"""

        class Plugin1(Plugin):
            id = "plugin1"
            name = "Plugin 1"
            django_apps = ["app1", "app2"]

        class Plugin2(Plugin):
            id = "plugin2"
            name = "Plugin 2"
            django_apps = ["app3"]

        self.registry.register(Plugin1)
        self.registry.register(Plugin2)

        apps = self.registry.get_installed_apps()
        self.assertEqual(len(apps), 3)
        self.assertIn("app1", apps)
        self.assertIn("app2", apps)
        self.assertIn("app3", apps)

    def test_get_installed_apps_empty(self):
        """Test getting installed apps when no plugins registered"""
        apps = self.registry.get_installed_apps()
        self.assertEqual(apps, [])

    @patch("airone.plugins.registry.include")
    @patch("airone.plugins.registry.path")
    def test_register_api_v2_patterns(self, mock_path, mock_include):
        """Test registering plugin with API v2 patterns"""

        class TestPlugin(Plugin):
            id = "test-plugin"
            name = "Test Plugin"
            api_v2_patterns = "test_plugin.urls"

        self.registry.register(TestPlugin)

        patterns = self.registry.get_api_v2_patterns()
        self.assertEqual(len(patterns), 1)
        mock_include.assert_called_once_with("test_plugin.urls")

    @patch("airone.plugins.registry.include")
    @patch("airone.plugins.registry.path")
    def test_get_url_patterns(self, mock_path, mock_include):
        """Test getting URL patterns from plugins"""

        class TestPlugin(Plugin):
            id = "test-plugin"
            name = "Test Plugin"
            url_patterns = "test_plugin.urls"

        self.registry.register(TestPlugin)

        patterns = self.registry.get_url_patterns()
        self.assertEqual(len(patterns), 1)
        mock_include.assert_called_once_with("test_plugin.urls")

    def test_get_url_patterns_empty(self):
        """Test getting URL patterns when plugin has none"""

        class TestPlugin(Plugin):
            id = "test-plugin"
            name = "Test Plugin"
            url_patterns = None

        self.registry.register(TestPlugin)

        patterns = self.registry.get_url_patterns()
        self.assertEqual(len(patterns), 0)

    def test_register_plugin_with_invalid_id(self):
        """Test registering plugin with invalid ID raises error"""

        class BadPlugin(Plugin):
            id = ""  # Empty ID
            name = "Bad Plugin"

        with self.assertRaises(Exception):
            self.registry.register(BadPlugin)

    @patch("airone.plugins.registry.hook_manager")
    def test_register_plugin_with_multiple_hooks(self, mock_hook_manager):
        """Test registering plugin with multiple hooks"""

        class MultiHookPlugin(Plugin):
            id = "multi-hook"
            name = "Multi Hook Plugin"

            @entry_hook("after_create")
            def hook1(self):
                pass

            @entry_hook("before_update")
            def hook2(self):
                pass

            @entry_hook("after_update")
            def hook3(self):
                pass

        self.registry.register(MultiHookPlugin)

        # Verify all hooks were registered
        self.assertEqual(mock_hook_manager.register_hook.call_count, 3)


if __name__ == "__main__":
    unittest.main()
