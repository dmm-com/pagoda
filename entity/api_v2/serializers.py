import collections
import json
from typing import Any, Dict, List

import requests
import custom_view

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airone.lib.acl import ACLType
from airone.lib.types import AttrTypeValue
from entity.models import Entity, EntityAttr
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
            return [{"headerKey": k, "headerValue": v} for k, v in json.loads(obj.headers).items()]
        except json.decoder.JSONDecodeError:
            return []


class WebhookPostSerializer(WebhookSerializerBase):
    headers = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField(), allow_empty=True),
        allow_empty=True,
    )

    def validate_headers(self, headers):
        results = {}
        for header in headers:
            results[header["headerKey"]] = header["headerValue"]
        return results


class EntityDetailSerializer(EntityWithAttrSerializer):
    # webhooks = serializers.ListField(child=WebhookGetSerializer())
    webhooks = WebhookGetSerializer(many=True)

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "status", "is_toplevel", "attrs", "webhooks"]


class EntityAttrSerializer(serializers.ModelSerializer):
    referral = serializers.ListField(allow_empty=True)

    class Meta:
        model = EntityAttr
        fields = [
            "name",
            "type",
            "is_mandatory",
            "referral",
            "index",
            "is_summarized",
            "is_delete_in_chain",
        ]


class EntityCreateSerializer(EntitySerializer):
    note = serializers.CharField(allow_blank=True)
    attrs = serializers.ListField(child=EntityAttrSerializer(), write_only=True, required=False)
    webhooks = WebhookPostSerializer(many=True, write_only=True)

    class Meta:
        model = Entity
        fields = ["id", "name", "attrs", "note", "webhooks"]

    def validate_name(self, name):
        if Entity.objects.filter(name=name, is_active=True).exists():
            raise ValidationError("Duplication error. There is same named Entity")

        return name

    def validate_attrs(self, attrs):
        # duplication checks
        counter = collections.Counter(
            [attr["name"] for attr in attrs if "deleted" not in attr or not attr["deleted"]]
        )
        if len([v for v, count in counter.items() if count > 1]):
            raise ValidationError("Duplicated attribute names are not allowed", status=400)

        return attrs

    def create(self, validated_data):
        user: User = User.objects.get(id=self.context["request"].user.id)

        if custom_view.is_custom("before_create_entity"):
            custom_view.call_custom("before_create_entity", None, validated_data)

        attrs_data = validated_data.pop("attrs", [])
        webhooks_data = validated_data.pop("webhooks", [])
        entity: Entity = Entity.objects.create(
            **validated_data, status=Entity.STATUS_CREATING, created_user=user
        )

        # register history data to create Entity
        history = user.seth_entity_add(entity)

        # set status parameters
        if validated_data.get("is_toplevel", False):
            entity.status = Entity.STATUS_TOP_LEVEL
            entity.save(update_fields=["status"])

        # create EntityAttr instances in associated with specifying data
        for attr in attrs_data:
            # This is necessary not to pass invalid parameter to DRF DB-register
            attr_referrals = attr.pop("referral", [])

            # create EntityAttr instance with user specified params
            attr_base = EntityAttr.objects.create(
                **attr,
                created_user=user,
                parent_entity=entity,
            )

            # set referrals if necessary
            if int(attr["type"]) & AttrTypeValue["object"]:
                [attr_base.referral.add(x) for x in attr_referrals]

            # make association with Entity and EntityAttrs
            entity.attrs.add(attr_base)

            # register history to modify Entity
            history.add_attr(attr_base)

        # unset Editing MODE
        entity.del_status(Entity.STATUS_CREATING)

        # TODO:
        # - register EntityAttr(s) and Webhook(s)
        for webhook_data in webhooks_data:
            webhook = Webhook.objects.create(**webhook_data)
            entity.webhooks.add(webhook)
            resp = requests.post(
                webhook.url,
                **{
                    "headers": webhook.headers,
                    "data": json.dumps({}),
                    "verify": False,
                },
            )
            webhook.is_verified = resp.ok
            webhook.save()

        return entity
