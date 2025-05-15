import re
from collections.abc import Iterable
from datetime import date, datetime
from typing import Any, List, Optional, Type, Union

from django.conf import settings
from django.db import models
from django.db.models import Prefetch, Q, QuerySet
from simple_history.models import HistoricalRecords

from acl.models import ACLBase
from airone.lib import auto_complement
from airone.lib.acl import ACLObjType, ACLType
from airone.lib.drf import ExceedLimitError
from airone.lib.elasticsearch import (
    ESS,
    AttributeDocument,
    EntryDocument,
)
from airone.lib.types import (
    AttrDefaultValue,
    AttrType,
)
from entity.models import Entity, EntityAttr
from group.models import Group
from role.models import Role
from user.models import User

from .settings import CONFIG


class AttributeValue(models.Model):
    # This is a constant that indicates target object binds multiple AttributeValue objects.
    STATUS_DATA_ARRAY_PARENT = 1 << 0

    MAXIMUM_VALUE_SIZE = 1 << 16

    value = models.TextField()
    referral = models.ForeignKey(
        ACLBase,
        null=True,
        related_name="referred_attr_value",
        on_delete=models.SET_NULL,
    )
    created_time = models.DateTimeField(auto_now_add=True)
    created_user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    parent_attr = models.ForeignKey("Attribute", on_delete=models.DO_NOTHING)
    status = models.IntegerField(default=0)
    boolean = models.BooleanField(default=False)
    date = models.DateField(null=True)
    datetime = models.DateTimeField(null=True)
    group = models.ForeignKey(
        Group,
        null=True,
        related_name="referred_attr_value",
        on_delete=models.SET_NULL,
    )
    role = models.ForeignKey(
        Role,
        null=True,
        related_name="referred_attr_value",
        on_delete=models.SET_NULL,
    )

    # This parameter means that target AttributeValue is the latest one. This is usefull to
    # find out enabled AttributeValues by Attribute or EntityAttr object. And separating this
    # parameter from status is very meaningful to reduce query at clearing this flag (If this
    # flag is a value of status paramete, you have to send at least two query to set it down,
    # because you have to check current value by SELECT, after that you calculate new value
    # then update it).
    is_latest = models.BooleanField(default=True)

    # The reason why the 'data_type' parameter is also needed in addition to the Attribute is that
    # the value of 'type' in Attribute may be changed dynamically.
    #
    # If that value is changed after making AttributeValue, we can't know the old type of Attribute.
    # So it's necessary to save the value of AttrTypeVelue for each AttributeValue instance.
    # And this value is constract, this parameter will never be changed after creating.
    data_type = models.IntegerField(default=0)

    # This indicates the parent AttributeValue object, this parameter is usefull to identify
    # leaf AttriuteValue objects.
    parent_attrv = models.ForeignKey(
        "AttributeValue", null=True, related_name="data_array", on_delete=models.SET_NULL
    )

    @classmethod
    def get_default_value(kls, attr: "Attribute"):
        """
        Returns the default value for each attribute type.
        Used when there is no attribute value.
        """
        return AttrDefaultValue[attr.schema.type]

    def set_status(self, val: int):
        self.status |= val
        self.save(update_fields=["status"])

    def del_status(self, val: int):
        self.status &= ~val
        self.save(update_fields=["status"])

    def get_status(self, val: int):
        return self.status & val

    def clone(self, user: User, **extra_params) -> "AttributeValue":
        cloned_value = AttributeValue.objects.get(id=self.id)

        # By removing the primary key, we can clone a django model instance
        cloned_value.pk = None

        # set extra configure
        for k, v in extra_params.items():
            setattr(cloned_value, k, v)

        # update basic parameters to new one
        cloned_value.created_user = user
        cloned_value.created_time = datetime.now()
        cloned_value.save()

        cloned_value.data_array.clear()

        return cloned_value

    def get_value(
        self,
        with_metainfo: bool = False,
        with_entity: bool = False,
        serialize: bool = False,
        is_active: bool = True,
    ):
        """
        This returns registered value according to the type of Attribute
        """

        def _get_named_value(
            attrv: "AttributeValue", is_active: bool = True
        ) -> dict[str, dict[str, int | str] | None]:
            if attrv.referral and (attrv.referral.is_active or not is_active):
                if with_metainfo:
                    return {
                        attrv.value: {
                            "id": attrv.referral.id,
                            "name": attrv.referral.name,
                        }
                    }
                elif with_entity:
                    referral_entry = attrv.referral.get_subclass_object()
                    if not isinstance(referral_entry, Entry):
                        raise ValueError("object(%s) is not Entry object", attrv.referral)
                    return {
                        attrv.value: {
                            "name": attrv.referral.name,
                            "entity": referral_entry.schema.name,
                        }
                    }
                else:
                    return {attrv.value: attrv.referral.name}
            else:
                return {attrv.value: None}

        def _get_object_value(
            attrv: "AttributeValue", is_active: bool = True
        ) -> dict[str, str] | None:
            if attrv.referral and (attrv.referral.is_active or not is_active):
                if with_metainfo:
                    return {"id": attrv.referral.id, "name": attrv.referral.name}
                elif with_entity:
                    referral_entry = attrv.referral.get_subclass_object()
                    if not isinstance(referral_entry, Entry):
                        raise ValueError("object(%s) is not Entry object", attrv.referral)
                    return {
                        "name": attrv.referral.name,
                        "entity": referral_entry.schema.name,
                    }
                else:
                    return attrv.referral.name
            return None

        def _get_model_value(attrv: "AttributeValue"):
            match attrv.data_type:
                case AttrType.GROUP | AttrType.ARRAY_GROUP if attrv.group and attrv.group.is_active:
                    instance = attrv.group
                case AttrType.ROLE | AttrType.ARRAY_ROLE if attrv.role and attrv.role.is_active:
                    instance = attrv.role
                case _:
                    return None

            if with_metainfo:
                return {"id": instance.id, "name": instance.name}
            else:
                return instance.name

        value = None
        match self.parent_attr.schema.type:
            case AttrType.STRING | AttrType.TEXT:
                value = self.value

            case AttrType.BOOLEAN:
                value = self.boolean

            case AttrType.DATE:
                if serialize:
                    value = str(self.date)
                else:
                    value = self.date

            case AttrType.OBJECT:
                value = _get_object_value(self, is_active)

            case AttrType.NAMED_OBJECT:
                value = _get_named_value(self, is_active)

            case AttrType.GROUP if self.group:
                value = _get_model_value(self)

            case AttrType.ROLE if self.role:
                value = _get_model_value(self)

            case AttrType.DATETIME:
                if serialize:
                    if self.datetime:
                        value = self.datetime.isoformat()
                    else:
                        value = None
                else:
                    value = self.datetime

            case AttrType.ARRAY_NAMED_OBJECT | AttrType.ARRAY_NAMED_OBJECT_BOOLEAN:
                value = [_get_named_value(x, is_active) for x in self.data_array.all()]

            case AttrType.ARRAY_STRING:
                value = [x.value for x in self.data_array.all()]

            case AttrType.ARRAY_OBJECT:
                value = [
                    _get_object_value(x, is_active) for x in self.data_array.all() if x.referral
                ]
            case AttrType.ARRAY_GROUP:
                value = [
                    x
                    for x in [
                        _get_model_value(y) for y in self.data_array.all().select_related("group")
                    ]
                    if x
                ]
            case AttrType.ARRAY_ROLE:
                value = [
                    x
                    for x in [
                        _get_model_value(y) for y in self.data_array.all().select_related("role")
                    ]
                    if x
                ]

        if with_metainfo:
            value = {"type": self.parent_attr.schema.type, "value": value}

        return value

    def format_for_history(self):
        match self.data_type:
            case AttrType.ARRAY_STRING:
                return [x.value for x in self.data_array.all()]
            case AttrType.ARRAY_OBJECT:
                return [x.referral for x in self.data_array.all()]
            case AttrType.OBJECT:
                return self.referral
            case AttrType.BOOLEAN:
                return self.boolean
            case AttrType.DATE:
                return self.date
            case AttrType.NAMED_OBJECT:
                return {
                    "value": self.value,
                    "referral": self.referral,
                }
            case AttrType.ARRAY_NAMED_OBJECT:
                return sorted(
                    [
                        {
                            "value": x.value,
                            "referral": x.referral,
                        }
                        for x in self.data_array.all()
                    ],
                    key=lambda x: x["value"],
                )
            case AttrType.GROUP if self.group:
                return self.group
            case AttrType.ARRAY_GROUP:
                return [
                    y for y in [x.group for x in self.data_array.all().select_related("group")] if y
                ]
            case AttrType.ROLE if self.role:
                return self.role
            case AttrType.ARRAY_ROLE:
                return [
                    y for y in [x.role for x in self.data_array.all().select_related("role")] if y
                ]
            case AttrType.DATETIME:
                return self.datetime
            case _:
                return self.value

    def get_next_value(self) -> Optional["AttributeValue"]:
        attrv = AttributeValue.objects.filter(
            parent_attr=self.parent_attr, parent_attrv__isnull=True
        )
        return attrv.filter(created_time__gt=self.created_time).order_by("created_time").first()

    def get_preview_value(self) -> Optional["AttributeValue"]:
        attrv = AttributeValue.objects.filter(
            parent_attr=self.parent_attr, parent_attrv__isnull=True
        )
        return attrv.filter(created_time__lt=self.created_time).order_by("created_time").last()

    @classmethod
    def search(kls, query: str) -> list[dict[str, Any]]:
        results = []
        for obj in kls.objects.filter(value__icontains=query):
            attr = obj.parent_attr
            entry = attr.parent_entry

            results.append(
                {
                    "type": entry.__class__.__name__,
                    "object": entry,
                    "hint": "attribute '%s' has '%s'" % (attr.name, obj.value),
                }
            )

        return results

    @classmethod
    def create(kls, user: User, attr: "AttributeValue", **params):
        return kls.objects.create(
            created_user=user, parent_attr=attr, data_type=attr.schema.type, **params
        )

    # These are helper methods that changes input value to storable value for each
    # data type (e.g. case group type, this allows Group instance and int and str
    # value that indicate specific group instance, and it returns id of its instance)
    @classmethod
    def uniform_storable(kls, val: Group | Role | str | int, model: Type[Group | Role]) -> str:
        """
        This converts input to group id value(str) to be able to store at AttributeValue.
        And this expects input value as Group type instance, int value that indicate
        ID of specific Group instance and name(str) value of specific Group instance.
        """
        obj = None
        match val:
            case Group() | Role() as instance if instance.is_active:
                obj = instance
            case str():
                if val.isdigit():
                    obj = model.objects.filter(id=val, is_active=True).first()
                else:
                    obj = model.objects.filter(name=val, is_active=True).first()
            case int():
                obj = model.objects.filter(id=val, is_active=True).first()

        # when value is invalid value (e.g. False, empty string) set 0
        # not to cause ValueError exception at other retrieval processing.
        return str(obj.id) if obj else ""

    @classmethod
    def validate_attr_value(
        kls, type: int, input_value: Any, is_mandatory: bool
    ) -> tuple[bool, str | None]:
        """
        Validate if to add_value is a possible value.
        Returns: (is_valid, msg)
            is_valid(bool): result of validate
            msg(str): error message(Optional)
        """

        def _is_validate_attr_str(value: str) -> bool:
            if not isinstance(value, str):
                raise Exception("value(%s) is not str" % value)
            if len(str(value).encode("utf-8")) > AttributeValue.MAXIMUM_VALUE_SIZE:
                raise ExceedLimitError("value is exceeded the limit")
            if is_mandatory and value == "":
                return False
            return True

        def _is_validate_attr_object(value: int | str) -> bool:
            try:
                if isinstance(value, Entry) and value.is_active:
                    return True
                if (
                    isinstance(value, ACLBase)
                    and Entry.objects.filter(id=value.id, is_active=True).exists()
                ):
                    raise Exception("value(%s) is not valid entry" % value.name)
                if value and not Entry.objects.filter(id=value, is_active=True).exists():
                    raise Exception("value(%s) is not entry id" % value)
                if is_mandatory and not value:
                    return False
                return True
            except (ValueError, TypeError):
                raise Exception("value(%s) is not int" % value)

        def _is_validate_attr(t: int, value) -> bool:
            match t:
                case AttrType.STRING | AttrType.TEXT:
                    return _is_validate_attr_str(value)

                case AttrType.OBJECT:
                    return _is_validate_attr_object(value)

                case AttrType.NAMED_OBJECT:
                    if value:
                        if not isinstance(value, dict):
                            raise Exception("value(%s) is not dict" % value)
                        if not ("name" in value.keys() and "id" in value.keys()):
                            raise Exception("value(%s) is not key('name', 'id')" % value)
                        if not any(
                            [
                                _is_validate_attr_str(value["name"]),
                                _is_validate_attr_object(value["id"]),
                            ]
                        ):
                            return False
                    elif is_mandatory:
                        return False

                case AttrType.GROUP:
                    try:
                        if value and not Group.objects.filter(id=value, is_active=True).exists():
                            raise Exception("value(%s) is not group id" % value)
                        if is_mandatory and not value:
                            return False
                    except (ValueError, TypeError):
                        raise Exception("value(%s) is not int" % value)

                case AttrType.BOOLEAN:
                    if not isinstance(value, bool):
                        raise Exception("value(%s) is not bool" % value)

                case AttrType.DATE:
                    try:
                        if value:
                            datetime.strptime(value, "%Y-%m-%d").date()
                        elif is_mandatory:
                            return False
                    except (ValueError, TypeError):
                        raise Exception("value(%s) is not format(YYYY-MM-DD)" % value)

                case AttrType.ROLE:
                    try:
                        if value and (
                            (
                                isinstance(value, int)
                                and not Role.objects.filter(id=value, is_active=True).exists()
                            )
                            or (
                                isinstance(value, str)
                                and not Role.objects.filter(name=value, is_active=True).exists()
                            )
                        ):
                            raise Exception("value(%s) is not Role id" % value)

                        if is_mandatory and not value:
                            return False
                    except (ValueError, TypeError):
                        raise Exception("value(%s) is not int" % value)

                case AttrType.DATETIME:
                    try:
                        if value:
                            datetime.fromisoformat(value)
                        elif is_mandatory:
                            return False
                    except (ValueError, TypeError):
                        raise Exception("value(%s) is not ISO8601 format" % value)

            return True

        try:
            if type & AttrType._ARRAY:
                if not isinstance(input_value, list):
                    raise Exception("value(%s) is not list" % input_value)
                if is_mandatory and input_value == []:
                    raise Exception("mandatory attrs value is not specified")
                _is_mandatory = False
                for val in input_value:
                    if _is_validate_attr(type & ~AttrType._ARRAY, val):
                        _is_mandatory = True
                if is_mandatory and not _is_mandatory:
                    raise Exception("mandatory attrs value is not specified")
            else:
                if not _is_validate_attr(type, input_value):
                    raise Exception("mandatory attrs value is not specified")
        except ExceedLimitError as e:
            raise (e)

        except Exception as e:
            return (False, str(e))

        return (True, None)

    @property
    def is_array(self):
        return self.parent_attr.is_array()

    @property
    def ref_item(self):
        if self.referral is not None and self.referral.is_active:
            return self.referral.entry


class Attribute(ACLBase):
    values = models.ManyToManyField(AttributeValue)

    # This parameter is needed to make a relationship with corresponding EntityAttr
    schema = models.ForeignKey(EntityAttr, on_delete=models.DO_NOTHING)
    parent_entry = models.ForeignKey("Entry", related_name="attrs", on_delete=models.DO_NOTHING)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["parent_entry", "schema"], name="unique_attribute")
        ]

    def __init__(self, *args, **kwargs):
        super(Attribute, self).__init__(*args, **kwargs)
        self.objtype = ACLObjType.EntryAttr

    def is_array(self) -> bool:
        return self.schema.type & AttrType._ARRAY

    # This checks whether each specified attribute needs to update
    def is_updated(self, recv_value) -> bool:
        # the case new attribute-value is specified
        if not self.values.exists():
            # the result depends on the specified value
            if isinstance(recv_value, bool):
                # the case that first value is 'False' at the boolean typed parameter
                return True
            else:
                return recv_value

        last_value = self.values.last()
        match self.schema.type:
            case AttrType.STRING | AttrType.TEXT:
                # the case that specified value is empty or invalid
                if not recv_value:
                    # Value would be changed as empty when there is valid value
                    # in the latest AttributeValue
                    return last_value.value
                else:
                    return last_value.value != recv_value

            case AttrType.OBJECT:
                # formalize recv_value type
                if isinstance(recv_value, Entry):
                    recv_value = recv_value.id
                elif recv_value and isinstance(recv_value, str):
                    recv_value = int(recv_value)

                if not last_value.referral and not recv_value:
                    return False
                elif last_value.referral and not recv_value:
                    return True
                elif not last_value.referral and recv_value:
                    return True
                elif last_value.referral.id != recv_value:
                    return True

            case AttrType.ARRAY_STRING:
                # the case that specified value is empty or invalid
                if not recv_value:
                    # Value would be changed as empty when there are any values
                    # in the latest AttributeValue
                    return last_value.data_array.count() > 0

                # the case of changing value
                if last_value.data_array.count() != len(recv_value):
                    return True
                # the case of appending or deleting
                for value in recv_value:
                    if not last_value.data_array.filter(value=value).exists():
                        return True

            case AttrType.ARRAY_OBJECT:
                # the case that specified value is empty or invalid
                if not recv_value:
                    # Value would be changed as empty when there are any values
                    # in the latest AttributeValue
                    return last_value.data_array.count() > 0

                # the case of changing value
                if last_value.data_array.count() != len(recv_value):
                    return True

                # the case of appending or deleting
                for value in recv_value:
                    # formalize value type
                    try:
                        if isinstance(value, Entry):
                            entry_id = value.id
                        elif not value:
                            entry_id = 0
                        else:
                            entry_id = int(value)

                    except ValueError:
                        # When user specify an invalid value (e.g. ""), ValueError will be occcured
                        entry_id = 0

                    if not last_value.data_array.filter(referral__id=entry_id).exists():
                        return True

            case AttrType.BOOLEAN:
                return last_value.boolean != bool(recv_value)

            case AttrType.GROUP:
                last_group_id = str(last_value.group.id) if last_value.group else ""
                return last_group_id != AttributeValue.uniform_storable(recv_value, Group)

            case AttrType.ROLE:
                last_role_id = str(last_value.role.id) if last_value.role else ""
                return last_role_id != AttributeValue.uniform_storable(recv_value, Role)

            case AttrType.DATE:
                if isinstance(recv_value, str):
                    try:
                        return last_value.date != datetime.strptime(recv_value, "%Y-%m-%d").date()
                    except ValueError:
                        return last_value.date is not None

                return last_value.date != recv_value

            case AttrType.DATETIME:
                if isinstance(recv_value, str):
                    try:
                        return last_value.datetime != datetime.fromisoformat(recv_value)
                    except ValueError:
                        return last_value.datetime is not None

                return last_value.datetime != recv_value

            case AttrType.NAMED_OBJECT:
                # the case that specified value is empty or invalid
                if not recv_value:
                    # Value would be changed as empty when there is valid value
                    # in the latest AttributeValue
                    return last_value.value or (
                        last_value.referral and last_value.referral.is_active
                    )

                if last_value.value != recv_value["name"]:
                    return True

                # formalize recv_value['id'] type
                if isinstance(recv_value["id"], Entry):
                    recv_value["id"] = recv_value["id"].id

                if not last_value.referral and recv_value["id"]:
                    return True

                if (
                    last_value.referral
                    and recv_value["id"]
                    and last_value.referral.id != int(recv_value["id"])
                ):
                    return True

            case AttrType.ARRAY_NAMED_OBJECT:

                def get_entry_id(value: int | str | Entry | None) -> int | None:
                    if not value:
                        return None
                    if isinstance(value, Entry):
                        return value.id
                    elif isinstance(value, str):
                        return int(value)
                    else:
                        return value

                # the case that specified value is empty or invalid
                if not recv_value:
                    # Value would be changed as empty
                    # when there are any values in the latest AttributeValue
                    return last_value.data_array.count() > 0

                cmp_curr = last_value.data_array.values("value", "referral_id", "boolean")

                cmp_recv = [
                    {
                        "value": info.get("name", ""),
                        "referral_id": get_entry_id(info.get("id")),
                        "boolean": info.get("boolean", False),
                    }
                    for info in recv_value
                ]

                if sorted(cmp_curr, key=lambda x: x["value"]) != sorted(
                    cmp_recv, key=lambda x: x["value"]
                ):
                    return True

            case AttrType.ARRAY_GROUP:
                # This is the case when input value is None, this returns True when
                # any available values are already exists.
                if not recv_value:
                    return any(
                        [
                            x.group and x.group.is_active
                            for x in last_value.data_array.all().select_related("group")
                        ]
                    )

                return sorted(
                    [AttributeValue.uniform_storable(v, Group) for v in recv_value if v]
                ) != sorted(
                    [
                        str(x.group.id)
                        for x in last_value.data_array.all().select_related("group")
                        if x.group and x.group.is_active
                    ]
                )

            case AttrType.ARRAY_ROLE:
                # This is the case when input value is None, this returns True when
                # any available values are already exists.
                if not recv_value:
                    return any(
                        [
                            x.role and x.role.is_active
                            for x in last_value.data_array.all().select_related("role")
                        ]
                    )

                return sorted(
                    [AttributeValue.uniform_storable(v, Role) for v in recv_value if v]
                ) != sorted(
                    [
                        str(x.role.id)
                        for x in last_value.data_array.all().select_related("role")
                        if x.role and x.role.is_active
                    ]
                )

        return False

    def get_values(self, where_extra: list[str] = []):
        where_cond = [] + where_extra

        if self.is_array():
            where_cond.append("status & %d > 0" % AttributeValue.STATUS_DATA_ARRAY_PARENT)
        else:
            where_cond.append("status & %d = 0" % AttributeValue.STATUS_DATA_ARRAY_PARENT)

        return self.values.extra(where=where_cond).order_by("created_time")

    def get_latest_values(self):
        params = {
            "where_extra": ["is_latest > 0"],
        }
        return self.get_values(**params)

    def get_latest_value(self, is_readonly: bool = False) -> AttributeValue | None:
        def _create_new_value() -> AttributeValue:
            params = {
                "value": "",
                "created_user": self.created_user,
                "parent_attr": self,
                "data_type": self.schema.type,
                "status": 0,
            }
            if self.is_array():
                params["status"] |= AttributeValue.STATUS_DATA_ARRAY_PARENT

            attrv = AttributeValue.objects.create(**params)
            self.values.add(attrv)

            return attrv

        attrv = self.values.filter(is_latest=True).last()
        if attrv:
            # When a type of attribute value is clear, a new Attribute value will be created
            if attrv.data_type != self.schema.type:
                if is_readonly:
                    return None
                else:
                    return _create_new_value()
            else:
                return attrv

        elif self.values.count() > 0:
            # During the processing of updating attribute-value, a short period of time
            # that the latest attribute value is vanished might happen. This condition
            # prevents creating new blank AttributeValue when user get latest-value of
            # this Attribute at that time.
            attrv = self.values.last()

            # When a type of attribute value is clear, a new Attribute value will be created
            if attrv.data_type != self.schema.type:
                if is_readonly:
                    return None
                else:
                    return _create_new_value()
            else:
                return attrv

        else:
            if is_readonly:
                return None
            else:
                return _create_new_value()

    def get_last_value(self) -> AttributeValue:
        attrv = self.values.last()
        if not attrv:
            attrv = AttributeValue.objects.create(
                **{
                    "value": "",
                    "created_user": self.created_user,
                    "parent_attr": self,
                    "status": 1 if self.schema.type & AttrType.GROUP else 0,
                    "data_type": self.schema.type,
                }
            )
            self.values.add(attrv)

        return attrv

    # NOTE: Type-Write
    def clone(self, user: User, **extra_params) -> Optional["Attribute"]:
        if not user.has_permission(self, ACLType.Readable) or not user.has_permission(
            self.schema, ACLType.Readable
        ):
            return None

        # We can't clone an instance by the way (.pk=None and save) like AttributeValue,
        # since the subclass instance refers to the parent_link's primary key during save.
        params = {
            "name": self.name,
            "created_user": user,
            "schema": self.schema,
            "parent_entry": self.parent_entry,
        }
        params.update(extra_params)
        cloned_attr = Attribute.objects.create(**params)

        attrv = self.get_latest_value()
        if attrv:
            new_attrv = attrv.clone(user, parent_attr=cloned_attr)

            # When the Attribute is array, this method also clone co-AttributeValues
            if self.is_array():
                for co_attrv in attrv.data_array.all():
                    co_attrv.clone(user, parent_attr=cloned_attr, parent_attrv=new_attrv)

            cloned_attr.values.add(new_attrv)

        return cloned_attr

    def unset_latest_flag(self, exclude_id: int | None = None) -> None:
        exclude = Q()
        if exclude_id:
            exclude = Q(id=exclude_id)
        self.values.filter(is_latest=True).exclude(exclude).update(is_latest=False)

    def _validate_value(self, value) -> bool:
        def _is_group_object(val: Any, model: Type[Group | Role]) -> bool:
            return isinstance(val, (model, int, str)) or val is None

        match self.schema.type:
            case AttrType.NAMED_OBJECT:
                return isinstance(value, dict)

            case AttrType.STRING | AttrType.TEXT:
                return True

            case AttrType.OBJECT:
                return isinstance(value, (str, int, Entry)) or value is None

            case AttrType.BOOLEAN:
                return isinstance(value, bool)

            case AttrType.DATE:
                match value:
                    case None | date():
                        return True
                    case str() if value == "":
                        return True
                    case str():
                        try:
                            datetime.strptime(value, "%Y-%m-%d")
                            return True
                        except ValueError:
                            return False
                    case _:
                        return False

            case AttrType.GROUP:
                return _is_group_object(value, Group)

            case AttrType.ROLE:
                return _is_group_object(value, Role)

            case AttrType.DATETIME:

                def _is_iso8601(v: str) -> bool:
                    try:
                        datetime.fromisoformat(v)
                        return True
                    except ValueError:
                        return False

                match value:
                    case None | datetime():
                        return True
                    case str() if value == "":
                        return True
                    case str():
                        return _is_iso8601(value)
                    case _:
                        return False

            case _ if self.is_array():
                if value is None:
                    return True

                match self.schema.type:
                    case AttrType.ARRAY_NAMED_OBJECT:
                        return all(
                            isinstance(x, dict) or isinstance(x, type({}.values())) for x in value
                        )

                    case AttrType.ARRAY_OBJECT:
                        return all(isinstance(x, (str, int, Entry)) or x is None for x in value)

                    case AttrType.ARRAY_STRING:
                        return True

                    case AttrType.ARRAY_GROUP:
                        return all(_is_group_object(x, Group) for x in value)

                    case AttrType.ARRAY_ROLE:
                        return all(_is_group_object(x, Role) for x in value)

            case _:
                return False

        return False

    def add_value(self, user: User, value, boolean: bool = False) -> AttributeValue:
        """This method make AttributeValue and set it as the latest one"""

        # This is a helper method to set AttributeType
        def _set_attrv(
            attr_type: int, val, attrv: AttributeValue | None = None, params={}
        ) -> AttributeValue | None:
            if not attrv:
                attrv = AttributeValue(**params)

            match attr_type:
                case AttrType.STRING | AttrType.TEXT:
                    attrv.boolean = boolean
                    attrv.value = str(val)
                    if not attrv.value:
                        return None

                case AttrType.GROUP:
                    attrv.boolean = boolean
                    ref = None
                    match val:
                        case Group() if val.is_active:
                            ref = val
                        case int():
                            ref = Group.objects.filter(id=val, is_active=True).first()
                        case str() if val.isdigit():
                            ref = Group.objects.filter(id=val, is_active=True).first()
                        case _:
                            return None
                    if ref:
                        attrv.group = ref

                case AttrType.ROLE:
                    attrv.boolean = boolean
                    ref = None
                    match val:
                        case Role() if val.is_active:
                            ref = val
                        case int():
                            ref = Role.objects.filter(id=val, is_active=True).first()
                        case str() if val.isdigit():
                            ref = Role.objects.filter(id=val, is_active=True).first()
                        case _:
                            return None
                    if ref:
                        attrv.role = ref

                case AttrType.OBJECT:
                    attrv.boolean = boolean
                    # set None if the referral entry is not specified
                    attrv.referral = None
                    if not val:
                        pass
                    elif isinstance(val, Entry):
                        attrv.referral = val
                    elif isinstance(val, str) or isinstance(val, int):
                        ref_entry = Entry.objects.filter(id=val, is_active=True).first()
                        if ref_entry:
                            attrv.referral = ref_entry

                    if not attrv.referral:
                        return None

                case AttrType.BOOLEAN:
                    attrv.boolean = val

                case AttrType.DATE:
                    if isinstance(val, str) and val:
                        attrv.date = datetime.strptime(val, "%Y-%m-%d").date()
                    elif isinstance(val, date):
                        attrv.date = val

                    attrv.boolean = boolean

                case AttrType.NAMED_OBJECT:
                    attrv.value = val["name"] if "name" in val else ""
                    if "boolean" in val:
                        attrv.boolean = val["boolean"]
                    else:
                        attrv.boolean = boolean

                    attrv.referral = None
                    if "id" not in val or not val["id"]:
                        pass
                    elif isinstance(val["id"], str) or isinstance(val["id"], int):
                        ref_entry = Entry.objects.filter(id=val["id"], is_active=True).first()
                        if ref_entry:
                            attrv.referral = ref_entry
                    elif isinstance(val["id"], Entry):
                        attrv.referral = val["id"]
                    else:
                        attrv.referral = None

                    if not attrv.referral and not attrv.value:
                        return None

                case AttrType.DATETIME:
                    if isinstance(val, str) and val:
                        attrv.datetime = datetime.fromisoformat(val)
                    elif isinstance(val, datetime):
                        attrv.datetime = val

            return attrv

        # checks the type of specified value is acceptable for this Attribute object
        if not self._validate_value(value):
            raise TypeError(
                '[%s] "%s" is not acceptable [attr_type:%d]'
                % (self.schema.name, str(value), self.schema.type)
            )

        # Initialize AttrValue as None, because this may not created
        # according to the specified parameters.
        attr_value = AttributeValue.create(user, self)
        if self.is_array():
            attr_value.boolean = boolean

            # set status of parent data_array
            attr_value.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)

            if value and isinstance(value, Iterable):
                co_attrv_params = {
                    "created_user": user,
                    "parent_attr": self,
                    "data_type": self.schema.type,
                    "parent_attrv": attr_value,
                    "is_latest": False,
                    "boolean": boolean,
                }

                # create and append updated values
                attrv_bulk = []
                for v in value:
                    # set AttributeValue for each values
                    co_attrv = _set_attrv(
                        (self.schema.type & ~AttrType._ARRAY),
                        v,
                        params=co_attrv_params,
                    )
                    if co_attrv:
                        attrv_bulk.append(co_attrv)

                # Create each leaf AttributeValue in bulk.
                # This processing send only one query to the DB
                # for making all AttributeValue objects.
                AttributeValue.objects.bulk_create(attrv_bulk)

        else:
            _set_attrv(self.schema.type, value, attrv=attr_value)

        attr_value.save()

        # append new AttributeValue
        self.values.add(attr_value)

        # Clear the flag that means target AttrValues are latet from the Values
        # that are already created.
        self.unset_latest_flag(exclude_id=attr_value.id)

        return attr_value

    def convert_value_to_register(self, value):
        """
        This absorbs difference values according to the type of Attributes
        """

        def get_entry(schema: Entity, name: str) -> Entry:
            return Entry.objects.get(is_active=True, schema=schema, name=name)

        def is_entry(schema: Entity, name: str) -> bool:
            return Entry.objects.filter(is_active=True, schema=schema, name=name).exists()

        def get_named_object(data: dict) -> dict:
            (key, value) = list(data.items())[0]

            ret_value = {"name": key, "id": None}
            if isinstance(value, ACLBase):
                ret_value["id"] = value

            elif isinstance(value, str):
                entryset = [
                    get_entry(r, value) for r in self.schema.referral.all() if is_entry(r, value)
                ]

                if any(entryset):
                    ret_value["id"] = entryset[0]
                else:
                    ret_value["id"] = None

            return ret_value

        match self.schema.type:
            case AttrType.STRING | AttrType.TEXT:
                return value

            case AttrType.OBJECT:
                if isinstance(value, ACLBase):
                    return value
                elif isinstance(value, str):
                    entryset = [
                        get_entry(r, value)
                        for r in self.schema.referral.all()
                        if is_entry(r, value)
                    ]
                    if any(entryset):
                        return entryset[0]

            case AttrType.GROUP:
                # This avoids to return 0 when invaild value is specified because
                # uniform_storable() returns 0. By this check processing,
                # this returns None whe it happens.
                val = AttributeValue.uniform_storable(value, Group)
                if val:
                    return val

            case AttrType.ROLE:
                val = AttributeValue.uniform_storable(value, Role)
                if val:
                    return val

            case AttrType.BOOLEAN:
                return value

            case AttrType.DATE:
                return value

            case AttrType.NAMED_OBJECT:
                if not isinstance(value, dict):
                    return None
                return get_named_object(value)

            case AttrType.DATETIME:
                return value

            case _ if self.is_array():
                if not isinstance(value, list):
                    return None

                match self.schema.type:
                    case AttrType.ARRAY_NAMED_OBJECT | AttrType.ARRAY_NAMED_OBJECT_BOOLEAN:
                        if not all([isinstance(x, dict) for x in value]):
                            return None
                        return [get_named_object(x) for x in value]

                    case AttrType.ARRAY_STRING:
                        return value

                    case AttrType.ARRAY_OBJECT:
                        return sum(
                            [
                                [
                                    get_entry(r, v)
                                    for r in self.schema.referral.all()
                                    if is_entry(r, v)
                                ]
                                for v in value
                            ],
                            [],
                        )

                    case AttrType.ARRAY_GROUP:
                        return [
                            x
                            for x in [AttributeValue.uniform_storable(y, Group) for y in value]
                            if x
                        ]

                    case AttrType.ARRAY_ROLE:
                        return [
                            x
                            for x in [AttributeValue.uniform_storable(y, Role) for y in value]
                            if x
                        ]

        return None

    # NOTE: Type-Write
    def remove_from_attrv(self, user: User, referral: ACLBase | None = None, value: str = ""):
        """
        This method removes target entry from specified attribute
        """

        attrv = self.get_latest_value()
        if self.is_array() and attrv:
            match self.schema.type:
                case AttrType.ARRAY_NAMED_OBJECT | AttrType.ARRAY_NAMED_OBJECT_BOOLEAN:
                    if referral is None:
                        return

                    updated_data = [
                        {
                            "name": x.value,
                            "id": x.referral.id if x.referral else None,
                            "boolean": x.boolean,
                        }
                        for x in attrv.data_array.exclude(referral=referral, value=value)
                    ]

                case AttrType.ARRAY_STRING:
                    if not value:
                        return

                    updated_data = [x.value for x in attrv.data_array.all() if x.value != value]

                case AttrType.ARRAY_OBJECT:
                    if referral is None:
                        return

                    updated_data = [
                        x.referral.id
                        for x in attrv.data_array.all()
                        if x.referral and x.referral.id != referral.id
                    ]

                case AttrType.ARRAY_GROUP:
                    if not value:
                        return

                    updated_data = [
                        x.group.id
                        for x in attrv.data_array.all().select_related("group")
                        if (
                            x.group
                            and x.group.is_active
                            and str(x.group.id) != AttributeValue.uniform_storable(value, Group)
                        )
                    ]

                case AttrType.ARRAY_ROLE:
                    if not value:
                        return

                    updated_data = [
                        x.role.id
                        for x in attrv.data_array.all().select_related("role")
                        if (
                            x.role
                            and x.role.is_active
                            and str(x.role.id) != AttributeValue.uniform_storable(value, Role)
                        )
                    ]

                case _:
                    return

            if self.is_updated(updated_data):
                self.add_value(user, updated_data, boolean=attrv.boolean)

    # NOTE: Type-Write
    def add_to_attrv(
        self, user: User, referral: ACLBase | None = None, value: str = "", boolean: bool = False
    ):
        """
        This method adds target entry to specified attribute with referral_key
        """
        attrv = self.get_latest_value()
        if self.is_array() and attrv:
            updated_data = None
            match self.schema.type:
                case AttrType.ARRAY_NAMED_OBJECT | AttrType.ARRAY_NAMED_OBJECT_BOOLEAN:
                    if value or referral:
                        updated_data = [
                            {
                                "name": x.value,
                                "boolean": x.boolean,
                                "id": x.referral.id if x.referral else None,
                            }
                            for x in attrv.data_array.all()
                        ] + [{"name": str(value), "boolean": boolean, "id": referral}]

                case AttrType.ARRAY_STRING:
                    if value:
                        updated_data = [x.value for x in attrv.data_array.all()] + [value]

                case AttrType.ARRAY_OBJECT:
                    if referral:
                        updated_data = [x.referral.id for x in attrv.data_array.all()] + [referral]

                case AttrType.ARRAY_GROUP:
                    group_id = AttributeValue.uniform_storable(value, Group)
                    if group_id:
                        updated_data = [
                            x.group.id
                            for x in attrv.data_array.all().select_related("group")
                            if x.group
                        ] + [group_id]

                case AttrType.ARRAY_ROLE:
                    role_id = AttributeValue.uniform_storable(value, Role)
                    if role_id:
                        updated_data = [
                            x.role.id
                            for x in attrv.data_array.all().select_related("role")
                            if x.role
                        ] + [role_id]

                case _:
                    updated_data = None

            if updated_data and self.is_updated(updated_data):
                self.add_value(user, updated_data, boolean=attrv.boolean)

    def may_remove_referral(self) -> None:
        def _may_remove_referral(referral: ACLBase | None):
            if not referral:
                # the case this refers no entry, do nothing
                return

            entry: Entry = Entry.objects.filter(id=referral.id, is_active=True).first()
            if not entry:
                # the case referred entry is already deleted, do nothing
                return

            if entry.get_referred_objects().exclude(id=self.parent_entry.id).count() > 0:
                # the case other entries also refer target referral, do nothing
                return

            entry.delete()

        # delete referral object that isn't referred from any objects if it's necessary
        if self.schema.is_delete_in_chain and self.schema.type & AttrType.OBJECT:
            attrv = self.get_latest_value()

            if attrv:
                if self.is_array():
                    [_may_remove_referral(x.referral) for x in attrv.data_array.all()]
                else:
                    _may_remove_referral(attrv.referral)

    # NOTE: Type-Write
    def delete(self):
        super(Attribute, self).delete()

        self.may_remove_referral()

    # implementation for Attribute
    def check_duplication_entry_at_restoring(self, entry_chain: list["Entry"]) -> bool:
        def _check(referral: ACLBase | None):
            if referral and not referral.is_active:
                entry = Entry.objects.filter(id=referral.id, is_active=False).first()
                if entry:
                    if entry in entry_chain:
                        # It means it's safe to restore this Entry.
                        return False
                    dup_entry = Entry.objects.filter(
                        schema=entry.schema.id,
                        name=re.sub(r"_deleted_[0-9_]*$", "", entry.name),
                        is_active=True,
                    ).first()
                    if dup_entry:
                        return True

                    entry_chain.append(entry)

                    return entry.check_duplication_entry_at_restoring(entry_chain)

            # It means it's safe to restore this Entry.
            return False

        if self.schema.is_delete_in_chain and self.schema.type & AttrType.OBJECT:
            attrv = self.get_latest_value()

            if attrv:
                if self.is_array():
                    ret = [_check(x.referral) for x in attrv.data_array.all()]
                    if True in ret:
                        return True
                    else:
                        return False
                else:
                    return _check(attrv.referral)

        return False

    # NOTE: Type-Write
    def restore(self):
        super(Attribute, self).restore()

        def _may_restore_referral(referral: ACLBase | None):
            if not referral:
                # the case this refers no entry, do nothing
                return

            entry = Entry.objects.filter(id=referral.id, is_active=False).first()
            if not entry:
                # the case referred entry is already restored, do nothing
                return

            entry.restore()

        # restore referral object that isn't referred from any objects if it's necessary
        if self.schema.is_delete_in_chain and self.schema.type & AttrType.OBJECT:
            attrv = self.get_latest_value()

            if self.is_array():
                [_may_restore_referral(x.referral) for x in attrv.data_array.all()]
            else:
                _may_restore_referral(attrv.referral)


class Entry(ACLBase):
    # This flag is set just after created or edited, then cleared at completion of the processing
    STATUS_CREATING = 1 << 0
    STATUS_EDITING = 1 << 1
    STATUS_COMPLEMENTING_ATTRS = 1 << 2

    schema = models.ForeignKey(Entity, on_delete=models.DO_NOTHING)

    history = HistoricalRecords(excluded_fields=["status", "updated_time"])

    def __init__(self, *args, **kwargs):
        super(Entry, self).__init__(*args, **kwargs)
        self.objtype = ACLObjType.Entry

    def add_alias(self, name):
        # validate name that is not duplicated with other Item names and Aliases in this model
        if not self.schema.is_available(name):
            raise ValueError("Specified name has already been used by other Item or Alias")

        return AliasEntry.objects.create(name=name, entry=self)

    def delete_alias(self, name):
        alias = AliasEntry.objects.filter(
            name=name, entry__schema=self.schema, entry__is_active=True
        ).first()
        if alias:
            alias.delete()

    def add_attribute_from_base(self, base: EntityAttr, request_user: User):
        if not isinstance(base, EntityAttr):
            raise TypeError('Variable "base" is incorrect type')

        if not isinstance(request_user, User):
            raise TypeError('Variable "user" is incorrect type')

        # If multiple requests are invoked to make requests at the same time,
        # some may create the same attribute. So use get_or_create().
        attr, _ = Attribute.objects.get_or_create(
            schema=base,
            parent_entry=self,
            defaults={
                "name": base.name,
                "created_user": request_user,
            },
        )
        if attr.is_active is False:
            attr.restore()
        return attr

    def get_prev_refers_objects(self) -> QuerySet:
        """
        This returns objects to which this Entry referred just one before.
        """
        entry_ids = []
        for attr in self.attrs.filter(is_active=True, schema__is_active=True).prefetch_related(
            "values__data_array__referral"
        ):
            if attr.is_array():
                before_last_attrv = (
                    attr.values.filter(is_latest=False).order_by("created_time").last()
                )
                if before_last_attrv is None:
                    continue

                entry_ids += [
                    x.referral.id
                    for x in before_last_attrv.data_array.all()
                    if x.referral is not None
                ]

            else:
                before_last_attrv = (
                    attr.values.filter(is_latest=False).order_by("created_time").last()
                )
                if before_last_attrv is None or before_last_attrv.referral is None:
                    continue

                entry_ids.append(before_last_attrv.referral.id)

        return Entry.objects.filter(id__in=entry_ids)

    def get_refers_objects(self) -> QuerySet:
        """
        This returns all objects that this Entry refers to just by about twice SQL call.
        """
        query = Q(
            Q(is_latest=True) | Q(parent_attrv__is_latest=True),
            referral__is_active=True,
            parent_attr__parent_entry=self,
        )

        entry_ids = [x.referral.id for x in AttributeValue.objects.filter(query)]

        return Entry.objects.filter(id__in=entry_ids)

    def get_referred_objects(
        self, filter_entities: list[str] = [], exclude_entities: list[str] = []
    ) -> QuerySet:
        return Entry.get_referred_entries([self.id], filter_entities, exclude_entities)

    def complement_attrs(self, user: User):
        """
        This method complements Attributes which are appended after creation of Entity
        """

        # Get auto complement user
        user = auto_complement.get_auto_complement_user(user)

        for attr_id in set(
            self.schema.attrs.filter(is_active=True).values_list("id", flat=True)
        ) - set(self.attrs.filter(is_active=True).values_list("schema", flat=True)):
            entity_attr = self.schema.attrs.get(id=attr_id)
            if not user.has_permission(entity_attr, ACLType.Readable):
                continue

            newattr = self.add_attribute_from_base(entity_attr, user)

            if entity_attr.type & AttrType._ARRAY:
                # Create a initial AttributeValue for editing processing
                attr_value = AttributeValue.objects.create(
                    **{
                        "created_user": user,
                        "parent_attr": newattr,
                        "data_type": entity_attr.type,
                    }
                )

                # Set status of parent data_array
                attr_value.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)

                newattr.values.add(attr_value)

    # NOTE: Type-Read
    def get_available_attrs(self, user: User, permission=ACLType.Readable) -> list[dict[str, Any]]:
        # To avoid unnecessary DB access for caching referral entries
        ret_attrs: list[dict[str, Any]] = []
        attrv_prefetch = Prefetch(
            "values",
            queryset=AttributeValue.objects.filter(is_latest=True)
            .select_related("referral")
            .prefetch_related("data_array__referral"),
            to_attr="attrv_list",
        )
        attr_prefetch = Prefetch(
            "attribute_set",
            queryset=Attribute.objects.filter(parent_entry=self, is_active=True).prefetch_related(
                attrv_prefetch
            ),
            to_attr="attr_list",
        )
        for entity_attr in (
            self.schema.attrs.filter(is_active=True)
            .prefetch_related(attr_prefetch)
            .order_by("index")
        ):
            attrinfo: dict[str, Any] = {
                "id": "",
                "entity_attr_id": entity_attr.id,
                "name": entity_attr.name,
                "type": entity_attr.type,
                "is_mandatory": entity_attr.is_mandatory,
                "index": entity_attr.index,
                "is_readable": True,
                "last_value": AttrDefaultValue[entity_attr.type],
            }

            # check that attribute exists
            attr = entity_attr.attr_list[0] if entity_attr.attr_list else None
            if not attr:
                attrinfo["is_readable"] = user.has_permission(entity_attr, permission)
                ret_attrs.append(attrinfo)
                continue
            attrinfo["id"] = attr.id

            # check permission of attributes
            if not user.has_permission(attr, permission):
                attrinfo["is_readable"] = False
                ret_attrs.append(attrinfo)
                continue

            # set last-value of current attributes
            last_value = attr.attrv_list[-1] if attr.attrv_list else None
            if last_value is None:
                ret_attrs.append(attrinfo)
                continue

            match last_value.data_type:
                case AttrType.STRING | AttrType.TEXT:
                    attrinfo["last_value"] = last_value.value

                case AttrType.OBJECT:
                    if last_value.referral and last_value.referral.is_active:
                        attrinfo["last_value"] = last_value.referral
                    else:
                        attrinfo["last_value"] = None

                case AttrType.ARRAY_STRING:
                    # this dict-key 'last_value' is uniformed with all array types
                    attrinfo["last_value"] = [x.value for x in last_value.data_array.all()]

                case AttrType.ARRAY_OBJECT:
                    attrinfo["last_value"] = [
                        x.referral
                        for x in last_value.data_array.all()
                        if x.referral and x.referral.is_active
                    ]

                case AttrType.BOOLEAN:
                    attrinfo["last_value"] = last_value.boolean

                case AttrType.DATE:
                    attrinfo["last_value"] = last_value.date

                case AttrType.NAMED_OBJECT:
                    attrinfo["last_value"] = {"value": last_value.value}

                    if last_value.referral and last_value.referral.is_active:
                        attrinfo["last_value"]["id"] = last_value.referral.id
                        attrinfo["last_value"]["name"] = last_value.referral.name

                case AttrType.ARRAY_NAMED_OBJECT:
                    values = []
                    for attrv in last_value.data_array.all():
                        value = {"value": attrv.value}
                        if attrv.referral and not attrv.referral.is_active:
                            # not to show value when target referral Entry is deleted
                            continue

                        elif attrv.referral and attrv.referral.is_active:
                            value["id"] = attrv.referral.id
                            value["name"] = attrv.referral.name
                        values.append(value)

                    attrinfo["last_value"] = sorted(
                        values,
                        key=lambda x: x["value"],
                    )

                case AttrType.GROUP if last_value.group:
                    if last_value.group.is_active:
                        attrinfo["last_value"] = last_value.group
                    else:
                        attrinfo["last_value"] = None

                case AttrType.ARRAY_GROUP:
                    attrinfo["last_value"] = [
                        x
                        for x in [
                            v.group for v in last_value.data_array.all().select_related("group")
                        ]
                        if x
                    ]

                case AttrType.ROLE if last_value.role:
                    if last_value.role.is_active:
                        attrinfo["last_value"] = last_value.role
                    else:
                        attrinfo["last_value"] = None

                case AttrType.ARRAY_ROLE:
                    attrinfo["last_value"] = [
                        x
                        for x in [
                            v.role for v in last_value.data_array.all().select_related("role")
                        ]
                        if x
                    ]

                case AttrType.DATETIME:
                    attrinfo["last_value"] = last_value.datetime

            ret_attrs.append(attrinfo)

        return ret_attrs

    # NOTE: Type-Read
    def to_dict(self, user: User, with_metainfo: bool = False) -> dict[str, Any] | None:
        # check permissions for each entry, entity and attrs
        if not user.has_permission(self.schema, ACLType.Readable) or not user.has_permission(
            self, ACLType.Readable
        ):
            return None

        attr_prefetch = Prefetch(
            "attribute_set",
            queryset=Attribute.objects.filter(
                parent_entry=self, is_active=True, schema__is_active=True
            ),
            to_attr="attr_list",
        )
        sorted_attrs: List[Attribute] = [
            x.attr_list[0]
            for x in self.schema.attrs.filter(is_active=True)
            .prefetch_related(attr_prefetch)
            .order_by("index")
            if x.attr_list
        ]

        attrs = [
            x
            for x in sorted_attrs
            if (
                user.has_permission(x.schema, ACLType.Readable)
                and user.has_permission(x, ACLType.Readable)
            )
        ]

        returning_attrs = []
        for attr in attrs:
            attrv = attr.get_latest_value(is_readonly=True)
            if attrv is None:
                value = AttributeValue.get_default_value(attr)
                if attr.schema.type == AttrType.NAMED_OBJECT:
                    value = {"": None}
                if with_metainfo:
                    value = {"type": attr.schema.type, "value": value}
                returning_attrs.append(
                    {
                        "id": attr.id,
                        "schema_id": attr.schema.id,
                        "name": attr.schema.name,
                        "value": value,
                    }
                )

            else:
                returning_attrs.append(
                    {
                        "id": attr.id,
                        "schema_id": attr.schema.id,
                        "name": attr.schema.name,
                        "value": attrv.get_value(serialize=True, with_metainfo=with_metainfo),
                    }
                )

        return {
            "id": self.id,
            "name": self.name,
            "entity": {
                "id": self.schema.id,
                "name": self.schema.name,
            },
            "attrs": returning_attrs,
        }

    def save(self, *args, **kwargs) -> None:
        max_entries: int | None = settings.MAX_ENTRIES
        if max_entries and Entry.objects.count() >= max_entries:
            raise RuntimeError("The number of entries is over the limit")
        return super(Entry, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super(Entry, self).delete(*args, **kwargs)

        # update Elasticsearch index info which refered this entry not to refer this link
        es_object = ESS()
        for entry in [x for x in self.get_referred_objects() if x.id != self.id]:
            entry.register_es(es=es_object)

        # also delete each attributes
        for attr in self.attrs.filter(is_active=True):
            # delete Attribute object
            attr.delete()

        if settings.ES_CONFIG:
            self.unregister_es()

    # implementation for Entry
    def check_duplication_entry_at_restoring(self, entry_chain: list["Entry"] = []) -> bool:
        """This method returns true when this Entry has referral that is
           same name with other entry at restoring Entry.
        - case True: there is an Entry(at least) that is same name with same Entity.
        - case False: there is no Entry that is same name with same Entity.
        """
        for attr in self.attrs.filter(is_active=False):
            if attr.check_duplication_entry_at_restoring(entry_chain):
                return True

        # It means it's safe to restore this Entry.
        return False

    def restore(self):
        super(Entry, self).restore()

        # also restore each attributes
        for attr in self.attrs.filter(is_active=False):
            # restore Attribute object
            attr.restore()

        # update Elasticsearch index info which refered this entry to refer this link
        es_object = ESS()
        for entry in [x for x in self.get_referred_objects()]:
            entry.register_es(es=es_object)

        # update entry information to Elasticsearch
        self.register_es()

    def clone(self, user: User, **extra_params) -> Optional["Entry"]:
        if not user.has_permission(self, ACLType.Readable) or not user.has_permission(
            self.schema, ACLType.Readable
        ):
            return None

        # set STATUS_CREATING flag until all related parameters are set
        status = Entry.STATUS_CREATING
        if "status" in extra_params:
            status |= extra_params.pop("status")

        # We can't clone an instance by the way (.pk=None and save) like AttributeValue,
        # since the subclass instance refers to the parent_link's primary key during save.
        params = {
            "name": self.name,
            "created_user": user,
            "schema": self.schema,
            "status": status,
        }
        params.update(extra_params)
        cloned_entry = Entry(**params)

        # for history record
        cloned_entry._history_user = user

        cloned_entry.save()

        for attr in self.attrs.filter(is_active=True):
            attr.clone(user, parent_entry=cloned_entry)

        cloned_entry.del_status(Entry.STATUS_CREATING)
        return cloned_entry

    # NOTE: Type-Write
    def export(self, user: User) -> dict[str, Any]:
        attrinfo = {}

        # This calling of complement_attrs is needed to take into account the case of the Attributes
        # that are added after creating this entry.
        self.complement_attrs(user)

        for attr in self.attrs.filter(is_active=True, schema__is_active=True):
            if not user.has_permission(attr, ACLType.Readable):
                continue

            latest_value = attr.get_latest_value()
            if latest_value:
                attrinfo[attr.schema.name] = latest_value.get_value()
            else:
                attrinfo[attr.schema.name] = None

        return {"name": self.name, "attrs": attrinfo}

    def export_v2(self, user: User, with_entity: bool = False) -> dict:
        attrinfo = []

        # This calling of complement_attrs is needed to take into account the case of the Attributes
        # that are added after creating this entry.
        self.complement_attrs(user)

        for attr in self.attrs.filter(is_active=True, schema__is_active=True).order_by(
            "schema__index"
        ):
            if not user.has_permission(attr, ACLType.Readable):
                continue

            latest_value = attr.get_latest_value()
            value: Any | None = None
            if latest_value:
                match latest_value.data_type:
                    case AttrType.ARRAY_OBJECT:
                        # remove elements have None value
                        value = [x for x in latest_value.get_value(with_entity=with_entity) if x]
                    case AttrType.NAMED_OBJECT:
                        # remove elements have empty name and None value
                        value = {
                            n: v
                            for n, v in latest_value.get_value(with_entity=with_entity).items()
                            if len(n) > 0 or v
                        }
                    case AttrType.ARRAY_NAMED_OBJECT:
                        # remove elements have empty name and None value
                        value = [
                            x
                            for x in latest_value.get_value(with_entity=with_entity)
                            if len(list(x.keys())[0]) > 0 or list(x.values())[0]
                        ]
                    case _:
                        value = latest_value.get_value(with_entity=with_entity)

            attrinfo.append(
                {
                    "name": attr.schema.name,
                    "value": value,
                }
            )

        return {"name": self.name, "attrs": attrinfo}

    # NOTE: Type-Write
    def get_es_document(self, entity_attrs=None) -> EntryDocument:
        """This processing registers entry information to Elasticsearch"""

        # This inner method truncates value in taking multi-byte in account
        def truncate(value: str) -> str:
            while len(value.encode("utf-8")) > ESS.MAX_TERM_SIZE:
                value = value[:-1]
            return value

        def _set_attrinfo(
            entity_attr: EntityAttr,
            attr: Attribute | None,
            attrv: AttributeValue | None,
            container: list[AttributeDocument],
            is_recursive: bool = False,
        ):
            attrinfo: AttributeDocument = {
                "name": entity_attr.name,
                "type": entity_attr.type,
                "key": "",
                "value": "",
                "date_value": None,
                "referral_id": "",
                "is_readable": True
                if (not attr or attr.is_public or attr.default_permission >= ACLType.Readable)
                else False,
            }

            # default value for boolean attributes is False.
            if entity_attr.type & AttrType.BOOLEAN:
                attrinfo["value"] = False

            # Convert data format for mapping of Elasticsearch according to the data type
            if attrv is None:
                # This is the processing to be safe even if the empty AttributeValue was passed.
                pass

            elif entity_attr.type & AttrType.STRING or entity_attr.type & AttrType.TEXT:
                attrinfo["value"] = truncate(attrv.value)

            elif entity_attr.type & AttrType.BOOLEAN:
                attrinfo["value"] = attrv.boolean

            elif entity_attr.type & AttrType.DATE:
                attrinfo["date_value"] = attrv.date.strftime("%Y-%m-%d") if attrv.date else None

            elif entity_attr.type & AttrType.DATETIME:
                attrinfo["date_value"] = attrv.datetime.isoformat() if attrv.datetime else None

            elif entity_attr.type & AttrType._NAMED:
                attrinfo["key"] = attrv.value

                if attrv.referral and attrv.referral.is_active:
                    attrinfo["value"] = truncate(attrv.referral.name)
                    attrinfo["referral_id"] = attrv.referral.id
                elif (
                    entity_attr.type & AttrType._ARRAY
                    and attrv.referral
                    and not attrv.referral.is_active
                ):
                    attrinfo["key"] = ""

            elif entity_attr.type & AttrType.OBJECT:
                if attrv.referral and attrv.referral.is_active:
                    attrinfo["value"] = truncate(attrv.referral.name)
                    attrinfo["referral_id"] = attrv.referral.id

            elif entity_attr.type & AttrType.GROUP:
                group = attrv.group
                if group:
                    if group.is_active:
                        attrinfo["value"] = truncate(group.name)
                        attrinfo["referral_id"] = group.id

            elif entity_attr.type & AttrType.ROLE:
                role = attrv.role
                if role:
                    if role.is_active:
                        attrinfo["value"] = truncate(role.name)
                        attrinfo["referral_id"] = role.id

            # Basically register attribute information whatever value doesn't exist
            if not (entity_attr.type & AttrType._ARRAY and not is_recursive):
                container.append(attrinfo)

            elif entity_attr.type & AttrType._ARRAY and not is_recursive:
                if attrv is not None:
                    # Here is the case of parent array, set each child values
                    [
                        _set_attrinfo(entity_attr, attr, x, container, True)
                        for x in attrv.data_array.all()
                    ]

                # If there is no value in container,
                # this set blank value for maching blank search request
                if not [x for x in container if x["name"] == entity_attr.name]:
                    container.append(attrinfo)

        document: EntryDocument = {
            "entity": {"id": self.schema.id, "name": self.schema.name},
            "name": self.name,
            "attr": [],
            "referrals": [
                {
                    "id": x.id,
                    "name": x.name,
                    "schema": {"id": x.schema.id, "name": x.schema.name},
                }
                for x in self.get_referred_objects().select_related("schema")
            ],
            "is_readable": True
            if (self.is_public or self.default_permission >= ACLType.Readable.id)
            else False,
        }

        # The reason why this is a beat around the bush processing is for the case that Attibutes
        # objects are not existed in attr parameter because of delay processing. If this entry
        # doesn't have an Attribute object associated with an EntityAttr, this registers blank
        # value to the Elasticsearch.
        if entity_attrs is None:
            entity_attrs = self.schema.attrs.filter(is_active=True)

        for entity_attr in entity_attrs:
            attrv: AttributeValue | None = None

            # Use it when exists prefetch for faster
            if getattr(self, "prefetch_attrs", None):
                entry_attrs = self.prefetch_attrs
            else:
                entry_attrs = self.attrs.filter(schema=entity_attr, is_active=True)

            entry_attr: Attribute | None = None
            for attr in entry_attrs:
                if attr.schema == entity_attr:
                    entry_attr = attr
                    break

            if entry_attr:
                # Use it when exists prefetch for faster
                if getattr(entry_attr, "prefetch_values", None):
                    attrv = entry_attr.prefetch_values[-1]
                else:
                    attrv = entry_attr.get_latest_value()

            _set_attrinfo(entity_attr, entry_attr, attrv, document["attr"])

        return document

    def register_es(self, es: ESS | None = None, recursive_call_stack=[]):
        """
        Arguments
          * recursive_call_stack:
            - Entris that has ever been called, which is necessary to prevent
              falling into the infinite calling loop.

        This updates es-documents which are associated with following Entries
        - 1. Entries that this Entry referred (This is necessary because es-documents of Entries,
             which were referred before but now are not, should be updated.
        - 2. This Entry (the variable "self" indicate)
        - 3. Entries that this Entry refers
        """
        if not es:
            es = ESS()

        es.index(id=self.id, body=self.get_es_document())
        es.refresh()

        if recursive_call_stack:
            return

        # It's also needed to update es-document for Entries that this Entry refers to
        search_result = es.search(
            body={
                "query": {
                    "nested": {
                        "path": "referrals",
                        "query": {"term": {"referrals.id": self.id}},
                        "inner_hits": {},
                    }
                }
            }
        )

        refers_from_es = [
            {
                "dst_entry_id": int(x["_id"]),
                "entry_name": x["inner_hits"]["referrals"]["hits"]["hits"][0]["_source"]["name"],
            }
            for x in search_result["hits"]["hits"]
        ]

        refers_from_db = [
            {"dst_entry_id": e.id, "entry_name": self.name}
            for e in self.get_refers_objects()
            if e.id != self.id
        ]

        # elasticsearch: exists
        # db: not esixts
        # (or change entry name)
        for refer in refers_from_es:
            if refer not in refers_from_db:
                entry = Entry.objects.get(id=refer["dst_entry_id"])
                entry.register_es(es, recursive_call_stack + [self])

        # elasticsearch: not exists
        # db: esixts
        for refer in refers_from_db:
            if refer["dst_entry_id"] not in [x["dst_entry_id"] for x in refers_from_es]:
                entry = Entry.objects.get(id=refer["dst_entry_id"])
                entry.register_es(es, recursive_call_stack + [self])

    def unregister_es(self, es: ESS | None = None):
        if not es:
            es = ESS()

        es.delete(id=self.id, ignore=[404])
        es.refresh(ignore=[404])

    def get_value_history(
        self, user: User, count: int = CONFIG.MAX_HISTORY_COUNT, index: int = 0
    ) -> list[dict]:
        def _get_values(attrv: AttributeValue) -> dict[str, Any]:
            return {
                "attrv_id": attrv.id,
                "value": attrv.format_for_history(),
                "created_time": attrv.created_time,
                "created_user": attrv.created_user.username,
            }

        ret_values: list[dict] = []
        all_attrv = AttributeValue.objects.filter(
            parent_attr__in=self.attrs.all(), parent_attrv__isnull=True
        ).order_by("-created_time")[index:]

        for i, attrv in enumerate(all_attrv):
            if len(ret_values) >= count:
                break

            attr = attrv.parent_attr
            if (
                attr.is_active
                and attr.schema.is_active
                and user.has_permission(attr, ACLType.Readable)
                and user.has_permission(attr.schema, ACLType.Readable)
            ):
                # try to get next attrv
                next_attrv = None
                for _attrv in all_attrv[(i + 1) :]:
                    if _attrv.parent_attr == attr:
                        next_attrv = _attrv
                        break

                ret_values.append(
                    {
                        "attr_id": attr.id,
                        "attr_name": attr.schema.name,
                        "attr_type": attr.schema.type,
                        "curr": _get_values(attrv),
                        "prev": _get_values(next_attrv) if next_attrv else None,
                    }
                )

        return ret_values

    @classmethod
    def is_importable_data(kls, data) -> bool:
        """This method confirms import data has following data structure
        Entity:
            - name: entry_name
            - attrs:
                attr_name1: attr_value
                attr_name2: attr_value
                ...
        """
        if not isinstance(data, dict):
            return False

        if not all([isinstance(x, list) for x in data.values()]):
            return False

        for entry_data in sum(data.values(), []):
            if not isinstance(entry_data, dict):
                return False

            if not ("attrs" in entry_data and "name" in entry_data):
                return False

            if not isinstance(entry_data["name"], str):
                return False

            if not isinstance(entry_data["attrs"], dict):
                return False

        return True

    @classmethod
    def get_referred_entries(
        kls, id_list: list[int], filter_entities: list[str] = [], exclude_entities: list[str] = []
    ):
        """
        This returns objects that refer Entries, which is specifeied in the kd_list,
        in the AttributeValue.
        """
        ids = AttributeValue.objects.filter(
            Q(referral__in=id_list, is_latest=True)
            | Q(referral__in=id_list, parent_attrv__is_latest=True),
            parent_attr__is_active=True,
            parent_attr__schema__is_active=True,
        ).values_list("parent_attr__parent_entry", flat=True)

        # if entity_name param exists, add schema name to reduce filter execution time
        query = Q(pk__in=ids, is_active=True)
        if filter_entities:
            query &= Q(schema__name__in=filter_entities)

        return Entry.objects.filter(query).exclude(schema__name__in=exclude_entities).order_by("id")

    def get_attrv(self, attr_name: str) -> AttributeValue | None:
        """This returns specified attribute's value without permission check. Because
        this prioritizes performance (less frequency of sending query to Database) over
        authorization safety.

        CAUTION: Don't use this before permissoin check of specified attribute.
        """
        return AttributeValue.objects.filter(
            is_latest=True,
            parent_attr__schema__name=attr_name,
            parent_attr__schema__is_active=True,
            parent_attr__parent_entry=self,
        ).last()

    def get_attrv_item(self, attr_name: str) -> Union["Entry", list["Entry"], None]:
        """
        This helper method returns Item that is referred by specified attribute value
        """
        attrv = self.get_attrv(attr_name)
        if not attrv:
            return None

        if attrv.is_array:
            return [x.ref_item for x in attrv.data_array.filter(referral__is_active=True)]
        else:
            return attrv.ref_item

    def get_trigger_params(self, user: User, attrnames: list[str]) -> list[dict]:
        entry_dict = self.to_dict(user, with_metainfo=True) or {}

        def _get_value(attrname: str, attrtype: int, value):
            if isinstance(value, list):
                return [_get_value(attrname, attrtype, x) for x in value]

            elif attrtype & AttrType._NAMED:
                [name, ref] = list(value.keys()) + list(value.values())

                return {
                    "id": ref["id"] if ref else None,
                    "name": name,
                }

            elif attrtype & AttrType.OBJECT:
                return value["id"] if value else None

            else:
                return value

        trigger_params = []
        for attrname in attrnames:
            try:
                [(entity_attr_id, attrtype, attrvalue)] = [
                    (x["schema_id"], x["value"]["type"], x["value"]["value"])
                    for x in entry_dict["attrs"]
                    if x["name"] == attrname
                ]
            except ValueError:
                continue

            trigger_params.append(
                {"id": entity_attr_id, "value": _get_value(attrname, attrtype, attrvalue)}
            )

        return trigger_params


class AdvancedSearchAttributeIndex(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    entity_attr = models.ForeignKey(EntityAttr, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    attr = models.ForeignKey(Attribute, on_delete=models.CASCADE, null=True)

    type = models.IntegerField()
    entry_name = models.CharField(max_length=200)
    key = models.CharField(max_length=512, null=True)
    raw_value = models.JSONField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=["key"]),
        ]

    @classmethod
    def create_instance(
        cls, entry: Entry, entity_attr: EntityAttr, attrv: AttributeValue | None
    ) -> "AdvancedSearchAttributeIndex":
        key: str | None = None
        value: dict[str, Any] | list[Any] | None = None

        if attrv:
            match entity_attr.type:
                case AttrType.STRING | AttrType.TEXT:
                    key = attrv.value
                case AttrType.BOOLEAN:
                    key = "true" if attrv.boolean else "false"
                case AttrType.DATE:
                    key = attrv.date.isoformat() if attrv.date else None
                case AttrType.DATETIME:
                    key = attrv.datetime.isoformat() if attrv.datetime else None
                case AttrType.OBJECT:
                    key = attrv.referral.name if attrv.referral else None
                    value = (
                        {"id": attrv.referral.id, "name": attrv.referral.name}
                        if attrv.referral
                        else None
                    )
                case AttrType.NAMED_OBJECT:
                    key = attrv.referral.name if attrv.referral else None
                    value = {
                        str(attrv.value): {
                            "id": attrv.referral.id,
                            "name": attrv.referral.name,
                        }
                        if attrv.referral
                        else None
                    }
                case AttrType.GROUP:
                    key = attrv.group.name if attrv.group else None
                    value = (
                        {"id": attrv.group.id, "name": attrv.group.name} if attrv.group else None
                    )
                case AttrType.ROLE:
                    key = attrv.role.name if attrv.role else None
                    value = {"id": attrv.role.id, "name": attrv.role.name} if attrv.role else None
                case AttrType.ARRAY_STRING:
                    value = [v.value for v in attrv.data_array.all()]
                    key = ",".join(value)
                case AttrType.ARRAY_OBJECT:
                    value = [
                        {"id": v.referral.id, "name": v.referral.name}
                        for v in attrv.data_array.all()
                        if v.referral
                    ]
                    key = ",".join([v["name"] for v in value])
                case AttrType.ARRAY_NAMED_OBJECT:
                    value = [
                        {v.value: {"id": v.referral.id, "name": v.referral.name}}
                        for v in attrv.data_array.all()
                        if v.referral
                    ]
                    key = ",".join([v.referral.name for v in attrv.data_array.all() if v.referral])
                case AttrType.ARRAY_GROUP:
                    value = [
                        {"id": v.group.id, "name": v.group.name}
                        for v in attrv.data_array.all()
                        if v.group
                    ]
                    key = ",".join([v["name"] for v in value])
                case AttrType.ARRAY_ROLE:
                    value = [
                        {"id": v.role.id, "name": v.role.name}
                        for v in attrv.data_array.all()
                        if v.role
                    ]
                    key = ",".join([v["name"] for v in value])
                case _:
                    print("TODO implement it")

        return AdvancedSearchAttributeIndex(
            entity=entry.schema,
            entity_attr=entity_attr,
            entry=entry,
            attr=attrv.parent_attr if attrv else None,
            type=entity_attr.type,
            entry_name=entry.name,
            key=key,
            raw_value=value,
        )

    @property
    def value(self):
        match self.type:
            case (
                AttrType.STRING
                | AttrType.TEXT
                | AttrType.BOOLEAN
                | AttrType.DATE
                | AttrType.DATETIME
            ):
                return self.key
            case AttrType.BOOLEAN:
                return self.key == "true"
            case (
                AttrType.OBJECT
                | AttrType.NAMED_OBJECT
                | AttrType.GROUP
                | AttrType.ROLE
                | AttrType.ARRAY_STRING
                | AttrType.ARRAY_OBJECT
                | AttrType.ARRAY_NAMED_OBJECT
                | AttrType.ARRAY_GROUP
                | AttrType.ARRAY_ROLE
            ):
                return self.raw_value
            case _:
                print("TODO implement it")


class AliasEntry(models.Model):
    name = models.CharField(max_length=200)

    # This indicates alias of this Entry
    entry = models.ForeignKey(
        Entry,
        related_name="aliases",
        on_delete=models.CASCADE,
    )


# TODO: name more good name
# This instance wrapps prefetched Entry instance to abstract intermediate method call
# (e.g. attr_list, value_list, ...)
class PrefetchedItemWrapper(object):
    def __init__(self, prefetched_item, attrv=None):
        self.pi = prefetched_item
        self.attrv = attrv

    # Plz fix it
    # def __getitem__(self, attrname) -> PrefetchedItemWrapper | list(PrefetchedItemWrapper):
    def __getitem__(self, attrname):
        """
        This returns neighbor PrefetchedItemWrapper instance that wraps prefetched Entry instance
        """
        try:
            attr = [a for a in self.pi.attr_list if a.schema.name == attrname][0]

            # save attribute value to self.attrv to be able to return it via value() method
            attrv = attr.value_list[0]

            if attr.schema.type & AttrType._ARRAY and attr.schema.type & AttrType.OBJECT:
                if attr.schema.type & AttrType.OBJECT:
                    return [PrefetchedItemWrapper(v.referral.entry, attrv) for v in attrv.co_values]
                else:
                    return [PrefetchedItemWrapper(None, attrv) for v in attrv.co_values]

            elif attr.schema.type & AttrType.OBJECT:
                return PrefetchedItemWrapper(attrv.referral.entry, attrv)

            else:
                return PrefetchedItemWrapper(None, attrv)

        except IndexError as e:
            raise KeyError("(%s) " % attrname, e)

    @property
    def item(self) -> Entry:
        return self.pi

    @property
    def value(self) -> str:
        if self.attrv is not None:
            return self.attrv.value

        return ""


class ItemWalker(object):
    @classmethod
    def prefetch_attr_refs(kls, attrnames, nested_prefetch=[], is_intermediate=True):
        """
        This returns the Prefetch object for the specified attribute name
        to determine referral items that specified attribute name indicates.

        Making nested Prefetch structure by using this method, you can get
        referral items with less query count for backend database.
        """
        prefetch_co_values = Prefetch(
            lookup="data_array",
            queryset=AttributeValue.objects.filter(referral__is_active=True)
            .select_related("referral__entry")
            .prefetch_related(*nested_prefetch),
            to_attr="co_values",
        )

        prefetch_value = Prefetch(
            lookup="values",
            queryset=AttributeValue.objects.filter(is_latest=True)
            .select_related("referral")
            .prefetch_related(*nested_prefetch)
            .prefetch_related(prefetch_co_values),
            to_attr="value_list",
        )

        return Prefetch(
            lookup="referral__entry__attrs" if is_intermediate else "attrs",
            queryset=Attribute.objects.filter(
                is_active=True,
                schema__name__in=attrnames,
            )
            .select_related("schema")
            .prefetch_related(prefetch_value),
            to_attr="attr_list",
        )

    @classmethod
    def create_prefetch(kls, step_map={}, is_last=False) -> Prefetch:
        # check attr_routes has nested attribute steps
        related_prefetches = []
        for step_attrname, co_steps in step_map.items():
            if co_steps:
                related_prefetches.append(ItemWalker.create_prefetch(co_steps))

        # create Prefetch object
        return ItemWalker.prefetch_attr_refs(
            attrnames=step_map.keys(),
            nested_prefetch=related_prefetches,
            is_intermediate=not is_last,
        )

    def __init__(self, base_item_ids, step_map={}):
        prefetch = ItemWalker.create_prefetch(step_map, is_last=True)

        self.base_items = Entry.objects.prefetch_related(prefetch).filter(id__in=base_item_ids)

    @property
    def list(self):
        return [PrefetchedItemWrapper(x) for x in self.base_items]
