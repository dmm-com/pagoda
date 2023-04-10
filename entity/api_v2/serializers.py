import collections
import json
from typing import Any, Dict, List, Optional, TypedDict, Union

import requests
from django.core.validators import URLValidator
from drf_spectacular.utils import extend_schema_field
from requests.exceptions import ConnectionError
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

import custom_view
from airone.lib.acl import ACLType
from airone.lib.drf import DuplicatedObjectExistsError, ObjectNotExistsError, RequiredParameterError
from airone.lib.log import Logger
from airone.lib.types import AttrTypeValue
from entity.admin import EntityAttrResource, EntityResource
from entity.models import Entity, EntityAttr
from user.models import History, User
from webhook.models import Webhook


class WebhookHeadersSerializer(serializers.Serializer):
    header_key = serializers.CharField()
    header_value = serializers.CharField()


class WebhookSerializer(serializers.ModelSerializer):
    headers = serializers.ListField(child=WebhookHeadersSerializer(), required=False)
    is_deleted = serializers.BooleanField(required=False, default=False, write_only=True)
    url = serializers.CharField(required=False, max_length=200, allow_blank=True)

    class Meta:
        model = Webhook
        fields = ["id", "label", "url", "is_enabled", "is_verified", "headers", "is_deleted"]
        read_only_fields = ["is_verified"]


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

    def validate_id(self, id: Optional[int]):
        entity: Entity = self.parent.parent.instance
        if id is not None and not entity.webhooks.filter(id=id).exists():
            raise ObjectNotExistsError("Invalid id(%s) object does not exist" % id)

        return id

    def validate(self, webhook):
        # case create Webhook
        if "id" not in webhook and "url" not in webhook:
            raise RequiredParameterError("id or url field is required")

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
            raise ObjectNotExistsError("attrs type(%s) does not exist" % type)

        return type

    def validate(self, attr):
        referral = attr.get("referral", [])

        if attr["type"] & AttrTypeValue["object"] and not len(referral):
            raise RequiredParameterError("When specified object type, referral field is required")

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
            raise ObjectNotExistsError("Invalid id(%s) object does not exist" % id)

        return id

    def validate_type(self, type):
        if type not in AttrTypeValue.values():
            raise ObjectNotExistsError("attrs type(%s) does not exist" % type)

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
                raise RequiredParameterError("id or (name and type) field is required")

            referral = attr.get("referral", [])
            if attr["type"] & AttrTypeValue["object"] and not len(referral):
                raise RequiredParameterError(
                    "When specified object type, referral field is required"
                )

        return attr


class EntityCreateData(TypedDict, total=False):
    name: str
    note: str
    is_toplevel: bool
    attrs: List[EntityAttrCreateSerializer]
    webhooks: WebhookCreateUpdateSerializer
    created_user: User


class EntityUpdateData(TypedDict, total=False):
    id: int
    name: str
    note: str
    is_toplevel: bool
    attrs: List[EntityAttrUpdateSerializer]
    webhooks: WebhookCreateUpdateSerializer


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ["id", "name", "is_public"]

    def _update_or_create(
        self,
        user: User,
        entity_id: Optional[int],
        validated_data: Union[EntityCreateData, EntityUpdateData],
    ):
        is_toplevel_data = validated_data.pop("is_toplevel", None)
        attrs_data = validated_data.pop("attrs")
        webhooks_data = validated_data.pop("webhooks")
        entity: Entity
        entity, is_created_entity = Entity.objects.update_or_create(
            id=entity_id, defaults={**validated_data}
        )

        if is_toplevel_data is None:
            is_toplevel_data = (entity.status & Entity.STATUS_TOP_LEVEL) != 0

        # register history to create, update Entity
        history: History
        if is_created_entity:
            entity.set_status(Entity.STATUS_CREATING)
            history = user.seth_entity_add(entity)
        else:
            entity.set_status(Entity.STATUS_EDITING)
            history = user.seth_entity_mod(entity)

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
                id=attr_id, defaults={**attr_data, "parent_entity": entity, "created_user": user}
            )

            # set referrals if necessary
            if entity_attr.type & AttrTypeValue["object"]:
                entity_attr.referral_clear()
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
                webhook.is_verified = resp.ok
            except ConnectionError:
                webhook.is_verified = False

            webhook.save(update_fields=["is_verified"])

        # unset Editing MODE
        if is_created_entity:
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
    created_user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "is_toplevel", "attrs", "webhooks", "created_user"]
        extra_kwargs = {"note": {"write_only": True}}

    def validate_name(self, name):
        if Entity.objects.filter(name=name, is_active=True).exists():
            raise DuplicatedObjectExistsError("Duplication error. There is same named Entity")

        return name

    def validate_attrs(self, attrs: List[EntityAttrCreateSerializer]):
        # duplication checks
        counter = collections.Counter([attr["name"] for attr in attrs])
        if len([v for v, count in counter.items() if count > 1]):
            raise DuplicatedObjectExistsError("Duplicated attribute names are not allowed")

        return attrs

    def create(self, validated_data: EntityCreateData):
        user: User = self.context["request"].user

        if custom_view.is_custom("before_create_entity_V2"):
            validated_data = custom_view.call_custom(
                "before_create_entity_v2", None, user, validated_data
            )

        return self._update_or_create(user, None, validated_data)


class EntityUpdateSerializer(EntitySerializer):
    is_toplevel = serializers.BooleanField(write_only=True, required=False)
    attrs = serializers.ListField(
        child=EntityAttrUpdateSerializer(), write_only=True, required=False, default=[]
    )
    webhooks = WebhookCreateUpdateSerializer(many=True, write_only=True, required=False, default=[])

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "is_toplevel", "attrs", "webhooks"]
        extra_kwargs = {"name": {"required": False}, "note": {"write_only": True}}

    def validate_name(self, name):
        if self.instance.name != name and Entity.objects.filter(name=name, is_active=True).exists():
            raise DuplicatedObjectExistsError("Duplication error. There is same named Entity")

        return name

    def validate_attrs(self, attrs: List[EntityAttrUpdateSerializer]):
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

    def update(self, entity: Entity, validated_data: EntityUpdateData):
        user: User = self.context["request"].user

        if custom_view.is_custom("before_update_entity_v2"):
            validated_data = custom_view.call_custom(
                "before_update_entity_v2", None, user, validated_data, entity
            )

        return self._update_or_create(user, entity.id, validated_data)


class EntityListSerializer(EntitySerializer):
    is_toplevel = serializers.SerializerMethodField(method_name="get_is_toplevel")

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "status", "is_toplevel"]

    def get_is_toplevel(self, obj: Entity) -> bool:
        return (obj.status & Entity.STATUS_TOP_LEVEL) != 0


class EntityDetailAttributeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    index = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.IntegerField()
    is_mandatory = serializers.BooleanField()
    is_delete_in_chain = serializers.BooleanField()
    referral = serializers.ListField(child=serializers.DictField())

    class EntityDetailAttribute(TypedDict):
        id: int
        index: int
        name: str
        type: int
        is_mandatory: bool
        is_delete_in_chain: bool
        referral: List[Dict[str, Any]]


class EntityDetailSerializer(EntityListSerializer):
    attrs = serializers.SerializerMethodField(method_name="get_attrs")
    webhooks = WebhookSerializer(many=True)

    class Meta:
        model = Entity
        fields = ["id", "name", "note", "status", "is_toplevel", "attrs", "webhooks", "is_public"]

    @extend_schema_field(serializers.ListField(child=EntityDetailAttributeSerializer()))
    def get_attrs(self, obj: Entity) -> List[EntityDetailAttributeSerializer.EntityDetailAttribute]:
        user = User.objects.get(id=self.context["request"].user.id)

        attrinfo: List[EntityDetailAttributeSerializer.EntityDetailAttribute] = [
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

        # add and remove attributes depending on entity
        if custom_view.is_custom("get_entity_attr", obj.name):
            attrinfo = custom_view.call_custom("get_entity_attr", obj.name, obj, attrinfo)

        return attrinfo


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
        fields = ["id", "name", "note", "status", "created_user"]

    def to_representation(self, instance: Entity):
        ret = super().to_representation(instance)
        ret["created_user"] = instance.created_user.username
        return ret


# The format keeps compatibility with entity.views and dashboard.views
class EntityImportExportRootSerializer(serializers.Serializer):
    Entity = EntityImportExportSerializer(many=True)
    EntityAttr = EntityAttrImportExportSerializer(many=True)

    def save(self, **kwargs):
        user: User = self.context.get("request").user

        def _do_import(resource, iter_data):
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
