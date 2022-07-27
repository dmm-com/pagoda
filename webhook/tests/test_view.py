from airone.lib.test import AironeViewTest
from entity.models import Entity
from user.models import User
from webhook.models import Webhook


class ViewTest(AironeViewTest):
    def test_list_webhooks(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="test-entity", created_user=user)
        webhook = Webhook.objects.create(url="https://example.com")
        entity.webhooks.add(webhook)

        resp = self.client.get("/webhook/%s" % entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["entity"], entity)
        self.assertEqual(list(resp.context["webhooks"]), [webhook])

    def test_list_webhooks_without_permission(self):
        self.guest_login()
        test_user = User.objects.create(username="test-user", is_superuser=False)
        entity = Entity.objects.create(name="test-entity", created_user=test_user, is_public=False)

        resp = self.client.get("/webhook/%s" % entity.id)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.content.decode("utf-8"),
            "You don't have permission to access this object",
        )
