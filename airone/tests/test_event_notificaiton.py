import json
import mock

from airone.lib.event_notification import notify_entry_create
from airone.lib.event_notification import notify_entry_update
from airone.lib.event_notification import notify_entry_delete
from airone.lib.test import AironeViewTest
from entity.models import Entity
from entry.models import Entry


class EventNotificationTest(AironeViewTest):
    def setUp(self):
        self.user = self.guest_login()
        self.entity = Entity.objects.create(name='test-entity', created_user=self.user)
        self.entry = Entry.objects.create(name='e', schema=self.entity, created_user=self.user)

        self.entity.webhook_url = 'https://example.com'
        self.entity.webhook_headers = json.dumps({'Content-Type': 'application/json'})
        self.entity.save()

        # clear data which is used in individual tests
        self._test_data = {}

    @mock.patch('airone.lib.event_notification.requests')
    def test_notify_entry_create(self, mock_requests):
        def side_effect(url, data, headers, verify):
            self._test_data['is_post_called'] = True
            self.assertEqual(url, 'https://example.com')
            self.assertEqual(headers, {'Content-Type': 'application/json'})
            self.assertEqual(json.loads(data)['event'], 'entry.create')
            self.assertEqual(json.loads(data)['data']['name'], 'e')
            self.assertEqual(json.loads(data)['data']['schema'], 'test-entity')
            self.assertFalse(verify)
            return 'test-response'

        # call notification method and check response
        mock_requests.post.side_effect = side_effect
        resp = notify_entry_create(self.entry, self.user)
        self.assertEqual(resp, 'test-response')
        self.assertTrue(self._test_data['is_post_called'])

    @mock.patch('airone.lib.event_notification.requests')
    def test_notify_entry_update(self, mock_requests):
        def side_effect(url, data, headers, verify):
            self._test_data['is_post_called'] = True
            self.assertEqual(json.loads(data)['event'], 'entry.update')
            return 'test-response'

        # call notification method and check response
        mock_requests.post.side_effect = side_effect
        resp = notify_entry_update(self.entry, self.user)
        self.assertEqual(resp, 'test-response')
        self.assertTrue(self._test_data['is_post_called'])

    @mock.patch('airone.lib.event_notification.requests')
    def test_notify_entry_delete(self, mock_requests):
        def side_effect(url, data, headers, verify):
            self._test_data['is_post_called'] = True
            self.assertEqual(json.loads(data)['event'], 'entry.delete')
            return 'test-response'

        # call notification method and check response
        mock_requests.post.side_effect = side_effect
        resp = notify_entry_delete(self.entry, self.user)
        self.assertEqual(resp, 'test-response')
        self.assertTrue(self._test_data['is_post_called'])
