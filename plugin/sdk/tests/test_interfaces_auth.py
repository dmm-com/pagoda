"""
Tests for authentication interface.

Tests the AuthInterface protocol and its implementations
to ensure proper authentication and authorization functionality.
"""

import unittest
from unittest.mock import Mock

from pagoda_plugin_sdk.interfaces.auth import AuthInterface


class TestAuthInterface(unittest.TestCase):
    """Test cases for AuthInterface"""

    def test_auth_interface_is_abstract(self):
        """Test that AuthInterface cannot be instantiated directly"""
        with self.assertRaises(TypeError):
            AuthInterface()

    def test_auth_interface_requires_abstract_methods(self):
        """Test that subclasses must implement abstract methods"""

        class IncompleteAuthImpl(AuthInterface):
            def get_current_user_info(self, request):
                return {}

            # Missing other abstract methods

        with self.assertRaises(TypeError):
            IncompleteAuthImpl()


class MockAuthImplementation(AuthInterface):
    """Mock implementation of AuthInterface for testing"""

    def __init__(self):
        self.users = {
            "testuser": {
                "id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "is_authenticated": True,
                "is_staff": False,
                "is_superuser": False,
                "groups": ["editors", "reviewers"],
                "roles": ["content_editor"],
            },
            "admin": {
                "id": 2,
                "username": "admin",
                "email": "admin@example.com",
                "is_authenticated": True,
                "is_staff": True,
                "is_superuser": True,
                "groups": ["administrators"],
                "roles": ["admin"],
            },
        }
        self.tokens = {
            "valid_token": "testuser",
            "admin_token": "admin",
        }
        self.permissions = {
            "testuser": ["read_content", "edit_content"],
            "admin": ["read_content", "edit_content", "delete_content", "manage_users"],
        }

    def get_current_user_info(self, request):
        """Get current user info from mock request"""
        if hasattr(request, "user") and request.user:
            username = getattr(request.user, "username", None)
            if username in self.users:
                return self.users[username].copy()

        # Return anonymous user info
        return {
            "id": None,
            "username": None,
            "email": None,
            "is_authenticated": False,
            "is_staff": False,
            "is_superuser": False,
            "groups": [],
            "roles": [],
        }

    def check_user_permission(self, user, permission):
        """Check if user has specific permission"""
        if hasattr(user, "username"):
            username = user.username
        elif isinstance(user, str):
            username = user
        else:
            return False

        user_permissions = self.permissions.get(username, [])
        return permission in user_permissions

    def get_user_groups(self, user):
        """Get user's group names"""
        if hasattr(user, "username"):
            username = user.username
        elif isinstance(user, str):
            username = user
        else:
            return []

        user_info = self.users.get(username, {})
        return user_info.get("groups", [])

    def authenticate_token(self, token):
        """Authenticate user by token"""
        username = self.tokens.get(token)
        if username:
            # Return mock user object
            user = Mock()
            user.username = username
            user_info = self.users[username]
            for key, value in user_info.items():
                setattr(user, key, value)
            return user
        return None

    def has_object_permission(self, user, obj, permission):
        """Check object-level permission (custom implementation)"""
        # Custom logic: admin can do anything, others need to own the object
        if hasattr(user, "is_superuser") and user.is_superuser:
            return True

        if hasattr(obj, "owner") and hasattr(user, "username"):
            return obj.owner == user.username

        return super().has_object_permission(user, obj, permission)

    def get_user_roles(self, user):
        """Get user's role names (custom implementation)"""
        if hasattr(user, "username"):
            username = user.username
        elif isinstance(user, str):
            username = user
        else:
            return []

        user_info = self.users.get(username, {})
        return user_info.get("roles", [])


class TestMockAuthImplementation(unittest.TestCase):
    """Test cases for MockAuthImplementation"""

    def setUp(self):
        """Set up test fixtures"""
        self.auth = MockAuthImplementation()

    def test_get_current_user_info_authenticated_user(self):
        """Test getting current user info for authenticated user"""
        request = Mock()
        request.user = Mock()
        request.user.username = "testuser"

        user_info = self.auth.get_current_user_info(request)

        expected_info = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "is_authenticated": True,
            "is_staff": False,
            "is_superuser": False,
            "groups": ["editors", "reviewers"],
            "roles": ["content_editor"],
        }
        self.assertEqual(user_info, expected_info)

    def test_get_current_user_info_anonymous_user(self):
        """Test getting current user info for anonymous user"""
        request = Mock()
        request.user = None

        user_info = self.auth.get_current_user_info(request)

        expected_info = {
            "id": None,
            "username": None,
            "email": None,
            "is_authenticated": False,
            "is_staff": False,
            "is_superuser": False,
            "groups": [],
            "roles": [],
        }
        self.assertEqual(user_info, expected_info)

    def test_get_current_user_info_nonexistent_user(self):
        """Test getting current user info for nonexistent user"""
        request = Mock()
        request.user = Mock()
        request.user.username = "nonexistent"

        user_info = self.auth.get_current_user_info(request)

        # Should return anonymous user info for nonexistent users
        self.assertFalse(user_info["is_authenticated"])
        self.assertIsNone(user_info["username"])

    def test_check_user_permission_with_permission(self):
        """Test checking user permission when user has it"""
        user = Mock()
        user.username = "testuser"

        has_permission = self.auth.check_user_permission(user, "read_content")
        self.assertTrue(has_permission)

        has_permission = self.auth.check_user_permission(user, "edit_content")
        self.assertTrue(has_permission)

    def test_check_user_permission_without_permission(self):
        """Test checking user permission when user doesn't have it"""
        user = Mock()
        user.username = "testuser"

        has_permission = self.auth.check_user_permission(user, "delete_content")
        self.assertFalse(has_permission)

        has_permission = self.auth.check_user_permission(user, "manage_users")
        self.assertFalse(has_permission)

    def test_check_user_permission_with_string_user(self):
        """Test checking user permission with string username"""
        has_permission = self.auth.check_user_permission("admin", "manage_users")
        self.assertTrue(has_permission)

        has_permission = self.auth.check_user_permission("testuser", "manage_users")
        self.assertFalse(has_permission)

    def test_check_user_permission_invalid_user(self):
        """Test checking user permission with invalid user"""
        has_permission = self.auth.check_user_permission(None, "read_content")
        self.assertFalse(has_permission)

        has_permission = self.auth.check_user_permission(123, "read_content")
        self.assertFalse(has_permission)

    def test_get_user_groups_with_mock_user(self):
        """Test getting user groups with mock user object"""
        user = Mock()
        user.username = "testuser"

        groups = self.auth.get_user_groups(user)
        self.assertEqual(groups, ["editors", "reviewers"])

    def test_get_user_groups_with_string_user(self):
        """Test getting user groups with string username"""
        groups = self.auth.get_user_groups("admin")
        self.assertEqual(groups, ["administrators"])

    def test_get_user_groups_nonexistent_user(self):
        """Test getting user groups for nonexistent user"""
        groups = self.auth.get_user_groups("nonexistent")
        self.assertEqual(groups, [])

        user = Mock()
        user.username = "nonexistent"
        groups = self.auth.get_user_groups(user)
        self.assertEqual(groups, [])

    def test_authenticate_token_valid_token(self):
        """Test authenticating with valid token"""
        user = self.auth.authenticate_token("valid_token")

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.is_authenticated)
        self.assertFalse(user.is_staff)

    def test_authenticate_token_admin_token(self):
        """Test authenticating with admin token"""
        user = self.auth.authenticate_token("admin_token")

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "admin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_authenticate_token_invalid_token(self):
        """Test authenticating with invalid token"""
        user = self.auth.authenticate_token("invalid_token")
        self.assertIsNone(user)

        user = self.auth.authenticate_token("")
        self.assertIsNone(user)

    def test_has_object_permission_superuser(self):
        """Test object permission check for superuser"""
        admin_user = Mock()
        admin_user.is_superuser = True
        admin_user.username = "admin"

        obj = Mock()
        obj.owner = "someone_else"

        has_permission = self.auth.has_object_permission(admin_user, obj, "edit")
        self.assertTrue(has_permission)

    def test_has_object_permission_owner(self):
        """Test object permission check for object owner"""
        user = Mock()
        user.is_superuser = False
        user.username = "testuser"

        obj = Mock()
        obj.owner = "testuser"

        has_permission = self.auth.has_object_permission(user, obj, "edit")
        self.assertTrue(has_permission)

    def test_has_object_permission_non_owner(self):
        """Test object permission check for non-owner"""
        user = Mock()
        user.is_superuser = False
        user.username = "testuser"

        obj = Mock()
        obj.owner = "someone_else"

        has_permission = self.auth.has_object_permission(user, obj, "edit")
        self.assertFalse(has_permission)

    def test_has_object_permission_no_owner_attribute(self):
        """Test object permission check when object has no owner"""
        user = Mock()
        user.is_superuser = False
        user.username = "testuser"

        obj = Mock()
        # obj has no owner attribute

        has_permission = self.auth.has_object_permission(user, obj, "edit")
        self.assertFalse(has_permission)

    def test_get_user_roles_with_mock_user(self):
        """Test getting user roles with mock user object"""
        user = Mock()
        user.username = "testuser"

        roles = self.auth.get_user_roles(user)
        self.assertEqual(roles, ["content_editor"])

    def test_get_user_roles_with_string_user(self):
        """Test getting user roles with string username"""
        roles = self.auth.get_user_roles("admin")
        self.assertEqual(roles, ["admin"])

    def test_get_user_roles_nonexistent_user(self):
        """Test getting user roles for nonexistent user"""
        roles = self.auth.get_user_roles("nonexistent")
        self.assertEqual(roles, [])


class TestAuthInterfaceDefaultMethods(unittest.TestCase):
    """Test cases for AuthInterface default method implementations"""

    def test_has_object_permission_default_implementation(self):
        """Test that default has_object_permission returns False"""

        class MinimalAuthImpl(AuthInterface):
            def get_current_user_info(self, request):
                return {}

            def check_user_permission(self, user, permission):
                return False

            def get_user_groups(self, user):
                return []

            def authenticate_token(self, token):
                return None

        auth = MinimalAuthImpl()
        user = Mock()
        obj = Mock()

        result = auth.has_object_permission(user, obj, "edit")
        self.assertFalse(result)

    def test_get_user_roles_default_implementation(self):
        """Test that default get_user_roles returns empty list"""

        class MinimalAuthImpl(AuthInterface):
            def get_current_user_info(self, request):
                return {}

            def check_user_permission(self, user, permission):
                return False

            def get_user_groups(self, user):
                return []

            def authenticate_token(self, token):
                return None

        auth = MinimalAuthImpl()
        user = Mock()

        result = auth.get_user_roles(user)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
