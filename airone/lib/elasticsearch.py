import json
import re

from datetime import datetime
from django.conf import settings
from django.db.models import Q
from elasticsearch import Elasticsearch
from airone.lib.types import AttrTypeValue
from entry.settings import CONFIG


class ESS(Elasticsearch):
    MAX_TERM_SIZE = 32766

    def __init__(self, index=None, *args, **kwargs):
        self.additional_config = False

        if not index:
            self._index = settings.ES_CONFIG['INDEX']

        if ('timeout' not in kwargs) and (settings.ES_CONFIG['TIMEOUT'] is not None):
            kwargs['timeout'] = settings.ES_CONFIG['TIMEOUT']

        super(ESS, self).__init__(settings.ES_CONFIG['NODES'], *args, **kwargs)

    def delete(self, *args, **kwargs):
        return super(ESS, self).delete(index=self._index, *args, **kwargs)

    def refresh(self, *args, **kwargs):
        return self.indices.refresh(index=self._index, *args, **kwargs)

    def index(self, *args, **kwargs):
        return super(ESS, self).index(index=self._index, *args, **kwargs)

    def search(self, *args, **kwargs):
        # expand max_result_window parameter which indicates numbers to return at one searching
        if not self.additional_config:
            self.additional_config = True

            body = {"index": {"max_result_window": settings.ES_CONFIG['MAXIMUM_RESULTS_NUM']}}
            self.indices.put_settings(index=self._index, body=body)

        return super(ESS, self).search(index=self._index,
                                       size=settings.ES_CONFIG['MAXIMUM_RESULTS_NUM'], *args,
                                       **kwargs)

    def recreate_index(self):
        self.indices.delete(index=self._index, ignore=[400, 404])
        self.indices.create(index=self._index, ignore=400, body=json.dumps({
            'mappings': {
                'entry': {
                    'properties': {
                        'name': {
                            'type': 'text',
                            'index': 'true',
                            'analyzer': 'keyword',
                            'fields': {
                                'keyword': {'type': 'keyword'},
                            },
                        },
                        'entity': {
                            'type': 'nested',
                            'properties': {
                                'id': {
                                    'type': 'integer',
                                    'index': 'true',
                                },
                                'name': {
                                    'type': 'text',
                                    'index': 'true',
                                    'analyzer': 'keyword'
                                }
                            }
                        },
                        'attr': {
                            'type': 'nested',
                            'properties': {
                                'name': {
                                    'type': 'text',
                                    'index': 'true',
                                    'analyzer': 'keyword'
                                },
                                'type': {
                                    'type': 'integer',
                                    'index': 'false',
                                },
                                'id': {
                                    'type': 'integer',
                                    'index': 'false',
                                },
                                'key': {
                                    'type': 'text',
                                    'index': 'true',
                                },
                                'date_value': {
                                    'type': 'date',
                                    'index': 'true',
                                },
                                'value': {
                                    'type': 'text',
                                    'index': 'true',
                                    'analyzer': 'keyword'
                                },
                                'referral_id': {
                                    'type': 'integer',
                                    'index': 'false',
                                }
                            }
                        }
                    }
                }
            }
        }))


__all__ = [
    'make_query',
    'execute_query',
    'make_search_results',
    'prepend_escape_character',
    'is_date_check'
]


def make_query(hint_entity_ids, hint_attrs, entry_name, or_match):
    """Create a search query for Elasticsearch.

    Do the following:
    1. Initialize variables.
    2. Add the entity to the filtering condition.
    3. Add the entry name to the filtering condition.
    4. Add the attribute name to be searched.
    5. Analyzes the keyword entered for each attribute.
    6. Build queries along keywords.

    Args:
        hint_entity_ids (list(str)): Entity ID specified in the search condition input
        hint_attrs (list(dict[str, str])): A list of search strings and attribute sets
        entry_name (str): Search string for entry name
        or_match (bool): Flag to determine whether the simple search or
            advanced search is called

    Returns:
        dict[str, str]: The created search query is returned.

    """

    # Making a query to send ElasticSearch by the specified parameters
    query = {
        "query": {
            "bool": {
                'filter': [],
                'should': [],
            }
        }
    }

    # set condition to get results that only have specified entity
    query['query']['bool']['filter'].append({
        'nested': {
            'path': 'entity',
            'query': {
                'bool': {'should': [{'term': {'entity.id': int(x)}} for x in hint_entity_ids]}
            }
        }
    })

    # Included in query if refinement is entered for 'Name' in advanced search
    if entry_name:
        query['query']['bool']['filter'].append(_make_entry_name_query(entry_name))

    # Set the attribute name so that all the attributes specified in the attribute,
    # to be searched can be used
    if hint_attrs:
        query['query']['bool']['filter'].append({
            'nested': {
                'path': 'attr',
                'query': {
                    'bool': {
                        'should': [
                            {'term': {'attr.name': x['name']}} for x in hint_attrs if 'name' in x
                        ]
                    }
                }
            }
        })

    attr_query = {}

    # filter attribute by keywords
    for hint in [x for x in hint_attrs if 'name' in x and 'keyword' in x and x['keyword']]:
        _parse_or_search(hint, or_match, attr_query)

    # Build queries along keywords
    if attr_query:
        query['query']['bool']['filter'].append(
            _build_queries_along_keywords(hint_attrs, attr_query, or_match))

    return query


def _get_regex_pattern(keyword):
    """Create a regex pattern pattern.

    Create a regular expression pattern of the string received as an argument.

    Args:
        keyword (str): A string for which a regular expression pattern is created

    Returns:
        str: Regular expression pattern of argument

    """
    return '.*%s.*' % ''.join(['[%s%s]' % (
        x.lower(), x.upper()) if x.isalpha() else x for x in prepend_escape_character(
        CONFIG.ESCAPE_CHARACTERS, keyword)])


def prepend_escape_character(escape_character_list, keyword):
    """Add escape character.

    If the argument 'keyword' contains the characters specified in 'escape_character_list',
    an escape character is added to the target character.

    Args:
        escape_character_list (list(str)): Give escape characters to the characters in this list
        keyword (str): String to be converted

    Returns:
        str: Returns 'keyword' after conversion.

    """
    return ''.join(['\\' + x if x in escape_character_list else x for x in list(keyword)])


def _get_hint_keyword_val(keyword):
    """Null character conversion processing.

    Args:
        keyword (str): String to search for

    Returns:
        str: If a character corresponding to the empty string specified by CONFIG is entered,
            the empty character is returned.
            Otherwise, the input value is returned.

    """
    if (CONFIG.EMPTY_SEARCH_CHARACTER == keyword or
            CONFIG.EMPTY_SEARCH_CHARACTER_CODE == keyword):
        return ''
    return keyword


def _make_entry_name_query(entry_name):
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
    entry_name_or_query = {
        'bool': {
            'should': []
        }
    }

    # Split and process keywords with 'or'
    for keyword_divided_or in entry_name.split(CONFIG.OR_SEARCH_CHARACTER):

        entry_name_and_query = {
            'bool': {
                'filter': []
            }
        }

        # Keyword divided by 'or' is processed by dividing by 'and'
        for keyword in keyword_divided_or.split(CONFIG.AND_SEARCH_CHARACTER):
            name_val = _get_hint_keyword_val(keyword)
            if name_val:
                # When normal conditions are specified
                entry_name_and_query['bool']['filter'].append({
                    'regexp': {
                        'name': _get_regex_pattern(name_val)
                    }
                })
            else:
                # When blank is specified in the condition
                entry_name_and_query['bool']['filter'].append({
                    'match': {
                        'name': ''
                    }
                })
        entry_name_or_query['bool']['should'].append(entry_name_and_query)

    return entry_name_or_query


def _parse_or_search(hint, or_match, attr_query):
    """Performs keyword analysis processing.

    The search keyword is separated by OR and passed to the next process.

    Args:
        hint (dict[str, str]): Dictionary of attribute names and search keywords to be processed
        or_match (bool): Flag to determine whether the simple search or
            advanced search is called
        attr_query (dict[str, str]): Search query being created

    Returns:
        dict[str, str]: Add the analysis result to 'attr_query' for the keywords separated
            by 'OR' and return.

    """
    duplicate_keys = []

    # Split and process keywords with 'or'
    for keyword_divided_or in hint['keyword'].split(CONFIG.OR_SEARCH_CHARACTER):

        _parse_and_search(hint, keyword_divided_or, or_match, attr_query, duplicate_keys)

    return attr_query


def _parse_and_search(hint, keyword_divided_or, or_match, attr_query, duplicate_keys):
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
        hint (dict[str, str]): Dictionary of attribute names and search keywords to be processed
        keyword_divided_or (str): Character string with search keywords separated by OR
        or_match (bool): Flag to determine whether the simple search or
            advanced search is called
        attr_query (dict[str, str]): Search query being created
        duplicate_keys (list(str)): Holds a list of the smallest character strings
            that separate search keywords with AND and OR.
            If the target string is already included in the list, processing is skipped.

    Returns:
        dict[str, str]: The analysis result is added to 'attr_query' for the keywords separated
            by 'AND' and returned.

    """

    # Keyword divided by 'or' is processed by dividing by 'and'
    for keyword in keyword_divided_or.split(CONFIG.AND_SEARCH_CHARACTER):
        key = _make_key_for_each_block_of_keywords(hint, keyword, or_match)

        # Skip if keywords overlap
        if key in duplicate_keys:
            continue
        else:
            duplicate_keys.append(key)

        if or_match:
            if key not in attr_query:
                # Add keyword if temporary variable doesn't contain keyword
                attr_query[key] = {'bool': {'should': []}}

            attr_query[key]['bool']['should'].append(
                _make_an_attribute_filter(hint, keyword))
        else:
            attr_query[key] = _make_an_attribute_filter(hint, keyword)

    return attr_query


def _make_key_for_each_block_of_keywords(hint, keyword, or_match):
    """Create a key for each block of minimal keywords.

    Create a key for each block of keywords.
    For simple search, the keyword is used as a key.
    In case of advanced search, attribute name is given to judge for each attribute.

    Args:
        hint (dict[str, str]): Dictionary of attribute names and search keywords to be processed
        keyword (str): String of the smallest unit in which search keyword is
            separated by AND and OR
        or_match (bool): Flag to determine whether the simple search or
            advanced search is called

    Returns:
        dict[str, str]: For simple search, the keyword of the argument is returned.
            In the case of advanced search,
            the attribute name is assigned to the argument keyword and returned.

    """
    return keyword if or_match else keyword + '_' + hint['name']


def _build_queries_along_keywords(hint_attrs, attr_query, or_match):
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
        hint_attrs (list(dict[str, str])): A list of search strings and attribute sets
        attr_query (dict[str, str]): A query that summarizes attributes
            by the smallest unit of a search keyword
        or_match (bool): Flag to determine whether the simple search or
            advanced search is called

    Returns:
        dict[str, str]: Assemble and return the attribute value part of the search query.

    """

    # Get the keyword.
    hints = [x for x in hint_attrs if x['keyword']] if not or_match else [hint_attrs[0]]
    res_query = {}

    for hint in hints:
        and_query = {}
        or_query = {}

        # Split keyword by 'or'
        for keyword_divided_or in hint['keyword'].split(CONFIG.OR_SEARCH_CHARACTER):
            if CONFIG.AND_SEARCH_CHARACTER in keyword_divided_or:

                # If 'AND' is included in the keyword divided by 'OR', add it to 'filter'
                for keyword in keyword_divided_or.split(CONFIG.AND_SEARCH_CHARACTER):
                    if keyword_divided_or not in and_query:
                        and_query[keyword_divided_or] = {'bool': {'filter': []}}

                    and_query[keyword_divided_or]['bool']['filter'].append(
                        attr_query[_make_key_for_each_block_of_keywords(
                                           hint, keyword, or_match)])

            else:
                and_query[keyword_divided_or] = attr_query[
                    _make_key_for_each_block_of_keywords(hint, keyword_divided_or, or_match)
                ]

            if CONFIG.OR_SEARCH_CHARACTER in hint['keyword']:

                # If the keyword contains 'or', concatenate with 'should'
                if not or_query:
                    or_query = {'bool': {'should': []}}

                or_query['bool']['should'].append(and_query[keyword_divided_or])

            else:
                or_query = and_query[keyword_divided_or]

        if len(hints) > 1:
            # If conditions are specified for multiple attributes in advanced search,
            # connect with 'filter'
            if not res_query:
                res_query = {'bool': {'filter': []}}

            res_query['bool']['filter'].append(or_query)

        else:
            res_query = or_query

    return res_query


def _make_an_attribute_filter(hint, keyword):
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
    4. After the above process, create a 'nested' query and return it.

    Args:
        hint (dict[str, str]): Dictionary of attribute names and search keywords to be processed
        keyword (str): String to search for
            String of the smallest unit in which search keyword is separated by `AND` and `OR`

    Returns:
        dict[str, str]: Created attribute filter

    """
    cond_attr = []
    cond_attr.append({
        'term': {'attr.name': hint['name']}
    })

    date_results = _is_date(keyword)
    if date_results:
        date_cond = {
            'range': {
                'attr.date_value': {
                    'format': 'yyyy-MM-dd'
                }
            },
        }
        for (range_check, date_obj) in date_results:
            timestr = date_obj.strftime('%Y-%m-%d')
            if range_check == '<':
                # search of before date user specified
                date_cond['range']['attr.date_value']['lt'] = timestr

            elif range_check == '>':
                # search of after date user specified
                date_cond['range']['attr.date_value']['gt'] = timestr

            else:
                # search of exact day
                date_cond['range']['attr.date_value']['gte'] = timestr
                date_cond['range']['attr.date_value']['lte'] = timestr

        cond_attr.append(date_cond)

    else:
        hint_kyeword_val = _get_hint_keyword_val(keyword)
        cond_val = [{'match': {'attr.value': hint_kyeword_val}}]

        if hint_kyeword_val:
            if 'exact_match' not in hint:
                cond_val.append({
                    'regexp': {
                        'attr.value': _get_regex_pattern(hint_kyeword_val)
                    }
                })

            cond_attr.append({'bool': {'should': cond_val}})

        else:
            cond_val_tmp = [{'bool': {'must_not': {'exists': {'field': 'attr.date_value'}}}}]
            cond_val_tmp.append({'bool': {'should': cond_val}})
            cond_attr.append({'bool': {'must': cond_val_tmp}})

    adding_cond = {
        'nested': {
            'path': 'attr',
            'query': {
                'bool': {}
            }
        }
    }
    adding_cond['nested']['query']['bool']['filter'] = cond_attr

    return adding_cond


def execute_query(query):
    """Run a search query.

    Args:
        query (dict[str, str]): Search query

    Raises:
        Exception: If query execution fails, output error details.

    Returns:
        dict[str, str]: Search execution result

    """
    try:
        res = ESS().search(body=query, ignore=[404], sort=['name.keyword:asc'])
    except Exception as e:
        raise(e)

    return res


def make_search_results(results, res, hint_attrs, limit, hint_referral):
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
        results (dict[str, str]): Variable for final search result storage
        res (`str`, optional): Search results for Elasticsearch
        hint_entity_ids (list(str)): Entity ID specified in the search condition input
        hint_attrs (list(dict[str, str])): A list of search strings and attribute sets
        limit (int): Maximum number of search results to return
        hint_referral (str): Input value used to refine the reference entry.
            Use only for advanced searches.

    Returns:
        dict[str, str]: A set of attributes and attribute values associated with the entry
            that was hit in the search

    """
    from entry.models import Entry, AttributeValue

    # set numbers of found entries
    results['ret_count'] = res['hits']['total']

    # get django objects from the hit information from Elasticsearch
    hit_entry_ids = [x['_id'] for x in res['hits']['hits']]
    if isinstance(hint_referral, str) and hint_referral:
        # If the hint_referral parameter is specified,
        # this filters results that only have specified referral entry.

        if (CONFIG.EMPTY_SEARCH_CHARACTER == hint_referral or
                CONFIG.EMPTY_SEARCH_CHARACTER_CODE == hint_referral):

            hit_entry_ids_num = [int(x) for x in hit_entry_ids]
            filtered_ids = set(hit_entry_ids_num) - set(AttributeValue.objects.filter(
                    Q(referral__id__in=hit_entry_ids,
                      parent_attr__is_active=True,
                      is_latest=True) |
                    Q(referral__id__in=hit_entry_ids,
                      parent_attr__is_active=True,
                      parent_attrv__is_latest=True)
                    ).values_list('referral_id', flat=True))

        else:

            filtered_ids = AttributeValue.objects.filter(
                    Q(parent_attr__parent_entry__name__iregex=prepend_escape_character(
                        CONFIG.ESCAPE_CHARACTERS_REFERRALS_ENTRY, hint_referral),
                      referral__id__in=hit_entry_ids,
                      is_latest=True) |
                    Q(parent_attr__parent_entry__name__iregex=prepend_escape_character(
                        CONFIG.ESCAPE_CHARACTERS_REFERRALS_ENTRY, hint_referral),
                      referral__id__in=hit_entry_ids,
                      parent_attrv__is_latest=True)
                    ).values_list('referral', flat=True)

        hit_entries = Entry.objects.filter(pk__in=filtered_ids, is_active=True)

        # reset matched count by filtered results by hint_referral parameter
        results['ret_count'] = len(hit_entries)
    else:
        hit_entries = Entry.objects.filter(id__in=hit_entry_ids, is_active=True)

    hit_infos = {}
    for entry in hit_entries:
        if len(hit_infos) >= limit:
            break

        hit_infos[entry] = [
            x['_source']['attr'] for x in res['hits']['hits'] if int(x['_id']) == entry.id
        ][0]

    for (entry, hit_attrs) in sorted(hit_infos.items(), key=lambda x: x[0].name):
        # If 'keyword' parameter is specified and hited entry doesn't have value at the targt
        # attribute, that entry should be removed from result. This processing may be worth to
        # do before refering entry from DB for saving time of server-side processing.
        for hint in hint_attrs:
            if ('keyword' in hint and hint['keyword'] and
                    # This checks hitted entry has specified attribute
                    not [x for x in hit_attrs if x['name'] == hint['name']]):
                continue

        ret_info = {
            'entity': {'id': entry.schema.id, 'name': entry.schema.name},
            'entry': {'id': entry.id, 'name': entry.name},
            'attrs': {},
        }

        # When 'hint_referral' parameter is specifed, return referred entries for each results
        if hint_referral is not False:
            ret_info['referrals'] = [{
                'id': x.id,
                'name': x.name,
                'schema': x.schema.name,
            } for x in entry.get_referred_objects()]

        # formalize attribute values according to the type
        for attrinfo in hit_attrs:
            if attrinfo['name'] in ret_info['attrs']:
                ret_attrinfo = ret_info['attrs'][attrinfo['name']]
            else:
                ret_attrinfo = ret_info['attrs'][attrinfo['name']] = {}

            # if target attribute is array type, then values would be stored in array
            if attrinfo['name'] not in ret_info['attrs']:
                if attrinfo['type'] & AttrTypeValue['array']:
                    ret_info['attrs'][attrinfo['name']] = []
                else:
                    ret_info['attrs'][attrinfo['name']] = ret_attrinfo

            ret_attrinfo['type'] = attrinfo['type']
            if (attrinfo['type'] == AttrTypeValue['string'] or
                    attrinfo['type'] == AttrTypeValue['text']):

                if attrinfo['value']:
                    ret_attrinfo['value'] = attrinfo['value']
                elif 'date_value' in attrinfo and attrinfo['date_value']:
                    ret_attrinfo['value'] = attrinfo['date_value'].split('T')[0]

            elif attrinfo['type'] == AttrTypeValue['boolean']:
                ret_attrinfo['value'] = attrinfo['value']

            elif attrinfo['type'] == AttrTypeValue['date']:
                ret_attrinfo['value'] = attrinfo['date_value']

            elif (attrinfo['type'] == AttrTypeValue['object'] or
                  attrinfo['type'] == AttrTypeValue['group']):
                ret_attrinfo['value'] = {'id': attrinfo['referral_id'], 'name': attrinfo['value']}

            elif (attrinfo['type'] == AttrTypeValue['named_object']):
                ret_attrinfo['value'] = {
                        attrinfo['key']: {'id': attrinfo['referral_id'], 'name': attrinfo['value']}
                }

            elif attrinfo['type'] & AttrTypeValue['array']:
                if 'value' not in ret_attrinfo:
                    ret_attrinfo['value'] = []

                if attrinfo['type'] == AttrTypeValue['array_string']:
                    if 'date_value' in attrinfo:
                        ret_attrinfo['value'].append(attrinfo['date_value'].split('T')[0])
                    else:
                        ret_attrinfo['value'].append(attrinfo['value'])

                elif attrinfo['type'] == AttrTypeValue['array_object']:
                    ret_attrinfo['value'].append({
                        'id': attrinfo['referral_id'],
                        'name': attrinfo['value']
                    })

                elif attrinfo['type'] == AttrTypeValue['array_named_object']:
                    ret_attrinfo['value'].append({
                        attrinfo['key']: {'id': attrinfo['referral_id'], 'name': attrinfo['value']}
                    })

        results['ret_values'].append(ret_info)

    return results


def is_date_check(value):
    try:
        for delimiter in ['-', '/']:
            date_format = '%%Y%(del)s%%m%(del)s%%d' % {'del': delimiter}

            if re.match(r'^[<>]?[0-9]{4}%(del)s[0-9]+%(del)s[0-9]+' % {'del': delimiter}, value):

                if value[0] in ['<', '>']:
                    return (value[0],
                            datetime.strptime(value[1:].split(' ')[0], date_format))
                else:
                    return ('', datetime.strptime(value.split(' ')[0], date_format))

    except ValueError:
        # When datetime.strptie raised ValueError, it means value parameter maches date
        # format but they are not date value. In this case, we should deal it with a
        # string value.
        return None

    return None


def _is_date(value):
    # checks all specified value is date format
    result = [is_date_check(x) for x in value.split(' ') if x]

    # If result is not empty and all value is date, this returns the result
    return result if result and all(result) else None
