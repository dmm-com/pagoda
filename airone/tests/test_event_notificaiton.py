import json

import mock

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

    @mock.patch("airone.lib.event_notification.requests")
    def test_notify_entry_create(self, mock_requests):
        def side_effect(url, data, headers, verify):
            self._test_data["is_post_called"] = True
            self.assertEqual(url, "https://example.com")
            self.assertEqual(headers, {"Content-Type": "application/json"})
            self.assertEqual(json.loads(data)["event"], "entry.create")
            self.assertEqual(json.loads(data)["data"], self.entry.to_dict(self.user))
            self.assertEqual(json.loads(data)["user"], self.user.username)
            self.assertFalse(verify)

        # call notification method and check response
        mock_requests.post.side_effect = side_effect
        notify_entry_create(self.entry, self.user)

        # check side effect is called
        self.assertTrue(self._test_data["is_post_called"])

    @mock.patch("airone.lib.event_notification.requests")
    def test_notify_entry_update(self, mock_requests):
        def side_effect(url, data, headers, verify):
            self._test_data["is_post_called"] = True
            self.assertEqual(json.loads(data)["event"], "entry.update")
            self.assertEqual(json.loads(data)["data"], self.entry.to_dict(self.user))
            self.assertEqual(json.loads(data)["user"], self.user.username)

        # call notification method and check response
        mock_requests.post.side_effect = side_effect
        notify_entry_update(self.entry, self.user)

        # check side effect is called
        self.assertTrue(self._test_data["is_post_called"])

    @mock.patch("airone.lib.event_notification.requests")
    def test_notify_entry_delete(self, mock_requests):
        def side_effect(url, data, headers, verify):
            self._test_data["is_post_called"] = True
            self.assertEqual(json.loads(data)["event"], "entry.delete")
            self.assertEqual(json.loads(data)["data"], self.entry.to_dict(self.user))
            self.assertEqual(json.loads(data)["user"], self.user.username)

        # call notification method and check response
        mock_requests.post.side_effect = side_effect
        notify_entry_delete(self.entry, self.user)

        # check side effect is called
        self.assertTrue(self._test_data["is_post_called"])

    @mock.patch("airone.lib.event_notification.requests")
    def test_notify_event_when_webhook_is_unabled(self, mock_requests):
        def side_effect(url, data, headers, verify):
            self._test_data["is_post_called"] = True

        # disable registred webhook instance
        self.webhook.is_enabled = False
        self.webhook.save()

        # call notification method and check response
        mock_requests.post.side_effect = side_effect
        notify_entry_create(self.entry, self.user)

        # check side effect is not called
        self.assertFalse("is_post_called" in self._test_data)

    @mock.patch("airone.lib.event_notification.requests")
    def test_notify_event_when_webhook_is_unverified(self, mock_requests):
        def side_effect(url, data, headers, verify):
            self._test_data["is_post_called"] = True

        # disable registred webhook instance
        self.webhook.is_verified = False
        self.webhook.save()

        # call notification method and check response
        mock_requests.post.side_effect = side_effect
        notify_entry_create(self.entry, self.user)

        # check side effect is not called
        self.assertFalse("is_post_called" in self._test_data)
