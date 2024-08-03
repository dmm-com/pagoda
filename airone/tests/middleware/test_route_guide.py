import json

from django.urls import reverse

from airone.lib.test import AironeViewTest, with_airone_settings
from user.models import User


class ViewTest(AironeViewTest):
    @with_airone_settings({"LEGACY_UI_DISABLED": True})
    def test_vail_page_access_when_route_guide_activated(self):
        self.client.login(username="admin", password="admin")

        user = User.objects.create(username="test-user")
        active_user_count = User.objects.filter(is_active=True).count()

        resp = self.client.post(
            reverse("user:do_delete", args=[user.id]),
            json.dumps({}),
            "application/json",
        )

        # This check URLRouteGuider vails /user/do_delete request and
        # never run background processing.
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(User.objects.filter(is_active=True).count(), active_user_count)
