from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airone.exceptions import ElasticsearchException
from airone.lib.log import Logger
from entity.models import Entity, EntityAttr
from entry.models import Entry
from entry.settings import CONFIG

SEARCH_ENTRY_LIMIT = 999999


class ReferSerializer(serializers.Serializer):
    entity = serializers.CharField(max_length=200)
    entry = serializers.CharField(max_length=200, required=False)
    is_any = serializers.BooleanField(default=False)
    attrs = serializers.ListField(required=False)
    refers = serializers.ListField(required=False)

    def validate_entity(self, entity_name):
        if not Entity.objects.filter(name=entity_name, is_active=True).exists():
            raise ValidationError("There is no specified Entity (%s)" % entity_name)

        return entity_name

    def validate(self, data):
        entity = Entity.objects.filter(name=data["entity"], is_active=True).first()
        data["entity_id"] = entity.id
        return data


class AttrSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    value = serializers.CharField(max_length=200, required=False, allow_blank=True)
    is_any = serializers.BooleanField(default=False)
    attrs = serializers.ListField(required=False)
    refers = serializers.ListField(required=False)

    def validate_name(self, name):
        if not EntityAttr.objects.filter(name=name, is_active=True).exists():
            raise ValidationError("There is no specified Attribute (%s)" % name)

        return name

    def validate_is_any(self, value):
        return value


class EntrySearchChainSerializer(serializers.Serializer):
    entities = serializers.ListField(child=serializers.CharField(max_length=200))
    attrs = serializers.ListField(child=AttrSerializer(), required=False)
    refers = serializers.ListField(child=ReferSerializer(), required=False)
    is_any = serializers.BooleanField(default=False)

    def validate_is_any(self, value):
        return value

    def validate_entities(self, entities):
        ret_data = []
        for id_or_name in entities:
            if isinstance(id_or_name, int):
                if Entity.objects.filter(id=id_or_name, is_active=True).exists():
                    ret_data.append(id_or_name)

            elif isinstance(id_or_name, str):
                if (
                    id_or_name.isdecimal()
                    and Entity.objects.filter(id=int(id_or_name), is_active=True).exists()
                ):
                    ret_data.append(int(id_or_name))

                elif Entity.objects.filter(name=id_or_name, is_active=True).exists():
                    ret_data.append(Entity.objects.get(name=id_or_name, is_active=True).id)

        return ret_data

    def validate(self, data):
        # This validates and complements conditions contexts, expecially this method
        # adds "entities" parameter for each Attribute conditions. That is an internal
        # one to indicate Entity for searching Entries at Attribute conditions using
        # Entry.search_entries() method.
        def _validate_attribute(attrname, entities):
            # This validates whethere it is possible that Entity has specified Attribute
            if not any(
                [
                    EntityAttr.objects.filter(name=attrname, is_active=True, parent_entity__pk=x)
                    for x in entities
                ]
            ):
                raise ValidationError("Invalid Attribute name (%s) was specified" % str(attrname))

        def _complement_entities(condition, entities):
            if "name" in condition:
                # This Attributes must be existed because existance check has already been done
                entity_ids = []
                for attr in [
                    EntityAttr.objects.get(
                        name=condition["name"], is_active=True, parent_entity__pk=x
                    )
                    for x in entities
                ]:
                    # complements Entity IDs that this condition implicitly expects
                    entity_ids += [x.id for x in attr.referral.filter(is_active=True)]

                # complement Entity IDs of each conditions
                condition["entities"] = list(set(entity_ids))

        def _get_serializer(condition):
            # This determines which serializer is from condition context.
            if "entity" in condition:
                return ReferSerializer
            else:
                return AttrSerializer

        def _may_validate_and_complement_condition(condition, entities, serializer_class):
            serializer = serializer_class(data=condition)
            if not serializer.is_valid():
                raise ValidationError("Invalid condition(%s) was specified" % str(condition))

            if not entities:
                raise ValidationError("Condition(%s) couldn't find valid Entities" % str(condition))

            validated_data = serializer.validated_data
            if "name" in validated_data:
                _validate_attribute(validated_data["name"], entities)

            if isinstance(serializer, AttrSerializer):
                # complement "entities" parameter at this condition
                _complement_entities(validated_data, entities)

            if isinstance(serializer, ReferSerializer):
                validated_data["entities"] = [validated_data["entity_id"]]

            # call this method recursively to validate and complement value for each conditions
            if "attrs" in validated_data:
                validated_data["attrs"] = [
                    _may_validate_and_complement_condition(
                        x, validated_data["entities"], AttrSerializer
                    )
                    for x in validated_data["attrs"]
                ]

            elif "refers" in validated_data:
                validated_data["refers"] = [
                    _may_validate_and_complement_condition(
                        x, validated_data["entities"], ReferSerializer
                    )
                    for x in validated_data["refers"]
                ]

            return validated_data

        # validate parameter context
        if data.get("attrs"):
            data["attrs"] = [
                _may_validate_and_complement_condition(x, data["entities"], AttrSerializer)
                for x in data["attrs"]
            ]

        if data.get("refers"):
            data["refers"] = [
                _may_validate_and_complement_condition(x, data["entities"], ReferSerializer)
                for x in data["refers"]
            ]

        return data

    def merge_search_result(self, stored_list, result_data, is_any):
        def _deduplication(item_list):
            """
            This removes duplication items, that have same Entry-ID with other ones,from item_list
            """
            returned_items = []
            for item in item_list:
                if item["id"] not in [x["id"] for x in returned_items]:
                    returned_items.append(item)

            return returned_items

        if is_any:
            # This is OR condition processing
            result = result_data + stored_list

        else:
            # This is AND condition processing
            # The "stored_id_list" is an explanatory variable that only has Entry-ID
            # of stored_list Entry information
            if stored_list:
                stored_id_list = [x["id"] for x in stored_list]
                result = [x for x in result_data if x["id"] in stored_id_list]
            else:
                result = result_data

        return _deduplication(result)

    def backward_search_entries(self, user, queries, entity_id_list, is_any):
        # digging into the condition tree to get to leaf condition by depth-first search
        accumulated_result = []

        def _do_backward_search(sub_query, sub_query_result):
            # make query to search Entries using Entry.search_entries()
            search_keyword = "|".join([x["name"] for x in sub_query_result])
            if isinstance(sub_query.get("entry"), str) and len(sub_query["entry"]) > 0:
                search_keyword = sub_query.get("entry")

            # Query for forward search
            query_params = {
                "user": user,
                "hint_entity_ids": entity_id_list,
                "hint_referral": search_keyword,
                "hint_referral_entity_id": sub_query["entity_id"],
                "limit": 99999,
            }

            # get Entry informations from result
            try:
                search_result = Entry.search_entries(**query_params)
            except Exception as e:
                Logger.warning("Search Chain API error:%s" % e)
                raise ElasticsearchException()

            if search_result["ret_count"] > CONFIG.SEARCH_CHAIN_ACCEPTABLE_RESULT_COUNT:
                Logger.warning("Search Chain API error: SEARCH_CHAIN_ACCEPTABLE_RESULT_COUNT")
                raise ElasticsearchException()

            return [x["entry"] for x in search_result["ret_values"]]

        # This expects only AttrSerialized sub-query
        for sub_query in queries:
            (is_leaf, sub_query_result) = self.search_entries(user, sub_query)
            if not is_leaf and not sub_query_result:
                # In this case, it's useless to continue to search processing because
                # there is no possiblity to find out data that user wants to.
                if is_any:
                    continue
                else:
                    return (False, [])

            # This divides results into small chunks, that will be sent to the elasticsearch again
            # when it has large amount of data. The size of each chunks is SEARCH_ENTRY_LIMIT
            # at most.
            dividing_index = 0
            if len(sub_query_result) > 0:
                search_results = []
                while (dividing_index * SEARCH_ENTRY_LIMIT) < len(sub_query_result):
                    chunk_result = sub_query_result[
                        dividing_index
                        * SEARCH_ENTRY_LIMIT : (dividing_index + 1)
                        * SEARCH_ENTRY_LIMIT
                    ]
                    dividing_index += 1

                    search_results += _do_backward_search(sub_query, chunk_result)

            else:
                # This search Entries with hint values from sub_query and sub_query_result
                search_results = _do_backward_search(sub_query, sub_query_result)

            # merge result to the accumulated ones considering is_any value
            accumulated_result = self.merge_search_result(
                accumulated_result, search_results, is_any
            )

        # The first return value (False) describe this result returned by NO-leaf-node
        return (False, accumulated_result)

    def forward_search_entries(self, user, queries, entity_id_list, is_any):
        # digging into the condition tree to get to leaf condition by depth-first search
        accumulated_result = []

        def _do_forward_search(sub_query, sub_query_result):
            # make query to search Entries using Entry.search_entries()
            search_keyword = "|".join([x["name"] for x in sub_query_result])
            if isinstance(sub_query.get("value"), str) and len(sub_query["value"]) > 0:
                search_keyword = sub_query.get("value")

            elif sub_query.get("value") == "":
                # When value has empty string, this specify special character "\",
                # which will match Entries that refers nothing Entry at specified Attribute.
                search_keyword = "\\"

            # Query for forward search
            hint_attrs = [
                {
                    "name": sub_query["name"],
                    "keyword": search_keyword,
                }
            ]

            # get Entry informations from result
            try:
                search_result = Entry.search_entries(user, entity_id_list, hint_attrs, limit=99999)
            except Exception as e:
                Logger.warning("Search Chain API error:%s" % e)
                raise ElasticsearchException()

            if search_result["ret_count"] > CONFIG.SEARCH_CHAIN_ACCEPTABLE_RESULT_COUNT:
                Logger.warning("Search Chain API error: SEARCH_CHAIN_ACCEPTABLE_RESULT_COUNT")
                raise ElasticsearchException()

            return [x["entry"] for x in search_result["ret_values"]]

        # This expects only AttrSerialized sub-query
        for sub_query in queries:
            (is_leaf, sub_query_result) = self.search_entries(user, sub_query)
            if not is_leaf and not sub_query_result:
                # In this case, it's useless to continue to search processing because
                # there is no possiblity to find out data that user wants to.
                if is_any:
                    continue
                else:
                    return (False, [])

            # This divides results into small chunks, that will be sent to the elasticsearch again
            # when it has large amount of data. The size of each chunks is SEARCH_ENTRY_LIMIT
            # at most.
            dividing_index = 0
            if len(sub_query_result) > 0:
                search_results = []
                while (dividing_index * SEARCH_ENTRY_LIMIT) < len(sub_query_result):
                    chunk_result = sub_query_result[
                        dividing_index
                        * SEARCH_ENTRY_LIMIT : (dividing_index + 1)
                        * SEARCH_ENTRY_LIMIT
                    ]
                    dividing_index += 1

                    search_results += _do_forward_search(sub_query, chunk_result)

            else:
                # This search Entries with hint values from sub_query and sub_query_result
                search_results = _do_forward_search(sub_query, sub_query_result)

            # merge current result to the accumulated ones considering is_any value
            accumulated_result = self.merge_search_result(
                accumulated_result, search_results, is_any
            )

        # The first return value (False) describe this result returned by NO-leaf-node
        return (False, accumulated_result)

    def search_entries(self, user, query=None):
        if query is None:
            query = self.validated_data

        accumulated_result = []
        is_leaf = True
        if len(query.get("attrs", [])) > 0:
            is_leaf = False
            sub_query = query.get("attrs", [])

            (_, results) = self.forward_search_entries(
                user, sub_query, query["entities"], query["is_any"]
            )
            accumulated_result = self.merge_search_result(
                accumulated_result, results, query["is_any"]
            )

        if len(query.get("refers", [])) > 0:
            is_leaf = False
            sub_query = query.get("refers", [])

            (_, results) = self.backward_search_entries(
                user, sub_query, query["entities"], query["is_any"]
            )
            accumulated_result = self.merge_search_result(
                accumulated_result, results, query["is_any"]
            )

        # In the leaf condition return nothing
        # The first return value describe whethere this is leaf condition or not.
        # (True means result is returned by leaf-node)
        #
        # Empty result of second returned value has different meaning depends on
        # whethere that is leaf condition or intermediate one.
        # * Leaf condition:
        #   - it must return empty whatever condition.
        #     it should continue processing
        #
        # * Intermediate one:
        #   - it returns empty when there is no result.
        #     it's useless to continue this processing because there is no possibility
        #     to find out any data, which user wants to
        return (is_leaf, accumulated_result)

    def is_attr_chained(self, entry, attrs=None, is_any=False):
        if not attrs:
            attrs = self.validated_data["attrs"]
            is_any = self.validated_data["is_any"]

        # This is a helper method to check referral entry meets chaining conditions.
        def _is_attrv_referral_chained(attrv, info):
            if attrv.referral is None or not attrv.referral.is_active:
                if info.get("value") == "":
                    # The case when Attribute value doesn't refer Entry and query expects it is
                    return True

                elif info.get("value") is not None:
                    return False

                elif info.get("value") is None:
                    # When user specified query has sub-query, this returns False.
                    # but this returns True when query is terminated by this condition.
                    return info.get("attrs") is None

                else:
                    raise RuntimeError("Unexpected situation was happend")

            # In this code, attrv.referral.id must be existed
            if info.get("value") == "":
                # The case when Attribute value refers actual Entry but query expects it's blank
                return False

            elif info.get("value", "") not in attrv.referral.name:
                # The case when Attribute value deons't refer, or
                # referred Entry is not expected one.
                return False

            elif info.get("attrs"):
                return self.is_attr_chained(
                    Entry.objects.get(id=attrv.referral.id), info["attrs"], info["is_any"]
                )

            return not info["is_any"]

        for info in attrs:
            attrv = entry.get_attrv(info["name"])
            if not attrv:
                # NOTE: This describes logic procedure considered with is_any and
                #       info.get("value") context.
                #
                # * is_any
                #   - True: OR condition
                #       - when failed:    continue next
                #       - when succeeded: continue next
                #   - False: AND condition
                #       - when failed:  return False immediately
                #       - when succeeded: continue next
                #
                # * info.get("value")
                #   - None: match all value
                #   - "": match only empty value
                #   - other: match only contained value is matched with attrv.value or
                #            referral entry
                #     (This processing is work in _is_attrv_referral_chained() for referral entry)
                if is_any or (info.get("vlaue") == "" and not is_any):
                    continue

                else:
                    # In this case, it doesn't meet specified condition at least one.
                    # Then, there is no nocessity to check rest of query any more
                    # when is_any parameter is False (it means AND condition).
                    return False

            v = attrv.get_value(with_metainfo=True)
            if v["value"] is None:
                if is_any or (info.get("vlaue") == "" and not is_any):
                    continue

                else:
                    # In this case, it doesn't meet specified condition at least one.
                    # Then, there is no nocessity to check rest of query any more
                    # when is_any parameter is False (it means AND condition).
                    return False

            elif isinstance(v["value"], str) and info.get("value", "") in v["value"]:
                # This confirms text attribute value (e.g. AttrTypeValue['string'])
                # has expected value. It returns True when the "is_any" parameter
                # is True (it means OR condition).
                if is_any:
                    return True

            elif isinstance(v["value"], dict):
                # this confirms simple referral value (e.g. AttrTypeValue['object'])
                # has expected referral
                condition = _is_attrv_referral_chained(attrv, info)
                if not condition and not is_any:
                    # This returns False immediately whenever it doesn't meet specified
                    # conditions at least one when the "is_any" parameter is False
                    # (it means AND condition).
                    return False

                elif condition and is_any:
                    # This returns True immediately whenever it doesn't meet specified
                    # conditions at least one when the "is_any" parameter is True
                    # (it means OR condition).
                    return True

            elif isinstance(v["value"], list):
                # This is a termination condition when Attribute value refers no Entry.
                if not attrv.data_array.exists() and info.get("value") != "" and not is_any:
                    # This returns False immediately whenever there is no attribute value
                    # when the "is_any" parameter is False (it means AND condition).
                    # except for the case when query expects this Attribute value doesn't
                    # refer any Entries
                    return False

                elif attrv.data_array.exists():
                    # This variable (is_matched) is necessary for AND condition.
                    # We couldn't determine whether search is faileda until all co-Attribute
                    # value have been checked. It should return False when all co-Attribute
                    # values wouldn't meet specified condition if "is_any" parameter is False
                    # (it means AND condition).
                    is_matched = False
                    for co_attrv in attrv.data_array.all():
                        condition = _is_attrv_referral_chained(co_attrv, info)
                        if condition:
                            is_matched = True

                            # This returns True immediately whenever it doesn't meet specified
                            # conditions at least one when the "is_any" parameter is True
                            # (it means OR condition).
                            if is_any:
                                return True

                    if not is_matched and not is_any:
                        return False

        # This returns False when "is_any" parameter is True (it means OR condition), because
        # the query results didn't meet any specified conditions (it means there is no Entry
        # that matches specified query).
        # In opposiet, this returns True when "is_any" parameter is False (it means AND condition)
        # because, result matches all specified conditions.
        return not is_any
