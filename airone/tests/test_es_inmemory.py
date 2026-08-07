"""Behaviour tests for the in-process Elasticsearch stand-in.

These lock in the places where a naive implementation would silently disagree
with a real cluster -- Lucene's regexp dialect, how `filter` affects scoring,
how JSON types are indexed into a text field -- because a wrong answer here
looks like a product bug, not a test-harness bug.
"""

import os
import tempfile

from django.test import SimpleTestCase, override_settings
from elasticsearch import NotFoundError

from airone.lib.es_inmemory import STORE, InMemoryElasticsearch

INDEX = "test-es-inmemory"

# ES_CONFIG without PERSIST_PATH: no test should touch the filesystem unless it
# is the persistence test itself.
NO_PERSIST = {"INDEX_NAME": INDEX, "PERSIST_PATH": None, "MAXIMUM_RESULTS_NUM": 500000}


def doc(name, entity=("model", 1), attrs=(), referrals=(), is_readable=True):
    """A document shaped like the one Entry.get_es_document() produces."""
    return {
        "name": name,
        "entity": {"id": entity[1], "name": entity[0]},
        "attr": [
            {
                "name": attr_name,
                "type": 2,
                "key": "",
                "value": value,
                "date_value": date_value,
                "referral_id": "",
                "is_readable": True,
            }
            for attr_name, value, date_value in attrs
        ],
        "referrals": list(referrals),
        "is_readable": is_readable,
    }


@override_settings(ES_CONFIG=NO_PERSIST)
class EngineTestBase(SimpleTestCase):
    def setUp(self):
        STORE.reset()
        self.es = InMemoryElasticsearch(INDEX)
        self.es.indices.create(index=INDEX)

    def index(self, doc_id, document):
        self.es.index(id=doc_id, body=document)

    def names(self, body, **kwargs):
        res = self.es.search(body=body, **kwargs)
        return [hit["_source"]["name"] for hit in res["hits"]["hits"]]

    def ids(self, body, **kwargs):
        res = self.es.search(body=body, **kwargs)
        return [hit["_id"] for hit in res["hits"]["hits"]]


class MatchingTest(EngineTestBase):
    def test_term_and_match_are_whole_value_equality(self):
        # Every analysed field in Pagoda's mapping uses the `keyword` analyzer,
        # so neither clause does substring or token matching.
        self.index(1, doc("alpha beta"))
        for clause in ({"term": {"name": "alpha beta"}}, {"match": {"name": "alpha beta"}}):
            self.assertEqual(self.names({"query": clause}), ["alpha beta"], clause)
        for clause in ({"term": {"name": "alpha"}}, {"match": {"name": "beta"}}):
            self.assertEqual(self.names({"query": clause}), [], clause)

    def test_keyword_subfield_resolves_to_the_same_value(self):
        self.index(1, doc("alpha"))
        self.assertEqual(self.names({"query": {"term": {"name.keyword": "alpha"}}}), ["alpha"])

    def test_ids_query(self):
        self.index(1, doc("one"))
        self.index(2, doc("two"))
        self.assertEqual(self.ids({"query": {"ids": {"values": ["2"]}}}), ["2"])
        # Callers pass ints as well as strings.
        self.assertEqual(self.ids({"query": {"ids": {"values": [1]}}}), ["1"])

    def test_exists_ignores_nulls(self):
        self.index(1, doc("has", attrs=[("when", "", "2020-01-01")]))
        self.index(2, doc("hasnt", attrs=[("when", "", None)]))
        body = {
            "query": {"nested": {"path": "attr", "query": {"exists": {"field": "attr.date_value"}}}}
        }
        self.assertEqual(self.names(body), ["has"])

    def test_unsupported_clause_raises_rather_than_matching_nothing(self):
        self.index(1, doc("one"))
        with self.assertRaises(ValueError):
            self.es.search(body={"query": {"span_near": {}}})


class RegexpTest(EngineTestBase):
    def test_anchors_are_literal_characters(self):
        # Lucene has no anchor operators, so "^" and "$" are ordinary
        # characters there while Python would treat them as assertions. Entry
        # names really do contain them, and getting this wrong turns a matching
        # query into a silently empty one.
        self.index(1, doc("test$3"))
        self.index(2, doc("test^10"))
        self.assertEqual(
            self.names({"query": {"regexp": {"name": ".*[tT][eE][sS][tT]$3.*"}}}), ["test$3"]
        )
        self.assertEqual(
            self.names({"query": {"regexp": {"name": ".*[tT][eE][sS][tT]^10.*"}}}), ["test^10"]
        )

    def test_escaped_metacharacters_match_literally(self):
        self.index(1, doc("a(b)c"))
        self.assertEqual(self.names({"query": {"regexp": {"name": ".*a\\(b\\)c.*"}}}), ["a(b)c"])

    def test_pattern_is_fully_anchored(self):
        # Lucene's regexp must match the whole value, unlike Python's re.search.
        self.index(1, doc("prefix-value-suffix"))
        self.assertEqual(self.names({"query": {"regexp": {"name": "value"}}}), [])
        self.assertEqual(
            self.names({"query": {"regexp": {"name": ".*value.*"}}}), ["prefix-value-suffix"]
        )

    def test_character_class_negation_still_works(self):
        self.index(1, doc("abc"))
        self.index(2, doc("xbc"))
        self.assertEqual(self.names({"query": {"regexp": {"name": "[^x]bc"}}}), ["abc"])

    def test_non_string_values_are_matched_as_indexed_text(self):
        # attr.value is mapped as text but holds booleans and numbers; ES
        # stringifies them on the way in, which is what makes the "has any
        # value" filter (regexp ".+") match a boolean attribute.
        self.index(1, doc("flagged", attrs=[("flag", True, None)]))
        self.index(2, doc("numbered", attrs=[("count", 12, None)]))
        self.index(3, doc("empty", attrs=[("flag", None, None)]))
        body = {"query": {"nested": {"path": "attr", "query": {"regexp": {"attr.value": ".+"}}}}}
        self.assertEqual(sorted(self.names(body)), ["flagged", "numbered"])

    def test_boolean_matches_its_lowercase_text_form(self):
        self.index(1, doc("flagged", attrs=[("flag", False, None)]))
        body = {"query": {"nested": {"path": "attr", "query": {"match": {"attr.value": "False"}}}}}
        self.assertEqual(self.names(body), ["flagged"])


class BoolTest(EngineTestBase):
    def setUp(self):
        super().setUp()
        self.index(1, doc("alpha"))
        self.index(2, doc("beta"))

    def test_should_alone_requires_one_match(self):
        body = {"query": {"bool": {"should": [{"term": {"name": "alpha"}}]}}}
        self.assertEqual(self.names(body), ["alpha"])

    def test_should_is_optional_once_filter_is_present(self):
        # ES only makes "should" mandatory when there is nothing else to match.
        body = {
            "query": {
                "bool": {
                    "filter": [{"term": {"is_readable": True}}],
                    "should": [{"term": {"name": "nothing-matches-this"}}],
                }
            }
        }
        self.assertEqual(sorted(self.names(body)), ["alpha", "beta"])

    def test_minimum_should_match_is_honoured(self):
        body = {
            "query": {
                "bool": {
                    "filter": [{"term": {"is_readable": True}}],
                    "should": [{"term": {"name": "alpha"}}],
                    "minimum_should_match": 1,
                }
            }
        }
        self.assertEqual(self.names(body), ["alpha"])

    def test_must_not_excludes(self):
        body = {"query": {"bool": {"must_not": [{"term": {"name": "alpha"}}]}}}
        self.assertEqual(self.names(body), ["beta"])

    def test_empty_should_list_is_not_a_constraint(self):
        body = {"query": {"bool": {"filter": [], "should": []}}}
        self.assertEqual(sorted(self.names(body)), ["alpha", "beta"])


class ScoringTest(EngineTestBase):
    def test_filter_clauses_do_not_contribute_to_the_score(self):
        # This is what makes simple search rank an entry matched by *name*
        # above one matched only through the attribute clause, which Pagoda
        # wraps in a bool/filter.
        # The names are chosen so the secondary sort disagrees with the
        # intended order: if the filter clause did contribute a point, the two
        # would tie and "a_by_attr" would come first.
        self.index(1, doc("z_by_name"))
        self.index(2, doc("a_by_attr", attrs=[("val", "hoge", None)]))
        body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"name": "z_by_name"}},
                        {
                            "bool": {
                                "filter": {
                                    "nested": {
                                        "path": "attr",
                                        "query": {"match": {"attr.value": "hoge"}},
                                    }
                                }
                            }
                        },
                    ]
                }
            },
            "sort": [{"_score": {"order": "desc"}, "name.keyword": {"order": "asc"}}],
        }
        self.assertEqual(self.names(body), ["z_by_name", "a_by_attr"])

    def test_more_matching_should_clauses_scores_higher(self):
        self.index(1, doc("entry"))
        self.index(2, doc("[entry]"))
        body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"name": "entry"}},
                        {"regexp": {"name": ".*[eE][nN][tT][rR][yY].*"}},
                    ]
                }
            },
            "sort": [{"_score": {"order": "desc"}, "name.keyword": {"order": "asc"}}],
        }
        # By name alone "[entry]" sorts first; the extra matching clause on
        # "entry" is what reverses them.
        self.assertEqual(self.names(body), ["entry", "[entry]"])


class NestedTest(EngineTestBase):
    def test_conditions_must_hold_within_one_sub_document(self):
        # The whole point of a nested mapping: "name=a AND value=x" must be
        # satisfied by a single attribute, not by two different ones.
        self.index(1, doc("split", attrs=[("a", "other", None), ("b", "x", None)]))
        self.index(2, doc("together", attrs=[("a", "x", None)]))
        body = {
            "query": {
                "nested": {
                    "path": "attr",
                    "query": {
                        "bool": {
                            "filter": [
                                {"term": {"attr.name": "a"}},
                                {"term": {"attr.value": "x"}},
                            ]
                        }
                    },
                }
            }
        }
        self.assertEqual(self.names(body), ["together"])

    def test_single_object_behaves_as_a_one_element_nested_list(self):
        self.index(1, doc("one", entity=("model", 7)))
        body = {"query": {"nested": {"path": "entity", "query": {"term": {"entity.id": 7}}}}}
        self.assertEqual(self.names(body), ["one"])

    def test_inner_hits_returns_only_matching_sub_documents(self):
        self.index(1, doc("one", attrs=[("wanted", "x", None), ("other", "y", None)]))
        body = {
            "query": {
                "bool": {
                    "filter": {
                        "nested": {
                            "path": "attr",
                            "inner_hits": {"_source": ["attr.name"]},
                            "query": {"term": {"attr.value": "x"}},
                        }
                    }
                }
            }
        }
        hit = self.es.search(body=body)["hits"]["hits"][0]
        sources = [h["_source"] for h in hit["inner_hits"]["attr"]["hits"]["hits"]]
        self.assertEqual(sources, [{"name": "wanted"}])

    def test_declared_inner_hits_are_present_even_with_no_matches(self):
        self.index(1, doc("one", attrs=[("a", "x", None)]))
        body = {
            "query": {
                "bool": {
                    "should": [
                        {"term": {"name": "one"}},
                        {
                            "nested": {
                                "path": "attr",
                                "inner_hits": {},
                                "query": {"term": {"attr.value": "no-such-value"}},
                            }
                        },
                    ]
                }
            }
        }
        hit = self.es.search(body=body)["hits"]["hits"][0]
        self.assertEqual(hit["inner_hits"]["attr"]["hits"]["hits"], [])


class RangeTest(EngineTestBase):
    def setUp(self):
        super().setUp()
        self.index(1, doc("early", attrs=[("when", "", "2020-01-01")]))
        self.index(2, doc("late", attrs=[("when", "", "2021-06-15")]))
        self.index(3, doc("undated", attrs=[("when", "", None)]))

    def _range(self, spec):
        return sorted(
            self.names(
                {
                    "query": {
                        "nested": {
                            "path": "attr",
                            "query": {"range": {"attr.date_value": spec}},
                        }
                    }
                }
            )
        )

    def test_bounds(self):
        self.assertEqual(self._range({"gt": "2020-06-01"}), ["late"])
        self.assertEqual(self._range({"lt": "2020-06-01"}), ["early"])
        self.assertEqual(self._range({"gte": "2020-01-01", "lte": "2020-01-01"}), ["early"])
        self.assertEqual(self._range({"gte": "2019-01-01"}), ["early", "late"])

    def test_undated_documents_never_match_a_bounded_range(self):
        self.assertEqual(self._range({"gte": "1900-01-01"}), ["early", "late"])

    def test_datetimes_and_dates_compare_together(self):
        self.index(4, doc("stamped", attrs=[("when", "", "2020-03-01T12:30:00+00:00")]))
        self.assertEqual(self._range({"gte": "2020-02-01", "lte": "2020-04-01"}), ["stamped"])


class SortTest(EngineTestBase):
    def test_sort_by_name(self):
        for i, name in enumerate(["c", "a", "b"]):
            self.index(i, doc(name))
        self.assertEqual(self.names({"sort": [{"name.keyword": "asc"}]}), ["a", "b", "c"])
        self.assertEqual(
            self.names({"sort": [{"name.keyword": {"order": "desc"}}]}), ["c", "b", "a"]
        )

    def test_nested_sort_uses_the_filtered_attribute(self):
        self.index(1, doc("first", attrs=[("rank", "b", None), ("noise", "z", None)]))
        self.index(2, doc("second", attrs=[("rank", "a", None), ("noise", "a", None)]))
        body = {
            "sort": [
                {
                    "attr.value.keyword": {
                        "order": "asc",
                        "nested": {"path": "attr", "filter": {"term": {"attr.name": "rank"}}},
                    }
                },
                {"name.keyword": "asc"},
            ]
        }
        self.assertEqual(self.names(body), ["second", "first"])

    def test_documents_without_the_sort_value_come_last_in_both_directions(self):
        self.index(1, doc("has", attrs=[("rank", "m", None)]))
        self.index(2, doc("missing", attrs=[("other", "z", None)]))
        for order in ("asc", "desc"):
            body = {
                "sort": [
                    {
                        "attr.value.keyword": {
                            "order": order,
                            "nested": {
                                "path": "attr",
                                "filter": {"term": {"attr.name": "rank"}},
                            },
                        }
                    }
                ]
            }
            self.assertEqual(self.names(body), ["has", "missing"], order)

    def test_date_sort_orders_chronologically_not_lexically(self):
        self.index(1, doc("later", attrs=[("when", "", "2021-01-02T00:00:00+00:00")]))
        self.index(2, doc("earlier", attrs=[("when", "", "2020-12-31")]))
        body = {
            "sort": [
                {
                    "attr.date_value": {
                        "order": "asc",
                        "nested": {"path": "attr", "filter": {"term": {"attr.name": "when"}}},
                    }
                }
            ]
        }
        self.assertEqual(self.names(body), ["earlier", "later"])


class ResponseShapeTest(EngineTestBase):
    def setUp(self):
        super().setUp()
        for i in range(5):
            self.index(i, doc("name-%d" % i))

    def test_total_counts_all_matches_not_just_the_returned_window(self):
        res = self.es.search(body={"sort": [{"name.keyword": "asc"}]}, size=2)
        self.assertEqual(res["hits"]["total"]["value"], 5)
        self.assertEqual(len(res["hits"]["hits"]), 2)

    def test_from_offsets_the_window(self):
        body = {"sort": [{"name.keyword": "asc"}], "from": 3}
        self.assertEqual(self.names(body), ["name-3", "name-4"])

    def test_source_filtering_keeps_only_requested_fields(self):
        res = self.es.search(body={"_source": ["name"], "sort": [{"name.keyword": "asc"}]})
        self.assertEqual(list(res["hits"]["hits"][0]["_source"]), ["name"])


class WriteTest(EngineTestBase):
    def test_index_then_get(self):
        self.index(1, doc("one"))
        self.assertEqual(self.es.get(id=1)["_source"]["name"], "one")

    def test_get_missing_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.es.get(id=404)

    def test_delete_missing_raises_not_found(self):
        # Entry.unregister_es() relies on catching exactly this.
        with self.assertRaises(NotFoundError):
            self.es.delete(id=404)

    def test_bulk_indexes_action_document_pairs(self):
        self.es.bulk(body=[{"index": {"_id": 1}}, doc("one"), {"index": {"_id": 2}}, doc("two")])
        self.assertEqual(sorted(self.names({"query": {"match_all": {}}})), ["one", "two"])

    def test_delete_by_query_removes_only_matches(self):
        self.index(1, doc("keep"))
        self.index(2, doc("drop"))
        result = self.es.delete_by_query(index=INDEX, query={"term": {"name": "drop"}})
        self.assertEqual(result["deleted"], 1)
        self.assertEqual(self.names({"query": {"match_all": {}}}), ["keep"])

    def test_recreating_the_index_empties_it(self):
        self.index(1, doc("one"))
        self.es.indices.delete(index=INDEX, ignore_unavailable=True)
        self.es.indices.create(index=INDEX)
        self.assertEqual(self.es.count()["count"], 0)


class AggregationTest(EngineTestBase):
    def test_terms_aggregation_finds_duplicated_attribute_values(self):
        # Backs the "duplicated values" advanced-search filter.
        self.index(1, doc("a", attrs=[("val", "dup", None)]))
        self.index(2, doc("b", attrs=[("val", "dup", None)]))
        self.index(3, doc("c", attrs=[("val", "unique", None)]))
        body = {
            "aggs": {
                "attr_aggs": {
                    "nested": {"path": "attr"},
                    "aggs": {
                        "attr_name_aggs": {
                            "filter": {
                                "bool": {
                                    "must": [{"term": {"attr.name": "val"}}],
                                    "must_not": [{"term": {"attr.value.keyword": ""}}],
                                }
                            },
                            "aggs": {
                                "attr_value_aggs": {
                                    "terms": {
                                        "field": "attr.value.keyword",
                                        "min_doc_count": 2,
                                    }
                                }
                            },
                        }
                    },
                }
            }
        }
        buckets = self.es.search(body=body)["aggregations"]["attr_aggs"]["attr_name_aggs"][
            "attr_value_aggs"
        ]["buckets"]
        self.assertEqual(buckets, [{"key": "dup", "doc_count": 2}])

    def test_bucket_keys_are_strings_even_for_non_string_values(self):
        self.index(1, doc("a", attrs=[("val", 7, None)]))
        self.index(2, doc("b", attrs=[("val", 7, None)]))
        body = {
            "aggs": {
                "n": {
                    "nested": {"path": "attr"},
                    "aggs": {"t": {"terms": {"field": "attr.value.keyword", "min_doc_count": 2}}},
                }
            }
        }
        buckets = self.es.search(body=body)["aggregations"]["n"]["t"]["buckets"]
        self.assertEqual(buckets, [{"key": "7", "doc_count": 2}])


class PersistenceTest(SimpleTestCase):
    """The dev server keeps its index across restarts; tests must not."""

    def test_documents_survive_a_new_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = dict(NO_PERSIST, PERSIST_PATH=tmp)
            with override_settings(ES_CONFIG=config):
                STORE.reset()
                first = InMemoryElasticsearch(INDEX)
                first.indices.create(index=INDEX)
                first.index(id=1, body=doc("persisted"))

                # A fresh process starts with an empty STORE and loads the file.
                STORE.reset()
                second = InMemoryElasticsearch(INDEX)
                res = second.search(body={"query": {"match_all": {}}})
                self.assertEqual(res["hits"]["hits"][0]["_source"]["name"], "persisted")

    def test_nothing_is_written_when_persistence_is_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(ES_CONFIG=NO_PERSIST):
                STORE.reset()
                es = InMemoryElasticsearch(INDEX)
                es.indices.create(index=INDEX)
                es.index(id=1, body=doc("ephemeral"))
            self.assertEqual(os.listdir(tmp), [])
