from typing import Any, Dict, List, Optional, TypedDict

from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

import custom_view
from acl.models import ACLBase
from airone.lib.acl import ACLType
from airone.lib.types import AttrDefaultValue, AttrTypeValue
from entity.api_v2.serializers import EntitySerializer
from entity.models import Entity
from entry.models import Attribute, AttributeValue, Entry
from group.models import Group
from job.models import Job
from user.api_v2.serializers import UserBaseSerializer
from user.models import User


class EntityAttributeType(TypedDict):
    id: int
    name: str


class EntryAttributeValueObject(TypedDict):
    id: Optional[int]
    name: str
    schema: EntityAttributeType


class EntryAttributeValueGroup(TypedDict):
    id: int
    name: str


# A thin container returns typed value(s)
class EntryAttributeValue(TypedDict, total=False):
    as_object: Optional[EntryAttributeValueObject]
    as_string: str
    as_named_object: Dict[str, Optional[EntryAttributeValueObject]]
    as_array_object: List[Optional[EntryAttributeValueObject]]
    as_array_string: List[str]
    as_array_named_object: List[Dict[str, Optional[EntryAttributeValueObject]]]
    as_array_group: List[EntryAttributeValueGroup]
    # text; use string instead
    as_boolean: bool
    as_group: Optional[EntryAttributeValueGroup]
    # date; use string instead


class EntryAttributeType(TypedDict):
    id: Optional[int]
    type: int
    is_mandatory: bool
    value: EntryAttributeValue
    schema: EntityAttributeType


class EntryBaseSerializer(serializers.ModelSerializer):
    schema = EntitySerializer(read_only=True)
    deleted_user = UserBaseSerializer(read_only=True)

    class Meta:
        model = Entry
        fields = ["id", "name", "schema", "is_active", "deleted_user", "deleted_time"]
        extra_kwargs = {
            "id": {"read_only": True},
            "name": {"read_only": True},
            "is_active": {"read_only": True},
        }

    def _validate(self, name: str, schema: Entity, attrs: List[Dict[str, Any]]):
        # check name
        if name and Entry.objects.filter(name=name, schema=schema, is_active=True).exists():
            # In update case, there is no problem with the same name
            if not (self.instance and self.instance.name == name):
                raise ValidationError("specified name(%s) already exists" % name)

        # In create case, check attrs mandatory attribute
        if not self.instance:
            user: User = self.context["request"].user
            for mandatory_attr in schema.attrs.filter(is_mandatory=True, is_active=True):
                if not user.has_permission(mandatory_attr, ACLType.Writable):
                    raise ValidationError(
                        "mandatory attrs id(%s) is permission denied" % mandatory_attr.id
                    )

                if mandatory_attr.id not in [attr["id"] for attr in attrs]:
                    raise ValidationError(
                        "mandatory attrs id(%s) is not specified" % mandatory_attr.id
                    )

        # check attrs
        for attr in attrs:
            # check attrs id
            entity_attr = schema.attrs.filter(id=attr["id"], is_active=True).first()
            if not entity_attr:
                raise ValidationError("attrs id(%s) does not exist" % attr["id"])

            # check attrs value
            (is_valid, msg) = AttributeValue.validate_attr_value(
                entity_attr.type, attr["value"], entity_attr.is_mandatory
            )
            if not is_valid:
                raise ValidationError("attrs id(%s) - %s" % (attr["id"], msg))


@extend_schema_field({})
class AttributeValueField(serializers.Field):
    def to_internal_value(self, data):
        return data


class AttributeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    value = AttributeValueField(allow_null=True)


class EntryCreateData(TypedDict, total=False):
    name: str
    schema: Entity
    attrs: List[AttributeSerializer]
    created_user: User


@extend_schema_serializer(exclude_fields=["schema"])
class EntryCreateSerializer(EntryBaseSerializer):
    schema = serializers.PrimaryKeyRelatedField(
        queryset=Entity.objects.all(), write_only=True, required=True
    )
    attrs = serializers.ListField(child=AttributeSerializer(), write_only=True, required=False)
    created_user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Entry
        fields = ["id", "name", "schema", "attrs", "created_user"]

    def validate(self, params):
        self._validate(params["name"], params["schema"], params.get("attrs", []))
        return params

    def create(self, validated_data: EntryCreateData):
        user: User = self.context["request"].user

        entity_name = validated_data["schema"].name
        if custom_view.is_custom("before_create_entry_v2", entity_name):
            validated_data = custom_view.call_custom(
                "before_create_entry_v2", entity_name, user, validated_data
            )

        attrs_data = validated_data.pop("attrs", [])
        entry: Entry = Entry.objects.create(**validated_data, status=Entry.STATUS_CREATING)

        for entity_attr in entry.schema.attrs.filter(is_active=True):
            attr: Attribute = entry.add_attribute_from_base(entity_attr, user)

            # skip for unpermitted attributes
            if not user.has_permission(attr, ACLType.Writable):
                continue

            # make an initial AttributeValue object if the initial value is specified
            attr_data = [x for x in attrs_data if int(x["id"]) == entity_attr.id]
            if not attr_data:
                continue
            attr.add_value(user, attr_data[0]["value"])

        if custom_view.is_custom("after_create_entry_v2", entity_name):
            custom_view.call_custom("after_create_entry_v2", entity_name, user, entry)

        # register entry information to Elasticsearch
        entry.register_es()

        # clear flag to specify this entry has been completed to create
        entry.del_status(Entry.STATUS_CREATING)

        # Send notification to the webhook URL
        job_notify_event: Job = Job.new_notify_create_entry(user, entry)
        job_notify_event.run()

        return entry


class EntryUpdateData(TypedDict, total=False):
    name: str
    attrs: List[AttributeSerializer]


class EntryUpdateSerializer(EntryBaseSerializer):
    attrs = serializers.ListField(child=AttributeSerializer(), write_only=True, required=False)

    class Meta:
        model = Entry
        fields = ["id", "name", "attrs"]
        extra_kwargs = {
            "name": {"required": False},
        }

    def validate(self, params):
        self._validate(params.get("name", None), self.instance.schema, params.get("attrs", []))
        return params

    def update(self, entry: Entry, validated_data: EntryUpdateData):
        entry.set_status(Entry.STATUS_EDITING)
        user: User = self.context["request"].user

        entity_name = entry.schema.name
        if custom_view.is_custom("before_update_entry_v2", entity_name):
            validated_data = custom_view.call_custom(
                "before_update_entry_v2", entity_name, user, validated_data, entry
            )

        attrs_data = validated_data.pop("attrs", [])

        # update name of Entry object. If name would be updated, the elasticsearch data of entries
        # that refers this entry also be updated by creating REGISTERED_REFERRALS task.
        job_register_referrals: Optional[Job] = None
        if "name" in validated_data and entry.name != validated_data["name"]:
            entry.name = validated_data["name"]
            entry.save(update_fields=["name"])
            job_register_referrals = Job.new_register_referrals(user, entry)

        for entity_attr in entry.schema.attrs.filter(is_active=True):
            attr: Attribute = entry.attrs.filter(schema=entity_attr, is_active=True).first()
            if not attr:
                attr = entry.add_attribute_from_base(entity_attr, user)

            # skip for unpermitted attributes
            if not user.has_permission(attr, ACLType.Writable):
                continue

            # make AttributeValue object if the value is specified
            attr_data = [x for x in attrs_data if int(x["id"]) == entity_attr.id]
            if not attr_data:
                continue

            # Check a new update value is specified, or not
            if not attr.is_updated(attr_data[0]["value"]):
                continue

            attr.add_value(user, attr_data[0]["value"])

        if custom_view.is_custom("after_update_entry_v2", entity_name):
            custom_view.call_custom("after_update_entry_v2", entity_name, user, entry)

        # update entry information to Elasticsearch
        entry.register_es()

        # clear flag to specify this entry has been completed to edit
        entry.del_status(Entry.STATUS_EDITING)

        # running job of re-register referrals because of chaning entry's name
        if job_register_referrals:
            job_register_referrals.run()

        # running job to notify changing entry event
        job_notify_event: Job = Job.new_notify_update_entry(user, entry)
        job_notify_event.run()

        return entry


class EntryRetrieveSerializer(EntryBaseSerializer):
    attrs = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = ["id", "name", "schema", "is_active", "deleted_user", "deleted_time", "attrs"]
        read_only_fields = ["is_active"]

    def get_attrs(self, obj: Entry) -> List[EntryAttributeType]:
        def get_attr_value(attr: Attribute) -> EntryAttributeValue:
            attrv = attr.get_latest_value(is_readonly=True)

            if not attrv:
                return {}

            if attr.schema.type & AttrTypeValue["array"]:
                if attr.schema.type & AttrTypeValue["string"]:
                    return {
                        "as_array_string": [x.value for x in attrv.data_array.all()],
                    }

                elif attr.schema.type & AttrTypeValue["named"]:
                    array_named_object: List[Dict[str, Optional[EntryAttributeValueObject]]] = [
                        {
                            x.value: {
                                "id": x.referral.id if x.referral else None,
                                "name": x.referral.name if x.referral else "",
                                "schema": {
                                    "id": x.referral.entry.schema.id,
                                    "name": x.referral.entry.schema.name,
                                },
                            }
                            if x.referral
                            else None,
                        }
                        for x in attrv.data_array.all()
                    ]
                    return {"as_array_named_object": array_named_object}

                elif attr.schema.type & AttrTypeValue["object"]:
                    return {
                        "as_array_object": [
                            {
                                "id": x.referral.id if x.referral else None,
                                "name": x.referral.name if x.referral else "",
                                "schema": {
                                    "id": x.referral.entry.schema.id,
                                    "name": x.referral.entry.schema.name,
                                },
                            }
                            if x.referral
                            else None
                            for x in attrv.data_array.all()
                        ]
                    }

                elif attr.schema.type & AttrTypeValue["group"]:
                    groups = [Group.objects.get(id=x.value) for x in attrv.data_array.all()]
                    return {
                        "as_array_group": [
                            {
                                "id": group.id,
                                "name": group.name,
                            }
                            for group in groups
                        ]
                    }

            elif (
                attr.schema.type & AttrTypeValue["string"]
                or attr.schema.type & AttrTypeValue["text"]
            ):
                return {"as_string": attrv.value}

            elif attr.schema.type & AttrTypeValue["named"]:
                named: Dict[str, Optional[EntryAttributeValueObject]] = {
                    attrv.value: {
                        "id": attrv.referral.id if attrv.referral else None,
                        "name": attrv.referral.name if attrv.referral else "",
                        "schema": {
                            "id": attrv.referral.entry.schema.id,
                            "name": attrv.referral.entry.schema.name,
                        },
                    }
                    if attrv.referral
                    else None
                }
                return {"as_named_object": named}

            elif attr.schema.type & AttrTypeValue["object"]:
                return {
                    "as_object": {
                        "id": attrv.referral.id if attrv.referral else None,
                        "name": attrv.referral.name if attrv.referral else "",
                        "schema": {
                            "id": attrv.referral.entry.schema.id,
                            "name": attrv.referral.entry.schema.name,
                        },
                    }
                    if attrv.referral
                    else None
                }

            elif attr.schema.type & AttrTypeValue["boolean"]:
                return {"as_boolean": attrv.boolean}

            elif attr.schema.type & AttrTypeValue["date"]:
                return {"as_string": attrv.date if attrv.date else ""}

            elif attr.schema.type & AttrTypeValue["group"] and attrv.value:
                group = Group.objects.get(id=attrv.value)
                return {
                    "as_group": {
                        "id": group.id,
                        "name": group.name,
                    }
                }

            return {}

        def get_default_attr_value(type: int) -> EntryAttributeValue:
            if type & AttrTypeValue["array"]:
                if type & AttrTypeValue["string"]:
                    return {
                        "as_array_string": AttrDefaultValue[type],
                    }

                elif type & AttrTypeValue["named"]:
                    return {"as_array_named_object": AttrDefaultValue[type]}

                elif type & AttrTypeValue["object"]:
                    return {"as_array_object": AttrDefaultValue[type]}

                elif type & AttrTypeValue["group"]:
                    return {"as_array_group": AttrDefaultValue[type]}

            elif type & AttrTypeValue["string"] or type & AttrTypeValue["text"]:
                return {"as_string": AttrDefaultValue[type]}

            elif type & AttrTypeValue["named"]:
                return {"as_named_object": AttrDefaultValue[type]}

            elif type & AttrTypeValue["object"]:
                return {"as_object": AttrDefaultValue[type]}

            elif type & AttrTypeValue["boolean"]:
                return {"as_boolean": AttrDefaultValue[type]}

            elif type & AttrTypeValue["date"]:
                return {"as_string": AttrDefaultValue[type]}

            elif type & AttrTypeValue["group"]:
                return {"as_group": AttrDefaultValue[type]}

            raise ValidationError(f"unexpected type: {type}")

        attr_prefetch = Prefetch(
            "attribute_set",
            queryset=Attribute.objects.filter(parent_entry=obj),
            to_attr="attr_list",
        )
        entity_attrs = (
            obj.schema.attrs.filter(is_active=True)
            .prefetch_related(attr_prefetch)
            .order_by("index")
        )

        attrinfo: List[EntryAttributeType] = []
        for entity_attr in entity_attrs:
            attr = entity_attr.attr_list[0] if entity_attr.attr_list else None
            value = get_attr_value(attr) if attr else get_default_attr_value(entity_attr.type)
            attrinfo.append(
                {
                    "id": attr.id if attr else None,
                    "type": entity_attr.type,
                    "is_mandatory": entity_attr.is_mandatory,
                    "value": value,
                    "schema": {
                        "id": entity_attr.id,
                        "name": entity_attr.name,
                    },
                }
            )

        # add and remove attributes depending on entity
        if custom_view.is_custom("get_entry_attr", obj.schema.name):
            attrinfo = custom_view.call_custom(
                "get_entry_attr", obj.schema.name, obj, attrinfo, True
            )

        return attrinfo


class EntryCopySerializer(serializers.Serializer):
    copy_entry_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=True,
        allow_empty=False,
    )

    class Meta:
        fields = "copy_entry_names"

    def validate_copy_entry_names(self, copy_entry_names):
        entry: Entry = self.instance
        for copy_entry_name in copy_entry_names:
            if Entry.objects.filter(
                name=copy_entry_name, schema=entry.schema, is_active=True
            ).exists():
                raise ValidationError("specified name(%s) already exists" % copy_entry_name)


class GetEntrySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = ("id", "name")


class EntryExportSerializer(serializers.Serializer):
    format = serializers.CharField(default="yaml")

    def validate_format(self, data: str) -> str:
        if data.lower() == "csv":
            return "csv"
        return "yaml"


class GetEntryAttrReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = ACLBase
        fields = ("id", "name")
