from django.test import TestCase
from webhook.models import Webhook


class ModelTest(TestCase):
    def test_to_dict(self):
        webhook_instance = Webhook.objects.create(**{
            'label': 'test1',
            'url': 'http://example.com/api',
            'is_enabled': True,
            'is_verified': True,
            'headers': json.dumps([
                {'key': 'test-key1', 'value': 'test-value1'},
            ]),
        })
        
        self.assertEqual(webhook_instance.to_dict(), {
            'label': 'test1',
            'url': 'http://example.com/api',
            'is_enabled': True,
            'is_verified': True,
            'headers': [
                {'key': 'test-key1', 'value': 'test-value1'},
            ],
        })
