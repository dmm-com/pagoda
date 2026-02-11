"""
Tests for the Plugin base class.

Tests the core functionality of the Plugin class including validation,
metadata management, and string representations.
"""

import sys
import unittest
from pathlib import Path

# Add the SDK directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk"))

from pagoda_plugin_sdk.decorators import entry_hook
from pagoda_plugin_sdk.exceptions import PluginValidationError
from pagoda_plugin_sdk.plugin import Plugin


class ValidTestPlugin(Plugin):
    """Valid test plugin for testing purposes"""

    id = "test-plugin"
    name = "Test Plugin"
    version = "1.0.0"
    description = "A test plugin"
    author = "Test Author"
    dependencies = ["dep1", "dep2"]
    django_apps = ["test_app"]
    url_patterns = "test_urls"
    api_v2_patterns = "test_api_urls"

    @entry_hook("after_create")
    def test_handler(self):
        """Test hook handler"""
        pass


class TestPlugin(unittest.TestCase):
    """Test cases for Plugin base class"""

    def test_valid_plugin_initialization(self):
        """Test successful initialization of a valid plugin"""
        plugin = ValidTestPlugin()

        self.assertEqual(plugin.id, "test-plugin")
        self.assertEqual(plugin.name, "Test Plugin")
        self.assertEqual(plugin.version, "1.0.0")
        self.assertEqual(plugin.description, "A test plugin")
        self.assertEqual(plugin.author, "Test Author")
        self.assertEqual(plugin.dependencies, ["dep1", "dep2"])
        self.assertEqual(plugin.django_apps, ["test_app"])
        self.assertEqual(plugin.url_patterns, "test_urls")
        self.assertEqual(plugin.api_v2_patterns, "test_api_urls")
        # Hooks are now auto-detected via decorators, check via get_info()
        self.assertIn("entry.after_create", plugin.get_info()["hooks"])

    def test_missing_plugin_id_raises_error(self):
        """Test that missing plugin ID raises PluginValidationError"""

        class InvalidPlugin(Plugin):
            # Missing id
            name = "Test Plugin"
            version = "1.0.0"

        with self.assertRaises(PluginValidationError) as context:
            InvalidPlugin()

        self.assertEqual(str(context.exception), "Plugin ID is required")

    def test_missing_plugin_name_raises_error(self):
        """Test that missing plugin name raises PluginValidationError"""

        class InvalidPlugin(Plugin):
            id = "test-plugin"
            # Missing name
            version = "1.0.0"

        with self.assertRaises(PluginValidationError) as context:
            InvalidPlugin()

        self.assertEqual(str(context.exception), "Plugin name is required")

    def test_missing_plugin_version_raises_error(self):
        """Test that missing plugin version raises PluginValidationError"""

        class InvalidPlugin(Plugin):
            id = "test-plugin"
            name = "Test Plugin"
            version = ""  # Empty version

        with self.assertRaises(PluginValidationError) as context:
            InvalidPlugin()

        self.assertEqual(str(context.exception), "Plugin version is required")

    def test_invalid_plugin_id_format_raises_error(self):
        """Test that invalid plugin ID format raises PluginValidationError"""

        class InvalidPlugin(Plugin):
            id = "test plugin with spaces"  # Invalid characters
            name = "Test Plugin"
            version = "1.0.0"

        with self.assertRaises(PluginValidationError) as context:
            InvalidPlugin()

        self.assertIn("alphanumeric characters, hyphens, and underscores", str(context.exception))

    def test_valid_plugin_id_formats(self):
        """Test that valid plugin ID formats are accepted"""
        valid_ids = [
            "test-plugin",
            "test_plugin",
            "testplugin",
            "test-plugin-123",
            "test_plugin_123",
        ]

        for valid_id in valid_ids:

            class ValidPlugin(Plugin):
                id = valid_id
                name = "Test Plugin"
                version = "1.0.0"

            # Should not raise an exception
            plugin = ValidPlugin()
            self.assertEqual(plugin.id, valid_id)

    def test_invalid_django_apps_raises_error(self):
        """Test that invalid django_apps raises PluginValidationError"""

        class InvalidPlugin(Plugin):
            id = "test-plugin"
            name = "Test Plugin"
            version = "1.0.0"
            django_apps = ["valid_app", ""]  # Empty string is invalid

        with self.assertRaises(PluginValidationError) as context:
            InvalidPlugin()

        self.assertEqual(str(context.exception), "Django app names must be non-empty strings")

        class InvalidPlugin2(Plugin):
            id = "test-plugin"
            name = "Test Plugin"
            version = "1.0.0"
            django_apps = ["valid_app", None]  # None is invalid

        with self.assertRaises(PluginValidationError) as context:
            InvalidPlugin2()

        self.assertEqual(str(context.exception), "Django app names must be non-empty strings")

    def test_get_info_returns_correct_metadata(self):
        """Test that get_info() returns correct plugin metadata"""
        plugin = ValidTestPlugin()
        info = plugin.get_info()

        expected_info = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "dependencies": ["dep1", "dep2"],
            "django_apps": ["test_app"],
            "url_patterns": "test_urls",
            "api_v2_patterns": "test_api_urls",
            "hooks": ["entry.after_create"],
            "override_operations": [],
            "has_params_model": False,
        }

        self.assertEqual(info, expected_info)

    def test_get_info_with_empty_hooks(self):
        """Test get_info() with empty hooks"""

        class PluginWithoutHooks(Plugin):
            id = "test-plugin"
            name = "Test Plugin"
            version = "1.0.0"

        plugin = PluginWithoutHooks()
        info = plugin.get_info()

        self.assertEqual(info["hooks"], [])

    def test_string_representation(self):
        """Test __str__ method returns correct format"""
        plugin = ValidTestPlugin()
        expected_str = "Test Plugin v1.0.0 (test-plugin)"

        self.assertEqual(str(plugin), expected_str)

    def test_repr_representation(self):
        """Test __repr__ method returns correct format"""
        plugin = ValidTestPlugin()
        expected_repr = "<Plugin: test-plugin>"

        self.assertEqual(repr(plugin), expected_repr)

    def test_default_values(self):
        """Test that default values are properly set"""

        class MinimalPlugin(Plugin):
            id = "minimal-plugin"
            name = "Minimal Plugin"
            version = "1.0.0"

        plugin = MinimalPlugin()

        # Test default values
        self.assertEqual(plugin.description, "")
        self.assertEqual(plugin.author, "")
        self.assertEqual(plugin.dependencies, [])
        self.assertEqual(plugin.django_apps, [])
        self.assertIsNone(plugin.url_patterns)
        self.assertIsNone(plugin.api_v2_patterns)
        # Hooks are auto-detected, so minimal plugin has no hooks
        self.assertEqual(plugin.get_info()["hooks"], [])

    def test_validate_method_can_be_called_separately(self):
        """Test that validate() method can be called separately"""
        plugin = ValidTestPlugin()

        # Should not raise any exception
        plugin.validate()

        # Change id to invalid format
        plugin.id = "invalid id with spaces"

        with self.assertRaises(PluginValidationError):
            plugin.validate()


if __name__ == "__main__":
    unittest.main()
