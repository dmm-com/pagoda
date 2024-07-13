from datetime import date, datetime
from typing import Any, Literal

from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from pydantic import BaseModel
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from typing_extensions import TypedDict

from acl.models import ACLBase
from airone.lib import custom_view, drf
from airone.lib.acl import ACLType
from airone.lib.drf import (
    DuplicatedObjectExistsError,
    IncorrectTypeError,
    InvalidValueError,
    ObjectNotExistsError,
    RequiredParameterError,
)
from airone.lib.elasticsearch import FilterKey
from airone.lib.log import Logger
from airone.lib.types import AttrDefaultValue, AttrType
from entity.api_v2.serializers import EntitySerializer
from entity.models import Entity, EntityAttr
from entry.models import Attribute, AttributeValue, Entry
from entry.settings import CONFIG as CONFIG_ENTRY
from group.models import Group
from job.models import Job, JobStatus
from role.models import Role
from user.api_v2.serializers import UserBaseSerializer
from user.models import User


class ExportedEntryAttributeValueObject(BaseModel):
    entity: str
    name: str


ExportedEntryAttributePrimitiveValue = (
    str  # includes text, string, group, role
    | date
    | datetime
    | bool
    | ExportedEntryAttributeValueObject
    | dict[str, ExportedEntryAttributeValueObject]  # named entry for yaml export
    | dict[str, str]  # named entry for csv export
    | dict[str, None]
    | None
)

ExportedEntryAttributeValue = (
    ExportedEntryAttributePrimitiveValue | list[ExportedEntryAttributePrimitiveValue]
)


class ExportedEntryAttribute(BaseModel):
    name: str
    value: ExportedEntryAttributeValue


class ReferralEntry(BaseModel):
    entity: str
    entry: str


class ExportedEntry(BaseModel):
    name: str
    attrs: list[ExportedEntryAttribute]
    referrals: list[ReferralEntry] | None = None


class ExportedEntityEntries(BaseModel):
    entity: str
    entries: list[ExportedEntry]


class ExportTaskParams(BaseModel):
    export_format: Literal["yaml", "csv"]
    target_id: int


class EntityAttributeType(TypedDict):
    id: int
    name: str


class EntryAttributeValueObject(TypedDict):
    id: int
    name: str
    schema: EntityAttributeType


class EntryAttributeValueNamedObject(TypedDict):
    name: str
    object: EntryAttributeValueObject | None


class EntryAttributeValueNamedObjectBoolean(EntryAttributeValueNamedObject):
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
    as_object: EntryAttributeValueObject | None
    as_string: str
    as_named_object: EntryAttributeValueNamedObject
    as_array_object: list[EntryAttributeValueObject | None]
    as_array_string: list[str]
    as_array_named_object: list[EntryAttributeValueNamedObject]
    as_array_group: list[EntryAttributeValueGroup]
    # text; use string instead
    as_boolean: bool
    as_group: EntryAttributeValueGroup | None
    # date; use string instead
    as_role: EntryAttributeValueRole | None
    as_array_role: list[EntryAttributeValueRole]


class EntryAttributeType(TypedDict):
    id: int | None
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


class EntryAttributeValueNamedObjectSerializer(serializers.Serializer):
    name = serializers.CharField()
    object = EntryAttributeValueObjectSerializer(allow_null=True)


class EntryAttributeValueNamedObjectBooleanSerializer(EntryAttributeValueNamedObjectSerializer):
    name = serializers.CharField()
    object = EntryAttributeValueObjectSerializer(allow_null=True)
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
    as_named_object = EntryAttributeValueNamedObjectSerializer(required=False)
    as_array_object = serializers.ListField(
        child=EntryAttributeValueObjectSerializer(allow_null=True), required=False
    )
    as_array_string = serializers.ListField(child=serializers.CharField(), required=False)
    as_array_named_object = serializers.ListField(
        child=EntryAttributeValueNamedObjectBooleanSerializer(),
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
    @extend_schema_field(
        {
            "type": "integer",
            "enum": [k.value for k in AttrType],
            "x-enum-varnames": [k.name for k in AttrType],
        }
    )
    class AttrTypeField(serializers.IntegerField):
        pass

    id = serializers.IntegerField(allow_null=True)
    type = AttrTypeField()
    is_mandatory = serializers.BooleanField()
    is_readable = serializers.BooleanField()
    value = EntryAttributeValueSerializer()
    schema = EntityAttributeTypeSerializer()


class EntryBaseSerializer(serializers.ModelSerializer):
    # This attribute toggle privileged mode that allow user to CRUD Entry without
    # considering permission. This must not change from program, but declare in a
    # serializer.
    privileged_mode = False

    schema = EntitySerializer(read_only=True)
    deleted_user = UserBaseSerializer(read_only=True, allow_null=True)

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
        if "\t" in name:
            raise InvalidValueError("Names containing tab characters cannot be specified.")
        return name

    def _validate(self, schema: Entity, name: str, attrs: list[dict[str, Any]]):
        user: User | None = None
        if "request" in self.context:
            user = self.context["request"].user
        if "_user" in self.context:
            user = self.context["_user"]

        # In create case, check attrs mandatory attribute
        if not self.instance:
            if user is None:
                raise RequiredParameterError("user is required")

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

        # check custom validate
        if custom_view.is_custom("validate_entry", schema.name):
            custom_view.call_custom("validate_entry", schema.name, user, schema.name, name, attrs)


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
    attrs: list[AttributeDataSerializer]
    created_user: User


@extend_schema_serializer(exclude_fields=["schema"])
class EntryCreateSerializer(EntryBaseSerializer):
    schema = serializers.PrimaryKeyRelatedField(
        queryset=Entity.objects.all(), write_only=True, required=True
    )
    attrs = serializers.ListField(child=AttributeDataSerializer(), write_only=True, required=False)
    created_user = serializers.HiddenField(default=drf.AironeUserDefault())

    class Meta:
        model = Entry
        fields = ["id", "name", "schema", "attrs", "created_user"]

    def validate(self, params):
        self._validate(params["schema"], params["name"], params.get("attrs", []))
        return params

    def create(self, validated_data: EntryCreateData):
        user: User | None = None
        if "request" in self.context:
            user = self.context["request"].user
        if "_user" in self.context:
            user = self.context["_user"]
        if user is None:
            raise RequiredParameterError("user is required")

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
            if not self.privileged_mode and not user.has_permission(attr, ACLType.Writable):
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

        # run task that may run TriggerAction in response to TriggerCondition configuration
        Job.new_invoke_trigger(user, entry, attrs_data).run()

        # clear flag to specify this entry has been completed to create
        entry.del_status(Entry.STATUS_CREATING)

        # Send notification to the webhook URL
        job_notify_event: Job = Job.new_notify_create_entry(user, entry)
        job_notify_event.run()

        return entry


class PrivilegedEntryCreateSerializer(EntryCreateSerializer):
    privileged_mode = True


class EntryUpdateData(TypedDict, total=False):
    name: str
    attrs: list[AttributeDataSerializer]
    delay_trigger: bool
    call_stacks: list[int]


class EntryUpdateSerializer(EntryBaseSerializer):
    attrs = serializers.ListField(child=AttributeDataSerializer(), write_only=True, required=False)

    # These parameters are only used to run TriggerActions
    delay_trigger = serializers.BooleanField(required=False, default=True)
    # This will contain EntityAttr IDs that have already been updated in this TriggerAction
    # running chain.
    call_stacks = serializers.ListField(child=serializers.IntegerField(), required=False)

    class Meta:
        model = Entry
        fields = ["id", "name", "attrs", "delay_trigger", "call_stacks"]
        extra_kwargs = {
            "name": {"required": False},
        }

    def validate(self, params):
        self._validate(
            self.instance.schema, params.get("name", self.instance.name), params.get("attrs", [])
        )
        return params

    def update(self, entry: Entry, validated_data: EntryUpdateData):
        entry.set_status(Entry.STATUS_EDITING)

        user: User | None = None
        if "request" in self.context:
            user = self.context["request"].user
        if "_user" in self.context:
            user = self.context["_user"]
        if user is None:
            raise RequiredParameterError("user is required")

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
        job_register_referrals: Job | None = None
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
            if not self.privileged_mode and not user.has_permission(attr, ACLType.Writable):
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

        # run task that may run TriggerAction in response to TriggerCondition configuration
        if validated_data["delay_trigger"]:
            Job.new_invoke_trigger(user, entry, attrs_data).run()
        else:
            # This declaration prevents circular reference because TriggerAction module
            # imports this module indirectly. And this might affect little negative affect
            # because Python interpreter will cache imported module once it's imported.
            from trigger.models import TriggerCondition

            # run TriggerActions immediately if it's necessary
            for action in TriggerCondition.get_invoked_actions(entry.schema, attrs_data):
                action.run(user, entry, validated_data["call_stacks"])

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


class PrivilegedEntryUpdateSerializer(EntryUpdateSerializer):
    privileged_mode = True


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
    def get_attrs(self, obj: Entry) -> list[EntryAttributeType]:
        def get_attr_value(attr: Attribute) -> EntryAttributeValue:
            attrv = attr.get_latest_value(is_readonly=True)

            if not attrv:
                return {}

            try:
                attr_type = AttrType(attr.schema.type)
            except ValueError:
                Logger.error("Invalid attribute type: %s" % attr.schema.type)
                return {}

            match attr_type:
                case AttrType.ARRAY_STRING:
                    return {
                        "as_array_string": [x.value for x in attrv.data_array.all()],
                    }

                case AttrType.ARRAY_OBJECT:
                    return {
                        "as_array_object": [
                            {
                                "id": x.referral.id if x.referral else 0,
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

                case AttrType.ARRAY_NAMED_OBJECT:
                    array_named_object: list[EntryAttributeValueNamedObject] = [
                        {
                            "name": x.value,
                            "object": {
                                "id": x.referral.id if x.referral else 0,
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
                        if not (x.referral and not x.referral.is_active)
                    ]
                    return {"as_array_named_object": array_named_object}

                case AttrType.ARRAY_GROUP:
                    groups = [v.group for v in attrv.data_array.all().select_related("group")]
                    return {
                        "as_array_group": [
                            {
                                "id": group.id,
                                "name": group.name,
                            }
                            for group in groups
                        ]
                    }

                case AttrType.ARRAY_ROLE:
                    roles = [v.role for v in attrv.data_array.all().select_related("role")]
                    return {
                        "as_array_role": [
                            {
                                "id": role.id,
                                "name": role.name,
                            }
                            for role in roles
                        ]
                    }

                case AttrType.STRING | AttrType.TEXT:
                    return {"as_string": attrv.value}

                case AttrType.OBJECT:
                    return {
                        "as_object": {
                            "id": attrv.referral.id if attrv.referral else 0,
                            "name": attrv.referral.name if attrv.referral else "",
                            "schema": {
                                "id": attrv.referral.entry.schema.id,
                                "name": attrv.referral.entry.schema.name,
                            },
                        }
                        if attrv.referral and attrv.referral.is_active
                        else None,
                    }

                case AttrType.NAMED_OBJECT:
                    named: EntryAttributeValueNamedObject = {
                        "name": attrv.value,
                        "object": {
                            "id": attrv.referral.id if attrv.referral else 0,
                            "name": attrv.referral.name if attrv.referral else "",
                            "schema": {
                                "id": attrv.referral.entry.schema.id,
                                "name": attrv.referral.entry.schema.name,
                            },
                        }
                        if attrv.referral and attrv.referral.is_active
                        else None,
                    }
                    return {"as_named_object": named}

                case AttrType.BOOLEAN:
                    return {"as_boolean": attrv.boolean}

                case AttrType.DATE:
                    return {"as_string": attrv.date if attrv.date else ""}

                case AttrType.GROUP if attrv.group:
                    return {
                        "as_group": {
                            "id": attrv.group.id,
                            "name": attrv.group.name,
                        }
                    }

                case AttrType.ROLE if attrv.role:
                    return {
                        "as_role": {
                            "id": attrv.role.id,
                            "name": attrv.role.name,
                        }
                    }

                case AttrType.DATETIME:
                    return {"as_string": attrv.datetime if attrv.datetime else ""}

                case _:
                    return {}

        def get_default_attr_value(type: int) -> EntryAttributeValue:
            try:
                attr_type = AttrType(type)
            except ValueError:
                raise IncorrectTypeError(f"unexpected type: {type}")

            match attr_type:
                case AttrType.ARRAY_STRING:
                    return {
                        "as_array_string": AttrDefaultValue[type],
                    }

                case AttrType.ARRAY_NAMED_OBJECT:
                    return {"as_array_named_object": []}

                case AttrType.ARRAY_OBJECT:
                    return {"as_array_object": AttrDefaultValue[type]}

                case AttrType.ARRAY_GROUP:
                    return {"as_array_group": AttrDefaultValue[type]}

                case AttrType.ARRAY_ROLE:
                    return {"as_array_role": AttrDefaultValue[type]}

                case AttrType.STRING | AttrType.TEXT:
                    return {"as_string": AttrDefaultValue[type]}

                case AttrType.OBJECT:
                    return {"as_object": AttrDefaultValue[type]}

                case AttrType.NAMED_OBJECT:
                    return {"as_named_object": {"name": "", "object": None}}

                case AttrType.BOOLEAN:
                    return {"as_boolean": AttrDefaultValue[type]}

                case AttrType.DATE:
                    return {"as_string": AttrDefaultValue[type]}

                case AttrType.GROUP:
                    return {"as_group": AttrDefaultValue[type]}

                case AttrType.ROLE:
                    return {"as_role": AttrDefaultValue[type]}

                case AttrType.DATETIME:
                    return {"as_string": AttrDefaultValue[type]}

                case _:
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

        attrinfo: list[EntryAttributeType] = []
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

    def validate_copy_entry_names(self, copy_entry_names: list[str]):
        entry: Entry = self.instance
        duplicated_entries = Entry.objects.filter(
            name__in=copy_entry_names, schema=entry.schema, is_active=True
        )
        if duplicated_entries.exists():
            raise DuplicatedObjectExistsError(
                "specified names(%s) already exists"
                % ",".join([e.name for e in duplicated_entries])
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

    def validate(self, params: dict):
        # It runs only in the background, because it takes a long time to process.
        if self.parent:
            return params

        def _convert_value_name_to_id(attr_data: dict, entity_attrs: dict):
            def _object(
                val: str | dict | None,
                refs: list[Entity],
            ) -> int | None:
                if val:
                    # for compatibility;
                    # it will pick wrong entry if there are multiple entries with same name
                    if isinstance(val, str):
                        if len(refs) >= 2:
                            Logger.warn(
                                "ambiguous object given: entry name(%s), entity names(%s)",
                                val,
                                [x.name for x in refs],
                            )
                        ref_entry: Entry | None = Entry.objects.filter(
                            name=val, schema__in=refs
                        ).first()
                        return ref_entry.id if ref_entry else 0
                    # fully qualified entry, safer than above
                    if isinstance(val, dict):
                        ref_entry = Entry.objects.filter(
                            name=val["name"], schema__name=val["entity"]
                        ).first()
                        return ref_entry.id if ref_entry else 0
                return None

            def _group(val: str) -> int | None:
                if val:
                    ref_group: Group | None = Group.objects.filter(name=val).first()
                    return ref_group.id if ref_group else 0
                return None

            def _role(val: str) -> int | None:
                if val:
                    ref_role: Role | None = Role.objects.filter(name=val).first()
                    return ref_role.id if ref_role else 0
                return None

            if entity_attrs[attr_data["name"]]["type"] & AttrType._ARRAY:
                if not isinstance(attr_data["value"], list):
                    return
                for i, child_value in enumerate(attr_data["value"]):
                    if entity_attrs[attr_data["name"]]["type"] & AttrType.OBJECT:
                        if entity_attrs[attr_data["name"]]["type"] & AttrType._NAMED:
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
                    if entity_attrs[attr_data["name"]]["type"] & AttrType.GROUP:
                        attr_data["value"][i] = _group(child_value)

                    if entity_attrs[attr_data["name"]]["type"] & AttrType.ROLE:
                        attr_data["value"][i] = _role(child_value)
            else:
                if entity_attrs[attr_data["name"]]["type"] & AttrType.OBJECT:
                    if entity_attrs[attr_data["name"]]["type"] & AttrType._NAMED:
                        if not isinstance(attr_data["value"], dict):
                            return
                        attr_data["value"] = (
                            {
                                "name": list(attr_data["value"].keys())[0],
                                "id": _object(
                                    list(attr_data["value"].values())[0],
                                    entity_attrs[attr_data["name"]]["refs"],
                                ),
                            }
                            if len(attr_data["value"].keys()) > 0
                            else {}
                        )
                    else:
                        attr_data["value"] = _object(
                            attr_data["value"], entity_attrs[attr_data["name"]]["refs"]
                        )
                if entity_attrs[attr_data["name"]]["type"] & AttrType.GROUP:
                    attr_data["value"] = _group(attr_data["value"])
                if entity_attrs[attr_data["name"]]["type"] & AttrType.ROLE:
                    attr_data["value"] = _role(attr_data["value"])

        entity: Entity | None = Entity.objects.filter(name=params["entity"], is_active=True).first()
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
    prev_id = serializers.SerializerMethodField()
    parent_attr = AttributeSerializer()

    class Meta:
        model = AttributeValue
        fields = (
            "id",
            "type",
            "created_time",
            "created_user",
            "curr_value",
            "prev_value",
            "prev_id",
            "parent_attr",
        )

    def _get_value(self, obj: AttributeValue) -> EntryAttributeValue:
        try:
            attr_type = AttrType(obj.data_type)
        except ValueError:
            Logger.error("Invalid attribute type: %s" % obj.data_type)
            return {}

        match attr_type:
            case AttrType.ARRAY_STRING:
                return {"as_array_string": [x.value for x in obj.data_array.all()]}

            case AttrType.ARRAY_OBJECT:
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

            case AttrType.ARRAY_NAMED_OBJECT:
                array_named_object: list[EntryAttributeValueNamedObject] = [
                    {
                        "name": x.value,
                        "object": {
                            "id": x.referral.id if x.referral else 0,
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

            case AttrType.ARRAY_GROUP:
                groups = [v.group for v in obj.data_array.all().select_related("group")]
                return {
                    "as_array_group": [
                        {
                            "id": group.id,
                            "name": group.name,
                        }
                        for group in groups
                    ]
                }

            case AttrType.ARRAY_ROLE:
                roles = [v.role for v in obj.data_array.all().select_related("role")]
                return {
                    "as_array_role": [
                        {
                            "id": role.id,
                            "name": role.name,
                        }
                        for role in roles
                    ]
                }

            case AttrType.STRING | AttrType.TEXT:
                return {"as_string": obj.value}

            case AttrType.BOOLEAN:
                return {"as_boolean": obj.boolean}

            case AttrType.DATE:
                return {"as_string": obj.date if obj.date else ""}

            case AttrType.OBJECT:
                return {
                    "as_object": {
                        "id": obj.referral.id if obj.referral else 0,
                        "name": obj.referral.name if obj.referral else "",
                        "schema": {
                            "id": obj.referral.entry.schema.id,
                            "name": obj.referral.entry.schema.name,
                        },
                    }
                    if obj.referral and obj.referral.is_active
                    else None,
                }

            case AttrType.NAMED_OBJECT:
                named: EntryAttributeValueNamedObject = {
                    "name": obj.value,
                    "object": {
                        "id": obj.referral.id if obj.referral else 0,
                        "name": obj.referral.name if obj.referral else "",
                        "schema": {
                            "id": obj.referral.entry.schema.id,
                            "name": obj.referral.entry.schema.name,
                        },
                    }
                    if obj.referral and obj.referral.is_active
                    else None,
                }
                return {"as_named_object": named}

            case AttrType.GROUP:
                group = obj.group
                return {
                    "as_group": {
                        "id": group.id,
                        "name": group.name,
                    }
                    if group
                    else None
                }

            case AttrType.ROLE:
                role = obj.role
                return {
                    "as_role": {
                        "id": role.id,
                        "name": role.name,
                    }
                    if role
                    else None
                }

            case AttrType.DATETIME:
                return {"as_string": obj.datetime if obj.datetime else ""}

            case _:
                return {}

    @extend_schema_field(EntryAttributeValueSerializer())
    def get_curr_value(self, obj: AttributeValue) -> EntryAttributeValue:
        return self._get_value(obj)

    @extend_schema_field(EntryAttributeValueSerializer())
    def get_prev_value(self, obj: AttributeValue) -> EntryAttributeValue | None:
        prev_value = obj.get_preview_value()
        if prev_value:
            return self._get_value(prev_value)
        return None

    def get_prev_id(self, obj: AttributeValue) -> int | None:
        prev_value = obj.get_preview_value()
        if prev_value:
            return prev_value.id
        return None


class EntryAttributeValueRestoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = []

    def create(self, validated_data):
        raise ValidationError("unsupported")

    def update(self, instance: AttributeValue, validated_data) -> AttributeValue:
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
    @extend_schema_field(
        {
            "type": "integer",
            "enum": [k.value for k in FilterKey],
            "x-enum-varnames": [k.name for k in FilterKey],
        }
    )
    class FilterKeyField(serializers.IntegerField):
        pass

    name = serializers.CharField()
    filter_key = FilterKeyField(required=False)
    keyword = serializers.CharField(
        required=False, allow_blank=True, max_length=CONFIG_ENTRY.MAX_QUERY_SIZE
    )

    def validate_filter_key(self, filter_key: int):
        if filter_key not in [k.value for k in FilterKey]:
            raise ValidationError("filter key parameter is invalid value")
        return filter_key


class AdvancedSearchJoinAttrInfoSerializer(serializers.Serializer):
    name = serializers.CharField()
    offset = serializers.IntegerField(default=0)
    attrinfo = AdvancedSearchResultAttrInfoSerializer(many=True)


class AdvancedSearchSerializer(serializers.Serializer):
    entities = serializers.ListField(child=serializers.IntegerField())
    entry_name = serializers.CharField(allow_blank=True, default="")
    attrinfo = AdvancedSearchResultAttrInfoSerializer(many=True)
    join_attrs = AdvancedSearchJoinAttrInfoSerializer(many=True, required=False)
    has_referral = serializers.BooleanField(default=False)
    referral_name = serializers.CharField(required=False, allow_blank=True)
    is_output_all = serializers.BooleanField(default=True)
    is_all_entities = serializers.BooleanField(default=False)
    entry_limit = serializers.IntegerField(default=CONFIG_ENTRY.MAX_LIST_ENTRIES)
    entry_offset = serializers.IntegerField(default=0)

    def validate_entry_name(self, entry_name: str) -> str:
        if len(entry_name) > CONFIG_ENTRY.MAX_QUERY_SIZE:
            raise ValidationError("entry_name is too long")
        return entry_name

    def validate_attrs(self, attrs: list[dict[str, str]]) -> list[dict[str, str]]:
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


class AdvancedSearchResultValueEntitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class AdvancedSearchResultValueReferralSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    schema = EntityAttributeTypeSerializer()


class AdvancedSearchResultValueSerializer(serializers.Serializer):
    attrs = serializers.DictField(child=AdvancedSearchResultValueAttrSerializer())
    entry = AdvancedSearchResultValueEntrySerializer()
    entity = AdvancedSearchResultValueEntitySerializer()
    referrals = AdvancedSearchResultValueReferralSerializer(many=True, required=False)
    is_readable = serializers.BooleanField()


class AdvancedSearchResultSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    values = AdvancedSearchResultValueSerializer(many=True)
    total_count = serializers.IntegerField()


class AdvancedSearchResultExportSerializer(serializers.Serializer):
    entities = serializers.ListField(child=serializers.IntegerField())
    attrinfo = AdvancedSearchResultAttrInfoSerializer(many=True)
    has_referral = serializers.BooleanField(required=False)
    referral_name = serializers.CharField(required=False)
    entry_name = serializers.CharField(
        required=False, allow_blank=True, max_length=CONFIG_ENTRY.MAX_QUERY_SIZE
    )
    is_all_entities = serializers.BooleanField(default=False)
    export_style = serializers.CharField()

    def validate_entities(self, entities: list[int]) -> list[int]:
        if Entity.objects.filter(id__in=entities).count() != len(entities):
            raise ValidationError("any entity_id(s) refers to an invalid entity")
        return entities

    def validate_export_style(self, export_style: str) -> str:
        if export_style != "yaml" and export_style != "csv":
            raise ValidationError("format must be yaml or csv")
        return export_style

    def validate(self, params):
        if params["is_all_entities"]:
            attr_names = [x["name"] for x in params["attrinfo"]]
            params["entities"] = list(
                EntityAttr.objects.filter(
                    name__in=attr_names, is_active=True, parent_entity__is_active=True
                )
                .order_by("parent_entity__name")
                .values_list("parent_entity__id", flat=True)
                .distinct()
            )
            if not params["entities"]:
                raise ValidationError("Invalid value for attribute parameter")

        return params

    def save(self, **kwargs) -> None:
        user: User = self.context["request"].user

        job_status_not_finished: list[JobStatus] = [JobStatus.PREPARING, JobStatus.PROCESSING]
        if (
            Job.get_job_with_params(user, self.validated_data)
            .filter(status__in=job_status_not_finished)
            .exists()
        ):
            raise ValidationError("Same export processing is under execution")

        # create a job to export search result and run it
        job = Job.new_export_search_result_v2(
            user=user,
            text="search_results.%s" % self.validated_data["export_style"],
            params=self.validated_data,
        )
        job.run()
