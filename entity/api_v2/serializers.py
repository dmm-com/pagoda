import json
from typing import Any, Dict, List
import custom_view

from rest_framework import serializers

from airone.lib.acl import ACLType
from entity.models import Entity
from user.models import User
from webhook.models import Webhook


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ["id", "name"]


class EntityWithAttrSerializer(EntitySerializer):
    is_toplevel = serializers.SerializerMethodField(method_name="get_is_toplevel")
    attrs = serializers.SerializerMethodField(method_name="get_attrs")

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "status", "is_toplevel", "attrs"]

    def get_is_toplevel(self, obj: Entity) -> bool:
        return (obj.status & Entity.STATUS_TOP_LEVEL) != 0

    def get_attrs(self, obj: Entity) -> List[Dict[str, Any]]:
        user = User.objects.get(id=self.context["request"].user.id)
        return [
            {
                "id": x.id,
                "name": x.name,
                "type": x.type,
                "is_mandatory": x.is_mandatory,
                "is_delete_in_chain": x.is_delete_in_chain,
                "referrals": [
                    {
                        "id": r.id,
                        "name": r.name,
                    }
                    for r in x.referral.all()
                ],
            }
            for x in obj.attrs.filter(is_active=True).order_by("index")
            if user.has_permission(x, ACLType.Writable)
        ]


class WebhookSerializerBase(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ["id", "label", "url", "is_enabled", "is_verified", "headers"]


class WebhookGetSerializer(WebhookSerializerBase):
    headers = serializers.SerializerMethodField()

    def get_headers(self, obj: Webhook) -> List[Dict[str, str]]:
        try:
            return [{'headerKey': k, 'headerValue': v} for k, v in json.loads(obj.headers)]
        except json.decoder.JSONDecodeError:
            return []


class WebhookPostSerializer(WebhookSerializerBase):
    headers = serializers.ListField(child=serializers.DictField(child=serializers.CharField(), allow_empty=True), allow_empty=True)

    def validate_headers(self, value):
        return json.dumps(value)


class EntityDetailSerializer(EntityWithAttrSerializer):
    # webhooks = serializers.ListField(child=WebhookGetSerializer())
    webhooks = WebhookGetSerializer(many=True)

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "status", "is_toplevel", "attrs", "webhooks"]


class EntityAttrSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class EntityCreateSerializer(EntitySerializer):
    attrs = serializers.ListField(child=EntityAttrSerializer(), write_only=True, required=False)
    webhooks = WebhookPostSerializer(many=True)

    class Meta:
        model = Entity
        fields = ["id", "name", "attrs", "note", "webhooks"]

    def validate(self, data):
        # todo: duplication check
        pass

    def create(self, validated_data):
        print(validated_data)
        user: User = User.objects.get(id=self.context["request"].user.id)

        if custom_view.is_custom("before_create_entity"):
            custom_view.call_custom("before_create_entity", None, validated_data)

        attrs_data = validated_data.pop("attrs", [])
        webhooks_data = validated_data.pop("webhooks", [])
        entity: Entity = Entity.objects.create(
            **validated_data, status=Entity.STATUS_CREATING, created_user=user
        )

        # set status parameters
        if validated_data.get("is_toplevel", False):
            entity.status = Entity.STATUS_TOP_LEVEL
            entity.save(update_fields=["status"])

        entity.del_status(Entity.STATUS_CREATING)

        # TODO:
        # - valudate attrs_data
        # - register EntityAttr(s) and Webhook(s)

        return entity
