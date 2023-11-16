from django.db import models

from airone.exceptions.trigger import InvalidInputException
from airone.lib.types import AttrTypeValue
from entity.models import Entity, EntityAttr
from entry.models import Entry


## These are internal classes for AirOne trigger and action
class InputTriggerCondition(object):
    def __init__(self, **input):
        # set EntityAttr from "attr" parameter of input
        attr_id = input.get("attr_id", 0)
        self.attr = EntityAttr.objects.filter(id=attr_id, is_active=True).first()
        if not self.attr:
            raise InvalidInputException("Specified attr(%s) is invalid" % attr_id)

        self.str_cond = input.get("str_cond", "")

        ref_id = input.get("ref_cond", None)
        self.ref_cond = None
        if ref_id:
            self.ref_cond = Entry.objects.filter(id=ref_id, is_active=True).first()
            if not self.ref_cond:
                raise InvalidInputException("Specified referral Entry(%s) is invalid" % ref_id)

        self.bool_cond = input.get("bool_cond", False)


class InputTriggerActionValue(object):
    def __init__(self, **input):
        self.str_cond = input.get("str_cond", "")
        self.ref_cond = input.get("ref_cond", None)
        self.bool_cond = input.get("bool_cond", False)


class InputTriggerAction(object):
    def __init__(self, **input):
        # set EntityAttr from "attr" parameter of input
        attr_id = input.get("attr_id", 0)
        self.attr = EntityAttr.objects.filter(id=attr_id, is_active=True).first()
        if not self.attr:
            raise InvalidInputException("Specified attr(%s) is invalid" % attr_id)

        self.values = []

        value = self.get_value(input.get("value"))
        if isinstance(value, list):
            self.values = value
        elif isinstance(value, InputTriggerActionValue):
            self.values.append(value)

    def get_value(self, input_value):
        if isinstance(input_value, str):
            return InputTriggerActionValue(str_cond=input_value)
        elif isinstance(input_value, Entry):
            return InputTriggerActionValue(ref_cond=input_value)
        elif isinstance(input_value, int):
            return InputTriggerActionValue(
                ref_cond=Entry.objects.filter(id=input_value, is_active=True).first()
            )
        elif isinstance(input_value, dict):
            return InputTriggerActionValue(
                str_cond=input_value["name"],
                ref_cond=Entry.objects.filter(id=input_value["id"], is_active=True).first(),
            )
        elif isinstance(input_value, bool):
            return InputTriggerActionValue(bool_cond=input_value)
        elif isinstance(input_value, list):
            return [self.get_value(x) for x in input_value if x]


class TriggerParentCondition(models.Model):
    entity = models.ForeignKey("entity.Entity", on_delete=models.CASCADE)

    def is_match_condition(self, inputs: list[InputTriggerCondition]):
        if all([c.is_same_condition(inputs) for c in self.co_condition.all()]):
            return True
        return False

    def save_conditions(self, inputs: list[InputTriggerCondition]):
        for input_cond in inputs:
            params = {
                "parent": self,
                "attr": input_cond.attr,
                "str_cond": input_cond.str_cond,
                "ref_cond": input_cond.ref_cond,
                "bool_cond": input_cond.bool_cond,
            }
            if not TriggerCondition.objects.filter(**params).exists():
                TriggerCondition.objects.create(**params)


class TriggerCondition(models.Model):
    parent = models.ForeignKey(
        TriggerParentCondition, on_delete=models.CASCADE, related_name="co_conditions"
    )
    attr = models.ForeignKey("entity.EntityAttr", on_delete=models.CASCADE)
    str_cond = models.TextField()
    ref_cond = models.ForeignKey("entry.Entry", on_delete=models.SET_NULL, null=True, blank=True)
    bool_cond = models.BooleanField(default=False)

    def is_same_condition(self, input_list: list[InputTriggerCondition]) -> bool:
        # This checks one of the InputCondition which is in input_list matches with this condition
        def _do_check_condition(input: InputTriggerCondition):
            if self.attr.id == input.attr.id:
                if self.attr.type & AttrTypeValue["boolean"]:
                    return self.bool_cond == input.bool_cond

                elif self.attr.type & AttrTypeValue["object"]:
                    return self.ref_cond == input.ref_cond

                elif self.attr.type & AttrTypeValue["string"]:
                    return self.str_cond == input.str_cond

            return False

        return any([_do_check_condition(input) for input in input_list])

    @classmethod
    def register(cls, entity: Entity, conditions: list, actions: list):
        # convert input to InputTriggerCondition
        input_trigger_conditions = [InputTriggerCondition(**condition) for condition in conditions]

        # check if condition is already registered
        for parent_condition in TriggerParentCondition.objects.filter(entity=entity):
            # This prevents to registering exactly same condition that have already been registered
            if parent_condition.is_match_condition(input_trigger_conditions):
                raise InvalidInputException(
                    "There is condition that have same condition with specified one"
                )

        # register specified condition as AirOne TriggerCondition
        parent_condition = TriggerParentCondition.objects.create(entity=entity)
        parent_condition.save_conditions(input_trigger_conditions)

        # convert input to InputTriggerCondition
        for action in actions:
            input_trigger_action = InputTriggerAction(**action)
            trigger_action = TriggerAction.objects.create(
                condition=parent_condition, attr=input_trigger_action.attr
            )
            trigger_action.save_actions(input_trigger_action)


class TriggerAction(models.Model):
    condition = models.ForeignKey(
        TriggerParentCondition, on_delete=models.CASCADE, related_name="actions"
    )
    attr = models.ForeignKey("entity.EntityAttr", on_delete=models.CASCADE)

    def save_actions(self, input: InputTriggerAction):
        for input_action_value in input.values:
            params = {
                "action": self,
                "str_cond": input_action_value.str_cond,
                "ref_cond": input_action_value.ref_cond,
                "bool_cond": input_action_value.bool_cond,
            }
            TriggerActionValue.objects.create(**params)


class TriggerActionValue(models.Model):
    action = models.ForeignKey(TriggerAction, on_delete=models.CASCADE, related_name="values")
    str_cond = models.TextField()
    ref_cond = models.ForeignKey("entry.Entry", on_delete=models.SET_NULL, null=True, blank=True)
    bool_cond = models.BooleanField(default=False)

    # TODO: Add method to register value to Attribute when action is invoked
