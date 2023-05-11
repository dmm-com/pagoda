from rest_framework.serializers import ModelSerializer, Field, CharField, IntegerField
from entity.models import Entity

from entry.models import Entry, Attribute, AttributeValue


class RecursiveField(Field):
    def to_representation(self, obj):
        return AdvancedSearchSerializer(obj, depth=0).data


class EntitySerializer(ModelSerializer):
    class Meta:
        model = Entity
        fields = ("id", "name")


class EntrySerializer(ModelSerializer):
    schema = EntitySerializer()

    class Meta:
        model = Entry
        fields = ("id", "name", "schema")


class ReferSerializer(ModelSerializer):
    id = IntegerField(source="parent_attr.parent_entry.id")
    name = CharField(source="parent_attr.parent_entry.name")
    schema = EntitySerializer(source="parent_attr.parent_entry.schema")

    class Meta:
        model = AttributeValue
        fields = ("id", "name", "schema")


class AttributeValueChildSerializer(ModelSerializer):
    # referral = RecursiveField()
    referral = EntrySerializer()

    class Meta:
        model = AttributeValue
        fields = ("value", "referral")


class AttributeValueParentSerializer(ModelSerializer):
    data_array = AttributeValueChildSerializer(many=True)
    # referral = RecursiveField()

    class Meta:
        model = AttributeValue
        fields = ("value", "referral", "data_array")


class AttributeSerializer(ModelSerializer):
    values = AttributeValueParentSerializer(many=True)

    class Meta:
        model = Attribute
        fields = ("id", "name", "values")


class AdvancedSearchSerializer(ModelSerializer):
    schema = EntitySerializer()
    attrs = AttributeSerializer(many=True)
    refes = ReferSerializer(source="referred_attr_value", many=True)

    class Meta:
        model = Entry
        fields = ("id", "name", "schema", "attrs", "refes")

    """
    def __init__(self, *args, **kwargs):
        depth = kwargs.pop("depth", 1)
        super().__init__(*args, **kwargs)
        self.depth = depth

    def to_representation(self, obj):
        if self.depth == 0:
            return []
        return super().to_representation(obj)
    """
