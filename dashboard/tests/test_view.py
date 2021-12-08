import mock
import json
import yaml
import errno

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeStr, AttrTypeObj, AttrTypeText
from airone.lib.types import AttrTypeArrStr, AttrTypeArrObj
from airone.lib.types import AttrTypeNamedObj, AttrTypeArrNamedObj
from airone.lib.types import AttrTypeValue
from django.urls import reverse
from django.contrib.auth.models import User as DjangoUser
from group.models import Group
from job.models import Job, JobOperation
from datetime import date

from entity.models import Entity, EntityAttr
from entry.models import Entry, Attribute, AttributeValue
from entry import tasks as entry_tasks
from dashboard import tasks as dashboard_tasks

from unittest.mock import patch
from unittest.mock import Mock

from dashboard.settings import CONFIG


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        self.admin = self.admin_login()

        # preparing test Entity/Entry objects
        fp = self.open_fixture_file('entry.yaml')
        self.client.post(reverse('dashboard:do_import'), {'file': fp})

    def test_search_without_query(self):
        resp = self.client.get(reverse('dashboard:search'))
        self.assertEqual(resp.status_code, 400)

    def test_search_entity_and_entry(self):
        query = 'ent'

        resp = self.client.get(reverse('dashboard:search'), {'query': query})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['entries']), 7)

    def test_search_with_big_query(self):
        resp = self.client.get(reverse('dashboard:search'),
                               {'query': 'A' * (CONFIG.MAX_QUERY_SIZE + 1)})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'Sending parameter is too large')

        # check boundary value
        resp = self.client.get(reverse('dashboard:search'), {'query': 'A' * CONFIG.MAX_QUERY_SIZE})
        self.assertEqual(resp.status_code, 200)

        # When multibyte characters were sent, check the length of byte number
        resp = self.client.get(reverse('dashboard:search'), {'query': 'あ' * CONFIG.MAX_QUERY_SIZE})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'Sending parameter is too large')

        # check boundary value with multibyte characters
        resp = self.client.get(
            reverse('dashboard:search'),
            {'query': 'あ' * int(CONFIG.MAX_QUERY_SIZE / len('あ'.encode('utf-8')))})
        self.assertEqual(resp.status_code, 200)

    def test_search_entry_only_redirect(self):
        query = 'srv001'
        entry = Entry.objects.get(name=query, is_active=True)

        resp = self.client.get(reverse('dashboard:search'), {'query': query})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/entry/show/%s/' % entry.id)

    def test_search_entry_from_value(self):
        entry = Entry.objects.get(name='srv001', is_active=True)

        resp = self.client.get(reverse('dashboard:search'), {'query': 'hoge'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/entry/show/%s/' % entry.id)

    def test_search_invalid_objects(self):
        resp = self.client.get(reverse('dashboard:search'), {'query': 'hogefuga'})
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(len(resp.context['entries']), 0)

    def test_search_entry_from_value_with_unnecessary_whitespaces(self):
        entry = Entry.objects.get(name='srv001', is_active=True)

        resp = self.client.get(reverse('dashboard:search'), {'query': '  hoge  '})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/entry/show/%s/' % entry.id)

    def test_show_dashboard_with_airone_user(self):
        # prepare the data of the imported file
        obj = yaml.safe_load(self.open_fixture_file('entry.yaml'))
        obj_entity_list = sorted(obj['Entity'], key=lambda x: x['id'])
        entry = Entry.objects.get(name='srv001', is_active=True)

        resp = self.client.get(reverse('dashboard:index'))
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.context["version"], str)
        self.assertEqual([x['attr_value'].id for x in resp.context["last_entries"]],
                         [entry.attrs.get(schema__name='attr-str').get_latest_value().id,
                          entry.attrs.get(schema__name='attr-arr-obj').get_latest_value().id,
                          entry.attrs.get(schema__name='attr-arr-str').get_latest_value().id,
                          entry.attrs.get(schema__name='attr-obj').get_latest_value().id])
        for i, x in enumerate(resp.context["navigator"]['entities']):
            self.assertEqual(x.id, obj_entity_list[i]['id'])

    def test_show_dashboard_with_django_user(self):
        # create test user which is authenticated by Django, not AirOne
        user = DjangoUser(username='django-user')
        user.set_password('passwd')
        user.save()

        # login as the django-user
        self.client.login(username='django-user', password='passwd')

        resp = self.client.get(reverse('dashboard:index'))
        self.assertEqual(resp.status_code, 200)

    def test_show_dashboard_with_anonymous(self):
        # logout test-user, this means current user is Anonymous
        self.client.logout()

        resp = self.client.get(reverse('dashboard:index'))
        self.assertEqual(resp.status_code, 200)

    def test_show_advanced_search(self):
        # create entity which has attr
        entity1 = Entity.objects.create(name="entity-1", created_user=self.admin)
        entity1.attrs.add(EntityAttr.objects.create(**{
            'name': 'attr-1-1',
            'type': AttrTypeValue['string'],
            'created_user': self.admin,
            'parent_entity': entity1,
        }))
        entity1.save()

        # create entity which doesn't have attr
        entity2 = Entity.objects.create(name="entity-2", created_user=self.admin)
        entity2.save()

        resp = self.client.get(reverse('dashboard:advanced_search'))
        self.assertEqual(resp.status_code, 200)

        entity_names = map(lambda e: e.name, resp.context['entities'])

        # entity-1 should be displayed
        self.assertEquals(1, len(list(filter(lambda n: n == "entity-1", entity_names))))
        # entity-2 should not be displayed
        self.assertEquals(0, len(list(filter(lambda n: n == "entity-2", entity_names))))

    @patch('dashboard.tasks.export_search_result.delay',
           Mock(side_effect=dashboard_tasks.export_search_result))
    def test_show_advanced_search_results(self):
        for entity_index in range(0, 2):
            entity = Entity.objects.create(name='entity-%d' % entity_index, created_user=self.admin)
            entity.attrs.add(EntityAttr.objects.create(**{
                'name': 'attr',
                'type': AttrTypeValue['string'],
                'created_user': self.admin,
                'parent_entity': entity,
            }))

            for entry_index in range(0, 10):
                entry = Entry.objects.create(name='entry-%d' % (entry_index),
                                             schema=entity, created_user=self.admin)
                entry.complement_attrs(self.admin)

                # add an AttributeValue
                entry.attrs.first().add_value(self.admin, 'data-%d' % entry_index)

                # register entry to the Elasticsearch
                entry.register_es()

        # test to show advanced_search_result page
        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'entity[]': [x.id for x in Entity.objects.filter(name__regex='^entity-')],
            'attr[]': ['attr'],  # an older param will be deprecated
        })
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'entity[]': [x.id for x in Entity.objects.filter(name__regex='^entity-')],
            'attrinfo': json.dumps([{'name': 'attr'}]),  # A newer param
        })
        self.assertEqual(resp.status_code, 200)

        # test to export results of advanced_search
        export_params = {
            'entities': [x.id for x in Entity.objects.filter(name__regex='^entity-')],
            'attrinfo': [{'name': 'attr', 'keyword': 'data-5'}],
            'export_style': 'csv',
        }

        resp = self.client.post(reverse('dashboard:export_search_result'),
                                json.dumps(export_params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        # check export task is executed
        job = Job.objects.last()
        self.assertEqual(job.operation, JobOperation.EXPORT_SEARCH_RESULT.value)
        self.assertEqual(job.status, Job.STATUS['DONE'])
        self.assertEqual(json.loads(job.params), export_params)

        # check result is set at cache
        csv_contents = [x for x in job.get_cache().splitlines() if x]
        self.assertEqual(len(csv_contents), 3)
        self.assertEqual(csv_contents[0], 'Name,Entity,attr')
        self.assertEqual(sorted(csv_contents[1:]),
                         sorted(['entry-5,entity-0,data-5', 'entry-5,entity-1,data-5']))

        ###
        # The case when export processing is canceled after running background processing
        ###
        for export_style in ['csv', 'yaml']:
            export_params['export_style'] = export_style
            with patch.object(Job, 'is_canceled', return_value=True):
                resp = self.client.post(reverse('dashboard:export_search_result'),
                                        json.dumps(export_params),
                                        'application/json')

            # check export task is executed
            job = Job.objects.last()
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(job.operation, JobOperation.EXPORT_SEARCH_RESULT.value)
            with self.assertRaises(OSError) as e:
                raise OSError

            if e.exception.errno == errno.ENOENT:
                job.get_cache()

        # test to show advanced_search_result page without mandatory params
        resp = self.client.get(reverse('dashboard:advanced_search_result'), {})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'),
                         'The attr[] or attrinfo parameters is required')

        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'attrinfo': 'hoge',
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'),
                         'The attr[] or attrinfo parameters is required')

        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'attrinfo': json.dumps([{'hoge': 'attr'}]),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'),
                         'The name key is required for attrinfo parameter')

        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'attrinfo': json.dumps([{'name': []}]),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'),
                         'Invalid name key value for attrinfo parameter')

        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'attrinfo': json.dumps([{'name': 'attr'}]),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'The entity[] parameters are required')

        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'attrinfo': json.dumps([{'name': 'attr'}]),
            'entity[]': ['hoge']
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid entity ID is specified')

        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'attrinfo': json.dumps([{'name': 'attr'}]),
            'entity[]': [9999]
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid entity ID is specified')

        # test to show advanced_search_result page with is_all_entries param
        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'attrinfo': json.dumps([{'name': 'attr'}]),
            'is_all_entities': 'true',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(sorted(resp.context['entities'].split(',')),
                         sorted([str(Entity.objects.get(name='entity-%d' % i).id)
                                 for i in range(2)]))
        self.assertEqual(resp.context['results']['ret_count'], 20)

        # test to show advanced_search_result page with entry_name param
        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'attrinfo': json.dumps([{'name': 'attr'}]),
            'is_all_entities': 'true',
            'entry_name': 'entry-0',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['results']['ret_count'], 2)

        # test to show advanced_search_result page with has_referal param
        ref_entry = Entry.objects.get(name='srv001', schema__name='Server')
        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'attrinfo': '[]',
            'entity[]': [Entity.objects.get(name='Entity1').id],
            'has_referral': 'true',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['results']['ret_count'], 3)
        self.assertEqual(resp.context['results']['ret_values'][0]['referrals'], [{
            'id': ref_entry.id,
            'name': ref_entry.name,
            'schema': ref_entry.schema.name,
        }])

        # test to show advanced_search_result page with referral_name param
        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'attrinfo': '[]',
            'entity[]': [Entity.objects.get(name='Entity1').id],
            'has_referral': 'true',
            'referral_name': 'srv001',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['results']['ret_count'], 1)

        # test to show advanced_search_result page with invalid has_referal param
        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'attrinfo': '[]',
            'entity[]': [Entity.objects.get(name='Entity1').id],
            'has_referral': 'hoge',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['results']['ret_count'], 3)
        self.assertTrue(all(['referrals' not in x for x in resp.context['results']['ret_values']]))

    def test_show_advanced_search_results_with_no_permission(self):
        guest_user = self.guest_login()

        # check when not have permission to read Entity
        entity = Entity.objects.get(name='Server')
        entity.is_public = False
        entity.save(update_fields=['is_public'])

        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'is_all_entities': 'true',
            'attrinfo': json.dumps([{'name': 'attr-str'}]),
        })
        self.assertEqual(resp.context['results']['ret_count'], 0)
        self.assertEqual(resp.context['results']['ret_values'], [])

        # check when not have permission to read EntityAttr
        entity.is_public = True
        entity.save(update_fields=['is_public'])
        entity_attr = EntityAttr.objects.get(name='attr-str')
        entity_attr.is_public = False
        entity_attr.save(update_fields=['is_public'])

        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'entity[]': [entity.id],
            'attrinfo': json.dumps([{'name': 'attr-str'}, {'name': 'attr-obj'}]),
        })
        self.assertEqual(resp.context['results']['ret_count'], 1)
        resp_attrs = resp.context['results']['ret_values'][0]['attrs']
        self.assertFalse(resp_attrs['attr-str']['is_readble'])
        self.assertTrue(resp_attrs['attr-obj']['is_readble'])

        # check when not have permission to read Entry
        entry = Entry.objects.get(name='srv001', schema__name='Server')
        entry.is_public = False
        entry.save(update_fields=['is_public'])
        entry.register_es()

        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'entity[]': [entity.id],
            'attrinfo': json.dumps([{'name': 'attr-obj'}]),
        })
        self.assertEqual(resp.context['results']['ret_count'], 1)
        resp_entry = resp.context['results']['ret_values'][0]
        self.assertFalse(resp_entry['is_readble'])
        self.assertEqual(resp_entry['attrs'], {})

        guest_user.permissions.add(entry.readable)

        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'entity[]': [entity.id],
            'attrinfo': json.dumps([{'name': 'attr-obj'}]),
        })
        self.assertEqual(resp.context['results']['ret_count'], 1)
        resp_entry = resp.context['results']['ret_values'][0]
        self.assertTrue(resp_entry['is_readble'])
        self.assertEqual(resp_entry['attrs']['attr-obj']['value'], {'id': 8, 'name': 'entry11'})

        # check when not have permission to read Attribute
        attr = entry.attrs.get(name='attr-obj')
        attr.is_public = False
        attr.save(update_fields=['is_public'])
        entry.register_es()

        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'entity[]': [entity.id],
            'attrinfo': json.dumps([{'name': 'attr-obj'}]),
        })
        self.assertEqual(resp.context['results']['ret_count'], 1)
        resp_attr = resp.context['results']['ret_values'][0]['attrs']['attr-obj']
        self.assertFalse(resp_attr['is_readble'])
        self.assertFalse('value' in resp_attr)

        guest_user.permissions.add(attr.readable)
        resp = self.client.get(reverse('dashboard:advanced_search_result'), {
            'entity[]': [entity.id],
            'attrinfo': json.dumps([{'name': 'attr-obj'}]),
        })
        self.assertEqual(resp.context['results']['ret_count'], 1)
        resp_attr = resp.context['results']['ret_values'][0]['attrs']['attr-obj']
        self.assertTrue(resp_attr['is_readble'])
        self.assertEqual(resp_attr['value'], {'id': 8, 'name': 'entry11'})

    @patch('dashboard.tasks.export_search_result.delay',
           Mock(side_effect=dashboard_tasks.export_search_result))
    def test_export_advanced_search_result(self):
        user = self.admin

        ref_entity = Entity.objects.create(name='Referred Entity', created_user=user)
        ref_entry = Entry.objects.create(name='ref_entry', schema=ref_entity, created_user=user)
        grp_entry = Group.objects.create(name='group_entry')
        attr_info = {
            'str': {'type': AttrTypeValue['string'], 'value': 'foo'},
            'text': {'type': AttrTypeValue['text'], 'value': 'foo'},
            'bool': {'type': AttrTypeValue['boolean'], 'value': True},
            'date': {'type': AttrTypeValue['date'], 'value': '2020-01-01'},
            'obj': {'type': AttrTypeValue['object'], 'value': ref_entry},
            'grp': {'type': AttrTypeValue['group'], 'value': grp_entry},
            'name': {'type': AttrTypeValue['named_object'],
                     'value': {'name': 'bar', 'id': ref_entry.id}},
            'arr_str': {'type': AttrTypeValue['array_string'], 'value': ['foo']},
            'arr_obj': {'type': AttrTypeValue['array_object'], 'value': [ref_entry]},
            'arr_grp': {'type': AttrTypeValue['array_group'], 'value': [grp_entry]},
            'arr_name': {'type': AttrTypeValue['array_named_object'],
                         'value': [{'name': 'hoge', 'id': ref_entry.id}]}
        }

        entity = Entity.objects.create(name='Entity', created_user=user)
        for attr_name, info in attr_info.items():
            entity.attrs.add(EntityAttr.objects.create(**{
                'name': attr_name,
                'type': info['type'],
                'created_user': user,
                'parent_entity': entity
            }))

        entry = Entry.objects.create(name='entry', schema=entity, created_user=user)
        entry.complement_attrs(user)
        for attr_name, info in attr_info.items():
            attr = entry.attrs.get(schema__name=attr_name)
            attr.add_value(user, info['value'])

        # register entry information to the index database
        entry.register_es()

        exporting_attr_names = ['str', 'text', 'bool', 'date', 'obj', 'grp', 'name',
                                'arr_str', 'arr_obj', 'arr_grp', 'arr_name']

        # test to export_search_result without mandatory params
        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'attrinfo': [{'name': x} for x in exporting_attr_names],
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'attrinfo': [{'name': x} for x in exporting_attr_names],
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        # test to export_search_result with invalid params
        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': 'hoge',
            'attrinfo': [{'name': x} for x in exporting_attr_names],
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [{'key': 'value'}],
            'attrinfo': [{'name': x} for x in exporting_attr_names],
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': ['hoge'],
            'attrinfo': [{'name': x} for x in exporting_attr_names],
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [9999],
            'attrinfo': [{'name': x} for x in exporting_attr_names],
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'attrinfo': 'hoge',
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'attrinfo': ['hoge'],
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'attrinfo': [{'hoge': 'value'}],
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'attrinfo': [{'name': ['hoge']}],
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'attrinfo': [{'name': 'hoge', 'keyword': ['hoge']}],
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'attrinfo': [{'name': x} for x in exporting_attr_names],
            'export_style': 'hoge',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid "export_type" is specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'attrinfo': [{'name': x} for x in exporting_attr_names],
            'export_style': 'csv',
            'entry_name': [],
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'attrinfo': [{'name': x} for x in exporting_attr_names],
            'export_style': 'csv',
            'has_referral': 'hoge',
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'attrinfo': [{'name': x} for x in exporting_attr_names],
            'export_style': 'csv',
            'referral_name': [],
        }), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode('utf-8'), 'Invalid parameters are specified')

        # send request to export data
        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'attrinfo': [{'name': x} for x in exporting_attr_names],
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 200)

        # verifying result has referral entry's infomations
        csv_contents = [x for x in Job.objects.last().get_cache().splitlines() if x]

        # checks all attribute are exported in order of specified sequence
        self.assertEqual(csv_contents[0], 'Name,Entity,%s' % ','.join(exporting_attr_names))

        # checks all data value are exported
        self.assertEqual(csv_contents[1], 'entry,Entity,foo,foo,True,2020-01-01,ref_entry,'
                                          'group_entry,bar: ref_entry,foo,ref_entry,'
                                          'group_entry,hoge: ref_entry')

    @patch('dashboard.tasks.export_search_result.delay',
           Mock(side_effect=dashboard_tasks.export_search_result))
    def test_export_advanced_search_result_with_referral(self):
        user = self.admin

        # initialize Entities
        ref_entity = Entity.objects.create(name='Referred Entity', created_user=user)
        entity = Entity.objects.create(name='entity', created_user=user)
        entity_attr = EntityAttr.objects.create(name='attr_ref',
                                                type=AttrTypeValue['object'],
                                                created_user=user,
                                                parent_entity=entity)
        entity_attr.referral.add(ref_entity)
        entity.attrs.add(entity_attr)

        # initialize Entries
        ref_entry = Entry.objects.create(name='ref', schema=ref_entity, created_user=user)
        ref_entry.register_es()

        entry = Entry.objects.create(name='entry', schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.attrs.first().add_value(user, ref_entry)

        # export with 'has_referral' parameter which has blank value
        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [ref_entity.id],
            'attrinfo': [],
            'has_referral': True,
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 200)

        # verifying result has referral entry's infomations
        csv_contents = [x for x in Job.objects.last().get_cache().splitlines() if x]
        self.assertEqual(len(csv_contents), 2)
        self.assertEqual(csv_contents[0], 'Name,Entity,Referral')
        self.assertEqual(csv_contents[1], "ref,Referred Entity,['entry / entity']")

        # export with 'has_referral' parameter which has invalid value
        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [ref_entity.id],
            'attrinfo': [],
            'has_referral': True,
            'referral_name': 'hogefuga',
            'export_style': 'csv',
        }), 'application/json')
        self.assertEqual(resp.status_code, 200)

        csv_contents = [x for x in Job.objects.last().get_cache().splitlines() if x]
        self.assertEqual(len(csv_contents), 1)

    @patch('dashboard.tasks.export_search_result.delay',
           Mock(side_effect=dashboard_tasks.export_search_result))
    def test_export_advanced_search_result_with_no_permission(self):
        self.guest_login()
        entry = Entry.objects.get(name='srv001', schema__name='Server')
        entry.is_public = False
        entry.save(update_fields=['is_public'])
        entry.register_es()

        self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [Entity.objects.get(name='Server').id],
            'attrinfo': [{'name': 'attr-str'}],
            'export_style': 'csv',
        }), 'application/json')

        csv_contents = [x for x in Job.objects.last().get_cache().splitlines() if x]
        self.assertEqual(csv_contents[0], 'Name,Entity,attr-str')
        self.assertEqual(csv_contents[1], 'srv001,Server,')

    @patch('dashboard.tasks.export_search_result.delay',
           Mock(side_effect=dashboard_tasks.export_search_result))
    def test_show_advanced_search_results_csv_escape(self):
        user = self.admin

        dummy_entity = Entity.objects.create(name='Dummy', created_user=user)
        dummy_entry = Entry(name='D,U"MM"Y', schema=dummy_entity, created_user=user)
        dummy_entry.save()

        CASES = [
            [AttrTypeStr, 'raison,de"tre', '"raison,de""tre"'],
            [AttrTypeObj,  dummy_entry, '"D,U""MM""Y"'],
            [AttrTypeText, "1st line\r\n2nd line", '"1st line' + "\r\n" + '2nd line"'],
            [AttrTypeNamedObj, {"key": dummy_entry}, "\"key: D,U\"\"MM\"\"Y\""],
            [AttrTypeArrStr, ["one", "two", "three"], "\"one\nthree\ntwo\""],
            [AttrTypeArrObj, [dummy_entry], "\"D,U\"\"MM\"\"Y\""],
            [AttrTypeArrNamedObj, [{"key1": dummy_entry}], "\"key1: D,U\"\"MM\"\"Y\""]
        ]

        for case in CASES:
            # setup data
            type_name = case[0].__name__  # AttrTypeStr -> 'AttrTypeStr'
            attr_name = type_name + ',"ATTR"'

            test_entity = Entity.objects.create(name="TestEntity_" + type_name, created_user=user)

            test_entity_attr = EntityAttr.objects.create(
                name=attr_name, type=case[0], created_user=user, parent_entity=test_entity)

            test_entity.attrs.add(test_entity_attr)
            test_entity.save()

            test_entry = Entry.objects.create(name=type_name + ',"ENTRY"', schema=test_entity,
                                              created_user=user)
            test_entry.save()

            test_attr = Attribute.objects.create(
                name=attr_name, schema=test_entity_attr, created_user=user, parent_entry=test_entry)

            test_attr.save()
            test_entry.attrs.add(test_attr)
            test_entry.save()

            test_val = None

            if case[0].TYPE & AttrTypeValue['array'] == 0:
                if case[0] == AttrTypeStr:
                    test_val = AttributeValue.create(user=user, attr=test_attr, value=case[1])
                elif case[0] == AttrTypeObj:
                    test_val = AttributeValue.create(user=user, attr=test_attr, referral=case[1])
                elif case[0] == AttrTypeText:
                    test_val = AttributeValue.create(user=user, attr=test_attr, value=case[1])
                elif case[0] == AttrTypeNamedObj:
                    [(k, v)] = case[1].items()
                    test_val = AttributeValue.create(user=user, attr=test_attr, value=k, referral=v)
            else:
                test_val = AttributeValue.create(user=user, attr=test_attr)
                test_val.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
                for child in case[1]:
                    test_val_child = None
                    if case[0] == AttrTypeArrStr:
                        test_val_child = AttributeValue.create(user=user, attr=test_attr,
                                                               value=child)
                    elif case[0] == AttrTypeArrObj:
                        test_val_child = AttributeValue.create(user=user, attr=test_attr,
                                                               referral=child)
                    elif case[0] == AttrTypeArrNamedObj:
                        [(k, v)] = child.items()
                        test_val_child = AttributeValue.create(user=user, attr=test_attr, value=k,
                                                               referral=v)
                    test_val.data_array.add(test_val_child)

            test_val.save()
            test_attr.values.add(test_val)
            test_attr.save()

            test_entry.register_es()

            resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
                'entities': [test_entity.id],
                'attrinfo': [{'name': test_attr.name, 'keyword': ''}],
                'export_style': 'csv',
            }), 'application/json')
            self.assertEqual(resp.status_code, 200)

            content = Job.objects.last().get_cache()
            header = content.splitlines()[0]
            self.assertEqual(header, 'Name,Entity,"%s,""ATTR"""' % type_name)

            data = content.replace(header, '', 1).strip()
            self.assertEqual(data, '"%s,""ENTRY""",%s,%s' % (type_name, test_entity.name, case[2]))

    @patch('entry.tasks.import_entries.delay', Mock(side_effect=entry_tasks.import_entries))
    @patch('dashboard.tasks.export_search_result.delay',
           Mock(side_effect=dashboard_tasks.export_search_result))
    def test_yaml_export(self):
        user = self.admin

        # create entity
        entity_ref = Entity.objects.create(name='RefEntity', created_user=user)
        entry_ref = Entry.objects.create(name='ref', schema=entity_ref, created_user=user)

        attr_info = {
            'str': {'type': AttrTypeValue['string'], 'value': 'foo',
                    'invalid_values': [123, entry_ref, True]},
            'obj': {'type': AttrTypeValue['object'], 'value': str(entry_ref.id)},
            'name': {'type': AttrTypeValue['named_object'],
                     'value': {'name': 'bar', 'id': str(entry_ref.id)}},
            'bool': {'type': AttrTypeValue['boolean'], 'value': False},
            'arr_str': {'type': AttrTypeValue['array_string'], 'value': ['foo', 'bar', 'baz']},
            'arr_obj': {'type': AttrTypeValue['array_object'],
                        'value': [str(entry_ref.id)]},
            'arr_name': {'type': AttrTypeValue['array_named_object'],
                         'value': [
                             {'name': 'hoge', 'id': str(entry_ref.id)},
                             {'name': 'fuga', 'boolean': False},  # specify boolean parameter
                          ]},
            'group': {'type': AttrTypeValue['group'],
                      'value': str(Group.objects.create(name='group').id)},
            'date': {'type': AttrTypeValue['date'], 'value': date(2020, 1, 1)}
        }
        entities = []
        for index in range(2):
            entity = Entity.objects.create(name='Entity-%d' % index, created_user=user)
            for attr_name, info in attr_info.items():
                attr = EntityAttr.objects.create(name=attr_name,
                                                 type=info['type'],
                                                 created_user=user,
                                                 parent_entity=entity)

                if info['type'] & AttrTypeValue['object']:
                    attr.referral.add(entity_ref)

                entity.attrs.add(attr)

            # create an entry of Entity
            for e_index in range(2):
                entry = Entry.objects.create(name='e-%d' % e_index, schema=entity,
                                             created_user=user)
                entry.complement_attrs(user)

                for attr_name, info in attr_info.items():
                    attr = entry.attrs.get(name=attr_name)
                    attrv = attr.add_value(user, info['value'])

                entry.register_es()

            entities.append(entity)

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [x.id for x in Entity.objects.filter(name__regex='^Entity-')],
            'attrinfo': [{'name': x, 'keyword': ''} for x in attr_info.keys()],
            'export_style': 'yaml',
        }), 'application/json')
        self.assertEqual(resp.status_code, 200)

        resp_data = yaml.load(Job.objects.last().get_cache(), Loader=yaml.FullLoader)
        for index in range(2):
            entity = Entity.objects.get(name='Entity-%d' % index)
            e_data = resp_data[entity.name]

            self.assertEqual(len(resp_data[entity.name]),
                             Entry.objects.filter(schema=entity).count())
            for e_data in resp_data[entity.name]:
                self.assertTrue(e_data['name'] in ['e-0', 'e-1'])
                self.assertTrue(all([x in attr_info.keys() for x in e_data['attrs']]))

        # Checked to be able to import exported data
        entry_another_ref = Entry.objects.create(name='another_ref', schema=entity_ref,
                                                 created_user=user)
        new_group = Group.objects.create(name='new_group')
        new_attr_values = {
            'str': 'bar',
            'obj': 'another_ref',
            'name': {'hoge': 'another_ref'},
            'bool': True,
            'arr_str': ['hoge', 'fuga'],
            'arr_obj': ['another_ref'],
            'arr_name': [{'foo': 'another_ref'}, {'bar': 'ref'}],
            'group': 'new_group',
            'date': '1999-01-01',
        }
        resp_data['Entity-1'][0]['attrs'] = new_attr_values

        mockio = mock.mock_open(read_data=yaml.dump(resp_data))
        with mock.patch('builtins.open', mockio):
            with open('hogefuga.yaml') as fp:
                resp = self.client.post(reverse('entry:do_import', args=[entities[1].id]),
                                        {'file': fp})
                self.assertEqual(resp.status_code, 303)

        self.assertEqual(entry_another_ref.get_referred_objects().count(), 1)

        updated_entry = entry_another_ref.get_referred_objects().first()
        self.assertEqual(updated_entry.name, resp_data['Entity-1'][0]['name'])

        for (attr_name, value_info) in new_attr_values.items():
            attrv = updated_entry.attrs.get(name=attr_name).get_latest_value()

            if attr_name == 'str':
                self.assertEqual(attrv.value, value_info)
            elif attr_name == 'obj':
                self.assertEqual(attrv.referral.id, entry_another_ref.id)
            elif attr_name == 'name':
                self.assertEqual(attrv.value, list(value_info.keys())[0])
                self.assertEqual(attrv.referral.id, entry_another_ref.id)
            elif attr_name == 'bool':
                self.assertTrue(attrv.boolean)
            elif attr_name == 'arr_str':
                self.assertEqual(sorted([x.value for x in attrv.data_array.all()]),
                                 sorted(value_info))
            elif attr_name == 'arr_obj':
                self.assertEqual([x.referral.id for x in attrv.data_array.all()],
                                 [entry_another_ref.id])
            elif attr_name == 'arr_name':
                self.assertEqual(sorted([x.value for x in attrv.data_array.all()]),
                                 sorted([list(x.keys())[0] for x in value_info]))
                self.assertEqual(sorted([x.referral.name for x in attrv.data_array.all()]),
                                 sorted([list(x.values())[0] for x in value_info]))
            elif attr_name == 'group':
                self.assertEqual(int(attrv.value), new_group.id)
            elif attr_name == 'date':
                self.assertEqual(attrv.date, date(1999, 1, 1))

    @patch('dashboard.tasks.export_search_result.delay',
           Mock(side_effect=dashboard_tasks.export_search_result))
    def test_duplicate_export(self):
        user = self.admin

        entity = Entity.objects.create(name='Entity', created_user=user)
        export_params = {
            'entities': [entity.id],
            'attrinfo': [{'name': 'attr', 'keyword': 'data-5'}],
            'export_style': 'csv',
        }

        # create a job to export search result
        job = Job.new_export(user, params=export_params)

        # A request with same parameter which is under execution will be denied
        resp = self.client.post(reverse('dashboard:export_search_result'),
                                json.dumps(export_params, sort_keys=True),
                                'application/json')
        self.assertEqual(resp.status_code, 400)

        # A request with another condition will be accepted
        new_export_params = dict(export_params, **{'export_style': 'yaml'})
        resp = self.client.post(reverse('dashboard:export_search_result'),
                                json.dumps(new_export_params, sort_keys=True),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        # When the job is finished, the processing is passed.
        job.status = Job.STATUS['DONE']
        job.save(update_fields=['status'])
        resp = self.client.post(reverse('dashboard:export_search_result'),
                                json.dumps(export_params, sort_keys=True),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

    @patch('dashboard.tasks.export_search_result.delay',
           Mock(side_effect=dashboard_tasks.export_search_result))
    def test_export_with_hint_entry_name(self):
        entity = Entity.objects.create(name='Entity', created_user=self.admin)
        for name in ['foo', 'bar', 'baz']:
            Entry.objects.create(name=name, schema=entity, created_user=self.admin).register_es()

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [entity.id],
            'attrinfo': [],
            'entry_name': 'ba',
            'export_style': 'yaml',
        }), 'application/json')
        self.assertEqual(resp.status_code, 200)

        resp_data = yaml.load(Job.objects.last().get_cache(), Loader=yaml.FullLoader)
        self.assertEqual(len(resp_data['Entity']), 2)
        self.assertEqual([x['name'] for x in resp_data['Entity']], ['bar', 'baz'])

    @patch('dashboard.tasks.export_search_result.delay',
           Mock(side_effect=dashboard_tasks.export_search_result))
    def test_yaml_export_with_referral(self):
        user = self.admin

        # initialize Entities
        ref_entity = Entity.objects.create(name='ReferredEntity', created_user=user)
        entity = Entity.objects.create(name='entity', created_user=user)
        entity_attr = EntityAttr.objects.create(name='attr_ref',
                                                type=AttrTypeValue['object'],
                                                created_user=user,
                                                parent_entity=entity)
        entity_attr.referral.add(ref_entity)
        entity.attrs.add(entity_attr)

        # initialize Entries
        ref_entry = Entry.objects.create(name='ref', schema=ref_entity, created_user=user)
        ref_entry.register_es()

        entry = Entry.objects.create(name='entry', schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.attrs.first().add_value(user, ref_entry)

        resp = self.client.post(reverse('dashboard:export_search_result'), json.dumps({
            'entities': [ref_entity.id],
            'attrinfo': [],
            'export_style': 'yaml',
            'has_referral': True,
        }), 'application/json')
        self.assertEqual(resp.status_code, 200)

        resp_data = yaml.load(Job.objects.last().get_cache(), Loader=yaml.FullLoader)
        self.assertEqual(len(resp_data['ReferredEntity']), 1)
        referrals = resp_data['ReferredEntity'][0]['referrals']
        self.assertEqual(len(referrals), 1)
        self.assertEqual(referrals[0]['entity'], 'entity')
        self.assertEqual(referrals[0]['entry'], 'entry')
