import json

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeStr, AttrTypeText
from airone.lib.types import AttrTypeArrStr
from airone.lib.types import AttrTypeValue
from django.urls import reverse
from entity import tasks
from entity.models import Entity

from unittest import mock


class ViewTest(AironeViewTest):
    @mock.patch('entity.tasks.create_entity.delay', mock.Mock(side_effect=tasks.create_entity))
    def test_history(self):
        self.guest_login()

        params = {
            'name': 'hoge',
            'note': 'fuga',
            'is_toplevel': True,
            'attrs': [
                {'name': 'foo', 'type': str(AttrTypeStr), 'is_delete_in_chain': False,
                 'is_mandatory': True, 'row_index': '1'},
                {'name': 'bar', 'type': str(AttrTypeText), 'is_delete_in_chain': False,
                 'is_mandatory': True, 'row_index': '2'},
                {'name': 'baz', 'type': str(AttrTypeArrStr), 'is_delete_in_chain': False,
                 'is_mandatory': False, 'row_index': '3'},
                {'name': 'attr_bool', 'type': str(AttrTypeValue['boolean']),
                 'is_delete_in_chain': False, 'is_mandatory': False, 'row_index': '4'},
                {'name': 'attr_group', 'type': str(AttrTypeValue['group']),
                 'is_delete_in_chain': False, 'is_mandatory': False, 'row_index': '5'},
                {'name': 'attr_date', 'type': str(AttrTypeValue['date']),
                 'is_delete_in_chain': False, 'is_mandatory': False, 'row_index': '6'},
            ],
        }
        resp = self.client.post(reverse('entity:do_create'),
                                json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)
        entity = Entity.objects.first()

        resp = self.client.get('/entity/api/v2/history/%s' % entity.id)
        self.assertEqual(resp.status_code, 200)

        histories = resp.json()
        self.assertEqual(len(histories), 1)
        self.assertEqual(len(histories[0]['details']), 6)

    def test_get_entity(self):
        user = self.guest_login()

        entity = Entity.objects.create(name='foo', is_public=True, created_user=user)

        resp = self.client.get('/entity/api/v2/entities/%s' % entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['name'], 'foo')

        resp = self.client.get('/entity/api/v2/entities')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['results'][0]['name'], 'foo')

        resp = self.client.get('/entity/api/v2/entities?query=foo')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()['results']), 1)
