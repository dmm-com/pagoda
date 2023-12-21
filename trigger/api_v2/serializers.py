from rest_framework import serializers

from entity.api_v2.serializers import EntitySerializer
from trigger.models import TriggerCondition


class TriggerParentConditionSerializer(serializers.ModelSerializer):
    entity = EntitySerializer(read_only=True)

    class Meta:
        model = TriggerCondition
        fields = [
            "id",
            "entity",
        ]


class TriggerBaseSerializer(serializers.ModelSerializer):
    parent = TriggerParentConditionSerializer(read_only=True)

    class Meta:
        model = TriggerCondition
        fields = [
            "id",
            "attr",
            "str_cond",
            "ref_cond",
            "bool_cond",
            "parent",
        ]

    def get_entity(self, obj):
        return {
            "id": obj.parent.entity.id,
            "name": obj.parent.entity.name,
            "is_active": obj.parent.entity.is_active,
        }
