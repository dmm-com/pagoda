from typing import TYPE_CHECKING

from django.db import connection
from django.test.utils import CaptureQueriesContext

from airone.lib.acl import ACLType
from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from entity.models import Entity
from entry.api_v2.serializers import GetEntryAttrReferralSerializer
from entry.models import Entry
from role.models import Role

if TYPE_CHECKING:
    from user.models import User


class DisplayAttrTest(AironeViewTest):
    """Coverage for EntityAttr.display_attr — the value of a nominated attr on
    the referred entry is returned as `display_label` in the entry retrieve
    payload for object-like attribute types.
    """

    def setUp(self):
        super().setUp()
        self.user: User = self.guest_login()

        self.ref_entity: Entity = self.create_entity(
            self.user,
            "ServerModel",
            attrs=[
                {"name": "location", "type": AttrType.STRING},
                {"name": "count", "type": AttrType.NUMBER},
                {"name": "is_prod", "type": AttrType.BOOLEAN},
            ],
        )
        self.ref_entry: Entry = self.add_entry(
            self.user,
            "srv-001",
            self.ref_entity,
            values={"location": "tokyo", "count": 12, "is_prod": True},
        )

    def _make_referring_entity(self, attr_type: int, display_attr: str) -> Entity:
        return self.create_entity(
            self.user,
            f"Ref_{attr_type}_{display_attr}",
            attrs=[
                {
                    "name": "ref",
                    "type": attr_type,
                    "ref": self.ref_entity,
                    "display_attr": display_attr,
                },
            ],
        )

    def _attr_value(self, resp, attr_name):
        for a in resp.json()["attrs"]:
            if a["schema"]["name"] == attr_name:
                return a["value"]
        self.fail(f"attr {attr_name} not found in response")

    def test_object_uses_display_attr_string(self):
        entity = self._make_referring_entity(AttrType.OBJECT, "location")
        entry = self.add_entry(self.user, "e0", entity, values={"ref": self.ref_entry.id})
        resp = self.client.get(f"/entry/api/v2/{entry.id}/")
        self.assertEqual(resp.status_code, 200)

        value = self._attr_value(resp, "ref")
        self.assertEqual(value["as_object"]["id"], self.ref_entry.id)
        self.assertEqual(value["as_object"]["name"], "srv-001")
        self.assertEqual(value["as_object"]["display_label"], "tokyo")

    def test_object_uses_display_attr_number(self):
        entity = self._make_referring_entity(AttrType.OBJECT, "count")
        entry = self.add_entry(self.user, "e1", entity, values={"ref": self.ref_entry.id})
        resp = self.client.get(f"/entry/api/v2/{entry.id}/")
        value = self._attr_value(resp, "ref")
        # NUMBER stored as TextField in AttributeValue; expect stringified.
        self.assertEqual(value["as_object"]["display_label"], "12")

    def test_object_uses_display_attr_boolean(self):
        entity = self._make_referring_entity(AttrType.OBJECT, "is_prod")
        entry = self.add_entry(self.user, "e2", entity, values={"ref": self.ref_entry.id})
        value = self._attr_value(self.client.get(f"/entry/api/v2/{entry.id}/"), "ref")
        self.assertEqual(value["as_object"]["display_label"], "true")

    def test_display_attr_empty_omits_label(self):
        """When display_attr is unset, the payload omits display_label entirely
        so pre-existing consumers see the historic shape."""
        entity = self._make_referring_entity(AttrType.OBJECT, "")
        entry = self.add_entry(self.user, "e3", entity, values={"ref": self.ref_entry.id})
        value = self._attr_value(self.client.get(f"/entry/api/v2/{entry.id}/"), "ref")
        self.assertNotIn("display_label", value["as_object"])

    def test_display_attr_missing_on_target_falls_back_to_name(self):
        """When display_attr points to a name that doesn't exist on the
        referred entity, we omit display_label (frontend falls back to name)."""
        entity = self._make_referring_entity(AttrType.OBJECT, "nonexistent")
        entry = self.add_entry(self.user, "e4", entity, values={"ref": self.ref_entry.id})
        value = self._attr_value(self.client.get(f"/entry/api/v2/{entry.id}/"), "ref")
        self.assertNotIn("display_label", value["as_object"])

    def test_array_object_populates_labels_per_element(self):
        # Second referred entry, distinct location
        ref_entry_2 = self.add_entry(
            self.user, "srv-002", self.ref_entity, values={"location": "osaka"}
        )
        entity = self._make_referring_entity(AttrType.ARRAY_OBJECT, "location")
        entry = self.add_entry(
            self.user,
            "e5",
            entity,
            values={"ref": [self.ref_entry.id, ref_entry_2.id]},
        )
        value = self._attr_value(self.client.get(f"/entry/api/v2/{entry.id}/"), "ref")
        labels = {x["id"]: x.get("display_label") for x in value["as_array_object"]}
        self.assertEqual(labels[self.ref_entry.id], "tokyo")
        self.assertEqual(labels[ref_entry_2.id], "osaka")

    def test_named_object_populates_label(self):
        entity = self._make_referring_entity(AttrType.NAMED_OBJECT, "location")
        entry = self.add_entry(
            self.user,
            "e6",
            entity,
            values={"ref": {"name": "primary", "id": self.ref_entry.id}},
        )
        value = self._attr_value(self.client.get(f"/entry/api/v2/{entry.id}/"), "ref")
        self.assertEqual(value["as_named_object"]["name"], "primary")
        self.assertEqual(value["as_named_object"]["object"]["display_label"], "tokyo")

    def test_array_named_object_populates_label_per_element(self):
        ref_entry_2 = self.add_entry(
            self.user, "srv-003", self.ref_entity, values={"location": "nagoya"}
        )
        entity = self._make_referring_entity(AttrType.ARRAY_NAMED_OBJECT, "location")
        entry = self.add_entry(
            self.user,
            "e7",
            entity,
            values={
                "ref": [
                    {"name": "n1", "id": self.ref_entry.id},
                    {"name": "n2", "id": ref_entry_2.id},
                ]
            },
        )
        value = self._attr_value(self.client.get(f"/entry/api/v2/{entry.id}/"), "ref")
        labels = {
            elem["object"]["id"]: elem["object"].get("display_label")
            for elem in value["as_array_named_object"]
        }
        self.assertEqual(labels[self.ref_entry.id], "tokyo")
        self.assertEqual(labels[ref_entry_2.id], "nagoya")

    def test_display_attr_empty_string_value_is_omitted(self):
        """A blank string value should not overshadow Entry.name — omit the key."""
        blank_ref = self.add_entry(self.user, "srv-blank", self.ref_entity, values={"location": ""})
        entity = self._make_referring_entity(AttrType.OBJECT, "location")
        entry = self.add_entry(self.user, "e8", entity, values={"ref": blank_ref.id})
        value = self._attr_value(self.client.get(f"/entry/api/v2/{entry.id}/"), "ref")
        self.assertNotIn("display_label", value["as_object"])

    def test_history_api_carries_display_label(self):
        entity = self._make_referring_entity(AttrType.OBJECT, "location")
        entry = self.add_entry(self.user, "e-hist", entity, values={"ref": self.ref_entry.id})
        # Trigger a second value so a history record is produced.
        entry.attrs.get(schema__name="ref").add_value(self.user, self.ref_entry)

        resp = self.client.get(f"/entry/api/v2/{entry.id}/histories/")
        self.assertEqual(resp.status_code, 200)
        histories = resp.json().get("results", resp.json())
        ref_histories = [h for h in histories if h["parent_attr"]["name"] == "ref"]
        self.assertGreater(len(ref_histories), 0)
        for h in ref_histories:
            curr = h["curr_value"]["as_object"]
            self.assertEqual(curr["display_label"], "tokyo")

    def test_attr_referrals_api_carries_display_label(self):
        entity = self._make_referring_entity(AttrType.OBJECT, "location")
        entity_attr = entity.attrs.get(name="ref")
        resp = self.client.get(f"/entry/api/v2/{entity_attr.id}/attr_referrals/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["results"]
        target = next(r for r in data if r["id"] == self.ref_entry.id)
        self.assertEqual(target["display_label"], "tokyo")

    def test_attr_referrals_api_display_label_null_when_unset(self):
        entity = self._make_referring_entity(AttrType.OBJECT, "")
        entity_attr = entity.attrs.get(name="ref")
        resp = self.client.get(f"/entry/api/v2/{entity_attr.id}/attr_referrals/")
        data = resp.json()["results"]
        target = next(r for r in data if r["id"] == self.ref_entry.id)
        self.assertIsNone(target["display_label"])

    def _make_many_referrals(self, count: int) -> list[Entry]:
        return [
            self.add_entry(
                self.user, f"srv-many-{i}", self.ref_entity, values={"location": f"loc-{i}"}
            )
            for i in range(count)
        ]

    def test_private_display_sources_are_hidden_on_all_read_paths(self):
        """Current and previous history values must use the reader's current ACL."""
        cases = [
            (AttrType.OBJECT, self.ref_entry.id),
            (AttrType.ARRAY_OBJECT, [self.ref_entry.id]),
            (AttrType.NAMED_OBJECT, {"name": "alias", "id": self.ref_entry.id}),
            (AttrType.ARRAY_NAMED_OBJECT, [{"name": "alias", "id": self.ref_entry.id}]),
        ]
        for attr_type, value in cases:
            entity = self._make_referring_entity(attr_type, "location")
            entry = self.add_entry(self.user, f"private-{attr_type}", entity, values={"ref": value})
            attr = entry.attrs.get(schema__name="ref")
            attr.add_value(self.user, value)
            target_attr = self.ref_entry.attrs.get(schema__name="location")
            for protected in (target_attr, target_attr.schema):
                with self.subTest(attr_type=attr_type, protected=type(protected).__name__):
                    protected.is_public = False
                    protected.save()
                    self.assertTrue(self.user.has_permission(self.ref_entry, ACLType.Readable))
                    self.assertFalse(self.user.has_permission(target_attr, ACLType.Readable))
                    urls = [
                        f"/entry/api/v2/{entry.id}/",
                        f"/entry/api/v2/{entry.id}/histories/",
                        f"/entry/api/v2/{attr.schema.id}/attr_referrals/",
                    ]
                    for url in urls:
                        response = self.client.get(url)
                        self.assertEqual(response.status_code, 200)
                        self.assertNotIn("tokyo", response.content.decode())
                    protected.is_public = True
                    protected.save()
                    response = self.client.get(urls[0])
                    self.assertIn("tokyo", response.content.decode())

    def test_object_display_source_checks_referred_entry_and_entity_acl(self):
        hidden_entity = self.create_entity(self.user, "HiddenModel")
        hidden_entry = self.add_entry(self.user, "private-label", hidden_entity)
        self.update_entity(
            self.user,
            self.ref_entity,
            attrs=[{"name": "owner", "type": AttrType.OBJECT, "ref": hidden_entity}],
        )
        self.ref_entry.complement_attrs(self.user)
        self.ref_entry.attrs.get(schema__name="owner").add_value(self.user, hidden_entry)
        entity = self._make_referring_entity(AttrType.OBJECT, "owner")
        entry = self.add_entry(self.user, "object-label", entity, values={"ref": self.ref_entry.id})
        urls = [
            f"/entry/api/v2/{entry.id}/",
            f"/entry/api/v2/{entry.id}/histories/",
            f"/entry/api/v2/{entity.attrs.get(name='ref').id}/attr_referrals/",
        ]
        for protected in (hidden_entry, hidden_entity):
            with self.subTest(protected=type(protected).__name__):
                protected.is_public = False
                protected.save()
                for url in urls:
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    self.assertNotIn("private-label", response.content.decode())
                protected.is_public = True
                protected.save()
        self.assertIn("private-label", self.client.get(urls[0]).content.decode())

    def test_display_label_without_reader_is_hidden(self):
        serializer = GetEntryAttrReferralSerializer(
            self.ref_entry, context={"display_attr_name": "location"}
        )
        self.assertIsNone(serializer.data["display_label"])

    def test_array_object_retrieve_avoids_n_plus_one(self):
        """Regression guard for the prefetch chain — adding more referrals
        must not scale query count linearly when display_attr is set."""
        entity = self._make_referring_entity(AttrType.ARRAY_OBJECT, "location")

        few = self._make_many_referrals(3)
        entry_few = self.add_entry(
            self.user, "app-few", entity, values={"ref": [e.id for e in few]}
        )
        many = self._make_many_referrals(15)
        entry_many = self.add_entry(
            self.user, "app-many", entity, values={"ref": [e.id for e in many]}
        )

        with CaptureQueriesContext(connection) as ctx_few:
            resp = self.client.get(f"/entry/api/v2/{entry_few.id}/")
            self.assertEqual(resp.status_code, 200)
        with CaptureQueriesContext(connection) as ctx_many:
            resp = self.client.get(f"/entry/api/v2/{entry_many.id}/")
            self.assertEqual(resp.status_code, 200)

        # 5x referrals must not translate into 5x queries; a small constant
        # increase is tolerated for auth / permission overhead.
        self.assertLess(
            len(ctx_many.captured_queries) - len(ctx_few.captured_queries),
            10,
            msg=(
                f"query count scales with referrals: "
                f"3 refs => {len(ctx_few.captured_queries)}, "
                f"15 refs => {len(ctx_many.captured_queries)}"
            ),
        )

    def test_role_readable_labels_avoid_n_plus_one_and_refresh_between_requests(self):
        role = Role.objects.create(name="label-reader")
        role.users.add(self.user)
        entity = self._make_referring_entity(AttrType.ARRAY_OBJECT, "location")
        entries = []
        counts = []
        for count in (3, 15):
            referrals = self._make_many_referrals(count)
            for referral in referrals:
                attr = referral.attrs.get(schema__name="location")
                attr.is_public = False
                attr.save()
                attr.readable.roles.add(role)
            entry = self.add_entry(
                self.user, f"role-{count}", entity, values={"ref": [r.id for r in referrals]}
            )
            entries.append(entry)
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(f"/entry/api/v2/{entry.id}/")
            self.assertEqual(response.status_code, 200)
            objects = self._attr_value(response, "ref")["as_array_object"]
            self.assertEqual(len(objects), count)
            self.assertTrue(all(obj.get("display_label") for obj in objects))
            counts.append(len(queries))
        self.assertLess(counts[1] - counts[0], 10, msg=f"Role label query counts: {counts}")

        # A new response must observe revocation rather than a cached grant.
        role.users.remove(self.user)
        response = self.client.get(f"/entry/api/v2/{entries[-1].id}/")
        self.assertTrue(
            all(
                "display_label" not in obj
                for obj in self._attr_value(response, "ref")["as_array_object"]
            )
        )

    def test_role_readable_attribute_does_not_bypass_parent_acl(self):
        role = Role.objects.create(name="label-reader")
        role.users.add(self.user)
        attr = self.ref_entry.attrs.get(schema__name="location")
        attr.is_public = False
        attr.save()
        attr.readable.roles.add(role)
        entity = self._make_referring_entity(AttrType.OBJECT, "location")
        entry = self.add_entry(self.user, "parent-acl", entity, values={"ref": self.ref_entry.id})
        for protected in (attr.schema, self.ref_entry, self.ref_entity):
            with self.subTest(protected=type(protected).__name__):
                protected.is_public = False
                protected.save()
                response = self.client.get(f"/entry/api/v2/{entry.id}/")
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("tokyo", response.content.decode())
                protected.is_public = True
                protected.save()

    def test_history_api_avoids_n_plus_one(self):
        entity = self._make_referring_entity(AttrType.OBJECT, "location")
        entry = self.add_entry(self.user, "app-hist-n1", entity, values={"ref": self.ref_entry.id})
        # emit several history records against the same referring attr
        for _ in range(3):
            entry.attrs.get(schema__name="ref").add_value(self.user, self.ref_entry)

        with CaptureQueriesContext(connection) as ctx_few:
            resp = self.client.get(f"/entry/api/v2/{entry.id}/histories/")
            self.assertEqual(resp.status_code, 200)

        # emit more history records; query count should stay roughly flat.
        for _ in range(10):
            entry.attrs.get(schema__name="ref").add_value(self.user, self.ref_entry)

        with CaptureQueriesContext(connection) as ctx_many:
            resp = self.client.get(f"/entry/api/v2/{entry.id}/histories/")
            self.assertEqual(resp.status_code, 200)

        self.assertLess(
            len(ctx_many.captured_queries) - len(ctx_few.captured_queries),
            10,
            msg=(
                f"history query count scales with rows: "
                f"few => {len(ctx_few.captured_queries)}, "
                f"many => {len(ctx_many.captured_queries)}"
            ),
        )
