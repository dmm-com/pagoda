from typing import Any, Optional, TypedDict
from rest_framework import serializers
from entity.models import Entity, EntityAttr
from rest_framework.exceptions import PermissionDenied, ValidationError

from airone.lib.drf import (
    InvalidValueError,
)

from entity.api_v2.serializers import (
  EntityAttrSerializer,
  EntitySerializer,
)
from trigger.models import (
  TriggerParentCondition,
  TriggerCondition,
  TriggerAction,
  TriggerActionValue,
)

class TriggerActionValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerActionValue
        fields = [
            "id",
            "str_cond",
            "ref_cond",
            "bool_cond",
        ]

class TriggerActionSerializer(serializers.ModelSerializer):
    values = TriggerActionValueSerializer(many=True)

    class Meta:
        model = TriggerAction
        fields = [
            "id",
            "values",
        ]


class TriggerConditionSerializer(serializers.ModelSerializer):
    attr = EntityAttrSerializer(read_only=True)

    class Meta:
        model = TriggerCondition
        fields = [
            "id",
            "attr",
            "str_cond",
            "ref_cond",
            "bool_cond",
        ]


class TriggerParentConditionSerializer(serializers.ModelSerializer):
    entity = EntitySerializer(read_only=True)
    actions = TriggerActionSerializer(many=True)
    co_conditions = TriggerConditionSerializer(many=True)

    class Meta:
        model = TriggerParentCondition
        fields = [
            "id",
            "entity",
            "actions",
            "co_conditions",
        ]


class ConditionUpdateData(TypedDict):
    attr_id: int
    cond: Any


class ActionUpdateData(TypedDict):
    attr_id: int
    values: Any


class TriggerParentUpdateData(TypedDict):
    entity_id: int
    conditions: list[ConditionUpdateData]
    actions: list[ActionUpdateData]


class TriggerParentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerParentCondition
        fields = ["id"]

    def update(self, parent_condition: TriggerParentCondition, validated_data: TriggerParentUpdateData):
        return parent_condition


class TriggerConditionUpdateSerializer(serializers.Serializer):
    attr_id = serializers.IntegerField(required=True)
    cond = serializers.CharField(required=True)


class TriggerActionUpdateSerializer(serializers.Serializer):
    attr_id = serializers.IntegerField(required=True)
    values = serializers.ListField(child=serializers.CharField(), required=False)
    value = serializers.CharField(required=False)


class TriggerParentBaseSerializer(serializers.ModelSerializer):
    entity_id = serializers.IntegerField(write_only=True, required=True)
    conditions = serializers.ListField(child=TriggerConditionUpdateSerializer(), write_only=True, required=True)
    actions = serializers.ListField(child=TriggerActionUpdateSerializer(), write_only=True, required=True)

    class Meta:
        model = TriggerParentCondition
        fields = ["id", "entity_id", "conditions", "actions"]

    def validate(self, data):
        entity = Entity.objects.filter(id=data["entity_id"], is_active=True).first()
        if not entity:
            raise ValidationError("Invalid entity_id(%s) was specified" % data["entity_id"])

        # Element in conditions and actions is necessary at least one
        if not data["conditions"] or not data["actions"]:
            raise InvalidValueError("Configuration of condotions or actions is required at least one")

        # This checks each EntityAttrs in parameters are Entity's one of data["entity_id"]
        for key in ["conditions", "actions"]:
            attr_id_list = [x["attr_id"] for x in data[key]]
            if EntityAttr.objects.filter(id__in=attr_id_list, parent_entity=entity).count() != len(data[key]):
                raise InvalidValueError("%s.attr_id contains non EntityAttr of specified Entity" % key)

        return data


class TriggerParentCreateSerializer(TriggerParentBaseSerializer):
    def create(self, validated_data: TriggerParentUpdateData):
        return TriggerCondition.register(
            entity=Entity.objects.get(id=validated_data["entity_id"]),
            conditions=validated_data["conditions"],
            actions=validated_data["actions"]
        )

class TriggerParentUpdateSerializer(TriggerParentBaseSerializer):
    def update(self, parent_condition, validated_data):
        # clear configurations that have already been registered in this TriggerParentCondition
        parent_condition.clear()

        # update parent_condition's configuration
        parent_condition.update(
            conditions=validated_data["conditions"],
            actions=validated_data["actions"]
        )

        return parent_condition

class TriggerParentDestroySerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerParentCondition
        fields = ["id"]

    def delete(self, *args, **kwargs):
        print("[onix/delete] args: %s" % str(args))
        print("[onix/delete] kwargs: %s" % str(kwargs))