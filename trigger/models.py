import itertools
import json
from typing import TYPE_CHECKING, Any

from django.db import models

from acl.models import ACLBase
from airone.exceptions.trigger import InvalidInputException
from airone.lib.http import DRFRequest
from airone.lib.log import Logger
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.api_v2.serializers import EntryUpdateSerializer
from entry.models import Entry

if TYPE_CHECKING:
    from django.db.models import Manager


## These are internal classes for AirOne trigger and action
class InputTriggerCondition(object):
    def __init__(self, **input):
        # set EntityAttr from "attr" parameter of input
        attr_id = input.get("attr_id", 0)
        self.attr = EntityAttr.objects.filter(id=attr_id, is_active=True).first()
        if not self.attr:
            raise InvalidInputException("Specified attr(%s) is invalid" % attr_id)

        # initialize each condition parameters
        self.initialize_condition()

        self.is_unmatch = input.get("is_unmatch", False)

        # set each condition parameters by specified condition value
        self.parse_input_condition(input.get("cond"), input.get("hint"))

    def __repr__(self):
        return "(attr:%s[%s]) str_cond:%s, ref_cond:%s, bool_cond:%s is_unmatch:%s" % (
            self.attr.name,
            self.attr.id,
            str(self.str_cond),
            str(self.ref_cond),
            str(self.bool_cond),
            self.is_unmatch,
        )

    def initialize_condition(self):
        self.str_cond = ""
        self.ref_cond = None
        self.bool_cond = False
        self.is_unmatch = False

    def parse_input_condition(self, input_condition, hint=None):
        def _convert_value_to_entry(value: Entry | int | str | Any):
            if isinstance(value, Entry):
                return value
            elif isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                # convert ID to Entry instance
                entry = Entry.objects.filter(id=int(value), is_active=True).first()
                if entry:
                    return entry
            return None

        def _decode_value(value) -> dict:
            try:
                return json.loads(value)
            except (ValueError, TypeError):
                return {}

        match AttrType(self.attr.type):
            case AttrType.NAMED_OBJECT | AttrType.ARRAY_NAMED_OBJECT:
                match hint:
                    case "entry":
                        self.ref_cond = _convert_value_to_entry(input_condition)
                    case "json":
                        info = _decode_value(input_condition)

                        self.ref_cond = _convert_value_to_entry(info.get("id"))
                        self.str_cond = info.get("name", "")
                    case _:
                        self.str_cond = input_condition

            case AttrType.OBJECT | AttrType.ARRAY_OBJECT:
                self.ref_cond = _convert_value_to_entry(input_condition)

            case AttrType.STRING | AttrType.ARRAY_STRING | AttrType.TEXT:
                self.str_cond = input_condition if input_condition else ""

            case AttrType.BOOLEAN:
                if isinstance(input_condition, bool):
                    self.bool_cond = input_condition
                elif isinstance(input_condition, str):
                    self.bool_cond = input_condition.lower() == "true"
                else:
                    self.bool_cond = input_condition is not None


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
        if self.attr.type & AttrType._ARRAY:
            self.values = self.get_value(input.get("values", []))
        else:
            self.values = [self.get_value(input.get("value"))]

    def get_value(self, raw_input_value):
        def _do_get_value(input_value, attr_type):
            match AttrType(attr_type):
                case (
                    AttrType.ARRAY_OBJECT
                    | AttrType.ARRAY_NAMED_OBJECT
                    | AttrType.ARRAY_NAMED_OBJECT_BOOLEAN
                    | AttrType.ARRAY_STRING
                ):
                    return [_do_get_value(x, attr_type ^ AttrType._ARRAY) for x in input_value if x]

                case AttrType.STRING | AttrType.TEXT:
                    return InputTriggerActionValue(str_cond=input_value)

                case AttrType.NAMED_OBJECT:
                    ref_entry = None
                    if isinstance(input_value.get("id"), int):
                        ref_entry = Entry.objects.filter(
                            id=input_value["id"], is_active=True
                        ).first()
                    if isinstance(input_value.get("id"), str):
                        ref_entry = Entry.objects.filter(
                            id=int(input_value["id"]), is_active=True
                        ).first()
                    elif isinstance(input_value.get("id"), Entry):
                        ref_entry = input_value["id"]

                    return InputTriggerActionValue(
                        str_cond=input_value.get("name", ""),
                        ref_cond=ref_entry,
                    )

                case AttrType.OBJECT:
                    params = {}
                    if isinstance(input_value, Entry):
                        params["ref_cond"] = input_value
                    elif isinstance(input_value, int):
                        params["ref_cond"] = Entry.objects.filter(
                            id=input_value, is_active=True
                        ).first()
                    elif isinstance(input_value, str):
                        params["ref_cond"] = Entry.objects.filter(
                            id=int(input_value), is_active=True
                        ).first()

                    return InputTriggerActionValue(**params)

                case AttrType.BOOLEAN:
                    if isinstance(input_value, str):
                        return InputTriggerActionValue(bool_cond=input_value.lower() == "true")
                    else:
                        return InputTriggerActionValue(bool_cond=input_value)

        return _do_get_value(raw_input_value, self.attr.type)


class TriggerParent(models.Model):
    entity = models.ForeignKey("entity.Entity", on_delete=models.CASCADE)

    if TYPE_CHECKING:
        conditions: Manager["TriggerCondition"]
        actions: Manager["TriggerAction"]

    def is_match_condition(self, inputs: list[InputTriggerCondition]):
        if all([c.is_same_condition(inputs) for c in self.conditions.all()]):
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
                "is_unmatch": input_cond.is_unmatch,
            }
            if not TriggerCondition.objects.filter(**params).exists():
                TriggerCondition.objects.create(**params)

    def get_actions(self, recv_attrs: list) -> list["TriggerAction"]:
        """
        This method checks whether specified entity's Trigger is invoked by recv_attrs context.
        The recv_attrs format should be compatible with APIv2 standard.

        TODO:
        It's necessary to expand APIv2 implementation to pass EntityAttr ID in the recv_attrs
        context to reduce DB query to get it from Attribute instance.
        """

        def _is_match(condition: TriggerCondition):
            for attr_info in [x for x in recv_attrs if x["attr_id"] == condition.attr.id]:
                if condition.is_match_condition(attr_info["value"]):
                    if not condition.is_unmatch:
                        return True
                else:
                    if condition.is_unmatch:
                        return True

            return False

        if all([_is_match(c) for c in self.conditions.filter(attr__is_active=True)]):
            # In this case, all recv_attrs are matched with configured TriggerCondition,
            # then return corresponding TriggerAction.
            return list(TriggerAction.objects.filter(condition=self))

        else:
            return []

    def clear(self, *args, **kwargs):
        # delete TriggerActionValues, which are associated with TriggerAction instance
        TriggerActionValue.objects.filter(action__condition=self).delete()

        # delete all conditions and actions that are related with this instance
        self.conditions.all().delete()
        self.actions.all().delete()

    def update(self, conditions: list, actions: list):
        # convert input to InputTriggerCondition
        input_trigger_conditions = [InputTriggerCondition(**condition) for condition in conditions]

        # save conditions
        self.save_conditions(input_trigger_conditions)

        # save actions
        for action in actions:
            input_trigger_action = InputTriggerAction(**action)
            trigger_action = TriggerAction.objects.create(
                condition=self, attr=input_trigger_action.attr
            )
            trigger_action.save_actions(input_trigger_action)


class TriggerCondition(models.Model):
    parent = models.ForeignKey(TriggerParent, on_delete=models.CASCADE, related_name="conditions")
    attr = models.ForeignKey("entity.EntityAttr", on_delete=models.CASCADE)
    str_cond = models.TextField(blank=True, null=True)
    ref_cond = models.ForeignKey("entry.Entry", on_delete=models.SET_NULL, null=True, blank=True)
    bool_cond = models.BooleanField(default=False)
    is_unmatch = models.BooleanField(default=False)

    @property
    def ATTR_TYPE(self):
        return AttrType(self.attr.type)

    def is_same_condition(self, input_list: list[InputTriggerCondition]) -> bool:
        # This checks one of the InputCondition which is in input_list matches with this condition
        def _do_check_condition(input: InputTriggerCondition):
            if self.attr.id == input.attr.id and self.is_unmatch == input.is_unmatch:
                match self.ATTR_TYPE:
                    case AttrType.STRING | AttrType.TEXT | AttrType.ARRAY_STRING:
                        return self.str_cond == input.str_cond
                    case AttrType.OBJECT | AttrType.ARRAY_OBJECT:
                        return self.ref_cond == input.ref_cond
                    case AttrType.BOOLEAN:
                        return self.bool_cond == input.bool_cond
                    case AttrType.NAMED_OBJECT | AttrType.ARRAY_NAMED_OBJECT:
                        return self.str_cond == input.str_cond and self.ref_cond == input.ref_cond

            return False

        return any([_do_check_condition(input) for input in input_list])

    def is_match_condition(self, raw_recv_value) -> bool:
        """
        This checks specified value, which is compatible with APIv2 standard, matches
        with this condition.
        """

        def _compatible_with_apiv1(recv_value):
            """
            This method retrieve value from recv_value that is specified by user. This processing
            is necessary to compatible with both API versions (v1 and v2)
            """
            if isinstance(recv_value, list) and all(
                [isinstance(x, dict) and "data" in x for x in recv_value]
            ):
                # In this case, the recv_value is compatible with APIv1 standard
                # it's necessary to convert it to APIv2 standard
                if self.attr.type & AttrType._ARRAY:
                    return [x["data"] for x in recv_value]
                else:
                    return recv_value[0]["data"]

            else:
                # In this case, the recv_value is compatible with APIv2 standard
                # and this method designed for it.
                return recv_value

        # This is a helper method when AttrType is "object" or "named_object"
        recv_value = _compatible_with_apiv1(raw_recv_value)

        def _is_match_object(val) -> bool:
            if isinstance(val, int) or isinstance(val, str):
                if self.ref_cond and self.ref_cond.is_active:
                    return self.ref_cond.id == int(val)

            elif isinstance(val, Entry) or isinstance(val, ACLBase):
                return self.ref_cond.id == val.id

            elif val is None:
                return self.ref_cond is None

            return False

        def _is_match_named_object(val) -> bool:
            # This refilling processing is necessary because any type of value is acceptable
            eval_value: dict[str, Any] = {
                "name": "",
                "id": None,
            }
            if isinstance(val, str):
                eval_value["name"] = val
                eval_value["id"] = val if val.isdigit() else None
            if isinstance(val, int):
                eval_value["id"] = val
            if isinstance(val, dict):
                eval_value["name"] = val.get("name", "")
                eval_value["id"] = val.get("id")

            # when both str_cond and ref_cond are set in the same condition
            # this returns True only when both values are matched with eval_value
            if self.str_cond != "" and self.ref_cond is not None:
                return self.str_cond == eval_value.get("name") and _is_match_object(
                    eval_value.get("id")
                )

            # check specified value is matched with this condition
            if eval_value.get("name") and self.str_cond == eval_value.get("name"):
                return True

            if eval_value.get("id") and _is_match_object(eval_value.get("id")):
                return True

            # this matches explicit empty eval_valueue
            if (
                self.str_cond == eval_value.get("name", "") == ""
                and self.ref_cond is None
                and eval_value.get("id") is None
            ):
                return True

            return False

        try:
            match self.ATTR_TYPE:
                case AttrType.OBJECT:
                    return _is_match_object(recv_value)

                case AttrType.ARRAY_OBJECT:
                    if recv_value is None or not recv_value:
                        # when both recv_value and self.ref_cond is empty, this condition is matched
                        return self.ref_cond is None

                    elif isinstance(recv_value, list):
                        return any([_is_match_object(x) for x in recv_value])

                case AttrType.STRING | AttrType.TEXT:
                    return self.str_cond == recv_value

                case AttrType.NAMED_OBJECT:
                    return _is_match_named_object(recv_value)

                case AttrType.ARRAY_NAMED_OBJECT:
                    if recv_value is None or not recv_value:
                        # when both recv_value and self.ref_cond is empty, this condition is matched
                        return self.ref_cond is None and self.str_cond == ""

                    elif isinstance(recv_value, list):
                        return any([_is_match_named_object(x) for x in recv_value])

                case AttrType.ARRAY_STRING:
                    if recv_value is None or not recv_value:
                        # when both recv_value and self.str_cond is empty, this condition is matched
                        return self.str_cond == ""

                    elif isinstance(recv_value, list):
                        return self.str_cond in recv_value

                case AttrType.BOOLEAN:
                    return self.bool_cond == recv_value

        except ValueError:
            Logger.error(
                "Invalid Attribute Type(%s) was registered (attr_id: %s)"
                % (self.attr.type, self.attr.id)
            )

        return False

    @classmethod
    def register(cls, entity: Entity, conditions: list, actions: list) -> TriggerParent:
        # convert input to InputTriggerCondition
        input_trigger_conditions = [InputTriggerCondition(**condition) for condition in conditions]

        # check if condition is already registered
        for parent_condition in TriggerParent.objects.filter(entity=entity):
            # This prevents to registering exactly same condition that have already been registered
            if parent_condition.is_match_condition(input_trigger_conditions):
                raise InvalidInputException(
                    "There is condition that have same condition with specified one"
                )

        # register specified condition as AirOne TriggerCondition
        parent_condition = TriggerParent.objects.create(entity=entity)
        parent_condition.save_conditions(input_trigger_conditions)

        # convert input to InputTriggerCondition
        for action in actions:
            input_trigger_action = InputTriggerAction(**action)
            trigger_action = TriggerAction.objects.create(
                condition=parent_condition, attr=input_trigger_action.attr
            )
            trigger_action.save_actions(input_trigger_action)

        return parent_condition

    @classmethod
    def get_invoked_actions(cls, entity: Entity, recv_data: list):
        # The APIv1 and APIv2 format is different.
        # In the APIv2, the "id" parameter in the recv_data variable means EntityAttr ID.
        # But in the APIv1, the "id" parameter in the recv_data variable means Attribute ID
        # of Entry. So, it's necessary to refer "entity_attr_id" parameter to be compatible
        # with both API versions.
        if any(["entity_attr_id" in x for x in recv_data]):
            # This is for APIv1
            params = []
            for data in recv_data:
                entity_attr = EntityAttr.objects.filter(id=data["entity_attr_id"]).first()

                if entity_attr.type & AttrType._NAMED and entity_attr.type & AttrType.OBJECT:
                    # merge name and id value to the data parameter to be compatible with APIv2
                    # for naemd_object typed Attribute
                    v = [
                        {
                            "index": v["index"] if v else "0",
                            "data": {
                                "name": r["data"] if r else "",
                                "id": v["data"] if v else None,
                            },
                        }
                        for (v, r) in itertools.zip_longest(
                            sorted(data["value"], key=lambda x: x["index"]),
                            sorted(data["referral_key"], key=lambda x: x["index"]),
                        )
                    ]
                    params.append({"attr_id": int(entity_attr.id), "value": v})
                else:
                    params.append({"attr_id": int(entity_attr.id), "value": data["value"]})
        else:
            # This is for APIv2
            params = [{"attr_id": int(x["id"]), "value": x["value"]} for x in recv_data]

        actions = []
        for parent_condition in TriggerParent.objects.filter(entity=entity):
            actions += parent_condition.get_actions(params)

        return actions


class TriggerAction(models.Model):
    condition = models.ForeignKey(TriggerParent, on_delete=models.CASCADE, related_name="actions")
    attr = models.ForeignKey("entity.EntityAttr", on_delete=models.CASCADE)

    if TYPE_CHECKING:
        values: Manager["TriggerActionValue"]

    def save_actions(self, input: InputTriggerAction):
        for input_action_value in input.values:
            params = {
                "action": self,
                "str_cond": input_action_value.str_cond,
                "ref_cond": input_action_value.ref_cond,
                "bool_cond": input_action_value.bool_cond,
            }
            TriggerActionValue.objects.create(**params)

    def get_serializer_acceptable_value(self, value=None, attr_type=None):
        """
        This converts TriggerActionValue to the value that EntryUpdateSerializer can accept.
        """
        if not attr_type:
            attr_type = self.attr.type

        value = value or self.values.first()
        if attr_type & AttrType._ARRAY:
            return [
                self.get_serializer_acceptable_value(x, attr_type ^ AttrType._ARRAY)
                for x in self.values.all()
            ]
        elif attr_type == AttrType.BOOLEAN:
            return value.bool_cond
        elif attr_type == AttrType.NAMED_OBJECT:
            return {
                "name": value.str_cond,
                "id": value.ref_cond.id if isinstance(value.ref_cond, Entry) else None,
            }
        elif attr_type == AttrType.STRING:
            return value.str_cond
        elif attr_type == AttrType.TEXT:
            return value.str_cond
        elif attr_type == AttrType.OBJECT:
            return value.ref_cond.id if isinstance(value.ref_cond, Entry) else None

    def run(self, user, entry, call_stacks=[]):
        # When self.id contains in call_stacks, it means that this action is already invoked.
        # This prevents infinite loop.
        if self.id in call_stacks:
            return

        # update specified Entry by configured attribute value
        setting_data = {
            "id": entry.id,
            "name": entry.name,
            "attrs": [{"id": self.attr.id, "value": self.get_serializer_acceptable_value()}],
            "delay_trigger": False,
            "call_stacks": [*call_stacks, self.id],
        }
        serializer = EntryUpdateSerializer(
            instance=entry, data=setting_data, context={"request": DRFRequest(user)}
        )
        if serializer:
            serializer.is_valid(raise_exception=True)
            serializer.save()


class TriggerActionValue(models.Model):
    action = models.ForeignKey(TriggerAction, on_delete=models.CASCADE, related_name="values")
    str_cond = models.TextField(blank=True, null=True)
    ref_cond = models.ForeignKey("entry.Entry", on_delete=models.SET_NULL, null=True, blank=True)
    bool_cond = models.BooleanField(default=False)

    # TODO: Add method to register value to Attribute when action is invoked
