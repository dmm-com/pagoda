from airone.lib.test import AironeTestCase
from airone.lib.types import AttrTypeValue
from trigger.models import (
    InputTriggerAction,
    InputTriggerActionValue,
    InputTriggerCondition,
    TriggerAction,
    TriggerActionValue,
    TriggerCondition,
    TriggerParentCondition,
)
from user.models import User


class ModelTest(AironeTestCase):
    def setUp(self):
        super(ModelTest, self).setUp()

        self.user: User = User.objects.create(username="test")
        self.entity_ref = self.create_entity(self.user, "test_entity_ref")
        self.entity = self.create_entity(
            self.user,
            "test_entity",
            attrs=[
                # These are attributes that are used for trigger
                {"name": "str_trigger", "type": AttrTypeValue["string"]},
                {"name": "ref_trigger", "type": AttrTypeValue["object"], "ref": self.entity_ref},
                {
                    "name": "named_trigger",
                    "type": AttrTypeValue["named_object"],
                    "ref": self.entity_ref,
                },
                {"name": "arr_str_trigger", "type": AttrTypeValue["array_string"]},
                {
                    "name": "arr_ref_trigger",
                    "type": AttrTypeValue["array_object"],
                    "ref": self.entity_ref,
                },
                {
                    "name": "arr_named_trigger",
                    "type": AttrTypeValue["array_named_object"],
                    "ref": self.entity_ref,
                },
                {"name": "bool_trigger", "type": AttrTypeValue["boolean"]},
                # These are attributes that are used for action
                {"name": "str_action", "type": AttrTypeValue["string"]},
                {"name": "ref_action", "type": AttrTypeValue["object"], "ref": self.entity_ref},
                {
                    "name": "named_action",
                    "type": AttrTypeValue["named_object"],
                    "ref": self.entity_ref,
                },
                {"name": "arr_str_action", "type": AttrTypeValue["array_string"]},
                {
                    "name": "arr_ref_action",
                    "type": AttrTypeValue["array_object"],
                    "ref": self.entity_ref,
                },
                {
                    "name": "arr_named_action",
                    "type": AttrTypeValue["array_named_object"],
                    "ref": self.entity_ref,
                },
                {"name": "bool_action", "type": AttrTypeValue["boolean"]},
            ],
        )

    def test_input_airone_trigger_action(self):
        entries = [self.add_entry(self.user, "test_entry_%s" % i, self.entity) for i in range(3)]

        TEST_CONDITIONS = [
            {"attr_id": self.entity.attrs.get(name="str_trigger").id, "str_cond": "test"},
            {"attr_id": self.entity.attrs.get(name="ref_trigger").id, "ref_cond": entries[0].id},
            {
                "attr_id": self.entity.attrs.get(name="named_trigger").id,
                "str_cond": "test",
                "ref_cond": entries[0].id,
            },
            {"attr_id": self.entity.attrs.get(name="arr_str_trigger").id, "str_cond": "test"},
            {
                "attr_id": self.entity.attrs.get(name="arr_ref_trigger").id,
                "ref_cond": entries[0].id,
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_named_trigger").id,
                "str_cond": "test",
                "ref_cond": entries[0].id,
            },
            {"attr_id": self.entity.attrs.get(name="bool_trigger").id, "bool_cond": False},
        ]
        for cond in TEST_CONDITIONS:
            input_trigger_condition = InputTriggerCondition(**cond)
            self.assertEqual(input_trigger_condition.attr.id, cond["attr_id"])
            self.assertEqual(input_trigger_condition.str_cond, cond.get("str_cond", ""))
            self.assertEqual(input_trigger_condition.bool_cond, cond.get("bool_cond", False))
            if cond.get("ref_cond", None):
                self.assertEqual(input_trigger_condition.ref_cond.id, cond.get("ref_cond", None))

    def test_create_trigger_action_initialization(self):
        entries = [self.add_entry(self.user, "test_entry_%s" % i, self.entity) for i in range(3)]

        # NOTE: This only assume partial match. When the specification is change to expand to support
        #       full match, this test should be updated.
        settingTriggerConditions = [
            {"attr_id": self.entity.attrs.get(name="str_trigger").id, "str_cond": "test"},
            {"attr_id": self.entity.attrs.get(name="ref_trigger").id, "ref_cond": entries[0].id},
            {
                "attr_id": self.entity.attrs.get(name="named_trigger").id,
                "str_cond": "test",
                "ref_cond": entries[0].id,
            },
            {"attr_id": self.entity.attrs.get(name="bool_trigger").id, "bool_cond": False},
            {"attr_id": self.entity.attrs.get(name="arr_str_trigger").id, "str_cond": "test"},
            {
                "attr_id": self.entity.attrs.get(name="arr_ref_trigger").id,
                "ref_cond": entries[0].id,
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_named_trigger").id,
                "str_cond": "test",
                "ref_cond": entries[0].id,
            },
        ]
        settingTriggerActions = [
            {"attr_id": self.entity.attrs.get(name="str_action").id, "value": "changed_value"},
            {"attr_id": self.entity.attrs.get(name="ref_action").id, "value": entries[1].id},
            {
                "attr_id": self.entity.attrs.get(name="named_action").id,
                "value": {"name": "changed_value", "id": entries[1].id},
            },
            {"attr_id": self.entity.attrs.get(name="bool_action").id, "value": True},
            {
                "attr_id": self.entity.attrs.get(name="arr_str_action").id,
                "value": ["foo", "bar", "baz"],
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_ref_action").id,
                "value": [x.id for x in entries],
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_named_action").id,
                "value": [
                    {"name": "foo", "id": entries[0].id},
                    {"name": "bar", "id": None},
                    {"name": "", "id": entries[2].id},
                ],
            },
        ]

        # This tests processing to initialize Airone Triggers and its Actions
        TriggerCondition.register(self.entity, settingTriggerConditions, settingTriggerActions)

        # This checks expected Trigger condition objects would be created
        parent_conditions = TriggerParentCondition.objects.filter(entity=self.entity)
        self.assertEqual(parent_conditions.count(), 1)

        trigger_conditions = TriggerCondition.objects.filter(parent=parent_conditions[0])
        self.assertEqual(trigger_conditions.count(), len(settingTriggerConditions))
        # omit tests for TriggerCondition context

        # This checks expected Trigger action objects would be created
        trigger_actions = TriggerAction.objects.filter(condition=parent_conditions[0])
        self.assertEqual(trigger_actions.count(), len(settingTriggerActions))

        for trigger_action in trigger_actions:
            if trigger_action.attr.type & AttrTypeValue["array"]:
                self.assertEqual(trigger_action.values.count(), 3)
            else:
                self.assertEqual(trigger_action.values.count(), 1)

    def test_condition_is_invoked(self):
        entry_refs = [self.add_entry(self.user, "ref-%s" % i, self.entity_ref) for i in range(3)]
        entry = self.add_entry(self.user, "test_entry", self.entity)

        # register TriggerCondition and its Actions
        settingTriggerConditions = [
            {"attr_id": self.entity.attrs.get(name="str_trigger").id, "str_cond": "test"},
        ]
        settingTriggerActions = [
            {"attr_id": self.entity.attrs.get(name="str_action").id, "value": "changed_value"},
            {"attr_id": self.entity.attrs.get(name="ref_action").id, "value": entry_refs[0]},
            {"attr_id": self.entity.attrs.get(name="bool_action").id, "value": True},
            {"attr_id": self.entity.attrs.get(name="named_action").id, "value": {
                "name": "changed_value",
                "id": entry_refs[0],
            }},
            {"attr_id": self.entity.attrs.get(name="arr_str_action").id, "value": ["foo", "bar", "baz"]},
            {"attr_id": self.entity.attrs.get(name="arr_ref_action").id, "value": entry_refs},
            {"attr_id": self.entity.attrs.get(name="arr_named_action").id, "value": [
                {"name": "foo", "id": entry_refs[0]},
                {"name": "bar", "id": entry_refs[1]},
                {"name": "baz", "id": entry_refs[2]},
            ]},
        ]
        parent_condition = TriggerCondition.register(self.entity, settingTriggerConditions, settingTriggerActions)

        # TriggerCondition.is_invoked() returns empty array when unrelevant attribute is updated
        trigger_actions = parent_condition.get_actions([
            {"attr_id": entry.attrs.get(schema__name="ref_trigger").schema.id, "value": entry_refs[0].id},
        ])
        self.assertEqual(trigger_actions, [])

        # This checks TriggerParentCondition.get_actions() returns expected TriggerActions
        # and they have expected context (TriggerActionValue).
        trigger_actions = parent_condition.get_actions([
            {"attr_id": entry.attrs.get(schema__name="str_trigger").schema.id, "value": "test"},
            {"attr_id": entry.attrs.get(schema__name="ref_trigger").schema.id, "value": entry_refs[0].id},
        ])
        self.assertEqual(len(trigger_actions), 7)
        self.assertTrue(all([isinstance(a, TriggerAction) for a in trigger_actions]))
        for (index, trigger_action) in enumerate(trigger_actions):
            self.assertEqual(trigger_action.attr.id, settingTriggerActions[index]["attr_id"])

        # This checks each TriggerActionValue has expected context
        self.assertEqual(trigger_actions[0].values.count(), 1)
        self.assertEqual(trigger_actions[0].values.first().str_cond, "changed_value")

        self.assertEqual(trigger_actions[1].values.count(), 1)
        self.assertEqual(trigger_actions[1].values.first().ref_cond, entry_refs[0])

        self.assertEqual(trigger_actions[2].values.count(), 1)
        self.assertEqual(trigger_actions[2].values.first().bool_cond, True)

        self.assertEqual(trigger_actions[3].values.count(), 1)
        self.assertEqual(trigger_actions[3].values.first().str_cond, "changed_value")
        self.assertEqual(trigger_actions[3].values.first().ref_cond, entry_refs[0])

        self.assertEqual(trigger_actions[4].values.count(), 3)
        self.assertEqual([x.str_cond for x in trigger_actions[4].values.all()], ["foo", "bar", "baz"])

        self.assertEqual(trigger_actions[5].values.count(), 3)
        self.assertEqual([x.ref_cond for x in trigger_actions[5].values.all()], entry_refs)

        self.assertEqual(trigger_actions[6].values.count(), 3)
        self.assertEqual([(x.str_cond, x.ref_cond) for x in trigger_actions[6].values.all()],
                         [("foo", entry_refs[0]), ("bar", entry_refs[1]), ("baz", entry_refs[2])])

    def test_run_trigger_action(self):
        # This test to run TriggerAction and check Entry is updated as expected