from airone.lib.types import AttrTypeValue
from airone.lib.test import AironeTestCase
from trigger.models import (
  TriggerParentCondition,
  TriggerCondition,
  TriggerParentAction,
  TriggerAction,
  TriggerActionValue
)
from user.models import User


class ModelTest(AironeTestCase):
  def setUp(self):
    super(ModelTest, self).setUp()

    self.user: User = User(username="test")
    self.entity = self.create_entity(self.user, "test_entity", attrs=[
      # These are attributes that are used for trigger
      {"name": "str_trigger", "type": AttrTypeValue["string"]},
      {"name": "ref_trigger", "type": AttrTypeValue["object"]},
      {"name": "arr_str_trigger", "type": AttrTypeValue["array_string"]},
      {"name": "arr_ref_trigger", "type": AttrTypeValue["array_object"]},
      {"name": "arr_name_ref_trigger", "type": AttrTypeValue["array_named_object"]},
      {"name": "bool_trigger", "type": AttrTypeValue["boolean"]},

      # These are attributes that are used for action
      {"name": "str_action", "type": AttrTypeValue["string"]},
      {"name": "ref_action", "type": AttrTypeValue["object"]},
      {"name": "arr_str_action", "type": AttrTypeValue["array_string"]},
      {"name": "arr_ref_action", "type": AttrTypeValue["array_object"]},
      {"name": "arr_name_ref_action", "type": AttrTypeValue["array_named_object"]},
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
      attr=self.entity.attrs.get(name="atr_action"),
    )