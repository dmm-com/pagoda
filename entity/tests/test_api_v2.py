import datetime
import json

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeStr, AttrTypeText
from airone.lib.types import AttrTypeArrStr
from airone.lib.types import AttrTypeValue
from django.urls import reverse
from entity import tasks
from entity.models import Entity

from unittest import mock
from entry.models import Entry
from group.models import Group
from user.models import User


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        self.user: User = self.guest_login()

        # create Entities, Entries and Group for using this test case
        self.ref_entity: Entity = self.create_entity(self.user, 'ref_entity')
        self.ref_entry: Entry = self.add_entry(self.user, 'r-0', self.ref_entity)
        self.group: Group = Group.objects.create(name='group0')

        self.entity: Entity = self.create_entity(**{
            'user': self.user,
            'name': 'test-entity',
            'attrs': self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY,
        })

    def test_list_entry(self):
        entries = []
        for index in range(2):
            entries.append(self.add_entry(self.user, 'e-%d' % index, self.entity))

        resp = self.client.get('/entity/api/v2/%d/entries/' % self.entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['results'], [{
            'id': entries[0].id,
            'name': 'e-0',
            'schema': {
                'id': self.entity.id,
                'name': 'test-entity'
            },
            'is_active': True,
        }, {
            'id': entries[1].id,
            'name': 'e-1',
            'schema': {
                'id': self.entity.id,
                'name': 'test-entity'
            },
            'is_active': True,
        }])

    def test_list_entry_with_param_is_active(self):
        entries = []
        for index in range(2):
            entries.append(self.add_entry(self.user, 'e-%d' % index, self.entity))

        entries[0].delete()

        resp = self.client.get('/entity/api/v2/%d/entries/?is_active=true' % self.entity.id)
        self.assertEqual(resp.json()['count'], 1)
        self.assertEqual(resp.json()['results'][0]['name'], 'e-1')

        resp = self.client.get('/entity/api/v2/%d/entries/?is_active=false' % self.entity.id)
        self.assertEqual(resp.json()['count'], 1)
        self.assertRegex(resp.json()['results'][0]['name'], 'e-0')

    def test_list_entry_with_param_serach(self):
        for index in range(2):
            self.add_entry(self.user, 'e-%d' % index, self.entity)

        resp = self.client.get('/entity/api/v2/%d/entries/?search=-0' % self.entity.id)
        self.assertEqual(resp.json()['count'], 1)
        self.assertEqual(resp.json()['results'][0]['name'], 'e-0')

    def test_list_entry_with_ordering(self):
        self.add_entry(self.user, 'e-2', self.entity)
        self.add_entry(self.user, 'e-3', self.entity)
        self.add_entry(self.user, 'e-1', self.entity)

        resp = self.client.get('/entity/api/v2/%d/entries/?' % self.entity.id)
        self.assertEqual([x['name'] for x in resp.json()['results']], ['e-2', 'e-3', 'e-1'])

        resp = self.client.get('/entity/api/v2/%d/entries/?ordering=name' % self.entity.id)
        self.assertEqual([x['name'] for x in resp.json()['results']], ['e-1', 'e-2', 'e-3'])

        resp = self.client.get('/entity/api/v2/%d/entries/?ordering=-name' % self.entity.id)
        self.assertEqual([x['name'] for x in resp.json()['results']], ['e-3', 'e-2', 'e-1'])

    def test_list_entry_without_permission(self):
        self.entity.is_public = False
        self.entity.save()

        resp = self.client.get('/entity/api/v2/%d/entries/' % self.entity.id)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json(), {
            'detail': 'You do not have permission to perform this action.'
        })

        self.user.permissions.add(self.entity.readable)
        resp = self.client.get('/entity/api/v2/%d/entries/' % self.entity.id)
        self.assertEqual(resp.status_code, 200)

    def test_list_entry_with_invalid_param(self):
        resp = self.client.get('/entity/api/v2/%s/entries/' % 'hoge')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/entity/api/v2/%s/entries/' % 9999)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json(), {'detail': 'Not found.'})

    def test_create_entry(self):
        attr = {}
        for attr_name in [x['name'] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)

        params = {
            'name': 'entry1',
            'attrs': [
                {'id': attr['val'].id, 'value': 'hoge'},
                {'id': attr['vals'].id, 'value': ['hoge', 'fuga']},
                {'id': attr['ref'].id, 'value': self.ref_entry.id},
                {'id': attr['refs'].id, 'value': [self.ref_entry.id]},
                {'id': attr['name'].id, 'value': {'name': 'hoge', 'id': self.ref_entry.id}},
                {'id': attr['names'].id, 'value': [{'name': 'hoge', 'id': self.ref_entry.id}]},
                {'id': attr['group'].id, 'value': self.group.id},
                {'id': attr['groups'].id, 'value': [self.group.id]},
                {'id': attr['text'].id, 'value': 'hoge\nfuga'},
                {'id': attr['bool'].id, 'value': True},
                {'id': attr['date'].id, 'value': '2018-12-31'},
            ],
        }
        resp = self.client.post(
            '/entity/api/v2/%s/entries/' % self.entity.id, json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 201)

        entry: Entry = Entry.objects.get(id=resp.json()['id'], is_active=True)
        self.assertEqual(resp.json(), {
            'id': entry.id,
            'name': 'entry1',
        })
        self.assertEqual(entry.schema, self.entity)
        self.assertEqual(entry.created_user, self.user)
        self.assertEqual(entry.status, 0)
        self.assertEqual({
            attrv.parent_attr.name: attrv.get_value() for attrv in
            [attr.get_latest_value() for attr in entry.attrs.all()]
        }, {
            'bool': True,
            'date': datetime.date(2018, 12, 31),
            'group': 'group0',
            'groups': ['group0'],
            'name': {'hoge': 'r-0'},
            'names': [{'hoge': 'r-0'}],
            'ref': 'r-0',
            'refs': ['r-0'],
            'text': 'hoge\nfuga',
            'val': 'hoge',
            'vals': ['hoge', 'fuga']
        })
        search_result = self._es.search(body={'query': {'term': {'name': entry.name}}})
        self.assertEqual(search_result['hits']['total'], 1)

    def test_create_entry_without_permission_entity(self):
        params = {
            'name': 'entry1',
        }

        # permission nothing
        self.entity.is_public = False
        self.entity.save()
        resp = self.client.post(
            '/entity/api/v2/%s/entries/' % self.entity.id, json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json(),
                         {'detail': 'You do not have permission to perform this action.'})

        # permission readable
        self.user.permissions.add(self.entity.readable)
        resp = self.client.post(
            '/entity/api/v2/%s/entries/' % self.entity.id, json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json(),
                         {'detail': 'You do not have permission to perform this action.'})

        # permission writable
        self.user.permissions.add(self.entity.writable)
        resp = self.client.post(
            '/entity/api/v2/%s/entries/' % self.entity.id, json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 201)

    def test_create_entry_without_permission_entity_attr(self):
        attr = {}
        for attr_name in [x['name'] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)

        params = {
            'attrs': [
                {'id': attr['val'].id, 'value': 'hoge'},
                {'id': attr['vals'].id, 'value': ['hoge']},
            ]
        }

        attr['vals'].is_public = False
        attr['vals'].save()
        resp = self.client.post(
            '/entity/api/v2/%s/entries/' % self.entity.id,
            json.dumps({**params, 'name': 'entry1'}), 'application/json')
        self.assertEqual(resp.status_code, 201)

        entry: Entry = Entry.objects.get(id=resp.json()['id'], is_active=True)
        self.assertEqual(entry.attrs.get(schema=attr['val']).get_latest_value().get_value(), 'hoge')
        self.assertEqual(entry.attrs.get(schema=attr['vals']).get_latest_value().get_value(), [])

        attr['vals'].is_mandatory = True
        attr['vals'].save()
        resp = self.client.post(
            '/entity/api/v2/%s/entries/' % self.entity.id,
            json.dumps({**params, 'name': 'entry2'}), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {
            'non_field_errors': ['mandatory attrs id(%s) is permission denied' % attr['vals'].id]
        })

    def test_create_entry_with_invalid_param_entity_id(self):
        resp = self.client.post('/entity/api/v2/%s/entries/' % 'hoge',
                                json.dumps({'name': 'entry1'}), 'application/json')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.post('/entity/api/v2/%s/entries/' % 9999,
                                json.dumps({'name': 'entry1'}), 'application/json')
        self.assertEqual(resp.json(), {'schema': ['Invalid pk "9999" - object does not exist.']})

    def test_create_entry_with_invalid_param_name(self):
        resp = self.client.post(
            '/entity/api/v2/%s/entries/' % self.entity.id,
            json.dumps({'name': 'a' * (Entry._meta.get_field('name').max_length + 1)}),
            'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(),
                         {'name': ['Ensure this field has no more than 200 characters.']})

        resp = self.client.post(
            '/entity/api/v2/%s/entries/' % self.entity.id,
            json.dumps({'name': 'a' * (Entry._meta.get_field('name').max_length)}),
            'application/json')
        self.assertEqual(resp.status_code, 201)

        entry = self.add_entry(self.user, 'hoge', self.entity)
        resp = self.client.post('/entity/api/v2/%s/entries/' % self.entity.id,
                                json.dumps({'name': 'hoge'}), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(),
                         {'non_field_errors': ['specified name(hoge) already exists']})

        entry.delete()
        resp = self.client.post('/entity/api/v2/%s/entries/' % self.entity.id,
                                json.dumps({'name': 'hoge'}), 'application/json')
        self.assertEqual(resp.status_code, 201)

    def test_create_entry_with_invalid_param_attrs(self):
        attr = {}
        for attr_name in [x['name'] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)

        test_values = [{
            'input': 'hoge',
            'error_msg': {'attrs': ['Expected a list of items but got type "str".']}
        }, {
            'input': ['hoge'],
            'error_msg': {'attrs': {'0': {
                'non_field_errors': ['Invalid data. Expected a dictionary, but got str.']
            }}}
        }, {
            'input': [{'attr1': 'hoge'}],
            'error_msg': {'attrs': {'0': {
                'id': ['This field is required.'],
                'value': ['This field is required.'],
            }}}
        }, {
            'input': [{
                'id': 'hoge',
                'value': 'hoge',
            }],
            'error_msg': {'attrs': {'0': {
                'id': ['A valid integer is required.']
            }}}
        }, {
            'input': [{
                'id': 9999,
                'value': 'hoge',
            }],
            'error_msg': {'non_field_errors': ['attrs id(9999) does not exist']}
        }, {
            'input': [{
                'id': attr['ref'].id,
                'value': 'hoge',
            }],
            'error_msg': {
                'non_field_errors': ['attrs id(%s) - value(hoge) is not int' % attr['ref'].id]
            }
        }]

        for test_value in test_values:
            params = {
                'name': 'entry1',
                'attrs': test_value['input']
            }
            resp = self.client.post('/entity/api/v2/%s/entries/' % self.entity.id,
                                    json.dumps(params), 'application/json')
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.json(), test_value['error_msg'])

        params = {
            'name': 'entry1',
            'attrs': []
        }

        attr['val'].is_mandatory = True
        attr['val'].save()

        resp = self.client.post(
            '/entity/api/v2/%s/entries/' % self.entity.id, json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {
            'non_field_errors': ['mandatory attrs id(%s) is not specified' % attr['val'].id]
        })

        attr['val'].is_public = False
        attr['val'].save()

        resp = self.client.post(
            '/entity/api/v2/%s/entries/' % self.entity.id, json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {
            'non_field_errors': ['mandatory attrs id(%s) is permission denied' % attr['val'].id]
        })

        attr['val'].delete()
        resp = self.client.post(
            '/entity/api/v2/%s/entries/' % self.entity.id, json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 201)

    @mock.patch('entry.tasks.notify_create_entry.delay')
    def test_create_entry_notify(self, mock_task):
        self.client.post('/entity/api/v2/%s/entries/' % self.entity.id,
                         json.dumps({'name': 'hoge'}), 'application/json')

        self.assertTrue(mock_task.called)

    @mock.patch('custom_view.is_custom', mock.Mock(return_value=True))
    @mock.patch('custom_view.call_custom')
    def test_create_entry_with_customview(self, mock_call_custom):
        def side_effect(handler_name, entity_name, user, *args):
            # Check specified parameters are expected
            self.assertEqual(entity_name, self.entity.name)
            self.assertEqual(user, self.user)

            if handler_name == 'before_create_entry':
                self.assertEqual(args[0], {**params, 'schema': self.entity})

            if handler_name == 'after_create_entry':
                entry = Entry.objects.get(name='hoge', is_active=True)
                self.assertEqual(args[0], params['attrs'])
                self.assertEqual(args[1], entry)

        mock_call_custom.side_effect = side_effect

        attr = {}
        for attr_name in [x['name'] for x in self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY]:
            attr[attr_name] = self.entity.attrs.get(name=attr_name)
        params = {
            'name': 'hoge',
            'attrs': [
                {'id': attr['val'].id, 'value': 'fuga'},
            ]
        }
        self.client.post(
            '/entity/api/v2/%s/entries/' % self.entity.id, json.dumps(params), 'application/json')

        self.assertTrue(mock_call_custom.called)

    @mock.patch('entity.tasks.create_entity.delay', mock.Mock(side_effect=tasks.create_entity))
    def test_history(self):
        params = {
            "name": "hoge",
            "note": "fuga",
            "is_toplevel": True,
            "attrs": [
                {
                    "name": "foo",
                    "type": str(AttrTypeStr),
                    "is_delete_in_chain": False,
                    "is_mandatory": True,
                    "row_index": "1",
                },
                {
                    "name": "bar",
                    "type": str(AttrTypeText),
                    "is_delete_in_chain": False,
                    "is_mandatory": True,
                    "row_index": "2",
                },
                {
                    "name": "baz",
                    "type": str(AttrTypeArrStr),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "3",
                },
                {
                    "name": "attr_bool",
                    "type": str(AttrTypeValue["boolean"]),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "4",
                },
                {
                    "name": "attr_group",
                    "type": str(AttrTypeValue["group"]),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "5",
                },
                {
                    "name": "attr_date",
                    "type": str(AttrTypeValue["date"]),
                    "is_delete_in_chain": False,
                    "is_mandatory": False,
                    "row_index": "6",
                },
            ],
        }
        resp = self.client.post(reverse("entity:do_create"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        entity = Entity.objects.filter(name='hoge', is_active=True).first()

        resp = self.client.get("/entity/api/v2/history/%s" % entity.id)
        self.assertEqual(resp.status_code, 200)

        histories = resp.json()
        self.assertEqual(len(histories), 1)
        self.assertEqual(len(histories[0]["details"]), 6)

    def test_get_entity(self):
        resp = self.client.get('/entity/api/v2/entities/%s' % self.entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['name'], 'test-entity')
