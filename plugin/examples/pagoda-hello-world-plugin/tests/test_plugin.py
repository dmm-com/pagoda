"""
Tests for HelloWorldPlugin class

Tests the basic functionality of the HelloWorldPlugin including:
- Plugin initialization and metadata
- Hook registration and discovery
- Plugin information retrieval
"""

import unittest
from unittest.mock import patch

from pagoda_hello_world_plugin.plugin import HelloWorldPlugin


class TestHelloWorldPlugin(unittest.TestCase):
    """Test cases for HelloWorldPlugin class"""

    def setUp(self):
        """Set up test fixtures"""
        self.plugin = HelloWorldPlugin()

    def test_plugin_metadata(self):
        """Test plugin metadata is correctly defined"""
        self.assertEqual(self.plugin.id, "hello-world-plugin")
        self.assertEqual(self.plugin.name, "Hello World Plugin")
        self.assertEqual(self.plugin.version, "1.0.0")
        self.assertEqual(
            self.plugin.description,
            "A sample plugin demonstrating Pagoda plugin system capabilities",
        )
        self.assertEqual(self.plugin.author, "Pagoda Development Team")

    def test_plugin_django_apps(self):
        """Test Django apps configuration"""
        self.assertEqual(self.plugin.django_apps, ["pagoda_hello_world_plugin"])

    def test_plugin_api_v2_patterns(self):
        """Test API v2 patterns configuration"""
        self.assertEqual(self.plugin.api_v2_patterns, "pagoda_hello_world_plugin.api_v2.urls")

    def test_plugin_hooks_registered(self):
        """Test that hooks are properly registered"""
        info = self.plugin.get_info()
        hooks = info["hooks"]

        # Check entry hooks
        self.assertIn("entry.after_create", hooks)
        self.assertIn("entry.before_update", hooks)
        self.assertIn("entry.after_update", hooks)
        self.assertIn("entry.before_delete", hooks)

        # Check entity hooks
        self.assertIn("entity.after_create", hooks)
        self.assertIn("entity.before_update", hooks)
        self.assertIn("entity.after_update", hooks)

        # Check validation hook
        self.assertIn("entry.validate", hooks)

        # Check get_attrs hooks
        self.assertIn("entry.get_attrs", hooks)
        self.assertIn("entity.get_attrs", hooks)

    def test_plugin_initialization_logging(self):
        """Test that plugin initialization logs correctly"""
        with patch("pagoda_hello_world_plugin.plugin.logger") as mock_logger:
            _ = HelloWorldPlugin()
            mock_logger.info.assert_called_once_with("Initialized Hello World Plugin v1.0.0")

    def test_plugin_get_info(self):
        """Test get_info() returns complete plugin information"""
        info = self.plugin.get_info()

        # Check basic metadata
        self.assertEqual(info["id"], "hello-world-plugin")
        self.assertEqual(info["name"], "Hello World Plugin")
        self.assertEqual(info["version"], "1.0.0")
        self.assertEqual(
            info["description"], "A sample plugin demonstrating Pagoda plugin system capabilities"
        )
        self.assertEqual(info["author"], "Pagoda Development Team")

        # Check configuration
        self.assertEqual(info["django_apps"], ["pagoda_hello_world_plugin"])
        self.assertEqual(info["api_v2_patterns"], "pagoda_hello_world_plugin.api_v2.urls")

        # Check hooks are present
        self.assertIsInstance(info["hooks"], list)
        self.assertGreater(len(info["hooks"]), 0)

    def test_plugin_string_representation(self):
        """Test __str__ method"""
        expected = "Hello World Plugin v1.0.0 (hello-world-plugin)"
        self.assertEqual(str(self.plugin), expected)

    def test_plugin_repr_representation(self):
        """Test __repr__ method"""
        expected = "<Plugin: hello-world-plugin>"
        self.assertEqual(repr(self.plugin), expected)

    def test_log_helloworld_create_method_exists(self):
        """Test that entry hook methods exist"""
        self.assertTrue(hasattr(self.plugin, "log_helloworld_create"))
        self.assertTrue(callable(self.plugin.log_helloworld_create))

    def test_log_helloworld_before_update_method_exists(self):
        """Test that before update hook method exists"""
        self.assertTrue(hasattr(self.plugin, "log_helloworld_before_update"))
        self.assertTrue(callable(self.plugin.log_helloworld_before_update))

    def test_log_helloworld_after_update_method_exists(self):
        """Test that after update hook method exists"""
        self.assertTrue(hasattr(self.plugin, "log_helloworld_after_update"))
        self.assertTrue(callable(self.plugin.log_helloworld_after_update))

    def test_log_entry_delete_method_exists(self):
        """Test that delete hook method exists"""
        self.assertTrue(hasattr(self.plugin, "log_entry_delete"))
        self.assertTrue(callable(self.plugin.log_entry_delete))

    def test_validate_entry_method_exists(self):
        """Test that validation hook method exists"""
        self.assertTrue(hasattr(self.plugin, "validate_entry"))
        self.assertTrue(callable(self.plugin.validate_entry))

    def test_get_entry_attrs_method_exists(self):
        """Test that entry attrs hook method exists"""
        self.assertTrue(hasattr(self.plugin, "get_entry_attrs"))
        self.assertTrue(callable(self.plugin.get_entry_attrs))

    def test_log_entity_create_method_exists(self):
        """Test that entity create hook method exists"""
        self.assertTrue(hasattr(self.plugin, "log_entity_create"))
        self.assertTrue(callable(self.plugin.log_entity_create))

    def test_log_entity_before_update_method_exists(self):
        """Test that entity before update hook method exists"""
        self.assertTrue(hasattr(self.plugin, "log_entity_before_update"))
        self.assertTrue(callable(self.plugin.log_entity_before_update))

    def test_log_entity_after_update_method_exists(self):
        """Test that entity after update hook method exists"""
        self.assertTrue(hasattr(self.plugin, "log_entity_after_update"))
        self.assertTrue(callable(self.plugin.log_entity_after_update))

    def test_get_entity_attrs_method_exists(self):
        """Test that entity attrs hook method exists"""
        self.assertTrue(hasattr(self.plugin, "get_entity_attrs"))
        self.assertTrue(callable(self.plugin.get_entity_attrs))


if __name__ == "__main__":
    unittest.main()
