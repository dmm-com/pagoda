"""
Tests for custom_view plugin hooks integration
"""

import unittest
from unittest.mock import patch

from airone.lib import custom_view


class TestCustomViewPluginHooks(unittest.TestCase):
    """Test plugin hooks integration with custom_view"""

    def setUp(self):
        from airone.plugins.hook_manager import hook_manager

        hook_manager._hooks = {}
        hook_manager._stats = {"total_registered": 0, "total_executed": 0, "total_failed": 0}
        custom_view.CUSTOM_VIEW = {}

    def tearDown(self):
        custom_view.CUSTOM_VIEW = {}

    @patch("airone.lib.custom_view.Path.is_file")
    def test_is_custom_with_plugin_hook(self, mock_is_file):
        """Test is_custom returns True when plugin hook exists"""
        mock_is_file.return_value = False

        from airone.plugins.hook_manager import hook_manager

        hook_manager.register_hook("test_handler", lambda: "plugin", "test-plugin")

        result = custom_view.is_custom("test_handler", "TestEntity")
        self.assertTrue(result)

    @patch("airone.lib.custom_view._isin_cache")
    def test_call_custom_with_plugin_hook(self, mock_in_cache):
        """Test call_custom executes plugin hook"""
        mock_in_cache.return_value = False

        from airone.plugins.hook_manager import hook_manager

        hook_manager.register_hook(
            "test_handler", lambda *args, **kwargs: "from_plugin", "test-plugin"
        )

        result = custom_view.call_custom("test_handler", "TestEntity")
        self.assertEqual(result, "from_plugin")
