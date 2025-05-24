import enum
import re
from datetime import datetime
from typing import Any, NotRequired

from django.conf import settings
from elasticsearch import Elasticsearch
from pydantic import BaseModel
from typing_extensions import TypedDict

from airone.lib.acl import ACLType
from airone.lib.log import Logger
from airone.lib.types import AttrType, BaseIntEnum
from entity.models import Entity
from entry.settings import CONFIG
from user.models import User


class AdvancedSearchResultRecordIdNamePair(TypedDict):
    id: int
    name: str
    schema: NotRequired["AdvancedSearchResultRecordIdNamePair"]


class AdvancedSearchResultRecordAttr(TypedDict, total=False):
    type: int
    value: Any
    is_readable: bool


class AdvancedSearchResultRecord(BaseModel):
    entity: AdvancedSearchResultRecordIdNamePair
    entry: AdvancedSearchResultRecordIdNamePair
    attrs: dict[str, AdvancedSearchResultRecordAttr]
    is_readable: bool
    referrals: list[AdvancedSearchResultRecordIdNamePair] | None = None


class AdvancedSearchResults(BaseModel):
    ret_count: int
    ret_values: list[AdvancedSearchResultRecord]


@enum.unique
class FilterKey(BaseIntEnum):
    CLEARED = 0
    EMPTY = 1
    NON_EMPTY = 2
    TEXT_CONTAINED = 3
    TEXT_NOT_CONTAINED = 4
    DUPLICATED = 5


@enum.unique
class EntryFilterKey(BaseIntEnum):
    CLEARED = 0
    TEXT_CONTAINED = 1
    TEXT_NOT_CONTAINED = 2


class AttrHint(BaseModel):
    name: str
    is_readable: bool | None = None
    filter_key: FilterKey | None = None
    keyword: str | None = None
    exact_match: bool | None = None


class EntryHint(BaseModel):
    is_readable: bool | None = None
    filter_key: EntryFilterKey | None = None
    keyword: str | None = None
    exact_match: bool | None = None


class AttributeDocument(TypedDict):
    name: str
    type: int
    key: str
    value: str | bool
    date_value: str | None
    referral_id: str
    is_readable: bool


class EntryDocument(TypedDict):
    entity: dict[str, str | int]
    name: str
    attr: list[AttributeDocument]
    referrals: list[dict[str, str | int | dict[str, str | int]]]
    is_readable: bool


class ESS(Elasticsearch):
    MAX_TERM_SIZE = 32766

    def __init__(self, index=None, *args, **kwargs):
        self.additional_config = False

        self._index = index
        if not index:
            self._index = settings.ES_CONFIG["INDEX_NAME"]

        if ("timeout" not in kwargs) and (settings.ES_CONFIG["TIMEOUT"] is not None):
            kwargs["timeout"] = settings.ES_CONFIG["TIMEOUT"]

        super(ESS, self).__init__(settings.ES_CONFIG["URL"], *args, **kwargs)

    def bulk(self, *args, **kwargs):
        return super(ESS, self).bulk(index=self._index, *args, **kwargs)

    def delete(self, *args, **kwargs):
        return super(ESS, self).delete(index=self._index, *args, **kwargs)

    def refresh(self, *args, **kwargs):
        return self.indices.refresh(index=self._index, *args, **kwargs)

    def index(self, *args, **kwargs):
        return super(ESS, self).index(index=self._index, *args, **kwargs)

    def search(self, *args, **kwargs) -> dict[str, Any]:
        # expand max_result_window parameter which indicates numbers to return at one searching
        if not self.additional_config:
            self.additional_config = True

            body = {"index": {"max_result_window": settings.ES_CONFIG["MAXIMUM_RESULTS_NUM"]}}
            self.indices.put_settings(index=self._index, body=body)

        if "size" not in kwargs:
            kwargs["size"] = settings.ES_CONFIG["MAXIMUM_RESULTS_NUM"]

        return super(ESS, self).search(index=self._index, *args, **kwargs)

    def recreate_index(self) -> None:
        self.indices.delete(index=self._index, ignore=[400, 404])
        self.indices.create(
            index=self._index,
            ignore=400,
            settings={
                "index": {
                    "mapping": {
                        "nested_objects": {
                            "limit": settings.ES_CONFIG["MAXIMUM_NESTED_OBJECT_NUM"],
                        }
                    }
                }
            },
            mappings={
                "properties": {
                    "name": {
                        "type": "text",
                        "index": "true",
                        "analyzer": "keyword",
                        "fields": {
                            "keyword": {"type": "keyword"},
                        },
                    },
                    "referrals": {
                        "type": "nested",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "index": "true",
                            },
                            "name": {
                                "type": "text",
                                "index": "true",
                                "analyzer": "keyword",
                            },
                            "schema": {
                                "type": "nested",
                                "properties": {
                                    "id": {
                                        "type": "integer",
                                        "index": "true",
                                    },
                                    "name": {
                                        "type": "text",
                                        "index": "true",
                                        "analyzer": "keyword",
                                    },
                                },
                            },
                        },
                    },
                    "entity": {
                        "type": "nested",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "index": "true",
                            },
                            "name": {
                                "type": "text",
                                "index": "true",
                                "analyzer": "keyword",
                            },
                        },
                    },
                    "attr": {
                        "type": "nested",
                        "properties": {
                            "name": {
                                "type": "text",
                                "index": "true",
                                "analyzer": "keyword",
                            },
                            "type": {
                                "type": "integer",
                                "index": "false",
                            },
                            "id": {
                                "type": "integer",
                                "index": "false",
                            },
                            "key": {
                                "type": "text",
                                "index": "true",
                            },
                            "date_value": {
                                "type": "date",
                                "index": "true",
                            },
                            "value": {
                                "type": "text",
                                "index": "true",
                                "analyzer": "keyword",
                                "fields": {
                                    "keyword": {"type": "keyword"},
                                },
                            },
                            "referral_id": {
                                "type": "integer",
                                "index": "false",
                            },
                            "is_readable": {
                                "type": "boolean",
                                "index": "true",
                            },
                        },
                    },
                    "is_readable": {
                        "type": "boolean",
                        "index": "true",
                    },
                }
            },
        )


def make_query(
    hint_entity: Entity,
    hint_attrs: list[AttrHint],
    entry_name: str | None,
    hint_referral: str | None = None,
    hint_referral_entity_id: int | None = None,
    hint_entry: EntryHint | None = None,
    allow_missing_attributes: bool = False,
) -> dict[str, Any]:
    """Create a search query for Elasticsearch.

    Do the following:
    1. Initialize variables.
    2. Add the entity to the filtering condition.
    3. Add the entry name to the filtering condition.
    4. Add the attribute name to be searched.
    5. Analyzes the keyword entered for each attribute.
    6. Build queries along keywords.

    Args:
        hint_entity (Entity): Entity ID specified in the search condition input
        hint_attrs (list(AttrHint)): A list of search strings and attribute sets
        entry_name (str): Search string for entry name
        hint_referral (str): Search string for referred entry name
        hint_referral_entity_id (int):
            - Limit result to the Entries that refer to Entry, which belongs to
              specified Entity.
        allow_missing_attributes (bool, optional): Defaults to False.
            If True, entries that do not have attributes specified in hint_attrs (without a keyword)
            will be included in the search results.
            If False, attributes specified in hint_attrs (without a keyword) must exist
            in the entry.

    Returns:
        dict[str, Any]: The created search query is returned.

    """

    # Conversion processing from "filter_key" to "keyword" for each hint_attrs
    for hint_attr in hint_attrs:
        match hint_attr.filter_key:
            case FilterKey.CLEARED:
                # remove "keyword" parameter
                hint_attr.keyword = None
            case FilterKey.EMPTY:
                hint_attr.keyword = "\\"
            case FilterKey.NON_EMPTY:
                hint_attr.keyword = "*"
            case FilterKey.DUPLICATED:
                aggs_query = _make_aggs_query(hint_attr.name)
                # TODO Set to 1 for convenience
                resp = execute_query(aggs_query, 1)
                keyword_infos = resp["aggregations"]["attr_aggs"]["attr_name_aggs"][
                    "attr_value_aggs"
                ]["buckets"]
                if keyword_infos == []:
                    # Since there are 0 duplicates, set a condition that will always be false.
                    hint_attr.keyword = "a^"
                else:
                    keyword_list = [x["key"] for x in keyword_infos]
                    hint_attr.keyword = CONFIG.OR_SEARCH_CHARACTER.join(
                        ["^" + x + "$" for x in keyword_list]
                    )

    # Making a query to send ElasticSearch by the specified parameters
    query: dict[str, Any] = {
        "query": {
            "bool": {
                "filter": [],
                "should": [],
            }
        }
    }

    # set condition to get results that only have specified entity
    query["query"]["bool"]["filter"].append(
        {"nested": {"path": "entity", "query": {"term": {"entity.id": hint_entity.id}}}}
    )

    # Included in query if refinement is entered for 'Name' in advanced search
    if hint_entry is not None:
        pattern = _get_regex_pattern(hint_entry.keyword or "")
        match getattr(hint_entry, "filter_key", None):
            case EntryFilterKey.CLEARED:
                # Don't perform any filter
                pass
            case EntryFilterKey.TEXT_CONTAINED:
                should_clause = {"bool": {"must": [{"regexp": {"name": pattern}}]}}
                query["query"]["bool"]["filter"].append({"bool": {"should": [should_clause]}})
            case EntryFilterKey.TEXT_NOT_CONTAINED:
                must_not_clause = {"bool": {"must": [{"regexp": {"name": pattern}}]}}
                query["query"]["bool"]["filter"].append({"bool": {"must_not": [must_not_clause]}})
            case _:
                # NOTE: Unsupported filter key
                pass
    elif entry_name:
        query["query"]["bool"]["filter"].append(_make_entry_name_query(entry_name))

    if hint_referral:
        query["query"]["bool"]["filter"].append(_make_referral_query(hint_referral))

    if hint_referral_entity_id:
        query["query"]["bool"]["filter"].append(
            _make_referral_entity_query(hint_referral_entity_id)
        )

    # Determine attributes for existence check
    attr_existence_should_clauses: list[dict[str, Any]] = []
    if allow_missing_attributes:
        # For APIv2: Only attributes with specified keywords are subject to existence check
        for hint in hint_attrs:
            if hint.name and hint.keyword:
                attr_existence_should_clauses.append({"term": {"attr.name": hint.name}})
    else:
        for hint in hint_attrs:
            if hint.name:
                attr_existence_should_clauses.append({"term": {"attr.name": hint.name}})

    # Add attribute existence check condition (commonized)
    if attr_existence_should_clauses:
        nested_query_bool_part: dict[str, Any] = {"should": attr_existence_should_clauses}

        # Add minimum_should_match only for APIv2
        if allow_missing_attributes:
            nested_query_bool_part["minimum_should_match"] = 1

        query["query"]["bool"]["filter"].append(
            {
                "nested": {
                    "path": "attr",
                    "query": {"bool": nested_query_bool_part},
                }
            }
        )

    attr_query: dict[str, dict] = {}

    # filter attribute by keywords
    for hint in [hint for hint in hint_attrs if hint.name and hint.keyword]:
        attr_query.update(_parse_or_search(hint))

    # Build queries along keywords
    if attr_query:
        query["query"]["bool"]["filter"].append(
            _build_queries_along_keywords(hint_attrs, attr_query)
        )

    return query


def make_query_for_simple(
    hint_string: str, hint_entity_name: str | None, exclude_entity_names: list[str], offset: int
) -> dict[str, Any]:
    """Create a search query for Elasticsearch.

    Do the following:
        Create a query to search by AttributeValue and Entry Name.
        inner_hits returns only filtered attributes

    Args:
        hint_string (str): Search string
        hint_entity_name (str): Search string for Entity Name
        offset (int): Offset number

    Returns:
        dict[str, Any]: The created search query is returned.

    """
    query: dict[str, Any] = {
        "query": {"bool": {"must": []}},
        "_source": ["name", "entity"],
        "sort": [{"_score": {"order": "desc"}, "name.keyword": {"order": "asc"}}],
        "from": offset,
    }

    hint_query: dict = {"bool": {"should": [{"match": {"name": hint_string}}]}}
    hint_query["bool"]["should"].append(_make_entry_name_query(hint_string))
    hint_query["bool"]["should"].append(_make_attr_query_for_simple(hint_string))
    query["query"]["bool"]["must"].append(hint_query)

    if hint_entity_name:
        query["query"]["bool"]["must"].append(
            {
                "nested": {
                    "path": "entity",
                    "query": {"term": {"entity.name": hint_entity_name}},
                }
            }
        )

    if exclude_entity_names:
        query["query"]["bool"]["must_not"] = [
            {
                "nested": {
                    "path": "entity",
                    "query": {"term": {"entity.name": exclude_entity_name}},
                }
            }
            for exclude_entity_name in exclude_entity_names
        ]

    return query


def _make_aggs_query(hint_attr_name: str) -> dict:
    return {
        "aggs": {
            "attr_aggs": {
                "nested": {
                    "path": "attr",
                },
                "aggs": {
                    "attr_name_aggs": {
                        "filter": {
                            "bool": {
                                "must": [{"term": {"attr.name": hint_attr_name}}],
                                "must_not": [{"term": {"attr.value.keyword": ""}}],
                            }
                        },
                        "aggs": {
                            "attr_value_aggs": {
                                "terms": {"field": "attr.value.keyword", "min_doc_count": 2}
                            }
                        },
                    }
                },
            }
        },
    }


def _get_regex_pattern(keyword: str) -> str:
    """Create a regex pattern pattern.

    Create a regular expression pattern of the string received as an argument.

    Args:
        keyword (str): A string for which a regular expression pattern is created

    Returns:
        str: Regular expression pattern of argument

    """
    escaped = prepend_escape_character(CONFIG.ESCAPE_CHARACTERS, keyword)

    # Elasticsearch doesn't support anchor operators,
    begin = ".*"
    if escaped and escaped[0] == "^":
        begin = ""
        escaped = escaped.lstrip("^")

    end = ".*"
    if escaped and escaped[-1] == "$":
        end = ""
        escaped = escaped.rstrip("$")

    body = "".join(["[%s%s]" % (x.lower(), x.upper()) if x.isalpha() else x for x in escaped])

    return begin + body + end


def prepend_escape_character(escape_character_list: list[str], keyword: str) -> str:
    """Add escape character.

    If the argument 'keyword' contains the characters specified in 'escape_character_list',
    an escape character is added to the target character.

    Args:
        escape_character_list (list(str)): Give escape characters to the characters in this list
        keyword (str): String to be converted

    Returns:
        str: Returns 'keyword' after conversion.

    """
    return "".join(["\\" + x if x in escape_character_list else x for x in list(keyword)])


def _get_hint_keyword_val(keyword: str) -> str:
    """Null character conversion processing.

    Args:
        keyword (str): String to search for

    Returns:
        str: If a character corresponding to the empty string specified by CONFIG is entered,
            the empty character is returned.
            Else if keyword contains '\\', a white space is returned specially.
            Otherwise, the input value is returned.

    """
    if CONFIG.EMPTY_SEARCH_CHARACTER == keyword or CONFIG.EMPTY_SEARCH_CHARACTER_CODE == keyword:
        return ""
    if "\\" in keyword:
        return " "
    return keyword


def _make_entry_name_query(entry_name: str) -> dict[str, str]:
    """Create a search query for the entry name.

    Divides the search string with OR.
    Divide the divided character string with AND.
    Create a regular expression pattern query with the smallest unit string.
    If the string corresponds to a null character, specify the null character.

    Args:
        entry_name (str): Search string for entry name

    Returns:
        dict[str, str]: Entry name search query

    """
    entry_name_or_query: dict = {"bool": {"should": []}}

    # Split and process keywords with 'or'
    for keyword_divided_or in entry_name.split(CONFIG.OR_SEARCH_CHARACTER):
        entry_name_and_query: dict = {"bool": {"must": []}}

        # Keyword divided by 'or' is processed by dividing by 'and'
        for keyword in keyword_divided_or.split(CONFIG.AND_SEARCH_CHARACTER):
            name_val = _get_hint_keyword_val(keyword)
            if name_val:
                # When normal conditions are specified
                entry_name_and_query["bool"]["must"].append(
                    {"regexp": {"name": _get_regex_pattern(name_val)}}
                )
            else:
                # When blank is specified in the condition
                entry_name_and_query["bool"]["must"].append({"match": {"name": ""}})
        entry_name_or_query["bool"]["should"].append(entry_name_and_query)

    return entry_name_or_query


def _make_referral_query(referral_name: str) -> dict[str, str]:
    referral_or_query: dict = {"bool": {"should": []}}

    # Split and process keywords with 'or'
    for keyword_divided_or in referral_name.split(CONFIG.OR_SEARCH_CHARACTER):
        referral_and_query: dict = {
            "bool": {
                "must": [],
                "must_not": [],
            }
        }

        # Keyword divided by 'or' is processed by dividing by 'and'
        for keyword in keyword_divided_or.split(CONFIG.AND_SEARCH_CHARACTER):
            name_val = _get_hint_keyword_val(keyword)
            if name_val == CONFIG.EXSIT_CHARACTER:
                # When existed referral is specified in the condition
                referral_and_query["bool"]["must"].append(
                    {"nested": {"path": "referrals", "query": {"exists": {"field": "referrals"}}}}
                )
            elif name_val:
                # When normal conditions are specified
                referral_and_query["bool"]["must"].append(
                    {
                        "nested": {
                            "path": "referrals",
                            "query": {"regexp": {"referrals.name": _get_regex_pattern(name_val)}},
                        }
                    }
                )
            else:
                # When blank is specified in the condition
                referral_and_query["bool"]["must_not"].append(
                    {"nested": {"path": "referrals", "query": {"exists": {"field": "referrals"}}}}
                )

        referral_or_query["bool"]["should"].append(referral_and_query)

    return referral_or_query


def _make_referral_entity_query(referral_entity_id: int) -> dict[str, str]:
    referral_or_query: dict = {
        "bool": {
            "should": [
                {
                    "nested": {
                        "path": "referrals.schema",
                        "query": {"match": {"referrals.schema.id": referral_entity_id}},
                    }
                }
            ]
        }
    }

    return referral_or_query


def _make_attr_query_for_simple(hint_string: str) -> dict[str, dict]:
    """Create a search query for the AttributeValue in simple search.

    Divides the search string with OR.
    Divide the divided character string with AND.
    Create a regular expression pattern query with the smallest unit string.

    Args:
        hint_string (str): Search string for AttributeValue

    Returns:
        dict[str, str]: AttributeValue search query

    """

    attr_query: dict[str, dict] = {
        "bool": {"filter": {"nested": {"path": "attr", "inner_hits": {"_source": ["attr.name"]}}}}
    }

    attr_or_query: dict[str, dict] = {"bool": {"should": []}}
    for keyword_divided_or in hint_string.split(CONFIG.OR_SEARCH_CHARACTER):
        if not keyword_divided_or:
            continue

        attr_and_query: dict[str, dict] = {"bool": {"filter": []}}
        for keyword_divided_and in keyword_divided_or.split(CONFIG.AND_SEARCH_CHARACTER):
            if not keyword_divided_and:
                continue

            attr_and_query["bool"]["filter"].append(
                {"regexp": {"attr.value": _get_regex_pattern(keyword_divided_and)}}
            )
        attr_or_query["bool"]["should"].append(attr_and_query)

    attr_query["bool"]["filter"]["nested"]["query"] = attr_or_query

    return attr_query


def _parse_or_search(hint: AttrHint) -> dict[str, dict]:
    """Performs keyword analysis processing.

    The search keyword is separated by OR and passed to the next process.

    Args:
        hint (AttrHint): Dictionary of attribute names and search keywords to be processed
        attr_query (dict[str, str]): Search query being created

    Returns:
        dict[str, str]: Add the analysis result to 'attr_query' for the keywords separated
            by 'OR' and return.

    """
    attr_query: dict[str, dict] = {}
    duplicate_keys: list = []

    # Split and process keywords with 'or'
    for keyword_divided_or in (hint.keyword or "").split(CONFIG.OR_SEARCH_CHARACTER):
        parsed_query = _parse_and_search(hint, keyword_divided_or, duplicate_keys)
        attr_query.update(parsed_query)

    return attr_query


def _parse_and_search(
    hint: AttrHint,
    keyword_divided_or: str,
    duplicate_keys: list[str],
) -> dict[str, dict]:
    """Analyze the keywords separated by `OR`

    Keywords separated by OR are separated by AND.
    Create a block that summarizes all attribute filters for each smallest keyword.

    If the plan has already been processed, skip it.
    If not, add it to the list.

    If called from simple search, add to the query below.
    If called from advanced search, add it directly under keyword.
        {
            keyword: {
                'bool': {
                    'should': []
                }
            }
        }

    Args:
        hint (AttrHint): Dictionary of attribute names and search keywords to be processed
        keyword_divided_or (str): Character string with search keywords separated by OR
        attr_query (dict[str, str]): Search query being created
        duplicate_keys (list(str)): Holds a list of the smallest character strings
            that separate search keywords with AND and OR.
            If the target string is already included in the list, processing is skipped.

    Returns:
        dict[str, dict]: The analysis result is added to 'attr_query' for the keywords separated
            by 'AND' and returned.

    """
    attr_query: dict[str, dict] = {}

    # Keyword divided by 'or' is processed by dividing by 'and'
    for keyword in keyword_divided_or.split(CONFIG.AND_SEARCH_CHARACTER):
        key = f"{keyword}_{hint.name}"

        # Skip if keywords overlap
        if key in duplicate_keys:
            continue
        else:
            duplicate_keys.append(key)

        attr_query[key] = _make_an_attribute_filter(hint, keyword)

    return attr_query


def _build_queries_along_keywords(
    hint_attrs: list[AttrHint],
    attr_query: dict[str, dict],
) -> dict[str, dict]:
    """Build queries along search terms.

    Do the following:
    1. Get the keyword.
       In case of simple search, get the first search keyword.
       For advanced searches, retrieve multiple records for each attribute value.
    2. Process for each keyword acquired in 1.
    3. The search keyword is processed for each character string of the
       smallest unit separated by `AND` and `OR`.
    4. If `AND` is included in the string separated by `OR`, concatenate them with a filter.
       If it is not included, use it as is.
    5. If the search keyword contains OR, connect with should.
       If it is not included, use it as is.
    6. When conditions are specified with multiple attributes in advanced search,
       they are combined with filter.
    7. The query will be returned when the processing
       for the retrieved search keywords is completed.

    Args:
        hint_attrs (list(AttrHint)): A list of search strings and attribute sets
        attr_query (dict[str, dict]): A query that summarizes attributes
            by the smallest unit of a search keyword

    Returns:
        dict[str, dict]: Assemble and return the attribute value part of the search query.

    """

    # Get the keyword.
    hints = [x for x in hint_attrs if x.keyword]
    res_query: dict[str, Any] = {}

    for hint in hints:
        and_query: dict[str, Any] = {}
        or_query: dict[str, Any] = {}

        # Split keyword by 'or'
        for keyword_divided_or in (hint.keyword or "").split(CONFIG.OR_SEARCH_CHARACTER):
            if CONFIG.AND_SEARCH_CHARACTER in keyword_divided_or:
                # If 'AND' is included in the keyword divided by 'OR', add it to 'filter'
                for keyword in keyword_divided_or.split(CONFIG.AND_SEARCH_CHARACTER):
                    if keyword_divided_or not in and_query:
                        and_query[keyword_divided_or] = {"bool": {"filter": []}}

                    and_query[keyword_divided_or]["bool"]["filter"].append(
                        attr_query[keyword + "_" + hint.name]
                    )

            else:
                and_query[keyword_divided_or] = attr_query[keyword_divided_or + "_" + hint.name]

            if CONFIG.OR_SEARCH_CHARACTER in (hint.keyword or ""):
                # If the keyword contains 'or', concatenate with 'should'
                if not or_query:
                    or_query = {"bool": {"should": []}}

                or_query["bool"]["should"].append(and_query[keyword_divided_or])

            else:
                or_query = and_query[keyword_divided_or]

        if len(hints) > 1:
            # If conditions are specified for multiple attributes in advanced search,
            # connect with 'filter'
            if not res_query:
                res_query = {"bool": {"filter": []}}

            res_query["bool"]["filter"].append(or_query)

        else:
            res_query = or_query

    return res_query


def _make_an_attribute_filter(hint: AttrHint, keyword: str) -> dict[str, dict]:
    """creates an attribute filter from keywords.

    For the attribute set in the name of hint, create a filter for filtering search keywords.
    If the search keyword is a date, the following processing is performed.
    1. Create a format for date fields.
    2. If the search keyword is a date, the following processing is performed.
       If `< date`, search below the specified date.
       If `> date`, search for dates after the specified date.
       If `<>` is not included,
           the search will be made before the specified date and after the specified date.
    3. If the search keyword is not a date, do the following:
       If a character corresponding to a null character is specified,
           it is converted to a null character.
       Create a 'match' query with the conversion results.
       If the conversion result is not empty, create a 'regexp' query.
       If the conversion result is an empty string, search for data
           with an empty attribute value
    # 4. After the above process, create a 'nested' query and return it.

    Args:
        hint (AttrHint): Dictionary of attribute names and search keywords to be processed
        keyword (str): String to search for
            String of the smallest unit in which search keyword is separated by `AND` and `OR`

    Returns:
        dict[str, str]: Created attribute filter

    """
    cond_attr: list[dict] = [{"term": {"attr.name": hint.name}}]

    date_results = _is_date(keyword)
    if date_results:
        date_cond = {
            "range": {"attr.date_value": {"format": "yyyy-MM-dd"}},
        }
        for range_check, date_obj in date_results:
            match range_check:
                case "<":
                    # search of before date user specified
                    date_cond["range"]["attr.date_value"]["lt"] = date_obj.strftime("%Y-%m-%d")
                case ">":
                    # search of after date user specified
                    date_cond["range"]["attr.date_value"]["gt"] = date_obj.strftime("%Y-%m-%d")
                case "~":
                    # search of date range user specified
                    start_date, end_date = date_obj
                    date_cond["range"]["attr.date_value"]["gte"] = start_date.strftime("%Y-%m-%d")
                    date_cond["range"]["attr.date_value"]["lte"] = end_date.strftime("%Y-%m-%d")
                case _:
                    # search of exact day
                    date_cond["range"]["attr.date_value"]["gte"] = date_obj.strftime("%Y-%m-%d")
                    date_cond["range"]["attr.date_value"]["lte"] = date_obj.strftime("%Y-%m-%d")

        str_cond = {"regexp": {"attr.value": _get_regex_pattern(keyword)}}

        if hint.filter_key == FilterKey.TEXT_NOT_CONTAINED:
            cond_attr.append({"bool": {"must_not": [date_cond, str_cond]}})
        else:
            cond_attr.append({"bool": {"should": [date_cond, str_cond]}})

    else:
        hint_keyword_val = _get_hint_keyword_val(keyword)
        cond_val = [{"match": {"attr.value": hint_keyword_val}}]

        # This is an exceptional bypass processing to be able to search Entries
        # that has substantial Attribute.
        if hint_keyword_val == CONFIG.EXSIT_CHARACTER:
            cond_attr.append(
                {
                    "bool": {
                        "should": [
                            # This query get results that have any substantial values
                            {"regexp": {"attr.value": ".+"}},
                            # This query get results that have date value
                            {"exists": {"field": "attr.date_value"}},
                        ]
                    }
                }
            )

        elif hint_keyword_val:
            if hint.exact_match is None:
                cond_val.append({"regexp": {"attr.value": _get_regex_pattern(hint_keyword_val)}})

            if hint.filter_key == FilterKey.TEXT_NOT_CONTAINED:
                cond_attr.append({"bool": {"must_not": cond_val}})
            else:
                cond_attr.append({"bool": {"should": cond_val}})

        else:
            cond_val_tmp = [
                {"bool": {"must_not": {"exists": {"field": "attr.date_value"}}}},
                {"bool": {"should": cond_val}},
            ]
            cond_attr.append({"bool": {"must": cond_val_tmp}})

    return {"nested": {"path": "attr", "query": {"bool": {"filter": cond_attr}}}}


def execute_query(
    query: dict[str, Any], size: int | None = None, offset: int | None = None
) -> dict[str, Any]:
    """Run a search query.

    Args:
        query (dict[str, dict]): Search query
        size (int | None): Size of search query results
        offset (int | None): Offset of search query results

    Raises:
        Exception: If query execution fails, output error details.

    Returns:
        dict[str, Any]: Search execution result

    """
    kwargs = {
        "size": min(size, 500000) if size else settings.ES_CONFIG["MAXIMUM_RESULTS_NUM"],
        "from_": offset,
        "body": query,
        "ignore": [404],
        "sort": ["name.keyword:asc"],
        "track_total_hits": True,
    }

    try:
        res = ESS().search(**kwargs)
    except Exception as e:
        raise (e)

    return res


def make_search_results(
    user: User,
    res: dict[str, Any],
    hint_attrs: list[AttrHint],
    hint_referral: str | None,
    limit: int,
) -> AdvancedSearchResults:
    """Acquires and returns the attribute values held by each search result

    When the condition of reference entry is specified, the entry to reference is acquired.
    Also, get the attribute name and attribute value that matched the condition.

    Do the following:
    1. Keep a list of IDs of all entries that have been found in Elasticsearch.
    2. If the reference entry filtering conditions have been entered,
       the following processing is performed.
       If not entered, get entry object from search result of Elasticsearch.

       2-1. If blank characters are entered in the filtering condition of the reference entry,
            only entries that are not referenced by other entries are filtered.
       2-2. In cases other than the above, only entries whose filtering condition is
            included in the entry name being referred to are acquired.
       2-3. Get the entry object from the entry ID obtained above.

    3. Get attributes for each entry for the maximum number of displayed items
       from the Elasticsearch search results.
    4. For the attribute of the acquired entry,
       the attribute value is acquired according to the attribute type.
    5. When all entries have been processed, the search results are returned.

    Args:
        res (`str`, optional): Search results for Elasticsearch
        hint_attrs (list(AttrHint)):  A list of search strings and attribute sets
        limit (int): Maximum number of search results to return

    Returns:
       AdvancedSearchResults: A set of attributes and attribute values associated with the entry
            that was hit in the search

    """
    from entry.models import Entry

    # set numbers of found entries
    results = AdvancedSearchResults(
        ret_count=res["hits"]["total"]["value"],
        ret_values=[],
    )

    # get django objects from the hit information from Elasticsearch
    hit_entry_ids = [x["_id"] for x in res["hits"]["hits"]]
    hit_entries = Entry.objects.filter(id__in=hit_entry_ids, is_active=True).select_related(
        "schema"
    )

    hit_infos: dict = {}
    for entry in hit_entries[:limit]:
        hit_infos[entry] = [x["_source"] for x in res["hits"]["hits"] if int(x["_id"]) == entry.id][
            0
        ]

    for entry, entry_info in sorted(hit_infos.items(), key=lambda x: x[0].name):
        record = AdvancedSearchResultRecord(
            entity={"id": entry.schema.id, "name": entry.schema.name},
            entry={"id": entry.id, "name": entry.name},
            attrs={},
            is_readable=False,
        )

        if hint_referral is not None:
            record.referrals = entry_info.get("referrals", [])

        # Check for has permission to Entry. But it will be omitted when user is None.
        if (
            entry_info["is_readable"]
            or user is None
            or user.has_permission(entry, ACLType.Readable)
        ):
            record.is_readable = True
        else:
            record.is_readable = False
            results.ret_values.append(record)
            continue

        # formalize attribute values according to the type
        for attrinfo in entry_info["attr"]:
            # Skip other than the target Attribute
            if attrinfo["name"] not in [x.name for x in hint_attrs]:
                continue

            ret_attrinfo: AdvancedSearchResultRecordAttr = {}
            if attrinfo["name"] in record.attrs:
                ret_attrinfo = record.attrs[attrinfo["name"]]
            else:
                ret_attrinfo = record.attrs[attrinfo["name"]] = {}

            ret_attrinfo["is_readable"] = True
            ret_attrinfo["type"] = attrinfo["type"]

            # if target attribute is array type, then values would be stored in array
            if attrinfo["name"] not in record.attrs:
                if attrinfo["type"] & AttrType._ARRAY:
                    record.attrs[attrinfo["name"]] = {}
                else:
                    record.attrs[attrinfo["name"]] = ret_attrinfo

            # Check for has permission to EntityAttr
            if attrinfo["name"] not in [x.name for x in hint_attrs if x.is_readable]:
                ret_attrinfo["is_readable"] = False
                continue

            # Check for has permission to Attribute
            if not attrinfo["is_readable"]:
                attr = entry.attrs.filter(schema__name=attrinfo["name"], is_active=True).first()
                if not attr:
                    Logger.warning(
                        "Non exist Attribute (entry:%s, name:%s) is registered in ESS."
                        % (entry.id, attrinfo["name"])
                    )
                    continue

                if not user.has_permission(attr, ACLType.Readable):
                    ret_attrinfo["is_readable"] = False
                    continue

            try:
                attr_type = AttrType(attrinfo["type"])
            except ValueError:
                # For compatibility; continue that, and record the error
                Logger.error("Invalid attribute type: %s" % attrinfo["type"])
                continue

            match attr_type:
                case AttrType.STRING | AttrType.TEXT | AttrType.BOOLEAN:
                    ret_attrinfo["value"] = attrinfo["value"]

                case AttrType.DATE | AttrType.DATETIME:
                    ret_attrinfo["value"] = attrinfo["date_value"]

                case AttrType.OBJECT | AttrType.GROUP | AttrType.ROLE:
                    ret_attrinfo["value"] = {
                        "id": attrinfo["referral_id"],
                        "name": attrinfo["value"],
                    }

                case AttrType.NAMED_OBJECT:
                    ret_attrinfo["value"] = {
                        attrinfo["key"]: {
                            "id": attrinfo["referral_id"],
                            "name": attrinfo["value"],
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
                    if "value" not in ret_attrinfo:
                        ret_attrinfo["value"] = []

                    # If there is no value, it will be skipped.
                    if attrinfo["key"] == attrinfo["value"] == attrinfo["referral_id"] == "":
                        continue

                    match attr_type:
                        case AttrType.ARRAY_NAMED_OBJECT:
                            ret_attrinfo["value"].append(
                                {
                                    attrinfo["key"]: {
                                        "id": attrinfo["referral_id"],
                                        "name": attrinfo["value"],
                                    }
                                }
                            )

                        case AttrType.ARRAY_STRING:
                            ret_attrinfo["value"].append(attrinfo["value"])

                        case AttrType.ARRAY_OBJECT | AttrType.ARRAY_GROUP | AttrType.ARRAY_ROLE:
                            ret_attrinfo["value"].append(
                                {"id": attrinfo["referral_id"], "name": attrinfo["value"]}
                            )

        results.ret_values.append(record)

    return results


def make_search_results_for_simple(res: dict[str, Any]) -> dict[str, str]:
    result = {
        "ret_count": res["hits"]["total"]["value"],
        "ret_values": [],
    }

    for resp_entry in res["hits"]["hits"]:
        ret_value = {
            "id": resp_entry["_id"],
            "name": resp_entry["_source"]["name"],
            "schema": resp_entry["_source"]["entity"],
        }

        for resp_entry_attr in resp_entry["inner_hits"]["attr"]["hits"]["hits"]:
            ret_value["attr"] = resp_entry_attr["_source"]["name"]
            break

        result["ret_values"].append(ret_value)

    return result


def _is_date_check(value: str) -> tuple[str, datetime | tuple[datetime, datetime]] | None:
    def _parse_basic_iso8601(value: str) -> datetime | None:
        """Parse a basic ISO 8601 formatted date string

        Only supports YYYY-MM-DDThh:mm:ss format.
        The 'T' character must be used as the separator between date and time.
        Returns a datetime object if successful, None if parsing fails.
        """
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    # First check for ISO 8601 format
    operator = ""
    iso_value = value

    # Check if there's a comparison operator
    if value and value[0] in ["<", ">"]:
        operator = value[0]
        iso_value = value[1:]

    # Check if there's a date range
    if "~" in iso_value:
        date_parts = iso_value.split("~")
        if len(date_parts) == 2:
            start_datetime = _parse_basic_iso8601(date_parts[0].strip())
            end_datetime = _parse_basic_iso8601(date_parts[1].strip())
            if start_datetime and end_datetime:
                # Ensure start date is not after end date
                if start_datetime <= end_datetime:
                    return "~", (start_datetime, end_datetime)

    # Check for single ISO 8601 format
    iso_datetime = _parse_basic_iso8601(iso_value)
    if iso_datetime:
        return operator, iso_datetime

    # Check for legacy date format
    try:
        for delimiter in ["-", "/"]:
            date_format = "%%Y%(del)s%%m%(del)s%%d" % {"del": delimiter}

            # Detect date range separated by tilde (~)
            if "~" in value:
                date_parts = value.split("~")
                if len(date_parts) == 2:
                    # Verify both dates have the same format
                    start_date_match = re.match(
                        r"^[0-9]{4}%(del)s[0-9]+%(del)s[0-9]+" % {"del": delimiter},
                        date_parts[0].strip(),
                    )
                    end_date_match = re.match(
                        r"^[0-9]{4}%(del)s[0-9]+%(del)s[0-9]+" % {"del": delimiter},
                        date_parts[1].strip(),
                    )

                    if start_date_match and end_date_match:
                        start_date = datetime.strptime(date_parts[0].strip(), date_format)
                        end_date = datetime.strptime(date_parts[1].strip(), date_format)

                        # Validate start date is not after end date
                        if start_date <= end_date:
                            return ("~", (start_date, end_date))

            # Process existing date searches with < and > operators
            if re.match(r"^[<>]?[0-9]{4}%(del)s[0-9]+%(del)s[0-9]+" % {"del": delimiter}, value):
                if value[0] in ["<", ">"]:
                    return (
                        value[0],
                        datetime.strptime(value[1:].split(" ")[0], date_format),
                    )
                else:
                    return "", datetime.strptime(value.split(" ")[0], date_format)

    except ValueError:
        # datetime.strptime raises ValueError when format matches but contains invalid date values
        return None

    return None


def _is_date(value: str) -> list | None:
    # checks all specified value is date format
    result = [_is_date_check(x) for x in value.split(" ") if x]

    # If result is not empty and all value is date, this returns the result
    return result if result and all(result) else None
