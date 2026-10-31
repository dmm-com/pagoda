import json
from unittest import mock

from requests.exceptions import ConnectionError

from airone.lib.test import AironeViewTest
from entity.models import Entity
from webhook.models import Webhook


class APITest(AironeViewTest):
    @mock.patch("webhook.api_v1.views.requests")
    def test_create_invalid_endpoint_webhook(self, mock_requests):
        user = self.guest_login()
        entity = Entity.objects.create(name="test-entity", created_user=user)

        # Declare requests mock that responds HTTP 400(ERROR)
        mock_resp = mock.Mock()
        mock_resp.ok = False
        mock_resp.reason = "test-failure"
        mock_resp.text = "test-failure"
        mock_requests.post.return_value = mock_resp

        resp = self.client.post(
            "/webhook/api/v1/set/%s" % entity.id,
            json.dumps(
                {
                    "webhook_url": "https://example.com",
                    "label": "test endpoint",
                    "request_headers": [
                        {"header_key": "content-type", "header_value": "application/json"}
                    ],
                    "is_enabled": True,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["msg"], "Succeded in registering Webhook")

        webhook = Webhook.objects.get(id=resp.json()["webhook_id"])
        self.assertEqual(webhook.url, "https://example.com")
        self.assertEqual(webhook.label, "test endpoint")
        self.assertEqual(
            webhook.headers, [{"header_key": "content-type", "header_value": "application/json"}]
        )
        self.assertTrue(webhook.is_enabled)
        self.assertFalse(webhook.is_verified)

    @mock.patch("webhook.api_v1.views.requests")
    def test_create_valid_endpoint_webhook(self, mock_requests):
        user = self.guest_login()
        entity = Entity.objects.create(name="test-entity", created_user=user)

        # Declare requests mock that responds HTTP 200(Success)
        mock_resp = mock.Mock()
        mock_resp.ok = True
        mock_resp.text = "test-failure"
        mock_requests.post.return_value = mock_resp

        resp = self.client.post(
            "/webhook/api/v1/set/%s" % entity.id,
            json.dumps(
                {
                    "webhook_url": "https://example.com",
                    "label": "test endpoint",
                    "request_headers": [
                        {"header_key": "content-type", "header_value": "application/json"}
                    ],
                    "is_enabled": True,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["msg"], "Succeded in registering Webhook")

        webhook = Webhook.objects.get(id=resp.json()["webhook_id"])
        self.assertEqual(webhook.url, "https://example.com")
        self.assertEqual(webhook.label, "test endpoint")
        self.assertEqual(
            webhook.headers, [{"header_key": "content-type", "header_value": "application/json"}]
        )
        self.assertTrue(webhook.is_enabled)
        self.assertTrue(webhook.is_verified)

    @mock.patch("webhook.api_v1.views.requests")
    def test_edit_invalid_webhook(self, mock_requests):
        user = self.guest_login()
        entity = Entity.objects.create(name="test-entity", created_user=user)

        # Declare requests mock that responds HTTP 200(Success)
        mock_resp = mock.Mock()
        mock_resp.ok = True
        mock_resp.text = "test-failure"
        mock_requests.post.return_value = mock_resp

        resp = self.client.post(
            "/webhook/api/v1/set/%s" % entity.id,
            json.dumps(
                {
                    "id": 999999,  # invlaid webhook id
                    "webhook_url": "https://example.com",
                    "label": "test endpoint",
                    "request_headers": [
                        {"header_key": "content-type", "header_value": "application/json"}
                    ],
                    "is_enabled": True,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode("utf-8"), "Invalid Webhook ID is specified")

    @mock.patch("webhook.api_v1.views.requests")
    def test_edit_unreachable_webhook(self, mock_requests):
        user = self.guest_login()
        entity = Entity.objects.create(name="test-entity", created_user=user)

        mock_requests.post.side_effect = ConnectionError()

        resp = self.client.post(
            "/webhook/api/v1/set/%s" % entity.id,
            json.dumps(
                {
                    "webhook_url": "https://example.com",
                    "label": "test endpoint",
                    "request_headers": [
                        {"header_key": "content-type", "header_value": "application/json"}
                    ],
                    "is_enabled": True,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        webhook = Webhook.objects.get(id=resp.json()["webhook_id"])
        self.assertFalse(webhook.is_verified)

    @mock.patch("webhook.api_v1.views.requests")
    def test_edit_webhook_instance(self, mock_requests):
        user = self.guest_login()
        entity = Entity.objects.create(name="test-entity", created_user=user)
        webhook = Webhook.objects.create(
            **{
                "url": "https://example.com",
                "label": "initial-label",
            }
        )
        # a webhook that is editable through this entity has to belong to it
        entity.webhooks.add(webhook)

        # Declare requests mock that responds HTTP 200(Success)
        mock_resp = mock.Mock()
        mock_resp.ok = True
        mock_resp.text = "test-failure"
        mock_requests.post.return_value = mock_resp

        resp = self.client.post(
            "/webhook/api/v1/set/%s" % entity.id,
            json.dumps(
                {
                    "id": webhook.id,
                    "webhook_url": "https://changed-example.com",
                    "label": "changed-label",
                    "request_headers": [
                        {"header_key": "content-type", "header_value": "application/json"}
                    ],
                    "is_enabled": True,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        webhook.refresh_from_db()
        self.assertEqual(webhook.id, resp.json()["webhook_id"])
        self.assertEqual(webhook.url, "https://changed-example.com")
        self.assertEqual(webhook.label, "changed-label")
        self.assertEqual(
            webhook.headers, [{"header_key": "content-type", "header_value": "application/json"}]
        )
        self.assertTrue(webhook.is_enabled)
        self.assertTrue(webhook.is_verified)

    def test_delete_webhook_instance(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="test-entity", created_user=user)
        webhook = Webhook.objects.create(**{"url": "https://example.com"})
        entity.webhooks.add(webhook)

        resp = self.client.delete("/webhook/api/v1/del/%s" % webhook.id)
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(Webhook.objects.filter(id=webhook.id).first(), None)

    def test_delete_webhook_instance_without_login(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="test-entity", created_user=user)
        webhook = Webhook.objects.create(**{"url": "https://example.com"})
        entity.webhooks.add(webhook)

        self.client.logout()
        resp = self.client.delete("/webhook/api/v1/del/%s" % webhook.id)
        self.assertEqual(resp.status_code, 401)

        self.assertIsNotNone(Webhook.objects.filter(id=webhook.id).first())

    def test_delete_webhook_instance_with_invalid_method(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="test-entity", created_user=user)
        webhook = Webhook.objects.create(**{"url": "https://example.com"})
        entity.webhooks.add(webhook)

        resp = self.client.get("/webhook/api/v1/del/%s" % webhook.id)
        self.assertEqual(resp.status_code, 400)

        self.assertIsNotNone(Webhook.objects.filter(id=webhook.id).first())

    def test_delete_webhook_instance_without_permission(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="test-entity", created_user=user)
        entity.is_public = False
        entity.save()
        webhook = Webhook.objects.create(**{"url": "https://example.com"})
        entity.webhooks.add(webhook)

        resp = self.client.delete("/webhook/api/v1/del/%s" % webhook.id)
        self.assertEqual(resp.status_code, 403)

        self.assertIsNotNone(Webhook.objects.filter(id=webhook.id).first())

    @mock.patch("webhook.api_v1.views.requests")
    def test_cannot_update_webhook_of_another_entity(self, mock_requests):
        user = self.guest_login()
        own_entity = Entity.objects.create(name="own-entity", created_user=user)

        victim_entity = Entity.objects.create(name="victim-entity", created_user=user)
        victim_webhook = Webhook.objects.create(**{"url": "https://victim.example.com"})
        victim_entity.webhooks.add(victim_webhook)

        resp = self.client.post(
            "/webhook/api/v1/set/%s" % own_entity.id,
            json.dumps(
                {
                    "id": victim_webhook.id,
                    "webhook_url": "https://attacker.example.com",
                    "label": "hijacked",
                    "request_headers": [],
                    "is_enabled": True,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode("utf-8"), "Invalid Webhook ID is specified")

        victim_webhook.refresh_from_db()
        self.assertEqual(victim_webhook.url, "https://victim.example.com")
        self.assertFalse(own_entity.webhooks.filter(id=victim_webhook.id).exists())
        mock_requests.post.assert_not_called()

    @mock.patch("webhook.api_v1.views.requests")
    def test_edit_webhook_with_non_integer_id(self, mock_requests):
        user = self.guest_login()
        entity = Entity.objects.create(name="test-entity", created_user=user)

        resp = self.client.post(
            "/webhook/api/v1/set/%s" % entity.id,
            json.dumps(
                {
                    "id": "invalid-id",
                    "webhook_url": "https://example.com",
                    "label": "test endpoint",
                    "request_headers": [],
                    "is_enabled": True,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode("utf-8"), "Invalid Webhook ID is specified")
        mock_requests.post.assert_not_called()

    @mock.patch("webhook.api_v1.views.requests")
    def test_cannot_modify_shared_webhook_without_permission_on_all_entities(self, mock_requests):
        user = self.guest_login()
        own_entity = Entity.objects.create(name="own-entity", created_user=user)

        # another entity that registers the same webhook but is not readable
        private_entity = Entity.objects.create(name="private-entity", created_user=user)
        private_entity.is_public = False
        private_entity.save()

        webhook = Webhook.objects.create(**{"url": "https://example.com"})
        own_entity.webhooks.add(webhook)
        private_entity.webhooks.add(webhook)

        # updating the shared webhook would also affect the private entity
        resp = self.client.post(
            "/webhook/api/v1/set/%s" % own_entity.id,
            json.dumps(
                {
                    "id": webhook.id,
                    "webhook_url": "https://changed-example.com",
                    "label": "changed-label",
                    "request_headers": [],
                    "is_enabled": True,
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 403)
        mock_requests.post.assert_not_called()

        webhook.refresh_from_db()
        self.assertEqual(webhook.url, "https://example.com")

        # deleting it would remove the webhook from the private entity as well
        resp = self.client.delete("/webhook/api/v1/del/%s" % webhook.id)
        self.assertEqual(resp.status_code, 403)
        self.assertIsNotNone(Webhook.objects.filter(id=webhook.id).first())
