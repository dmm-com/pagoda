"""
Tests for the override decorator and utilities.

These tests verify the SDK-side override functionality including
the decorator, metadata handling, and response helpers.
"""

import unittest
from unittest.mock import MagicMock

# Check if Django is configured for response helper tests
try:
    import django

    django.setup()
    DJANGO_CONFIGURED = True
except Exception:
    DJANGO_CONFIGURED = False

from pagoda_plugin_sdk.override import (
    OVERRIDE_META_ATTR,
    OverrideContext,
    OverrideMeta,
    accepted_response,
    created_response,
    error_response,
    no_content_response,
    not_found_response,
    override_operation,
    permission_denied_response,
    success_response,
    validation_error_response,
)


class TestOverrideMeta(unittest.TestCase):
    """Tests for OverrideMeta dataclass."""

    def test_meta_creation(self):
        """Test creating OverrideMeta with operation."""
        meta = OverrideMeta(operation="create")
        self.assertEqual(meta.operation, "create")

    def test_to_dict(self):
        """Test conversion to dictionary."""
        meta = OverrideMeta(operation="create")
        result = meta.to_dict()
        self.assertEqual(result["operation"], "create")
        self.assertNotIn("priority", result)


class TestOverrideOperationDecorator(unittest.TestCase):
    """Tests for @override_operation decorator (new-style)."""

    def test_decorator_attaches_metadata(self):
        """Test decorator attaches metadata to function."""

        @override_operation("create")
        def my_handler(self, context):
            return "response"

        self.assertTrue(hasattr(my_handler, OVERRIDE_META_ATTR))
        meta = getattr(my_handler, OVERRIDE_META_ATTR)
        self.assertIsInstance(meta, OverrideMeta)
        self.assertEqual(meta.operation, "create")

    def test_decorator_preserves_function(self):
        """Test decorated function still works."""

        @override_operation("update")
        def my_handler(self, context):
            return f"updated {context}"

        result = my_handler(None, "test-context")
        self.assertEqual(result, "updated test-context")

    def test_decorator_invalid_operation(self):
        """Test decorator raises error for invalid operation."""
        with self.assertRaises(ValueError) as context:

            @override_operation("invalid")
            def my_handler(self, context):
                pass

        self.assertIn("Invalid operation", str(context.exception))

    def test_decorator_normalizes_operation(self):
        """Test decorator normalizes operation to lowercase."""

        @override_operation("CREATE")
        def my_handler(self, context):
            return "response"

        meta = getattr(my_handler, OVERRIDE_META_ATTR)
        self.assertEqual(meta.operation, "create")


@unittest.skipUnless(DJANGO_CONFIGURED, "Django not configured")
class TestResponseHelpers(unittest.TestCase):
    """Tests for response helper functions."""

    def test_success_response(self):
        """Test success_response creates correct response."""
        response = success_response({"key": "value"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"key": "value"})

    def test_success_response_empty(self):
        """Test success_response with no data."""
        response = success_response()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {})

    def test_success_response_custom_status(self):
        """Test success_response with custom status."""
        response = success_response({"data": "test"}, status_code=201)
        self.assertEqual(response.status_code, 201)

    def test_created_response(self):
        """Test created_response creates 201 response."""
        response = created_response(entry_id=123, entry_name="test")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["id"], 123)
        self.assertEqual(response.data["name"], "test")

    def test_created_response_with_data(self):
        """Test created_response with custom data."""
        response = created_response(data={"custom": "data"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {"custom": "data"})

    def test_accepted_response(self):
        """Test accepted_response creates 202 response."""
        response = accepted_response()
        self.assertEqual(response.status_code, 202)
        self.assertIn("message", response.data)

    def test_accepted_response_custom_message(self):
        """Test accepted_response with custom message."""
        response = accepted_response(message="Processing started")
        self.assertEqual(response.data["message"], "Processing started")

    def test_no_content_response(self):
        """Test no_content_response creates 204 response."""
        response = no_content_response()
        self.assertEqual(response.status_code, 204)

    def test_error_response(self):
        """Test error_response creates error response."""
        response = error_response("Something went wrong")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Something went wrong")

    def test_error_response_custom_status(self):
        """Test error_response with custom status."""
        response = error_response("Server error", status_code=500)
        self.assertEqual(response.status_code, 500)

    def test_error_response_with_details(self):
        """Test error_response with details."""
        response = error_response("Validation failed", details={"field": "invalid"})
        self.assertEqual(response.data["details"], {"field": "invalid"})

    def test_not_found_response(self):
        """Test not_found_response creates 404 response."""
        response = not_found_response()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error"], "Entry not found")

    def test_not_found_response_custom_message(self):
        """Test not_found_response with custom message."""
        response = not_found_response("Resource not found")
        self.assertEqual(response.data["error"], "Resource not found")

    def test_permission_denied_response(self):
        """Test permission_denied_response creates 403 response."""
        response = permission_denied_response()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "Permission denied")

    def test_permission_denied_response_with_entries(self):
        """Test permission_denied_response with denied entries list."""
        response = permission_denied_response(message="Access denied", denied_entries=[1, 2, 3])
        self.assertEqual(response.data["denied_entries"], [1, 2, 3])

    def test_validation_error_response_string(self):
        """Test validation_error_response with string."""
        response = validation_error_response("Invalid input")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Invalid input")

    def test_validation_error_response_dict(self):
        """Test validation_error_response with dict."""
        errors = {"name": ["Required"], "email": ["Invalid"]}
        response = validation_error_response(errors)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, errors)

    def test_validation_error_response_list(self):
        """Test validation_error_response with list."""
        errors = ["Error 1", "Error 2"]
        response = validation_error_response(errors)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, errors)


class TestOverrideContext(unittest.TestCase):
    """Tests for OverrideContext class."""

    def test_context_creation(self):
        """Test creating an OverrideContext with new-style fields."""
        mock_request = MagicMock()
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_request.user = mock_user
        mock_entity = MagicMock()
        mock_entity.name = "TestEntity"

        context = OverrideContext(
            request=mock_request,
            user=mock_user,
            entity=mock_entity,
            plugin_id="test-plugin",
            operation="create",
            data={"name": "test"},
            params={"config_id": 99},
        )

        self.assertEqual(context.plugin_id, "test-plugin")
        self.assertEqual(context.operation, "create")
        self.assertEqual(context.entity, mock_entity)
        self.assertEqual(context.data, {"name": "test"})
        self.assertEqual(context.params, {"config_id": 99})

    def test_context_with_entry(self):
        """Test context with entry for retrieve/update/delete operations."""
        mock_request = MagicMock()
        mock_user = MagicMock()
        mock_entity = MagicMock()
        mock_entity.name = "TestEntity"
        mock_entry = MagicMock()
        mock_entry.id = 123

        context = OverrideContext(
            request=mock_request,
            user=mock_user,
            entity=mock_entity,
            entry=mock_entry,
            plugin_id="test-plugin",
            operation="retrieve",
        )

        self.assertEqual(context.entry, mock_entry)
        self.assertEqual(context.entry.id, 123)

    def test_is_authenticated_true(self):
        """Test is_authenticated when user is authenticated."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True

        context = OverrideContext(
            request=MagicMock(),
            user=mock_user,
            entity=MagicMock(),
            plugin_id="test",
            operation="create",
        )

        self.assertTrue(context.is_authenticated)

    def test_is_authenticated_false(self):
        """Test is_authenticated when user is not authenticated."""
        mock_user = MagicMock()
        mock_user.is_authenticated = False

        context = OverrideContext(
            request=MagicMock(),
            user=mock_user,
            entity=MagicMock(),
            plugin_id="test",
            operation="create",
        )

        self.assertFalse(context.is_authenticated)

    def test_get_request_data_from_data_field(self):
        """Test get_request_data returns data field when set."""
        mock_request = MagicMock()
        mock_request.data = {"other": "data"}

        context = OverrideContext(
            request=mock_request,
            user=MagicMock(),
            entity=MagicMock(),
            plugin_id="test",
            operation="create",
            data={"key": "value"},
        )

        data = context.get_request_data()
        self.assertEqual(data, {"key": "value"})

    def test_get_request_data_from_request(self):
        """Test get_request_data falls back to request.data."""
        mock_request = MagicMock()
        mock_request.data = {"key": "value"}

        context = OverrideContext(
            request=mock_request,
            user=MagicMock(),
            entity=MagicMock(),
            plugin_id="test",
            operation="create",
        )

        data = context.get_request_data()
        self.assertEqual(data, {"key": "value"})


if __name__ == "__main__":
    unittest.main()
