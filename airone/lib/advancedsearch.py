"""
XXX A super experimental advanced search module,
as an alternative for elasticsearch based current advanced search.
"""

from django.db.models import Prefetch

from airone.lib.elasticsearch import AdvancedSearchResults, AdvancedSearchResultValue, AttrHint
from entity.models import EntityAttr
from entry.models import Attribute, AttributeValue, Entry
from entry.settings import CONFIG
from user.models import User


def query(
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
        queryset=Attribute.objects.filter(name__in=attr_names).prefetch_related(
            Prefetch(
                "values",
                queryset=AttributeValue.objects.filter(is_latest=True),
                to_attr="prefetched_values",
            ),
            Prefetch("schema", queryset=EntityAttr.objects.all(), to_attr="prefetched_schema"),
        ),
        to_attr="prefetched_attrs",
    )
    entries = (
        Entry.objects.filter(schema__id__in=entities)
        .prefetch_related("schema")
        .prefetch_related(attrs_prefetch)
    )[offset:limit]

    values = [
        AdvancedSearchResultValue(
            entity={"id": e.schema.id, "name": e.schema.name},
            entry={"id": e.id, "name": e.name},
            attrs={
                a.name: {
                    "type": a.prefetched_schema.type,
                    "value": a.prefetched_values,
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
