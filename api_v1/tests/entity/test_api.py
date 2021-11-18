import re

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue

from django.conf import settings
from entity.models import Entity, EntityAttr


class APITest(AironeViewTest):
    def setUp(self):
        user = self.admin_login()
        entity_info = {
            'test_entity1': ['foo', 'bar', 'fuga'],
            'test_entity2': ['bar', 'hoge', 'fuga']
        }
        for (entity_name, attrnames) in entity_info.items():
            entity = Entity.objects.create(name=entity_name, created_user=user)

            for attrname in attrnames:
                entity.attrs.add(EntityAttr.objects.create(name=attrname,
                                                           type=AttrTypeValue['string'],
                                                           created_user=user,
                                                           parent_entity=entity))

        # swap original configuration not to make a negative influence on other tests
        self._orig_profile_setting = settings.AIRONE['ENABLE_PROFILE']
        settings.AIRONE['ENABLE_PROFILE'] = True

    def tearDown(self):
        # retrieve original configuration
        settings.AIRONE['ENABLE_PROFILE'] = self._orig_profile_setting

    def test_get_entity_attrs_with_invalid_entity_id(self):
        resp = self.client.get('/api/v1/entity/attrs/9999')
        self.assertEqual(resp.status_code, 400)

    def test_get_all_entity_attrs(self):
        with self.assertLogs('airone', level='INFO') as log:
            resp = self.client.get('/api/v1/entity/attrs/,')

            # check output log format is expected
            self.assertEqual(len(log.output), 1)
            self.assertTrue(re.match('.*\(user-id: \d+\) GET /api/v1/entity/attrs/,$',  # noqa: W605
                            log.output[0]))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['result'], sorted(['foo', 'bar', 'hoge', 'fuga']))

    def test_get_partial_entity_attrs(self):
        entities = Entity.objects.filter(name__contains='test_entity')
        resp = self.client.get('/api/v1/entity/attrs/%s' % ','.join([str(x.id) for x in entities]))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['result'], sorted(['bar', 'fuga']))
