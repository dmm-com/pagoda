from rest_framework.serializers import (
    ReadOnlyField,
    ModelSerializer,
    Field,
    CharField,
    IntegerField,
)
from entity.models import Entity

from entry.models import (
    IPADDR,
    LB,
    Server,
    Entry,
    Attribute,
    AttributeValue,
    LBPolicyTemplate,
    LBServiceGroup,
    LBVirtualServer,
    LargeCategory,
    m2mLBServiceGroupLBServer,
)


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


class LargeCategorySerializer(ModelSerializer):
    class Meta:
        model = LargeCategory
        fields = ("id", "name")


class ServerSerializer(ModelSerializer):
    large_category = LargeCategorySerializer()

    class Meta:
        model = Server
        fields = ("id", "name", "large_category")


class IPADDRSerializer(ModelSerializer):
    ref_server = ServerSerializer(source="server_set", many=True)

    class Meta:
        model = IPADDR
        fields = ("id", "name", "ref_server")


class LBServerSerializer(ModelSerializer):
    id = ReadOnlyField(source="lbserver.id")
    name = ReadOnlyField(source="lbserver.name")
    ipaddr = IPADDRSerializer(source="lbserver.ipaddr")

    class Meta:
        model = m2mLBServiceGroupLBServer
        fields = ("id", "name", "key", "ipaddr")


"""
class LBServiceGroupSerializer(ModelSerializer):
    lb_server = LBServerSerializer(source="m2mlbservicegrouplbserver_set", many=True)

    class Meta:
        model = LBServiceGroup
        fields = ("id", "name", "lb_server")
"""


"""
class LBPolicyTemplateSerializer(ModelSerializer):
    lb_service_group = LBServiceGroupSerializer(many=True)

    class Meta:
        model = LBPolicyTemplate
        fields = ("id", "name", "lb_service_group")
"""


class LBSerializer(ModelSerializer):
    class Meta:
        model = LB
        fields = ("id", "name")


class LBPolicyTemplateSerializer(ModelSerializer):
    lb = LBSerializer()

    class Meta:
        model = LBPolicyTemplate
        fields = ("id", "name", "lb")


class AdvancedSearchSQLSerializer(ModelSerializer):
    lb = LBSerializer()
    ipaddr = IPADDRSerializer()
    large_category = LargeCategorySerializer()
    lb_policy_template = LBPolicyTemplateSerializer(many=True)
    lb_service_group = LBServiceGroupSerializer(many=True)

    class Meta:
        model = LBVirtualServer
        fields = (
            "id",
            "name",
            "lb",
            "ipaddr",
            "large_category",
            "lb_policy_template",
            "lb_service_group",
        )
