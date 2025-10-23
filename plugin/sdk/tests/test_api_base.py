"""
Tests for API base classes.

Tests the base API view and viewset classes defined in the pagoda_plugin_sdk.api.base module
including plugin context management, exception handling, and request processing.
"""

import unittest
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

if TYPE_CHECKING:
    from rest_framework import status
    from rest_framework.request import Request
    from rest_framework.response import Response
    from rest_framework.test import APIRequestFactory

try:
    from rest_framework import status
    from rest_framework.request import Request
    from rest_framework.response import Response
    from rest_framework.test import APIRequestFactory

    REST_FRAMEWORK_AVAILABLE = True
except ImportError:
    # Mock REST framework components if not available
    REST_FRAMEWORK_AVAILABLE = False

    class MockStatus:
        HTTP_400_BAD_REQUEST = 400
        HTTP_204_NO_CONTENT = 204

    status = MockStatus()  # type: ignore

    class Request:  # type: ignore
        pass

    class Response:  # type: ignore
        def __init__(self, data=None, status=200):
            self.data = data
            self.status_code = status

    class APIRequestFactory:  # type: ignore
        pass


# Add the SDK directory to Python path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk"))

from pagoda_plugin_sdk.api.base import PluginAPIView, PluginViewSet
from pagoda_plugin_sdk.exceptions import PluginError, PluginValidationError


@unittest.skipUnless(REST_FRAMEWORK_AVAILABLE, "Django REST Framework not available")
class TestPluginAPIView(unittest.TestCase):
    """Test cases for PluginAPIView class"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()

    def test_plugin_api_view_with_plugin_id(self):
        """Test PluginAPIView with plugin_id set"""

        class TestView(PluginAPIView):
            plugin_id = "test-plugin"
            plugin_version = "1.0.0"

        view = TestView()
        self.assertEqual(view.get_plugin_id(), "test-plugin")
        self.assertEqual(view.get_plugin_version(), "1.0.0")

    def test_plugin_api_view_without_plugin_id_raises_error(self):
        """Test PluginAPIView without plugin_id raises NotImplementedError"""

        class TestView(PluginAPIView):
            pass

        view = TestView()
        with self.assertRaises(NotImplementedError) as context:
            view.get_plugin_id()

        self.assertIn("must define plugin_id", str(context.exception))
        self.assertIn("TestView", str(context.exception))

    def test_get_plugin_version_returns_none_when_not_set(self):
        """Test get_plugin_version returns None when not set"""

        class TestView(PluginAPIView):
            plugin_id = "test-plugin"

        view = TestView()
        self.assertIsNone(view.get_plugin_version())

    @patch("pagoda_plugin_sdk.mixins.PluginAPIViewMixin.get_plugin_context")
    def test_get_plugin_context_enhances_parent_context(self, mock_parent_context):
        """Test get_plugin_context enhances parent context"""
        mock_parent_context.return_value = {"user": "test_user"}

        class TestView(PluginAPIView):
            plugin_id = "test-plugin"
            plugin_version = "2.0.0"

        view = TestView()
        context = view.get_plugin_context()

        expected_context = {
            "user": "test_user",
            "plugin_id": "test-plugin",
            "plugin_version": "2.0.0",
            "view_name": "TestView",
        }
        self.assertEqual(context, expected_context)

    @patch("pagoda_plugin_sdk.api.base.logger")
    def test_handle_exception_with_plugin_error(self, mock_logger):
        """Test handle_exception with PluginError"""

        class TestView(PluginAPIView):
            plugin_id = "test-plugin"

        view = TestView()
        plugin_error = PluginValidationError("Test validation error")

        response = view.handle_exception(plugin_error)

        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "plugin_error")
        self.assertEqual(response.data["message"], "Test validation error")
        self.assertEqual(response.data["plugin_id"], "test-plugin")

        mock_logger.error.assert_called_once()

    @patch("pagoda_plugin_sdk.api.base.logger")
    @patch("pagoda_plugin_sdk.mixins.PluginAPIViewMixin.handle_exception")
    def test_handle_exception_with_non_plugin_error(self, mock_parent_handle, mock_logger):
        """Test handle_exception with non-PluginError delegates to parent"""
        mock_parent_handle.return_value = Response({"error": "server_error"}, status=500)

        class TestView(PluginAPIView):
            plugin_id = "test-plugin"

        view = TestView()
        generic_error = ValueError("Generic error")

        response = view.handle_exception(generic_error)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["error"], "server_error")
        mock_parent_handle.assert_called_once_with(generic_error)
        mock_logger.error.assert_called_once()

    @patch("pagoda_plugin_sdk.api.base.logger")
    def test_handle_exception_with_unknown_plugin_id(self, mock_logger):
        """Test handle_exception when plugin_id is not set"""

        class TestView(PluginAPIView):
            pass

        view = TestView()
        plugin_error = PluginError("Test error")

        response = view.handle_exception(plugin_error)

        self.assertEqual(response.data["plugin_id"], "unknown")
        mock_logger.error.assert_called_once()


@unittest.skipUnless(REST_FRAMEWORK_AVAILABLE, "Django REST Framework not available")
class TestPluginViewSet(unittest.TestCase):
    """Test cases for PluginViewSet class"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()

    @patch("pagoda_plugin_sdk.api.base.logger")
    def test_plugin_viewset_initialization_with_plugin_id(self, mock_logger):
        """Test PluginViewSet initialization with plugin_id"""

        class TestViewSet(PluginViewSet):
            plugin_id = "test-plugin"
            plugin_version = "1.0.0"

        viewset = TestViewSet()
        self.assertEqual(viewset.plugin_id, "test-plugin")
        self.assertEqual(viewset.plugin_version, "1.0.0")

        # Should not log warning when plugin_id is set
        mock_logger.warning.assert_not_called()

    @patch("pagoda_plugin_sdk.api.base.logger")
    def test_plugin_viewset_initialization_without_plugin_id_logs_warning(self, mock_logger):
        """Test PluginViewSet initialization without plugin_id logs warning"""

        class TestViewSet(PluginViewSet):
            pass

        TestViewSet()

        mock_logger.warning.assert_called_once()
        self.assertIn("should define plugin_id", mock_logger.warning.call_args[0][0])

    def test_get_plugin_id_with_plugin_id_set(self):
        """Test get_plugin_id when plugin_id is set"""

        class TestViewSet(PluginViewSet):
            plugin_id = "test-plugin"

        viewset = TestViewSet()
        self.assertEqual(viewset.get_plugin_id(), "test-plugin")

    def test_get_plugin_id_without_plugin_id_raises_error(self):
        """Test get_plugin_id without plugin_id raises NotImplementedError"""

        class TestViewSet(PluginViewSet):
            pass

        viewset = TestViewSet()
        with self.assertRaises(NotImplementedError) as context:
            viewset.get_plugin_id()

        self.assertIn("must define plugin_id", str(context.exception))

    def test_get_plugin_context_with_all_attributes(self):
        """Test get_plugin_context returns complete context"""

        class TestViewSet(PluginViewSet):
            plugin_id = "test-plugin"
            plugin_version = "1.0.0"

        viewset = TestViewSet()
        viewset.action = "list"

        # Mock request and user
        request = Mock()
        request.user = Mock()
        viewset.request = request

        context = viewset.get_plugin_context()

        expected_context = {
            "plugin_id": "test-plugin",
            "plugin_version": "1.0.0",
            "viewset_name": "TestViewSet",
            "action": "list",
            "user": request.user,
        }
        self.assertEqual(context, expected_context)

    def test_get_plugin_context_without_plugin_id(self):
        """Test get_plugin_context when plugin_id is not set"""

        class TestViewSet(PluginViewSet):
            pass

        viewset = TestViewSet()

        context = viewset.get_plugin_context()

        self.assertEqual(context["plugin_id"], "unknown")
        self.assertIsNone(context["plugin_version"])
        self.assertIsNone(context["action"])
        self.assertIsNone(context["user"])

    def test_get_plugin_context_without_request(self):
        """Test get_plugin_context when request is not available"""

        class TestViewSet(PluginViewSet):
            plugin_id = "test-plugin"

        viewset = TestViewSet()

        context = viewset.get_plugin_context()

        self.assertIsNone(context["user"])

    def test_filter_queryset_for_plugin_default_implementation(self):
        """Test filter_queryset_for_plugin returns queryset unchanged by default"""

        class TestViewSet(PluginViewSet):
            plugin_id = "test-plugin"

        viewset = TestViewSet()
        mock_queryset = Mock()

        result = viewset.filter_queryset_for_plugin(mock_queryset)

        self.assertEqual(result, mock_queryset)

    @patch("pagoda_plugin_sdk.api.base.logger")
    def test_handle_exception_with_plugin_error(self, mock_logger):
        """Test handle_exception with PluginError"""

        class TestViewSet(PluginViewSet):
            plugin_id = "test-plugin"

        viewset = TestViewSet()
        viewset.action = "create"
        plugin_error = PluginError("Test plugin error")

        response = viewset.handle_exception(plugin_error)

        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "plugin_error")
        self.assertEqual(response.data["message"], "Test plugin error")
        self.assertEqual(response.data["plugin_id"], "test-plugin")
        self.assertEqual(response.data["action"], "create")

        mock_logger.error.assert_called_once()

    def test_initialize_request_adds_plugin_context(self):
        """Test initialize_request adds plugin context to request"""

        class TestViewSet(PluginViewSet):
            plugin_id = "test-plugin"

        viewset = TestViewSet()

        # Mock parent's initialize_request
        with patch("rest_framework.viewsets.ModelViewSet.initialize_request") as mock_init:
            mock_request = Mock(spec=Request)
            mock_init.return_value = mock_request

            result = viewset.initialize_request(mock_request)

            self.assertEqual(result, mock_request)
            self.assertTrue(hasattr(result, "plugin_context"))
            self.assertEqual(result.plugin_context["plugin_id"], "test-plugin")

    def test_initialize_request_preserves_existing_plugin_context(self):
        """Test initialize_request preserves existing plugin context"""

        class TestViewSet(PluginViewSet):
            plugin_id = "test-plugin"

        viewset = TestViewSet()

        with patch("rest_framework.viewsets.ModelViewSet.initialize_request") as mock_init:
            mock_request = Mock(spec=Request)
            mock_request.plugin_context = {"existing": "context"}
            mock_init.return_value = mock_request

            result = viewset.initialize_request(mock_request)

            self.assertEqual(result.plugin_context, {"existing": "context"})

    @patch("pagoda_plugin_sdk.api.base.logger")
    def test_create_logs_activity(self, mock_logger):
        """Test create method logs plugin activity"""

        class TestViewSet(PluginViewSet):
            plugin_id = "test-plugin"

        viewset = TestViewSet()

        with patch("rest_framework.viewsets.ModelViewSet.create") as mock_create:
            mock_create.return_value = Response({"id": 1})
            mock_request = Mock(spec=Request)

            viewset.create(mock_request)

            mock_logger.info.assert_called_once_with("Plugin test-plugin creating new instance")
            mock_create.assert_called_once_with(mock_request)

    @patch("pagoda_plugin_sdk.api.base.logger")
    def test_update_logs_activity(self, mock_logger):
        """Test update method logs plugin activity"""

        class TestViewSet(PluginViewSet):
            plugin_id = "test-plugin"

        viewset = TestViewSet()

        with patch("rest_framework.viewsets.ModelViewSet.update") as mock_update:
            mock_update.return_value = Response({"id": 1})
            mock_request = Mock(spec=Request)

            viewset.update(mock_request)

            mock_logger.info.assert_called_once_with("Plugin test-plugin updating instance")
            mock_update.assert_called_once_with(mock_request)

    @patch("pagoda_plugin_sdk.api.base.logger")
    def test_destroy_logs_activity(self, mock_logger):
        """Test destroy method logs plugin activity"""

        class TestViewSet(PluginViewSet):
            plugin_id = "test-plugin"

        viewset = TestViewSet()

        with patch("rest_framework.viewsets.ModelViewSet.destroy") as mock_destroy:
            mock_destroy.return_value = Response(status=status.HTTP_204_NO_CONTENT)
            mock_request = Mock(spec=Request)

            viewset.destroy(mock_request)

            mock_logger.info.assert_called_once_with("Plugin test-plugin deleting instance")
            mock_destroy.assert_called_once_with(mock_request)


if __name__ == "__main__":
    unittest.main()
