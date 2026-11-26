import json
from unittest import mock

from django.conf import settings
from requests.exceptions import RequestException

from airone.lib.event_notification import (
    notify_entry_create,
    notify_entry_delete,
    notify_entry_update,
)
from airone.lib.test import AironeViewTest
from entity.models import Entity
from entry.models import Entry
from webhook.models import Webhook


class EventNotificationTest(AironeViewTest):
    def setUp(self):
        super(EventNotificationTest, self).setUp()
        self.user = self.guest_login()
        self.entity = Entity.objects.create(name="test-entity", created_user=self.user)
        self.entry = Entry.objects.create(name="e", schema=self.entity, created_user=self.user)

        self.webhook = Webhook.objects.create(
            **{
                "url": "https://example.com",
                "headers": [{"header_key": "Content-Type", "header_value": "application/json"}],
                "is_enabled": True,
                "is_verified": True,
            }
        )

        self.entity.webhooks.add(self.webhook)

        # clear data which is used in individual tests
        self._test_data = {}

    @mock.patch("airone.lib.event_notification.post_webhook")
    def test_delivery_continues_after_a_webhook_fails(self, mock_post_webhook):
        second = Webhook.objects.create(
            url="https://other.example.com", headers=[], is_enabled=True, is_verified=True
        )
        self.entity.webhooks.add(second)
        mock_post_webhook.side_effect = [RequestException("Destination rejected"), None]

        with self.assertRaisesRegex(RequestException, "Destination rejected"):
            notify_entry_create(self.entry, self.user)

        self.assertEqual(
            {call.args[0] for call in mock_post_webhook.call_args_list},
            {self.webhook.url, second.url},
        )

    @mock.patch("airone.lib.event_notification.post_webhook")
    def test_notify_entry_create(self, mock_post_webhook):
        def side_effect(url, *, data, headers):
            self._test_data["is_post_called"] = True
            self.assertEqual(url, "https://example.com")
            self.assertEqual(headers, {"Content-Type": "application/json"})
            self.assertEqual(json.loads(data)["event"], "entry.create")
            self.assertEqual(json.loads(data)["data"], self.entry.to_dict(self.user))
            self.assertEqual(json.loads(data)["user"], self.user.username)

        # call notification method and check response
        mock_post_webhook.side_effect = side_effect
        notify_entry_create(self.entry, self.user)

        # check side effect is called
        self.assertTrue(self._test_data["is_post_called"])

    @mock.patch("airone.lib.event_notification.post_webhook")
    def test_notify_entry_update(self, mock_post_webhook):
        def side_effect(url, *, data, headers):
            self._test_data["is_post_called"] = True
            self.assertEqual(json.loads(data)["event"], "entry.update")
            self.assertEqual(json.loads(data)["data"], self.entry.to_dict(self.user))
            self.assertEqual(json.loads(data)["user"], self.user.username)

        # call notification method and check response
        mock_post_webhook.side_effect = side_effect
        notify_entry_update(self.entry, self.user)

        # check side effect is called
        self.assertTrue(self._test_data["is_post_called"])

    @mock.patch("airone.lib.event_notification.post_webhook")
    def test_notify_entry_delete(self, mock_post_webhook):
        def side_effect(url, *, data, headers):
            self._test_data["is_post_called"] = True
            self.assertEqual(json.loads(data)["event"], "entry.delete")
            self.assertEqual(json.loads(data)["data"], self.entry.to_dict(self.user))
            self.assertEqual(json.loads(data)["user"], self.user.username)

        # call notification method and check response
        mock_post_webhook.side_effect = side_effect
        notify_entry_delete(self.entry, self.user)

        # check side effect is called
        self.assertTrue(self._test_data["is_post_called"])

    @mock.patch("airone.lib.event_notification.post_webhook")
    def test_notify_event_when_webhook_is_unabled(self, mock_post_webhook):
        def side_effect(url, *, data, headers):
            self._test_data["is_post_called"] = True

        # disable registred webhook instance
        self.webhook.is_enabled = False
        self.webhook.save()

        # call notification method and check response
        mock_post_webhook.side_effect = side_effect
        notify_entry_create(self.entry, self.user)

        # check side effect is not called
        self.assertFalse("is_post_called" in self._test_data)

    @mock.patch("airone.lib.event_notification.post_webhook")
    def test_notify_event_when_webhook_is_unverified(self, mock_post_webhook):
        def side_effect(url, *, data, headers):
            self._test_data["is_post_called"] = True

        # disable registred webhook instance
        self.webhook.is_verified = False
        self.webhook.save()

        # call notification method and check response
        mock_post_webhook.side_effect = side_effect
        notify_entry_create(self.entry, self.user)

        # check side effect is not called
        self.assertFalse("is_post_called" in self._test_data)

    @mock.patch("airone.lib.event_notification.post_webhook")
    def test_notify_event_when_webhook_flag_is_disabled(self, mock_post_webhook):
        def side_effect(url, *, data, headers):
            self._test_data["is_post_called"] = True

        # call notification method and check response
        mock_post_webhook.side_effect = side_effect

        try:
            settings.AIRONE_FLAGS = {"WEBHOOK": False}
            notify_entry_create(self.entry, self.user)
        finally:
            settings.AIRONE_FLAGS = {"WEBHOOK": True}

        # check side effect is not called
        self.assertFalse(self._test_data.get("is_post_called", None))
