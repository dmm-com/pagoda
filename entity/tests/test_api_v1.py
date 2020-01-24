from airone.lib.test import AironeViewTest

from django.urls import reverse

from entity.models import Entity


class ViewTest(AironeViewTest):
    def test_get_entities(self):
        user = self.guest_login()

        entity_info = [
            {'name': 'foo', 'is_public': True},
            {'name': 'bar', 'is_public': False},
        ]
        for info in entity_info:
            Entity.objects.create(name=info['name'], is_public=info['is_public'], created_user=user)

        resp = self.client.get(reverse('entity:api_v1:get_entities'))
        self.assertEqual(resp.status_code, 200)

        entities = resp.json()['entities']
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0]['name'], 'foo')
