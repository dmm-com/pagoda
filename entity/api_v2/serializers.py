import json
from typing import Any, Dict, List

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


class WebhookSerializer(serializers.ModelSerializer):
    headers = serializers.SerializerMethodField()

    class Meta:
        model = Webhook
        fields = ["id", "label", "url", "is_enabled", "is_verified", "headers"]

    def get_headers(self, obj: Webhook) -> List[Dict[str, str]]:
        try:
            return [{'headerKey': k, 'headerValue': v} for k, v in json.loads(obj.headers)]
        except json.decoder.JSONDecodeError:
            return []


class EntityDetailSerializer(EntityWithAttrSerializer):
    # webhooks = serializers.ListField(child=WebhookSerializer())
    webhooks = WebhookSerializer(many=True)

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "status", "is_toplevel", "attrs", "webhooks"]
