from unittest.mock import Mock, patch

from airone.lib.acl import ACLType
from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from entry import tasks
from job.models import Job
from role.models import Role


class CascadeACLTest(AironeViewTest):
    """A source mutation never grants write access to its cascade targets."""

    def setUp(self):
        super().setUp()
        self.user = self.guest_login()
        self.target_model = self.create_entity(self.user, "Target")
        self.target = self.add_entry(self.user, "target", self.target_model)
        self.source_model = self.create_entity(
            self.user,
            "Source",
            attrs=[
                {
                    "name": "ref",
                    "type": AttrType.OBJECT,
                    "ref": self.target_model,
                    "is_delete_in_chain": True,
                }
            ],
        )
        self.source_model.attrs.update(is_delete_in_chain=True)
        self.source = self.add_entry(
            self.user, "source", self.source_model, values={"ref": self.target}
        )

    def _restrict(self, obj):
        obj.refresh_from_db()
        obj.is_public = False
        obj.default_permission = ACLType.Readable.id
        obj.save()

    def test_delete_preserves_target_without_entry_or_entity_write_access(self):
        for protected in (self.target, self.target_model):
            with self.subTest(protected=type(protected).__name__):
                self._restrict(protected)
                self.source.delete(deleted_user=self.user)
                self.target.refresh_from_db()
                self.assertTrue(self.target.is_active)
                self.assertIsNone(self.target.deleted_user)
                self.source.restore(user=self.user)
                protected.is_public = True
                protected.save()

    def test_restore_preserves_target_without_entry_or_entity_write_access(self):
        for protected in (self.target, self.target_model):
            with self.subTest(protected=type(protected).__name__):
                self.source.delete(deleted_user=self.user)
                self._restrict(protected)
                self.source.restore(user=self.user)
                self.source.refresh_from_db()
                self.target.refresh_from_db()
                self.assertTrue(self.source.is_active)
                self.assertFalse(self.target.is_active)
                protected.is_public = True
                protected.save()
                self.target.restore(user=self.user)

    def test_actorless_entry_and_attribute_mutations_do_not_cascade(self):
        self.source.delete()
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)
        self.target.delete()
        self.source.restore()
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)
        self.target.restore()
        attr = self.source.attrs.get(schema__name="ref")
        attr.delete()
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)
        self.target.delete()
        attr.restore()
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

    def test_multi_hop_delete_and_restore_propagate_actor_and_check_each_target(self):
        self.update_entity(
            self.user,
            self.target_model,
            attrs=[
                {
                    "name": "next",
                    "type": AttrType.OBJECT,
                    "ref": self.target_model,
                    "is_delete_in_chain": True,
                }
            ],
        )
        self.target.complement_attrs(self.user)
        self.target_model.attrs.update(is_delete_in_chain=True)
        leaf = self.add_entry(self.user, "leaf", self.target_model)
        self.target.attrs.get(schema__name="next").add_value(self.user, leaf)
        self._restrict(leaf)
        self.source.delete(deleted_user=self.user)
        self.target.refresh_from_db()
        leaf.refresh_from_db()
        self.assertFalse(self.target.is_active)
        self.assertEqual(self.target.deleted_user, self.user)
        self.assertEqual(self.target.history.first().history_user, self.user)
        self.assertTrue(leaf.is_active)
        self.source.restore(user=self.user)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)
        leaf.is_public = True
        leaf.save()
        self.source.delete(deleted_user=self.user)
        self._restrict(leaf)
        self.source.restore(user=self.user)
        self.target.refresh_from_db()
        leaf.refresh_from_db()
        self.assertTrue(self.target.is_active)
        self.assertFalse(leaf.is_active)

    def test_role_granted_target_still_cascades(self):
        self._restrict(self.target)
        role = Role.objects.create(name="writer")
        role.users.add(self.user)
        self.target.writable.roles.add(role)
        self.source.delete(deleted_user=self.user)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)
        self.source.restore(user=self.user)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    def test_object_variants_check_each_cascade_target(self):
        allowed = self.add_entry(self.user, "allowed", self.target_model)
        for attr_type, value in [
            (AttrType.ARRAY_OBJECT, [self.target, allowed]),
            (AttrType.NAMED_OBJECT, {"name": "blocked", "id": self.target}),
            (
                AttrType.ARRAY_NAMED_OBJECT,
                [{"name": "blocked", "id": self.target}, {"name": "allowed", "id": allowed}],
            ),
            (AttrType.NAMED_OBJECT_BOOLEAN, {"name": "blocked", "id": self.target}),
            (
                AttrType.ARRAY_NAMED_OBJECT_BOOLEAN,
                [{"name": "blocked", "id": self.target}, {"name": "allowed", "id": allowed}],
            ),
        ]:
            with self.subTest(attr_type=attr_type):
                schema = self.source_model.attrs.get(name="ref")
                schema.type = attr_type
                schema.save()
                attr = self.source.attrs.get(schema=schema)
                attr.add_value(self.user, value)
                self._restrict(self.target)
                self.source.delete(deleted_user=self.user)
                self.target.refresh_from_db()
                allowed.refresh_from_db()
                self.assertTrue(self.target.is_active)
                if attr_type & AttrType._ARRAY:
                    self.assertFalse(allowed.is_active)
                self.source.restore(user=self.user)
                allowed.refresh_from_db()
                self.assertTrue(allowed.is_active)
                self.target.delete()
                attr.delete()
                attr.restore(user=self.user)
                self.target.refresh_from_db()
                self.assertFalse(self.target.is_active)
                self.target.restore()

    def test_attribute_complement_checks_restore_target_acl(self):
        self.source.delete(deleted_user=self.user)
        self._restrict(self.target)
        schema = self.source_model.attrs.get(name="ref")
        self.source.add_attribute_from_base(schema, self.user)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)
        self.source.attrs.get(schema=schema).delete()
        self.target.is_public = True
        self.target.save()
        self.source.add_attribute_from_base(schema, self.user)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    def test_readonly_actor_cannot_cascade_even_to_public_targets(self):
        self.user.is_readonly = True
        self.user.save()
        self.source.delete(deleted_user=self.user)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)
        self.target.delete()
        self.source.restore(user=self.user)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    def test_v2_delete_and_restore_use_request_actor(self):
        response = self.client.delete(f"/entry/api/v2/{self.source.id}/")
        self.assertEqual(response.status_code, 204)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)
        response = self.client.post(f"/entry/api/v2/{self.source.id}/restore/")
        self.assertEqual(response.status_code, 201)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    @patch("entry.tasks.delete_entry_v2.delay", Mock(side_effect=tasks.delete_entry_v2))
    def test_v2_requests_preserve_unwritable_target(self):
        self._restrict(self.target)
        response = self.client.delete(f"/entry/api/v2/{self.source.id}/")
        self.assertEqual(response.status_code, 204)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)
        self.target.delete()
        response = self.client.post(f"/entry/api/v2/{self.source.id}/restore/")
        self.assertEqual(response.status_code, 201)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

    def test_legacy_jobs_propagate_actor(self):
        tasks.delete_entry(Job.new_delete(self.user, self.source).id)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)
        tasks.restore_entry(Job.new_restore(self.user, self.source).id)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)
