"""
Tests for HelloWorldPlugin API views

Tests the behavior of all API endpoints including:
- Hello, Greet, Status, Test views
- Entity list and detail views
- Entry list and detail views
- Authentication and permissions
- Error handling
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase
from pagoda_hello_world_plugin.api_v2.views import (
    EntityDetailView,
    EntityListView,
    EntryDetailView,
    EntryListView,
    GreetView,
    HelloView,
    StatusView,
    TestView,
)
from rest_framework import status


class TestHelloView(TestCase):
    """Test cases for HelloView"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.view = HelloView.as_view()

    def test_get_authenticated_user(self):
        """Test GET request with authenticated user"""
        request = self.factory.get("/api/v2/plugins/hello-world-plugin/hello/")
        request.user = Mock()
        request.user.username = "test_user"
        request.user.is_authenticated = True

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("Hello from External Hello World Plugin", response.data["message"])
        self.assertEqual(response.data["user"]["username"], "test_user")
        self.assertTrue(response.data["user"]["is_authenticated"])

    def test_get_anonymous_user(self):
        """Test GET request with anonymous user"""
        request = self.factory.get("/api/v2/plugins/hello-world-plugin/hello/")
        request.user = Mock()
        request.user.username = ""
        request.user.is_authenticated = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "anonymous")
        self.assertFalse(response.data["user"]["is_authenticated"])

    def test_get_response_structure(self):
        """Test GET response has correct structure"""
        request = self.factory.get("/api/v2/plugins/hello-world-plugin/hello/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        # Check required fields
        self.assertIn("message", response.data)
        self.assertIn("plugin", response.data)
        self.assertIn("user", response.data)
        self.assertIn("timestamp", response.data)

        # Check plugin info
        plugin = response.data["plugin"]
        self.assertEqual(plugin["id"], "hello-world-plugin")
        self.assertEqual(plugin["name"], "Hello World Plugin")
        self.assertEqual(plugin["version"], "1.0.0")

    def test_post_with_custom_message(self):
        """Test POST request with custom message"""
        request = self.factory.post(
            "/api/v2/plugins/hello-world-plugin/hello/",
            data={"message": "Custom greeting"},
            content_type="application/json",
        )
        request.user = Mock()
        request.user.username = "test_user"
        request.user.is_authenticated = True

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Custom greeting", response.data["message"])

    def test_post_without_message(self):
        """Test POST request without message (uses default)"""
        request = self.factory.post(
            "/api/v2/plugins/hello-world-plugin/hello/", data={}, content_type="application/json"
        )
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Hello World!", response.data["message"])


class TestGreetView(TestCase):
    """Test cases for GreetView"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.view = GreetView.as_view()

    def test_greet_with_name(self):
        """Test greeting with a specific name"""
        request = self.factory.get("/api/v2/plugins/hello-world-plugin/greet/Alice/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request, name="Alice")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Alice", response.data["greeting"])
        self.assertEqual(response.data["requested_name"], "Alice")

    def test_greet_with_different_names(self):
        """Test greeting with different names"""
        names = ["Bob", "Charlie", "日本太郎"]

        for name in names:
            request = self.factory.get(f"/api/v2/plugins/hello-world-plugin/greet/{name}/")
            request.user = Mock()
            request.user.is_authenticated = False

            response = self.view(request, name=name)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(name, response.data["greeting"])
            self.assertEqual(response.data["requested_name"], name)

    def test_greet_response_structure(self):
        """Test greet response has correct structure"""
        request = self.factory.get("/api/v2/plugins/hello-world-plugin/greet/TestUser/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request, name="TestUser")

        # Check required fields
        self.assertIn("greeting", response.data)
        self.assertIn("plugin", response.data)
        self.assertIn("requested_name", response.data)
        self.assertIn("user", response.data)
        self.assertIn("timestamp", response.data)


class TestStatusView(TestCase):
    """Test cases for StatusView"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.view = StatusView.as_view()

    def test_status_response(self):
        """Test status endpoint returns correct information"""
        request = self.factory.get("/api/v2/plugins/hello-world-plugin/status/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check plugin info
        plugin = response.data["plugin"]
        self.assertEqual(plugin["id"], "hello-world-plugin")
        self.assertEqual(plugin["status"], "active")
        self.assertEqual(plugin["author"], "Pagoda Development Team")

        # Check system info
        system = response.data["system"]
        self.assertEqual(system["django_app"], "pagoda_hello_world_plugin")
        self.assertIn("endpoints", system)
        self.assertIsInstance(system["endpoints"], list)

    def test_status_endpoints_list(self):
        """Test that status returns list of available endpoints"""
        request = self.factory.get("/api/v2/plugins/hello-world-plugin/status/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        endpoints = response.data["system"]["endpoints"]
        self.assertGreater(len(endpoints), 0)
        self.assertIn("/api/v2/plugins/hello-world-plugin/hello/", endpoints)
        self.assertIn("/api/v2/plugins/hello-world-plugin/status/", endpoints)


class TestTestView(TestCase):
    """Test cases for TestView (authentication-free endpoint)"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.view = TestView.as_view()

    def test_test_endpoint_without_auth(self):
        """Test that test endpoint works without authentication"""
        request = self.factory.get("/api/v2/plugins/hello-world-plugin/test/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["test"], "no-auth")

    def test_test_endpoint_response_structure(self):
        """Test test endpoint response structure"""
        request = self.factory.get("/api/v2/plugins/hello-world-plugin/test/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        # Check required fields
        self.assertIn("message", response.data)
        self.assertIn("plugin", response.data)
        self.assertIn("test", response.data)
        self.assertIn("user", response.data)


class TestEntityListView(TestCase):
    """Test cases for EntityListView"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.view = EntityListView.as_view()

    @patch("pagoda_hello_world_plugin.api_v2.views.Entity")
    def test_entity_list_success(self, mock_entity_class):
        """Test successful entity list retrieval"""
        # Mock entity objects
        mock_entity1 = Mock()
        mock_entity1.id = 1
        mock_entity1.name = "Entity1"
        mock_entity1.note = "Note1"
        mock_entity1.is_active = True
        mock_entity1.created_time = datetime(2024, 1, 1)
        mock_entity1.created_user = Mock(username="user1")

        mock_entity2 = Mock()
        mock_entity2.id = 2
        mock_entity2.name = "Entity2"
        mock_entity2.note = "Note2"
        mock_entity2.is_active = True
        mock_entity2.created_time = datetime(2024, 1, 2)
        mock_entity2.created_user = Mock(username="user2")

        # Mock queryset
        mock_queryset = [mock_entity1, mock_entity2]
        mock_entity_class.objects.filter.return_value = mock_queryset
        mock_entity_class.objects.filter.return_value.count.return_value = 2

        request = self.factory.get("/api/v2/plugins/hello-world-plugin/entities/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("entities", response.data)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["entities"]), 2)

    @patch("pagoda_hello_world_plugin.api_v2.views.Entity", None)
    def test_entity_list_model_unavailable(self):
        """Test entity list when Entity model is not available"""
        request = self.factory.get("/api/v2/plugins/hello-world-plugin/entities/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", response.data)

    @patch("pagoda_hello_world_plugin.api_v2.views.Entity")
    def test_entity_list_exception_handling(self, mock_entity_class):
        """Test entity list error handling"""
        mock_entity_class.objects.filter.side_effect = Exception("Database error")

        request = self.factory.get("/api/v2/plugins/hello-world-plugin/entities/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)


class TestEntityDetailView(TestCase):
    """Test cases for EntityDetailView"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.view = EntityDetailView.as_view()

    @patch("pagoda_hello_world_plugin.api_v2.views.Entity")
    def test_entity_detail_success(self, mock_entity_class):
        """Test successful entity detail retrieval"""
        mock_entity = Mock()
        mock_entity.id = 1
        mock_entity.name = "TestEntity"
        mock_entity.note = "Test note"
        mock_entity.is_active = True
        mock_entity.created_time = datetime(2024, 1, 1)
        mock_entity.created_user = Mock(username="test_user")

        mock_entity_class.objects.get.return_value = mock_entity

        request = self.factory.get("/api/v2/plugins/hello-world-plugin/entities/1/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request, entity_id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("entity", response.data)
        self.assertEqual(response.data["entity"]["id"], 1)
        self.assertEqual(response.data["entity"]["name"], "TestEntity")

    @patch("pagoda_hello_world_plugin.api_v2.views.Entity")
    def test_entity_detail_not_found(self, mock_entity_class):
        """Test entity detail when entity doesn't exist"""
        from django.core.exceptions import ObjectDoesNotExist

        mock_entity_class.DoesNotExist = ObjectDoesNotExist
        mock_entity_class.objects.get.side_effect = ObjectDoesNotExist()

        request = self.factory.get("/api/v2/plugins/hello-world-plugin/entities/999/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request, entity_id=999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)


class TestEntryListView(TestCase):
    """Test cases for EntryListView"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.view = EntryListView.as_view()

    @patch("pagoda_hello_world_plugin.api_v2.views.Entry")
    def test_entry_list_success(self, mock_entry_class):
        """Test successful entry list retrieval"""
        # Mock entry objects
        mock_schema = Mock()
        mock_schema.id = 1
        mock_schema.name = "TestEntity"

        mock_entry1 = Mock()
        mock_entry1.id = 1
        mock_entry1.name = "Entry1"
        mock_entry1.note = "Note1"
        mock_entry1.is_active = True
        mock_entry1.schema = mock_schema
        mock_entry1.created_time = datetime(2024, 1, 1)
        mock_entry1.created_user = Mock(username="user1")
        mock_entry1.updated_time = datetime(2024, 1, 2)

        # Mock queryset
        mock_queryset = [mock_entry1]
        mock_entry_class.objects.filter.return_value = mock_queryset
        mock_entry_class.objects.filter.return_value.count.return_value = 1

        request = self.factory.get("/api/v2/plugins/hello-world-plugin/entries/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("entries", response.data)
        self.assertEqual(len(response.data["entries"]), 1)

    @patch("pagoda_hello_world_plugin.api_v2.views.Entry")
    def test_entry_list_with_entity_filter(self, mock_entry_class):
        """Test entry list with entity_id filter"""
        mock_queryset = Mock()
        mock_entry_class.objects.filter.return_value = mock_queryset
        mock_queryset.filter.return_value = []
        mock_queryset.filter.return_value.count = lambda: 0

        request = self.factory.get("/api/v2/plugins/hello-world-plugin/entries/?entity_id=1")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify that filter was called with entity_id
        mock_queryset.filter.assert_called()

    @patch("pagoda_hello_world_plugin.api_v2.views.Entry")
    def test_entry_list_with_limit(self, mock_entry_class):
        """Test entry list with limit parameter"""
        mock_queryset = [Mock(), Mock(), Mock()]
        mock_entry_class.objects.filter.return_value = mock_queryset

        request = self.factory.get("/api/v2/plugins/hello-world-plugin/entries/?limit=2")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("pagoda_hello_world_plugin.api_v2.views.Entry")
    def test_entry_list_invalid_entity_id(self, mock_entry_class):
        """Test entry list with invalid entity_id"""
        request = self.factory.get("/api/v2/plugins/hello-world-plugin/entries/?entity_id=invalid")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)


class TestEntryDetailView(TestCase):
    """Test cases for EntryDetailView"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.view = EntryDetailView.as_view()

    @patch("pagoda_hello_world_plugin.api_v2.views.Entry")
    def test_entry_detail_success(self, mock_entry_class):
        """Test successful entry detail retrieval"""
        mock_schema = Mock()
        mock_schema.id = 1
        mock_schema.name = "TestEntity"

        mock_entry = Mock()
        mock_entry.id = 1
        mock_entry.name = "TestEntry"
        mock_entry.note = "Test note"
        mock_entry.is_active = True
        mock_entry.schema = mock_schema
        mock_entry.created_time = datetime(2024, 1, 1)
        mock_entry.created_user = Mock(username="test_user")
        mock_entry.updated_time = datetime(2024, 1, 2)
        mock_entry.get_attrs.return_value = [{"name": "attr1", "value": "value1"}]

        mock_entry_class.objects.get.return_value = mock_entry

        request = self.factory.get("/api/v2/plugins/hello-world-plugin/entries/1/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request, entry_id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("entry", response.data)
        self.assertEqual(response.data["entry"]["id"], 1)
        self.assertEqual(response.data["entry"]["name"], "TestEntry")
        self.assertIn("attributes", response.data["entry"])

    @patch("pagoda_hello_world_plugin.api_v2.views.Entry")
    def test_entry_detail_not_found(self, mock_entry_class):
        """Test entry detail when entry doesn't exist"""
        from django.core.exceptions import ObjectDoesNotExist

        mock_entry_class.DoesNotExist = ObjectDoesNotExist
        mock_entry_class.objects.get.side_effect = ObjectDoesNotExist()

        request = self.factory.get("/api/v2/plugins/hello-world-plugin/entries/999/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = self.view(request, entry_id=999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)


class TestHelloViewCeleryTask(TestCase):
    """Test cases for HelloView Celery task integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.view = HelloView.as_view()

    @patch("pagoda_hello_world_plugin.api_v2.views.PluginTaskRegistry")
    @patch("pagoda_hello_world_plugin.api_v2.views.Job")
    def test_post_queues_task_successfully(self, mock_job_class, mock_registry):
        """Test that POST request queues a Celery task"""
        mock_job = Mock()
        mock_job.id = 1
        mock_job.status = 1
        mock_job_class._create_new_job.return_value = mock_job

        mock_registry.get_operation_id.return_value = 5001

        request = self.factory.post(
            "/api/v2/plugins/hello-world-plugin/hello/",
            data={"message": "Test message"},
            content_type="application/json",
        )
        request.user = Mock()
        request.user.username = "test_user"
        request.user.is_authenticated = True

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("job_id", response.data)
        self.assertEqual(response.data["job_id"], 1)
        self.assertIn("task_message", response.data)
        self.assertEqual(response.data["task_message"], "Test message")

        mock_job_class._create_new_job.assert_called_once()
        mock_job.run.assert_called_once()

    @patch("pagoda_hello_world_plugin.api_v2.views.PluginTaskRegistry")
    @patch("pagoda_hello_world_plugin.api_v2.views.Job")
    def test_post_with_registry_error(self, mock_job_class, mock_registry):
        """Test error handling when PluginTaskRegistry fails"""
        mock_registry.get_operation_id.side_effect = ValueError("Operation not found")

        request = self.factory.post(
            "/api/v2/plugins/hello-world-plugin/hello/",
            data={"message": "Test"},
            content_type="application/json",
        )
        request.user = Mock()
        request.user.is_authenticated = True

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)
        self.assertIn("Failed to queue task", response.data["error"])

    @patch("pagoda_hello_world_plugin.api_v2.views.PluginTaskRegistry")
    @patch("pagoda_hello_world_plugin.api_v2.views.Job")
    def test_post_with_job_creation_error(self, mock_job_class, mock_registry):
        """Test error handling when Job creation fails"""
        mock_registry.get_operation_id.return_value = 5001
        mock_job_class._create_new_job.side_effect = Exception("Database error")

        request = self.factory.post(
            "/api/v2/plugins/hello-world-plugin/hello/",
            data={"message": "Test"},
            content_type="application/json",
        )
        request.user = Mock()
        request.user.is_authenticated = True

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)


if __name__ == "__main__":
    unittest.main()
