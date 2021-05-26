import json

from airone.lib.test import AironeViewTest
from entity.models import Entity

from unittest import mock
from user.models import User


class ViewTest(AironeViewTest):
    def test_get_entities(self):
        user = self.guest_login()

        entity_info = [
            {'name': 'foo', 'is_public': True},
            {'name': 'bar', 'is_public': False},
        ]
        for info in entity_info:
            Entity.objects.create(name=info['name'], is_public=info['is_public'], created_user=user)

        resp = self.client.get('/entity/api/v1/get_entities')
        self.assertEqual(resp.status_code, 200)

        entities = resp.json()['entities']
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0]['name'], 'foo')

    def test_post_settings_without_permission(self):
        self.guest_login()
        test_user = User.objects.create(username='test-user', is_superuser=False)

        entity = Entity.objects.create(name='test-entity', created_user=test_user, is_public=False)

        resp = self.client.post('/entity/api/v1/settings/%s' % entity.id, json.dumps({
            'webhook_url': 'https://example.com',
            'request_headers': [],
            'is_enabled_webhook': True,
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'),
                         "You don't have permission to access this object")

    def test_post_settings_invalid_url(self):
        user = self.guest_login()
        entity = Entity.objects.create(name='test-entity', created_user=user)

        resp = self.client.post('/entity/api/v1/settings/%s' % entity.id, json.dumps({
            'webhook_url': 'invalid URL',
            'request_headers': [],
            'is_enabled_webhook': True,
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Specified URL is invalid')

    def test_post_settings_invalid_headers(self):
        user = self.guest_login()
        entity = Entity.objects.create(name='test-entity', created_user=user)

        resp = self.client.post('/entity/api/v1/settings/%s' % entity.id, json.dumps({
            'webhook_url': 'https://example.com',
            'request_headers': 'hogefuga',
            'is_enabled_webhook': True,
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

    @mock.patch('entity.api_v1.views.requests')
    def test_post_settings_invalid_endpoint(self, mock_requests):
        user = self.guest_login()
        entity = Entity.objects.create(name='test-entity', created_user=user)

        # Declare requests mock
        mock_resp = mock.Mock()
        mock_resp.ok = False
        mock_resp.text = 'test-failure'
        mock_requests.post.return_value = mock_resp

        resp = self.client.post('/entity/api/v1/settings/%s' % entity.id, json.dumps({
            'webhook_url': 'https://example.com',
            'request_headers': [],
            'is_enabled_webhook': True,
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'),
                         'Failed send message to the endpoint: test-failure')

    @mock.patch('entity.api_v1.views.requests')
    def test_post_settings(self, mock_requests):
        user = self.guest_login()
        entity = Entity.objects.create(name='test-entity', created_user=user)

        # Declare requests mock
        mock_resp = mock.Mock()
        mock_resp.ok = True
        mock_requests.post.return_value = mock_resp

        webhook_headers = [
            {'key': 'X-Auth-Token', 'value': 'API-token'},
            {'key': 'Content-Type', 'value': 'application/json'},
        ]

        resp = self.client.post('/entity/api/v1/settings/%s' % entity.id, json.dumps({
            'webhook_url': 'https://example.com',
            'request_headers': webhook_headers,
            'is_enabled_webhook': True,
        }), 'application/json')
        self.assertEqual(resp.status_code, 200)

        # check webhook configurations are set in the specified entity
        entity.refresh_from_db()
        self.assertTrue(entity.is_enabled_webhook)
        self.assertEqual(entity.webhook_url, 'https://example.com')
        self.assertEqual(json.loads(entity.webhook_headers), {
            'X-Auth-Token': 'API-token',
            'Content-Type': 'application/json',
        })
