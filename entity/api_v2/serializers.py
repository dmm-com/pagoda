import collections
import json
import math
import re
from typing import Any, List, Optional, TypedDict

import requests
from django.conf import settings
from django.core.validators import URLValidator
from drf_spectacular.utils import extend_schema_field
from requests.exceptions import ConnectionError
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

from airone.lib import custom_view, drf
from airone.lib.acl import ACLType
from airone.lib.drf import DuplicatedObjectExistsError, ObjectNotExistsError, RequiredParameterError
from airone.lib.log import Logger
from airone.lib.types import AttrType, AttrTypeValue
from entity.admin import EntityAttrResource, EntityResource
from entity.models import Entity, EntityAttr
from user.models import History, User
from webhook.models import Webhook


# Enhanced TypedDict definitions
class EntityAttrReferralData(TypedDict):
    """Type definition for EntityAttr referral data"""

    id: int
    name: str


class EntityDetailAttribute(TypedDict):
    """Enhanced type definition for Entity detail attributes"""

    id: int
    index: int
    name: str
    type: int
    is_mandatory: bool
    is_delete_in_chain: bool
    is_summarized: bool
    is_writable: bool
    referral: List[EntityAttrReferralData]
    note: str
    default_value: Any


class WebhookHeadersSerializer(serializers.Serializer):
    header_key = serializers.CharField()
    header_value = serializers.CharField()


class WebhookSerializer(serializers.ModelSerializer):
    headers = serializers.ListField(child=WebhookHeadersSerializer(), required=False)
    is_deleted = serializers.BooleanField(required=False, default=False, write_only=True)
    url = serializers.CharField(required=False, max_length=200, allow_blank=True)

    class Meta:
        model = Webhook
        fields = [
            "id",
            "label",
            "url",
            "is_enabled",
            "is_verified",
            "verification_error_details",
            "headers",
            "is_deleted",
        ]
        read_only_fields = ["is_verified", "verification_error_details"]


class WebhookCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    url = serializers.CharField(required=False, max_length=200, allow_blank=True)
    headers = serializers.ListField(child=WebhookHeadersSerializer(), required=False)
    is_deleted = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = Webhook
        fields = ["id", "label", "url", "is_enabled", "is_verified", "headers", "is_deleted"]
        read_only_fields = ["is_verified"]
        extra_kwargs = {"url": {"required": False}}

    def validate_id(self, id: Optional[int]) -> Optional[int]:
        entity: Entity = self.parent.parent.instance
        if id is not None and not entity.webhooks.filter(id=id).exists():
            raise ObjectNotExistsError("Invalid id(%s) object does not exist" % id)

        return id

    def validate(self, webhook: dict):
        # case create Webhook
        if "id" not in webhook and "url" not in webhook:
            raise RequiredParameterError("id or url field is required")

        if not webhook.get("is_deleted"):
            validator = URLValidator()
            validator(webhook.get("url"))

        return webhook


class EntityAttrCreateSerializer(serializers.ModelSerializer):
    created_user = serializers.HiddenField(default=drf.AironeUserDefault())

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
            "note",
            "default_value",
        ]

    def validate_type(self, type: Optional[int]) -> Optional[int]:
        if type is not None and type not in AttrTypeValue.values():
            raise ObjectNotExistsError("attrs type(%s) does not exist" % type)

        return type

    def _validate_default_value_for_type(self, attr_type: int, default_value):
        """
        Validates that the default_value is appropriate for the given attribute type.
        Returns the validated (and potentially converted) default value.
        """
        if default_value is None:
            return None

        # String and Text types
        if attr_type in [AttrType.STRING, AttrType.TEXT]:
            if not isinstance(default_value, str):
                raise ValidationError(
                    f"Default value must be a string for this attribute type, "
                    f"got {type(default_value).__name__}"
                )
            return default_value

        # Boolean type
        elif attr_type == AttrType.BOOLEAN:
            if isinstance(default_value, bool):
                return default_value
            raise ValidationError(
                f"Default value must be a boolean for BOOLEAN type, "
                f"got {type(default_value).__name__}"
            )

        # Number type
        elif attr_type == AttrType.NUMBER:
            if isinstance(default_value, (int, float)) and not isinstance(default_value, bool):
                if math.isnan(default_value) or math.isinf(default_value):
                    raise ValidationError(
                        "Default value cannot be NaN or Infinity for NUMBER type"
                    )
                return default_value
            raise ValidationError(
                f"Default value must be a number for NUMBER type, "
                f"got {type(default_value).__name__}"
            )

        return default_value

    def validate(self, attr: dict):
        referral = attr.get("referral", [])

        if attr["type"] & AttrType.OBJECT and not len(referral):
            raise RequiredParameterError("When specified object type, referral field is required")

        # Only String, Text, Boolean, Number types support default values (MVP)
        attr_type = attr.get("type")
        default_value = attr.get("default_value")

        if default_value is not None and attr_type is not None:
            supported_types = [AttrType.STRING, AttrType.TEXT, AttrType.BOOLEAN, AttrType.NUMBER]
            if attr_type not in supported_types:
                # Clear default_value for unsupported types
                attr["default_value"] = None
            else:
                # Validate and potentially convert the default value
                attr["default_value"] = self._validate_default_value_for_type(
                    attr_type, default_value
                )

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
            "note",
            "default_value",
        ]
        extra_kwargs = {"name": {"required": False}, "type": {"required": False}}

    def validate_id(self, id: int) -> int:
        # Handle case when serializer is used directly (e.g., in tests)
        if (
            self.parent is None
            or not hasattr(self.parent, "parent")
            or self.parent.parent is None
            or not hasattr(self.parent.parent, "instance")
        ):
            # When used directly, try to get the entity from the EntityAttr
            entity_attr: Optional[EntityAttr] = EntityAttr.objects.filter(
                id=id, is_active=True
            ).first()
            if not entity_attr:
                raise ObjectNotExistsError("Invalid id(%s) object does not exist" % id)
            return id

        # Normal case when used as nested serializer
        entity: Entity = self.parent.parent.instance
        nested_entity_attr: Optional[EntityAttr] = entity.attrs.filter(
            id=id, is_active=True
        ).first()
        if not nested_entity_attr:
            raise ObjectNotExistsError("Invalid id(%s) object does not exist" % id)

        return id

    def validate_type(self, type: Optional[int]) -> Optional[int]:
        if type is not None and type not in AttrTypeValue.values():
            raise ObjectNotExistsError("attrs type(%s) does not exist" % type)

        return type

    def _validate_default_value_for_type(self, attr_type: int, default_value):
        """
        Validates that the default_value is appropriate for the given attribute type.
        Returns the validated (and potentially converted) default value.
        """
        if default_value is None:
            return None

        # String and Text types
        if attr_type in [AttrType.STRING, AttrType.TEXT]:
            if not isinstance(default_value, str):
                raise ValidationError(
                    f"Default value must be a string for this attribute type, "
                    f"got {type(default_value).__name__}"
                )
            return default_value

        # Boolean type
        elif attr_type == AttrType.BOOLEAN:
            if isinstance(default_value, bool):
                return default_value
            raise ValidationError(
                f"Default value must be a boolean for BOOLEAN type, "
                f"got {type(default_value).__name__}"
            )

        # Number type
        elif attr_type == AttrType.NUMBER:
            if isinstance(default_value, (int, float)) and not isinstance(default_value, bool):
                if math.isnan(default_value) or math.isinf(default_value):
                    raise ValidationError(
                        "Default value cannot be NaN or Infinity for NUMBER type"
                    )
                return default_value
            raise ValidationError(
                f"Default value must be a number for NUMBER type, "
                f"got {type(default_value).__name__}"
            )

        return default_value

    def validate(self, attr: dict):
        # case update EntityAttr
        if "id" in attr:
            entity_attr = EntityAttr.objects.get(id=attr["id"])
            if "type" in attr and attr["type"] != entity_attr.type:
                raise ValidationError("type cannot be changed")

            user: User = self.context.get("_user") or self.context["request"].user
            if attr["is_deleted"] and not user.has_permission(entity_attr, ACLType.Full):
                raise PermissionDenied("Does not have permission to delete")
            if not attr["is_deleted"] and not user.has_permission(entity_attr, ACLType.Writable):
                raise PermissionDenied("Does not have permission to update")

        # case create EntityAttr
        else:
            if "name" not in attr or "type" not in attr:
                raise RequiredParameterError("id or (name and type) field is required")

            referral = attr.get("referral", [])
            if attr["type"] & AttrType.OBJECT and not len(referral):
                raise RequiredParameterError(
                    "When specified object type, referral field is required"
                )

        # Only String, Text, Boolean, Number types support default values (MVP)
        attr_type = attr.get("type")
        default_value = attr.get("default_value")

        # For updates, check existing attribute type if type is not being changed
        if "id" in attr and attr_type is None:
            entity_attr = EntityAttr.objects.get(id=attr["id"])
            attr_type = entity_attr.type

        if default_value is not None and attr_type is not None:
            supported_types = [AttrType.STRING, AttrType.TEXT, AttrType.BOOLEAN, AttrType.NUMBER]
            if attr_type not in supported_types:
                # Clear default_value for unsupported types
                attr["default_value"] = None
            else:
                # Validate and potentially convert the default value
                attr["default_value"] = self._validate_default_value_for_type(
                    attr_type, default_value
                )

        return attr


class EntityCreateData(TypedDict, total=False):
    name: str
    note: str
    item_name_pattern: str
    is_toplevel: bool
    attrs: list[EntityAttrCreateSerializer]
    webhooks: WebhookCreateUpdateSerializer
    created_user: User


class EntityUpdateData(TypedDict, total=False):
    id: int
    name: str
    note: str
    item_name_pattern: str
    is_toplevel: bool
    attrs: list[EntityAttrUpdateSerializer]
    webhooks: WebhookCreateUpdateSerializer


class EntityAttrSerializer(serializers.ModelSerializer):
    type = serializers.IntegerField(required=False, read_only=True)

    class Meta:
        model = EntityAttr
        fields = ("id", "name", "type")


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ["id", "name", "is_public"]

    def validate_item_name_pattern(self, item_name_pattern: str):
        try:
            re.compile(item_name_pattern)
        except Exception:
            raise ValidationError("Invalid regex pattern")

        return item_name_pattern

    def _validate_and_convert_default_value(self, attr_type: int, default_value):
        """
        Helper method to validate and convert default_value based on attribute type.
        This implements the same logic as EntityAttrCreateSerializer.
        """
        if default_value is None:
            return None

        # Only certain types support default values
        supported_types = [AttrType.STRING, AttrType.TEXT, AttrType.BOOLEAN, AttrType.NUMBER]
        if attr_type not in supported_types:
            return None

        # String and Text types
        if attr_type in [AttrType.STRING, AttrType.TEXT]:
            if not isinstance(default_value, str):
                raise ValidationError(
                    f"Default value must be a string for this attribute type, "
                    f"got {type(default_value).__name__}"
                )
            return default_value

        # Boolean type
        elif attr_type == AttrType.BOOLEAN:
            if isinstance(default_value, bool):
                return default_value
            raise ValidationError(
                f"Default value must be a boolean for BOOLEAN type, "
                f"got {type(default_value).__name__}"
            )

        # Number type
        elif attr_type == AttrType.NUMBER:
            if isinstance(default_value, (int, float)) and not isinstance(default_value, bool):
                if math.isnan(default_value) or math.isinf(default_value):
                    raise ValidationError(
                        "Default value cannot be NaN or Infinity for NUMBER type"
                    )
                return default_value
            raise ValidationError(
                f"Default value must be a number for NUMBER type, "
                f"got {type(default_value).__name__}"
            )

        return default_value

    def _update_or_create(
        self,
        user: User,
        entity: Entity,
        is_create_mode: bool,
        validated_data: EntityCreateData | EntityUpdateData,
    ) -> Entity:
        attrs_data: list = validated_data.get("attrs", [])
        webhooks_data: list = validated_data.get("webhooks", [])

        # register history to create, update Entity
        history: History
        if is_create_mode:
            history = user.seth_entity_add(entity)
        else:
            history = user.seth_entity_mod(entity)

        # create EntityAttr instances in associated with specifying data
        for attr_data in attrs_data:
            # Apply type-specific validation and conversion for default_value
            attr_type = attr_data.get("type")
            default_value = attr_data.get("default_value")

            if default_value is not None and attr_type is not None:
                # Apply the same validation logic as in the serializer
                try:
                    converted_value = self._validate_and_convert_default_value(
                        attr_type, default_value
                    )
                    attr_data["default_value"] = converted_value
                except Exception:
                    # If conversion fails, keep the original value
                    pass

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
                id=attr_id, defaults={**attr_data, "parent_entity": entity, "created_user": user}
            )

            # set referrals if necessary
            if entity_attr.type & AttrType.OBJECT:
                entity_attr.referral_clear()
                [entity_attr.referral.add(x) for x in attr_referrals]

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

            webhook: Webhook
            if is_deleted:
                if webhook_id:
                    webhook = Webhook.objects.get(id=webhook_id)
                    webhook.delete()
                continue

            webhook, is_created_webhook = Webhook.objects.update_or_create(
                id=webhook_data.get("id", None), defaults={**webhook_data}
            )
            entity.webhooks.add(webhook)

            try:
                resp = requests.post(
                    webhook.url,
                    json.dumps({}),
                    headers={x["header_key"]: x["header_value"] for x in webhook.headers},
                    verify=False,
                )
                # The is_verified parameter will be set True,
                # when requests received HTTP 200 from specifying endpoint.
                if resp.ok:
                    webhook.is_verified = True
                    webhook.verification_error_details = None
                else:
                    webhook.is_verified = False
                    webhook.verification_error_details = resp.reason
            except ConnectionError as e:
                webhook.is_verified = False
                webhook.verification_error_details = str(e)

            webhook.save(update_fields=["is_verified", "verification_error_details"])

        # unset Editing MODE
        if is_create_mode:
            entity.del_status(Entity.STATUS_CREATING)
            if custom_view.is_custom("after_create_entity_v2"):
                custom_view.call_custom("after_create_entity_v2", None, user, entity)
        else:
            entity.del_status(Entity.STATUS_EDITING)
            if custom_view.is_custom("after_update_entity_v2"):
                custom_view.call_custom("after_update_entity_v2", None, user, entity)

        return entity


class EntityCreateSerializer(EntitySerializer):
    is_toplevel = serializers.BooleanField(write_only=True, required=False, default=False)
    attrs = serializers.ListField(
        child=EntityAttrCreateSerializer(), write_only=True, required=False, default=[]
    )
    webhooks = WebhookCreateUpdateSerializer(many=True, write_only=True, required=False, default=[])

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "item_name_pattern", "is_toplevel", "attrs", "webhooks"]
        extra_kwargs = {"note": {"write_only": True}}

    def validate_name(self, name: str):
        if Entity.objects.filter(name=name, is_active=True).exists():
            raise DuplicatedObjectExistsError("Duplication error. There is same named Entity")

        return name

    def validate_attrs(self, attrs: list[EntityAttrCreateSerializer]):
        # duplication checks
        counter = collections.Counter([attr["name"] for attr in attrs])
        if len([v for v, count in counter.items() if count > 1]):
            raise DuplicatedObjectExistsError("Duplicated attribute names are not allowed")

        return attrs

    def validate_webhooks(self, webhooks: list[WebhookCreateUpdateSerializer]):
        # deny webhooks if its disabled
        if not settings.AIRONE_FLAGS["WEBHOOK"] and len(webhooks) > 0:
            raise ValidationError("webhook is disabled")

        return webhooks

    def create(self, validated_data: EntityCreateData) -> Entity:
        user: User | None = None
        if "request" in self.context:
            user = self.context["request"].user
        if "_user" in self.context:
            user = self.context["_user"]
        if user is None:
            raise RequiredParameterError("user is required")

        validated_data["created_user"] = user
        if custom_view.is_custom("before_create_entity_V2"):
            validated_data = custom_view.call_custom(
                "before_create_entity_v2", None, user, validated_data
            )

        entity = Entity.objects.create(
            name=validated_data.get("name"),
            note=validated_data.get("note", ""),
            item_name_pattern=validated_data.get("item_name_pattern", ""),
            created_user=validated_data.get("created_user"),
        )

        # set status parameters
        if validated_data.get("is_toplevel", False):
            entity.set_status(Entity.STATUS_TOP_LEVEL)
        entity.set_status(Entity.STATUS_CREATING)

        return entity

    def create_remaining(self, entity: Entity, validated_data: EntityCreateData) -> Entity:
        user: User | None = None
        if "request" in self.context:
            user = self.context["request"].user
        if "_user" in self.context:
            user = self.context["_user"]
        if user is None:
            raise RequiredParameterError("user is required")

        return self._update_or_create(user, entity, True, validated_data)


class EntityUpdateSerializer(EntitySerializer):
    is_toplevel = serializers.BooleanField(write_only=True, required=False)
    attrs = serializers.ListField(
        child=EntityAttrUpdateSerializer(), write_only=True, required=False, default=[]
    )
    webhooks = WebhookCreateUpdateSerializer(many=True, write_only=True, required=False, default=[])

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "item_name_pattern", "is_toplevel", "attrs", "webhooks"]
        extra_kwargs = {"name": {"required": False}, "note": {"write_only": True}}

    def validate_name(self, name: str):
        if self.instance.name != name and Entity.objects.filter(name=name, is_active=True).exists():
            raise DuplicatedObjectExistsError("Duplication error. There is same named Entity")

        return name

    def validate_attrs(self, attrs: list[EntityAttrUpdateSerializer]):
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
            raise DuplicatedObjectExistsError("Duplicated attribute names are not allowed")

        return attrs

    def validate_webhooks(self, webhooks: list[WebhookCreateUpdateSerializer]):
        entity: Entity = self.instance

        # deny changing webhooks if its disabled
        if not settings.AIRONE_FLAGS["WEBHOOK"]:
            if len(webhooks) != entity.webhooks.count():
                raise ValidationError("webhook is disabled")

        return webhooks

    def update(self, entity: Entity, validated_data: EntityUpdateData):
        user: User | None = None
        if "request" in self.context:
            user = self.context["request"].user
        if "_user" in self.context:
            user = self.context["_user"]

        if user is None:
            raise RequiredParameterError("user is required")

        if custom_view.is_custom("before_update_entity_v2"):
            validated_data = custom_view.call_custom(
                "before_update_entity_v2", None, user, validated_data, entity
            )

        # record history for specific fields on update
        updated_fields: list[str] = []
        if "name" in validated_data and entity.name != validated_data.get("name"):
            entity.name = validated_data.get("name")
            updated_fields.append("name")
        if "note" in validated_data and entity.note != validated_data.get("note"):
            entity.note = validated_data.get("note")
            updated_fields.append("note")
        if "item_name_pattern" in validated_data and entity.item_name_pattern != validated_data.get(
            "item_name_pattern"
        ):
            entity.item_name_pattern = validated_data.get("item_name_pattern")
            updated_fields.append("item_name_pattern")
        if len(updated_fields) > 0:
            entity.save(update_fields=updated_fields)
        else:
            entity.save_without_historical_record()

        # set status parameters
        if validated_data.pop("is_toplevel", (entity.status & Entity.STATUS_TOP_LEVEL) != 0):
            entity.set_status(Entity.STATUS_TOP_LEVEL)
        else:
            entity.del_status(Entity.STATUS_TOP_LEVEL)
        entity.set_status(Entity.STATUS_EDITING)

        return entity

    def update_remaining(self, entity: Entity, validated_data: EntityUpdateData) -> Entity:
        user: User | None = None
        if "request" in self.context:
            user = self.context["request"].user
        if "_user" in self.context:
            user = self.context["_user"]
        if user is None:
            raise RequiredParameterError("user is required")

        return self._update_or_create(user, entity, False, validated_data)


class EntityListSerializer(EntitySerializer):
    is_toplevel = serializers.SerializerMethodField(method_name="get_is_toplevel")

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "item_name_pattern", "status", "is_toplevel"]

    def get_is_toplevel(self, obj: Entity) -> bool:
        return (obj.status & Entity.STATUS_TOP_LEVEL) != 0


class EntityDetailAttributeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    index = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.IntegerField()
    is_mandatory = serializers.BooleanField()
    is_delete_in_chain = serializers.BooleanField()
    is_summarized = serializers.BooleanField()
    is_writable = serializers.BooleanField()
    referral = serializers.ListField(child=serializers.DictField())
    note = serializers.CharField()
    default_value = serializers.JSONField(required=False, allow_null=True)


class EntityDetailSerializer(EntityListSerializer):
    attrs = serializers.SerializerMethodField(method_name="get_attrs")
    webhooks = WebhookSerializer(many=True)
    has_ongoing_changes = serializers.SerializerMethodField()

    class Meta:
        model = Entity
        fields = [
            "id",
            "name",
            "note",
            "item_name_pattern",
            "status",
            "is_toplevel",
            "attrs",
            "webhooks",
            "is_public",
            "has_ongoing_changes",
        ]

    @extend_schema_field(serializers.ListField(child=EntityDetailAttributeSerializer()))
    def get_attrs(self, obj: Entity) -> List[EntityDetailAttribute]:
        user = User.objects.get(id=self.context["request"].user.id)

        attrinfo: List[EntityDetailAttribute] = [
            {
                "id": x.id,
                "index": x.index,
                "name": x.name,
                "type": x.type,
                "is_mandatory": x.is_mandatory,
                "is_delete_in_chain": x.is_delete_in_chain,
                "is_summarized": x.is_summarized,
                "is_writable": user.has_permission(x, ACLType.Writable),
                "referral": [
                    EntityAttrReferralData(
                        {
                            "id": r.id,
                            "name": r.name,
                        }
                    )
                    for r in x.referral.all()
                ],
                "note": x.note,
                "default_value": x.default_value,
            }
            for x in obj.attrs.filter(is_active=True).prefetch_related("referral").order_by("index")
        ]

        # add and remove attributes depending on entity
        if custom_view.is_custom("get_entity_attr", obj.name):
            attrinfo = custom_view.call_custom("get_entity_attr", obj.name, obj, attrinfo)

        return attrinfo

    def get_has_ongoing_changes(self, obj: Entity) -> bool:
        return (obj.status & Entity.STATUS_CREATING) > 0 or (obj.status & Entity.STATUS_EDITING) > 0


class EntityHistorySerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    target_obj = serializers.CharField(source="target_obj.name")

    class Meta:
        model = History
        fields = ["operation", "time", "username", "text", "target_obj", "is_detail"]
        read_only_fields = ["operation", "time", "username", "text", "target_obj", "is_detail"]

    def get_username(self, obj: History) -> str:
        return obj.user.username


"""
class EntityHistorySerializer(serializers.Serializer):
    # we need diff values, not a snapshot
    user = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    changes = serializers.SerializerMethodField(method_name="get_entity_changes")

    def get_user(self, history):
        if not history.history_user:
            return {}

        return {
            "id": history.history_user.id,
            "username": history.history_user.username,
        }

    def get_time(self, history):
        return history.history_date

    def get_entity_changes(self, history):
        if history.prev_record:
            delta = history.diff_against(history.prev_record)
            return [
                {
                    "action": "update",
                    "target": change.field,
                    "old": change.old,
                    "new": change.new,
                }
                for change in delta.changes
            ]
        else:
            return [
                {"action": "create", "target": field, "old": "", "new": getattr(history, field)}
                for field in ["name", "note"]
            ]
"""


# The format keeps compatibility with entity.views and dashboard.views
class EntityAttrImportExportSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False)
    type = serializers.IntegerField(required=False)
    entity = serializers.CharField(required=False)
    created_user = serializers.CharField(required=False)
    refer = serializers.CharField(allow_blank=True)

    class Meta:
        model = EntityAttr
        fields = ["id", "name", "type", "entity", "is_mandatory", "created_user", "refer"]

    def to_representation(self, instance: EntityAttr):
        return {
            "created_user": instance.created_user.username,
            "entity": instance.parent_entity.name,
            "id": instance.id,
            "is_mandatory": instance.is_mandatory,
            "name": instance.name,
            "refer": ",".join(
                list(map(lambda x: x.name, instance.referral.filter(is_active=True)))
            ),
            "type": instance.type,
        }


# The format keeps compatibility with entity.views and dashboard.views
class EntityImportExportSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False)
    created_user = serializers.CharField(required=False)

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "item_name_pattern", "status", "created_user"]

    def to_representation(self, instance: Entity):
        ret = super().to_representation(instance)
        ret["created_user"] = instance.created_user.username
        return ret


# The format keeps compatibility with entity.views and dashboard.views
class EntityImportExportRootSerializer(serializers.Serializer):
    Entity = EntityImportExportSerializer(many=True)
    EntityAttr = EntityAttrImportExportSerializer(many=True)

    def save(self, **kwargs) -> None:
        user: User = self.context.get("request").user

        def _do_import(resource, iter_data: Any):
            results = []
            for data in iter_data:
                try:
                    result = resource.import_data_from_request(data, user)
                    results.append({"result": result, "data": data})
                except RuntimeError as e:
                    Logger.warning(("(%s) %s " % (resource, data)) + str(e))
            if results:
                resource.after_import_completion(results)

        _do_import(EntityResource, self.validated_data["Entity"])
        _do_import(EntityAttrResource, self.validated_data["EntityAttr"])


class EntityAttrNameSerializer(serializers.ListSerializer):
    child = serializers.CharField()
