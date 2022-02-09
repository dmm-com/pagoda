import json

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeStr, AttrTypeText
from airone.lib.types import AttrTypeArrStr
from airone.lib.types import AttrTypeValue
from django.urls import reverse
from entity import tasks
from entity.models import Entity
from entry.models import Entry
from entry.settings import CONFIG as ENTRY_CONFIG

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

        resp = self.client.get('/entity/api/v2/%s' % entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['name'], 'foo')

    def test_get_entries(self):
        user = self.guest_login()
        entity = Entity.objects.create(name='foo', is_public=True, created_user=user)

        # This creates Entries in the order of e9, e8, e7 ... e1
        entries = {
            'e%d' % i: Entry.objects.create(name='e%d' % i, schema=entity, created_user=user)
            for i in range(9, 0, -1)}

        # Swap and changge configuration to test API returns entries in expected order
        orig_config = ENTRY_CONFIG.conf['MAX_LIST_ENTRIES']
        ENTRY_CONFIG.conf['MAX_LIST_ENTRIES'] = 2

        resp = self.client.get('/entity/api/v2/%d' % entity.id)
        self.assertEqual(resp.status_code, 200)

        # Confirm getting entries are sorted by name and limited by config
        self.assertEqual([e['name'] for e in resp.json()['entries']], ['e1', 'e2'])

        # Check to get unactive entries
        entries['e9'].delete()
        resp = self.client.get('/entity/api/v2/%d?is_active_entry=False' % entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([e['id'] for e in resp.json()['entries']], [entries['e9'].id])

        # retrieve original configuration
        ENTRY_CONFIG.conf['MAX_LIST_ENTRIES'] = orig_config
