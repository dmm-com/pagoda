from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue

from entity.models import Entity, EntityAttr


class APITest(AironeViewTest):
    def test_get_entity_attrs_with_invalid_entity_id(self):
        self.admin_login()

        resp = self.client.get('/api/v1/entity/attrs/9999')
        self.assertEqual(resp.status_code, 400)

    def test_get_entity_attrs(self):
        user = self.admin_login()

        entities = []
        entity_info = {
            'entity1': ['foo', 'bar', 'fuga'],
            'entity2': ['bar', 'hoge', 'fuga']
        }
        for (entity_name, attrnames) in entity_info.items():
            entity = Entity.objects.create(name=entity_name, created_user=user)
            entities.append(entity)

            for attrname in attrnames:
                entity.attrs.add(EntityAttr.objects.create(name=attrname,
                                                           type=AttrTypeValue['string'],
                                                           created_user=user,
                                                           parent_entity=entity))

        resp = self.client.get('/api/v1/entity/attrs/%s' % ','.join([str(x.id) for x in entities]))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(sorted(resp.json()['result']), sorted(['bar', 'fuga']))

        # test to get all EntityAttrs
        resp = self.client.get('/api/v1/entity/attrs/,')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(sorted(resp.json()['result']), sorted(['foo', 'bar', 'hoge', 'fuga']))
