import json

from group.models import Group
from django.urls import reverse

from user.models import User
from acl.models import ACLBase
from entity.models import Entity, EntityAttr
from entry.models import Entry, Attribute

from airone.lib.acl import ACLType
from airone.lib.test import AironeViewTest


class ViewTest(AironeViewTest):
    # override 'admin_login' method to create initial ACLBase objects
    def admin_login(self):
        user = super(ViewTest, self).admin_login()

        self._aclobj = ACLBase(name='test', created_user=user)
        self._aclobj.save()

        return user

    def send_set_request(self, aclobj, user, aclid=ACLType.Writable.id):
        params = {
            'object_id': str(aclobj.id),
            'object_type': str(aclobj.objtype),
            'acl': [
                {
                    'member_id': str(user.id),
                    'member_type': 'user',
                    'value': str(aclid)},
            ],
            'default_permission': str(ACLType.Nothing.id),
        }
        return self.client.post(reverse('acl:set'), json.dumps(params), 'application/json')

    def test_index_without_login(self):
        resp = self.client.get(reverse('acl:index', args=[0]))
        self.assertEqual(resp.status_code, 303)

    def test_index(self):
        self.admin_login()

        resp = self.client.get(reverse('acl:index', args=[self._aclobj.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([x['name'] for x in resp.context['members']], ['admin'])

    def test_index_with_objects(self):
        self.admin_login()

        User(username='hoge').save()

        resp = self.client.get(reverse('acl:index', args=[self._aclobj.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([x['name'] for x in resp.context['members']], ['admin', 'hoge'])

    def test_get_acl_set(self):
        self.admin_login()

        resp = self.client.get(reverse('acl:set'))
        self.assertEqual(resp.status_code, 400)

    def test_post_acl_set_without_login(self):
        user = User(username='hoge')
        user.save()

        aclobj = ACLBase(name='hoge', created_user=user)

        params = {
            'object_id': str(aclobj.id),
            'object_type': str(aclobj.objtype),
            'acl': [
                {
                    'member_id': str(user.id),
                    'member_type': 'user',
                    'value': str(ACLType.Writable.id)},
            ],
            'default_permission': str(ACLType.Nothing.id),
        }
        resp = self.client.post(reverse('acl:set'), json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 401)

    def test_post_acl_set(self):
        user = self.admin_login()
        resp = self.send_set_request(self._aclobj, user)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(user.permissions.count(), 1)
        self.assertEqual(user.permissions.last(), self._aclobj.writable)
        self.assertFalse(ACLBase.objects.get(id=self._aclobj.id).is_public)

    def test_post_acl_set_attrbase(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='entity', created_user=user)
        attrbase = EntityAttr.objects.create(name='hoge',
                                             created_user=user,
                                             parent_entity=entity)
        resp = self.send_set_request(attrbase, user)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['redirect_url'], '/entity/edit/%s' % entity.id)
        self.assertEqual(user.permissions.last(), attrbase.writable)
        self.assertFalse(EntityAttr.objects.get(id=attrbase.id).is_public)

    def test_post_acl_set_entity(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='hoge', created_user=user)
        resp = self.send_set_request(entity, user)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['redirect_url'], '/entity/')
        self.assertEqual(user.permissions.last(), entity.writable)
        self.assertFalse(Entity.objects.get(id=entity.id).is_public)

    def test_post_acl_set_attribute(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='hoge', created_user=user)
        entry = Entry.objects.create(name='hoge', created_user=user, schema=entity)
        attrbase = EntityAttr.objects.create(name='hoge',
                                             created_user=user,
                                             parent_entity=entity)
        entity.attrs.add(attrbase)
        attr = entry.add_attribute_from_base(attrbase, user)

        resp = self.send_set_request(attr, user)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['redirect_url'], '/entry/edit/%s' % entry.id)
        self.assertEqual(user.permissions.last(), attr.writable)
        self.assertFalse(Attribute.objects.get(id=attr.id).is_public)
        search_result = self._es.search(body={'query': {'term': {'name': entry.name}}})
        self.assertFalse(search_result['hits']['hits'][0]['_source']['attr'][0]['is_readble'])

    def test_post_acl_set_entry(self):
        user = self.admin_login()

        entity = Entity.objects.create(name='hoge', created_user=user)
        entry = Entry.objects.create(name='fuga', created_user=user, schema=entity)
        resp = self.send_set_request(entry, user)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['redirect_url'], '/entry/show/%s' % entry.id)
        self.assertEqual(user.permissions.last(), entry.writable)
        self.assertFalse(Entry.objects.get(id=entry.id).is_public)
        search_result = self._es.search(body={'query': {'term': {'name': entry.name}}})
        self.assertFalse(search_result['hits']['hits'][0]['_source']['is_readble'])

    def test_post_acl_set_nothing(self):
        user = self.admin_login()
        params = {
            'object_id': str(self._aclobj.id),
            'object_type': str(self._aclobj.objtype),
            'is_public': 'on',
            'acl': [
                {
                    'member_id': str(user.id),
                    'member_type': 'user',
                    'value': str(ACLType.Nothing.id)},
            ],
            'default_permission': str(ACLType.Nothing.id),
        }
        resp = self.client.post(reverse('acl:set'), json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(user.permissions.count(), 0)

    def test_update_acl(self):
        self.admin_login()

        group = Group(name='fuga')
        group.save()

        # set ACL object in advance, there are two members in the full parameter
        group.permissions.add(self._aclobj.full)

        params = {
            'object_id': str(self._aclobj.id),
            'object_type': str(self._aclobj.objtype),
            'acl': [
                {
                    'member_id': str(group.id),
                    'member_type': 'group',
                    'value': str(ACLType.Readable.id)
                }
            ],
            'default_permission': str(ACLType.Nothing.id),
        }
        resp = self.client.post(reverse('acl:set'), json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(group.permissions.count(), 1)
        self.assertEqual(group.permissions.last(), self._aclobj.readable)
        self.assertFalse(ACLBase.objects.get(id=self._aclobj.id).is_public)

    def test_update_acl_to_nothing(self):
        self.admin_login()

        group = Group(name='fuga')
        group.save()

        # set ACL object in advance, there are two members in the full parameter
        group.permissions.add(self._aclobj.full)

        params = {
            'object_id': str(self._aclobj.id),
            'object_type': str(self._aclobj.objtype),
            'acl': [
                {
                    'member_id': str(group.id),
                    'member_type': 'group',
                    'value': str(ACLType.Nothing.id)
                }
            ],
            'default_permission': str(ACLType.Nothing.id),
        }
        resp = self.client.post(reverse('acl:set'), json.dumps(params), 'application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(group.permissions.count(), 0)

    def test_post_acl_set_without_object_id(self):
        user = self.admin_login()
        params = {
            'acl': [
                {'member_id': str(user.id), 'value': str(ACLType.Writable)},
            ]
        }
        resp = self.client.post(reverse('acl:set'), json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 400)

    def test_post_acl_set_without_acl_params(self):
        self.admin_login()
        params = {
            'object_id': str(self._aclobj.id)
        }
        resp = self.client.post(reverse('acl:set'), json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 400)

    def test_post_acl_set_with_invalid_member_id(self):
        self.admin_login()
        params = {
            'object_id': str(self._aclobj.id),
            'acl': [
                {'member_id': '9999', 'value': str(ACLType.Writable)},
            ]
        }
        resp = self.client.post(reverse('acl:set'), json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 400)

    def test_post_acl_set_with_invalid_acl(self):
        user = self.admin_login()
        params = {
            'object_id': str(self._aclobj.id),
            'acl': [
                {'member_id': str(user.id), 'value': 'abcd'},
            ]
        }
        resp = self.client.post(reverse('acl:set'), json.dumps(params), 'application/json')

        self.assertEqual(resp.status_code, 400)

    def test_check_entry_permission_by_setting_permission_of_entity(self):
        guest = User.objects.create(username='guest', is_superuser=False)
        user = self.admin_login()

        entity = Entity.objects.create(name='hoge', created_user=user)
        entry = Entry.objects.create(name='fuga', created_user=user, schema=entity)

        resp = self.send_set_request(entity, user, ACLType.Readable.id)

        # reflesh object with latest DB data
        entity.refresh_from_db()
        entry.refresh_from_db()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(user.permissions.count(), 1)
        self.assertEqual(user.permissions.last(), entity.readable)
        self.assertEqual(entity.default_permission, ACLType.Nothing)
        self.assertFalse(entity.is_public)

        # check that guest user can't access Entry that schema's acl is set
        self.assertTrue(entry.is_public)
        self.assertTrue(user.has_permission(entry, ACLType.Readable))
        self.assertFalse(guest.has_permission(entry, ACLType.Readable))

    def test_check_attribute_permission_by_setting_permission_of_entityattr(self):
        guest = User.objects.create(username='guest', is_superuser=False)
        user = self.admin_login()

        entity = Entity.objects.create(name='hoge', created_user=user)
        attrbase = EntityAttr.objects.create(name='attr1',
                                             created_user=user,
                                             parent_entity=entity)

        entry = Entry.objects.create(name='fuga', created_user=user, schema=entity)
        attr = entry.add_attribute_from_base(attrbase, user)

        resp = self.send_set_request(attrbase, user, ACLType.Full.id)

        # reflesh object with latest DB data
        attrbase.refresh_from_db()
        attr.refresh_from_db()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(user.permissions.count(), 1)
        self.assertEqual(user.permissions.last(), attrbase.full)
        self.assertFalse(attrbase.is_public)
        self.assertEqual(attrbase.default_permission, ACLType.Nothing)

        # check that guest user can't access Entry that schema's acl is set
        self.assertTrue(attr.is_public)
        self.assertTrue(user.has_permission(attr, ACLType.Full))
        self.assertFalse(guest.has_permission(attr, ACLType.Full))

    def test_access_to_no_permission_object(self):
        user = self.guest_login()
        obj = ACLBase.objects.create(name='obj', created_user=user, is_public=False)

        # When normal user access to the ACL setting page of object which user doens't
        # have ACLType.Full, AirOne returns http-staus 400.
        resp = self.client.get(reverse('acl:index', args=[obj.id]))
        self.assertEqual(resp.status_code, 400)

        # While user has no permission of object, admin user can access to it.
        self.admin_login()
        resp = self.client.get(reverse('acl:index', args=[obj.id]))
        self.assertEqual(resp.status_code, 200)
