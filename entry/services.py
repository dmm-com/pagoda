from typing import Any

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
    make_query,
    make_query_for_simple,
    make_search_results,
    make_search_results_for_simple,
)
from airone.lib.log import Logger
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.models import Attribute, AttributeValue, Entry
from user.models import User

from .settings import CONFIG


class AdvancedSearchService:
    @classmethod
    def search_entries(
        kls,
        user: User,
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
    ) -> AdvancedSearchResults:
        """Main method called from advanced search.

        Do the following:
        1. Create a query for Elasticsearch search. (make_query)
        2. Execute the created query. (execute_query)
        3. Search the reference entry, Check permissions,
           process the search results, and return. (make_search_results)

        Args:
            user (:obj:`str`, optional): User who executed the process
            hint_entity_ids (list(str)): Entity ID specified in the search condition input
            hint_attrs (list(dict[str, str])): Defaults to Empty list.
                A list of search strings and attribute sets
            limit (int): Defaults to 100.
                Maximum number of search results to return
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

        Returns:
            AdvancedSearchResults: As a result of the search,
                the acquired entry and the attribute value of the entry are returned.
        """
        if not hint_attrs:
            hint_attrs = []

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
            )

            # sending request to elasticsearch with making query
            resp = execute_query(query, limit, offset)

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
                limit,
            )
            results.ret_count += search_result.ret_count
            results.ret_values.extend(search_result.ret_values)
            limit -= len(search_result.ret_values)
            offset = max(0, offset - search_result.ret_count)

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
        user: User,
        resp: AdvancedSearchResults,
        join_attrs: list,
        entry_limit: int,
        is_output_all: bool,
        exclude_referrals: list[int] = [],
        include_referrals: list[int] = [],
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

            # Call search_entries() per Entity to apply keyword filters
            matched_results: dict[int, AdvancedSearchResultRecord] = {}
            for entity_id, ref_ids_in_entity in ref_entries_by_entity.items():
                search_result = kls.search_entries(
                    user,
                    [str(entity_id)],
                    hint_attrs,
                    limit=len(ref_ids_in_entity) + 100,
                )
                for record in search_result.ret_values:
                    if record.entry["id"] in ref_ids_in_entity:
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
    def update_documents(kls, entity: Entity, is_update: bool = False):
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
