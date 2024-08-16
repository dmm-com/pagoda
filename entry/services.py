from copy import deepcopy
from typing import Any

from django.conf import settings
from django.db.models import Prefetch

from airone.lib.acl import ACLType
from airone.lib.elasticsearch import (
    ESS,
    AdvancedSearchResults,
    AttrHint,
    execute_query,
    make_query,
    make_query_for_simple,
    make_search_results,
    make_search_results_for_simple,
)
from airone.lib.log import Logger
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
                    name__in=[h["name"] for h in hint_attrs], is_active=True
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
                if "name" not in hint_attr:
                    continue

                hint_entity_attr = next(
                    filter(lambda x: x.name == hint_attr["name"], entity.prefetch_attrs), None
                )
                hint_attr["is_readable"] = (
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
                entity, hint_attrs, entry_name, hint_referral, hint_referral_entity_id
            )

            # sending request to elasticsearch with making query
            resp = execute_query(query, limit, offset)

            if "status" in resp and resp["status"] == 404:
                continue

            tmp_hint_attrs = deepcopy(hint_attrs)
            # Check for has permission to EntityAttr, when is_output_all flag
            if is_output_all:
                for entity_attr in entity.attrs.filter(is_active=True):
                    if entity_attr.name not in [x["name"] for x in tmp_hint_attrs if "name" in x]:
                        tmp_hint_attrs.append(
                            {
                                "name": entity_attr.name,
                                "is_readable": True
                                if (
                                    user is None
                                    or user.has_permission(entity_attr, ACLType.Readable)
                                )
                                else False,
                            }
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

        if "status" in resp and resp["status"] == 404:
            return {
                "ret_count": 0,
                "ret_values": [],
            }

        return make_search_results_for_simple(resp)

    @classmethod
    def get_all_es_docs(kls) -> dict[str, Any]:
        return ESS().search(body={"query": {"match_all": {}}}, ignore=[404])

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

        value_prefetch = Prefetch(
            "values",
            queryset=AttributeValue.objects.filter(is_latest=True)
            .select_related("referral")
            .prefetch_related("data_array__referral"),
            to_attr="prefetch_values",
        )
        attr_prefetch = Prefetch(
            "attrs",
            queryset=Attribute.objects.filter(is_active=True).prefetch_related(
                "schema", value_prefetch
            ),
            to_attr="prefetch_attrs",
        )

        # This targets following Entries that belong to specified Entity
        entry_list = (
            Entry.objects.filter(schema=entity, is_active=True)
            .select_related("schema")
            .prefetch_related(attr_prefetch)
        )

        entity_attrs = entity.attrs.filter(is_active=True)

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
            es.delete(id=entry_id, ignore=[404])

        es.indices.refresh()
