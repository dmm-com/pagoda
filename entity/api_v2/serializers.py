import collections
import json
from typing import Any, Dict, List

import requests
from requests.exceptions import ConnectionError
import custom_view

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airone.lib.acl import ACLType
from airone.lib.types import AttrTypeValue
from entity.models import Entity, EntityAttr
from user.models import History, User
from webhook.models import Webhook


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ["id", "name"]


class WebhookSerializer(serializers.ModelSerializer):
    headers = serializers.DictField(child=serializers.CharField(), required=False)

    class Meta:
        model = Webhook
        fields = ["id", "label", "url", "is_enabled", "is_verified", "headers"]
        read_only_fields = ["is_verified"]


class EntityDetailSerializer(EntitySerializer):
    is_toplevel = serializers.SerializerMethodField(method_name="get_is_toplevel")
    attrs = serializers.SerializerMethodField(method_name="get_attrs")
    webhooks = WebhookSerializer(many=True)

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "status", "is_toplevel", "attrs", "webhooks"]

    def get_is_toplevel(self, obj: Entity) -> bool:
        return (obj.status & Entity.STATUS_TOP_LEVEL) != 0

    def get_attrs(self, obj: Entity) -> List[Dict[str, Any]]:
        user = User.objects.get(id=self.context["request"].user.id)
        return [
            {
                "id": x.id,
                "index": x.index,
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


class EntityAttrSerializer(serializers.ModelSerializer):
    created_user = serializers.HiddenField(default=serializers.CurrentUserDefault())

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
            "created_user",
        ]

    def validate_type(self, type):
        if type not in AttrTypeValue.values():
            raise ValidationError("attrs type(%s) does not exist" % type)

        return type


class EntityCreateSerializer(EntitySerializer):
    is_toplevel = serializers.BooleanField(write_only=True, required=False, default=False)
    attrs = serializers.ListField(
        child=EntityAttrSerializer(), write_only=True, required=False, default=[]
    )
    webhooks = WebhookSerializer(many=True, write_only=True, required=False, default=[])
    created_user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "is_toplevel", "attrs", "webhooks", "created_user"]
        extra_kwargs = {"note": {"write_only": True}}

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
            raise ValidationError("Duplicated attribute names are not allowed")

        return attrs

    def create(self, validated_data):
        user: User = User.objects.get(id=self.context["request"].user.id)

        if custom_view.is_custom("before_create_entity"):
            custom_view.call_custom("before_create_entity", None, validated_data)

        is_toplevel_data = validated_data.pop("is_toplevel")
        attrs_data = validated_data.pop("attrs")
        webhooks_data = validated_data.pop("webhooks")
        entity: Entity = Entity.objects.create(**validated_data, status=Entity.STATUS_CREATING)

        # register history data to create Entity
        history: History = user.seth_entity_add(entity)

        # set status parameters
        if is_toplevel_data:
            entity.status = Entity.STATUS_TOP_LEVEL
            entity.save(update_fields=["status"])

        # create EntityAttr instances in associated with specifying data
        for attr in attrs_data:
            # This is necessary not to pass invalid parameter to DRF DB-register
            attr_referrals = attr.pop("referral", [])

            # create EntityAttr instance with user specified params
            attr_base: EntityAttr = EntityAttr.objects.create(
                **attr,
                parent_entity=entity,
            )

            # set referrals if necessary
            if attr["type"] & AttrTypeValue["object"]:
                [attr_base.referral.add(x) for x in attr_referrals]

            # make association with Entity and EntityAttrs
            entity.attrs.add(attr_base)

            # register history to modify Entity
            history.add_attr(attr_base)

        # register webhook
        for webhook_data in webhooks_data:
            webhook: Webhook = Webhook.objects.create(**webhook_data)
            entity.webhooks.add(webhook)
            try:
                resp = requests.post(
                    webhook.url,
                    **{
                        "headers": webhook.headers,
                        "data": json.dumps({}),
                        "verify": False,
                    },
                )
                # The is_verified parameter will be set True,
                # when requests received HTTP 200 from specifying endpoint.
                webhook.is_verified = resp.ok
            except ConnectionError:
                webhook.is_verified = False

            webhook.save(update_fields=["is_verified"])

        # unset Editing MODE
        entity.del_status(Entity.STATUS_CREATING)

        return entity
