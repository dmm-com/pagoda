from typing import Any, TypedDict

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airone.lib.drf import (
    InvalidValueError,
)
from entity.api_v2.serializers import (
    EntityAttrSerializer,
    EntitySerializer,
)
from entity.models import Entity, EntityAttr
from entry.api_v2.serializers import (
    EntryAttributeValueNamedObjectSerializer,
    EntryAttributeValueObject,
    AttributeValueField,
)
from trigger.models import (
    TriggerAction,
    TriggerActionValue,
    TriggerCondition,
    TriggerParent,
)


class TriggerActionValueSerializer(serializers.ModelSerializer):
    ref_cond = serializers.SerializerMethodField()

    class Meta:
        model = TriggerActionValue
        fields = [
            "id",
            "str_cond",
            "ref_cond",
            "bool_cond",
        ]

    def get_ref_cond(self, obj: TriggerActionValue) -> EntryAttributeValueObject | None:
        if obj.ref_cond:
            return {
                "id": obj.ref_cond.id,
                "name": obj.ref_cond.name,
                "schema": {
                    "id": obj.ref_cond.schema.id,
                    "name": obj.ref_cond.schema.name,
                },
            }
        else:
            return None


class TriggerActionSerializer(serializers.ModelSerializer):
    attr = EntityAttrSerializer(read_only=True)
    values = TriggerActionValueSerializer(many=True)

    class Meta:
        model = TriggerAction
        fields = [
            "id",
            "attr",
            "values",
        ]


class TriggerConditionSerializer(serializers.ModelSerializer):
    attr = EntityAttrSerializer(read_only=True)
    ref_cond = serializers.SerializerMethodField()

    class Meta:
        model = TriggerCondition
        fields = [
            "id",
            "attr",
            "str_cond",
            "ref_cond",
            "bool_cond",
        ]

    def get_ref_cond(self, obj: TriggerCondition) -> EntryAttributeValueObject | None:
        if obj.ref_cond:
            return {
                "id": obj.ref_cond.id,
                "name": obj.ref_cond.name,
                "schema": {
                    "id": obj.ref_cond.schema.id,
                    "name": obj.ref_cond.schema.name,
                },
            }
        else:
            return None


class TriggerParentSerializer(serializers.ModelSerializer):
    entity = EntitySerializer(read_only=True)
    actions = TriggerActionSerializer(many=True)
    conditions = TriggerConditionSerializer(many=True)

    class Meta:
        model = TriggerParent
        fields = [
            "id",
            "entity",
            "actions",
            "conditions",
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


class TriggerConditionUpdateSerializer(serializers.Serializer):
    attr_id = serializers.IntegerField(required=True)
    cond = serializers.CharField(required=False, allow_blank=True)
    hint = serializers.CharField(required=False, allow_blank=True)

class TriggerActionUpdateSerializer(serializers.Serializer):
    attr_id = serializers.IntegerField(required=True)
    values = serializers.ListField(child=AttributeValueField(allow_null=True), required=False)
    value = AttributeValueField(allow_null=True)


class TriggerParentBaseSerializer(serializers.ModelSerializer):
    entity_id = serializers.IntegerField(write_only=True, required=False)
    conditions = serializers.ListField(
        child=TriggerConditionUpdateSerializer(), write_only=True, required=False
    )
    actions = serializers.ListField(
        child=TriggerActionUpdateSerializer(), write_only=True, required=False
    )

    class Meta:
        model = TriggerParent
        fields = ["id", "entity_id", "conditions", "actions"]

    def validate(self, data):
        entity = Entity.objects.filter(id=data["entity_id"], is_active=True).first()
        if not entity:
            raise ValidationError("Invalid entity_id(%s) was specified" % data["entity_id"])

        # Element in conditions and actions is necessary at least one
        if not data["conditions"] or not data["actions"]:
            raise InvalidValueError(
                "Configuration of condotions or actions is required at least one"
            )

        # This checks each EntityAttrs in parameters are Entity's one of data["entity_id"]
        for key in ["conditions", "actions"]:
            attr_id_list = [x["attr_id"] for x in data[key]]
            if not EntityAttr.objects.filter(id__in=attr_id_list, parent_entity=entity).exists():
                raise InvalidValueError(
                    "%s.attr_id contains non EntityAttr of specified Entity" % key
                )

        return data


class TriggerParentCreateSerializer(TriggerParentBaseSerializer):
    def create(self, validated_data: TriggerParentUpdateData):
        return TriggerCondition.register(
            entity=Entity.objects.get(id=validated_data["entity_id"]),
            conditions=validated_data["conditions"],
            actions=validated_data["actions"],
        )


class TriggerParentUpdateSerializer(TriggerParentBaseSerializer):
    def update(self, parent_condition, validated_data):
        # clear configurations that have already been registered in this TriggerParent
        parent_condition.clear()

        # update parent_condition's configuration
        parent_condition.update(
            conditions=validated_data["conditions"], actions=validated_data["actions"]
        )

        return parent_condition
