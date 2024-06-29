"""
XXX A super experimental advanced search module,
as an alternative for elasticsearch based current advanced search.
"""

from django.db.models import Prefetch

from airone.lib.elasticsearch import AdvancedSearchResults, AdvancedSearchResultValue, AttrHint
from airone.lib.log import Logger
from airone.lib.types import AttrType
from entry.models import Attribute, AttributeValue, Entry
from entry.settings import CONFIG
from user.models import User


def _render_attribute_value(
    type: int, values: list[AttributeValue]
) -> str | bool | dict | list | None:
    try:
        attr_type = AttrType(type)
    except ValueError:
        # For compatibility; continue that, and record the error
        Logger.error("Invalid attribute type: %s" % type)
        return None

    match attr_type:
        case AttrType.STRING | AttrType.TEXT:
            return values[0].value

        case AttrType.BOOLEAN:
            return values[0].boolean

        case AttrType.DATE:
            return values[0].date

        case AttrType.DATETIME:
            return values[0].datetime

        case AttrType.OBJECT | AttrType.GROUP | AttrType.ROLE:
            return {
                "id": values[0].referral.id,
                "name": values[0].referral.name,
            }

        case AttrType.NAMED_OBJECT:
            return {
                values[0].key: {
                    "id": values[0].referral.id,
                    "name": values[0].referral.name,
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
            if len([v.value for v in values if v.value]) == 0:
                return []

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

                case AttrType.ARRAY_OBJECT | AttrType.ARRAY_GROUP | AttrType.ARRAY_ROLE:
                    return [
                        {"id": v.referral.id, "name": v.value}
                        for v in values
                        if v.referral.id and v.referral.name
                    ]

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

    attrs_prefetch = Prefetch(
        "attrs",
        queryset=Attribute.objects.filter(schema__name__in=attr_names)
        .prefetch_related(
            Prefetch(
                "values",
                queryset=AttributeValue.objects.filter(is_latest=True).select_related("referral"),
                to_attr="prefetched_values",
            )
        )
        .select_related("schema"),
        to_attr="prefetched_attrs",
    )
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
            },
            # dummy
            is_readable=True,
            referrals=[],
        )
        for e in entries
    ]

    # NOTE without prefetch; will cause N+1, for benchmarking
    # entries = Entry.objects.filter(schema__id__in=entities)
    # values = [
    #     AdvancedSearchResultValue(
    #         entity={"id": e.schema.id, "name": e.schema.name},
    #         entry={"id": e.id, "name": e.name},
    #         attrs={
    #             a.name: {
    #                 "type": a.schema.type,
    #                 "value": a.values.filter(is_latest=True),
    #                 "is_readable": True,
    #             }
    #             for a in e.attrs.filter(name__in=attr_names)
    #         },
    #         # dummy
    #         is_readable=True,
    #         referrals=[],
    #     )
    #     for e in entries
    # ]

    return AdvancedSearchResults(
        ret_count=len(values),
        ret_values=values,
    )
