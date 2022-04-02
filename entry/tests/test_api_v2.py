from unittest import mock

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue, AttrTypeStr
from entity.models import EntityAttr
from entry.models import Entry
from group.models import Group


class ViewTest(AironeViewTest):
    def test_get_entry(self):
        user = self.guest_login()

        # create Entities, Entries and Group for using this test case
        ref_entity = self.create_entity(user, 'ref_entity')
        ref_entry = self.add_entry(user, 'r-0', ref_entity)
        group = Group.objects.create(name='group0')

        entity = self.create_entity(**{
            'user': user,
            'name': 'test-entity',
            'attrs': self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY,
        })
        entry = self.add_entry(user, 'Entry', entity, values={
            'val': 'hoge',
            'ref': ref_entry.id,
            'name': {'name': 'hoge', 'id': ref_entry.id},
            'bool': False,
            'date': '2018-12-31',
            'group': group.id,
            'groups': [group.id],
            'text': 'fuga',
            'vals': ['foo', 'bar'],
            'refs': [ref_entry.id],
            'names': [
                {'name': 'foo', 'id': ref_entry.id},
                {'name': 'bar', 'id': ref_entry.id}],
        })
        # add an optional attribute after creating entry
        optional_attr = EntityAttr.objects.create(**{
            'name': 'opt',
            'type': AttrTypeValue['string'],
            'is_mandatory': False,
            'parent_entity': entity,
            'created_user': user,
        })
        entity.attrs.add(optional_attr)

        resp = self.client.get('/entry/api/v2/%d' % entry.id)
        self.assertEqual(resp.status_code, 200)

        resp_data = resp.json()
        self.assertEqual(resp_data['id'], entry.id)
        self.assertEqual(resp_data['name'], entry.name)
        self.assertEqual(resp_data['schema'],
                         {'id': entry.schema.id, 'name': entry.schema.name})

        self.assertEqual(next(filter(lambda x: x['schema_name'] == 'val', resp_data['attrs'])), {
            'type': AttrTypeValue['string'],
            'value': 'hoge',
            'id': entry.attrs.get(schema__name='val').id,
            'schema_id': entry.attrs.get(schema__name='val').schema.id,
            'schema_name': 'val',
        })
        self.assertEqual(next(filter(lambda x: x['schema_name'] == 'ref', resp_data['attrs'])), {
            'type': AttrTypeValue['object'],
            'value': {
                'id': ref_entry.id,
                'name': ref_entry.name,
                'schema': {
                    'id': ref_entry.schema.id,
                    'name': ref_entry.schema.name,
                },
            },
            'id': entry.attrs.get(schema__name='ref').id,
            'schema_id': entry.attrs.get(schema__name='ref').schema.id,
            'schema_name': 'ref',
        })
        self.assertEqual(next(filter(lambda x: x['schema_name'] == 'name', resp_data['attrs'])), {
            'type': AttrTypeValue['named_object'],
            'value': {
                'hoge': {
                    'id': ref_entry.id,
                    'name': ref_entry.name,
                    'schema': {
                        'id': ref_entry.schema.id,
                        'name': ref_entry.schema.name,
                    },
                },
            },
            'id': entry.attrs.get(schema__name='name').id,
            'schema_id': entry.attrs.get(schema__name='name').schema.id,
            'schema_name': 'name',
        })
        self.assertEqual(next(filter(lambda x: x['schema_name'] == 'bool', resp_data['attrs'])), {
            'type': AttrTypeValue['boolean'],
            'value': False,
            'id': entry.attrs.get(schema__name='bool').id,
            'schema_id': entry.attrs.get(schema__name='bool').schema.id,
            'schema_name': 'bool',
        })
        self.assertEqual(next(filter(lambda x: x['schema_name'] == 'date', resp_data['attrs'])), {
            'type': AttrTypeValue['date'],
            'value': '2018-12-31',
            'id': entry.attrs.get(schema__name='date').id,
            'schema_id': entry.attrs.get(schema__name='date').schema.id,
            'schema_name': 'date',
        })
        self.assertEqual(next(filter(lambda x: x['schema_name'] == 'group', resp_data['attrs'])), {
            'type': AttrTypeValue['group'],
            'value': {
                'id': group.id,
                'name': group.name,
            },
            'id': entry.attrs.get(schema__name='group').id,
            'schema_id': entry.attrs.get(schema__name='group').schema.id,
            'schema_name': 'group',
        })
        self.assertEqual(next(filter(lambda x: x['schema_name'] == 'groups', resp_data['attrs'])), {
            'type': AttrTypeValue['array_group'],
            'value': [{
                'id': group.id,
                'name': group.name,
            }],
            'id': entry.attrs.get(schema__name='groups').id,
            'schema_id': entry.attrs.get(schema__name='groups').schema.id,
            'schema_name': 'groups',
        })
        self.assertEqual(next(filter(lambda x: x['schema_name'] == 'text', resp_data['attrs'])), {
            'type': AttrTypeValue['text'],
            'value': 'fuga',
            'id': entry.attrs.get(schema__name='text').id,
            'schema_id': entry.attrs.get(schema__name='text').schema.id,
            'schema_name': 'text',
        })
        self.assertEqual(next(filter(lambda x: x['schema_name'] == 'vals', resp_data['attrs'])), {
            'type': AttrTypeValue['array_string'],
            'value': ['foo', 'bar'],
            'id': entry.attrs.get(schema__name='vals').id,
            'schema_id': entry.attrs.get(schema__name='vals').schema.id,
            'schema_name': 'vals',
        })
        self.assertEqual(next(filter(lambda x: x['schema_name'] == 'refs', resp_data['attrs'])), {
            'type': AttrTypeValue['array_object'],
            'value': [{
                'id': ref_entry.id,
                'name': ref_entry.name,
                'schema': {
                    'id': ref_entry.schema.id,
                    'name': ref_entry.schema.name,
                },
            }],
            'id': entry.attrs.get(schema__name='refs').id,
            'schema_id': entry.attrs.get(schema__name='refs').schema.id,
            'schema_name': 'refs',
        })
        self.assertEqual(next(filter(lambda x: x['schema_name'] == 'names', resp_data['attrs'])), {
            'type': AttrTypeValue['array_named_object'],
            'value': [{
                'foo': {
                    'id': ref_entry.id,
                    'name': ref_entry.name,
                    'schema': {
                        'id': ref_entry.schema.id,
                        'name': ref_entry.schema.name,
                    },
                },
            }, {
                'bar': {
                    'id': ref_entry.id,
                    'name': ref_entry.name,
                    'schema': {
                        'id': ref_entry.schema.id,
                        'name': ref_entry.schema.name,
                    },
                },
            }],
            'id': entry.attrs.get(schema__name='names').id,
            'schema_id': entry.attrs.get(schema__name='names').schema.id,
            'schema_name': 'names',
        })
        self.assertEqual(next(filter(lambda x: x['schema_name'] == 'opt', resp_data['attrs'])), {
            'type': AttrTypeValue['string'],
            'value': AttrTypeStr.DEFAULT_VALUE,
            'id': None,
            'schema_id': entity.attrs.get(name='opt').id,
            'schema_name': 'opt',
        })

    def test_get_entry_without_permission(self):
        user = self.guest_login()

        entity = self.create_entity(**{
            'user': user,
            'name': 'test-entity',
            'is_public': False,
        })
        entry = self.add_entry(user, 'test-entry', entity)

        resp = self.client.get('/entry/api/v2/%d' % entry.id)
        self.assertEqual(resp.status_code, 403)

    def test_get_entry_with_invalid_param(self):
        self.guest_login()

        for param in ['hoge', 9999]:
            resp = self.client.get('/entry/api/v2/%s' % param)
            self.assertEqual(resp.status_code, 404)

    def test_get_entries_without_permission(self):
        user = self.guest_login()

        entity = self.create_entity(**{
            'user': user,
            'name': 'test-entity',
            'is_public': False,
        })

        resp = self.client.get('/entry/api/v2/entries/%d' % entity.id)
        self.assertEqual(resp.status_code, 403)

    def test_get_entries_with_invalid_param(self):
        self.guest_login()

        for param in ['hoge', 9999]:
            resp = self.client.get('/entry/api/v2/entries/%s' % param)
            self.assertEqual(resp.status_code, 404)

    @mock.patch('custom_view.is_custom', mock.Mock(return_value=True))
    @mock.patch('custom_view.call_custom')
    def test_get_entry_with_customview(self, mock_call_custom):
        user = self.guest_login()

        entity = self.create_entity(**{
            'user': user,
            'name': 'test-entity',
            'attrs': self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY,
        })
        entry = self.add_entry(user, 'test-entry', entity)

        def side_effect(handler_name, entity_name, entry, entry_attrs):
            self.assertEqual(handler_name, 'get_entry_attr')
            self.assertEqual(entity_name, 'test-entity')
            self.assertEqual(entry.name, 'test-entry')
            self.assertEqual(len(entry_attrs), len(self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY))

            # add attribute
            entry_attrs.append({
                'id': 0,
                'type': AttrTypeValue['string'],
                'value': 'hoge',
                'schema_id': 0,
                'schema_name': 'fuga',
            })

            return entry_attrs

        mock_call_custom.side_effect = side_effect
        resp = self.client.get('/entry/api/v2/%s' % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()['attrs']),
                         len(self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY) + 1)
        self.assertEqual(resp.json()['attrs'][-1], {
            'id': 0,
            'type': AttrTypeValue['string'],
            'value': 'hoge',
            'schema_id': 0,
            'schema_name': 'fuga',
        })

    def test_serach_entry(self):
        user = self.guest_login()

        ref_entity = self.create_entity(user, 'ref_entity')
        ref_entry4 = self.add_entry(user, 'hoge4', ref_entity)
        ref_entry5 = self.add_entry(user, 'hoge5', ref_entity)
        ref_entry6 = self.add_entry(user, 'hoge6', ref_entity)
        ref_entry7 = self.add_entry(user, 'hoge7', ref_entity)

        entity = self.create_entity(**{
            'user': user,
            'name': 'test-entity',
            'attrs': self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
        })
        self.add_entry(user, 'entry1', entity, values={
            'val': 'hoge1',
        })
        self.add_entry(user, 'entry2', entity, values={
            'vals': ['hoge2', 'fuga2'],
        })
        self.add_entry(user, 'entry3', entity, values={
            'text': 'hoge3',
        })
        self.add_entry(user, 'entry4', entity, values={
            'ref': ref_entry4.id,
        })
        self.add_entry(user, 'entry5', entity, values={
            'refs': [ref_entry5.id],
        })
        self.add_entry(user, 'entry6', entity, values={
            'name': {'name': 'index6', 'id': ref_entry6.id},
        })
        self.add_entry(user, 'entry7', entity, values={
            'names': [{'name': 'index7', 'id': ref_entry7.id}]
        })

        # test value attribute
        for x in range(1, 3):
            resp = self.client.get('/entry/api/v2/search?query=hoge%s' % x)
            self.assertEqual(resp.status_code, 200)
            resp_data = resp.json()
            self.assertEqual(len(resp_data), 1)
            entry = Entry.objects.get(name='entry%s' % x)
            self.assertEqual(resp_data[0]['id'], entry.id)
            self.assertEqual(resp_data[0]['name'], entry.name)

        # test object attribute
        for x in range(4, 4):
            resp = self.client.get('/entry/api/v2/search?query=hoge%s' % x)
            self.assertEqual(resp.status_code, 200)
            resp_data = resp.json()
            self.assertEqual(len(resp_data), 2)
            ref_entry = Entry.objects.get(name='hoge%s' % x)
            entry = Entry.objects.get(name='entry%s' % x)
            self.assertEqual(resp_data[0]['id'], ref_entry.id)
            self.assertEqual(resp_data[0]['name'], ref_entry.name)
            self.assertEqual(resp_data[1]['id'], entry.id)
            self.assertEqual(resp_data[1]['name'], entry.name)

        # test named_object attribute
        for x in range(6, 2):
            resp = self.client.get('/entry/api/v2/search?query=index%s' % x)
            self.assertEqual(resp.status_code, 200)
            resp_data = resp.json()
            self.assertEqual(len(resp_data), 1)
            entry = Entry.objects.get(name='entry%s' % x)
            self.assertEqual(resp_data[0]['id'], entry.id)
            self.assertEqual(resp_data[0]['name'], entry.name)

    def test_serach_entry_with_regexp(self):
        user = self.guest_login()

        ref_entity = self.create_entity(user, 'ref_entity')
        ref_entry = self.add_entry(user, 'ref_entry', ref_entity)
        entity = self.create_entity(**{
            'user': user,
            'name': 'test-entity',
            'attrs': self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
        })
        entry = self.add_entry(user, 'entry', entity, values={
            'val': 'hoge',
            'ref': ref_entry.id,
        })

        resp = self.client.get('/entry/api/v2/search?query=Og')
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(len(resp_data), 1)
        self.assertEqual(resp_data[0]['id'], entry.id)
        self.assertEqual(resp_data[0]['name'], entry.name)

        resp = self.client.get('/entry/api/v2/search?query=F_e')
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(len(resp_data), 2)
        self.assertEqual(resp_data[0]['id'], ref_entry.id)
        self.assertEqual(resp_data[0]['name'], ref_entry.name)
        self.assertEqual(resp_data[1]['id'], entry.id)
        self.assertEqual(resp_data[1]['name'], entry.name)

    def test_serach_entry_multi_match(self):
        user = self.guest_login()

        entity = self.create_entity(**{
            'user': user,
            'name': 'test-entity',
            'attrs': self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
        })
        entry = self.add_entry(user, 'hoge', entity, values={
            'val': 'hoge',
        })

        resp = self.client.get('/entry/api/v2/search?query=hoge')
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(len(resp_data), 1)
        self.assertEqual(resp_data[0]['id'], entry.id)
        self.assertEqual(resp_data[0]['name'], entry.name)

    def test_serach_entry_order_by(self):
        user = self.guest_login()

        entity = self.create_entity(**{
            'user': user,
            'name': 'test-entity',
            'attrs': self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
        })
        self.add_entry(user, 'z_hoge', entity)
        self.add_entry(user, 'a_hoge', entity)
        self.add_entry(user, 'a_entry', entity, values={
            'val': 'z_hoge',
        })
        self.add_entry(user, 'z_entry', entity, values={
            'val': 'a_hoge',
        })

        # Entry name match has high priority
        resp = self.client.get('/entry/api/v2/search?query=hoge')
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(len(resp_data), 4)
        for i, entry_name in enumerate(['a_hoge', 'z_hoge', 'a_entry', 'z_entry']):
            entry = Entry.objects.get(name=entry_name)
            self.assertEqual(resp_data[i]['id'], entry.id)
            self.assertEqual(resp_data[i]['name'], entry.name)

    def test_serach_entry_deleted_entry(self):
        user = self.guest_login()

        ref_entity = self.create_entity(user, 'ref_entity')
        ref_entry = self.add_entry(user, 'ref_entry', ref_entity)
        entity = self.create_entity(**{
            'user': user,
            'name': 'test-entity',
            'attrs': self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
        })
        entry1 = self.add_entry(user, 'entry1', entity, values={
            'val': 'hoge1',
            'ref': ref_entry.id,
        })
        entry1.delete()

        self.add_entry(user, 'entry2', entity, values={
            'ref': ref_entry.id,
        })
        ref_entry.delete()

        for query in ['entry1', 'hoge', 'ref_entry']:
            resp = self.client.get('/entry/api/v2/search?query=%s' % query)
            self.assertEqual(resp.status_code, 200)
            resp_data = resp.json()
            self.assertEqual(len(resp_data), 0)

    def test_serach_entry_update_attrv(self):
        user = self.guest_login()

        ref_entity = self.create_entity(user, 'ref_entity')
        ref_entry1 = self.add_entry(user, 'ref_entry1', ref_entity)
        ref_entry2 = self.add_entry(user, 'ref_entry2', ref_entity)
        entity = self.create_entity(**{
            'user': user,
            'name': 'test-entity',
            'attrs': self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
        })
        entry = self.add_entry(user, 'entry', entity, values={
            'val': 'hoge',
            'vals': ['hoge'],
            'ref': ref_entry1.id,
            'refs': [ref_entry1.id],
        })
        entry.attrs.get(name='val').add_value(user, 'fuga')
        entry.attrs.get(name='vals').add_value(user, ['fuga'])
        entry.attrs.get(name='ref').add_value(user, ref_entry2.id)
        entry.attrs.get(name='refs').add_value(user, [ref_entry2.id])

        resp = self.client.get('/entry/api/v2/search?query=hoge')
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(len(resp_data), 0)

        resp = self.client.get('/entry/api/v2/search?query=ref_entry1')
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(len(resp_data), 1)
        self.assertEqual(resp_data[0]['id'], ref_entry1.id)
        self.assertEqual(resp_data[0]['name'], ref_entry1.name)

    def test_get_entries_of_specific_entity(self):
        user = self.guest_login()

        # Create Entities and Entries for using this test-case
        entities = [self.create_entity(user, 'E-%d' % x) for x in range(2)]
        for index in range(3):
            self.add_entry(user, 'e-%d' % index, entities[0])

        # Create an Entry that is related with another Entity "E-1"
        self.add_entry(user, 'spare-entry', entities[1])

        # This expects to return only Entries that is related with Entity "E-0"
        resp = self.client.get('/entry/api/v2/entries/%d' % entities[0].id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(sorted([x['name'] for x in resp.json()['results']]),
                         sorted(['e-0', 'e-1', 'e-2']))
        self.assertTrue(all([sorted(['id', 'name', 'schema']) == sorted(x.keys())
                             for x in resp.json()['results']]))

    def test_get_deleted_entries_of_specific_entity(self):
        user = self.guest_login()

        # Create an Entity and Entry, then delete it
        entity = self.create_entity(user, 'Entity')
        entry = self.add_entry(user, 'deleted-entry', entity)
        entry.delete()

        # Check this respond deleted entry
        resp = self.client.get('/entry/api/v2/entries/%d?is_active=False' % entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()['results']), 1)
        self.assertIn('deleted-entry', resp.json()['results'][0]['name'])

    def test_entry_after_entity_attr_was_deleted(self):
        user = self.guest_login()

        # create Entities, Entries and Group for using this test case
        entity = self.create_entity(**{
            'user': user,
            'name': 'test-entity',
            'attrs': self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
        })
        entry = self.add_entry(user, 'Entry', entity)

        # delete EntityAttr, then check it won't be returned in response
        entity.attrs.get(name='val', is_active=True).delete()

        resp = self.client.get('/entry/api/v2/%d' % entry.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(sorted([attr['schema_name'] for attr in resp.json()['attrs']]),
                         sorted(['ref', 'name', 'bool', 'date', 'group', 'groups', 'text', 'vals',
                                 'refs', 'names']))
