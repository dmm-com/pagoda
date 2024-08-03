"""
XXX A super experimental advanced search module,
as an alternative for elasticsearch based current advanced search.
"""

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from django.db.models import Prefetch

from airone.lib.elasticsearch import AdvancedSearchResults, AdvancedSearchResultValue, AttrHint
from airone.lib.log import Logger
from airone.lib.types import AttrType
from entry.models import Attribute, AttributeValue, Entry
from entry.settings import CONFIG
from user.models import User


# NOTE fetching Group and Role, and data_array will cause N+1
def _render_attribute_value(
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
            if attrv.get("referral__id"):
                return {
                    "id": attrv["referral__id"],
                    "name": attrv["referral__name"],
                }
            else:
                return None

        case AttrType.GROUP:
            if attrv.get("group__id"):
                return {
                    "id": attrv["group__id"],
                    "name": attrv["group__name"],
                }
            else:
                return None

        case AttrType.ROLE:
            if attrv.get("role__id"):
                return {
                    "id": attrv["role__id"],
                    "name": attrv["role__name"],
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
                    return [
                        {"id": v["group__id"], "name": v["group__name"]}
                        for v in children
                        if v.get("group__id") and v.get("group__name")
                    ]

                case AttrType.ARRAY_ROLE:
                    return [
                        {"id": v["role__id"], "name": v["role__name"]}
                        for v in children
                        if v.get("role__id") and v.get("role__name")
                    ]

    raise ValueError("Invalid attribute type: %s" % type)


def search_entries(
    user: User,
    entities: list[int],
    # NOTE only 'name' is supported; FIXME support other hints
    attr_hints: list[AttrHint],
    # FIXME later
    entry_name: str | None = None,
    hint_referral: str | None = None,
    hint_referral_entity_id: int | None = None,
    is_output_all: bool = False,
    limit: int = CONFIG.MAX_LIST_ENTRIES,
    offset: int = 0,
) -> AdvancedSearchResults:
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

    # NOTE django-debug-toolbar doesn't work SQL analytics with concurrent execution
    attr_values_by_attr: dict[int, dict[str, Any]] = {}
    attr_values_children_by_parent: dict[int, list[dict[str, Any]]] = defaultdict(list)
    with ThreadPoolExecutor() as executor:

        def _fetch_attrv() -> dict[int, dict[str, Any]]:
            # TODO better to have indexed fields in AttributeValue
            attr_values = (
                AttributeValue.objects.filter(
                    parent_attrv__isnull=True,
                    is_latest=True,
                    parent_attr__schema__name__in=attr_names,
                )
                .select_related("referral", "group", "role")
                .values(
                    "id",
                    "value",
                    "boolean",
                    "date",
                    "datetime",
                    "parent_attr",
                    "referral__id",
                    "referral__name",
                    "group__id",
                    "group__name",
                    "role__id",
                    "role__name",
                )
            )
            return {attrv["parent_attr"]: attrv for attrv in attr_values}

        def _fetch_attrv_children() -> dict[int, list[dict[str, Any]]]:
            # TODO better to have indexed fields in AttributeValue
            attr_values_children = (
                AttributeValue.objects.filter(
                    parent_attrv__isnull=False, parent_attr__schema__name__in=attr_names
                )
                .select_related("referral", "group", "role")
                .values(
                    "value",
                    "parent_attrv",
                    "referral__id",
                    "referral__name",
                    "group__id",
                    "group__name",
                    "role__id",
                    "role__name",
                )
            )
            attr_values_children_by_parent: dict[int, list[dict[str, Any]]] = defaultdict(list)
            for child in attr_values_children:
                attr_values_children_by_parent[child["parent_attrv"]].append(child)
            return attr_values_children_by_parent

        f1 = executor.submit(_fetch_attrv)
        f2 = executor.submit(_fetch_attrv_children)

        attr_values_by_attr = f1.result()
        attr_values_children_by_parent = f2.result()

    values = [
        AdvancedSearchResultValue(
            entity={"id": e.schema.id, "name": e.schema.name},
            entry={"id": e.id, "name": e.name},
            attrs={
                a.schema.name: {
                    "type": a.schema.type,
                    "value": _render_attribute_value(
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
