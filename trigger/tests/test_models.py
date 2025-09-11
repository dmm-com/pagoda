import json

import mock

from airone.lib.test import AironeTestCase
from airone.lib.types import AttrType
from entry.models import AttributeValue
from trigger import tasks as trigger_tasks
from trigger.models import (
    InputTriggerCondition,
    TriggerAction,
    TriggerActionValue,
    TriggerCondition,
    TriggerParent,
)
from user.models import User

FAT_LADY_PASSWDS = ["Caputo Draconis", "Pig snout"]


class ModelTest(AironeTestCase):
    def setUp(self):
        super(ModelTest, self).setUp()

        self.user = User.objects.create(username="test")
        self.entity_ref = self.create_entity(self.user, "test_entity_ref")
        self.entity = self.create_entity(
            self.user,
            "test_entity",
            attrs=[
                # These are attributes that are used for trigger
                {"name": "str_trigger", "type": AttrType.STRING},
                {
                    "name": "ref_trigger",
                    "type": AttrType.OBJECT,
                    "ref": self.entity_ref,
                },
                {
                    "name": "named_trigger",
                    "type": AttrType.NAMED_OBJECT,
                    "ref": self.entity_ref,
                },
                {
                    "name": "named_trigger2",
                    "type": AttrType.NAMED_OBJECT,
                    "ref": self.entity_ref,
                },
                {"name": "arr_str_trigger", "type": AttrType.ARRAY_STRING},
                {
                    "name": "arr_ref_trigger",
                    "type": AttrType.ARRAY_OBJECT,
                    "ref": self.entity_ref,
                },
                {
                    "name": "arr_named_trigger",
                    "type": AttrType.ARRAY_NAMED_OBJECT,
                    "ref": self.entity_ref,
                },
                {"name": "bool_trigger", "type": AttrType.BOOLEAN},
                # These are attributes that are used for action
                {"name": "str_action", "type": AttrType.STRING},
                {
                    "name": "ref_action",
                    "type": AttrType.OBJECT,
                    "ref": self.entity_ref,
                },
                {
                    "name": "named_action",
                    "type": AttrType.NAMED_OBJECT,
                    "ref": self.entity_ref,
                },
                {"name": "arr_str_action", "type": AttrType.ARRAY_STRING},
                {
                    "name": "arr_ref_action",
                    "type": AttrType.ARRAY_OBJECT,
                    "ref": self.entity_ref,
                },
                {
                    "name": "arr_named_action",
                    "type": AttrType.ARRAY_NAMED_OBJECT,
                    "ref": self.entity_ref,
                },
                {"name": "bool_action", "type": AttrType.BOOLEAN},
            ],
        )

        self.entry_refs = [
            self.add_entry(self.user, "ref-%s" % i, self.entity_ref) for i in range(3)
        ]
        self.FULL_CONDITION_CONFIGURATION_PARAMETERS = [
            {
                "attr_id": self.entity.attrs.get(name="str_trigger").id,
                "cond": FAT_LADY_PASSWDS[0],
            },
            {
                "attr_id": self.entity.attrs.get(name="ref_trigger").id,
                "cond": self.entry_refs[2],
            },
            {"attr_id": self.entity.attrs.get(name="bool_trigger").id, "cond": True},
            {
                "attr_id": self.entity.attrs.get(name="named_trigger").id,
                "cond": FAT_LADY_PASSWDS[0],
            },
            {
                "attr_id": self.entity.attrs.get(name="named_trigger").id,
                "cond": self.entry_refs[2],
                "hint": "entry",
            },
            {
                "attr_id": self.entity.attrs.get(name="named_trigger2").id,
                "cond": json.dumps({"name": FAT_LADY_PASSWDS[1], "id": self.entry_refs[1].id}),
                "hint": "json",
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_str_trigger").id,
                "cond": FAT_LADY_PASSWDS[0],
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_ref_trigger").id,
                "cond": self.entry_refs[2],
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_named_trigger").id,
                "cond": FAT_LADY_PASSWDS[0],
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_named_trigger").id,
                "cond": self.entry_refs[2],
                "hint": "entry",
            },
        ]
        self.FULL_CONDITION_CONFIGURATION_PARAMETERS_BUT_EMPTY = [
            {
                "attr_id": self.entity.attrs.get(name="str_trigger").id,
                "cond": "",
            },
            {
                "attr_id": self.entity.attrs.get(name="ref_trigger").id,
                "cond": None,
            },
            {"attr_id": self.entity.attrs.get(name="bool_trigger").id, "cond": False},
            {
                "attr_id": self.entity.attrs.get(name="arr_str_trigger").id,
                "cond": "",
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_ref_trigger").id,
                "cond": None,
            },
            {
                "attr_id": self.entity.attrs.get(name="named_trigger").id,
                "cond": "",
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_named_trigger").id,
                "cond": "",
            },
        ]
        self.FULL_ACTION_CONFIGURATION_PARAMETERS = [
            {
                "attr_id": self.entity.attrs.get(name="str_action").id,
                "value": "changed_value",
            },
            {
                "attr_id": self.entity.attrs.get(name="ref_action").id,
                "value": self.entry_refs[0],
            },
            {"attr_id": self.entity.attrs.get(name="bool_action").id, "value": True},
            {
                "attr_id": self.entity.attrs.get(name="named_action").id,
                "value": {
                    "name": "changed_value",
                    "id": self.entry_refs[0],
                },
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_str_action").id,
                "values": ["foo", "bar", "baz"],
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_ref_action").id,
                "values": self.entry_refs,
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_named_action").id,
                "values": [
                    {"name": "foo", "id": self.entry_refs[0]},
                    {"name": "bar", "id": self.entry_refs[1]},
                    {"name": "baz", "id": self.entry_refs[2]},
                ],
            },
        ]
        self.FULL_ACTION_CONFIGURATION_PARAMETERS_BUT_EMPTY = [
            {
                "attr_id": self.entity.attrs.get(name="str_action").id,
                "value": "",
            },
            {
                "attr_id": self.entity.attrs.get(name="ref_action").id,
                "value": None,
            },
            {"attr_id": self.entity.attrs.get(name="bool_action").id, "value": False},
            {
                "attr_id": self.entity.attrs.get(name="arr_str_action").id,
                "values": [],
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_ref_action").id,
                "values": [],
            },
            {
                "attr_id": self.entity.attrs.get(name="named_action").id,
                "value": {},
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_named_action").id,
                "values": [],
            },
        ]

    def test_input_airone_trigger_action(self):
        entries = [self.add_entry(self.user, "test_entry_%s" % i, self.entity) for i in range(3)]

        # set condition for string typed Attribute
        input_trigger_condition = InputTriggerCondition(
            attr_id=self.entity.attrs.get(name="str_trigger").id, cond="test"
        )
        self.assertEqual(
            input_trigger_condition.attr.id,
            self.entity.attrs.get(name="str_trigger").id,
        )
        self.assertEqual(input_trigger_condition.str_cond, "test")
        self.assertEqual(input_trigger_condition.ref_cond, None)
        self.assertEqual(input_trigger_condition.bool_cond, False)

        # set condition for object typed Attribute
        input_trigger_condition = InputTriggerCondition(
            attr_id=self.entity.attrs.get(name="ref_trigger").id, cond=entries[0].id
        )
        self.assertEqual(input_trigger_condition.str_cond, "")
        self.assertEqual(input_trigger_condition.ref_cond, entries[0])
        self.assertEqual(input_trigger_condition.bool_cond, False)

        # set condition for array named object typed Attribute
        input_trigger_condition = InputTriggerCondition(
            attr_id=self.entity.attrs.get(name="arr_named_trigger").id,
            cond=entries[0].id,
            hint="entry",
        )
        self.assertEqual(input_trigger_condition.str_cond, "")
        self.assertEqual(input_trigger_condition.ref_cond, entries[0])
        self.assertEqual(input_trigger_condition.bool_cond, False)
        input_trigger_condition = InputTriggerCondition(
            attr_id=self.entity.attrs.get(name="arr_named_trigger").id, cond="hoge"
        )
        self.assertEqual(input_trigger_condition.str_cond, "hoge")
        self.assertEqual(input_trigger_condition.ref_cond, None)
        self.assertEqual(input_trigger_condition.bool_cond, False)

        # set condition for boolean typed Attribute
        input_trigger_condition = InputTriggerCondition(
            attr_id=self.entity.attrs.get(name="bool_trigger").id, cond=True
        )
        self.assertEqual(input_trigger_condition.str_cond, "")
        self.assertEqual(input_trigger_condition.ref_cond, None)
        self.assertEqual(input_trigger_condition.bool_cond, True)

    def test_create_trigger_action_initialization(self):
        entries = [self.add_entry(self.user, "test_entry_%s" % i, self.entity) for i in range(3)]

        settingTriggerConditions = [
            {"attr_id": self.entity.attrs.get(name="str_trigger").id, "cond": "test"},
            {
                "attr_id": self.entity.attrs.get(name="ref_trigger").id,
                "cond": entries[0].id,
            },
            {
                "attr_id": self.entity.attrs.get(name="named_trigger").id,
                "cond": "test",
            },
            {
                "attr_id": self.entity.attrs.get(name="named_trigger").id,
                "cond": entries[0].id,
                "hint": "entry",
            },
            {"attr_id": self.entity.attrs.get(name="bool_trigger").id, "cond": False},
            {
                "attr_id": self.entity.attrs.get(name="arr_str_trigger").id,
                "cond": "test",
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_ref_trigger").id,
                "cond": entries[0].id,
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_named_trigger").id,
                "cond": "test",
            },
            {
                "attr_id": self.entity.attrs.get(name="arr_named_trigger").id,
                "cond": entries[0].id,
                "hint": "entry",
            },
        ]
        settingTriggerActions = self.FULL_ACTION_CONFIGURATION_PARAMETERS.copy()

        # This tests processing to initialize Airone Triggers and its Actions
        TriggerCondition.register(self.entity, settingTriggerConditions, settingTriggerActions)

        # This checks expected Trigger condition objects would be created
        parent_conditions = TriggerParent.objects.filter(entity=self.entity)
        self.assertEqual(parent_conditions.count(), 1)

        trigger_conditions = TriggerCondition.objects.filter(parent=parent_conditions[0])
        self.assertEqual(trigger_conditions.count(), len(settingTriggerConditions))
        # omit tests for TriggerCondition context

        # This checks expected Trigger action objects would be created
        trigger_actions = TriggerAction.objects.filter(condition=parent_conditions[0])
        self.assertEqual(trigger_actions.count(), len(settingTriggerActions))

        for trigger_action in trigger_actions:
            if trigger_action.attr.type & AttrType._ARRAY:
                self.assertEqual(trigger_action.values.count(), 3)
            else:
                self.assertEqual(trigger_action.values.count(), 1)

    def test_condition_will_be_invoked(self):
        entry = self.add_entry(self.user, "test_entry", self.entity)

        # register TriggerCondition and its Actions
        settingTriggerConditions = [
            {"attr_id": self.entity.attrs.get(name="str_trigger").id, "cond": "test"},
            {
                "attr_id": self.entity.attrs.get(name="ref_trigger").id,
                "cond": self.entry_refs[0],
            },
        ]
        settingTriggerActions = self.FULL_ACTION_CONFIGURATION_PARAMETERS.copy()
        parent_condition = TriggerCondition.register(
            self.entity, settingTriggerConditions, settingTriggerActions
        )

        # This checks TriggerParent.get_actions() returns expected TriggerActions
        # and they have expected context (TriggerActionValue).
        trigger_actions = parent_condition.get_actions(
            [
                {
                    "attr_id": entry.attrs.get(schema__name="str_trigger").schema.id,
                    "value": "test",
                },
                {
                    "attr_id": entry.attrs.get(schema__name="ref_trigger").schema.id,
                    "value": self.entry_refs[0].id,
                },
            ]
        )
        self.assertEqual(len(trigger_actions), 7)
        self.assertTrue(all([isinstance(a, TriggerAction) for a in trigger_actions]))
        for index, trigger_action in enumerate(trigger_actions):
            self.assertEqual(trigger_action.attr.id, settingTriggerActions[index]["attr_id"])

        # This checks each TriggerActionValue has expected context
        self.assertEqual(trigger_actions[0].values.count(), 1)
        self.assertEqual(trigger_actions[0].values.first().str_cond, "changed_value")

        self.assertEqual(trigger_actions[1].values.count(), 1)
        self.assertEqual(trigger_actions[1].values.first().ref_cond, self.entry_refs[0])

        self.assertEqual(trigger_actions[2].values.count(), 1)
        self.assertEqual(trigger_actions[2].values.first().bool_cond, True)

        self.assertEqual(trigger_actions[3].values.count(), 1)
        self.assertEqual(trigger_actions[3].values.first().str_cond, "changed_value")
        self.assertEqual(trigger_actions[3].values.first().ref_cond, self.entry_refs[0])

        self.assertEqual(trigger_actions[4].values.count(), 3)
        self.assertEqual(
            [x.str_cond for x in trigger_actions[4].values.all()], ["foo", "bar", "baz"]
        )

        self.assertEqual(trigger_actions[5].values.count(), 3)
        self.assertEqual([x.ref_cond for x in trigger_actions[5].values.all()], self.entry_refs)

        self.assertEqual(trigger_actions[6].values.count(), 3)
        self.assertEqual(
            [(x.str_cond, x.ref_cond) for x in trigger_actions[6].values.all()],
            [
                ("foo", self.entry_refs[0]),
                ("bar", self.entry_refs[1]),
                ("baz", self.entry_refs[2]),
            ],
        )

    def test_condition_can_be_invoked_for_each_attribute_types(self):
        self.add_entry(self.user, "test_entry", self.entity)

        # register TriggerCondition and its Actions
        settingTriggerAction = self.FULL_ACTION_CONFIGURATION_PARAMETERS.copy()[0]

        for cond_param in self.FULL_CONDITION_CONFIGURATION_PARAMETERS:
            TriggerCondition.register(self.entity, [cond_param], [settingTriggerAction])

        # These are testing parameters whether specifying "vlaue" could invoke TriggerCondition
        # for each typed Attributes.
        test_input_params = [
            {"attrname": "str_trigger", "value": "", "will_invoke": False},
            {"attrname": "str_trigger", "value": "Open Sesame", "will_invoke": False},
            {"attrname": "str_trigger", "value": FAT_LADY_PASSWDS[0], "will_invoke": True},
            {"attrname": "ref_trigger", "value": None, "will_invoke": False},
            {
                "attrname": "ref_trigger",
                "value": self.entry_refs[0],
                "will_invoke": False,
            },
            {
                "attrname": "ref_trigger",
                "value": self.entry_refs[2],
                "will_invoke": True,
            },
            {
                "attrname": "bool_trigger",
                "value": True,
                "will_invoke": True,
            },
            {
                "attrname": "bool_trigger",
                "value": False,
                "will_invoke": False,
            },
            {
                "attrname": "named_trigger",
                "value": {"name": "Open Sesame", "id": self.entry_refs[0].id},
                "will_invoke": False,
            },
            {
                "attrname": "named_trigger",
                "value": {"name": "", "id": self.entry_refs[0].id},
                "will_invoke": False,
            },
            {
                "attrname": "named_trigger",
                "value": {"name": "Unexpected words", "id": None},
                "will_invoke": False,
            },
            {
                "attrname": "named_trigger",
                "value": {"name": FAT_LADY_PASSWDS[0], "id": None},
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger",
                "value": {"name": "", "id": self.entry_refs[2].id},
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger",
                "value": {"name": FAT_LADY_PASSWDS[0], "id": self.entry_refs[2].id},
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger2",
                "value": {"name": FAT_LADY_PASSWDS[1], "id": None},
                "will_invoke": False,
            },
            {
                "attrname": "named_trigger2",
                "value": {"name": "", "id": self.entry_refs[1].id},
                "will_invoke": False,
            },
            {
                "attrname": "named_trigger2",
                "value": {"name": FAT_LADY_PASSWDS[1], "id": self.entry_refs[1].id},
                "will_invoke": True,
            },
            {"attrname": "arr_str_trigger", "value": [""], "will_invoke": False},
            {
                "attrname": "arr_str_trigger",
                "value": ["Open Sesame"],
                "will_invoke": False,
            },
            {
                "attrname": "arr_str_trigger",
                "value": ["Open Sesame", FAT_LADY_PASSWDS[0]],
                "will_invoke": True,
            },
            {"attrname": "arr_ref_trigger", "value": [], "will_invoke": False},
            {
                "attrname": "arr_ref_trigger",
                "value": [self.entry_refs[0], self.entry_refs[1]],
                "will_invoke": False,
            },
            {
                "attrname": "arr_ref_trigger",
                "value": self.entry_refs,
                "will_invoke": True,
            },
            {
                "attrname": "arr_named_trigger",
                "value": [{"name": "Open Sesame", "id": self.entry_refs[0].id}],
                "will_invoke": False,
            },
            {
                "attrname": "arr_named_trigger",
                "value": [
                    {"name": "Open Sesame", "id": self.entry_refs[0].id},
                    {"name": FAT_LADY_PASSWDS[0], "id": self.entry_refs[2].id},
                ],
                "will_invoke": True,
            },
        ]
        for test_input_param in test_input_params:
            attr = self.entity.attrs.get(name=test_input_param["attrname"])
            actions = TriggerCondition.get_invoked_actions(
                self.entity, [{"id": attr.id, "value": test_input_param["value"]}]
            )
            if test_input_param["will_invoke"]:
                self.assertGreaterEqual(len(actions), 1)
            else:
                self.assertEqual(len(actions), 0)

    def test_condition_can_be_invoked_for_each_attribute_types_with_oldui(self):
        self.add_entry(self.user, "test_entry", self.entity)

        # register TriggerCondition and its Actions
        settingTriggerAction = self.FULL_ACTION_CONFIGURATION_PARAMETERS.copy()[0]

        for cond_param in self.FULL_CONDITION_CONFIGURATION_PARAMETERS:
            TriggerCondition.register(self.entity, [cond_param], [settingTriggerAction])

        # These are testing parameters whether specifying "vlaue" could invoke TriggerCondition
        # for each typed Attributes.
        test_input_params = [
            {
                "attrname": "str_trigger",
                "value": [{"data": ""}],
                "referral_key": [],
                "will_invoke": False,
            },
            {
                "attrname": "str_trigger",
                "value": [{"data": "Open Sesame"}],
                "referral_key": [],
                "will_invoke": False,
            },
            {
                "attrname": "str_trigger",
                "value": [{"data": FAT_LADY_PASSWDS[0]}],
                "referral_key": [],
                "will_invoke": True,
            },
            {
                "attrname": "ref_trigger",
                "value": [{"data": None, "index": "0"}],
                "referral_key": [],
                "will_invoke": False,
            },
            {
                "attrname": "ref_trigger",
                "value": [{"data": self.entry_refs[0].id, "index": "0"}],
                "referral_key": [],
                "will_invoke": False,
            },
            {
                "attrname": "ref_trigger",
                "value": [{"data": self.entry_refs[2].id, "index": "0"}],
                "referral_key": [],
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger",
                "value": [{"data": self.entry_refs[0].id, "index": "0"}],
                "referral_key": [{"data": "Open Sesame", "index": "0"}],
                "will_invoke": False,
            },
            {
                "attrname": "named_trigger",
                "value": [{"data": self.entry_refs[0].id, "index": "0"}],
                "referral_key": [{"data": "", "index": "0"}],
                "will_invoke": False,
            },
            {
                "attrname": "named_trigger",
                "value": [{"data": None, "index": "0"}],
                "referral_key": [{"data": "Unexpected words", "index": "0 "}],
                "will_invoke": False,
            },
            {
                "attrname": "named_trigger",
                "value": [{"data": None, "index": "0"}],
                "referral_key": [{"data": FAT_LADY_PASSWDS[0], "index": "0"}],
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger",
                "value": [{"data": self.entry_refs[2].id, "index": "0"}],
                "referral_key": [{"data": "", "index": "0"}],
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger",
                "value": [{"data": self.entry_refs[2].id, "index": "0"}],
                "referral_key": [{"data": FAT_LADY_PASSWDS[0], "index": "0"}],
                "will_invoke": True,
            },
            {
                "attrname": "arr_str_trigger",
                "value": [{"data": "", "index": "0"}],
                "referral_key": [],
                "will_invoke": False,
            },
            {
                "attrname": "arr_str_trigger",
                "value": [{"data": "Open Sesame", "index": "0"}],
                "referral_key": [],
                "will_invoke": False,
            },
            {
                "attrname": "arr_str_trigger",
                "value": [
                    {"data": "Open Sesame", "index": "0"},
                    {"data": FAT_LADY_PASSWDS[0], "index": "1"},
                ],
                "referral_key": [],
                "will_invoke": True,
            },
            {"attrname": "arr_ref_trigger", "value": [], "referral_key": [], "will_invoke": False},
            {
                "attrname": "arr_ref_trigger",
                "value": [
                    {"data": self.entry_refs[0].id, "index": "0"},
                    {"data": self.entry_refs[1].id, "index": "1"},
                ],
                "referral_key": [],
                "will_invoke": False,
            },
            {
                "attrname": "arr_ref_trigger",
                "value": [
                    {"data": self.entry_refs[0].id, "index": "0"},
                    {"data": self.entry_refs[1].id, "index": "1"},
                    {"data": self.entry_refs[2].id, "index": "2"},
                ],
                "referral_key": [],
                "will_invoke": True,
            },
            {
                "attrname": "arr_named_trigger",
                "value": [{"data": self.entry_refs[0].id, "index": "0"}],
                "referral_key": [{"data": "Open Sesame", "index": "0"}],
                "will_invoke": False,
            },
            {
                "attrname": "arr_named_trigger",
                "value": [
                    {"data": self.entry_refs[0].id, "index": "0"},
                    {"data": self.entry_refs[2].id, "index": "1"},
                ],
                "referral_key": [
                    {"data": "Open Sesame", "index": "0"},
                    {"data": FAT_LADY_PASSWDS[0], "index": "1"},
                ],
                "will_invoke": True,
            },
        ]
        for test_input_param in test_input_params:
            attr = self.entity.attrs.get(name=test_input_param["attrname"])
            actions = TriggerCondition.get_invoked_actions(
                self.entity,
                [
                    {
                        "entity_attr_id": attr.id,
                        "value": test_input_param["value"],
                        "referral_key": test_input_param["referral_key"],
                    }
                ],
            )
            if test_input_param["will_invoke"]:
                self.assertGreaterEqual(len(actions), 1)
            else:
                self.assertEqual(len(actions), 0)

    def test_register_conditions_with_blank_values(self):
        # register TriggerCondition and its Actions
        settingTriggerAction = self.FULL_ACTION_CONFIGURATION_PARAMETERS.copy()[0]

        for cond_param in self.FULL_CONDITION_CONFIGURATION_PARAMETERS_BUT_EMPTY:
            TriggerCondition.register(self.entity, [cond_param], [settingTriggerAction])

        # check each TriggerConditoins are created correctly
        self.assertEqual(
            TriggerParent.objects.filter(entity=self.entity).count(),
            len(self.FULL_CONDITION_CONFIGURATION_PARAMETERS_BUT_EMPTY),
        )
        self.assertEqual(
            TriggerCondition.objects.filter(parent__entity=self.entity).count(),
            len(self.FULL_CONDITION_CONFIGURATION_PARAMETERS_BUT_EMPTY),
        )
        for cond in TriggerCondition.objects.filter(parent__entity=self.entity):
            self.assertEqual(cond.str_cond, "")
            self.assertEqual(cond.ref_cond, None)
            self.assertFalse(cond.bool_cond)

        # test cases for specifying empty value
        for index, cond_info in enumerate(self.FULL_CONDITION_CONFIGURATION_PARAMETERS_BUT_EMPTY):
            target_attr = self.entity.attrs.get(id=cond_info["attr_id"])
            actions = TriggerCondition.get_invoked_actions(
                self.entity, [{"id": target_attr.id, "value": cond_info["cond"]}]
            )
            self.assertEqual(len(actions), 1)

            target_entry = self.add_entry(self.user, "e-%s" % index, self.entity)
            actions[0].run(self.user, target_entry)

            # This confirms action value is changed by test case value
            target_attrv = target_entry.get_attrv("str_action")
            self.assertEqual(target_attrv.value, "changed_value")

    def test_register_actions_with_blank_values(self):
        cond_attr = self.entity.attrs.get(name="bool_action")
        parent_condition = TriggerCondition.register(
            self.entity,
            [{"attr_id": cond_attr.id, "cond": True}],
            self.FULL_ACTION_CONFIGURATION_PARAMETERS_BUT_EMPTY,
        )

        for value in TriggerActionValue.objects.filter(action__condition=parent_condition):
            self.assertEqual(value.str_cond, "")
            self.assertEqual(value.ref_cond, None)
            self.assertFalse(value.bool_cond)

        # create an Entry with valid attribute value to cehck action processing
        target_entry = self.add_entry(
            self.user,
            "test entry",
            self.entity,
            values={
                "str_action": "test-value",
                "ref_action": self.entry_refs[0],
                "named_action": {"name": "foo", "id": self.entry_refs[0]},
                "arr_str_action": ["foo", "bar", "baz"],
                "arr_ref_action": self.entry_refs,
                "arr_named_action": [
                    {"name": "hoge", "id": self.entry_refs[0]},
                    {"name": "fuga", "id": self.entry_refs[1]},
                ],
                "bool_action": True,
            },
        )

        # invoke trigger action
        actions = TriggerCondition.get_invoked_actions(
            self.entity, [{"id": cond_attr.id, "value": True}]
        )
        self.assertEqual(len(actions), len(self.FULL_ACTION_CONFIGURATION_PARAMETERS_BUT_EMPTY))
        for action in actions:
            action.run(self.user, target_entry)

        # check each values of target_entry were removed by trigger-action processing
        self.assertEqual(target_entry.get_attrv("str_action").value, "")
        self.assertEqual(target_entry.get_attrv("ref_action").referral, None)
        self.assertEqual(target_entry.get_attrv("bool_action").boolean, False)
        self.assertEqual(target_entry.get_attrv("arr_str_action").data_array.count(), 0)
        self.assertEqual(target_entry.get_attrv("arr_ref_action").data_array.count(), 0)
        self.assertEqual(target_entry.get_attrv("named_action").value, "")
        self.assertEqual(target_entry.get_attrv("named_action").referral, None)
        self.assertEqual(target_entry.get_attrv("arr_named_action").data_array.count(), 0)

    def test_run_trigger_action(self):
        # This test to run TriggerAction and check Entry is updated as expected
        entry = self.add_entry(self.user, "test_entry", self.entity)

        # register TriggerCondition and its Actions
        settingTriggerConditions = [
            {"attr_id": self.entity.attrs.get(name="str_trigger").id, "cond": "test"},
        ]
        settingTriggerActions = self.FULL_ACTION_CONFIGURATION_PARAMETERS.copy()
        parent_condition = TriggerCondition.register(
            self.entity, settingTriggerConditions, settingTriggerActions
        )

        # Run each actions of parent_condition
        input_params = [
            {"attr_id": self.entity.attrs.get(name="str_trigger").id, "value": "test"},
        ]
        for action in parent_condition.get_actions(input_params):
            action.run(self.user, entry)

        # Then, check entry is updated as expected
        self.assertEqual(entry.get_attrv("str_action").value, "changed_value")
        self.assertEqual(entry.get_attrv("ref_action").referral.id, self.entry_refs[0].id)
        self.assertTrue(entry.get_attrv("bool_action"))
        self.assertEqual(entry.get_attrv("named_action").value, "changed_value")
        self.assertEqual(entry.get_attrv("named_action").referral.id, self.entry_refs[0].id)
        self.assertEqual(
            [x.value for x in entry.get_attrv("arr_str_action").data_array.all()],
            ["foo", "bar", "baz"],
        )
        self.assertEqual(
            [x.referral.id for x in entry.get_attrv("arr_ref_action").data_array.all()],
            [x.id for x in self.entry_refs],
        )
        self.assertEqual(
            [
                (x.value, x.referral.id)
                for x in entry.get_attrv("arr_named_action").data_array.all()
            ],
            [
                ("foo", self.entry_refs[0].id),
                ("bar", self.entry_refs[1].id),
                ("baz", self.entry_refs[2].id),
            ],
        )

    @mock.patch(
        "trigger.tasks.may_invoke_trigger.delay",
        mock.Mock(side_effect=trigger_tasks.may_invoke_trigger),
    )
    def test_prevent_infinite_loop_updating(self):
        """
        This tests Attribute won't be updated if TriggerAction updates the same Attribute.
        """
        # register the simplest TriggerConditoin that could loop update
        target_attr = self.entity.attrs.get(name="str_trigger")
        TriggerCondition.register(
            self.entity,
            [{"attr_id": target_attr.id, "cond": "hoge"}],
            [{"attr_id": target_attr.id, "value": "fuga"}],
        )
        TriggerCondition.register(
            self.entity,
            [{"attr_id": target_attr.id, "cond": "fuga"}],
            [{"attr_id": target_attr.id, "value": "hoge"}],
        )

        actions = TriggerCondition.get_invoked_actions(
            self.entity, [{"id": target_attr.id, "value": "hoge"}]
        )
        self.assertEqual(len(actions), 1)

        # This tests TriggerAction running chain won't be executed infinitely
        target_entry = self.add_entry(self.user, "test_entry", self.entity)
        actions[0].run(self.user, target_entry)

        # Then, check entry is updated as expected
        self.assertEqual(target_entry.get_attrv("str_trigger").value, "hoge")
        self.assertEqual(
            [
                x.value
                for x in AttributeValue.objects.filter(parent_attr__schema=target_attr).order_by(
                    "created_time"
                )
            ],
            ["", "fuga", "hoge"],
        )

    def test_clear_and_update_parent_condition(self):
        parent_cond = TriggerCondition.register(
            self.entity,
            self.FULL_CONDITION_CONFIGURATION_PARAMETERS,
            self.FULL_ACTION_CONFIGURATION_PARAMETERS,
        )

        # This checks expected TriggerActionValue and TriggerCondition instances are created
        COUNT_CONDS = len(self.FULL_CONDITION_CONFIGURATION_PARAMETERS)
        COUNT_ACTIONS = len(self.FULL_ACTION_CONFIGURATION_PARAMETERS)

        self.assertEqual(parent_cond.conditions.count(), COUNT_CONDS)
        self.assertEqual(parent_cond.actions.count(), COUNT_ACTIONS)
        self.assertEqual(TriggerCondition.objects.filter(parent=parent_cond).count(), COUNT_CONDS)
        self.assertEqual(TriggerAction.objects.filter(condition=parent_cond).count(), COUNT_ACTIONS)

        # This clears all conditions and actions that are associated with TriggerParnetCondition
        parent_cond.clear()
        self.assertEqual(parent_cond.conditions.count(), 0)
        self.assertEqual(parent_cond.actions.count(), 0)
        self.assertEqual(TriggerCondition.objects.filter(parent=parent_cond).count(), 0)
        self.assertEqual(TriggerAction.objects.filter(condition=parent_cond).count(), 0)
        self.assertEqual(
            TriggerActionValue.objects.filter(action__condition=parent_cond).count(), 0
        )

        # This update conditions and actions
        parent_cond.update(
            self.FULL_CONDITION_CONFIGURATION_PARAMETERS,
            self.FULL_ACTION_CONFIGURATION_PARAMETERS,
        )
        COUNT_CONDS = len(self.FULL_CONDITION_CONFIGURATION_PARAMETERS)
        COUNT_ACTIONS = len(self.FULL_ACTION_CONFIGURATION_PARAMETERS)

        self.assertEqual(parent_cond.conditions.count(), COUNT_CONDS)
        self.assertEqual(parent_cond.actions.count(), COUNT_ACTIONS)
        self.assertEqual(TriggerCondition.objects.filter(parent=parent_cond).count(), COUNT_CONDS)
        self.assertEqual(TriggerAction.objects.filter(condition=parent_cond).count(), COUNT_ACTIONS)

    def test_register_actions_with_unmatch(self):
        self.add_entry(self.user, "test_entry", self.entity)

        # register TriggerCondition and its Actions
        settingTriggerAction = self.FULL_ACTION_CONFIGURATION_PARAMETERS.copy()[0]

        # Case: is_unmatch is True
        for cond_param in self.FULL_CONDITION_CONFIGURATION_PARAMETERS:
            cond_param["is_unmatch"] = True
            TriggerCondition.register(self.entity, [cond_param], [settingTriggerAction])

        # These are testing parameters whether specifying "vlaue" could invoke TriggerCondition
        # for each typed Attributes.

        test_input_params = [
            {"attrname": "str_trigger", "value": "", "will_invoke": True},
            {"attrname": "str_trigger", "value": "Open Sesame", "will_invoke": True},
            {"attrname": "str_trigger", "value": FAT_LADY_PASSWDS[0], "will_invoke": False},
            {"attrname": "ref_trigger", "value": None, "will_invoke": True},
            {
                "attrname": "ref_trigger",
                "value": self.entry_refs[0],
                "will_invoke": True,
            },
            {
                "attrname": "ref_trigger",
                "value": self.entry_refs[2],
                "will_invoke": False,
            },
            {
                "attrname": "bool_trigger",
                "value": True,
                "will_invoke": False,
            },
            {
                "attrname": "bool_trigger",
                "value": False,
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger",
                "value": {"name": "Open Sesame", "id": self.entry_refs[0].id},
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger",
                "value": {"name": "", "id": self.entry_refs[0].id},
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger",
                "value": {"name": "Unexpected words", "id": None},
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger",
                "value": {"name": FAT_LADY_PASSWDS[0], "id": None},
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger",
                "value": {"name": "", "id": self.entry_refs[2].id},
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger",
                "value": {"name": FAT_LADY_PASSWDS[0], "id": self.entry_refs[2].id},
                "will_invoke": False,
            },
            {
                "attrname": "named_trigger2",
                "value": {"name": FAT_LADY_PASSWDS[1], "id": None},
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger2",
                "value": {"name": "", "id": self.entry_refs[1].id},
                "will_invoke": True,
            },
            {
                "attrname": "named_trigger2",
                "value": {"name": FAT_LADY_PASSWDS[1], "id": self.entry_refs[1].id},
                "will_invoke": False,
            },
            {"attrname": "arr_str_trigger", "value": [""], "will_invoke": True},
            {
                "attrname": "arr_str_trigger",
                "value": ["Open Sesame"],
                "will_invoke": True,
            },
            {
                "attrname": "arr_str_trigger",
                "value": ["Open Sesame", FAT_LADY_PASSWDS[0]],
                "will_invoke": False,
            },
            {"attrname": "arr_ref_trigger", "value": [], "will_invoke": True},
            {
                "attrname": "arr_ref_trigger",
                "value": [self.entry_refs[0], self.entry_refs[1]],
                "will_invoke": True,
            },
            {
                "attrname": "arr_ref_trigger",
                "value": self.entry_refs,
                "will_invoke": False,
            },
            {
                "attrname": "arr_named_trigger",
                "value": [{"name": "Open Sesame", "id": self.entry_refs[0].id}],
                "will_invoke": True,
            },
            {
                "attrname": "arr_named_trigger",
                "value": [
                    {"name": "Open Sesame", "id": self.entry_refs[0].id},
                    {"name": FAT_LADY_PASSWDS[0], "id": self.entry_refs[2].id},
                ],
                "will_invoke": False,
            },
        ]
        for test_input_param in test_input_params:
            attr = self.entity.attrs.get(name=test_input_param["attrname"])
            actions = TriggerCondition.get_invoked_actions(
                self.entity, [{"id": attr.id, "value": test_input_param["value"]}]
            )
            if test_input_param["will_invoke"]:
                self.assertGreaterEqual(len(actions), 1)
            else:
                self.assertEqual(len(actions), 0)
