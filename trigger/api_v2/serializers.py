from rest_framework import serializers

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