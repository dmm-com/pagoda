import json
import socket
from unittest import mock

from requests.exceptions import RequestException
from urllib3.exceptions import ReadTimeoutError, SSLError

from airone.lib.event_notification import (
    notify_entry_create,
    notify_entry_delete,
    notify_entry_update,
)
from airone.lib.test import AironeViewTest
from entity import tasks
from entity.models import Entity
from entry.models import Entry
from entry.tasks import _notify_event
from job.models import JobStatus
from webhook.models import Webhook


class WebhookBoundaryTest(AironeViewTest):
    def setUp(self):
        super().setUp()
        self.user = self.guest_login()
        self.entity = self.create_entity(self.user, "webhook-security")
        self.dns = self.enterContext(mock.patch("airone.lib.webhook.socket.getaddrinfo"))
        self.dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 80))
        ]
        # Keep regression tests safe even if any caller bypasses the helper.
        self.connect = self.enterContext(
            mock.patch(
                "urllib3.connection.HTTPConnection._new_conn",
                side_effect=AssertionError("Blocked webhook must not open a connection"),
            )
        )

    def test_v1_registration_and_update_cannot_verify_internal_destinations(self):
        for url in ("http://169.254.169.254/", "https://internal.example.com/"):
            params = {
                "label": "security",
                "webhook_url": url,
                "is_enabled": True,
                "request_headers": [],
            }
            for updating in (False, True):
                with self.subTest(url=url, updating=updating):
                    if updating:
                        webhook = self.entity.webhooks.last()
                        webhook.is_verified = True
                        webhook.save()
                        params["id"] = webhook.id
                    response = self.client.post(
                        f"/webhook/api/v1/set/{self.entity.id}",
                        json.dumps(params),
                        "application/json",
                    )
                    self.assertEqual(response.status_code, 200)
                    webhook = Webhook.objects.get(id=response.json()["webhook_id"])
                    self.assertFalse(webhook.is_verified)
                    self.assertIn("public IP", webhook.verification_error_details)
        self.connect.assert_not_called()

    @mock.patch(
        "entity.tasks.create_entity_v2.delay", mock.Mock(side_effect=tasks.create_entity_v2)
    )
    @mock.patch("entity.tasks.edit_entity_v2.delay", mock.Mock(side_effect=tasks.edit_entity_v2))
    def test_v2_async_create_and_update_cannot_verify_internal_destinations(self):
        params = {"name": "webhook-create", "webhooks": [{"url": "https://internal.example.com/"}]}
        response = self.client.post("/entity/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(response.status_code, 202)
        entity = Entity.objects.get(name="webhook-create")
        webhook = entity.webhooks.get()
        self.assertFalse(webhook.is_verified)
        self.assertIn("public IP", webhook.verification_error_details)
        webhook.is_verified = True
        webhook.save()
        params["webhooks"][0]["id"] = webhook.id
        response = self.client.put(
            f"/entity/api/v2/{entity.id}/", json.dumps(params), "application/json"
        )
        self.assertEqual(response.status_code, 202)
        webhook.refresh_from_db()
        self.assertFalse(webhook.is_verified)
        self.connect.assert_not_called()

    def test_existing_verified_webhooks_are_rechecked_for_every_event_and_fail_the_job(self):
        webhook = Webhook.objects.create(
            url="https://internal.example.com/", is_enabled=True, is_verified=True
        )
        self.entity.webhooks.add(webhook)
        entry = Entry.objects.create(
            name="security-entry", schema=self.entity, created_user=self.user
        )
        for notify in (notify_entry_create, notify_entry_update, notify_entry_delete):
            with self.subTest(notify=notify.__name__):
                with self.assertRaisesRegex(RequestException, "public IP"):
                    notify(entry, self.user)
                result = _notify_event(notify, entry.id, self.user)
                self.assertEqual(result[0], JobStatus.ERROR)
                self.assertIn("public IP", result[1])
        self.connect.assert_not_called()

    def test_v1_tls_and_timeout_failures_are_recorded_as_unverified(self):
        self.dns.return_value[0] = (
            socket.AF_INET,
            socket.SOCK_STREAM,
            6,
            "",
            ("93.184.216.34", 443),
        )
        for error in (
            SSLError("certificate verify failed"),
            ReadTimeoutError(None, "/", "timeout"),
        ):
            with (
                self.subTest(error=error),
                mock.patch("urllib3.connectionpool.HTTPSConnectionPool.urlopen", side_effect=error),
            ):
                response = self.client.post(
                    f"/webhook/api/v1/set/{self.entity.id}",
                    json.dumps(
                        {
                            "label": "security",
                            "webhook_url": "https://example.com/",
                            "is_enabled": True,
                            "request_headers": [],
                        }
                    ),
                    "application/json",
                )
                self.assertEqual(response.status_code, 200)
                webhook = Webhook.objects.get(id=response.json()["webhook_id"])
                self.assertFalse(webhook.is_verified)
                self.assertTrue(webhook.verification_error_details)
        self.connect.assert_not_called()
