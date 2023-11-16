from airone.lib.types import AttrTypeValue
from airone.lib.test import AironeTestCase
from trigger.models import (
  TriggerParentCondition,
  TriggerCondition,
  TriggerParentAction,
  TriggerAction,
  TriggerActionValue,
  InputAironeTriggerCondition,
  InputAironeTriggerActionValue,
  InputAironeTriggerAction,
)
from user.models import User


class ModelTest(AironeTestCase):
  def setUp(self):
    super(ModelTest, self).setUp()

    self.user: User = User.objects.create(username="test")
    self.entity_ref = self.create_entity(self.user, "test_entity_ref")
    self.entity = self.create_entity(self.user, "test_entity", attrs=[
      # These are attributes that are used for trigger
      {"name": "str_trigger", "type": AttrTypeValue["string"]},
      {"name": "ref_trigger", "type": AttrTypeValue["object"], "ref": self.entity_ref},
      {"name": "named_trigger", "type": AttrTypeValue["named_object"], "ref": self.entity_ref},
      {"name": "arr_str_trigger", "type": AttrTypeValue["array_string"]},
      {"name": "arr_ref_trigger", "type": AttrTypeValue["array_object"], "ref": self.entity_ref},
      {"name": "arr_named_trigger", "type": AttrTypeValue["array_named_object"],
       "ref": self.entity_ref},
      {"name": "bool_trigger", "type": AttrTypeValue["boolean"]},

      # These are attributes that are used for action
      {"name": "str_action", "type": AttrTypeValue["string"]},
      {"name": "ref_action", "type": AttrTypeValue["object"], "ref": self.entity_ref},
      {"name": "named_action", "type": AttrTypeValue["named_object"], "ref": self.entity_ref},
      {"name": "arr_str_action", "type": AttrTypeValue["array_string"]},
      {"name": "arr_ref_action", "type": AttrTypeValue["array_object"], "ref": self.entity_ref},
      {"name": "arr_name_ref_action", "type": AttrTypeValue["array_named_object"],
       "ref": self.entity_ref},
      {"name": "bool_action", "type": AttrTypeValue["boolean"]},
    ])

  def test_create_condition_for_str(self):
    # create Condition
    parent_condition = TriggerParentCondition.objects.create(entity=self.entity)
    cond_attr_str = TriggerCondition.objects.create(
      parent=parent_condition,
      attr=self.entity.attrs.get(name="str_trigger"),
      str_cond="test",
    )

    # create Action
    parent_action = TriggerParentAction.objects.create(condition=parent_condition)
    action = TriggerAction.objects.create(
      parent=parent_action,
      attr=self.entity.attrs.get(name="str_action"),
    )

  def test_input_airone_trigger_action(self):
    entries = [self.add_entry(self.user, "test_entry_%s" % i, self.entity) for i in range(3)]

    TEST_CONDITIONS = [
      {"attr_id": self.entity.attrs.get(name="str_trigger").id, "str_cond": "test"},
      {"attr_id": self.entity.attrs.get(name="ref_trigger").id, "ref_cond": entries[0].id},
      {"attr_id": self.entity.attrs.get(name="named_trigger").id, "str_cond": "test", "ref_cond": entries[0].id},
      {"attr_id": self.entity.attrs.get(name="arr_str_trigger").id, "str_cond": "test"},
      {"attr_id": self.entity.attrs.get(name="arr_ref_trigger").id, "ref_cond": entries[0].id},
      {"attr_id": self.entity.attrs.get(name="arr_named_trigger").id, "str_cond": "test", "ref_cond": entries[0].id},
      {"attr_id": self.entity.attrs.get(name="bool_trigger").id, "bool_cond": False},
    ]
    for cond in TEST_CONDITIONS:
      input_trigger_condition = InputAironeTriggerCondition(**cond)
      self.assertEqual(input_trigger_condition.attr.id, cond["attr_id"])
      self.assertEqual(input_trigger_condition.str_cond, cond.get("str_cond", ""))
      self.assertEqual(input_trigger_condition.bool_cond, cond.get("bool_cond", False))
      if cond.get("ref_cond", None):
        self.assertEqual(input_trigger_condition.ref_cond.id, cond.get("ref_cond", None))

  def test_trigger_parent_condition(self):
    trigger_parent = TriggerParentCondition.objects.create(entity=self.entity)


  def test_create_trigger_action_initialization(self):
    entries = [self.add_entry(self.user, "test_entry_%s" % i, self.entity) for i in range(3)]

    # NOTE: This only assume partial match. When the specification is change to expand to support
    #       full match, this test should be updated.
    settingTriggerConditions = [
      {"attr_id": self.entity.attrs.get(name="str_trigger").id, "str_cond": "test"},
      {"attr_id": self.entity.attrs.get(name="ref_trigger").id, "ref_cond": entries[0].id},
      {"attr_id": self.entity.attrs.get(name="named_trigger").id, "str_cond": "test", "ref_cond": entries[0].id},
      {"attr_id": self.entity.attrs.get(name="bool_trigger").id, "bool_cond": False},
      {"attr_id": self.entity.attrs.get(name="arr_str_trigger").id, "str_cond": "test"},
      {"attr_id": self.entity.attrs.get(name="arr_ref_trigger").id, "ref_cond": entries[0].id},
      {"attr_id": self.entity.attrs.get(name="arr_named_trigger").id, "str_cond": "test", "ref_cond": entries[0].id},
    ]
    settingTriggerActions = [
      {"attr_id": self.entity.attrs.get(name="str_action").id, "value": "changed_value"},
      {"attr_id": self.entity.attrs.get(name="ref_action").id, "value": entries[1].id},
      {"attr_id": self.entity.attrs.get(name="named_action").id, "value": {"name": "changed_value", "id": entries[1].id}},
      {"attr_id": self.entity.attrs.get(name="bool_action").id, "value": True},
      {"attr_id": self.entity.attrs.get(name="arr_str_action").id, "value": ["foo", "bar", "baz"]},
      {"attr_id": self.entity.attrs.get(name="arr_ref_action").id, "value": [x.id for x in entries]},
      {"attr_id": self.entity.attrs.get(name="arr_named_action").id, "value": [
        {"name": "foo", "id": entries[0].id},
        {"name": "bar", "id": None},
        {"name": "", "id": entries[2].id},
      ]},
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
    parent_action = TriggerParentAction.objects.filter(condition=parent_conditions[0])
    self.assertEqual(parent_conditions.count(), 1)

    trigger_actions = TriggerAction.objects.filter(parent=parent_action[0])
    self.assertEqual(trigger_actions.count(), len(settingTriggerActions))

    for trigger_action in trigger_actions:
      if trigger_action.attr.type & AttrTypeValue["array"]:
        self.assertEqual(trigger_action.values.count(), 3)
      else:
        self.assertEqual(trigger_action.values.count(), 1)