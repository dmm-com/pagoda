from rest_framework import serializers

from trigger.models import TriggerCondition


class TriggerBaseSerializer(serializers.ModelSerializer):
  entity = serializers.SerializerMethodField()

  class Meta:
    model = TriggerCondition
    fields = [
      "id",
      "attr",
      "str_cond",
      "ref_cond",
      "bool_cond",
      "entity",
    ]

  def get_entity(self, obj):
    return {
      "id": obj.parent.entity.id,
      "name": obj.parent.entity.name,
      "is_active": obj.parent.entity.is_active,
    }