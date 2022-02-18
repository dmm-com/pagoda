from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue

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
            'attrs': self.ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
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

        resp = self.client.get('/entry/api/v2/%d' % entry.id)
        self.assertEqual(resp.status_code, 200)

        resp_data = resp.json()
        self.assertEqual(resp_data['id'], entry.id)
        self.assertEqual(resp_data['name'], entry.name)
        self.assertEqual(resp_data['schema'],
                         {'id': entry.schema.id, 'name': entry.schema.name})

        self.assertEqual(resp_data['attrs']['val'],
                         {'type': AttrTypeValue['string'], 'value': 'hoge',
                          'id': entry.attrs.get(schema__name='val').id,
                          'schema_id': entry.attrs.get(schema__name='val').schema.id})
        self.assertEqual(resp_data['attrs']['ref'],
                         {'type': AttrTypeValue['object'], 'value': {
                             'id': ref_entry.id, 'name': ref_entry.name},
                          'id': entry.attrs.get(schema__name='ref').id,
                          'schema_id': entry.attrs.get(schema__name='ref').schema.id})
        self.assertEqual(resp_data['attrs']['name'],
                         {'type': AttrTypeValue['named_object'], 'value': {
                             'hoge': {'id': ref_entry.id, 'name': ref_entry.name}},
                          'id': entry.attrs.get(schema__name='name').id,
                          'schema_id': entry.attrs.get(schema__name='name').schema.id})
        self.assertEqual(resp_data['attrs']['bool'],
                         {'type': AttrTypeValue['boolean'], 'value': False,
                          'id': entry.attrs.get(schema__name='bool').id,
                          'schema_id': entry.attrs.get(schema__name='bool').schema.id})
        self.assertEqual(resp_data['attrs']['date'],
                         {'type': AttrTypeValue['date'], 'value': '2018-12-31',
                          'id': entry.attrs.get(schema__name='date').id,
                          'schema_id': entry.attrs.get(schema__name='date').schema.id})
        self.assertEqual(resp_data['attrs']['group'],
                         {'type': AttrTypeValue['group'], 'value': {
                             'id': group.id, 'name': group.name},
                          'id': entry.attrs.get(schema__name='group').id,
                          'schema_id': entry.attrs.get(schema__name='group').schema.id})
        self.assertEqual(resp_data['attrs']['groups'],
                         {'type': AttrTypeValue['array_group'], 'value': [{
                             'id': group.id, 'name': group.name}],
                          'id': entry.attrs.get(schema__name='groups').id,
                          'schema_id': entry.attrs.get(schema__name='groups').schema.id})
        self.assertEqual(resp_data['attrs']['text'],
                         {'type': AttrTypeValue['text'], 'value': 'fuga',
                          'id': entry.attrs.get(schema__name='text').id,
                          'schema_id': entry.attrs.get(schema__name='text').schema.id})
        self.assertEqual(resp_data['attrs']['vals'],
                         {'type': AttrTypeValue['array_string'], 'value': ['foo', 'bar'],
                          'id': entry.attrs.get(schema__name='vals').id,
                          'schema_id': entry.attrs.get(schema__name='vals').schema.id})
        self.assertEqual(resp_data['attrs']['refs'],
                         {'type': AttrTypeValue['array_object'], 'value': [{
                             'id': ref_entry.id, 'name': ref_entry.name}],
                          'id': entry.attrs.get(schema__name='refs').id,
                          'schema_id': entry.attrs.get(schema__name='refs').schema.id})
        self.assertEqual(resp_data['attrs']['names'],
                         {'type': AttrTypeValue['array_named_object'], 'value': [
                             {'foo': {'id': ref_entry.id, 'name': ref_entry.name}},
                             {'bar': {'id': ref_entry.id, 'name': ref_entry.name}}],
                          'id': entry.attrs.get(schema__name='names').id,
                          'schema_id': entry.attrs.get(schema__name='names').schema.id})

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
        self.add_entry(user, 'spare-entry', entities[0])

        # This expects to return only Entries that is related with Entity "E-0"
        resp = self.client.get('/entry/api/v2/entries/%d' % entities[0].id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(sorted([x['name'] for x in resp.json()['results']]),
                         sorted(['e-0', 'e-1', 'e-2']))

    def test_get_deleted_entries_of_specific_entity(self):
        user = self.guest_login()

        # Create an Entity and Entry, then delete it
        entity = self.create_entity(user, 'Entity')
        entry = self.add_entry(user, 'deleted-entry', entity)
        entry.delete()

        # Check this respond deleted entry
        resp = self.client.get('/entry/api/v2/entries/%d?is_active=False' % entity.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['count'], 1)
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
        self.assertEqual(sorted(resp.json()['attrs'].keys()),
                         sorted(['ref', 'name', 'bool', 'date', 'group', 'groups', 'text', 'vals',
                                 'refs', 'names']))
