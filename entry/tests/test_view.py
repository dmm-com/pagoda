import json
import yaml
import errno

from django.http import HttpResponse
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q
from group.models import Group
from datetime import date

from entity.models import Entity, EntityAttr
from entry.models import Entry, Attribute, AttributeValue
from user.models import User

from airone.lib.types import AttrTypeStr, AttrTypeObj, AttrTypeText
from airone.lib.types import AttrTypeArrStr, AttrTypeArrObj
from airone.lib.types import AttrTypeNamedObj, AttrTypeArrNamedObj
from airone.lib.types import AttrTypeValue
from airone.lib.test import AironeViewTest
from airone.lib.acl import ACLType

from unittest.mock import patch
from unittest.mock import Mock
from unittest import skip
from entry import tasks
from job.models import Job, JobOperation
from django.http.response import JsonResponse


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        # clear all caches
        cache.clear()

    # override 'admin_login' method to create initial Entity/EntityAttr objects
    def admin_login(self):
        user = super(ViewTest, self).admin_login()

        # create test entity which is a base of creating entry
        self._entity = Entity.objects.create(name='hoge', created_user=user)

        # set EntityAttr for the test Entity object
        self._entity_attr = EntityAttr(name='test',
                                       type=AttrTypeStr,
                                       is_mandatory=True,
                                       created_user=user,
                                       parent_entity=self._entity)
        self._entity_attr.save()
        self._entity.attrs.add(self._entity_attr)

        return user

    def make_attr(self, name, attrtype=AttrTypeStr, created_user=None, parent_entity=None,
                  parent_entry=None):
        schema = EntityAttr.objects.create(name=name,
                                           type=attrtype,
                                           created_user=(
                                               created_user and created_user or self._user),
                                           parent_entity=(
                                               parent_entity and parent_entity or self._entity))

        return Attribute.objects.create(name=name,
                                        schema=schema,
                                        created_user=(created_user and created_user or self._user),
                                        parent_entry=(parent_entry and parent_entry or self._entry))

    def test_get_index_without_login(self):
        resp = self.client.get(reverse('entry:index', args=[0]))
        self.assertEqual(resp.status_code, 303)

    def test_get_index_with_login(self):
        self.admin_login()

        resp = self.client.get(reverse('entry:index', args=[self._entity.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_index_with_entries(self):
        user = self.admin_login()

        Entry(name='fuga', schema=self._entity, created_user=user).save()

        resp = self.client.get(reverse('entry:index', args=[self._entity.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_permitted_entries(self):
        self.guest_login()

        another_user = User.objects.create(username='hoge')
        entity = Entity(name='hoge', created_user=another_user, is_public=False)
        entity.save()

        resp = self.client.get(reverse('entry:index', args=[entity.id]))
        self.assertEqual(resp.status_code, 400)

    def test_get_self_created_entries(self):
        self.admin_login()

        self._entity.is_public = False

        resp = self.client.get(reverse('entry:index', args=[self._entity.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_entries_with_user_permission(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='hoge',
                                       is_public=False,
                                       created_user=User.objects.create(username='hoge'))

        # set permission to the logged-in user
        user.permissions.add(entity.readable)

        resp = self.client.get(reverse('entry:index', args=[entity.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_entries_with_superior_user_permission(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='hoge',
                                       is_public=False,
                                       created_user=User.objects.create(username='hoge'))

        # set superior permission to the logged-in user
        user.permissions.add(entity.writable)

        resp = self.client.get(reverse('entry:index', args=[entity.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_with_inferior_user_permission(self):
        user = self.guest_login()

        entity = Entity.objects.create(name='hoge',
                                       is_public=False,
                                       created_user=User.objects.create(username='hoge'))

        # set superior permission to the logged-in user
        user.permissions.add(entity.readable)

        resp = self.client.get(reverse('entry:create', args=[entity.id]))
        self.assertEqual(resp.status_code, 400)

    def test_get_entries_with_group_permission(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='hoge',
                                       is_public=False,
                                       created_user=User.objects.create(username='hoge'))

        # create test group
        group = Group.objects.create(name='test-group')
        user.groups.add(group)

        # set permission to the group which logged-in user belonged to
        group.permissions.add(entity.readable)

        resp = self.client.get(reverse('entry:index', args=[entity.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_entries_with_superior_group_permission(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='hoge',
                                       is_public=False,
                                       created_user=User.objects.create(username='hoge'))

        # create test group
        group = Group.objects.create(name='test-group')
        user.groups.add(group)

        # set superior permission to the group which logged-in user belonged to
        group.permissions.add(entity.full)

        resp = self.client.get(reverse('entry:index', args=[entity.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_create_page_without_login(self):
        resp = self.client.get(reverse('entry:create', args=[0]))
        self.assertEqual(resp.status_code, 303)

    def test_get_create_page_with_login(self):
        self.admin_login()

        resp = self.client.get(reverse('entry:create', args=[self._entity.id]))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['entity'], self._entity)

    def test_post_without_login(self):
        params = {
            'entry_name': 'hoge',
            'attrs': [
                {'id': '0', 'value': [{'data': 'fuga', 'index': 0}], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[0]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Attribute.objects.count(), 0)
        self.assertEqual(AttributeValue.objects.count(), 0)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_post_create_entry(self):
        user = self.admin_login()

        params = {
            'entry_name': 'hoge',
            'attrs': [
                {'id': str(self._entity_attr.id), 'type': str(AttrTypeArrStr),
                 'value': [{'data': 'hoge', 'index': '0'}], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(Attribute.objects.count(), 1)
        self.assertEqual(AttributeValue.objects.count(), 1)

        entry = Entry.objects.last()
        self.assertEqual(entry.attrs.count(), 1)
        self.assertEqual(entry.attrs.last(), Attribute.objects.last())
        self.assertEqual(entry.attrs.last().values.count(), 1)

        attrvalue = AttributeValue.objects.last()
        self.assertEqual(entry.attrs.last().values.last(), attrvalue)
        self.assertTrue(attrvalue.is_latest)

        # checks that created entry is also registered in the Elasticsearch
        res = self._es.get(index=settings.ES_CONFIG['INDEX'], doc_type='entry', id=entry.id)
        self.assertTrue(res['found'])
        self.assertEqual(res['_source']['entity']['id'], self._entity.id)
        self.assertEqual(res['_source']['name'], entry.name)
        self.assertEqual(len(res['_source']['attr']), entry.attrs.count())
        for attrinfo in res['_source']['attr']:
            attrv = AttributeValue.objects.get(parent_attr__name=attrinfo['name'], is_latest=True)
            self.assertEqual(attrinfo['value'], attrv.value)

        # checks job was created
        job = Job.objects.filter(user=user)
        self.assertEqual(job.count(), 1)

        # checks each parameters of the job are as expected
        obj = job.first()
        self.assertEqual(obj.target.id, entry.id)
        self.assertEqual(obj.target_type, Job.TARGET_ENTRY)
        self.assertEqual(obj.status, Job.STATUS['DONE'])
        self.assertEqual(obj.operation, JobOperation.CREATE_ENTRY.value)

        # checks specify part of attribute parameter then set AttributeValue
        # which is only specified one
        new_attr = EntityAttr.objects.create(name='new_attr',
                                             created_user=user,
                                             type=AttrTypeValue['string'],
                                             parent_entity=self._entity,
                                             is_mandatory=False)
        self._entity.attrs.add(new_attr)
        params['entry_name'] = 'new_entry'
        params['attrs'] = [{'id': str(new_attr.id), 'value': [{'data': 'foo', 'index': '0'}]}]

        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params), 'application/json')

        entry = Entry.objects.last()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(entry.name, params['entry_name'])
        self.assertEqual(entry.attrs.count(), 2)

        attr_info = entry.get_available_attrs(user)
        self.assertEqual(len(attr_info), 2)
        self.assertEqual(sorted([x['name'] for x in attr_info]),
                         sorted([x.schema.name for x in entry.attrs.all()]))

        self.assertEqual([x['last_value'] for x in attr_info if x['name'] == 'test'], [''])
        self.assertEqual([x['last_value'] for x in attr_info if x['name'] == 'new_attr'], ['foo'])

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_post_create_entry_without_permission(self):
        self.guest_login()

        another_user = User.objects.create(username='hoge')
        entity = Entity.objects.create(name='hoge', is_public=False, created_user=another_user)
        attr_base = EntityAttr.objects.create(name='test',
                                              type=AttrTypeStr,
                                              is_mandatory=True,
                                              parent_entity=entity,
                                              created_user=another_user)
        entity.attrs.add(attr_base)

        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(attr_base.id), 'value': [{'data': 'hoge', 'index': 0}],
                 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Attribute.objects.count(), 0)
        self.assertEqual(AttributeValue.objects.count(), 0)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_post_with_optional_parameter(self):
        user = self.admin_login()

        # add an optional EntityAttr to the test Entity object
        self._entity_attr_optional = EntityAttr(name='test-optional',
                                                type=AttrTypeStr,
                                                is_mandatory=False,
                                                created_user=user,
                                                parent_entity=self._entity)
        self._entity_attr_optional.save()
        self._entity.attrs.add(self._entity_attr_optional)

        params = {
            'entry_name': 'hoge',
            'attrs': [
                {'id': str(self._entity_attr.id), 'type': str(AttrTypeStr),
                 'value': [{'data': 'hoge', 'index': 0}], 'referral_key': []},
                {'id': str(self._entity_attr_optional.id), 'type': str(AttrTypeStr), 'value': [],
                 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(Attribute.objects.count(), 2)

        # Even if an empty value is specified, an AttributeValue will be create for creating.
        self.assertEqual(AttributeValue.objects.count(), 2)

        entry = Entry.objects.last()
        self.assertEqual(entry.attrs.count(), 2)
        self.assertEqual(entry.attrs.get(name='test').values.count(), 1)
        self.assertEqual(entry.attrs.get(name='test-optional').values.count(), 1)
        self.assertEqual(entry.attrs.get(name='test').values.last().value, 'hoge')

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_post_with_lack_of_params(self):
        self.admin_login()

        params = {
            'entry_name': '',
            'attrs': [
                {'id': str(self._entity_attr.id), 'value': [{'data': 'hoge', 'index': 0}],
                 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Attribute.objects.count(), 0)
        self.assertEqual(AttributeValue.objects.count(), 0)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_post_create_with_referral(self):
        user = self.admin_login()

        attr_base = EntityAttr.objects.create(name='attr_with_referral',
                                              created_user=user,
                                              type=AttrTypeObj,
                                              parent_entity=self._entity,
                                              is_mandatory=False)
        attr_base.referral.add(self._entity)
        self._entity.attrs.add(attr_base)

        entry = Entry.objects.create(name='entry', schema=self._entity, created_user=user)

        params = {
            'entry_name': 'new_entry',
            'attrs': [
                {'id': str(self._entity_attr.id), 'type': str(AttrTypeObj),
                 'value': [{'data': 'hoge', 'index': 0}], 'referral_key': []},
                {'id': str(attr_base.id), 'type': str(AttrTypeObj),
                 'value': [{'data': str(entry.id), 'index': 0}], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), 2)
        self.assertEqual(Entry.objects.last().name, 'new_entry')
        self.assertEqual(Entry.objects.last().attrs.last().schema.type, AttrTypeObj)
        self.assertEqual(Entry.objects.last().attrs.last().values.count(), 1)
        self.assertEqual(Entry.objects.last().attrs.last().values.last().value, '')
        self.assertEqual(Entry.objects.last().attrs.last().values.last().referral.id, entry.id)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_post_with_invalid_param(self):
        self.admin_login()

        params = {
            'entry_name': 'hoge',
            'attrs': [
                {'id': str(self._entity_attr.id), 'value': [{'data': 'hoge', 'index': 0}],
                 'referral_key': []},
                {'id': '9999', 'value': ['invalid value'], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Attribute.objects.count(), 0)
        self.assertEqual(AttributeValue.objects.count(), 0)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_post_without_entry(self):
        user = self.admin_login()

        attr_base = EntityAttr.objects.create(name='ref_attr',
                                              created_user=user,
                                              type=AttrTypeObj,
                                              parent_entity=self._entity,
                                              is_mandatory=False)
        attr_base.referral.add(self._entity)
        self._entity.attrs.add(attr_base)

        params = {
            'entry_name': 'new_entry',
            'attrs': [
                {'id': str(self._entity_attr.id), 'type': str(AttrTypeObj),
                 'value': [{'data': 'hoge', 'index': 0}], 'referral_key': []},
                {'id': str(attr_base.id), 'type': str(AttrTypeObj),
                 'value': [{'data': '0', 'index': 0}], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        new_entry = Entry.objects.get(name='new_entry')
        self.assertEqual(new_entry.attrs.get(schema=self._entity_attr).values.count(), 1)
        self.assertEqual(new_entry.attrs.get(schema=self._entity_attr).values.last().value, 'hoge')
        # Even if an empty value is specified, an AttributeValue will be create for creating.
        self.assertEqual(new_entry.attrs.get(schema=attr_base).values.count(), 1)

    def test_get_edit_without_login(self):
        resp = self.client.get(reverse('entry:edit', args=[0]))
        self.assertEqual(resp.status_code, 303)

    def test_get_edit_with_invalid_entry_id(self):
        user = self.admin_login()

        Entry(name='fuga', schema=self._entity, created_user=user).save()

        # with invalid entry-id
        resp = self.client.get(reverse('entry:edit', args=[0]))
        self.assertEqual(resp.status_code, 400)

    def test_get_edit_with_valid_entry_id(self):
        user = self.admin_login()

        # making test Entry set
        entry = Entry(name='fuga', schema=self._entity, created_user=user)
        entry.save()

        for attr_name in ['foo', 'bar']:
            attr = self.make_attr(name=attr_name,
                                  parent_entry=entry,
                                  created_user=user)

            for value in ['hoge', 'fuga']:
                attr_value = AttributeValue(value=value, created_user=user, parent_attr=attr)
                attr_value.save()

                attr.values.add(attr_value)

            entry.attrs.add(attr)

        # with invalid entry-id
        resp = self.client.get(reverse('entry:edit', args=[entry.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_edit_with_optional_attr(self):
        user = self.admin_login()

        # making test Entry set
        entry = Entry(name='fuga', schema=self._entity, created_user=user)
        entry.save()

        attr = self.make_attr(name='attr', created_user=user, parent_entry=entry)
        entry.attrs.add(attr)

        # with invalid entry-id
        resp = self.client.get(reverse('entry:edit', args=[entry.id]))
        self.assertEqual(resp.status_code, 200)

    def test_post_edit_without_login(self):
        params = {'attrs': [{'id': '0', 'value': [], 'referral_key': []}]}
        resp = self.client.post(reverse('entry:do_edit', args=[0]),
                                json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(AttributeValue.objects.count(), 0)

    def test_post_edit_with_invalid_param(self):
        self.admin_login()

        params = {'attrs': [{'id': '0', 'value': [], 'referral_key': []}]}
        resp = self.client.post(reverse('entry:do_edit', args=[0]),
                                json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(AttributeValue.objects.count(), 0)

    def test_post_edit_creating_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name='entry', schema=self._entity, created_user=user)
        entry.set_status(Entry.STATUS_CREATING)

        params = {'entry_name': 'changed-entry'}
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.get(id=entry.id).name, 'entry')

    def test_get_show_and_edit_creating_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name='entry', schema=self._entity, created_user=user)
        entry.set_status(Entry.STATUS_CREATING)

        resp = self.client.get(reverse('entry:show', args=[entry.id]))
        self.assertEqual(resp.status_code, 400)

        resp = self.client.get(reverse('entry:edit', args=[entry.id]))
        self.assertEqual(resp.status_code, 400)

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_with_valid_param(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='entity', created_user=user)
        for attr_name in ['foo', 'bar']:
            entity.attrs.add(EntityAttr.objects.create(name=attr_name,
                                                       type=AttrTypeValue['string'],
                                                       created_user=user,
                                                       parent_entity=entity))

        # making test Entry set
        entry = Entry.objects.create(name='fuga', schema=entity, created_user=user)
        entry.complement_attrs(user)

        for attr in entry.attrs.all():
            attr.add_value(user, 'hoge')

        params = {
            'entry_name': 'hoge',
            'attrs': [
                {'id': str(Attribute.objects.get(name='foo').id), 'type': str(AttrTypeArrStr),
                 'value': [{'data': 'hoge', 'index': 0}], 'referral_key': []},
                {'id': str(Attribute.objects.get(name='bar').id), 'type': str(AttrTypeArrStr),
                 'value': [{'data': 'fuga', 'index': 0}], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AttributeValue.objects.count(), 3)
        self.assertEqual(Attribute.objects.get(name='foo').values.count(), 1)
        self.assertEqual(Attribute.objects.get(name='bar').values.count(), 2)
        self.assertEqual(Attribute.objects.get(name='foo').values.last().value, 'hoge')
        self.assertEqual(Attribute.objects.get(name='bar').values.last().value, 'fuga')
        self.assertEqual(Entry.objects.get(id=entry.id).name, 'hoge')

        # checks to set corrected status-flag
        foo_value_first = Attribute.objects.get(name='foo').values.first()
        bar_value_first = Attribute.objects.get(name='bar').values.first()
        bar_value_last = Attribute.objects.get(name='bar').values.last()

        self.assertTrue(foo_value_first.is_latest)
        self.assertFalse(bar_value_first.is_latest)
        self.assertTrue(bar_value_last.is_latest)

        # checks that we can search updated entry using updated value
        resp = Entry.search_entries(user, [entity.id], [{'name': 'bar', 'keyword': 'fuga'}])
        self.assertEqual(resp['ret_count'], 1)
        self.assertEqual(resp['ret_values'][0]['entity']['id'], entity.id)
        self.assertEqual(resp['ret_values'][0]['entry']['id'], entry.id)

        # checks job was created
        job = Job.objects.filter(user=user)
        self.assertEqual(job.count(), 1)

        # checks each parameters of the job are as expected
        obj = job.first()
        self.assertEqual(obj.target.id, entry.id)
        self.assertEqual(obj.target_type, Job.TARGET_ENTRY)
        self.assertEqual(obj.status, Job.STATUS['DONE'])
        self.assertEqual(obj.operation, JobOperation.EDIT_ENTRY.value)

        # checks specify part of attribute parameter then set AttributeValue
        # which is only specified one
        params = {
            'entry_name': 'foo',
            'attrs': [
                {'id': str(Attribute.objects.get(name='foo').id),
                 'value': [{'data': 'puyo', 'index': 0}]},
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        entry.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(entry.attrs.get(name='foo').get_latest_value().value, 'puyo')
        self.assertEqual(entry.attrs.get(name='bar').get_latest_value().value, 'fuga')

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_with_optional_params(self):
        user = self.admin_login()

        # making test Entry set
        entry = Entry(name='fuga', schema=self._entity, created_user=user)
        entry.save()

        for attr_name in ['foo', 'bar', 'baz']:
            attr = self.make_attr(name=attr_name,
                                  created_user=user,
                                  parent_entry=entry)
            entry.attrs.add(attr)

        params = {
            'entry_name': entry.name,
            'attrs': [
                # include blank value
                {'id': str(Attribute.objects.get(name='foo').id), 'type': str(AttrTypeArrStr),
                 'value': [{'data': '', 'index': 0}], 'referral_key': []},
                {'id': str(Attribute.objects.get(name='bar').id), 'type': str(AttrTypeArrStr),
                 'value': [{'data': 'fuga', 'index': 0}], 'referral_key': []},
                {'id': str(Attribute.objects.get(name='baz').id), 'type': str(AttrTypeArrStr),
                 'value': [{'data': '0', 'index': 0}], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Attribute.objects.get(name='foo').values.filter(is_latest=True).count(), 0)
        self.assertEqual(Attribute.objects.get(name='bar').values.filter(is_latest=True).count(), 1)
        self.assertEqual(Attribute.objects.get(name='bar').values.last().value, 'fuga')
        self.assertEqual(Attribute.objects.get(name='baz').values.filter(is_latest=True).count(), 1)
        self.assertEqual(Attribute.objects.get(name='baz').values.last().value, '0')
        self.assertEqual(Entry.objects.get(id=entry.id).name, entry.name)

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_with_array_string_value(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='entity', created_user=user)
        entity.attrs.add(EntityAttr.objects.create(**{
            'name': 'attr',
            'type': AttrTypeArrStr,
            'created_user': user,
            'parent_entity': entity,
        }))

        entry = Entry.objects.create(name='entry', created_user=user, schema=entity)
        entry.complement_attrs(user)
        attr = entry.attrs.first()
        attr.add_value(user, [
            {'name': 'hoge', 'id': ''},
            {'name': 'fuga', 'id': ''},
        ])

        parent_values_count = AttributeValue.objects.extra(**{
            'where': ['status & %s = 1' % AttributeValue.STATUS_DATA_ARRAY_PARENT]
        }).count()

        params = {
            'entry_name': entry.name,
            'attrs': [{
                'id': str(attr.id),
                'type': str(attr.schema.type),
                'value': [
                    {'data': 'hoge', 'index': 0},
                    {'data': 'puyo', 'index': 1},
                ],
                'referral_key': [],
            }],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        # checks to set correct status flags
        leaf_values = [x for x in AttributeValue.objects.all()
                       if not x.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)]

        parent_values = [x for x in AttributeValue.objects.all()
                         if x.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)]
        self.assertEqual(len(leaf_values), 4)
        self.assertEqual(len(parent_values), parent_values_count + 1)

        self.assertEqual(attr.values.count(), parent_values_count + 1)
        self.assertTrue(attr.values.last().status & AttributeValue.STATUS_DATA_ARRAY_PARENT)

        self.assertEqual(attr.values.last().data_array.count(), 2)
        self.assertTrue(
            all([x.value in ['hoge', 'puyo'] for x in attr.values.last().data_array.all()]))

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_with_array_object_value(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='entity', created_user=user)
        entity.attrs.add(EntityAttr.objects.create(**{
            'name': 'attr',
            'type': AttrTypeValue['array_named_object'],
            'created_user': user,
            'parent_entity': entity,
        }))

        entry = Entry.objects.create(name='entry', created_user=user, schema=entity)
        entry.complement_attrs(user)

        (e1, e2, e3) = [Entry.objects.create(
            name='E%d' % i, created_user=user, schema=entity) for i in range(3)]

        attr = entry.attrs.first()
        attr.add_value(user, [
            {'name': '', 'id': e1},
            {'name': '', 'id': e2},
        ])

        parent_values_count = AttributeValue.objects.extra(**{
            'where': ['status & %s = 1' % AttributeValue.STATUS_DATA_ARRAY_PARENT]
        }).count()

        params = {
            'entry_name': entry.name,
            'attrs': [{
                'id': str(attr.id),
                'type': str(AttrTypeArrObj),
                'value': [
                    {'data': e2.id, 'index': 0},
                    {'data': e3.id, 'index': 1},
                ],
                'referral_key': [],
            }],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        # checks to set correct status flags
        leaf_values = [x for x in AttributeValue.objects.all()
                       if not x.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)]

        parent_values = [x for x in AttributeValue.objects.all()
                         if x.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)]
        self.assertEqual(len(leaf_values), 4)
        self.assertEqual(len(parent_values), parent_values_count + 1)
        self.assertEqual(attr.values.count(), parent_values_count + 1)
        self.assertTrue(attr.values.last().status & AttributeValue.STATUS_DATA_ARRAY_PARENT)

        self.assertEqual(attr.values.last().data_array.count(), 2)
        self.assertTrue(all([x.referral.id in [e2.id, e3.id]
                            for x in attr.values.last().data_array.all()]))

    def test_get_detail_with_invalid_param(self):
        self.admin_login()

        resp = self.client.get(reverse('entry:show', args=[0]))
        self.assertEqual(resp.status_code, 400)

    def test_get_detail_with_valid_param(self):
        user = self.admin_login()

        # making test Entry set
        entry = Entry(name='fuga', schema=self._entity, created_user=user)
        entry.save()

        for attr_name in ['foo', 'bar']:
            attr = self.make_attr(name=attr_name,
                                  created_user=user,
                                  parent_entry=entry)

            for value in ['hoge', 'fuga']:
                attr_value = AttributeValue(value=value, created_user=user, parent_attr=attr)
                attr_value.save()

                attr.values.add(attr_value)

            entry.attrs.add(attr)

        resp = self.client.get(reverse('entry:show', args=[entry.id]))
        self.assertEqual(resp.status_code, 200)

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_with_referral(self):
        user = self.admin_login()

        attr_base = EntityAttr.objects.create(name='attr_with_referral',
                                              created_user=user,
                                              type=AttrTypeObj,
                                              parent_entity=self._entity,
                                              is_mandatory=False)
        attr_base.referral.add(self._entity)
        self._entity.attrs.add(attr_base)

        entry = Entry.objects.create(name='old_entry', schema=self._entity, created_user=user)

        attr = entry.add_attribute_from_base(attr_base, user)
        attr_value = AttributeValue.objects.create(referral=entry,
                                                   created_user=user,
                                                   parent_attr=attr)
        attr.values.add(attr_value)

        new_entry = Entry.objects.create(name='new_entry', schema=self._entity, created_user=user)

        params = {
            'entry_name': 'old_entry',
            'attrs': [
                {'id': str(attr.id), 'type': str(AttrTypeObj),
                 'value': [{'data': str(new_entry.id), 'index': 0}], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(entry.attrs.last().values.count(), 2)
        self.assertEqual(entry.attrs.last().values.first().value, '')
        self.assertEqual(entry.attrs.last().values.first().referral.id, entry.id)
        self.assertEqual(entry.attrs.last().values.last().value, '')
        self.assertEqual(entry.attrs.last().values.last().referral.id, new_entry.id)

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_without_referral_value(self):
        user = self.admin_login()

        attr_base = EntityAttr.objects.create(name='attr_with_referral',
                                              created_user=user,
                                              type=AttrTypeObj,
                                              parent_entity=self._entity,
                                              is_mandatory=False)
        attr_base.referral.add(self._entity)
        self._entity.attrs.add(attr_base)

        entry = Entry.objects.create(name='entry', schema=self._entity, created_user=user)

        attr = entry.add_attribute_from_base(attr_base, user)
        attr_value = AttributeValue.objects.create(referral=entry,
                                                   created_user=user,
                                                   parent_attr=attr)
        attr.values.add(attr_value)

        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(attr.id), 'type': str(AttrTypeObj),
                 'value': [{'data': '0', 'index': 0}], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(attr.values.count(), 2)
        self.assertEqual(attr.values.last().value, '')

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_to_no_referral(self):
        user = self.admin_login()

        entry = Entry.objects.create(name='entry', schema=self._entity, created_user=user)

        attr = self.make_attr(name='attr',
                              attrtype=AttrTypeObj,
                              created_user=user,
                              parent_entry=entry)
        entry.attrs.add(attr)

        attr_value = AttributeValue.objects.create(referral=entry,
                                                   created_user=user,
                                                   parent_attr=attr)
        attr.values.add(attr_value)

        params = {
            'entry_name': entry.name,
            'attrs': [
                # include blank value
                {'id': str(attr.id), 'type': str(AttrTypeObj), 'value': [], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(attr.values.count(), 2)
        self.assertEqual(attr.values.first(), attr_value)
        self.assertIsNone(attr.values.last().referral)

    @patch('entry.tasks.export_entries.delay', Mock(side_effect=tasks.export_entries))
    def test_get_export(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='ほげ', created_user=user)
        for name in ['foo', 'bar']:
            entity.attrs.add(EntityAttr.objects.create(**{
                'name': name,
                'type': AttrTypeValue['string'],
                'created_user': user,
                'parent_entity': entity,
            }))

        entry = Entry.objects.create(name='fuga', schema=entity, created_user=user)
        entry.complement_attrs(user)
        for attr in entry.attrs.all():
            [attr.add_value(user, x) for x in ['hoge', 'fuga']]

        resp = self.client.get(reverse('entry:export', args=[entity.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {
            'result': 'Succeed in registering export processing. Please check Job list.'
        })

        job = Job.objects.last()
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY.value)
        self.assertEqual(job.status, Job.STATUS['DONE'])
        self.assertEqual(job.text, 'entry_ほげ.yaml')

        obj = yaml.load(job.get_cache())
        self.assertTrue(entity.name in obj)

        self.assertEqual(len(obj[entity.name]), 1)
        entry_data = obj[entity.name][0]
        self.assertTrue(all(['name' in entry_data and 'attrs' in entry_data]))

        self.assertEqual(entry_data['name'], entry.name)
        self.assertEqual(len(entry_data['attrs']), entry.attrs.count())
        self.assertEqual(entry_data['attrs']['foo'], 'fuga')
        self.assertEqual(entry_data['attrs']['bar'], 'fuga')

        resp = self.client.get(reverse('entry:export', args=[entity.id]), {'format': 'CSV'})
        self.assertEqual(resp.status_code, 200)

        # append an unpermitted Attribute
        entity.attrs.add(EntityAttr.objects.create(**{
            'name': 'new_attr',
            'type': AttrTypeValue['string'],
            'created_user': user,
            'parent_entity': entity,
            'is_public': False,
        }))

        # re-login with guest user
        user = self.guest_login()

        resp = self.client.get(reverse('entry:export', args=[entity.id]))
        self.assertEqual(resp.status_code, 200)
        obj = yaml.load(Job.objects.last().get_cache())

        # check permitted attributes exist in the result
        self.assertTrue(all([x in obj['ほげ'][0]['attrs'] for x in ['foo', 'bar']]))

        # check unpermitted attribute doesn't exist in the result
        self.assertFalse('new_attr' in obj['ほげ'][0]['attrs'])

        ###
        # Check the case of canceling job
        ###
        with patch.object(Job, 'is_canceled', return_value=True):
            resp = self.client.get(reverse('entry:export', args=[entity.id]))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {
            'result': 'Succeed in registering export processing. Please check Job list.'
        })

        job = Job.objects.last()
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY.value)
        self.assertEqual(job.text, 'entry_ほげ.yaml')
        with self.assertRaises(OSError) as e:
            raise OSError

        if e.exception.errno == errno.ENOENT:
            job.get_cache()

    @patch('entry.tasks.export_entries.delay', Mock(side_effect=tasks.export_entries))
    def test_get_export_csv_escape(self):
        user = self.admin_login()

        dummy_entity = Entity.objects.create(name='Dummy', created_user=user)
        dummy_entry = Entry(name='D,U"MM"Y', schema=dummy_entity, created_user=user)
        dummy_entry.save()

        CASES = [
            [AttrTypeStr, 'raison,de"tre', '"raison,de""tre"'],
            [AttrTypeObj,  dummy_entry, '"D,U""MM""Y"'],
            [AttrTypeText, "1st line\r\n2nd line", '"1st line' + "\r\n" + '2nd line"'],
            [AttrTypeNamedObj, {"key": dummy_entry}, "\"{'key': 'D,U\"\"MM\"\"Y'}\""],
            [AttrTypeArrStr, ["one", "two", "three"], "\"['one', 'two', 'three']\""],
            [AttrTypeArrObj, [dummy_entry], "\"['D,U\"\"MM\"\"Y']\""],
            [AttrTypeArrNamedObj, [{"key1": dummy_entry}], "\"[{'key1': 'D,U\"\"MM\"\"Y'}]\""]
        ]

        for case in CASES:
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

            resp = self.client.get(reverse('entry:export', args=[test_entity.id]),
                                   {'format': 'CSV'})
            self.assertEqual(resp.status_code, 200)

            content = Job.objects.last().get_cache()
            header = content.splitlines()[0]
            self.assertEqual(header, 'Name,"%s,""ATTR"""' % type_name)

            data = content.replace(header, '', 1).strip()
            self.assertEqual(data, '"%s,""ENTRY""",' % type_name + case[2])

    @patch('entry.tasks.delete_entry.delay', Mock(side_effect=tasks.delete_entry))
    def test_post_delete_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name='fuga', schema=self._entity, created_user=user)
        entry.attrs.add(self.make_attr(name='attr-test',
                                       parent_entry=entry,
                                       created_user=user))

        entry_count = Entry.objects.count()

        resp = self.client.post(reverse('entry:do_delete', args=[entry.id]),
                                json.dumps({}), 'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), entry_count)

        entry = Entry.objects.last()
        self.assertFalse(entry.is_active)
        self.assertFalse(Attribute.objects.get(name__icontains='attr-test_deleted_').is_active)

        # Checks Elasticsearch also removes document of removed entry
        res = self._es.get(index=settings.ES_CONFIG['INDEX'], doc_type='entry', id=entry.id,
                           ignore=[404])
        self.assertFalse(res['found'])

    @patch('entry.tasks.delete_entry.delay', Mock(return_value=None))
    def test_post_delete_entry_with_long_delay(self):
        # This is the case when background processing never be started
        user = self.guest_login()

        # Create an entry to be deleted
        entity = Entity.objects.create(name='Entity', created_user=user)
        entry = Entry.objects.create(name='entry', schema=entity, created_user=user)

        # Send a request to delete an entry
        resp = self.client.post(reverse('entry:do_delete', args=[entry.id]),
                                json.dumps({}), 'application/json')

        # Check that deleted entry's active flag is down
        entry.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(entry.is_active)

    def test_post_delete_entry_without_permission(self):
        user1 = self.guest_login()
        user2 = User(username='nyaa')
        user2.save()

        entity = Entity.objects.create(name='entity', created_user=user1)
        entry = Entry(name='fuga', schema=entity, created_user=user2, is_public=False)
        entry.save()

        entry_count = Entry.objects.count()

        params = {}

        resp = self.client.post(reverse('entry:do_delete', args=[entry.id]),
                                json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 400)

        self.assertEqual(Entry.objects.count(), entry_count)

        entry = Entry.objects.last()
        self.assertTrue(entry.is_active)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_post_create_array_string_attribute(self):
        user = self.admin_login()

        # create a test data set
        entity = Entity.objects.create(name='entity-test',
                                       created_user=user)

        attr_base = EntityAttr.objects.create(name='attr-test',
                                              type=AttrTypeArrStr,
                                              is_mandatory=False,
                                              created_user=user,
                                              parent_entity=self._entity)
        entity.attrs.add(attr_base)

        params = {
            'entry_name': 'entry-test',
            'attrs': [{
                'id': str(attr_base.id),
                'type': str(AttrTypeArrStr),
                'value': [
                    {'data': 'hoge', 'index': 0},
                    {'data': 'fuga', 'index': 1},
                    {'data': 'puyo', 'index': 2},
                ],
                'referral_key': [],
            }],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(AttributeValue.objects.count(), 4)

        entry = Entry.objects.last()
        self.assertEqual(entry.name, 'entry-test')
        self.assertEqual(entry.attrs.count(), 1)

        attr = entry.attrs.last()
        self.assertEqual(attr.name, 'attr-test')
        self.assertEqual(attr.values.count(), 1)

        attr_value = attr.values.last()
        self.assertTrue(attr_value.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT))
        self.assertEqual(attr_value.value, '')
        self.assertIsNone(attr_value.referral)
        self.assertEqual(attr_value.data_array.count(), 3)
        self.assertTrue([x.value == 'hoge' or x.value == 'fuga' or x.value == 'puyo'
                         for x in attr_value.data_array.all()])

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_post_create_array_object_attribute(self):
        user = self.admin_login()

        # create a test data set
        entity = Entity.objects.create(name='entity-test',
                                       created_user=user)

        attr_base = EntityAttr.objects.create(name='attr-ref-test',
                                              created_user=user,
                                              type=AttrTypeArrObj,
                                              parent_entity=self._entity,
                                              is_mandatory=False)
        attr_base.referral.add(self._entity)
        entity.attrs.add(attr_base)

        referral = Entry.objects.create(name='entry0', schema=self._entity, created_user=user)

        params = {
            'entry_name': 'entry-test',
            'attrs': [{
                'id': str(attr_base.id),
                'type': str(AttrTypeArrObj),
                'value': [
                    {'data': str(referral.id), 'index': 0},
                    {'data': str(referral.id), 'index': 1},
                ],
                'referral_key': [],
            }],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(AttributeValue.objects.count(), 3)

        entry = Entry.objects.last()
        self.assertEqual(entry.name, 'entry-test')
        self.assertEqual(entry.attrs.count(), 1)

        attr = entry.attrs.last()
        self.assertEqual(attr.name, 'attr-ref-test')
        self.assertEqual(attr.values.count(), 1)

        attr_value = attr.values.last()
        self.assertTrue(attr_value.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT))
        self.assertEqual(attr_value.value, '')
        self.assertIsNone(attr_value.referral)
        self.assertEqual(attr_value.data_array.count(), 2)
        self.assertTrue(all([x.referral.id == referral.id for x in attr_value.data_array.all()]))

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_post_text_area_value(self):
        user = self.admin_login()

        textattr = EntityAttr.objects.create(name='attr-text',
                                             type=AttrTypeText,
                                             created_user=user,
                                             parent_entity=self._entity)
        self._entity.attrs.add(textattr)

        params = {
            'entry_name': 'entry',
            'attrs': [
                {
                    'id': str(self._entity_attr.id),
                    'type': str(AttrTypeText),
                    'value': [{'data': 'hoge', 'index': 0}],
                    'referral_key': [],
                },
                {
                    'id': str(textattr.id),
                    'type': str(AttrTypeText),
                    'value': [{'data': 'fuga', 'index': 0}],
                    'referral_key': [],
                },
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(Attribute.objects.count(), 2)
        self.assertEqual(AttributeValue.objects.count(), 2)

        entry = Entry.objects.last()
        self.assertEqual(entry.attrs.count(), 2)
        self.assertTrue(any([
            (x.values.last().value == 'hoge' or x.values.last().value == 'fuga')
            for x in entry.attrs.all()
        ]))

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_post_create_just_limit_of_value(self):
        self.admin_login()

        params = {
            'entry_name': 'entry',
            'attrs': [{
                'id': str(self._entity_attr.id),
                'type': str(AttrTypeValue['string']),
                'value': [{'data': 'A' * AttributeValue.MAXIMUM_VALUE_SIZE, 'index': 0}],
                'referral_key': [],
            }],
        }
        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), 1)

        entry = Entry.objects.last()
        self.assertEqual(entry.attrs.count(), 1)
        self.assertEqual(entry.attrs.last().values.count(), 1)
        self.assertEqual(len(entry.attrs.last().values.last().value),
                         AttributeValue.MAXIMUM_VALUE_SIZE)

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_just_limit_of_value(self):
        user = self.admin_login()

        entry = Entry.objects.create(name='entry', created_user=user, schema=self._entity)
        attr = entry.add_attribute_from_base(self._entity_attr, user)

        params = {
            'entry_name': 'entry',
            'attrs': [{
                'id': str(attr.id),
                'type': str(AttrTypeValue['string']),
                'value': [{'data': 'A' * AttributeValue.MAXIMUM_VALUE_SIZE, 'index': 0}],
                'referral_key': [],
            }],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AttributeValue.objects.filter(parent_attr=attr, is_latest=True).count(), 1)
        self.assertEqual(len(attr.values.last().value), AttributeValue.MAXIMUM_VALUE_SIZE)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_post_create_exceeding_limit_of_value(self):
        self.admin_login()

        params = {
            'entry_name': 'entry',
            'attrs': [{
                'id': str(self._entity_attr.id),
                'type': str(AttrTypeValue['string']),
                'value': {
                    'data': ['A' * AttributeValue.MAXIMUM_VALUE_SIZE + 'A'],
                    'index': 0,
                },
                'referral_key': [],
            }],
        }
        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.count(), 0)

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_exceeding_limit_of_value(self):
        user = self.admin_login()

        entry = Entry.objects.create(name='entry', created_user=user, schema=self._entity)
        attr = entry.add_attribute_from_base(self._entity_attr, user)

        params = {
            'entry_name': 'entry',
            'attrs': [{
                'id': str(attr.id),
                'type': str(AttrTypeValue['string']),
                'value': [{'data': 'A' * AttributeValue.MAXIMUM_VALUE_SIZE + 'A', 'index': 0}],
                'referral_key': [],
            }],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(attr.values.count(), 0)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_try_to_create_duplicate_name_of_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name='entry', created_user=user, schema=self._entity)
        entry.add_attribute_from_base(self._entity_attr, user)

        params = {
            'entry_name': 'entry',
            'attrs': [
                {
                    'id': str(self._entity_attr.id),
                    'type': str(AttrTypeStr),
                    'value': [{'data': 'hoge', 'index': 0}],
                    'referral_key': [],
                },
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 400)

    def test_try_to_edit_duplicate_name_of_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name='entry', created_user=user, schema=self._entity)
        entry.add_attribute_from_base(self._entity_attr, user)

        dup_entry = Entry.objects.create(name='dup_entry', created_user=user, schema=self._entity)
        dup_attr = Attribute.objects.create(name=self._entity_attr.name,
                                            schema=self._entity_attr,
                                            created_user=user,
                                            parent_entry=entry)

        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(dup_attr.id), 'value': [{'data': 'hoge', 'index': 0}],
                 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[dup_entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 400)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_make_entry_with_unpermitted_params(self):
        user = self.admin_login()

        # update ACL of EntityAttr
        attr = EntityAttr.objects.create(name='newattr',
                                         type=AttrTypeStr,
                                         created_user=user,
                                         parent_entity=self._entity)
        self._entity.attrs.add(attr)

        self._entity_attr.is_mandatory = False
        self._entity_attr.is_public = False
        self._entity_attr.default_permission = ACLType.Nothing.id
        self._entity_attr.save()

        self.guest_login()

        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(self._entity_attr.id), 'type': str(AttrTypeStr),
                 'value': [{'data': 'hoge', 'index': 0}], 'referral_key': []},
                {'id': str(attr.id), 'type': str(AttrTypeStr),
                 'value': [{'data': 'fuga', 'index': 0}], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        # checks that Entry object is created with only permitted Attributes
        entry = Entry.objects.last()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.name, 'entry')
        self.assertEqual(entry.attrs.count(), 1)
        self.assertEqual(entry.attrs.last().schema, attr)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_get_available_attrs(self):
        admin = self.admin_login()

        entity = Entity.objects.create(name='entity', created_user=admin)

        attrs = []
        for index, permission in enumerate([ACLType.Readable, ACLType.Writable]):
            attr = EntityAttr.objects.create(name='attr%d' % index,
                                             type=AttrTypeStr,
                                             created_user=admin,
                                             parent_entity=entity,
                                             is_public=False,
                                             default_permission=permission.id)
            entity.attrs.add(attr)
            attrs.append(attr)

        params = {
            'entry_name': 'entry1',
            'attrs': [
                {'id': str(attrs[0].id), 'type': str(AttrTypeStr),
                 'value': [{'data': 'hoge', 'index': 0}], 'referral_key': []},
                {'id': str(attrs[1].id), 'type': str(AttrTypeStr),
                 'value': [{'data': 'fuga', 'index': 0}], 'referral_key': []},
            ],
        }

        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        # switch to guest user
        user = self.guest_login()

        entry = Entry.objects.get(name='entry1')
        self.assertEqual(len(entry.get_available_attrs(admin)), 2)
        self.assertEqual(len(entry.get_available_attrs(user)), 2)
        self.assertEqual(len(entry.get_available_attrs(user, ACLType.Writable)), 1)
        self.assertEqual(entry.get_available_attrs(user, ACLType.Writable)[0]['name'], 'attr1')

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_create_and_edit_entry_that_has_boolean_attr(self):
        admin = self.admin_login()

        entity = Entity.objects.create(name='entity', created_user=admin)
        entity_attr = EntityAttr.objects.create(name='attr_bool',
                                                type=AttrTypeValue['boolean'],
                                                parent_entity=entity,
                                                created_user=admin)
        entity.attrs.add(entity_attr)

        # creates entry that has a parameter which is typed boolean
        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(entity_attr.id), 'type': str(AttrTypeValue['boolean']),
                 'value': [{'data': True, 'index': 0}], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        # get entry which is created in here
        entry = Entry.objects.get(name='entry', schema=entity)

        self.assertEqual(entry.attrs.count(), 1)
        self.assertIsNotNone(entry.attrs.last().get_latest_value())
        self.assertTrue(entry.attrs.last().get_latest_value().boolean)

        # edit entry to update the value of attribute 'attr_bool'
        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(entry.attrs.get(name='attr_bool').id),
                 'type': str(AttrTypeValue['boolean']), 'value': [{'data': False, 'index': 0}],
                 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        # checks AttributeValue which is specified to update
        self.assertEqual(entry.attrs.last().values.count(), 2)
        self.assertFalse(entry.attrs.last().get_latest_value().boolean)

    def test_post_create_entry_without_mandatory_param(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='Entity', is_public=False, created_user=user)
        attr_base = EntityAttr.objects.create(name='attr',
                                              type=AttrTypeStr,
                                              is_mandatory=True,
                                              parent_entity=entity,
                                              created_user=user)
        entity.attrs.add(attr_base)

        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(attr_base.id), 'type': str(AttrTypeStr), 'value': [],
                 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Attribute.objects.count(), 0)
        self.assertEqual(AttributeValue.objects.count(), 0)

    def test_post_edit_entry_without_mandatory_param(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='Entity', is_public=False, created_user=user)
        attr_base = EntityAttr.objects.create(name='attr',
                                              type=AttrTypeStr,
                                              is_mandatory=True,
                                              parent_entity=entity,
                                              created_user=user)
        entity.attrs.add(attr_base)

        entry = Entry.objects.create(name='Entry', schema=entity, created_user=user)
        entry.complement_attrs(user)

        params = {
            'entry_name': 'Updated Entry',
            'attrs': [
                {'id': str(entry.attrs.get(name='attr').id), 'type': str(AttrTypeStr), 'value': [],
                 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.get(id=entry.id).name, 'Entry')

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    @patch('entry.tasks.delete_entry.delay', Mock(side_effect=tasks.delete_entry))
    def test_referred_entry_cache(self):
        user = self.admin_login()

        ref_entity = Entity.objects.create(name='referred_entity', created_user=user)

        ref_entry1 = Entry.objects.create(name='referred1', schema=ref_entity, created_user=user)
        ref_entry2 = Entry.objects.create(name='referred2', schema=ref_entity, created_user=user)
        ref_entry3 = Entry.objects.create(name='referred3', schema=ref_entity, created_user=user)

        entity = Entity.objects.create(name='entity', created_user=user)
        entity.attrs.add(EntityAttr.objects.create(name='ref',
                                                   type=AttrTypeValue['object'],
                                                   parent_entity=entity,
                                                   created_user=user))
        entity.attrs.add(EntityAttr.objects.create(name='arr_ref',
                                                   type=AttrTypeValue['array_object'],
                                                   parent_entity=entity,
                                                   created_user=user))

        # set entity that target each attributes refer to
        [x.referral.add(ref_entity) for x in entity.attrs.all()]

        params = {
            'entry_name': 'entry',
            'attrs': [
                {
                    'id': str(entity.attrs.get(name='ref').id),
                    'type': str(AttrTypeValue['object']),
                    'value': [
                        {'data': str(ref_entry1.id), 'index': 0},
                    ],
                    'referral_key': [],
                },
                {
                    'id': str(entity.attrs.get(name='arr_ref').id),
                    'type': str(AttrTypeValue['array_object']),
                    'value': [
                        {'data': str(ref_entry1.id), 'index': 0},
                        {'data': str(ref_entry2.id), 'index': 1},
                    ],
                    'referral_key': [],
                },
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        # checks referred_object cache is set
        entry = Entry.objects.get(name='entry')

        self.assertEqual(list(ref_entry1.get_referred_objects()), [entry])
        self.assertEqual(list(ref_entry2.get_referred_objects()), [entry])
        self.assertEqual(list(ref_entry3.get_referred_objects()), [])
        self.assertEqual(ref_entry1.get_referred_objects().count(), 1)
        self.assertEqual(ref_entry2.get_referred_objects().count(), 1)

        # checks referred_object cache will be updated by unrefering
        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(entry.attrs.get(name='ref').id), 'type': str(AttrTypeValue['object']),
                 'value': [], 'referral_key': []},
                {'id': str(entry.attrs.get(name='arr_ref').id),
                 'type': str(AttrTypeValue['array_object']), 'value': [], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(list(ref_entry1.get_referred_objects()), [])
        self.assertEqual(list(ref_entry2.get_referred_objects()), [])
        self.assertEqual(list(ref_entry3.get_referred_objects()), [])

        # checks referred_object cache will be updated by the edit processing
        params = {
            'entry_name': 'entry',
            'attrs': [
                {
                    'id': str(entry.attrs.get(name='ref').id),
                    'type': str(AttrTypeValue['object']),
                    'value': [
                        {'data': str(ref_entry2.id), 'index': 0},
                    ],
                    'referral_key': [],
                },
                {
                    'id': str(entry.attrs.get(name='arr_ref').id),
                    'type': str(AttrTypeValue['array_object']),
                    'value': [
                        {'data': str(ref_entry2.id), 'index': 0},
                        {'data': str(ref_entry3.id), 'index': 1},
                    ],
                    'referral_key': [],
                },
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 200)

        # checks referred_object cache is updated by changing referring
        self.assertEqual(list(ref_entry1.get_referred_objects()), [])
        self.assertEqual(list(ref_entry2.get_referred_objects()), [entry])
        self.assertEqual(list(ref_entry3.get_referred_objects()), [entry])
        self.assertEqual(ref_entry2.get_referred_objects().count(), 1)
        self.assertEqual(ref_entry3.get_referred_objects().count(), 1)

        # delete referring entry and make sure that
        # the cahce of referred_entry of ref_entry is reset
        resp = self.client.post(reverse('entry:do_delete', args=[entry.id]),
                                json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(ref_entry1.get_referred_objects()), [])
        self.assertEqual(list(ref_entry2.get_referred_objects()), [])
        self.assertEqual(list(ref_entry3.get_referred_objects()), [])

        # checks jobs were created
        self.assertEqual(Job.objects.filter(user=user).count(), 4)

        job = Job.objects.filter(user=user, operation=JobOperation.DELETE_ENTRY.value)
        self.assertEqual(job.count(), 1)

        # checks each parameters of the job are as expected
        obj = job.first()
        self.assertEqual(obj.target.id, entry.id)
        self.assertEqual(obj.target_type, Job.TARGET_ENTRY)
        self.assertEqual(obj.status, Job.STATUS['DONE'])

        # checking for the cases of sending invalid referral parameters
        requests = [
            {'name': 'entry_with_zero1', 'value': '0'},
            {'name': 'entry_with_zero2', 'value': ''},
        ]

        for req in requests:
            params = {
                'entry_name': req['name'],
                'attrs': [
                    {
                        'id': str(entity.attrs.get(name='ref').id),
                        'type': str(AttrTypeValue['object']),
                        'value': [
                            {'data': req['value'], 'index': 0},
                        ],
                        'referral_key': [],
                    },
                    {
                        'id': str(entity.attrs.get(name='arr_ref').id),
                        'type': str(AttrTypeValue['array_object']),
                        'value': [
                            {'data': req['value'], 'index': 0},
                        ],
                        'referral_key': [],
                    },
                ],
            }
            resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                    json.dumps(params),
                                    'application/json')

            self.assertEqual(resp.status_code, 200)

            entry = Entry.objects.get(name=req['name'])
            attr_ref = entry.attrs.get(schema__name='ref')
            entry.attrs.get(schema__name='arr_ref')

            self.assertIsNone(attr_ref.get_latest_value().referral)
            self.assertEqual(attr_ref.get_latest_value().data_array.count(), 0)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_create_entry_with_named_ref(self):
        user = self.admin_login()

        ref_entity = Entity.objects.create(name='referred_entity', created_user=user)
        ref_entry = Entry.objects.create(name='referred_entry', created_user=user,
                                         schema=ref_entity)

        entity = Entity.objects.create(name='entity', created_user=user)
        new_attr_params = {
            'name': 'named_ref',
            'type': AttrTypeValue['named_object'],
            'created_user': user,
            'parent_entity': entity,
        }
        attr_base = EntityAttr.objects.create(**new_attr_params)
        attr_base.referral.add(ref_entity)

        entity.attrs.add(attr_base)

        # try to create with empty params
        params = {
            'entry_name': 'new_entry1',
            'attrs': [{
                'id': str(attr_base.id),
                'type': str(AttrTypeValue['named_object']),
                'referral_key': [],
                'value': [],
            }],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]), json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(name='new_entry1')

        # An AttributeValue will be created at the creating processing even though
        # the value is empty, but except for invalid one.
        self.assertEqual(entry.attrs.get(name='named_ref').values.count(), 1)
        self.assertIsNone(entry.attrs.get(name='named_ref').values.first().referral)

        # try to create only with value which is a reference for other entry
        params = {
            'entry_name': 'new_entry2',
            'attrs': [{
                'id': str(attr_base.id),
                'type': str(AttrTypeValue['named_object']),
                'value': [{'data': str(ref_entry.id), 'index': 0}],
                'referral_key': [],
            }],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]), json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(name='new_entry2')
        self.assertEqual(entry.attrs.get(name='named_ref').values.count(), 1)
        self.assertEqual(entry.attrs.get(name='named_ref').values.last().value, '')
        self.assertEqual(entry.attrs.get(name='named_ref').values.last().referral.id, ref_entry.id)

        # try to create only with referral_key
        params = {
            'entry_name': 'new_entry3',
            'attrs': [{
                'id': str(attr_base.id),
                'type': str(AttrTypeValue['named_object']),
                'value': [],
                'referral_key': [{'data': 'hoge', 'index': 0}],
            }],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]), json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(name='new_entry3')
        self.assertEqual(entry.attrs.get(name='named_ref').values.count(), 1)
        self.assertEqual(entry.attrs.get(name='named_ref').values.last().value, 'hoge')
        self.assertEqual(entry.attrs.get(name='named_ref').values.last().referral, None)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_create_entry_with_array_named_ref(self):
        user = self.admin_login()

        ref_entity = Entity.objects.create(name='referred_entity', created_user=user)
        ref_entry = Entry.objects.create(name='referred_entry', created_user=user,
                                         schema=ref_entity)

        entity = Entity.objects.create(name='entity', created_user=user)
        new_attr_params = {
            'name': 'arr_named_ref',
            'type': AttrTypeValue['array_named_object'],
            'created_user': user,
            'parent_entity': entity,
        }
        attr_base = EntityAttr.objects.create(**new_attr_params)
        attr_base.referral.add(ref_entity)

        entity.attrs.add(attr_base)

        params = {
            'entry_name': 'new_entry',
            'attrs': [{
                'id': str(attr_base.id),
                'type': str(AttrTypeValue['array_named_object']),
                'value': [
                    {'data': str(ref_entry.id), 'index': 0},
                    {'data': str(ref_entry.id), 'index': 1},
                ],
                'referral_key': [
                    {'data': 'hoge', 'index': 1},
                    {'data': 'fuga', 'index': 2},
                ],
            }],
        }

        resp = self.client.post(reverse('entry:do_create', args=[entity.id]), json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(name='new_entry')
        self.assertEqual(entry.attrs.get(name='arr_named_ref').values.count(), 1)

        attrv = entry.attrs.get(name='arr_named_ref').values.last()
        self.assertTrue(attrv.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT))
        self.assertEqual(attrv.data_array.count(), 3)

        self.assertEqual(attrv.data_array.all()[0].value, '')
        self.assertEqual(attrv.data_array.all()[0].referral.id, ref_entry.id)

        self.assertEqual(attrv.data_array.all()[1].value, 'hoge')
        self.assertEqual(attrv.data_array.all()[1].referral.id, ref_entry.id)

        self.assertEqual(attrv.data_array.all()[2].value, 'fuga')
        self.assertEqual(attrv.data_array.all()[2].referral, None)

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_edit_entry_with_named_ref(self):
        user = self.admin_login()

        ref_entity = Entity.objects.create(name='referred_entity', created_user=user)
        ref_entry = Entry.objects.create(name='referred_entry', created_user=user,
                                         schema=ref_entity)

        entity = Entity.objects.create(name='entity', created_user=user)

        attr_base = EntityAttr.objects.create(**{
            'name': 'named_ref',
            'type': AttrTypeValue['named_object'],
            'created_user': user,
            'parent_entity': entity,
        })
        attr_base.referral.add(ref_entity)

        entity.attrs.add(attr_base)

        entry = Entry.objects.create(name='entry', created_user=user, schema=entity)
        entry.complement_attrs(user)

        attr = entry.attrs.get(name='named_ref')
        attr.add_value(user, {'id': ref_entry, 'name': 'hoge'})

        # try to update with same data (expected not to be updated)
        params = {
            'entry_name': 'updated_entry',
            'attrs': [{
                'id': str(entry.attrs.get(name='named_ref').id),
                'type': str(AttrTypeValue['named_object']),
                'value': [{'data': str(ref_entry.id), 'index': 0}],
                'referral_key': [{'data': 'hoge', 'index': 0}],
            }],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]), json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        updated_entry = Entry.objects.get(id=entry.id)
        self.assertEqual(updated_entry.name, 'updated_entry')
        self.assertEqual(updated_entry.attrs.get(name='named_ref').values.count(), 1)

        # try to update with different data (expected to be updated)
        ref_entry2 = Entry.objects.create(name='referred_entry2', created_user=user,
                                          schema=ref_entity)
        params = {
            'entry_name': 'updated_entry',
            'attrs': [{
                'id': str(entry.attrs.get(name='named_ref').id),
                'type': str(AttrTypeValue['named_object']),
                'value': [{'data': str(ref_entry2.id), 'index': 0}],
                'referral_key': [{'data': 'fuga', 'index': 0}],
            }],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]), json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        updated_entry = Entry.objects.get(id=entry.id)
        self.assertEqual(updated_entry.attrs.get(name='named_ref').values.count(), 2)
        self.assertEqual(updated_entry.attrs.get(name='named_ref').values.last().value, 'fuga')
        self.assertEqual(updated_entry.attrs.get(name='named_ref').values.last().referral.id,
                         ref_entry2.id)

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_edit_entry_with_array_named_ref(self):
        user = self.admin_login()

        ref_entity = Entity.objects.create(name='referred_entity', created_user=user)
        ref_entry = Entry.objects.create(name='referred_entry', created_user=user,
                                         schema=ref_entity)

        entity = Entity.objects.create(name='entity', created_user=user)
        new_attr_params = {
            'name': 'arr_named_ref',
            'type': AttrTypeValue['array_named_object'],
            'created_user': user,
            'parent_entity': entity,
        }
        attr_base = EntityAttr.objects.create(**new_attr_params)
        attr_base.referral.add(ref_entity)

        entity.attrs.add(attr_base)

        # create an Entry associated to the 'entity'
        entry = Entry.objects.create(name='entry', created_user=user, schema=entity)
        entry.complement_attrs(user)

        attr = entry.attrs.get(name='arr_named_ref')
        self.assertTrue(attr.is_updated([{'id': ref_entry.id}]))

        attrv = attr.add_value(user, [{
            'name': 'key_%d' % i,
            'id': Entry.objects.create(name='r_%d' % i, created_user=user, schema=ref_entity)
        } for i in range(3)])

        # try to update with same data (expected not to be updated)
        old_attrv_count = attr.values.count()
        r_entries = [x.referral.id for x in attrv.data_array.all()]
        params = {
            'entry_name': 'updated_entry',
            'attrs': [{
                'id': str(entry.attrs.get(name='arr_named_ref').id),
                'type': str(AttrTypeValue['array_named_object']),
                'value': [{'data': str(r), 'index': i} for i, r in enumerate(r_entries)],
                'referral_key': [{'data': 'key_%d' % i, 'index': i} for i in range(0, 3)],
            }],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]), json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        updated_entry = Entry.objects.get(id=entry.id)
        self.assertEqual(updated_entry.name, 'updated_entry')
        self.assertEqual(updated_entry.attrs.get(name='arr_named_ref').values.count(),
                         old_attrv_count)

        # try to update with different data (expected to be updated)
        params = {
            'entry_name': 'updated_entry',
            'attrs': [{
                'id': str(entry.attrs.get(name='arr_named_ref').id),
                'type': str(AttrTypeValue['array_named_object']),
                'value': [
                    {'data': r_entries[1], 'index': 1},
                    {'data': r_entries[2], 'index': 2},
                ],
                'referral_key': [{'data': 'hoge_%d' % i, 'index': i} for i in range(0, 2)],
            }],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]), json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        updated_entry = Entry.objects.get(id=entry.id)
        self.assertEqual(updated_entry.attrs.get(name='arr_named_ref').values.count(),
                         old_attrv_count + 1)

        new_attrv = updated_entry.attrs.get(name='arr_named_ref').values.last()
        self.assertEqual(new_attrv.data_array.count(), 3)

        contexts = [{
            'name': x.value,
            'referral': x.referral.id if x.referral else None,
        } for x in new_attrv.data_array.all()]

        self.assertTrue({'name': 'hoge_0', 'referral': None} in contexts)
        self.assertTrue({'name': 'hoge_1', 'referral': r_entries[1]} in contexts)
        self.assertTrue({'name': '', 'referral': r_entries[2]} in contexts)

        # try to update with same data but order is different (expected not to be updated)
        params = {
            'entry_name': 'updated_entry',
            'attrs': [{
                'id': str(entry.attrs.get(name='arr_named_ref').id),
                'type': str(AttrTypeValue['array_named_object']),
                'value': [
                    {'data': r_entries[2], 'index': 2},
                    {'data': r_entries[1], 'index': 1},
                ],
                'referral_key': [
                    {'data': 'hoge_1', 'index': 1},
                    {'data': 'hoge_0', 'index': 0},
                ],
            }],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]), json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        updated_entry = Entry.objects.get(id=entry.id)
        self.assertEqual(updated_entry.attrs.get(name='arr_named_ref').values.count(),
                         old_attrv_count + 1)

    def test_get_copy_with_invalid_entry(self):
        self.admin_login()

        resp = self.client.get(reverse('entry:index', args=[9999]))
        self.assertEqual(resp.status_code, 400)

    def test_get_copy_with_valid_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name='entry', created_user=user, schema=self._entity)

        resp = self.client.get(reverse('entry:copy', args=[entry.id]))
        self.assertEqual(resp.status_code, 200)

    def test_post_copy_without_mandatory_parameter(self):
        user = self.admin_login()

        entry = Entry.objects.create(name='entry', created_user=user, schema=self._entity)

        resp = self.client.post(reverse('entry:do_copy', args=[entry.id]),
                                json.dumps({}), 'application/json')
        self.assertEqual(resp.status_code, 400)

    def test_post_copy_with_invalid_entry(self):
        self.admin_login()

        params = {
            'entries': 'foo\nbar\nbaz',
        }
        resp = self.client.post(reverse('entry:do_copy', args=[9999]),
                                json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 400)

    @patch('entry.tasks.copy_entry.delay', Mock(side_effect=tasks.copy_entry))
    def test_post_copy_with_valid_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name='entry', created_user=user, schema=self._entity)
        entry.complement_attrs(user)

        entry_count = Entry.objects.filter(schema=self._entity).count()

        params = {
            # 'foo' is duplicated and 'entry' is already created
            'entries': 'foo\nbar\nbaz\nfoo\nentry',
        }
        resp = self.client.post(reverse('entry:do_copy', args=[entry.id]),
                                json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertTrue('results' in resp.json())

        self.assertEqual(Entry.objects.filter(schema=self._entity).count(), entry_count + 3)
        for name in ['foo', 'bar', 'baz']:
            self.assertEqual(Entry.objects.filter(name=name, schema=self._entity).count(), 1)

        results = resp.json()['results']
        self.assertEqual(len(results), 5)
        self.assertEqual(len([x for x in results if x['status'] == 'fail']), 2)
        self.assertEqual(len([x for x in results if x['status'] == 'success']), 3)

        # checks copied entries were registered to the Elasticsearch
        res = self._es.indices.stats(index=settings.ES_CONFIG['INDEX'])
        self.assertEqual(res['_all']['total']['segments']['count'], 3)

        # checks jobs were created
        self.assertEqual(Job.objects.filter(user=user).count(), 3)

        jobs = Job.objects.filter(user=user, operation=JobOperation.COPY_ENTRY.value)

        self.assertEqual(jobs.count(), 3)
        for obj in jobs.all():
            self.assertTrue(any([obj.target.name == x for x in ['foo', 'bar', 'baz']]))
            self.assertEqual(obj.text, 'original entry: %s' % entry.name)
            self.assertEqual(obj.target_type, Job.TARGET_ENTRY)
            self.assertEqual(obj.status, Job.STATUS['DONE'])
            self.assertNotEqual(obj.created_at, obj.updated_at)
            self.assertTrue((obj.updated_at - obj.created_at).total_seconds() > 0)

    @patch('entry.tasks.copy_entry.delay', Mock(side_effect=tasks.copy_entry))
    def test_post_copy_after_job_creating(self):
        user = self.admin_login()
        entry = Entry.objects.create(name='entry', created_user=user, schema=self._entity)

        # creating a job to copy entry
        params = {
            # A job of creating entry 'foo' is already created
            'entries': 'foo',
        }
        job = Job.new_copy(user, entry, text='', params={'new_name': 'foo', 'post_data': params})
        resp = self.client.post(reverse('entry:do_copy', args=[entry.id]),
                                json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 200)

        # check that creating foo would be failed
        results = resp.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 'fail')
        self.assertEqual(results[0]['msg'],
                         'There is another job that targets same name(foo) is existed')

        # check job won't be created by this request
        self.assertFalse(Job.objects.filter(Q(target=entry) & ~Q(id=job.id)).exists())

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_create_entry_with_group_attr(self):
        admin = self.admin_login()

        group = Group.objects.create(name='group')
        admin.groups.add(group)

        entity = Entity.objects.create(name='entity', created_user=admin)
        entity.attrs.add(EntityAttr.objects.create(**{
            'name': 'attr_group',
            'type': AttrTypeValue['group'],
            'created_user': admin,
            'parent_entity': entity,
        }))

        params = {
            'entry_name': 'entry',
            'attrs': [{
                'id': str(entity.attrs.first().id),
                'type': str(AttrTypeValue['group']),
                'value': [{'index': 0, 'data': str(group.id)}],
            }],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(name='entry', schema=entity)
        self.assertEqual(entry.attrs.count(), 1)

        attrv = entry.attrs.first().get_latest_value()
        self.assertIsNotNone(attrv)
        self.assertEqual(attrv.value, str(group.id))
        self.assertEqual(attrv.data_type, AttrTypeValue['group'])

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_edit_entry_with_group_attr(self):
        admin = self.admin_login()

        for index in range(0, 10):
            group = Group.objects.create(name='group-%d' % (index))
            admin.groups.add(group)

        entity = Entity.objects.create(name='entity', created_user=admin)
        entity.attrs.add(EntityAttr.objects.create(**{
            'name': 'attr_group',
            'type': AttrTypeValue['group'],
            'created_user': admin,
            'parent_entity': entity,
        }))

        entry = Entry.objects.create(name='entry', schema=entity, created_user=admin)
        entry.complement_attrs(admin)

        attr = entry.attrs.first()
        attr.add_value(admin, str(Group.objects.get(name='group-0').id))

        # Specify a value which is same with the latest one, then AirOne do not update it.
        attrv_count = AttributeValue.objects.count()
        params = {
            'entry_name': 'entry',
            'attrs': [{
                'id': str(attr.id),
                'type': str(AttrTypeValue['group']),
                'value': [{'index': 0, 'data': str(Group.objects.get(name='group-0').id)}],
            }],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AttributeValue.objects.count(), attrv_count)

        # Specify a different value to add a new AttributeValue
        params = {
            'entry_name': 'entry',
            'attrs': [{
                'id': str(attr.id),
                'type': str(AttrTypeValue['group']),
                'value': [{'index': 0, 'data': str(Group.objects.get(name='group-1').id)}],
            }],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AttributeValue.objects.count(), attrv_count + 1)

        attrv = attr.get_latest_value()
        self.assertIsNotNone(attrv)
        self.assertEqual(attrv.value, str(Group.objects.get(name='group-1').id))

    @patch('entry.tasks.import_entries.delay', Mock(side_effect=tasks.import_entries))
    def test_import_entry(self):
        user = self.guest_login()

        # prepare to Entity and Entries which importing data refers to
        ref_entity = Entity.objects.create(name='RefEntity', created_user=user)
        ref_entry = Entry.objects.create(name='ref', created_user=user, schema=ref_entity)
        group = Group.objects.create(name='group')

        entity = Entity.objects.create(name='Entity', created_user=user)
        attr_info = {
            'str': {'type': AttrTypeValue['string']},
            'obj': {'type': AttrTypeValue['object']},
            'grp': {'type': AttrTypeValue['group']},
            'name': {'type': AttrTypeValue['named_object']},
            'bool': {'type': AttrTypeValue['boolean']},
            'date': {'type': AttrTypeValue['date']},
            'arr1': {'type': AttrTypeValue['array_string']},
            'arr2': {'type': AttrTypeValue['array_object']},
            'arr3': {'type': AttrTypeValue['array_named_object']},
        }
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(name=attr_name,
                                             type=info['type'],
                                             created_user=user,
                                             parent_entity=entity)

            if info['type'] & AttrTypeValue['object']:
                attr.referral.add(ref_entity)

            entity.attrs.add(attr)

        # try to import data which has invalid data structure
        for index in range(3):
            fp = self.open_fixture_file('invalid_import_data%d.yaml' % index)
            resp = self.client.post(reverse('entry:do_import', args=[entity.id]), {'file': fp})
            self.assertEqual(resp.status_code, 400)

        # import data from test file
        fp = self.open_fixture_file('import_data01.yaml')
        resp = self.client.post(reverse('entry:do_import', args=[entity.id]), {'file': fp})

        # check the import is success
        self.assertEqual(resp.status_code, 303)
        self.assertTrue(Entry.objects.filter(name='Entry', schema=entity))

        # check job status
        job = Job.objects.filter(target=entity).last()
        self.assertEqual(job.status, Job.STATUS['DONE'])
        self.assertEqual(job.text, '')

        entry = Entry.objects.get(name='Entry', schema=entity)
        checklist = [
            {'attr': 'str', 'checker': lambda x: x.value == 'foo'},
            {'attr': 'obj', 'checker': lambda x: x.referral.id == ref_entry.id},
            {'attr': 'grp', 'checker': lambda x: x.value == str(group.id)},
            {'attr': 'name',
             'checker': lambda x: x.value == 'foo' and x.referral.id == ref_entry.id},
            {'attr': 'bool', 'checker': lambda x: x.boolean is False},
            {'attr': 'date', 'checker': lambda x: x.date == date(2018, 12, 31)},
            {'attr': 'arr1', 'checker': lambda x: x.data_array.count() == 3},
            {'attr': 'arr2',
             'checker': lambda x: x.data_array.count() == 1 and
             x.data_array.first().referral.id == ref_entry.id},
            {'attr': 'arr3',
             'checker': lambda x: x.data_array.count() == 1 and
             x.data_array.first().referral.id == ref_entry.id},
        ]
        for info in checklist:
            attr = entry.attrs.get(name=info['attr'])
            attrv = attr.get_latest_value()

            self.assertIsNotNone(attrv)
            self.assertTrue(info['checker'](attrv))

        # checks that created entry was registered to the Elasticsearch
        res = self._es.get(index=settings.ES_CONFIG['INDEX'], doc_type='entry', id=entry.id)
        self.assertTrue(res['found'])

        # set permission to prohibit update and check the result of job
        entity.is_public = False
        entity.save(update_fields=['is_public'])

        # check the import is success but job was failed
        fp = self.open_fixture_file('import_data01.yaml')
        resp = self.client.post(reverse('entry:do_import', args=[entity.id]), {'file': fp})

        self.assertEqual(resp.status_code, 303)
        job = Job.objects.filter(target=entity).last()
        self.assertEqual(job.status, Job.STATUS['ERROR'])
        self.assertEqual(
            job.text,
            'Permission denied to import. You need Writable permission for "%s"' % entity.name)

    @patch('entry.tasks.import_entries.delay', Mock(side_effect=tasks.import_entries))
    def test_import_entry_with_changing_entity_attr(self):
        user = self.admin_login()

        # prepare to Entity and Entries which importing data refers to
        ref_entity = Entity.objects.create(name='RefEntity', created_user=user)
        Entry.objects.create(name='ref', created_user=user, schema=ref_entity)
        Group.objects.create(name='group')

        entity = Entity.objects.create(name='Entity', created_user=user)
        attr_info = {
            'str (before changing)': {'type': AttrTypeValue['string']},
            'obj': {'type': AttrTypeValue['object']},
            'grp': {'type': AttrTypeValue['group']},
            'name': {'type': AttrTypeValue['named_object']},
            'bool': {'type': AttrTypeValue['boolean']},
            'date': {'type': AttrTypeValue['date']},
            'arr1': {'type': AttrTypeValue['array_string']},
            'arr2': {'type': AttrTypeValue['array_object']},
            'arr3': {'type': AttrTypeValue['array_named_object']},
        }
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(name=attr_name,
                                             type=info['type'],
                                             created_user=user,
                                             parent_entity=entity)

            if info['type'] & AttrTypeValue['object']:
                attr.referral.add(ref_entity)

            entity.attrs.add(attr)

        # Change a name of EntityAttr 'str (before changing)' to 'str'
        entity_attr = EntityAttr.objects.get(name='str (before changing)', parent_entity=entity)
        entity_attr.name = 'str'
        entity_attr.save()

        # import data from test file
        fp = self.open_fixture_file('import_data01.yaml')
        resp = self.client.post(reverse('entry:do_import', args=[entity.id]), {'file': fp})

        # check the import is success
        self.assertEqual(resp.status_code, 303)

        entry = Entry.objects.get(name='Entry', schema=entity)
        self.assertEqual(entry.attrs.get(schema=entity_attr).get_latest_value().value, 'foo')

        # check array_string value is set correctly
        attrv = entry.attrs.get(name='arr1').get_latest_value()
        self.assertEqual(attrv.data_type, AttrTypeValue['array_string'])
        self.assertEqual(attrv.data_array.count(), 3)
        self.assertTrue(all([x.parent_attrv == attrv for x in attrv.data_array.all()]))

        # check imported data was registered to the ElasticSearch
        res = self._es.indices.stats(index=settings.ES_CONFIG['INDEX'])
        self.assertEqual(res['_all']['total']['segments']['count'], 1)

        res = self._es.get(index=settings.ES_CONFIG['INDEX'], doc_type='entry', id=entry.id)
        self.assertTrue(res['found'])

    @skip('When a file which is encodeed by non UTF-8, django-test-client fails encoding')
    def test_import_entry_by_multi_encoded_files(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='Entity', created_user=user)
        entity.attrs.add(EntityAttr.objects.create(name='str',
                                                   type=AttrTypeValue['string'],
                                                   created_user=user,
                                                   parent_entity=entity))

        for encoding in ['UTF-8', 'Shift-JIS', 'EUC-JP']:
            fp = self.open_fixture_file('import_data_%s.yaml' % encoding)
            resp = self.client.post(reverse('entry:do_import', args=[entity.id]), {'file': fp})

            # check the import is success
            self.assertEqual(resp.status_code, 303)

        self.assertEqual(Entry.objects.filter(name__iregex=r'えんとり*').coiunt(), 3)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_create_and_edit_entry_that_has_date_attr(self):
        admin = self.admin_login()

        entity = Entity.objects.create(name='entity', created_user=admin)
        entity_attr = EntityAttr.objects.create(name='attr_date',
                                                type=AttrTypeValue['date'],
                                                parent_entity=entity,
                                                created_user=admin)
        entity.attrs.add(entity_attr)

        # creates entry that has a parameter which is typed date
        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(entity_attr.id), 'type': str(AttrTypeValue['date']),
                 'value': [{'data': '2018-12-31', 'index': 0}], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        # get entry which is created in here
        entry = Entry.objects.get(name='entry', schema=entity)

        self.assertEqual(entry.attrs.count(), 1)
        self.assertIsNotNone(entry.attrs.last().get_latest_value())
        self.assertEqual(entry.attrs.last().get_latest_value().date, date(2018, 12, 31))

        # edit entry to update the value of attribute 'attr_date'
        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(entry.attrs.get(name='attr_date').id),
                 'type': str(AttrTypeValue['date']), 'value': [{'data': '2019-1-1', 'index': 0}],
                 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        # checks AttributeValue which is specified to update
        self.assertEqual(entry.attrs.last().values.count(), 2)
        self.assertEqual(entry.attrs.last().get_latest_value().date, date(2019, 1, 1))

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_create_invalid_date_param(self):
        admin = self.admin_login()

        entity = Entity.objects.create(name='entity', created_user=admin)
        entity_attr = EntityAttr.objects.create(name='attr_date',
                                                type=AttrTypeValue['date'],
                                                parent_entity=entity,
                                                created_user=admin)
        entity.attrs.add(entity_attr)

        # creates entry that has a invalid format parameter which is typed date
        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(entity_attr.id), 'type': str(AttrTypeValue['date']),
                 'value': [{'data': '2018-13-30', 'index': 0}], 'referral_key': []},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 400)

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_edit_invalid_date_param(self):
        INITIAL_DATE = date.today()
        admin = self.admin_login()

        entity = Entity.objects.create(name='entity', created_user=admin)
        entity_attr = EntityAttr.objects.create(name='attr_date',
                                                type=AttrTypeValue['date'],
                                                parent_entity=entity,
                                                created_user=admin)
        entity.attrs.add(entity_attr)

        entry = Entry.objects.create(name='entry', schema=entity, created_user=admin)
        entry.complement_attrs(admin)

        attr = entry.attrs.last()
        attr.add_value(admin, INITIAL_DATE)

        # updates entry that has a invalid parameter which is typed date
        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(attr.id), 'type': str(AttrTypeValue['date']),
                 'value': [{'data': 'hoge', 'index': 0}], 'referral_key': []},
            ],
        }

        # check that invalied parameter raises error with self.assertRaises(ValueError) as ar:
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 400)

        # check that backend processing will not update with invalid value
        self.assertEqual(entry.attrs.last().values.count(), 1)
        self.assertEqual(attr.get_latest_value().date, INITIAL_DATE)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_create_empty_date_param(self):
        admin = self.admin_login()

        entity = Entity.objects.create(name='entity', created_user=admin)
        entity_attr = EntityAttr.objects.create(name='attr_date',
                                                type=AttrTypeValue['date'],
                                                parent_entity=entity,
                                                created_user=admin)
        entity.attrs.add(entity_attr)

        # creates entry that has a empty parameter which is typed date
        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(entity_attr.id), 'type': str(AttrTypeValue['date']),
                 'value': [{'data': '', 'index': 0}], 'referral_key': []},
            ],
        }

        # check that created a new entry with an empty date parameter
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)

        # get entry which is created in here
        entry = Entry.objects.get(name='entry', schema=entity)

        self.assertEqual(entry.attrs.count(), 1)
        self.assertIsNone(entry.attrs.last().get_latest_value().date)

    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_edit_entry_for_each_typed_attributes_repeatedly(self):
        user = self.admin_login()

        # prepare to Entity and Entries which importing data refers to
        ref_entity = Entity.objects.create(name='RefEntity', created_user=user)
        ref_entry = Entry.objects.create(name='ref', created_user=user, schema=ref_entity)
        group = Group.objects.create(name='group')

        entity = Entity.objects.create(name='Entity', created_user=user)
        attr_info = {
            'str': {
                'type': AttrTypeValue['string'],
                'value': [{'data': 'data', 'index': 0}],
                'expect_value': 'data',
                'expect_blank_value': '',
                'referral_key': []
            },
            'obj': {
                'type': AttrTypeValue['object'],
                'value': [{'data': str(ref_entry.id), 'index': 0}],
                'expect_value': 'ref',
                'expect_blank_value': None,
                'referral_key': []
            },
            'grp': {
                'type': AttrTypeValue['group'],
                'value': [{'data': str(group.id), 'index': 0}],
                'expect_value': 'group',
                'expect_blank_value': None,
                'referral_key': []
            },
            'name': {
                'type': AttrTypeValue['named_object'],
                'value': [{'data': str(ref_entry.id), 'index': 0}],
                'expect_value': {'key': 'ref'},
                'expect_blank_value': {'': None},
                'referral_key': [{'data': 'key', 'index': 0}]
            },
            'bool': {
                'type': AttrTypeValue['boolean'],
                'value': [{'data': True, 'index': 0}],
                'expect_value': True,
                'expect_blank_value': False,
                'referral_key': []
            },
            'date': {
                'type': AttrTypeValue['date'],
                'value': [{'data': '2018-01-01', 'index': 0}],
                'expect_value': date(2018, 1, 1),
                'expect_blank_value': None,
                'referral_key': []
            },
            'arr1': {
                'type': AttrTypeValue['array_string'],
                'value': [{'data': 'foo', 'index': 0}, {'data': 'bar', 'index': 1}],
                'expect_value': ['bar', 'foo'],
                'expect_blank_value': [],
                'referral_key': []
            },
            'arr2': {
                'type': AttrTypeValue['array_object'],
                'value': [{'data': str(ref_entry.id), 'index': 0}],
                'expect_value': ['ref'],
                'expect_blank_value': [],
                'referral_key': []
            },
            'arr3': {
                'type': AttrTypeValue['array_named_object'],
                'value': [{'data': str(ref_entry.id), 'index': 0}],
                'expect_value': [{'foo': 'ref'}, {'bar': None}],
                'expect_blank_value': [],
                'referral_key': [{'data': 'foo', 'index': 0}, {'data': 'bar', 'index': 1}]
            }
        }
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(name=attr_name,
                                             type=info['type'],
                                             created_user=user,
                                             parent_entity=entity)

            info['schema'] = attr
            if info['type'] & AttrTypeValue['object']:
                attr.referral.add(ref_entity)

            entity.attrs.add(attr)

        entry = Entry.objects.create(name='entry', schema=entity, created_user=user)
        entry.complement_attrs(user)

        ###
        # set valid values for each attrs
        params = {
            'entry_name': 'entry',
            'attrs': [{
                'id': str(entry.attrs.get(schema=x['schema']).id),
                'type': str(x['type']),
                'value': x['value'],
                'referral_key': x['referral_key']
            } for x in attr_info.values()],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        # checks that expected values are set for each Attributes
        self.assertEqual(resp.status_code, 200)
        for info in attr_info.values():
            value = entry.attrs.get(schema=info['schema']).get_latest_value().get_value()

            if isinstance(value, list):
                self.assertTrue(any(x in info['expect_value'] for x in value))
            else:
                self.assertEqual(value, info['expect_value'])

        ###
        # checks that value histories for each Attributes will be same when same values are set
        # before_vh = [x.get_value() for x in entry.get_value_history(user)]
        before_vh = entry.get_value_history(user)

        params = {
            'entry_name': 'entry',
            'attrs': [{
                'id': str(entry.attrs.get(schema=x['schema']).id),
                'type': str(x['type']),
                'value': x['value'],
                'referral_key': x['referral_key']
            } for x in attr_info.values()],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(entry.get_value_history(user), before_vh)

        ###
        # checks that expected values are set for each Attributes
        self.assertEqual(resp.status_code, 200)

        # set all parameters to be empty
        params = {
            'entry_name': 'entry',
            'attrs': [{
                'id': str(entry.attrs.get(schema=x['schema']).id),
                'type': str(x['type']),
                'value': [],
                'referral_key': []
            } for x in attr_info.values()],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)
        for (name, info) in attr_info.items():
            self.assertEqual(entry.attrs.get(schema=info['schema']).get_latest_value().get_value(),
                             info['expect_blank_value'])

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_create_with_invalid_referral_params(self):
        user = self.admin_login()

        def checker_obj(attrv):
            self.assertIsNone(attrv.referral)

        def checker_name(attrv):
            self.assertEqual(attrv.value, 'foo')
            self.assertIsNone(attrv.referral)

        def checker_arr_obj(attrv):
            self.assertEqual(attrv.data_array.count(), 0)

        def checker_arr_name(attrv):
            self.assertEqual(attrv.data_array.count(), 1)
            self.assertEqual(attrv.data_array.first().value, 'foo')
            self.assertIsNone(attrv.data_array.first().referral)

        entity = Entity.objects.create(name='Entity', created_user=user)
        attr_info = {
            'obj': {'type': AttrTypeValue['object'], 'checker': checker_obj},
            'name': {'type': AttrTypeValue['named_object'], 'checker': checker_name},
            'arr_obj': {'type': AttrTypeValue['array_object'], 'checker': checker_arr_obj},
            'arr_name': {'type': AttrTypeValue['array_named_object'], 'checker': checker_arr_name},
        }
        for attr_name, info in attr_info.items():
            entity.attrs.add(EntityAttr.objects.create(name=attr_name,
                                                       type=info['type'],
                                                       created_user=user,
                                                       parent_entity=entity))

        for (i, value) in enumerate(['', '0', 0, '9999', None]):
            entry_name = 'entry-%d' % i
            params = {
                'entry_name': entry_name,
                'attrs':  [{
                    'id': str(x.id),
                    'type': str(x.type),
                    'value': [{'data': value, 'index': 0}],
                    'referral_key': [
                        {'data': 'foo', 'index': 0}] if x.type & AttrTypeValue['named'] else [],
                } for x in entity.attrs.all()],
            }
            resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                    json.dumps(params),
                                    'application/json')

            self.assertEqual(resp.status_code, 200)
            entry = Entry.objects.get(name=entry_name, schema=entity)

            for (name, info) in attr_info.items():
                info['checker'](entry.attrs.get(schema__name=name).get_latest_value())

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_attribute_of_mandatory_params(self):
        """
        This tests the processing of creating entry would return error, or not,
        when non-value was specified in a mandatory parameter for each attribute type.
        """
        user = self.admin_login()

        # prepare to Entity and Entries which importing data refers to
        entity_info = {
            'str': {'type': AttrTypeValue['string']},
            'obj': {'type': AttrTypeValue['object']},
            'grp': {'type': AttrTypeValue['group']},
            'name': {'type': AttrTypeValue['named_object']},
            'bool': {'type': AttrTypeValue['boolean']},
            'date': {'type': AttrTypeValue['date']},
            'arr1': {'type': AttrTypeValue['array_string']},
            'arr2': {'type': AttrTypeValue['array_object']},
            'arr3': {'type': AttrTypeValue['array_named_object']},
        }
        for name, info in entity_info.items():
            # create entity that only has one attribute of specified type
            entity = Entity.objects.create(name=name, created_user=user)
            attr = EntityAttr.objects.create(name=name,
                                             type=info['type'],
                                             created_user=user,
                                             is_mandatory=True,
                                             parent_entity=entity)

            entity.attrs.add(attr)

            # send a request to create entry and expect to be error
            referral_key = []
            if info['type'] & AttrTypeValue['named']:
                referral_key = [{'data': '', 'index': 0}]
            params = {
                'entry_name': 'entry',
                'attrs': [{
                    'id': str(attr.id),
                    'type': str(info['type']),
                    'value': [{'data': '', 'index': 0}],
                    'referral_key': referral_key
                }],
            }
            resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                    json.dumps(params),
                                    'application/json')
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(Entry.objects.filter(schema=entity).count(), 0)

            # when a referral_key is specified, named type will be successful to create
            if info['type'] & AttrTypeValue['named']:
                referral_key[0]['data'] = 'hoge'
                resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                        json.dumps(params),
                                        'application/json')

                self.assertEqual(resp.status_code, 200)
                self.assertEqual(Entry.objects.filter(schema=entity).count(), 1)

    def test_update_entry_without_backend(self):
        user = self.guest_login()
        entity = Entity.objects.create(name='entity', created_user=user)
        entry = Entry.objects.create(name='entry', created_user=user, schema=entity)

        params = {
            'entry_name': 'hoge',
            'attrs': [],
        }

        def side_effect(job_id):
            job = Job.objects.get(id=job_id)

            self.assertEqual(job.user.id, user.id)
            self.assertEqual(job.target.id, entry.id)
            self.assertEqual(job.target_type, Job.TARGET_ENTRY)
            self.assertEqual(job.status, Job.STATUS['PREPARING'])
            self.assertEqual(job.operation, JobOperation.EDIT_ENTRY.value)

        with patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=side_effect)):
            resp = self.client.post(reverse('entry:do_edit', args=[entry.id]),
                                    json.dumps(params),
                                    'application/json')

            self.assertEqual(resp.status_code, 200)

    @patch('entry.tasks.delete_entry.delay', Mock(side_effect=tasks.delete_entry))
    def test_not_to_show_deleted_entry(self):
        user = self.guest_login()
        entity = Entity.objects.create(name='entity', created_user=user)
        entry = Entry.objects.create(name='entry', created_user=user, schema=entity)

        # delete entry and check each page couldn't be shown
        entry.delete()

        self.assertEqual(self.client.get(reverse('entry:show', args=[entry.id])).status_code, 400)
        self.assertEqual(self.client.get(reverse('entry:edit', args=[entry.id])).status_code, 400)
        self.assertEqual(self.client.get(reverse('entry:copy', args=[entry.id])).status_code, 400)
        self.assertEqual(self.client.get(reverse('entry:refer', args=[entry.id])).status_code, 400)
        self.assertEqual(
            self.client.get(reverse('entry:history', args=[entry.id])).status_code, 400)

    def test_not_to_show_under_processing_entry(self):
        user = self.guest_login()
        entity = Entity.objects.create(name='entity', created_user=user)
        entry = Entry.objects.create(name='entry', created_user=user, schema=entity)

        # update status of entry and check each page couldn't be shown
        entry.set_status(Entry.STATUS_EDITING)
        self.assertEqual(self.client.get(reverse('entry:copy', args=[entry.id])).status_code, 400)

        entry.set_status(Entry.STATUS_CREATING)
        self.assertEqual(self.client.get(reverse('entry:show', args=[entry.id])).status_code, 400)
        self.assertEqual(self.client.get(reverse('entry:edit', args=[entry.id])).status_code, 400)
        self.assertEqual(self.client.get(reverse('entry:copy', args=[entry.id])).status_code, 400)
        self.assertEqual(self.client.get(reverse('entry:refer', args=[entry.id])).status_code, 400)
        self.assertEqual(
            self.client.get(reverse('entry:history', args=[entry.id])).status_code, 400)

    def test_show_entry_history(self):
        user = self.guest_login()
        entity = Entity.objects.create(name='entity', created_user=user)
        entity.attrs.add(EntityAttr.objects.create(**{
            'name': 'attr',
            'created_user': user,
            'parent_entity': entity,
            'type': AttrTypeValue['string']
        }))

        # create and add values
        entry = Entry.objects.create(name='entry', schema=entity, created_user=user)
        entry.complement_attrs(user)
        [entry.attrs.first().add_value(user, str(x)) for x in range(3)]

        resp = self.client.get(reverse('entry:history', args=[entry.id]))
        self.assertEqual(resp.status_code, 200)

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    @patch('entry.tasks.edit_entry_attrs.delay', Mock(side_effect=tasks.edit_entry_attrs))
    def test_create_and_edit_without_type_parameter(self):
        user = self.guest_login()
        entity = Entity.objects.create(name='entity', created_user=user)
        attr = EntityAttr.objects.create(name='attr', created_user=user, parent_entity=entity,
                                         type=AttrTypeValue['string'])
        entity.attrs.add(attr)

        # create without type parameter
        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(attr.id), 'value': [{'data': 'hoge', 'index': '0'}]},
            ],
        }
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]), json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(name='entry', schema=entity, is_active=True)
        self.assertEqual(entry.attrs.first().get_latest_value().value, 'hoge')

        # edit without type parameter
        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(entry.attrs.first().id), 'value': [{'data': 'fuga', 'index': '0'}]},
            ],
        }
        resp = self.client.post(reverse('entry:do_edit', args=[entry.id]), json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        entry.refresh_from_db()
        self.assertEqual(entry.attrs.first().get_latest_value().value, 'fuga')

    def test_index_deleting_entries(self):
        # initialize entries to test
        user = self.guest_login()
        entity = Entity.objects.create(name='entity', created_user=user)

        # to check the view of deleted entries, all entries would be deleted just after creating
        entries = []
        for index in range(3):
            entry = Entry.objects.create(name='e-%d' % index, schema=entity, created_user=user)
            entry.delete()

            entries.append(entry)

        # to check that entries that are set status would not be listed at restore page
        entries[1].set_status(Entry.STATUS_CREATING)

        resp = self.client.get(reverse('entry:restore', args=[entity.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['entries']), 2)
        self.assertEqual(len(resp.context['entries']), resp.context['list_count'])
        self.assertEqual(len(resp.context['entries']), resp.context['total_count'])

        # check listing entries are ordered by desc
        self.assertEqual(resp.context['entries'][0].name.find('e-2'), 0)
        self.assertEqual(resp.context['entries'][1].name.find('e-0'), 0)

    @patch('entry.tasks.restore_entry.delay', Mock(side_effect=tasks.restore_entry))
    def test_restore_entry(self):
        # initialize entries to test
        user = self.guest_login()
        entity = Entity.objects.create(name='entity', created_user=user)
        entity.attrs.add(EntityAttr.objects.create(**{
            'name': 'attr',
            'type': AttrTypeValue['string'],
            'created_user': user,
            'parent_entity': entity,
        }))

        entry = Entry.objects.create(name='entry', schema=entity, created_user=user)
        entry.complement_attrs(user)

        # send request with invalid entry-id
        resp = self.client.post(reverse('entry:do_restore', args=[9999]), json.dumps({}),
                                'application/json')
        self.assertEqual(resp.status_code, 400)

        # send request with entry-id which is active
        resp = self.client.post(reverse('entry:do_restore', args=[entry.id]), json.dumps({}),
                                'application/json')
        self.assertEqual(resp.status_code, 400)
        obj = json.loads(resp.content.decode("UTF-8"))
        self.assertEqual(obj['msg'], 'Failed to get entry from specified parameter')

        # delete target entry to run restore processing
        entry.delete()

        entry.refresh_from_db()
        self.assertTrue(entry.name.find('_deleted_') > 0)
        self.assertFalse(any([x.is_active for x in entry.attrs.all()]))

        resp = self.client.post(reverse('entry:do_restore', args=[entry.id]), json.dumps({}),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        entry.refresh_from_db()
        self.assertEqual(entry.name, 'entry')
        self.assertTrue(entry.is_active)
        self.assertTrue(all([x.is_active for x in entry.attrs.all()]))

        # check that index information of restored entry in Elasticsearch is also restored
        resp = Entry.search_entries(user, [entity.id])
        self.assertEqual(resp['ret_count'], 1)
        self.assertEqual(resp['ret_values'][0]['entry']['id'], entry.id)
        self.assertEqual(resp['ret_values'][0]['entry']['name'], entry.name)

    def test_restore_when_duplicate_entry_exist(self):
        # initialize entries to test
        user = self.guest_login()
        entity = Entity.objects.create(name='entity', created_user=user)
        entry = Entry.objects.create(name='entry', schema=entity, created_user=user)

        # delete target entry to run restore processing
        entry.delete()

        # After deleting, create an entry with the same name
        dup_entry = Entry.objects.create(name='entry', schema=entity, created_user=user)

        resp = self.client.post(reverse('entry:do_restore', args=[entry.id]), json.dumps({}),
                                'application/json')
        self.assertEqual(resp.status_code, 400)
        obj = json.loads(resp.content.decode("UTF-8"))
        self.assertEqual(obj['msg'], '')
        self.assertEqual(obj['entry_id'], dup_entry.id)
        self.assertEqual(obj['entry_name'], dup_entry.name)

    def test_revert_attrv(self):
        user = self.guest_login()

        # initialize referred objects
        ref_entity = Entity.objects.create(name='RefEntity', created_user=user)
        ref_entries = [Entry.objects.create(name='r%d' % i, created_user=user,
                                            schema=ref_entity) for i in range(3)]
        groups = [Group.objects.create(name='g%d' % i) for i in range(2)]

        # initialize Entity and Entry
        entity = Entity.objects.create(name='Entity', created_user=user)

        # First of all, this test set values which is in 'values' of attr_info to each attributes
        # in order of first and second (e.g. in the case of 'str', this test sets 'foo' at first,
        # then sets 'bar') manually. After that, this test retrieve first value by calling the
        # 'revert_attrv' handler. So finnaly, this test expects first value is stored
        # in Database and Elasticsearch.
        attr_info = {
            'str': {
                'type': AttrTypeValue['string'],
                'values': ['foo', 'bar']
            },
            'obj': {
                'type': AttrTypeValue['object'],
                'values': [ref_entries[0], ref_entries[1]]
            },
            'grp': {
                'type': AttrTypeValue['group'],
                'values': [groups[0], groups[1]]
            },
            'name': {
                'type': AttrTypeValue['named_object'],
                'values': [
                    {'name': 'foo', 'id': ref_entries[0]},
                    {'name': 'bar', 'id': ref_entries[1]},
                ]
            },
            'bool': {
                'type': AttrTypeValue['boolean'],
                'values': [False, True]
            },
            'date': {
                'type': AttrTypeValue['date'],
                'values': ['2018-01-01', '2018-02-01']
            },
            'arr1': {
                'type': AttrTypeValue['array_string'],
                'values': [
                    ['foo', 'bar', 'baz'],
                    ['hoge', 'fuga', 'puyo']
                ]
            },
            'arr2': {
                'type': AttrTypeValue['array_object'],
                'values': [
                    [ref_entries[0], ref_entries[1]],
                    [ref_entries[2]]
                ]
            },
            'arr3': {
                'type': AttrTypeValue['array_named_object'],
                'values': [
                    [{'name': 'foo', 'id': ref_entries[0]}, {'name': 'bar', 'id': ref_entries[1]}],
                    [{'name': '', 'id': ref_entries[1]}, {'name': 'fuga', 'id': ref_entries[2]}]
                ]
            }
        }
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(name=attr_name,
                                             type=info['type'],
                                             created_user=user,
                                             parent_entity=entity)

            if info['type'] & AttrTypeValue['object']:
                attr.referral.add(ref_entity)

            entity.attrs.add(attr)

        # initialize each AttributeValues
        entry = Entry.objects.create(name='Entry', schema=entity, created_user=user)
        entry.complement_attrs(user)
        for attr_name, info in attr_info.items():
            attr = entry.attrs.get(schema__name=attr_name)
            attrv1 = attr.add_value(user, info['values'][0])

            # store first value's attrv
            info['expected_value'] = attrv1.get_value()

            # update value to second value
            attrv2 = attr.add_value(user, info['values'][1])

            # check value is actually updated
            self.assertNotEqual(attrv1.get_value(), attrv2.get_value())

            # reset AttributeValue and latest_value equals with attrv1
            params = {'attr_id': str(attr.id), 'attrv_id': str(attrv1.id)}
            resp = self.client.post(reverse('entry:revert_attrv'),
                                    json.dumps(params), 'application/json')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(attrv1.get_value(), attr.get_latest_value().get_value())

        resp = Entry.search_entries(user, [entity.id])
        self.assertEqual(resp['ret_count'], 1)
        for attr_name, data in resp['ret_values'][0]['attrs'].items():
            self.assertEqual(data['type'], attr_info[attr_name]['type'])

            value = attr_info[attr_name]['values'][0]
            if data['type'] == AttrTypeValue['boolean']:
                self.assertEqual(data['value'], str(value))

            elif data['type'] == AttrTypeValue['group']:
                self.assertEqual(data['value'], {'name': value.name, 'id': value.id})

            elif data['type'] == AttrTypeValue['object']:
                self.assertEqual(data['value'], {'name': value.name, 'id': value.id})

            elif data['type'] == AttrTypeValue['array_object']:
                self.assertEqual(data['value'], [{'name': x.name, 'id': x.id} for x in value])

            elif data['type'] == AttrTypeValue['named_object']:
                self.assertEqual(data['value'],
                                 {value['name']: {'name': value['id'].name, 'id': value['id'].id}})

            elif data['type'] == AttrTypeValue['array_named_object']:
                self.assertEqual(
                    data['value'],
                    [{x['name']: {'name': x['id'].name, 'id': x['id'].id}} for x in value])

            else:
                self.assertEqual(data['value'], value)

    def test_revert_attrv_with_invalid_value(self):
        user = self.guest_login()

        # initialize Entity and Entry
        entity = Entity.objects.create(name='Entity', created_user=user)
        [entity.attrs.add(EntityAttr.objects.create(**{
            'name': attr_name,
            'type': AttrTypeValue['string'],
            'created_user': user,
            'parent_entity': entity,
        })) for attr_name in ['attr1', 'attr2']]

        entry = Entry.objects.create(name='Entry', schema=entity, created_user=user)
        entry.complement_attrs(user)
        attr1 = entry.attrs.first()

        # send request with invalid arguments
        params = {'attr_id': '0', 'attrv_id': '0'}
        resp = self.client.post(reverse('entry:revert_attrv'),
                                json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'Specified Attribute-id is invalid')

        params = {'attr_id': str(attr1.id), 'attrv_id': '0'}
        resp = self.client.post(reverse('entry:revert_attrv'),
                                json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'Specified AttributeValue-id is invalid')

        attrvs = [attr1.add_value(user, str(x)) for x in range(2)]
        self.assertEqual(attr1.get_latest_value(), attrvs[-1])

        # change Attribute type of attr then get latest AttributeValue
        attr1.schema.type = AttrTypeValue['object']
        attr1.schema.save(update_fields=['type'])

        self.assertGreater(attr1.get_latest_value().id, attrvs[-1].id)

        # specify attrv_id which refers different parent_attr
        params = {'attr_id': str(entry.attrs.last().id), 'attrv_id': str(attrvs[0].id)}
        resp = self.client.post(reverse('entry:revert_attrv'), json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'Specified AttributeValue-id is invalid')

    @patch('custom_view.is_custom', Mock(return_value=True))
    @patch('custom_view.call_custom', Mock(return_value=HttpResponse('success')))
    def test_revert_attrv_with_custom_view(self):
        user = self.guest_login()

        # initialize Entity and Entry
        entity = Entity.objects.create(name='Entity', created_user=user)
        entity.attrs.add(EntityAttr.objects.create(**{
            'name': 'attr',
            'type': AttrTypeValue['string'],
            'created_user': user,
            'parent_entity': entity,
        }))

        entry = Entry.objects.create(name='Entry', schema=entity, created_user=user)
        entry.complement_attrs(user)
        attr = entry.attrs.first()

        # set AttributeValues to the Attribute object
        attrv1 = attr.add_value(user, 'hoge')
        attr.add_value(user, 'fuga')
        number_of_attrvalue = attr.values.count()

        # send request to revert AttributeValue which is set before
        params = {'attr_id': str(attr.id), 'attrv_id': str(attrv1.id)}
        resp = self.client.post(reverse('entry:revert_attrv'), json.dumps(params),
                                'application/json')

        # the latest AttributeValue object is reverted from "fuga" to "hoge"
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(attr.values.count(), number_of_attrvalue + 1)
        self.assertEqual(attr.get_latest_value().value, attrv1.value)
        self.assertNotEqual(attr.get_latest_value().id, attrv1.id)

    @patch('custom_view.is_custom', Mock(return_value=True))
    @patch('custom_view.call_custom', Mock(return_value=HttpResponse('success')))
    def test_revert_attrv_with_custom_view_by_latest_value(self):
        user = self.guest_login()

        # initialize Entity and Entry
        entity = Entity.objects.create(name='Entity', created_user=user)
        entity.attrs.add(EntityAttr.objects.create(**{
            'name': 'attr',
            'type': AttrTypeValue['string'],
            'created_user': user,
            'parent_entity': entity,
        }))

        entry = Entry.objects.create(name='Entry', schema=entity, created_user=user)
        entry.complement_attrs(user)
        attr = entry.attrs.first()

        # set AttributeValue to Attribute
        attrv = attr.add_value(user, 'hoge')
        number_of_attrvalue = attr.values.count()

        # try to revert AttributeValue which is the latest one
        params = {'attr_id': str(attr.id), 'attrv_id': str(attrv.id)}
        resp = self.client.post(reverse('entry:revert_attrv'), json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(attr.values.count(), number_of_attrvalue)
        self.assertEqual(attr.get_latest_value(), attrv)

    @patch('custom_view.is_custom', Mock(return_value=True))
    @patch('custom_view.call_custom', Mock(return_value=(False, 400, 'test')))
    def test_call_custom_do_create_entry_return_int(self):
        self.admin_login()

        params = {
            'entry_name': 'hoge',
            'attrs': [
                {'id': str(self._entity_attr.id), 'type': str(AttrTypeArrStr),
                 'value': [{'data': 'hoge', 'index': '0'}], 'referral_key': []},
            ],
        }

        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        self.assertEqual(resp.status_code, 400)

    @patch('custom_view.is_custom', Mock(return_value=True))
    @patch('custom_view.call_custom',
           Mock(return_value=(False, JsonResponse({'entry_id': 1, 'entry_name': 'fuga', }), '')))
    def test_call_custom_do_create_entry_return_json(self):
        self.admin_login()

        params = {
            'entry_name': 'hoge',
            'attrs': [
                {'id': str(self._entity_attr.id), 'type': str(AttrTypeArrStr),
                 'value': [{'data': 'hoge', 'index': '0'}], 'referral_key': []},
            ],
        }

        resp = self.client.post(reverse('entry:do_create', args=[self._entity.id]),
                                json.dumps(params),
                                'application/json')

        data = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['entry_id'], 1)
        self.assertEqual(data['entry_name'], 'fuga')

    @patch('entry.tasks.import_entries.delay', Mock(side_effect=tasks.import_entries))
    def test_import_entry_with_multiple_attr(self):
        user = self.admin_login()

        # Create a test entry
        entry = Entry.objects.create(name='entry', schema=self._entity, created_user=user)
        entry.complement_attrs(user)

        # Add 1 data and update to deleted
        attr = entry.attrs.get(schema__name='test')
        attr.add_value(user, 'test_value')
        attr.delete()

        # Add second data
        attr.add_value(user, 'test_value2')

        fp = self.open_fixture_file('import_data02.yaml')
        self.client.post(reverse('entry:do_import', args=[self._entity.id]), {'file': fp})
        fp.close()

        # Check attribute value
        self.assertEqual(
            entry.attrs.get(schema__name='test', is_active=True).get_latest_value().value, 'fuga')

    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    @patch.object(Job, 'is_canceled', Mock(return_value=True))
    def test_cancel_creating_entry(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='entity', created_user=user)
        entity_attr = EntityAttr.objects.create(name='attr',
                                                type=AttrTypeValue['string'],
                                                parent_entity=entity,
                                                created_user=user)
        entity.attrs.add(entity_attr)

        # creates entry that has a parameter which is typed boolean
        params = {
            'entry_name': 'entry',
            'attrs': [
                {'id': str(entity_attr.id), 'value': [{'data': 'hoge', 'index': 0}],
                 'referral_key': []},
            ],
        }

        # This task would be canceled because is_canceled method of creating job object
        # returns True.
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps(params),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.last()
        self.assertFalse(entry.is_active)
        self.assertIn('entry_deleted_', entry.name)

    @patch.object(Job, 'is_canceled', Mock(return_value=True))
    @patch.object(Job, 'proceed_if_ready', Mock(return_value=False))
    @patch('entry.tasks.create_entry_attrs.delay', Mock(side_effect=tasks.create_entry_attrs))
    def test_cancel_creating_entry_before_starting_background_processing(self):
        user = self.admin_login()
        entity = Entity.objects.create(name='entity', created_user=user)

        # The case that job is canceled before staring background processing
        resp = self.client.post(reverse('entry:do_create', args=[entity.id]),
                                json.dumps({'entry_name': 'entry', 'attrs': []}),
                                'application/json')
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.last()
        self.assertFalse(entry.is_active)
        self.assertIn('entry_deleted_', entry.name)

    @patch.object(Job, 'is_canceled', Mock(return_value=True))
    @patch('entry.tasks.import_entries.delay', Mock(side_effect=tasks.import_entries))
    def test_cancel_importing_entries(self):
        self.admin_login()

        fp = self.open_fixture_file('import_data03.yaml')
        resp = self.client.post(reverse('entry:do_import', args=[self._entity.id]), {'file': fp})
        fp.close()

        # check the import is success
        self.assertEqual(resp.status_code, 303)
        self.assertEqual(Entry.objects.filter(schema=self._entity).count(), 0)
        self.assertEqual(Job.objects.last().text, 'Now importing... (progress: [    1/    3])')
