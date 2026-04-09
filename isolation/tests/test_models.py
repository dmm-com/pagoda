from airone.lib.test import AironeTestCase
from airone.lib.types import AttrType
from isolation.models import IsolationAction, IsolationCondition, IsolationParent
from user.models import User


class IsolationModelTest(AironeTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="test")

        # entity_item: the entity whose entries may be isolated
        self.entity_item = self.create_entity(
            self.user,
            "Item",
            attrs=[
                {"name": "status", "type": AttrType.STRING},
                {"name": "is_active", "type": AttrType.BOOLEAN},
            ],
        )

        # entity_consumer: the entity that references Item entries
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

        # entity_other: another entity (should not be affected by consumer-targeted rules)
        self.entity_other = self.create_entity(self.user, "Other")

    def _make_parent(self, prevent_from=None, is_prevent_all=False):
        parent = IsolationParent.objects.create(entity=self.entity_item)
        IsolationAction.objects.create(
            parent=parent,
            prevent_from=prevent_from,
            is_prevent_all=is_prevent_all,
        )
        return parent

    def _add_string_condition(self, parent, attr_name, str_cond, is_unmatch=False):
        attr = self.entity_item.attrs.get(name=attr_name)
        IsolationCondition.objects.create(
            parent=parent,
            attr=attr,
            str_cond=str_cond,
            is_unmatch=is_unmatch,
        )

    def _add_bool_condition(self, parent, attr_name, bool_cond, is_unmatch=False):
        attr = self.entity_item.attrs.get(name=attr_name)
        IsolationCondition.objects.create(
            parent=parent,
            attr=attr,
            bool_cond=bool_cond,
            is_unmatch=is_unmatch,
        )

    # -----------------------------------------------------------------------
    # is_entry_isolated
    # -----------------------------------------------------------------------

    def test_string_condition_matches_correctly(self):
        entry = self.add_entry(self.user, "item1", self.entity_item, values={"status": "inactive"})
        parent = self._make_parent(prevent_from=self.entity_consumer)
        self._add_string_condition(parent, "status", "inactive")

        self.assertTrue(parent.is_entry_isolated(entry, self.entity_consumer))

    def test_string_condition_no_match(self):
        entry = self.add_entry(self.user, "item1", self.entity_item, values={"status": "active"})
        parent = self._make_parent(prevent_from=self.entity_consumer)
        self._add_string_condition(parent, "status", "inactive")

        self.assertFalse(parent.is_entry_isolated(entry, self.entity_consumer))

    def test_bool_condition_matches(self):
        entry = self.add_entry(self.user, "item1", self.entity_item, values={"is_active": False})
        parent = self._make_parent(prevent_from=self.entity_consumer)
        self._add_bool_condition(parent, "is_active", False)

        self.assertTrue(parent.is_entry_isolated(entry, self.entity_consumer))

    def test_is_unmatch_inverts_result(self):
        # Entry has status="active"; condition is str_cond="inactive" with is_unmatch=True
        # → matches because "active" != "inactive"
        entry = self.add_entry(self.user, "item1", self.entity_item, values={"status": "active"})
        parent = self._make_parent(prevent_from=self.entity_consumer)
        self._add_string_condition(parent, "status", "inactive", is_unmatch=True)

        self.assertTrue(parent.is_entry_isolated(entry, self.entity_consumer))

    def test_is_prevent_all_blocks_any_entity(self):
        entry = self.add_entry(self.user, "item1", self.entity_item, values={"status": "inactive"})
        parent = self._make_parent(is_prevent_all=True)
        self._add_string_condition(parent, "status", "inactive")

        self.assertTrue(parent.is_entry_isolated(entry, self.entity_consumer))
        self.assertTrue(parent.is_entry_isolated(entry, self.entity_other))

    def test_prevent_from_only_blocks_specified_entity(self):
        entry = self.add_entry(self.user, "item1", self.entity_item, values={"status": "inactive"})
        parent = self._make_parent(prevent_from=self.entity_consumer)
        self._add_string_condition(parent, "status", "inactive")

        self.assertTrue(parent.is_entry_isolated(entry, self.entity_consumer))
        self.assertFalse(parent.is_entry_isolated(entry, self.entity_other))

    # -----------------------------------------------------------------------
    # AND / OR logic
    # -----------------------------------------------------------------------

    def test_and_logic_both_conditions_must_match(self):
        # Two conditions in same parent → AND
        entry = self.add_entry(
            self.user,
            "item1",
            self.entity_item,
            values={"status": "inactive", "is_active": False},
        )
        parent = self._make_parent(prevent_from=self.entity_consumer)
        self._add_string_condition(parent, "status", "inactive")
        self._add_bool_condition(parent, "is_active", False)

        self.assertTrue(parent.is_entry_isolated(entry, self.entity_consumer))

    def test_and_logic_partial_match_is_not_isolated(self):
        entry = self.add_entry(
            self.user,
            "item1",
            self.entity_item,
            values={"status": "inactive", "is_active": True},
        )
        parent = self._make_parent(prevent_from=self.entity_consumer)
        self._add_string_condition(parent, "status", "inactive")
        self._add_bool_condition(parent, "is_active", False)

        self.assertFalse(parent.is_entry_isolated(entry, self.entity_consumer))

    def test_or_logic_either_parent_matches(self):
        # Two IsolationParents → OR (any match isolates the entry)
        entry = self.add_entry(self.user, "item1", self.entity_item, values={"status": "archived"})

        parent1 = self._make_parent(prevent_from=self.entity_consumer)
        self._add_string_condition(parent1, "status", "inactive")

        parent2 = self._make_parent(prevent_from=self.entity_consumer)
        self._add_string_condition(parent2, "status", "archived")

        self.assertFalse(parent1.is_entry_isolated(entry, self.entity_consumer))
        self.assertTrue(parent2.is_entry_isolated(entry, self.entity_consumer))

    # -----------------------------------------------------------------------
    # get_isolated_entry_ids
    # -----------------------------------------------------------------------

    def test_get_isolated_entry_ids_excludes_matching_entries(self):
        from entry.models import Entry

        entry_ok = self.add_entry(self.user, "ok", self.entity_item, values={"status": "active"})
        entry_ng = self.add_entry(self.user, "ng", self.entity_item, values={"status": "inactive"})

        parent = self._make_parent(prevent_from=self.entity_consumer)
        self._add_string_condition(parent, "status", "inactive")

        qs = Entry.objects.filter(schema=self.entity_item, is_active=True)
        isolated = IsolationParent.get_isolated_entry_ids(qs, self.entity_consumer)

        self.assertIn(entry_ng.id, isolated)
        self.assertNotIn(entry_ok.id, isolated)

    def test_get_isolated_entry_ids_empty_when_no_rules(self):
        from entry.models import Entry

        self.add_entry(self.user, "item1", self.entity_item, values={"status": "inactive"})

        qs = Entry.objects.filter(schema=self.entity_item, is_active=True)
        isolated = IsolationParent.get_isolated_entry_ids(qs, self.entity_consumer)

        self.assertEqual(isolated, set())
