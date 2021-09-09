import json

from airone.lib.test import AironeViewTest
from entity.models import Entity
from webhook.models import Webhook


class APITest(AironeViewTest):
    def test_get_webhooks(self):
        user = self.guest_login()

        # Prepared data strcutreus, witch are used in this test.
        entity = Entity.objects.create(name='test-entity', created_user=user)
        entity.webhooks.add(Webhook.objects.create(**{
            'label': 'test1',
            'url': 'http://example.com/api',
            'is_enabled': True,
            'is_verified': True,
            'headers': json.dumps([
                {'key': 'test-key1', 'value': 'test-value1'},
            ]),
        }))

        resp = self.client.get('/webhook/api/v2/%d' % entity.id)
        print('[onix-test(90)] %s' % resp.content.decode('utf-8'))

        self.assertEqual(resp.status_code, 200)

    def test_get_webhooks_with_invalid_entity_id(self):
        resp = self.client.get('/webhook/api/v2/9999')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {
            'msg': 'There is no entity for setting',
        })
