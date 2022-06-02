import collections
import json
from typing import Any, Dict, List, Optional

import requests
from django.core.validators import URLValidator
from requests.exceptions import ConnectionError
import custom_view

from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied

from airone.lib.acl import ACLType
from airone.lib.types import AttrTypeValue
from entity.models import Entity, EntityAttr
from user.models import History, User
from webhook.models import Webhook


class WebhookHeadersSerializer(serializers.Serializer):
    header_key = serializers.CharField()
    header_value = serializers.CharField()


class WebhookSerializer(serializers.ModelSerializer):
    headers = serializers.ListField(child=WebhookHeadersSerializer(), required=False)
    is_deleted = serializers.BooleanField(required=False, default=False, write_only=True)
    url = serializers.CharField(required=False, max_length=200)

    class Meta:
        model = Webhook
        fields = ["id", "label", "url", "is_enabled", "is_verified", "headers", "is_deleted"]
        read_only_fields = ["is_verified"]

    def validate(self, webhook):
        if not webhook.get("is_deleted"):
            validator = URLValidator()
            validator(webhook.get("url"))

        return webhook


class WebhookUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    url = serializers.CharField(required=False, max_length=200)
    headers = serializers.ListField(child=WebhookHeadersSerializer(), required=False)
    is_deleted = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = Webhook
        fields = ["id", "label", "url", "is_enabled", "is_verified", "headers", "is_deleted"]
        read_only_fields = ["is_verified"]
        extra_kwargs = {"url": {"required": False}}

    def validate_id(self, id):
        entity: Entity = self.parent.parent.instance
        if not entity.webhooks.filter(id=id).exists():
            raise ValidationError("Invalid id(%s) object does not exist" % id)

        return id

    def validate(self, webhook):
        # case create Webhook
        if "id" not in webhook and "url" not in webhook:
            raise ValidationError("id or url field is required")

        if not webhook.get("is_deleted"):
            validator = URLValidator()
            validator(webhook.get("url"))

        return webhook


class EntityAttrCreateSerializer(serializers.ModelSerializer):
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

    def validate(self, attr):
        referral = attr.get("referral", [])

        if attr["type"] & AttrTypeValue["object"] and not len(referral):
            raise ValidationError("When specified object type, referral field is required")

        return attr


class EntityAttrUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    is_deleted = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = EntityAttr
        fields = [
            "id",
            "name",
            "type",
            "is_mandatory",
            "referral",
            "index",
            "is_summarized",
            "is_delete_in_chain",
            "is_deleted",
        ]
        extra_kwargs = {"name": {"required": False}, "type": {"required": False}}

    def validate_id(self, id):
        entity: Entity = self.parent.parent.instance
        entity_attr: Optional[EntityAttr] = entity.attrs.filter(id=id, is_active=True).first()
        if not entity_attr:
            raise ValidationError("Invalid id(%s) object does not exist" % id)

        return id

    def validate_type(self, type):
        if type not in AttrTypeValue.values():
            raise ValidationError("attrs type(%s) does not exist" % type)

        return type

    def validate(self, attr):
        # case update EntityAttr
        if "id" in attr:
            entity_attr = EntityAttr.objects.get(id=attr["id"])
            if "type" in attr and attr["type"] != entity_attr.type:
                raise ValidationError("type cannot be changed")

            user: User = self.context["request"].user
            if attr["is_deleted"] and not user.has_permission(entity_attr, ACLType.Full):
                raise PermissionDenied("Does not have permission to delete")
            if not attr["is_deleted"] and not user.has_permission(entity_attr, ACLType.Writable):
                raise PermissionDenied("Does not have permission to update")

        # case create EntityAttr
        else:
            if "name" not in attr or "type" not in attr:
                raise ValidationError("id or (name and type) field is required")

            referral = attr.get("referral", [])
            if attr["type"] & AttrTypeValue["object"] and not len(referral):
                raise ValidationError("When specified object type, referral field is required")

        return attr


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ["id", "name"]

    def _update_or_create(self, user, validated_data, is_toplevel_data, attrs_data, webhooks_data):
        entity: Entity
        entity, is_created_entity = Entity.objects.update_or_create(
            id=validated_data.get("id", None), defaults={**validated_data}
        )

        # register history to create, update Entity
        if is_created_entity:
            entity.set_status(Entity.STATUS_CREATING)
            history: History = user.seth_entity_add(entity)
        else:
            entity.set_status(Entity.STATUS_EDITING)
            history: History = user.seth_entity_mod(entity)

        # set status parameters
        if is_toplevel_data:
            entity.status = Entity.STATUS_TOP_LEVEL
            entity.save(update_fields=["status"])

        # create EntityAttr instances in associated with specifying data
        for attr_data in attrs_data:
            # This is necessary not to pass invalid parameter to DRF DB-register
            attr_referrals = attr_data.pop("referral", [])

            # delete EntityAttr if necessary
            attr_id = attr_data.get("id", None)
            is_deleted = attr_data.pop("is_deleted", False)
            if is_deleted:
                if attr_id:
                    entity_attr: EntityAttr = EntityAttr.objects.get(id=attr_data["id"])
                    entity_attr.delete()
                    # register history data to delete EntityAttr
                    history.del_attr(entity_attr)
                continue

            # create, update EntityAttr instance with user specified params
            (entity_attr, is_created_attr) = EntityAttr.objects.update_or_create(
                id=attr_id, defaults={**attr_data, "parent_entity": entity}
            )

            # set referrals if necessary
            if entity_attr.type & AttrTypeValue["object"]:
                entity_attr.referral.clear()
                [entity_attr.referral.add(x) for x in attr_referrals]

            # make association with Entity and EntityAttrs
            entity.attrs.add(entity_attr)

            # register history to create, update EntityAttr
            if is_created_attr:
                history.add_attr(entity_attr)
            else:
                history.mod_attr(entity_attr)

        # register webhook
        for webhook_data in webhooks_data:
            # delete Webhook if necessary
            webhook_id = webhook_data.get("id")
            is_deleted = webhook_data.pop("is_deleted", False)

            if is_deleted:
                if webhook_id:
                    webhook: Webhook = Webhook.objects.get(id=webhook_id)
                    webhook.delete()
                continue

            webhook: Webhook
            webhook, is_created_webhook = Webhook.objects.update_or_create(
                id=webhook_data.get("id", None), defaults={**webhook_data}
            )
            entity.webhooks.add(webhook)
            try:
                resp = requests.post(
                    webhook.url,
                    **{
                        "headers": {x["header_key"]: x["header_value"] for x in webhook.headers},
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
        if is_created_entity:
            entity.del_status(Entity.STATUS_CREATING)
        else:
            entity.del_status(Entity.STATUS_EDITING)

        return entity


class EntityCreateSerializer(EntitySerializer):
    is_toplevel = serializers.BooleanField(write_only=True, required=False, default=False)
    attrs = serializers.ListField(
        child=EntityAttrCreateSerializer(), write_only=True, required=False, default=[]
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
        counter = collections.Counter([attr["name"] for attr in attrs])
        if len([v for v, count in counter.items() if count > 1]):
            raise ValidationError("Duplicated attribute names are not allowed")

        return attrs

    def create(self, validated_data):
        user: User = self.context["request"].user

        if custom_view.is_custom("before_create_entity"):
            custom_view.call_custom("before_create_entity", None, validated_data)

        is_toplevel_data = validated_data.pop("is_toplevel")
        attrs_data = validated_data.pop("attrs")
        webhooks_data = validated_data.pop("webhooks")

        return self._update_or_create(
            user, validated_data, is_toplevel_data, attrs_data, webhooks_data
        )


class EntityUpdateSerializer(EntitySerializer):
    is_toplevel = serializers.BooleanField(write_only=True, required=False)
    attrs = serializers.ListField(
        child=EntityAttrUpdateSerializer(), write_only=True, required=False, default=[]
    )
    webhooks = WebhookUpdateSerializer(many=True, write_only=True, required=False, default=[])

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "is_toplevel", "attrs", "webhooks"]
        extra_kwargs = {"name": {"required": False}, "note": {"write_only": True}}

    def validate_name(self, name):
        if self.instance.name != name and Entity.objects.filter(name=name, is_active=True).exists():
            raise ValidationError("Duplication error. There is same named Entity")

        return name

    def validate_attrs(self, attrs):
        entity: Entity = self.instance

        # duplication checks
        attr_names = {}
        for current_attr in entity.attrs.filter(is_active=True):
            attr_names[current_attr.id] = current_attr.name

        for update_attr in attrs:
            if "id" in update_attr:
                if "name" in update_attr:
                    attr_names[update_attr["id"]] = update_attr["name"]
                if update_attr["is_deleted"]:
                    attr_names.pop(update_attr["id"])

        counter = collections.Counter(
            [x for x in attr_names.values()] + [attr["name"] for attr in attrs if "id" not in attr]
        )
        if len([v for v, count in counter.items() if count > 1]):
            raise ValidationError("Duplicated attribute names are not allowed")

        return attrs

    def update(self, entity: Entity, validated_data):
        user: User = self.context["request"].user

        if custom_view.is_custom("before_update_entity"):
            custom_view.call_custom("before_update_entity", None, validated_data, entity)

        validated_data["id"] = entity.id
        is_toplevel_data = validated_data.pop(
            "is_toplevel", (entity.status & Entity.STATUS_TOP_LEVEL) != 0
        )
        attrs_data = validated_data.pop("attrs")
        webhooks_data = validated_data.pop("webhooks")

        return self._update_or_create(
            user, validated_data, is_toplevel_data, attrs_data, webhooks_data
        )


class EntityListSerializer(EntitySerializer):
    is_toplevel = serializers.SerializerMethodField(method_name="get_is_toplevel")

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "status", "is_toplevel"]

    def get_is_toplevel(self, obj: Entity) -> bool:
        return (obj.status & Entity.STATUS_TOP_LEVEL) != 0


class EntityDetailSerializer(EntityListSerializer):
    attrs = serializers.SerializerMethodField(method_name="get_attrs")
    webhooks = WebhookSerializer(many=True)

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "status", "is_toplevel", "attrs", "webhooks"]

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
                "referral": [
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
