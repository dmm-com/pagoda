from django.conf import settings
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.authtoken.models import Token
from social_django.models import UserSocialAuth

from airone.lib.acl import ACLType
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.models import Entry
from group.models import Group
from role.models import Role
from user.models import History, User


class ModelTest(TestCase):
    def setUp(self):
        self.user = User(username="ほげ", email="hoge@example.com")
        self.user.set_password("fuga")
        self.user.save()
        self.user_social_auth = UserSocialAuth.objects.create(user=self.user)

    def test_get_token(self):
        # if not have token
        self.assertIsNone(self.user.token)

        # create token
        self.client.login(username="ほげ", password="fuga")
        self.client.put("/api/v1/user/access_token")
        self.assertEqual(self.user.token, Token.objects.get(user=self.user))

    def test_make_user(self):
        self.assertEqual(self.user.username, "ほげ")
        self.assertEqual(self.user.authorized_type, 0)
        self.assertIsNotNone(self.user.date_joined)
        self.assertTrue(self.user.is_active)

    def test_delete_user(self):
        self.user.delete()

        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.username.find("ほげ_deleted_"), 0)
        self.assertEqual(user.email, "deleted__hoge@example.com")
        self.assertEqual(user.authorized_type, 0)
        self.assertIsNotNone(user.date_joined)
        self.assertFalse(user.is_active)
        self.assertFalse(user.social_auth.exists())

    def test_set_history(self):
        entity = Entity.objects.create(name="test-entity", created_user=self.user)
        entry = Entry.objects.create(name="test-attr", created_user=self.user, schema=entity)

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
        entity = Entity.objects.create(name="test-entity", created_user=self.user)
        attr = EntityAttr.objects.create(
            name="test-attr",
            type=AttrType.OBJECT,
            created_user=self.user,
            parent_entity=entity,
        )

        history = self.user.seth_entity_add(entity)

        history.add_attr(attr)
        history.mod_attr(attr, "changed points ...")
        history.del_attr(attr)
        history.mod_entity(entity, "changed points ...")

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

        Entity.objects.create(name="test-entity", created_user=self.user)
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

        admin = User.objects.create(username="admin")

        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        role = Role.objects.create(name="role")

        user.groups.add(group)
        role.groups.add(group)

        entity = Entity.objects.create(
            name="entity",
            created_user=admin,
            is_public=False,
            default_permission=ACLType.Nothing.id,
        )

        entity.readable.roles.add(role)

        self.assertTrue(user.has_permission(entity, ACLType.Readable))
        self.assertFalse(user.has_permission(entity, ACLType.Writable))
        self.assertFalse(user.has_permission(entity, ACLType.Full))

    def test_object_acl_that_should_not_be_shown(self):
        user = User.objects.create(username="user")
        entity = Entity.objects.create(
            name="entity", created_user=user, is_public=False, default_permission=ACLType.Nothing.id
        )

        entry = Entry.objects.create(
            name="Entry",
            schema=entity,
            is_public=False,
            default_permission=ACLType.Full.id,
            created_user=user,
        )

        self.assertFalse(user.has_permission(entry, ACLType.Readable))

    def test_user_has_permission(self):
        # This checks user has permission to access ACLObject either user belongs to Role as
        # normal member and administrative member.
        user = User.objects.create(username="user")
        role = Role.objects.create(name="Role1")
        entity = Entity.objects.create(
            name="entity", created_user=user, is_public=False, default_permission=ACLType.Nothing.id
        )
        entity.full.roles.add(role)

        # User doesn't have permission before belonging to Role
        self.assertFalse(user.has_permission(entity, ACLType.Full))

        # User has permission after belonging to Role as member
        role.users.add(user)
        self.assertTrue(user.has_permission(entity, ACLType.Full))

        # User has also permission when user belongs to Role as admin-member
        role.users.clear()
        role.admin_users.add(user)
        self.assertTrue(user.has_permission(entity, ACLType.Full))

    def test_belonging_roles(self):
        # This checks all the four paths (member/admin x direct/via-group) are
        # collected, and that hierarchical superior groups are traversed.
        user = User.objects.create(username="user")
        parent_group = Group.objects.create(name="parent_group")
        child_group = Group.objects.create(name="child_group", parent_group=parent_group)
        user.groups.add(child_group)

        direct_role = Role.objects.create(name="direct_role")
        direct_role.users.add(user)
        direct_admin_role = Role.objects.create(name="direct_admin_role")
        direct_admin_role.admin_users.add(user)
        group_role = Role.objects.create(name="group_role")
        group_role.groups.add(child_group)
        parent_group_role = Role.objects.create(name="parent_group_role")
        parent_group_role.admin_groups.add(parent_group)

        # inactive roles and roles of unrelated groups must not be returned
        inactive_role = Role.objects.create(name="inactive_role", is_active=False)
        inactive_role.users.add(user)
        unrelated_role = Role.objects.create(name="unrelated_role")
        unrelated_role.groups.add(Group.objects.create(name="unrelated_group"))

        belongings = {x.role.name: x for x in user.belonging_roles()}
        self.assertEqual(
            sorted(belongings.keys()),
            ["direct_admin_role", "direct_role", "group_role", "parent_group_role"],
        )

        self.assertTrue(belongings["direct_role"].is_direct)
        self.assertFalse(belongings["direct_role"].is_admin)
        self.assertEqual(belongings["direct_role"].via_groups, [])

        self.assertTrue(belongings["direct_admin_role"].is_direct)
        self.assertTrue(belongings["direct_admin_role"].is_admin)

        self.assertFalse(belongings["group_role"].is_direct)
        self.assertFalse(belongings["group_role"].is_admin)
        self.assertEqual([g.name for g in belongings["group_role"].via_groups], ["child_group"])

        self.assertFalse(belongings["parent_group_role"].is_direct)
        self.assertTrue(belongings["parent_group_role"].is_admin)
        self.assertEqual(
            [g.name for g in belongings["parent_group_role"].via_groups], ["parent_group"]
        )

        # when only direct belonging is requested, roles of the superior group are excluded
        belongings = {x.role.name: x for x in user.belonging_roles(is_direct_belonging=True)}
        self.assertEqual(
            sorted(belongings.keys()), ["direct_admin_role", "direct_role", "group_role"]
        )

    def test_belonging_roles_aggregates_multiple_paths(self):
        # A role reachable through several paths must be reported only once,
        # with all the provenance merged into it.
        user = User.objects.create(username="user")
        group1 = Group.objects.create(name="group1")
        group2 = Group.objects.create(name="group2")
        user.groups.add(group1, group2)

        role = Role.objects.create(name="role")
        role.users.add(user)
        role.groups.add(group1)
        role.admin_groups.add(group2)

        belongings = user.belonging_roles()
        self.assertEqual(len(belongings), 1)
        self.assertEqual(belongings[0].role.id, role.id)
        self.assertTrue(belongings[0].is_direct)
        self.assertTrue(belongings[0].is_admin)
        self.assertEqual(sorted(g.name for g in belongings[0].via_groups), ["group1", "group2"])

    def test_belonging_roles_issues_constant_number_of_queries(self):
        # The number of queries must not grow along with the number of groups,
        # because has_permission() calls this on a hot path.
        user = User.objects.create(username="user")
        role = Role.objects.create(name="role")
        for i in range(2):
            group = Group.objects.create(name=f"group-{i}")
            user.groups.add(group)
            role.groups.add(group)

        with CaptureQueriesContext(connection) as ctx:
            user.belonging_roles()
        baseline = len(ctx.captured_queries)

        for i in range(2, 10):
            group = Group.objects.create(name=f"group-{i}")
            user.groups.add(group)
            role.groups.add(group)

        with self.assertNumQueries(baseline):
            user.belonging_roles()

    def test_get_all_hierarchical_groups_when_they_are_looped(self):
        """This test try to get hierarchical groups when those are looped like this
        * group0
            └──group1 (member: user1)
                 └──group0
                       └──group1 (member: user1)
                            ....
        """
        group0 = Group.objects.create(name="group0")
        group1 = Group.objects.create(name="group1", parent_group=group0)
        group0.parent_group = group1
        group0.save(update_fields=["parent_group"])
        user = User.objects.create(username="user1")
        user.groups.add(group1)

        self.assertEqual(
            sorted([g.name for g in user.belonging_groups()]), sorted(["group0", "group1"])
        )

    def test_max_users(self):
        User.objects.all().delete()

        max_users = 10
        User.objects.bulk_create([User(username=f"user-{i}") for i in range(max_users)])

        # if the limit exceeded, RuntimeError should be raised
        settings.MAX_USERS = max_users
        with self.assertRaises(RuntimeError):
            User.objects.create(username=f"user-{max_users}")

        # if the limit is not set, RuntimeError should not be raised
        settings.MAX_USERS = None
        User.objects.create(username=f"user-{max_users}")
