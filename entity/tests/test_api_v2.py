from airone.lib.test import AironeViewTest
from entity.models import Entity


class ViewTest(AironeViewTest):
    def test_get_entity(self):
        user = self.guest_login()

        entity = Entity.objects.create(name='foo', is_public=True, created_user=user)

        resp = self.client.get('/entity/api/v2/entities/%s' % entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['name'], 'foo')
