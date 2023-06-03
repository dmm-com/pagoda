from typing import Any, Dict, List, Optional, TypedDict, Union

from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

import custom_view
from acl.models import ACLBase
from airone.lib.acl import ACLType
from airone.lib.drf import (
    DuplicatedObjectExistsError,
    IncorrectTypeError,
    ObjectNotExistsError,
    RequiredParameterError,
)
from airone.lib.types import AttrDefaultValue, AttrTypeValue
from entity.api_v2.serializers import EntitySerializer
from entity.models import Entity
from entry.models import Attribute, AttributeValue, Entry
from entry.settings import CONFIG as CONFIG_ENTRY
from group.models import Group
from job.models import Job
from role.models import Role
from user.api_v2.serializers import UserBaseSerializer
from user.models import User


class EntityAttributeType(TypedDict):
    id: int
    name: str


class EntryAttributeValueObject(TypedDict):
    id: int
    name: str
    schema: EntityAttributeType


class EntryAttributeValueObjectBoolean(EntryAttributeValueObject):
    boolean: bool


class EntryAttributeValueBoolean(TypedDict):
    boolean: bool


class EntryAttributeValueGroup(TypedDict):
    id: int
    name: str


class EntryAttributeValueRole(TypedDict):
    id: int
    name: str


# A thin container returns typed value(s)
class EntryAttributeValue(TypedDict, total=False):
    as_object: Optional[EntryAttributeValueObject]
    as_string: str
    as_named_object: Dict[str, Optional[EntryAttributeValueObject]]
    as_array_object: List[Optional[EntryAttributeValueObject]]
    as_array_string: List[str]
    as_array_named_object: List[
        Dict[
            str,
            Optional[
                Union[
                    EntryAttributeValueObject,
                    EntryAttributeValueObjectBoolean,
                    EntryAttributeValueBoolean,
                ]
            ],
        ]
    ]
    as_array_group: List[EntryAttributeValueGroup]
    # text; use string instead
    as_boolean: bool
    as_group: Optional[EntryAttributeValueGroup]
    # date; use string instead
    as_role: Optional[EntryAttributeValueRole]
    as_array_role: List[EntryAttributeValueRole]


class EntryAttributeType(TypedDict):
    id: Optional[int]
    type: int
    is_mandatory: bool
    is_readable: bool
    value: EntryAttributeValue
    schema: EntityAttributeType


class EntityAttributeTypeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class EntryAttributeValueObjectSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    schema = EntityAttributeTypeSerializer()
    boolean = serializers.BooleanField()


class EntryAttributeValueGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class EntryAttributeValueRoleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class EntryAttributeValueSerializer(serializers.Serializer):
    as_object = EntryAttributeValueObjectSerializer(allow_null=True, required=False)
    as_string = serializers.CharField(required=False)
    as_named_object = serializers.DictField(
        child=EntryAttributeValueObjectSerializer(allow_null=True), required=False
    )
    as_array_object = serializers.ListField(
        child=EntryAttributeValueObjectSerializer(allow_null=True), required=False
    )
    as_array_string = serializers.ListField(child=serializers.CharField(), required=False)
    as_array_named_object = serializers.ListField(
        child=serializers.DictField(child=EntryAttributeValueObjectSerializer(allow_null=True)),
        required=False,
    )
    as_array_group = serializers.ListField(
        child=EntryAttributeValueGroupSerializer(), required=False
    )
    # text; use string instead
    as_boolean = serializers.BooleanField(required=False)
    as_group = EntryAttributeValueGroupSerializer(allow_null=True, required=False)
    # date; use string instead
    as_role = EntryAttributeValueRoleSerializer(allow_null=True, required=False)
    as_array_role = serializers.ListField(child=EntryAttributeValueRoleSerializer(), required=False)


class EntryAttributeTypeSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    type = serializers.IntegerField()
    is_mandatory = serializers.BooleanField()
    is_readable = serializers.BooleanField()
    value = EntryAttributeValueSerializer()
    schema = EntityAttributeTypeSerializer()


class EntryBaseSerializer(serializers.ModelSerializer):
    schema = EntitySerializer(read_only=True)
    deleted_user = UserBaseSerializer(read_only=True)

    class Meta:
        model = Entry
        fields = [
            "id",
            "name",
            "schema",
            "is_active",
            "deleted_user",
            "deleted_time",
            "updated_time",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "name": {"read_only": True},
            "is_active": {"read_only": True},
        }

    def validate_name(self, name: str):
        if self.instance:
            schema = self.instance.schema
        else:
            schema = self.get_initial()["schema"]
        if name and Entry.objects.filter(name=name, schema=schema, is_active=True).exists():
            # In update case, there is no problem with the same name
            if not (self.instance and self.instance.name == name):
                raise DuplicatedObjectExistsError("specified name(%s) already exists" % name)
        return name

    def _validate(self, schema: Entity, attrs: List[Dict[str, Any]]):
        # In create case, check attrs mandatory attribute
        if not self.instance:
            user: User = self.context["request"].user
            for mandatory_attr in schema.attrs.filter(is_mandatory=True, is_active=True):
                if not user.has_permission(mandatory_attr, ACLType.Writable):
                    raise PermissionDenied(
                        "mandatory attrs id(%s) is permission denied" % mandatory_attr.id
                    )

                if mandatory_attr.id not in [attr["id"] for attr in attrs]:
                    raise RequiredParameterError(
                        "mandatory attrs id(%s) is not specified" % mandatory_attr.id
                    )

        # check attrs
        for attr in attrs:
            # check attrs id
            entity_attr = schema.attrs.filter(id=attr["id"], is_active=True).first()
            if not entity_attr:
                raise ObjectNotExistsError("attrs id(%s) does not exist" % attr["id"])

            # check attrs value
            (is_valid, msg) = AttributeValue.validate_attr_value(
                entity_attr.type, attr["value"], entity_attr.is_mandatory
            )
            if not is_valid:
                raise IncorrectTypeError("attrs id(%s) - %s" % (attr["id"], msg))


@extend_schema_field({})
class AttributeValueField(serializers.Field):
    def to_internal_value(self, data):
        return data


class AttributeDataSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    value = AttributeValueField(allow_null=True)


class EntryCreateData(TypedDict, total=False):
    name: str
    schema: Entity
    attrs: List[AttributeDataSerializer]
    created_user: User


@extend_schema_serializer(exclude_fields=["schema"])
class EntryCreateSerializer(EntryBaseSerializer):
    schema = serializers.PrimaryKeyRelatedField(
        queryset=Entity.objects.all(), write_only=True, required=True
    )
    attrs = serializers.ListField(child=AttributeDataSerializer(), write_only=True, required=False)
    created_user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Entry
        fields = ["id", "name", "schema", "attrs", "created_user"]

    def validate(self, params):
        self._validate(params["schema"], params.get("attrs", []))
        return params

    def create(self, validated_data: EntryCreateData):
        user: User = self.context["request"].user

        entity_name = validated_data["schema"].name
        if custom_view.is_custom("before_create_entry_v2", entity_name):
            validated_data = custom_view.call_custom(
                "before_create_entry_v2", entity_name, user, validated_data
            )

        attrs_data = validated_data.pop("attrs", [])
        entry: Entry = Entry(**validated_data, status=Entry.STATUS_CREATING)

        # for history record
        entry._history_user = user

        entry.save()

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
    attrs: List[AttributeDataSerializer]


class EntryUpdateSerializer(EntryBaseSerializer):
    attrs = serializers.ListField(child=AttributeDataSerializer(), write_only=True, required=False)

    class Meta:
        model = Entry
        fields = ["id", "name", "attrs"]
        extra_kwargs = {
            "name": {"required": False},
        }

    def validate(self, params):
        self._validate(self.instance.schema, params.get("attrs", []))
        return params

    def update(self, entry: Entry, validated_data: EntryUpdateData):
        entry.set_status(Entry.STATUS_EDITING)
        user: User = self.context["request"].user

        # for history record
        entry._history_user = user

        entity_name = entry.schema.name
        if custom_view.is_custom("before_update_entry_v2", entity_name):
            validated_data = custom_view.call_custom(
                "before_update_entry_v2", entity_name, user, validated_data, entry
            )

        attrs_data = validated_data.pop("attrs", [])

        is_updated = False
        # update name of Entry object. If name would be updated, the elasticsearch data of entries
        # that refers this entry also be updated by creating REGISTERED_REFERRALS task.
        job_register_referrals: Optional[Job] = None
        if "name" in validated_data and entry.name != validated_data["name"]:
            entry.name = validated_data["name"]
            entry.save(update_fields=["name"])
            is_updated = True
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
            is_updated = True

        if custom_view.is_custom("after_update_entry_v2", entity_name):
            custom_view.call_custom("after_update_entry_v2", entity_name, user, entry)

        # update entry information to Elasticsearch
        if is_updated:
            entry.register_es()

        # clear flag to specify this entry has been completed to edit
        entry.del_status(Entry.STATUS_EDITING)

        # running job of re-register referrals because of chaning entry's name
        if job_register_referrals:
            job_register_referrals.run()

        # running job to notify changing entry event
        if is_updated:
            job_notify_event: Job = Job.new_notify_update_entry(user, entry)
            job_notify_event.run()

        return entry


class EntryRetrieveSerializer(EntryBaseSerializer):
    attrs = serializers.SerializerMethodField()
    schema = EntitySerializer()

    class Meta:
        model = Entry
        fields = [
            "id",
            "name",
            "schema",
            "is_active",
            "deleted_user",
            "deleted_time",
            "attrs",
            "is_public",
        ]
        read_only_fields = ["is_active"]

    @extend_schema_field(serializers.ListField(child=EntryAttributeTypeSerializer()))
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
                    array_named_object: List[
                        Dict[
                            str,
                            Optional[
                                Union[
                                    EntryAttributeValueObject,
                                    EntryAttributeValueObjectBoolean,
                                    EntryAttributeValueBoolean,
                                ]
                            ],
                        ]
                    ] = [
                        {
                            x.value: {
                                "id": x.referral.id if x.referral else None,
                                "name": x.referral.name if x.referral else "",
                                "schema": {
                                    "id": x.referral.entry.schema.id,
                                    "name": x.referral.entry.schema.name,
                                },
                            }
                            if x.referral and x.referral.is_active
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
                            for x in attrv.data_array.all()
                            if x.referral and x.referral.is_active
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

                elif attr.schema.type & AttrTypeValue["role"]:
                    roles = [Role.objects.get(id=x.value) for x in attrv.data_array.all()]
                    return {
                        "as_array_role": [
                            {
                                "id": role.id,
                                "name": role.name,
                            }
                            for role in roles
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
                    if attrv.referral and attrv.referral.is_active
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
                    if attrv.referral and attrv.referral.is_active
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

            elif attr.schema.type & AttrTypeValue["role"] and attrv.value:
                role = Role.objects.get(id=attrv.value)
                return {
                    "as_role": {
                        "id": role.id,
                        "name": role.name,
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

                elif type & AttrTypeValue["role"]:
                    return {"as_array_role": AttrDefaultValue[type]}

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

            elif type & AttrTypeValue["role"]:
                return {"as_role": AttrDefaultValue[type]}

            raise IncorrectTypeError(f"unexpected type: {type}")

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

        user: User = self.context["request"].user

        attrinfo: List[EntryAttributeType] = []
        for entity_attr in entity_attrs:
            attr = entity_attr.attr_list[0] if entity_attr.attr_list else None
            if attr:
                is_readable = user.has_permission(attr, ACLType.Readable)
            else:
                is_readable = user.has_permission(entity_attr, ACLType.Readable)
            value = (
                get_attr_value(attr)
                if attr and is_readable
                else get_default_attr_value(entity_attr.type)
            )
            attrinfo.append(
                {
                    "id": attr.id if attr else None,
                    "type": entity_attr.type,
                    "is_mandatory": entity_attr.is_mandatory,
                    "is_readable": is_readable,
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
                raise DuplicatedObjectExistsError(
                    "specified name(%s) already exists" % copy_entry_name
                )


class EntryExportSerializer(serializers.Serializer):
    format = serializers.CharField(default="yaml")

    def validate_format(self, data: str) -> str:
        if data.lower() == "csv":
            return "csv"
        return "yaml"


class EntryImportAttributeSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = AttributeValueField(allow_null=True)


class EntryImportEntriesSerializer(serializers.Serializer):
    name = serializers.CharField()
    attrs = serializers.ListField(child=EntryImportAttributeSerializer(), required=False)


class EntryImportEntitySerializer(serializers.Serializer):
    entity = serializers.CharField()
    entries = serializers.ListField(child=EntryImportEntriesSerializer())

    def validate(self, params):
        # It runs only in the background, because it takes a long time to process.
        if self.parent:
            return params

        def _convert_value_name_to_id(attr_data, entity_attrs):
            def _object(val, refs):
                if val:
                    ref_entry = Entry.objects.filter(name=val, schema__in=refs).first()
                    return ref_entry.id if ref_entry else "0"
                return None

            def _group(val):
                if val:
                    ref_group = Group.objects.filter(name=val).first()
                    return ref_group.id if ref_group else "0"
                return None

            if entity_attrs[attr_data["name"]]["type"] & AttrTypeValue["array"]:
                if not isinstance(attr_data["value"], list):
                    return
                for i, child_value in enumerate(attr_data["value"]):
                    if entity_attrs[attr_data["name"]]["type"] & AttrTypeValue["object"]:
                        if entity_attrs[attr_data["name"]]["type"] & AttrTypeValue["named"]:
                            if not isinstance(child_value, dict):
                                return
                            attr_data["value"][i] = {
                                "name": list(child_value.keys())[0],
                                "id": _object(
                                    list(child_value.values())[0],
                                    entity_attrs[attr_data["name"]]["refs"],
                                ),
                            }
                        else:
                            attr_data["value"][i] = _object(
                                child_value, entity_attrs[attr_data["name"]]["refs"]
                            )
                    if entity_attrs[attr_data["name"]]["type"] & AttrTypeValue["group"]:
                        attr_data["value"][i] = _group(child_value)
            else:
                if entity_attrs[attr_data["name"]]["type"] & AttrTypeValue["object"]:
                    if entity_attrs[attr_data["name"]]["type"] & AttrTypeValue["named"]:
                        if not isinstance(attr_data["value"], dict):
                            return
                        attr_data["value"] = {
                            "name": list(attr_data["value"].keys())[0],
                            "id": _object(
                                list(attr_data["value"].values())[0],
                                entity_attrs[attr_data["name"]]["refs"],
                            ),
                        }
                    else:
                        attr_data["value"] = _object(
                            attr_data["value"], entity_attrs[attr_data["name"]]["refs"]
                        )
                if entity_attrs[attr_data["name"]]["type"] & AttrTypeValue["group"]:
                    attr_data["value"] = _group(attr_data["value"])

        entity: Entity = Entity.objects.filter(name=params["entity"], is_active=True).first()
        if not entity:
            return params
        entity_attrs = {
            entity_attr.name: {
                "id": entity_attr.id,
                "type": entity_attr.type,
                "refs": [x for x in entity_attr.referral.filter(is_active=True)],
            }
            for entity_attr in entity.attrs.filter(is_active=True)
        }
        for entry_data in params["entries"]:
            for attr_data in entry_data.get("attrs", []):
                if attr_data["name"] in entity_attrs.keys():
                    attr_data["id"] = entity_attrs[attr_data["name"]]["id"]
                    _convert_value_name_to_id(attr_data, entity_attrs)

        return params


class EntryImportSerializer(serializers.ListSerializer):
    child = EntryImportEntitySerializer()


class GetEntryAttrReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = ACLBase
        fields = ("id", "name")


class AttributeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="schema.name")

    class Meta:
        model = Attribute
        fields = ("id", "name")


class EntryHistoryAttributeValueSerializer(serializers.ModelSerializer):
    type = serializers.IntegerField(source="data_type")
    created_user = serializers.CharField(source="created_user.username")
    curr_value = serializers.SerializerMethodField()
    prev_value = serializers.SerializerMethodField()
    parent_attr = AttributeSerializer()

    class Meta:
        model = AttributeValue
        fields = (
            "id",
            "type",
            "created_time",
            "is_latest",
            "created_user",
            "curr_value",
            "prev_value",
            "parent_attr",
        )

    def _get_value(self, obj: AttributeValue) -> EntryAttributeValue:
        if obj.data_type == AttrTypeValue["array_string"]:
            return {"as_array_string": [x.value for x in obj.data_array.all()]}

        elif obj.data_type == AttrTypeValue["array_object"]:
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
                    if x.referral and x.referral.is_active
                    else None
                    for x in obj.data_array.all()
                ]
            }

        elif obj.data_type == AttrTypeValue["object"]:
            return {
                "as_object": {
                    "id": obj.referral.id if obj.referral else None,
                    "name": obj.referral.name if obj.referral else "",
                    "schema": {
                        "id": obj.referral.entry.schema.id,
                        "name": obj.referral.entry.schema.name,
                    },
                }
                if obj.referral and obj.referral.is_active
                else None
            }

        elif obj.data_type == AttrTypeValue["boolean"]:
            return {"as_boolean": obj.boolean}

        elif obj.data_type == AttrTypeValue["date"]:
            return {"as_string": obj.date if obj.date else None}

        elif obj.data_type == AttrTypeValue["named_object"]:
            named: Dict[str, Optional[EntryAttributeValueObject]] = {
                obj.value: {
                    "id": obj.referral.id if obj.referral else None,
                    "name": obj.referral.name if obj.referral else "",
                    "schema": {
                        "id": obj.referral.entry.schema.id,
                        "name": obj.referral.entry.schema.name,
                    },
                }
                if obj.referral and obj.referral.is_active
                else None
            }
            return {"as_named_object": named}

        elif obj.data_type == AttrTypeValue["array_named_object"]:
            array_named_object: List[
                Dict[
                    str,
                    Optional[
                        Union[
                            EntryAttributeValueObject,
                            EntryAttributeValueObjectBoolean,
                            EntryAttributeValueBoolean,
                        ]
                    ],
                ]
            ] = [
                {
                    x.value: {
                        "id": x.referral.id if x.referral else None,
                        "name": x.referral.name if x.referral else "",
                        "schema": {
                            "id": x.referral.entry.schema.id,
                            "name": x.referral.entry.schema.name,
                        },
                    }
                    if x.referral and x.referral.is_active
                    else None,
                }
                for x in obj.data_array.all()
            ]
            return {"as_array_named_object": array_named_object}

        elif obj.data_type == AttrTypeValue["group"] and obj.value:
            group = Group.objects.get(id=obj.value)
            return {
                "as_group": {
                    "id": group.id,
                    "name": group.name,
                }
            }

        elif obj.data_type == AttrTypeValue["array_group"]:
            groups = [Group.objects.get(id=x.value) for x in obj.data_array.all()]
            return {
                "as_array_group": [
                    {
                        "id": group.id,
                        "name": group.name,
                    }
                    for group in groups
                ]
            }

        elif obj.data_type == AttrTypeValue["role"] and obj.value:
            role = Role.objects.get(id=obj.value)
            return {
                "as_role": {
                    "id": role.id,
                    "name": role.name,
                }
            }

        elif obj.data_type == AttrTypeValue["array_role"]:
            roles = [Role.objects.get(id=x.value) for x in obj.data_array.all()]
            return {
                "as_array_role": [
                    {
                        "id": role.id,
                        "name": role.name,
                    }
                    for role in roles
                ]
            }

        elif obj.data_type == AttrTypeValue["string"] or obj.data_type == AttrTypeValue["text"]:
            return {"as_string": obj.value}

        return {}

    @extend_schema_field(EntryAttributeValueSerializer())
    def get_curr_value(self, obj: AttributeValue) -> EntryAttributeValue:
        return self._get_value(obj)

    @extend_schema_field(EntryAttributeValueSerializer())
    def get_prev_value(self, obj: AttributeValue) -> Optional[EntryAttributeValue]:
        prev_value = obj.get_preview_value()
        if prev_value:
            return self._get_value(prev_value)
        return None


class EntryAttributeValueRestoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = []

    def create(self, validated_data):
        raise ValidationError("unsupported")

    def update(self, instance: AttributeValue, validated_data):
        if not self.partial:
            raise ValidationError("only partial update is supported")

        attr = instance.parent_attr
        entry = attr.parent_entry
        user: User = self.context["request"].user

        # skip for unpermitted attributes
        if not user.has_permission(attr, ACLType.Writable):
            raise ValidationError(
                "user ({}) is not permitted for the recovery operation", user.username
            )

        attr.add_value(user, instance.value)
        entry.register_es()

        # running job to notify changing entry event
        job_notify_event: Job = Job.new_notify_update_entry(user, entry)
        job_notify_event.run()

        return instance


class AdvancedSearchResultAttrInfoSerializer(serializers.Serializer):
    name = serializers.CharField()
    keyword = serializers.CharField(
        required=False, allow_blank=True, max_length=CONFIG_ENTRY.MAX_QUERY_SIZE
    )


class AdvancedSearchSerializer(serializers.Serializer):
    entities = serializers.ListField(child=serializers.IntegerField())
    entry_name = serializers.CharField(allow_blank=True, default="")
    attrinfo = AdvancedSearchResultAttrInfoSerializer(many=True)
    has_referral = serializers.BooleanField(default=False)
    referral_name = serializers.CharField(required=False, allow_blank=True)
    is_output_all = serializers.BooleanField(default=True)
    is_all_entities = serializers.BooleanField(default=False)
    entry_limit = serializers.IntegerField(default=CONFIG_ENTRY.MAX_LIST_ENTRIES)
    entry_offset = serializers.IntegerField(default=0)

    def validate_entry_name(self, entry_name: str):
        if len(entry_name) > CONFIG_ENTRY.MAX_QUERY_SIZE:
            raise ValidationError("entry_name is too long")
        return entry_name

    def validate_attrs(self, attrs: List[Dict[str, str]]):
        if any([len(attr.get("keyword", "")) > CONFIG_ENTRY.MAX_QUERY_SIZE for attr in attrs]):
            raise ValidationError("keyword(s) in attrs are too large")
        return attrs


class AdvancedSearchResultValueAttrSerializer(serializers.Serializer):
    type = serializers.IntegerField()
    value = EntryAttributeValueSerializer()
    is_readable = serializers.BooleanField()


class AdvancedSearchResultValueEntrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class AdvancedSearchResultValueReferralSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    schema = EntityAttributeTypeSerializer()


class AdvancedSearchResultValueSerializer(serializers.Serializer):
    attrs = serializers.DictField(child=AdvancedSearchResultValueAttrSerializer())
    entry = AdvancedSearchResultValueEntrySerializer()
    referrals = AdvancedSearchResultValueReferralSerializer(many=True, required=False)


class AdvancedSearchResultSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    values = AdvancedSearchResultValueSerializer(many=True)


class AdvancedSearchResultExportSerializer(serializers.Serializer):
    entities = serializers.ListField(child=serializers.IntegerField())
    attrinfo = AdvancedSearchResultAttrInfoSerializer(many=True)
    has_referral = serializers.BooleanField(required=False)
    referral_name = serializers.CharField(required=False)
    entry_name = serializers.CharField(
        required=False, allow_blank=True, max_length=CONFIG_ENTRY.MAX_QUERY_SIZE
    )
    export_style = serializers.CharField()

    def validate_entities(self, entities: List[int]):
        if Entity.objects.filter(id__in=entities).count() != len(entities):
            raise ValidationError("any entity_id(s) refers to an invalid entity")
        return entities

    def validate_export_style(self, export_style: str):
        if export_style != "yaml" and export_style != "csv":
            raise ValidationError("format must be yaml or csv")
        return export_style

    def save(self, **kwargs):
        user: User = self.context["request"].user

        job_status_not_finished = [Job.STATUS["PREPARING"], Job.STATUS["PROCESSING"]]
        if (
            Job.get_job_with_params(user, self.validated_data)
            .filter(status__in=job_status_not_finished)
            .exists()
        ):
            raise ValidationError("Same export processing is under execution")

        # create a job to export search result and run it
        job = Job.new_export_search_result(
            user,
            **{
                "text": "search_results.%s" % self.validated_data["export_style"],
                "params": self.validated_data,
            },
        )
        job.run()
