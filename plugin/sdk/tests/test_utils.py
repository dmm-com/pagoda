"""
Tests for utility functions.

Tests the utility functions and classes defined in the pagoda_plugin_sdk.utils module
including validation, formatting, sanitization, and logging utilities.
"""

import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Add the SDK directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk"))

from pagoda_plugin_sdk.utils import (
    PluginLogger,
    format_datetime_for_api,
    generate_plugin_cache_key,
    get_pagoda_version,
    get_plugin_module_path,
    log_plugin_activity,
    merge_plugin_config,
    sanitize_plugin_id,
    validate_django_app_name,
    validate_plugin_data,
)


class TestVersionUtils(unittest.TestCase):
    """Test cases for version-related utilities"""

    def test_get_pagoda_version_returns_string(self):
        """Test that get_pagoda_version returns a version string"""
        version = get_pagoda_version()
        self.assertIsInstance(version, str)
        self.assertGreater(len(version), 0)


class TestValidationUtils(unittest.TestCase):
    """Test cases for validation utilities"""

    def test_validate_plugin_data_success(self):
        """Test successful plugin data validation"""
        data = {"name": "Test Plugin", "version": "1.0.0", "id": "test-plugin"}
        required_fields = ["name", "version", "id"]

        result = validate_plugin_data(data, required_fields)

        expected_result = {
            "valid": True,
            "data": data,
            "validated_fields": required_fields,
        }
        self.assertEqual(result, expected_result)

    def test_validate_plugin_data_missing_fields(self):
        """Test validation failure with missing fields"""
        data = {"name": "Test Plugin"}  # Missing version and id
        required_fields = ["name", "version", "id"]

        with self.assertRaises(ValueError) as context:
            validate_plugin_data(data, required_fields)

        error_message = str(context.exception)
        self.assertIn("Missing required fields", error_message)
        self.assertIn("version", error_message)
        self.assertIn("id", error_message)

    def test_validate_plugin_data_none_values(self):
        """Test validation failure with None values"""
        data = {"name": "Test Plugin", "version": None, "id": "test-plugin"}
        required_fields = ["name", "version", "id"]

        with self.assertRaises(ValueError) as context:
            validate_plugin_data(data, required_fields)

        self.assertIn("version", str(context.exception))

    def test_validate_plugin_data_empty_required_fields(self):
        """Test validation with no required fields"""
        data = {"extra": "data"}
        required_fields = []

        result = validate_plugin_data(data, required_fields)

        self.assertTrue(result["valid"])
        self.assertEqual(result["data"], data)
        self.assertEqual(result["validated_fields"], [])

    def test_validate_django_app_name_valid_names(self):
        """Test Django app name validation with valid names"""
        valid_names = [
            "myapp",
            "my_app",
            "myapp2",
            "django_app",
            "myapp.submodule",
            "myapp.submodule.nested",
        ]

        for name in valid_names:
            with self.subTest(name=name):
                self.assertTrue(validate_django_app_name(name))

    def test_validate_django_app_name_invalid_names(self):
        """Test Django app name validation with invalid names"""
        invalid_names = [
            "",
            None,
            "my-app",  # Hyphens not allowed
            "2myapp",  # Cannot start with number
            "my app",  # Spaces not allowed
            "my.app.",  # Cannot end with dot
            ".myapp",  # Cannot start with dot
            "my..app",  # Double dots not allowed
        ]

        for name in invalid_names:
            with self.subTest(name=name):
                self.assertFalse(validate_django_app_name(name))


class TestFormattingUtils(unittest.TestCase):
    """Test cases for formatting utilities"""

    def test_format_datetime_for_api_with_datetime(self):
        """Test datetime formatting with datetime object"""
        dt = datetime(2023, 12, 25, 15, 30, 45, 123456)
        result = format_datetime_for_api(dt)

        self.assertIsInstance(result, str)
        self.assertIn("2023-12-25", result)
        self.assertIn("15:30:45", result)

    def test_format_datetime_for_api_with_none(self):
        """Test datetime formatting with None"""
        result = format_datetime_for_api(None)
        self.assertIsNone(result)

    def test_format_datetime_for_api_with_string(self):
        """Test datetime formatting with string input"""
        dt_string = "2023-12-25 15:30:45"
        result = format_datetime_for_api(dt_string)

        self.assertEqual(result, dt_string)

    def test_format_datetime_for_api_with_non_datetime_object(self):
        """Test datetime formatting with non-datetime object"""
        non_dt = 12345
        result = format_datetime_for_api(non_dt)

        self.assertEqual(result, "12345")


class TestSanitizationUtils(unittest.TestCase):
    """Test cases for sanitization utilities"""

    def test_sanitize_plugin_id_valid_id(self):
        """Test sanitization with already valid plugin ID"""
        valid_ids = ["test-plugin", "test_plugin", "testplugin", "test123"]

        for plugin_id in valid_ids:
            with self.subTest(plugin_id=plugin_id):
                result = sanitize_plugin_id(plugin_id)
                self.assertEqual(result, plugin_id)

    def test_sanitize_plugin_id_invalid_characters(self):
        """Test sanitization removes invalid characters"""
        test_cases = [
            ("test plugin", "testplugin"),
            ("test@plugin", "testplugin"),
            ("test!@#$%plugin", "testplugin"),
            ("test-plugin!", "test-plugin"),
            ("test_plugin$", "test_plugin"),
        ]

        for input_id, expected in test_cases:
            with self.subTest(input_id=input_id):
                result = sanitize_plugin_id(input_id)
                self.assertEqual(result, expected)

    def test_sanitize_plugin_id_strips_leading_trailing(self):
        """Test sanitization strips leading/trailing hyphens and underscores"""
        test_cases = [
            ("-test-plugin-", "test-plugin"),
            ("_test_plugin_", "test_plugin"),
            ("--test--", "test"),
            ("__test__", "test"),
            ("-_test_-", "test"),
        ]

        for input_id, expected in test_cases:
            with self.subTest(input_id=input_id):
                result = sanitize_plugin_id(input_id)
                self.assertEqual(result, expected)

    def test_sanitize_plugin_id_empty_input(self):
        """Test sanitization with empty input"""
        self.assertEqual(sanitize_plugin_id(""), "")
        self.assertEqual(sanitize_plugin_id("---"), "")
        self.assertEqual(sanitize_plugin_id("___"), "")


class TestCacheUtils(unittest.TestCase):
    """Test cases for cache-related utilities"""

    def test_generate_plugin_cache_key(self):
        """Test cache key generation"""
        plugin_id = "test-plugin"
        key = "user_data"

        result = generate_plugin_cache_key(plugin_id, key)

        self.assertEqual(result, "pagoda:plugin:test-plugin:user_data")

    def test_generate_plugin_cache_key_with_invalid_id(self):
        """Test cache key generation with invalid plugin ID"""
        plugin_id = "test@plugin!"
        key = "user_data"

        result = generate_plugin_cache_key(plugin_id, key)

        self.assertEqual(result, "pagoda:plugin:testplugin:user_data")


class TestConfigUtils(unittest.TestCase):
    """Test cases for configuration utilities"""

    def test_merge_plugin_config(self):
        """Test configuration merging"""
        default_config = {"timeout": 30, "retries": 3, "debug": False}
        plugin_config = {"timeout": 60, "debug": True}

        result = merge_plugin_config(default_config, plugin_config)

        expected = {"timeout": 60, "retries": 3, "debug": True}
        self.assertEqual(result, expected)

    def test_merge_plugin_config_empty_plugin_config(self):
        """Test configuration merging with empty plugin config"""
        default_config = {"timeout": 30, "retries": 3}
        plugin_config = {}

        result = merge_plugin_config(default_config, plugin_config)

        self.assertEqual(result, default_config)

    def test_merge_plugin_config_empty_default_config(self):
        """Test configuration merging with empty default config"""
        default_config = {}
        plugin_config = {"timeout": 60, "debug": True}

        result = merge_plugin_config(default_config, plugin_config)

        self.assertEqual(result, plugin_config)

    def test_merge_plugin_config_does_not_modify_originals(self):
        """Test that merging doesn't modify original dictionaries"""
        default_config = {"timeout": 30}
        plugin_config = {"debug": True}

        merge_plugin_config(default_config, plugin_config)

        self.assertEqual(default_config, {"timeout": 30})
        self.assertEqual(plugin_config, {"debug": True})


class TestModuleUtils(unittest.TestCase):
    """Test cases for module-related utilities"""

    def test_get_plugin_module_path(self):
        """Test plugin module path generation"""
        test_cases = [
            ("test-plugin", "views", "test_plugin.views"),
            ("my_plugin", "models", "my_plugin.models"),
            ("hello-world", "api.views", "hello_world.api.views"),
        ]

        for plugin_id, module_name, expected in test_cases:
            with self.subTest(plugin_id=plugin_id, module_name=module_name):
                result = get_plugin_module_path(plugin_id, module_name)
                self.assertEqual(result, expected)


class TestLoggingUtils(unittest.TestCase):
    """Test cases for logging utilities"""

    @patch("pagoda_plugin_sdk.utils.logger")
    def test_log_plugin_activity_basic(self, mock_logger):
        """Test basic plugin activity logging"""
        log_plugin_activity("test-plugin", "startup")

        mock_logger.info.assert_called_once_with("Plugin 'test-plugin' performed action: startup")

    @patch("pagoda_plugin_sdk.utils.logger")
    def test_log_plugin_activity_with_details(self, mock_logger):
        """Test plugin activity logging with details"""
        details = {"version": "1.0.0", "config": {"debug": True}}
        log_plugin_activity("test-plugin", "startup", details)

        expected_message = (
            "Plugin 'test-plugin' performed action: startup | Details: "
            "{'version': '1.0.0', 'config': {'debug': True}}"
        )
        mock_logger.info.assert_called_once_with(expected_message)


class TestPluginLogger(unittest.TestCase):
    """Test cases for PluginLogger class"""

    def setUp(self):
        """Set up test fixtures"""
        self.plugin_logger = PluginLogger("test-plugin")

    def test_plugin_logger_initialization(self):
        """Test PluginLogger initialization"""
        self.assertEqual(self.plugin_logger.plugin_id, "test-plugin")
        self.assertEqual(self.plugin_logger.logger.name, "pagoda.plugin.test-plugin")

    @patch("logging.getLogger")
    def test_plugin_logger_info(self, mock_get_logger):
        """Test PluginLogger info method"""
        mock_logger = mock_get_logger.return_value
        plugin_logger = PluginLogger("test-plugin")

        plugin_logger.info("Test message")

        mock_logger.info.assert_called_once_with("[test-plugin] Test message")

    @patch("logging.getLogger")
    def test_plugin_logger_warning(self, mock_get_logger):
        """Test PluginLogger warning method"""
        mock_logger = mock_get_logger.return_value
        plugin_logger = PluginLogger("test-plugin")

        plugin_logger.warning("Warning message")

        mock_logger.warning.assert_called_once_with("[test-plugin] Warning message")

    @patch("logging.getLogger")
    def test_plugin_logger_error(self, mock_get_logger):
        """Test PluginLogger error method"""
        mock_logger = mock_get_logger.return_value
        plugin_logger = PluginLogger("test-plugin")

        plugin_logger.error("Error message")

        mock_logger.error.assert_called_once_with("[test-plugin] Error message")

    @patch("logging.getLogger")
    def test_plugin_logger_debug(self, mock_get_logger):
        """Test PluginLogger debug method"""
        mock_logger = mock_get_logger.return_value
        plugin_logger = PluginLogger("test-plugin")

        plugin_logger.debug("Debug message")

        mock_logger.debug.assert_called_once_with("[test-plugin] Debug message")

    @patch("logging.getLogger")
    def test_plugin_logger_with_kwargs(self, mock_get_logger):
        """Test PluginLogger methods with keyword arguments"""
        mock_logger = mock_get_logger.return_value
        plugin_logger = PluginLogger("test-plugin")

        plugin_logger.info("Test message", extra={"user": "test"})

        mock_logger.info.assert_called_once_with(
            "[test-plugin] Test message", extra={"user": "test"}
        )


if __name__ == "__main__":
    unittest.main()
