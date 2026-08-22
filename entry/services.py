import json
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db.models import Prefetch
from elasticsearch import NotFoundError

from airone.lib.acl import ACLType
from airone.lib.elasticsearch import (
    ESS,
    AdvancedSearchResultRecord,
    AdvancedSearchResultRecordAttr,
    AdvancedSearchResults,
    AttrHint,
    EntryHint,
    execute_query,
    make_attr_sort_clauses,
    make_query,
    make_query_for_simple,
    make_search_results,
    make_search_results_for_simple,
)
from airone.lib.http import DRFRequest
from airone.lib.import_preview import PreviewCollector
from airone.lib.log import Logger
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.api_v2.serializers import EntryCreateSerializer, EntryUpdateSerializer
from entry.models import Attribute, AttributeValue, Entry
from job.models import Job, JobOperation, JobStatus
from trigger.models import TriggerCondition
from user.models import User

from .settings import CONFIG

if TYPE_CHECKING:
    from entry.api_v2.serializers import AdvancedSearchJoinAttrInfo


class AdvancedSearchService:
    @classmethod
    def search_entries(
        kls,
        user: User | None,
        hint_entity_ids: list[str],
        hint_attrs: list[AttrHint] | None = None,
        limit: int = CONFIG.MAX_LIST_ENTRIES,
        entry_name: str | None = None,
        hint_referral: str | None = None,
        is_output_all: bool = False,
        hint_referral_entity_id: int | None = None,
        offset: int = 0,
        hint_entry: EntryHint | None = None,
        allow_missing_attributes: bool = False,
        exclude_referrals: list[int] = [],
        include_referrals: list[int] = [],
        entry_ids: list[int] | None = None,
        retrieve_all: bool = False,
        sort_target_attrname: str | None = None,
        sort_order: str = "asc",
        sort_target_attr_type: int | None = None,
    ) -> AdvancedSearchResults:
        """Main method called from advanced search.

        Do the following:
        1. Create a query for Elasticsearch search. (make_query)
        2. Execute the created query. (execute_query)
        3. Search the reference entry, Check permissions,
           process the search results, and return. (make_search_results)

        Args:
            user (User | None): User who executed the process
            hint_entity_ids (list(str)): Entity ID specified in the search condition input
            hint_attrs (list(dict[str, str])): Defaults to Empty list.
                A list of search strings and attribute sets
            limit (int): Defaults to 100.
                Maximum number of search results to return.
                Ignored when retrieve_all=True.
            entry_name (str): Search string for entry name
            hint_referral (str): Defaults to None.
                Input value used to refine the reference entry.
                Use only for advanced searches.
            hint_referral_entity_id (int): Defaults to None.
                Input value used to refine the reference Entity.
                Use only for advanced searches.
            is_output_all (bool): Defaults to False.
                Flag to output all attribute values.
            offset (int): Defaults to 0.
                The number of offset to get a part of a large amount of search results
            hint_entry (AttrHint | None): Defaults to None.
                Input value used to refine the entry.
            allow_missing_attributes (bool, optional): Defaults to False.
                If True, entries that do not have attributes specified in hint_attrs
                (without a keyword) will be included in the search results.
                If False, attributes specified in hint_attrs (without a keyword)
                must exist in the entry.
            exclude_referrals (list(int)): Default []
                This has Model ID's list that want to exclude for referral items.
            include_referrals (list(int)): Default []
                If it's set, this method only targets items that are referred by
                items of specified Models.
            entry_ids (list(int) | None): Default None.
                When provided, restricts search results to entries with these IDs.
                The effective limit is automatically set to len(entry_ids) to ensure
                all specified entries are returned.
            retrieve_all (bool): Defaults to False.
                When True, returns all entries that match the conditions, ignoring
                the `limit` argument. The effective upper bound is the Elasticsearch
                `max_result_window` (settings.ES_CONFIG["MAXIMUM_RESULTS_NUM"]).
                If the matched count exceeds this bound the result is silently
                truncated and a warning is logged.

        Returns:
            AdvancedSearchResults: As a result of the search,
                the acquired entry and the attribute value of the entry are returned.
        """
        if not hint_attrs:
            hint_attrs = []

        sort_clauses: list[dict[str, Any]] | None = None
        if sort_target_attrname:
            sort_clauses = make_attr_sort_clauses(
                sort_target_attrname, sort_order, sort_target_attr_type
            )

        if retrieve_all:
            # Use the Elasticsearch max_result_window as the upper bound. Beyond this
            # value ES rejects the query, and execute_query also clamps to the same
            # ceiling — so this is the largest size we can request in a single shot.
            limit = settings.ES_CONFIG["MAXIMUM_RESULTS_NUM"]

        results = AdvancedSearchResults(
            ret_count=0,
            ret_values=[],
        )
        entities = Entity.objects.filter(id__in=hint_entity_ids, is_active=True).prefetch_related(
            Prefetch(
                "attrs",
                queryset=EntityAttr.objects.filter(
                    name__in=[h.name for h in hint_attrs], is_active=True
                ),
                to_attr="prefetch_attrs",
            )
        )
        for entity in entities:
            # Check for has permission to Entity
            if user and not user.has_permission(entity, ACLType.Readable):
                continue

            # Check for has permission to EntityAttr
            for hint_attr in hint_attrs:
                hint_entity_attr = next(
                    filter(lambda x: x.name == hint_attr.name, entity.prefetch_attrs), None
                )
                # NOTE modify is_readable as a side-effect, will be expected by other logics
                hint_attr.is_readable = (
                    True
                    if (
                        user is None
                        or (
                            hint_entity_attr
                            and user.has_permission(hint_entity_attr, ACLType.Readable)
                        )
                    )
                    else False
                )

            # make query for elasticsearch to retrieve data user wants
            query = make_query(
                entity,
                hint_attrs,
                entry_name,
                hint_referral,
                hint_referral_entity_id,
                hint_entry,
                allow_missing_attributes=allow_missing_attributes,
                exclude_referrals=exclude_referrals,
                include_referrals=include_referrals,
                entry_ids=entry_ids,
            )

            # When entry_ids is specified, use its length as the effective limit to ensure
            # all requested entries are returned regardless of the default limit.
            effective_limit = len(entry_ids) if entry_ids else limit

            # sending request to elasticsearch with making query
            resp = execute_query(query, effective_limit, offset, sort=sort_clauses)

            tmp_hint_attrs = [attr.model_copy(deep=True) for attr in hint_attrs]
            # Check for has permission to EntityAttr, when is_output_all flag
            if is_output_all:
                for entity_attr in entity.attrs.filter(is_active=True):
                    if entity_attr.name not in [x.name for x in tmp_hint_attrs if x.name]:
                        tmp_hint_attrs.append(
                            AttrHint(
                                name=entity_attr.name,
                                is_readable=True
                                if (
                                    user is None
                                    or user.has_permission(entity_attr, ACLType.Readable)
                                )
                                else False,
                            )
                        )

            # retrieve data from database on the basis of the result of elasticsearch
            search_result = make_search_results(
                user,
                resp,
                tmp_hint_attrs,
                hint_referral,
                effective_limit,
            )
            results.ret_count += search_result.ret_count
            results.ret_values.extend(search_result.ret_values)
            if not entry_ids and not retrieve_all:
                limit -= len(search_result.ret_values)
                offset = max(0, offset - search_result.ret_count)

        if retrieve_all and results.ret_count > len(results.ret_values):
            # When retrieve_all=True, the caller expects every matched entry. If the
            # matched total exceeds the Elasticsearch max_result_window, the result is
            # silently truncated. Surface this so the truncation does not go unnoticed.
            Logger.warning(
                "search_entries(retrieve_all=True) truncated: matched=%d returned=%d "
                "(max_result_window=%d)",
                results.ret_count,
                len(results.ret_values),
                settings.ES_CONFIG["MAXIMUM_RESULTS_NUM"],
            )

        return results

    @classmethod
    def search_entries_for_simple(
        kls,
        hint_attr_value: str,
        hint_entity_name: str | None = None,
        exclude_entity_names: list[str] = [],
        limit: int = CONFIG.MAX_LIST_ENTRIES,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Method called from simple search.
        Returns the count and values of entries with hint_attr_value.

        Do the following:
        1. Create a query for Elasticsearch search. (make_query_for_attrv)
        2. Execute the created query. (execute_query)
        3. Process the search results, and return. (make_search_results_for_attrv)

        Args:
            hint_attr_value (str): Required.
                Search string for AttributeValue
            hint_entity_name (str): Defaults to None.
                Search string for Entity Name
            exclude_entity_names (list[str]): Defaults to [].
                Entity name string list to exclude from search
            limit (int): Defaults to 100.
                Maximum number of search results to return
            offset (int): Defaults to 0.
                Number of offset

        Returns:
            dict[str, any]: As a result of the search,
                the acquired entry and the attribute value of the entry are returned.
            {
                'ret_count': (int),
                'ret_values': [
                    'id': (str),
                    'name': (str),
                    'attr': (str),
                ],
            }

        """
        # by elasticsearch limit, from + size must be less than or equal to max_result_window
        if offset + limit > settings.ES_CONFIG["MAXIMUM_RESULTS_NUM"]:
            return {
                "ret_count": 0,
                "ret_values": [],
            }

        query = make_query_for_simple(
            hint_attr_value, hint_entity_name, exclude_entity_names, offset
        )

        resp = execute_query(query, limit)

        return make_search_results_for_simple(resp)

    @classmethod
    def _extract_ref_ids(kls, attr: AdvancedSearchResultRecordAttr) -> list[int]:
        """
        Retrun a list of referenced Entry IDs from an AdvancedSearchResultRecordAttr dict.
        """
        attr_type = attr.get("type")
        attr_value = attr.get("value")

        if not attr_type or not attr_value:
            return []

        def _valid_id(v: Any) -> int | None:
            # return only int and positive value, because Entry IDs are positive integers.
            return v if isinstance(v, int) and v > 0 else None

        if attr_type in (AttrType.OBJECT, AttrType.GROUP, AttrType.ROLE):
            if isinstance(attr_value, dict):
                ref_id = _valid_id(attr_value.get("id"))
                if ref_id is not None:
                    return [ref_id]
            return []

        if attr_type == AttrType.NAMED_OBJECT:
            if isinstance(attr_value, dict):
                for _k, v in attr_value.items():
                    if isinstance(v, dict):
                        ref_id = _valid_id(v.get("id"))
                        if ref_id is not None:
                            return [ref_id]
            return []

        if attr_type & AttrType._ARRAY:
            if not isinstance(attr_value, list):
                return []
            ids: list[int] = []
            if attr_type & AttrType._NAMED:
                # ARRAY_NAMED_OBJECT: This expects following data structure
                # [{"key": {"id": ..., "name": ...}}]
                for item in [x for x in attr_value if isinstance(x, dict)]:
                    for v in [v for v in item.values() if isinstance(v, dict)]:
                        ref_id = _valid_id(v.get("id"))
                        if ref_id is not None:
                            ids.append(ref_id)
            else:
                # ARRAY_OBJECT / ARRAY_GROUP / ARRAY_ROLE
                # This expects following data structure
                # [{"id": ..., "name": ...}]
                for item in [x for x in attr_value if isinstance(x, dict)]:
                    ref_id = _valid_id(item.get("id"))
                    if ref_id is not None:
                        ids.append(ref_id)
            return ids

        return []

    # Default value for joined attrs when there is no referral or it does not match the filter.
    # Initialized as STRING with an empty string because views.py
    # requires is_readable / type / value.
    _EMPTY_ATTR: AdvancedSearchResultRecordAttr = {
        "type": AttrType.STRING,
        "value": "",
        "is_readable": True,
    }

    @classmethod
    def apply_join_attrs(
        kls,
        user: User | None,
        resp: AdvancedSearchResults,
        join_attrs: list["AdvancedSearchJoinAttrInfo"],
    ) -> AdvancedSearchResults:
        """Join referred Entry attributes based on join_attrs and filter/expand the results.

        This is shared logic called from both AdvancedSearchAPI.post() in views.py
        and export_search_result_v2() in tasks.py.

        For each join_attr:
        1. Collect referred Entry IDs from the current search results
        2. Group by Entity in the DB and apply filters via search_entries()
        3. Attach attributes of entries that passed the filter under the key
           join_attr.name.subattr_name
        4. Expand ARRAY-type attrs into one row per referral
        """
        for join_attr in join_attrs:
            has_filter = any(a.keyword or a.filter_key for a in join_attr.attrinfo)
            hint_attrs = [
                AttrHint(
                    name=a.name,
                    keyword=a.keyword,
                    filter_key=a.filter_key,
                )
                for a in join_attr.attrinfo
            ]

            # Collect referred Entry IDs from all results and group by Entity
            all_ref_ids: set[int] = set()
            for entry_info in resp.ret_values:
                attr = entry_info.attrs.get(join_attr.name)
                if attr:
                    all_ref_ids.update(kls._extract_ref_ids(attr))

            # Fetch Entity IDs from DB and group them (batch lookup)
            ref_entries_by_entity: dict[int, list[int]] = {}
            if all_ref_ids:
                for ref_entry in Entry.objects.filter(
                    id__in=all_ref_ids, is_active=True
                ).select_related("schema"):
                    ref_entries_by_entity.setdefault(ref_entry.schema_id, []).append(ref_entry.id)

            # Call search_entries() per Entity to apply keyword filters.
            # Use entry_ids to restrict the search to only the known ref IDs, avoiding the
            # limit-based data loss that occurs when an entity has more entries than the limit.
            # Process in chunks of 1000 to keep ES query size manageable.
            CHUNK_SIZE = 1000
            matched_results: dict[int, AdvancedSearchResultRecord] = {}
            for entity_id, ref_ids_in_entity in ref_entries_by_entity.items():
                for i in range(0, len(ref_ids_in_entity), CHUNK_SIZE):
                    chunk = ref_ids_in_entity[i : i + CHUNK_SIZE]
                    search_result = kls.search_entries(
                        user,
                        [str(entity_id)],
                        hint_attrs,
                        entry_ids=chunk,
                    )
                    for record in search_result.ret_values:
                        matched_results[record.entry["id"]] = record

            # Process each entry and build new_ret_values
            new_ret_values: list[AdvancedSearchResultRecord] = []
            for entry_info in resp.ret_values:
                attr = entry_info.attrs.get(join_attr.name)
                attr_type = attr.get("type") if attr else None
                is_array = bool(attr_type and (attr_type & AttrType._ARRAY))
                ref_ids = kls._extract_ref_ids(attr) if attr else []

                if is_array:
                    # ARRAY type: expand into one row per referral
                    expanded = False
                    for ref_id in ref_ids:
                        matched = matched_results.get(ref_id)
                        if has_filter and matched is None:
                            continue  # this ref did not match the filter → skip
                        new_info = entry_info.model_copy(deep=True)
                        if matched:
                            for attr_name, attr_val in matched.attrs.items():
                                new_info.attrs[f"{join_attr.name}.{attr_name}"] = attr_val
                        else:
                            for a in join_attr.attrinfo:
                                new_info.attrs[f"{join_attr.name}.{a.name}"] = kls._EMPTY_ATTR
                        new_ret_values.append(new_info)
                        expanded = True

                    if not expanded:
                        # No referrals, or all excluded by filter
                        if not has_filter:
                            # No filter → keep the entry as one row (joined attrs are empty)
                            new_info = entry_info.model_copy(deep=True)
                            for a in join_attr.attrinfo:
                                new_info.attrs[f"{join_attr.name}.{a.name}"] = kls._EMPTY_ATTR
                            new_ret_values.append(new_info)
                        # has_filter: exclude the entry
                else:
                    # Non-ARRAY type (OBJECT, NAMED_OBJECT, etc.)
                    single_ref_id: int | None = ref_ids[0] if ref_ids else None
                    if single_ref_id:
                        matched = matched_results.get(single_ref_id)
                        if has_filter and matched is None:
                            continue  # filter did not match → exclude the entry
                        new_info = entry_info.model_copy(deep=True)
                        if matched:
                            for attr_name, attr_val in matched.attrs.items():
                                new_info.attrs[f"{join_attr.name}.{attr_name}"] = attr_val
                        else:
                            for a in join_attr.attrinfo:
                                new_info.attrs[f"{join_attr.name}.{a.name}"] = kls._EMPTY_ATTR
                        new_ret_values.append(new_info)
                    else:
                        # No referral
                        if not has_filter:
                            new_info = entry_info.model_copy(deep=True)
                            for a in join_attr.attrinfo:
                                new_info.attrs[f"{join_attr.name}.{a.name}"] = kls._EMPTY_ATTR
                            new_ret_values.append(new_info)
                        # has_filter and no referral → exclude the entry

            resp = AdvancedSearchResults(
                ret_count=len(new_ret_values),
                ret_values=new_ret_values,
            )

        return resp

    @classmethod
    def get_all_es_docs(kls) -> dict[str, Any]:
        return ESS().search(body={"query": {"match_all": {}}})

    @classmethod
    def update_documents(kls, entity: Entity, is_update: bool = False) -> None:
        es = ESS()
        query = {
            "query": {
                "nested": {
                    "path": "entity",
                    "query": {"match": {"entity.id": entity.id}},
                }
            }
        }
        res = es.search(body=query)

        results_from_es = [x["_source"] for x in res["hits"]["hits"]]
        entry_ids_from_es = [int(x["_id"]) for x in res["hits"]["hits"]]

        entity_attrs = entity.attrs.filter(is_active=True)

        value_prefetch = Prefetch(
            "values",
            queryset=AttributeValue.objects.filter(is_latest=True)
            .select_related("referral", "group", "role")
            .prefetch_related("data_array__referral", "data_array__group", "data_array__role"),
            to_attr="prefetch_values",
        )
        attr_prefetch = Prefetch(
            "attrs",
            queryset=Attribute.objects.filter(schema__in=entity_attrs, is_active=True)
            .select_related("schema")
            .prefetch_related(value_prefetch),
            to_attr="prefetch_attrs",
        )

        # This targets following Entries that belong to specified Entity
        entry_list = (
            Entry.objects.filter(schema=entity, is_active=True)
            .select_related("schema")
            .prefetch_related(attr_prefetch)
        )

        # check & update
        start_pos = 0
        exists: bool = True
        while exists:
            exists = False
            register_docs = []
            for entry in entry_list[start_pos : start_pos + 1000]:
                exists = True
                es_doc = entry.get_es_document(entity_attrs=entity_attrs)
                if es_doc not in results_from_es:
                    if not is_update:
                        Logger.warning("Update elasticsearch document (entry_id: %s)" % entry.id)

                    # Elasticsearch bulk API format is add meta information and data pairs as sets.
                    # [
                    #     {"index": {"_id": 1}}
                    #     {"name": {...}, "entity": {...}, "attr": {...}, "is_readable": {...}}
                    #     {"index": {"_id": 2}}
                    #     {"name": {...}, "entity": {...}, "attr": {...}, "is_readable": {...}}
                    # ]
                    register_docs.append({"index": {"_id": entry.id}})
                    register_docs.append(es_doc)

            if register_docs:
                es.bulk(body=register_docs)
            start_pos = start_pos + 1000

        # delete
        entry_ids_from_db = Entry.objects.filter(schema=entity, is_active=True).values_list(
            "id", flat=True
        )
        for entry_id in set(entry_ids_from_es) - set(entry_ids_from_db):
            if not is_update:
                Logger.warning("Delete elasticsearch document (entry_id: %s)" % entry.id)
            try:
                es.delete(id=entry_id)
            except NotFoundError:
                pass

        es.indices.refresh()


class EntryImportPreviewService:
    """Reports what an item import file would do, without doing any of it.

    Applying an item import also reindexes Elasticsearch and queues webhook and
    trigger jobs, so its preview cannot lean on a transaction to undo itself: it
    must simply not write. What it does instead is run the import's own decisions
    -- the same serializers for validation, the same Attribute.is_updated() for
    change detection -- and stop before the write.
    """

    @classmethod
    def build(
        kls,
        job: "Job",
        user: User,
        entity: Entity,
        entries: list[dict[str, Any]],
        raw_entries: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Return the preview payload, or None when the job was canceled."""
        context = {"request": DRFRequest(user)}
        collector = PreviewCollector()
        total_count = len(entries)

        for index, entry_data in enumerate(entries):
            job.text = "Now previewing... (progress: [%5d/%5d])" % (index + 1, total_count)
            job.save(update_fields=["text"])

            if job.is_canceled():
                return None

            raw_entry = raw_entries[index] if index < len(raw_entries) else {}
            _preview_one_entry(user, entity, entry_data, raw_entry, context, collector)

        return collector.payload()

    @classmethod
    def load_baselines(kls, job: "Job") -> dict[str, dict[str, Any]] | None:
        return _load_preview_baselines(job)

    @classmethod
    def is_stale(
        kls,
        entry: Entry,
        entry_data: dict[str, Any],
        baselines: dict[str, dict[str, Any]] | None,
    ) -> bool:
        return _is_stale(entry, entry_data, baselines)

    @classmethod
    def latest_value_ids(kls, entry: Entry, entity_attr_ids: list[int]) -> dict[str, int]:
        return _latest_value_ids(entry, entity_attr_ids)


def _render_import_value(value: Any) -> str:
    """Render a value as the user wrote it in the import file."""
    match value:
        case None:
            return ""
        case bool():
            return "true" if value else "false"
        case list():
            return ", ".join(_render_import_value(x) for x in value)
        case dict():
            return ", ".join("%s: %s" % (k, _render_import_value(v)) for k, v in value.items())
        case _:
            return str(value)


def _render_stored_value(attr: Attribute) -> str:
    """Render an attribute's current value.

    Attribute.get_latest_value() creates an empty AttributeValue when there is
    none, which a preview must never do, so the latest value is read directly.
    """
    attrv = attr.values.filter(is_latest=True).last()
    if attrv is None:
        return ""
    return _render_import_value(attrv.get_value())


def _unresolved_referrals(raw_value: Any, converted_value: Any) -> list[str]:
    """Names the importer could not resolve, reported as 0 by the serializer.

    A reference that cannot be resolved is silently stored as an empty value, so
    a preview that did not surface it would hide the import's most damaging
    failure mode.
    """
    match (raw_value, converted_value):
        case (list(), list()) if len(raw_value) == len(converted_value):
            return [
                name
                for raw, converted in zip(raw_value, converted_value)
                for name in _unresolved_referrals(raw, converted)
            ]
        case (dict(), dict()):
            # named object: {"name": ..., "id": <resolved>} against {"<name>": "<referral>"}
            if converted_value.get("id") == 0:
                return [_render_import_value(list(raw_value.values())[0])]
            return []
        case (_, 0) if raw_value:
            return [_render_import_value(raw_value)]
        case _:
            return []


def _render_serializer_errors(errors: Any) -> str:
    """Flatten a serializer's errors onto one line, keeping the message.

    A nested serializer reports a dict keyed by field, and a list of them keyed
    by row index. Walking only the top level turns "attrs: {0: {'id': [...]}}"
    into "attrs: 0" -- everything except the part the user needs.
    """
    match errors:
        case dict():
            return "; ".join(
                "%s: %s" % (key, _render_serializer_errors(value)) for key, value in errors.items()
            )
        case list() | tuple():
            return ", ".join(_render_serializer_errors(x) for x in errors)
        case _:
            return str(errors)


def _preview_one_entry(
    user: User,
    entity: Entity,
    entry_data: dict[str, Any],
    raw_entry: dict[str, Any],
    context: dict[str, Any],
    collector: PreviewCollector,
) -> None:
    entry_data = dict(entry_data, schema=entity)
    name = entry_data["name"]

    # Identify the Item the import would touch, exactly as import_entries_v2 does.
    entry: Entry | None = None
    if entry_data.get("id") is not None:
        entry = Entry.objects.filter(id=entry_data["id"], schema=entity, is_active=True).first()
    if not entry:
        entry = Entry.objects.filter(name=name, schema=entity, is_active=True).first()

    # Run the very serializer the import runs, but stop before save(): validation
    # errors are reported here instead of being logged and counted as a failure.
    serializer: EntryUpdateSerializer | EntryCreateSerializer = (
        EntryUpdateSerializer(instance=entry, data=entry_data, context=context)
        if entry
        else EntryCreateSerializer(data=entry_data, context=context)
    )
    if not serializer.is_valid():
        collector.add(
            kind="Item",
            name=name,
            action="error",
            reason=_render_serializer_errors(serializer.errors),
        )
        return

    warnings = _collect_unresolved(entry_data, raw_entry)
    changes, denied = _collect_attr_changes(user, entity, entry, entry_data, raw_entry)

    # Importing fires triggers, which change values the file never mentions.
    # Read-only: this asks which actions would match, it does not run them.
    will_invoke_trigger = bool(
        TriggerCondition.get_invoked_actions(entity, entry_data.get("attrs", []))
    )

    if entry is None:
        collector.add(
            kind="Item",
            name=name,
            action="create",
            reason="; ".join(warnings) or None,
            changes=changes,
            will_invoke_trigger=will_invoke_trigger,
            # Recorded even for a creation, so that an item somebody else creates
            # under this name in the meantime is not silently updated instead.
            baseline={"entry_id": None, "values": {}},
        )
        return

    if entry.name != name:
        changes.insert(0, {"field": "name", "before": entry.name, "after": name})

    if not changes and denied:
        # Reporting this as "unchanged" would be true but misleading: the file
        # does ask for a change, the user just cannot make it.
        collector.add(
            kind="Item",
            name=name,
            action="skip",
            reason="permission_denied",
            will_invoke_trigger=will_invoke_trigger,
        )
        return

    collector.add(
        kind="Item",
        name=name,
        action="update" if changes else "unchanged",
        reason="; ".join(warnings) or None,
        changes=changes,
        will_invoke_trigger=will_invoke_trigger,
        baseline=_entry_baseline(entry, entry_data),
    )


def _entry_baseline(entry: Entry, entry_data: dict[str, Any]) -> dict[str, Any]:
    """Fingerprint the values this row would overwrite.

    The import compares it against the values it finds, so that a row someone
    else changed in the meantime is not overwritten on the strength of a preview
    that no longer describes it.
    """
    return {
        "entry_id": entry.id,
        "values": _latest_value_ids(entry, [int(x["id"]) for x in entry_data.get("attrs", [])]),
    }


def _latest_value_ids(entry: Entry, entity_attr_ids: list[int]) -> dict[str, int]:
    latest: dict[str, int] = {}
    for attr in entry.attrs.filter(schema__id__in=entity_attr_ids, is_active=True):
        attrv = attr.values.filter(is_latest=True).last()
        latest[str(attr.schema_id)] = attrv.id if attrv else 0
    return latest


def _collect_unresolved(entry_data: dict[str, Any], raw_entry: dict[str, Any]) -> list[str]:
    raw_by_name = {x["name"]: x.get("value") for x in raw_entry.get("attrs", [])}
    warnings: list[str] = []
    for attr_data in entry_data.get("attrs", []):
        unresolved = _unresolved_referrals(raw_by_name.get(attr_data["name"]), attr_data["value"])
        if unresolved:
            warnings.append(
                "%s: 参照先が見つかりません (%s)" % (attr_data["name"], ", ".join(unresolved))
            )
    return warnings


def _collect_attr_changes(
    user: User,
    entity: Entity,
    entry: Entry | None,
    entry_data: dict[str, Any],
    raw_entry: dict[str, Any],
) -> tuple[list[dict[str, str | None]], bool]:
    """Return the differences the import would apply, and whether any were withheld.

    An attribute the user cannot write is silently left alone by the import, so
    the preview has to know the difference between "nothing to do" and "not
    allowed to do it".
    """
    raw_by_name = {x["name"]: x.get("value") for x in raw_entry.get("attrs", [])}
    attrs_data = entry_data.get("attrs", [])
    changes: list[dict[str, str | None]] = []
    denied = False

    for entity_attr in entity.attrs.filter(is_active=True):
        attr_data = next((x for x in attrs_data if int(x["id"]) == entity_attr.id), None)
        if attr_data is None:
            continue

        after = _render_import_value(raw_by_name.get(attr_data["name"]))

        attr: Attribute | None = (
            entry.attrs.filter(schema=entity_attr, is_active=True).first() if entry else None
        )
        if attr is None:
            # The import would create the attribute; anything non-empty is a change.
            if after:
                changes.append({"field": entity_attr.name, "before": None, "after": after})
            continue

        if not user.has_permission(attr, ACLType.Writable):
            denied = denied or attr.is_updated(attr_data["value"])
            continue

        if attr.is_updated(attr_data["value"]):
            changes.append(
                {
                    "field": entity_attr.name,
                    "before": _render_stored_value(attr),
                    "after": after,
                }
            )

    return changes, denied


def _load_preview_baselines(job: Job) -> dict[str, dict[str, Any]] | None:
    """Read the values a preview recorded, when the import was started from one.

    Without a preview job there is nothing to compare against and the import
    behaves exactly as it always has. The same is true row by row: a preview of
    a file long enough to be truncated records no values for the rows it could
    not list, and those rows import the way they always have.
    """
    preview_job_id = json.loads(job.params).get("preview_job_id")
    if not preview_job_id:
        return None

    preview_job = Job.objects.filter(
        id=preview_job_id, user=job.user, operation=JobOperation.IMPORT_ENTRY_PREVIEW
    ).first()
    if preview_job is None or preview_job.status != JobStatus.DONE:
        return None

    try:
        payload = preview_job.get_cache()
    except OSError:
        return None

    return {row["name"]: row["baseline"] for row in payload["rows"] if row.get("baseline")}


def _is_stale(
    entry: Entry, entry_data: dict[str, Any], baselines: dict[str, dict[str, Any]] | None
) -> bool:
    if baselines is None:
        return False

    baseline = baselines.get(entry_data["name"])
    if baseline is None:
        return False

    # The preview described a different item than the one the import found --
    # either it was going to create this name, or it matched something else.
    if baseline["entry_id"] != entry.id:
        return True

    current = _latest_value_ids(entry, [int(x["id"]) for x in entry_data.get("attrs", [])])
    return current != baseline["values"]
