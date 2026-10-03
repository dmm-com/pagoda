"""
Tests for API permission classes.

Tests the permission classes defined in the pagoda_plugin_sdk.api.permissions module,
focused on the authentication check performed via the shared _is_authenticated helper.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

# Add the SDK directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk"))

# rest_framework touches Django settings as a side effect of import (even just
# for permission classes, via the pagoda_plugin_sdk.api package's __init__),
# so minimally configure Django here for this standalone (non-Django-managed)
# test run, mirroring the guard used in tests/test_api_base.py.
import django
from django.conf import settings

if not settings.configured:
    settings.configure(REST_FRAMEWORK={})
    django.setup()

from pagoda_plugin_sdk.api.permissions import IsPluginAuthenticated


class TestIsPluginAuthenticated(unittest.TestCase):
    """Test cases for IsPluginAuthenticated.has_permission"""

    def setUp(self):
        self.permission = IsPluginAuthenticated()
        self.view = Mock()

    def test_has_permission_false_when_user_is_none(self):
        """request.user is None must be treated as not authenticated"""
        request = Mock()
        request.user = None

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_has_permission_false_when_not_authenticated(self):
        """request.user.is_authenticated=False must deny permission"""
        request = Mock()
        request.user = Mock(is_authenticated=False, is_active=True)

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_has_permission_true_when_authenticated_and_active(self):
        """An authenticated, active user is granted permission"""
        request = Mock()
        request.user = Mock(is_authenticated=True, is_active=True)

        self.assertTrue(self.permission.has_permission(request, self.view))

    def test_has_permission_false_when_authenticated_but_inactive(self):
        """An authenticated but inactive user is denied permission"""
        request = Mock()
        request.user = Mock(is_authenticated=True, is_active=False)

        self.assertFalse(self.permission.has_permission(request, self.view))


if __name__ == "__main__":
    unittest.main()
