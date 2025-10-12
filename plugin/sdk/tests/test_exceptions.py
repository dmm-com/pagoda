"""
Tests for exception classes.

Tests the exception hierarchy and behavior of custom exceptions
defined in the pagoda_plugin_sdk.exceptions module.
"""

import sys
import unittest
from pathlib import Path

# Add the SDK directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk"))

from pagoda_plugin_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DataAccessError,
    HookExecutionError,
    InterfaceError,
    PagodaError,
    PluginError,
    PluginLoadError,
    PluginSecurityError,
    PluginValidationError,
)


class TestExceptionHierarchy(unittest.TestCase):
    """Test cases for exception class hierarchy"""

    def test_pagoda_error_is_base_exception(self):
        """Test PagodaError is the base exception"""
        error = PagodaError("Test error")
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Test error")

    def test_plugin_error_inherits_from_pagoda_error(self):
        """Test PluginError inherits from PagodaError"""
        error = PluginError("Plugin error")
        self.assertIsInstance(error, PagodaError)
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Plugin error")

    def test_plugin_load_error_inherits_from_plugin_error(self):
        """Test PluginLoadError inherits from PluginError"""
        error = PluginLoadError("Load error")
        self.assertIsInstance(error, PluginError)
        self.assertIsInstance(error, PagodaError)
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Load error")

    def test_plugin_validation_error_inherits_from_plugin_error(self):
        """Test PluginValidationError inherits from PluginError"""
        error = PluginValidationError("Validation error")
        self.assertIsInstance(error, PluginError)
        self.assertIsInstance(error, PagodaError)
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Validation error")

    def test_plugin_security_error_inherits_from_plugin_error(self):
        """Test PluginSecurityError inherits from PluginError"""
        error = PluginSecurityError("Security error")
        self.assertIsInstance(error, PluginError)
        self.assertIsInstance(error, PagodaError)
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Security error")

    def test_interface_error_inherits_from_pagoda_error(self):
        """Test InterfaceError inherits from PagodaError"""
        error = InterfaceError("Interface error")
        self.assertIsInstance(error, PagodaError)
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Interface error")

    def test_authentication_error_inherits_from_pagoda_error(self):
        """Test AuthenticationError inherits from PagodaError"""
        error = AuthenticationError("Authentication error")
        self.assertIsInstance(error, PagodaError)
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Authentication error")

    def test_authorization_error_inherits_from_pagoda_error(self):
        """Test AuthorizationError inherits from PagodaError"""
        error = AuthorizationError("Authorization error")
        self.assertIsInstance(error, PagodaError)
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Authorization error")

    def test_data_access_error_inherits_from_pagoda_error(self):
        """Test DataAccessError inherits from PagodaError"""
        error = DataAccessError("Data access error")
        self.assertIsInstance(error, PagodaError)
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Data access error")

    def test_hook_execution_error_inherits_from_pagoda_error(self):
        """Test HookExecutionError inherits from PagodaError"""
        error = HookExecutionError("Hook execution error")
        self.assertIsInstance(error, PagodaError)
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Hook execution error")


class TestExceptionCatching(unittest.TestCase):
    """Test cases for exception catching behavior"""

    def test_catch_plugin_errors_with_plugin_error(self):
        """Test that plugin-specific errors can be caught with PluginError"""
        with self.assertRaises(PluginError):
            raise PluginLoadError("Load failed")

        with self.assertRaises(PluginError):
            raise PluginValidationError("Validation failed")

        with self.assertRaises(PluginError):
            raise PluginSecurityError("Security violation")

    def test_catch_all_errors_with_pagoda_error(self):
        """Test that all Pagoda errors can be caught with PagodaError"""
        errors_to_test = [
            PluginError("Plugin error"),
            PluginLoadError("Load error"),
            PluginValidationError("Validation error"),
            PluginSecurityError("Security error"),
            InterfaceError("Interface error"),
            AuthenticationError("Auth error"),
            AuthorizationError("Authz error"),
            DataAccessError("Data error"),
            HookExecutionError("Hook error"),
        ]

        for error in errors_to_test:
            with self.assertRaises(PagodaError):
                raise error

    def test_exception_with_empty_message(self):
        """Test exceptions can be created with empty messages"""
        error = PagodaError()
        self.assertEqual(str(error), "")

        error = PluginError()
        self.assertEqual(str(error), "")

    def test_exception_with_multiple_arguments(self):
        """Test exceptions can be created with multiple arguments"""
        error = PluginValidationError("Field validation failed", "field_name", 123)
        # The exact string representation may vary by Python version
        self.assertIn("Field validation failed", str(error))

    def test_exception_chaining(self):
        """Test exception chaining works correctly"""
        original_error = ValueError("Original error")

        # Create chained exception manually
        chained_error = PluginLoadError("Failed to load plugin")
        chained_error.__cause__ = original_error

        self.assertEqual(chained_error.__cause__, original_error)
        self.assertIsInstance(chained_error, PluginLoadError)
        self.assertIsInstance(chained_error, PluginError)

    def test_custom_exception_attributes(self):
        """Test that custom attributes can be added to exceptions"""

        class CustomPluginError(PluginError):
            def __init__(self, message, plugin_id=None, error_code=None):
                super().__init__(message)
                self.plugin_id = plugin_id
                self.error_code = error_code

        error = CustomPluginError("Test error", plugin_id="test-plugin", error_code=500)
        self.assertEqual(error.plugin_id, "test-plugin")
        self.assertEqual(error.error_code, 500)
        self.assertIsInstance(error, PluginError)
        self.assertIsInstance(error, PagodaError)


class TestExceptionMessages(unittest.TestCase):
    """Test cases for exception message handling"""

    def test_exception_message_formatting(self):
        """Test that exception messages are formatted correctly"""
        test_cases = [
            (PagodaError("Simple message"), "Simple message"),
            (PluginError("Plugin: test-plugin failed"), "Plugin: test-plugin failed"),
            (PluginValidationError("Field 'name' is required"), "Field 'name' is required"),
            (AuthenticationError("Invalid credentials"), "Invalid credentials"),
            (DataAccessError("Database connection failed"), "Database connection failed"),
        ]

        for exception, expected_message in test_cases:
            self.assertEqual(str(exception), expected_message)

    def test_exception_repr(self):
        """Test that exception repr works correctly"""
        error = PluginValidationError("Test error")
        repr_str = repr(error)

        self.assertIn("PluginValidationError", repr_str)
        self.assertIn("Test error", repr_str)


if __name__ == "__main__":
    unittest.main()
