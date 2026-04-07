import json
from unittest import mock

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from entity import tasks as entity_tasks
from isolation.models import IsolationAction, IsolationCondition, IsolationParent


class IsolationAPITest(AironeViewTest):
    def setUp(self):
        super().setUp()
        self.user = self.guest_login()

        self.entity_item = self.create_entity(
            self.user,
            "Item",
            attrs=[
                {"name": "status", "type": AttrType.STRING},
            ],
        )
        self.entity_consumer = self.create_entity(
            self.user,
            "Consumer",
            attrs=[
                {
                    "name": "item_ref",
                    "type": AttrType.OBJECT,
                    "ref": self.entity_item,
                }
            ],
        )

    # -----------------------------------------------------------------------
    # Entity detail includes isolation_rules
    # -----------------------------------------------------------------------

    def test_entity_detail_returns_isolation_rules(self):
        parent = IsolationParent.objects.create(entity=self.entity_item)
        IsolationCondition.objects.create(
            parent=parent,
            attr=self.entity_item.attrs.get(name="status"),
            str_cond="inactive",
        )
        IsolationAction.objects.create(
            parent=parent,
            prevent_from=self.entity_consumer,
            is_prevent_all=False,
        )

        resp = self.client.get(f"/entity/api/v2/{self.entity_item.id}/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIn("isolation_rules", data)
        self.assertEqual(len(data["isolation_rules"]), 1)

        rule = data["isolation_rules"][0]
        self.assertEqual(len(rule["conditions"]), 1)
        self.assertEqual(rule["conditions"][0]["str_cond"], "inactive")
        self.assertEqual(rule["action"]["prevent_from"], {
            "id": self.entity_consumer.id,
            "name": self.entity_consumer.name,
        })
        self.assertFalse(rule["action"]["is_prevent_all"])

    # -----------------------------------------------------------------------
    # Entity update adds isolation rule
    # -----------------------------------------------------------------------

    @mock.patch(
        "entity.tasks.edit_entity_v2.delay", mock.Mock(side_effect=entity_tasks.edit_entity_v2)
    )
    def test_entity_update_adds_isolation_rule(self):
        attr = self.entity_item.attrs.get(name="status")
        resp = self.client.put(
            f"/entity/api/v2/{self.entity_item.id}/",
            json.dumps(
                {
                    "isolation_rules": [
                        {
                            "conditions": [
                                {
                                    "attr_id": attr.id,
                                    "str_cond": "inactive",
                                    "is_unmatch": False,
                                }
                            ],
                            "action": {
                                "is_prevent_all": False,
                                "prevent_from_id": self.entity_consumer.id,
                            },
                        }
                    ]
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 202)

        parents = IsolationParent.objects.filter(entity=self.entity_item)
        self.assertEqual(parents.count(), 1)
        parent = parents.first()
        self.assertEqual(parent.conditions.count(), 1)
        self.assertEqual(parent.conditions.first().str_cond, "inactive")
        self.assertEqual(parent.action.prevent_from, self.entity_consumer)

    @mock.patch(
        "entity.tasks.edit_entity_v2.delay", mock.Mock(side_effect=entity_tasks.edit_entity_v2)
    )
    def test_entity_update_deletes_isolation_rule(self):
        parent = IsolationParent.objects.create(entity=self.entity_item)
        IsolationCondition.objects.create(
            parent=parent,
            attr=self.entity_item.attrs.get(name="status"),
            str_cond="inactive",
        )
        IsolationAction.objects.create(parent=parent, is_prevent_all=True)

        resp = self.client.put(
            f"/entity/api/v2/{self.entity_item.id}/",
            json.dumps(
                {
                    "isolation_rules": [
                        {"id": parent.id, "is_deleted": True, "conditions": [], "action": {}}
                    ]
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 202)

        self.assertFalse(IsolationParent.objects.filter(id=parent.id).exists())

    # -----------------------------------------------------------------------
    # EntryAttrReferralsAPI isolation enforcement
    # -----------------------------------------------------------------------

    def test_referral_list_excludes_isolated_entries(self):
        entry_ok = self.add_entry(
            self.user, "active_item", self.entity_item, values={"status": "active"}
        )
        entry_ng = self.add_entry(
            self.user, "inactive_item", self.entity_item, values={"status": "inactive"}
        )

        parent = IsolationParent.objects.create(entity=self.entity_item)
        IsolationCondition.objects.create(
            parent=parent,
            attr=self.entity_item.attrs.get(name="status"),
            str_cond="inactive",
        )
        IsolationAction.objects.create(
            parent=parent,
            prevent_from=self.entity_consumer,
            is_prevent_all=False,
        )

        # entity attribute on Consumer that references Item entries
        consumer_attr = self.entity_consumer.attrs.get(name="item_ref")
        resp = self.client.get(f"/entry/api/v2/{consumer_attr.id}/attr_referrals/")
        self.assertEqual(resp.status_code, 200)

        result_ids = [item["id"] for item in resp.json()]
        self.assertIn(entry_ok.id, result_ids)
        self.assertNotIn(entry_ng.id, result_ids)

    def test_referral_list_not_filtered_for_other_entity(self):
        """A rule targeting a different entity should not affect the consumer's referral list."""
        entry_ng = self.add_entry(
            self.user, "inactive_item", self.entity_item, values={"status": "inactive"}
        )

        entity_unrelated = self.create_entity(self.user, "Unrelated")
        parent = IsolationParent.objects.create(entity=self.entity_item)
        IsolationCondition.objects.create(
            parent=parent,
            attr=self.entity_item.attrs.get(name="status"),
            str_cond="inactive",
        )
        IsolationAction.objects.create(
            parent=parent,
            prevent_from=entity_unrelated,
            is_prevent_all=False,
        )

        consumer_attr = self.entity_consumer.attrs.get(name="item_ref")
        resp = self.client.get(f"/entry/api/v2/{consumer_attr.id}/attr_referrals/")
        self.assertEqual(resp.status_code, 200)

        result_ids = [item["id"] for item in resp.json()]
        # The rule targets entity_unrelated, so it should not affect consumer's referral list
        self.assertIn(entry_ng.id, result_ids)
