from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue

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
                         {'type': AttrTypeValue['string'], 'value': 'hoge'})
        self.assertEqual(resp_data['attrs']['ref'],
                         {'type': AttrTypeValue['object'], 'value': {
                             'id': ref_entry.id, 'name': ref_entry.name}})
        self.assertEqual(resp_data['attrs']['name'],
                         {'type': AttrTypeValue['named_object'], 'value': {
                             'hoge': {'id': ref_entry.id, 'name': ref_entry.name}}})
        self.assertEqual(resp_data['attrs']['bool'],
                         {'type': AttrTypeValue['boolean'], 'value': False})
        self.assertEqual(resp_data['attrs']['date'],
                         {'type': AttrTypeValue['date'], 'value': '2018-12-31'})
        self.assertEqual(resp_data['attrs']['group'],
                         {'type': AttrTypeValue['group'], 'value': {
                             'id': group.id, 'name': group.name}})
        self.assertEqual(resp_data['attrs']['groups'],
                         {'type': AttrTypeValue['array_group'], 'value': [{
                             'id': group.id, 'name': group.name}]})
        self.assertEqual(resp_data['attrs']['text'],
                         {'type': AttrTypeValue['text'], 'value': 'fuga'})
        self.assertEqual(resp_data['attrs']['vals'],
                         {'type': AttrTypeValue['array_string'], 'value': ['foo', 'bar']})
        self.assertEqual(resp_data['attrs']['refs'],
                         {'type': AttrTypeValue['array_object'], 'value': [{
                             'id': ref_entry.id, 'name': ref_entry.name}]})
        self.assertEqual(resp_data['attrs']['names'],
                         {'type': AttrTypeValue['array_named_object'], 'value': [
                             {'foo': {'id': ref_entry.id, 'name': ref_entry.name}},
                             {'bar': {'id': ref_entry.id, 'name': ref_entry.name}}
                         ]})
