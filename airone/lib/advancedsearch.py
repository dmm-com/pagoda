"""
XXX A super experimental advanced search module,
as an alternative for elasticsearch based current advanced search.
"""

import operator
from functools import reduce

from django.db.models import Prefetch, Q

from airone.lib.elasticsearch import AdvancedSearchResults, AdvancedSearchResultValue, AttrHint
from airone.lib.log import Logger
from airone.lib.types import AttrType
from entry.models import Attribute, AttributeValue, Entry
from entry.settings import CONFIG
from group.models import Group
from role.models import Role
from user.models import User


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
            return attrv.date

        case AttrType.DATETIME:
            return attrv.datetime

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
                values[0].key: {
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
            values = attrv.data_array.all()

            match attr_type:
                case AttrType.ARRAY_NAMED_OBJECT:
                    return [
                        {
                            v.key: {
                                "id": v.referral.id,
                                "name": v.referral.name,
                            }
                        }
                        for v in values
                        if v.key and v.referral.id and v.referral.name
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

    # TODO flexible query builder based on entity attrs
    # data_array_prefetch = Prefetch(
    #     "data_array",
    #     queryset=AttributeValue.objects.all(),
    #     to_attr="prefetched_data_array",
    # )
    attrv_prefetch = Prefetch(
        "values",
        queryset=AttributeValue.objects.filter(attrv_conditions).select_related("referral"),
        to_attr="prefetched_values",
    )
    attrs_prefetch = Prefetch(
        "attrs",
        queryset=Attribute.objects.filter(schema__name__in=attr_names)
        .prefetch_related(attrv_prefetch)
        .select_related("schema"),
        to_attr="prefetched_attrs",
    )
    # FIXME get total count
    entries = (
        Entry.objects.filter(schema__id__in=entities)
        .select_related("schema")
        .prefetch_related(attrs_prefetch)
    )[offset:limit]

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
