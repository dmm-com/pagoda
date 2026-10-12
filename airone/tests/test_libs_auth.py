from django.test import SimpleTestCase

from airone.libs.auth import check_user_permission, get_current_user_info, get_user_groups


class LibsAuthNoneUserTest(SimpleTestCase):
    """Regression tests for airone.libs.auth helpers when called with user=None.

    These helpers are exposed to plugins, which may pass in a None user (e.g.
    an unauthenticated request), so they must degrade gracefully instead of
    raising AttributeError.
    """

    def test_get_current_user_info_with_none_returns_anonymous_info(self):
        self.assertEqual(
            get_current_user_info(None),
            {
                "username": "anonymous",
                "is_authenticated": False,
                "is_staff": False,
                "is_superuser": False,
            },
        )

    def test_check_user_permission_with_none_returns_false(self):
        self.assertFalse(check_user_permission(None, "entry.view_entry"))

    def test_get_user_groups_with_none_returns_empty_list(self):
        self.assertEqual(get_user_groups(None), [])
