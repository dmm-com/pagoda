"""
XXX A super experimental advanced search module,
as an alternative for elasticsearch based current advanced search.
"""

import operator
from collections import defaultdict
from functools import reduce
from typing import Any

from django.db.models import Prefetch, Q
from django.db.models.manager import BaseManager

from airone.lib.elasticsearch import AdvancedSearchResults, AdvancedSearchResultValue, AttrHint
from airone.lib.log import Logger
from airone.lib.types import AttrType
from entry.models import Attribute, AttributeValue, Entry
from entry.settings import CONFIG
from group.models import Group
from role.models import Role
from user.models import User


def _make_query(
    user: User,
    entities: list[int],
    attr_hints: list[AttrHint],
    # FIXME later
    entry_name: str | None = None,
    hint_referral: str | None = None,
    hint_referral_entity_id: int | None = None,
    is_output_all: bool = False,
    limit: int = CONFIG.MAX_LIST_ENTRIES,
    offset: int = 0,
) -> BaseManager[Entry]:
    # FIXME fetch if entities is not empty

    attr_names = [attr_hint["name"] for attr_hint in attr_hints]
    # FIXME it supports only limited hints, implement more
    attrv_conditions = reduce(
        operator.or_,
        [
            Q(
                parent_attr__schema__name=attr_hint["name"],
                value__icontains=attr_hint["keyword"],
                is_latest=True,
            )
            if len(attr_hint["keyword"]) > 0
            else Q(parent_attr__schema__name=attr_hint["name"], is_latest=True)
            for attr_hint in attr_hints
        ],
    )

    # TODO flexible query builder based on entity attrs (necessary?)
    data_array_prefetch = Prefetch(
        "data_array",
        queryset=AttributeValue.objects.all()
        .only("value", "boolean", "referral")
        .select_related("referral"),
        to_attr="prefetched_data_array",
    )
    attrv_prefetch = Prefetch(
        "values",
        queryset=AttributeValue.objects.filter(attrv_conditions)
        .only("value", "boolean", "date", "datetime", "referral")
        .select_related("referral")
        .prefetch_related(data_array_prefetch),
        to_attr="prefetched_values",
    )
    attrs_prefetch = Prefetch(
        "attrs",
        queryset=Attribute.objects.filter(schema__name__in=attr_names)
        .only("schema")
        .select_related("schema")
        .prefetch_related(attrv_prefetch),
        to_attr="prefetched_attrs",
    )

    # FIXME get total count
    return (
        Entry.objects.filter(schema__id__in=entities)
        .only("id", "name", "schema")
        .select_related("schema")
        .prefetch_related(attrs_prefetch)
    )[offset:limit]


# NOTE fetching Group and Role, and data_array will cause N+1
def _render_attribute_value(
    type: int, values: list[AttributeValue]
) -> str | bool | dict | list | None:
    try:
        attr_type = AttrType(type)
    except ValueError:
        # For compatibility; continue that, and record the error
        Logger.error("Invalid attribute type: %s" % type)
        return None

    try:
        attrv = values[0]
    except IndexError:
        return None

    match attr_type:
        case AttrType.STRING | AttrType.TEXT:
            return attrv.value

        case AttrType.BOOLEAN:
            return attrv.boolean

        case AttrType.DATE:
            return attrv.date.strftime("%Y-%m-%d") if attrv.date else None

        case AttrType.DATETIME:
            return attrv.datetime.isoformat() if attrv.datetime else None

        case AttrType.OBJECT:
            return {
                "id": attrv.referral.id,
                "name": attrv.referral.name,
            }

        case AttrType.GROUP:
            group = Group.objects.get(id=attrv.value)
            if group:
                return {
                    "id": group.id,
                    "name": group.name,
                }
            else:
                return None

        case AttrType.ROLE:
            role = Role.objects.get(id=attrv.value)
            if role:
                return {
                    "id": role.id,
                    "name": role.name,
                }
            else:
                return None

        case AttrType.NAMED_OBJECT:
            return {
                attrv.value: {
                    "id": attrv.referral.id,
                    "name": attrv.referral.name,
                }
            }

        case (
            AttrType.ARRAY_OBJECT
            | AttrType.ARRAY_STRING
            | AttrType.ARRAY_NAMED_OBJECT
            | AttrType.ARRAY_NAMED_OBJECT_BOOLEAN
            | AttrType.ARRAY_GROUP
            | AttrType.ARRAY_ROLE
        ):
            values = attrv.prefetched_data_array

            match attr_type:
                case AttrType.ARRAY_NAMED_OBJECT:
                    return [
                        {
                            v.value: {
                                "id": v.referral.id,
                                "name": v.referral.name,
                            }
                        }
                        for v in values
                        if v.value and v.referral.id and v.referral.name
                    ]

                case AttrType.ARRAY_STRING:
                    return [v.value for v in values if v.value]

                case AttrType.ARRAY_OBJECT:
                    return [
                        {"id": v.referral.id, "name": v.referral.name}
                        for v in values
                        if v.referral.id and v.referral.name
                    ]

                case AttrType.ARRAY_GROUP:
                    groups = Group.objects.filter(id__in=[v.value for v in values if v])
                    return [{"id": g.id, "name": g.name} for g in groups]

                case AttrType.ARRAY_ROLE:
                    roles = Role.objects.filter(id__in=[v.value for v in values if v])
                    return [{"id": r.id, "name": r.name} for r in roles]

    raise ValueError("Invalid attribute type: %s" % type)


def search_entries(
    user: User,
    entities: list[int],
    attr_hints: list[AttrHint],
    # FIXME later
    entry_name: str | None = None,
    hint_referral: str | None = None,
    hint_referral_entity_id: int | None = None,
    is_output_all: bool = False,
    limit: int = CONFIG.MAX_LIST_ENTRIES,
    offset: int = 0,
) -> AdvancedSearchResults:
    entries = _make_query(
        user,
        entities,
        attr_hints,
        entry_name,
        hint_referral,
        hint_referral_entity_id,
        is_output_all,
        limit,
        offset,
    )

    values = [
        AdvancedSearchResultValue(
            entity={"id": e.schema.id, "name": e.schema.name},
            entry={"id": e.id, "name": e.name},
            attrs={
                a.schema.name: {
                    "type": a.schema.type,
                    "value": _render_attribute_value(a.schema.type, a.prefetched_values),
                    "is_readable": True,
                }
                for a in e.prefetched_attrs
                if len(a.prefetched_values) > 0
            },
            # dummy
            is_readable=True,
            referrals=[],
        )
        for e in entries
    ]

    return AdvancedSearchResults(
        ret_count=len(values),
        ret_values=values,
    )


#
# for experimental
#


# NOTE fetching Group and Role, and data_array will cause N+1
def _render_attribute_value_from_dict(
    type: int, attrv: dict[str, Any], children: list[dict[str, Any]]
) -> Any | None:
    try:
        attr_type = AttrType(type)
    except ValueError:
        # For compatibility; continue that, and record the error
        Logger.error("Invalid attribute type: %s" % type)
        return None

    match attr_type:
        case AttrType.STRING | AttrType.TEXT:
            return attrv["value"]

        case AttrType.BOOLEAN:
            return attrv["boolean"]

        case AttrType.DATE:
            d = attrv.get("date", None)
            return d.strftime("%Y-%m-%d") if d else None

        case AttrType.DATETIME:
            dt = attrv.get("datetime", None)
            return dt.isoformat() if dt else None

        case AttrType.OBJECT:
            return {
                "id": attrv["referral__id"],
                "name": attrv["referral__name"],
            }

        case AttrType.GROUP:
            group = Group.objects.get(id=attrv["value"])
            if group:
                return {
                    "id": group.id,
                    "name": group.name,
                }
            else:
                return None

        case AttrType.ROLE:
            role = Role.objects.get(id=attrv["value"])
            if role:
                return {
                    "id": role.id,
                    "name": role.name,
                }
            else:
                return None

        case AttrType.NAMED_OBJECT:
            return {
                attrv["value"]: {
                    "id": attrv["referral__id"],
                    "name": attrv["referral__name"],
                }
            }

        case (
            AttrType.ARRAY_OBJECT
            | AttrType.ARRAY_STRING
            | AttrType.ARRAY_NAMED_OBJECT
            | AttrType.ARRAY_NAMED_OBJECT_BOOLEAN
            | AttrType.ARRAY_GROUP
            | AttrType.ARRAY_ROLE
        ):
            match attr_type:
                case AttrType.ARRAY_NAMED_OBJECT:
                    return [
                        {
                            v["value"]: {
                                "id": v["referral__id"],
                                "name": v["referral__name"],
                            }
                        }
                        for v in children
                        if v.get("value") and v.get("referral__id") and v.get("referral__name")
                    ]

                case AttrType.ARRAY_STRING:
                    return [v["value"] for v in children if v.get("value")]

                case AttrType.ARRAY_OBJECT:
                    return [
                        {"id": v["referral__id"], "name": v["referral__name"]}
                        for v in children
                        if v.get("referral__id") and v.get("referral__name")
                    ]

                case AttrType.ARRAY_GROUP:
                    groups = Group.objects.filter(id__in=[v["value"] for v in children if v])
                    return [{"id": g.id, "name": g.name} for g in groups]

                case AttrType.ARRAY_ROLE:
                    roles = Role.objects.filter(id__in=[v["value"] for v in children if v])
                    return [{"id": r.id, "name": r.name} for r in roles]

    raise ValueError("Invalid attribute type: %s" % type)


def search_entries_with_wide_scan(
    user: User,
    entities: list[int],
    attr_hints: list[AttrHint],
    # FIXME later
    entry_name: str | None = None,
    hint_referral: str | None = None,
    hint_referral_entity_id: int | None = None,
    is_output_all: bool = False,
    limit: int = CONFIG.MAX_LIST_ENTRIES,
    offset: int = 0,
) -> AdvancedSearchResults:
    """
    Simulate advanced search with widely scaning attribute values.
    It will generate high load queries, but the query is so simple so possibly fast.
    """

    attr_names: list[str] = [attr_hint["name"] for attr_hint in attr_hints]

    attrs_prefetch = Prefetch(
        "attrs",
        queryset=Attribute.objects.filter(schema__name__in=attr_names)
        .only("schema")
        .select_related("schema"),
        to_attr="prefetched_attrs",
    )
    entries = (
        Entry.objects.filter(schema__id__in=entities)
        .only("id", "name", "schema")
        .select_related("schema")
        .prefetch_related(attrs_prefetch)[offset:limit]
    )

    # needs an index on name
    attr_values = (
        AttributeValue.objects.filter(parent_attr__schema__name__in=attr_names, is_latest=True)
        .select_related("referral")
        .values(
            "id",
            "value",
            "boolean",
            "date",
            "datetime",
            "parent_attr",
            "referral__id",
            "referral__name",
        )
    )
    attr_values_by_attr: dict[int, dict[str, Any]] = {
        attrv["parent_attr"]: attrv for attrv in attr_values
    }

    attr_values_children = (
        AttributeValue.objects.filter(
            parent_attr__schema__name__in=attr_names, parent_attrv__isnull=False
        )
        .select_related("referral")
        .values("value", "boolean", "parent_attrv", "referral__id", "referral__name")
    )
    attr_values_children_by_parent: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for child in attr_values_children:
        attr_values_children_by_parent[child["parent_attrv"]].append(child)

    values = [
        AdvancedSearchResultValue(
            entity={"id": e.schema.id, "name": e.schema.name},
            entry={"id": e.id, "name": e.name},
            attrs={
                a.schema.name: {
                    "type": a.schema.type,
                    "value": _render_attribute_value_from_dict(
                        a.schema.type,
                        attr_values_by_attr[a.id],
                        attr_values_children_by_parent.get(attr_values_by_attr[a.id]["id"], []),
                    ),
                    "is_readable": True,
                }
                for a in e.prefetched_attrs
                if attr_values_by_attr.get(a.id)
            },
            # dummy
            is_readable=True,
            referrals=[],
        )
        for e in entries
    ]

    return AdvancedSearchResults(
        ret_count=len(values),
        ret_values=values,
    )
