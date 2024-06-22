"""
XXX A super experimental advanced search module,
as an alternative for elasticsearch based current advanced search.
"""

from airone.lib.elasticsearch import AdvancedSearchResults, AdvancedSearchResultValue, AttrHint
from entry.models import Entry


def query(
    entities: list[int],
    attr_hints: list[AttrHint],
    # FIXME later
    entry: str | None = None,
    referral: str | None = None,
    referral_entity_id: int | None = None,
) -> AdvancedSearchResults:
    # XXX try prefetch

    # FIXME fetch if entities is not empty
    entries = Entry.objects.filter(schema__id__in=entities)
    # attributes: list[Attribute] = list(chain.from_iterable([
    #   e.attrs.filter(name__in=[attr_hint["name"] for attr_hint in attr_hints])
    #   for e
    #   in entries
    # ]))
    # values = list(chain.from_iterable([
    #   a.values.all()
    #   for a
    #   in attributes
    # ]))

    values = [
        AdvancedSearchResultValue(
            entity={"id": e.schema.id, "name": e.schema.name},
            entry={"id": e.id, "name": e.name},
            attrs={
                a.name: {
                    "type": a.schema.type,
                    "value": a.values.filter(is_latest=True),
                    "is_readable": True,
                }
                for a in e.attrs.filter(name__in=[attr_hint["name"] for attr_hint in attr_hints])
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
