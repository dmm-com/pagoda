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
    print("[onix/get_entity] obj: %s" % str(obj.__class__.__name__))
    return {
      "id": obj.parent.entity.id,
      "name": obj.parent.entity.name,
      "is_active": obj.parent.entity.is_active,
    }