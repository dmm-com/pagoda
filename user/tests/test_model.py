from django.test import TestCase
from django.contrib.auth.models import User as DjangoUser
from rest_framework.authtoken.models import Token

from airone.lib.acl import ACLType
from entity.models import Entity, EntityAttr
from entry.models import Entry
from group.models import Group
from role.models import Role
from user.models import User, History


class ModelTest(TestCase):
    def setUp(self):
        self.user = User(username='ほげ', email='hoge@example.com')
        self.user.set_password('fuga')
        self.user.save()

    def test_get_token(self):
        # if not have token
        self.assertIsNone(self.user.token)

        # create token
        self.client.login(username='ほげ', password='fuga')
        self.client.put('/api/v1/user/access_token')
        self.assertEqual(self.user.token, Token.objects.get(user=self.user))

    def test_make_user(self):
        self.assertTrue(isinstance(self.user, DjangoUser))
        self.assertEqual(self.user.username, 'ほげ')
        self.assertEqual(self.user.authorized_type, 0)
        self.assertIsNotNone(self.user.date_joined)
        self.assertTrue(self.user.is_active)

    def test_delete_user(self):
        self.user.delete()

        user = User.objects.get(id=self.user.id)
        self.assertTrue(isinstance(user, DjangoUser))
        self.assertEqual(user.username.find('ほげ_deleted_'), 0)
        self.assertEqual(user.email, "deleted__hoge@example.com")
        self.assertEqual(user.authorized_type, 0)
        self.assertIsNotNone(user.date_joined)
        self.assertFalse(user.is_active)

    def test_set_history(self):
        entity = Entity.objects.create(name='test-entity', created_user=self.user)
        entry = Entry.objects.create(name='test-attr', created_user=self.user, schema=entity)

        self.user.seth_entity_add(entity)
        self.user.seth_entity_mod(entity)
        self.user.seth_entity_del(entity)
        self.user.seth_entry_del(entry)

        self.assertEqual(History.objects.count(), 4)
        self.assertEqual(History.objects.filter(operation=History.ADD_ENTITY).count(), 1)
        self.assertEqual(History.objects.filter(operation=History.MOD_ENTITY).count(), 1)
        self.assertEqual(History.objects.filter(operation=History.DEL_ENTITY).count(), 1)
        self.assertEqual(History.objects.filter(operation=History.DEL_ENTRY).count(), 1)

    def test_set_history_with_detail(self):
        entity = Entity.objects.create(name='test-entity', created_user=self.user)
        attr = EntityAttr.objects.create(name='test-attr',
                                         created_user=self.user, parent_entity=entity)

        history = self.user.seth_entity_add(entity)

        history.add_attr(attr)
        history.mod_attr(attr, 'changed points ...')
        history.del_attr(attr)
        history.mod_entity(entity, 'changed points ...')

        self.assertEqual(History.objects.count(), 5)
        self.assertEqual(History.objects.filter(user=self.user).count(), 5)
        self.assertEqual(History.objects.filter(operation=History.ADD_ATTR).count(), 1)
        self.assertEqual(History.objects.filter(operation=History.MOD_ATTR).count(), 1)
        self.assertEqual(History.objects.filter(operation=History.DEL_ATTR).count(), 1)
        self.assertEqual(History.objects.filter(operation=History.ADD_ENTITY).count(), 1)
        self.assertEqual(History.objects.filter(operation=History.MOD_ENTITY).count(), 1)

        # checks detail histories are registered correctly
        self.assertEqual(history.details.count(), 4)
        self.assertEqual(history.details.filter(operation=History.ADD_ATTR).count(), 1)
        self.assertEqual(history.details.filter(operation=History.MOD_ATTR).count(), 1)
        self.assertEqual(history.details.filter(operation=History.DEL_ATTR).count(), 1)
        self.assertEqual(history.details.filter(operation=History.MOD_ENTITY).count(), 1)

    def test_set_history_of_invalid_type_entry(self):
        class InvalidType(object):
            pass

        Entity.objects.create(name='test-entity', created_user=self.user)
        invalid_obj = InvalidType()

        with self.assertRaises(TypeError):
            self.user.seth_entity_add(invalid_obj)
            self.user.seth_entity_mod(invalid_obj)
            self.user.seth_entity_del(invalid_obj)
            self.user.seth_entry_del(invalid_obj)

        self.assertEqual(History.objects.count(), 0)

    def test_affect_group_acl(self):
        """
        This checks permission which is set to group is affects to the user
        who is belonged to that group.
        """

        admin = User.objects.create(username='admin')

        user = User.objects.create(username='user')
        group = Group.objects.create(name='group')
        role = Role.objects.create(name='role')

        user.groups.add(group)
        role.groups.add(group)

        entity = Entity.objects.create(name='entity',
                                       created_user=admin,
                                       is_public=False,
                                       default_permission=ACLType.Nothing.id)

        role.permissions.add(entity.readable)

        self.assertTrue(user.has_permission(entity, ACLType.Readable))
        self.assertFalse(user.has_permission(entity, ACLType.Writable))
        self.assertFalse(user.has_permission(entity, ACLType.Full))

    def test_object_acl_that_should_not_be_shown(self):
        user = User.objects.create(username='user')
        entity = Entity.objects.create(name='entity',
                                       created_user=user,
                                       is_public=False,
                                       default_permission=ACLType.Nothing.id)

        entry = Entry.objects.create(name='Entry',
                                     schema=entity,
                                     is_public=False,
                                     default_permission=ACLType.Full.id,
                                     created_user=user)

        self.assertFalse(user.has_permission(entry, ACLType.Readable))
