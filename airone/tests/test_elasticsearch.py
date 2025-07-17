from django.test import TestCase

from airone.lib import elasticsearch
from airone.lib.elasticsearch import AdvancedSearchResultRecord, AttrHint
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.models import Attribute, AttributeValue, Entry
from user.models import User


class ElasticSearchTest(TestCase):
    def setUp(self):
        self._user = User(username="test")
        self._user.save()

        self._entity = Entity(name="entity", created_user=self._user)
        self._entity.save()

        self._entity_attr = EntityAttr(
            name="test",
            type=AttrType.STRING,
            is_mandatory=True,
            created_user=self._user,
            parent_entity=self._entity,
        )
        self._entity_attr.save()

    def test_get_regex_pattern(self):
        # without escape character
        p1 = elasticsearch._get_regex_pattern("keyword")
        self.assertEqual(p1, ".*[kK][eE][yY][wW][oO][rR][dD].*")

        # with escape character
        p2 = elasticsearch._get_regex_pattern("key@@@word")
        self.assertEqual(p2, ".*[kK][eE][yY]\\@\\@\\@[wW][oO][rR][dD].*")

        # with anchor operators
        p2 = elasticsearch._get_regex_pattern("^keyword$")
        self.assertEqual(p2, "[kK][eE][yY][wW][oO][rR][dD]")

        # with empty string
        p3 = elasticsearch._get_regex_pattern("")
        self.assertEqual(p3, ".*.*")

    def test_make_query(self):
        query = elasticsearch.make_query(
            hint_entity=self._entity,
            hint_attrs=[
                AttrHint(name="a1", keyword="hoge|fu&ga"),
                AttrHint(name="a2", keyword=""),
            ],
            entry_name="entry1",
        )

        self.assertEqual(
            query,
            {
                "query": {
                    "bool": {
                        "filter": [
                            {
                                "nested": {
                                    "path": "entity",
                                    "query": {"term": {"entity.id": self._entity.id}},
                                }
                            },
                            {
                                "bool": {
                                    "should": [
                                        {
                                            "bool": {
                                                "must": [
                                                    {
                                                        "regexp": {
                                                            "name": ".*[eE][nN][tT][rR][yY]1.*"
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    ]
                                }
                            },
                            {
                                "nested": {
                                    "path": "attr",
                                    "query": {
                                        "bool": {
                                            "should": [
                                                {"term": {"attr.name": "a1"}},
                                                {"term": {"attr.name": "a2"}},
                                            ]
                                        }
                                    },
                                }
                            },
                            {
                                "bool": {
                                    "should": [
                                        {
                                            "nested": {
                                                "path": "attr",
                                                "query": {
                                                    "bool": {
                                                        "filter": [
                                                            {"term": {"attr.name": "a1"}},
                                                            {
                                                                "bool": {
                                                                    "should": [
                                                                        {
                                                                            "match": {
                                                                                "attr.value": "hoge"
                                                                            }
                                                                        },
                                                                        {
                                                                            "regexp": {
                                                                                "attr.value": ".*[hH][oO][gG][eE].*"
                                                                            }
                                                                        },
                                                                    ]
                                                                }
                                                            },
                                                        ]
                                                    }
                                                },
                                            }
                                        },
                                        {
                                            "bool": {
                                                "filter": [
                                                    {
                                                        "nested": {
                                                            "path": "attr",
                                                            "query": {
                                                                "bool": {
                                                                    "filter": [
                                                                        {
                                                                            "term": {
                                                                                "attr.name": "a1"
                                                                            }
                                                                        },
                                                                        {
                                                                            "bool": {
                                                                                "should": [
                                                                                    {
                                                                                        "match": {
                                                                                            "attr.value": "fu"
                                                                                        }
                                                                                    },
                                                                                    {
                                                                                        "regexp": {
                                                                                            "attr.value": ".*[fF][uU].*"
                                                                                        }
                                                                                    },
                                                                                ]
                                                                            }
                                                                        },
                                                                    ]
                                                                }
                                                            },
                                                        }
                                                    },
                                                    {
                                                        "nested": {
                                                            "path": "attr",
                                                            "query": {
                                                                "bool": {
                                                                    "filter": [
                                                                        {
                                                                            "term": {
                                                                                "attr.name": "a1"
                                                                            }
                                                                        },
                                                                        {
                                                                            "bool": {
                                                                                "should": [
                                                                                    {
                                                                                        "match": {
                                                                                            "attr.value": "ga"
                                                                                        }
                                                                                    },
                                                                                    {
                                                                                        "regexp": {
                                                                                            "attr.value": ".*[gG][aA].*"
                                                                                        }
                                                                                    },
                                                                                ]
                                                                            }
                                                                        },
                                                                    ]
                                                                }
                                                            },
                                                        }
                                                    },
                                                ]
                                            }
                                        },
                                    ]
                                }
                            },
                        ],
                        "should": [],
                    }
                }
            },
        )

    def test_make_query_allow_missing_attributes(self):
        """Test make_query with allow_missing_attributes=True (APIv2 case)."""
        query = elasticsearch.make_query(
            hint_entity=self._entity,
            hint_attrs=[
                AttrHint(name="attr_with_keyword", keyword="has_keyword"),
                AttrHint(name="attr_without_keyword", keyword=""),
                AttrHint(name="another_attr_with_keyword", keyword="another_keyword"),
            ],
            entry_name="test_entry_apiv2",
            allow_missing_attributes=True,
        )

        expected_query = {
            "query": {
                "bool": {
                    "filter": [
                        {
                            "nested": {
                                "path": "entity",
                                "query": {"term": {"entity.id": self._entity.id}},
                            }
                        },
                        {
                            "bool": {
                                "should": [
                                    {
                                        "bool": {
                                            "must": [
                                                {
                                                    "regexp": {
                                                        "name": ".*[tT][eE][sS][tT]_[eE][nN][tT][rR][yY]_[aA][pP][iI][vV]2.*"
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            "nested": {
                                "path": "attr",
                                "query": {
                                    "bool": {
                                        "should": [
                                            {"term": {"attr.name": "attr_with_keyword"}},
                                            {"term": {"attr.name": "another_attr_with_keyword"}},
                                        ],
                                        "minimum_should_match": 1,
                                    }
                                },
                            }
                        },
                        {
                            "bool": {
                                "filter": [
                                    {
                                        "nested": {
                                            "path": "attr",
                                            "query": {
                                                "bool": {
                                                    "filter": [
                                                        {
                                                            "term": {
                                                                "attr.name": "attr_with_keyword"
                                                            }
                                                        },
                                                        {
                                                            "bool": {
                                                                "should": [
                                                                    {
                                                                        "match": {
                                                                            "attr.value": "has_keyword"
                                                                        }
                                                                    },
                                                                    {
                                                                        "regexp": {
                                                                            "attr.value": ".*[hH][aA][sS]_[kK][eE][yY][wW][oO][rR][dD].*"
                                                                        }
                                                                    },
                                                                ]
                                                            }
                                                        },
                                                    ]
                                                }
                                            },
                                        }
                                    },
                                    {
                                        "nested": {
                                            "path": "attr",
                                            "query": {
                                                "bool": {
                                                    "filter": [
                                                        {
                                                            "term": {
                                                                "attr.name": "another_attr_with_keyword"
                                                            }
                                                        },
                                                        {
                                                            "bool": {
                                                                "should": [
                                                                    {
                                                                        "match": {
                                                                            "attr.value": "another_keyword"
                                                                        }
                                                                    },
                                                                    {
                                                                        "regexp": {
                                                                            "attr.value": ".*[aA][nN][oO][tT][hH][eE][rR]_[kK][eE][yY][wW][oO][rR][dD].*"
                                                                        }
                                                                    },
                                                                ]
                                                            }
                                                        },
                                                    ]
                                                }
                                            },
                                        }
                                    },
                                ]
                            }
                        },
                    ],
                    "should": [],
                }
            }
        }
        self.assertEqual(query, expected_query)

    def test_make_query_for_simple(self):
        query = elasticsearch.make_query_for_simple("hoge|fuga&1", None, [], 0)
        self.assertEqual(
            query,
            {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "bool": {
                                    "should": [
                                        {"match": {"name": "hoge|fuga&1"}},
                                        {
                                            "bool": {
                                                "should": [
                                                    {
                                                        "bool": {
                                                            "must": [
                                                                {
                                                                    "regexp": {
                                                                        "name": ".*[hH][oO][gG][eE].*"
                                                                    }
                                                                }
                                                            ]
                                                        }
                                                    },
                                                    {
                                                        "bool": {
                                                            "must": [
                                                                {
                                                                    "regexp": {
                                                                        "name": ".*[fF][uU][gG][aA].*"
                                                                    }
                                                                },
                                                                {"regexp": {"name": ".*1.*"}},
                                                            ]
                                                        }
                                                    },
                                                ]
                                            }
                                        },
                                        {
                                            "bool": {
                                                "filter": {
                                                    "nested": {
                                                        "path": "attr",
                                                        "query": {
                                                            "bool": {
                                                                "should": [
                                                                    {
                                                                        "bool": {
                                                                            "filter": [
                                                                                {
                                                                                    "regexp": {
                                                                                        "attr.value": ".*[hH][oO][gG][eE].*"
                                                                                    }
                                                                                }
                                                                            ]
                                                                        }
                                                                    },
                                                                    {
                                                                        "bool": {
                                                                            "filter": [
                                                                                {
                                                                                    "regexp": {
                                                                                        "attr.value": ".*[fF][uU][gG][aA].*"
                                                                                    }
                                                                                },
                                                                                {
                                                                                    "regexp": {
                                                                                        "attr.value": ".*1.*"
                                                                                    }
                                                                                },
                                                                            ]
                                                                        }
                                                                    },
                                                                ]
                                                            }
                                                        },
                                                        "inner_hits": {"_source": ["attr.name"]},
                                                    }
                                                }
                                            }
                                        },
                                    ]
                                }
                            }
                        ]
                    }
                },
                "_source": ["name", "entity"],
                "sort": [{"_score": {"order": "desc"}, "name.keyword": {"order": "asc"}}],
                "from": 0,
            },
        )

        # set hint_entity_name
        query = elasticsearch.make_query_for_simple("hoge", "fuga", [], 0)
        self.assertEqual(
            query["query"]["bool"]["must"][1],
            {"nested": {"path": "entity", "query": {"term": {"entity.name": "fuga"}}}},
        )

        # set exclude_entity_names
        query = elasticsearch.make_query_for_simple("hoge", None, ["fuga"], 0)
        self.assertEqual(
            query["query"]["bool"]["must_not"][0],
            {"nested": {"path": "entity", "query": {"term": {"entity.name": "fuga"}}}},
        )

        # set offset
        query = elasticsearch.make_query_for_simple("hoge", "fuga", [], 100)
        self.assertEqual(query["from"], 100)

    def test_make_search_results(self):
        entry = Entry.objects.create(
            name="test_entry", schema=self._entity, created_user=self._user
        )
        attr = Attribute.objects.create(
            name="test_attr",
            schema=self._entity_attr,
            created_user=self._user,
            parent_entry=entry,
        )
        attr_value = AttributeValue.objects.create(
            value="test_attr_value", created_user=self._user, parent_attr=attr
        )
        attr.values.add(attr_value)
        attr.save()

        res = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_type": "entry",
                        "_id": entry.id,
                        "_source": {
                            "entity": {"id": entry.id, "name": entry.name},
                            "name": entry.name,
                            "attr": [
                                {
                                    "name": attr.name,
                                    "type": attr.schema.type,
                                    "key": "",
                                    "value": attr_value.value,
                                    "referral_id": "",
                                    "is_readable": True,
                                }
                            ],
                            "is_readable": True,
                        },
                        "sort": [entry.name],
                    }
                ],
            }
        }

        hint_attrs = [
            AttrHint(name="test_attr", keyword="", is_readable=True),
        ]
        hint_referral = ""
        results = elasticsearch.make_search_results(self._user, res, hint_attrs, hint_referral, 100)

        self.assertEqual(results.ret_count, 1)
        self.assertEqual(
            results.ret_values,
            [
                AdvancedSearchResultRecord(
                    entity={
                        "id": self._entity.id,
                        "name": self._entity.name,
                    },
                    entry={"id": entry.id, "name": entry.name},
                    attrs={
                        attr.name: {
                            "type": attr.schema.type,
                            "value": attr_value.value,
                            "is_readable": True,
                        }
                    },
                    is_readable=True,
                    referrals=[],
                )
            ],
        )

        hint_referral = None
        results = elasticsearch.make_search_results(self._user, res, hint_attrs, hint_referral, 100)
        self.assertFalse("referrals" in results.ret_values)

    def test_make_search_results_for_simple(self):
        entry = Entry.objects.create(
            name="test_entry", schema=self._entity, created_user=self._user
        )
        attr = Attribute.objects.create(
            name="test",
            schema=self._entity_attr,
            created_user=self._user,
            parent_entry=entry,
        )
        attr_value = AttributeValue.objects.create(
            value="test_attr_value", created_user=self._user, parent_attr=attr
        )
        attr.values.add(attr_value)
        attr.save()

        res = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_type": "entry",
                        "_id": entry.id,
                        "_source": {
                            "name": entry.name,
                            "entity": {
                                "id": entry.schema.id,
                                "name": entry.schema.name,
                            },
                        },
                        "inner_hits": {
                            "attr": {
                                "hits": {
                                    "total": 1,
                                    "hits": [
                                        {
                                            "_type": "entry",
                                            "_id": entry.id,
                                            "_source": {"name": attr.name},
                                        }
                                    ],
                                }
                            }
                        },
                    }
                ],
            }
        }

        results = elasticsearch.make_search_results_for_simple(res)

        self.assertEqual(results["ret_count"], 1)
        self.assertEqual(
            results["ret_values"],
            [
                {
                    "id": entry.id,
                    "name": entry.name,
                    "schema": {
                        "id": entry.schema.id,
                        "name": entry.schema.name,
                    },
                    "attr": attr.name,
                }
            ],
        )

    def test_make_search_results_with_limit(self):
        entries = [
            Entry.objects.create(name="entry-%d" % i, schema=self._entity, created_user=self._user)
            for i in range(1, 16)
        ]

        res = {
            "hits": {
                "total": {"value": len(entries)},
                "hits": [
                    {
                        "_type": "entry",
                        "_id": entry.id,
                        "_source": {
                            "entity": {"id": entry.id, "name": entry.name},
                            "name": entry.name,
                            "attr": [],
                            "is_readable": True,
                        },
                        "sort": [entry.name],
                    }
                    for entry in entries
                ],
            }
        }

        # 1 to 10
        results = elasticsearch.make_search_results(self._user, res, [], "", limit=10)
        self.assertEqual(results.ret_count, len(entries))
        self.assertEqual(
            sorted(results.ret_values, key=lambda x: x.entry["id"]),
            sorted(
                [
                    AdvancedSearchResultRecord(
                        entity={
                            "id": self._entity.id,
                            "name": self._entity.name,
                        },
                        entry={"id": entry.id, "name": entry.name},
                        attrs={},
                        is_readable=True,
                        referrals=[],
                    )
                    for entry in entries[0:10]
                ],
                key=lambda x: x.entry["id"],
            ),
        )

    def test_date_range_search(self):
        # Test for date range with tilde delimiter
        date_result = elasticsearch._is_date_check("2023-01-01~2023-12-31")
        self.assertEqual(date_result[0], "~")
        self.assertEqual(date_result[1][0].strftime("%Y-%m-%d"), "2023-01-01")
        self.assertEqual(date_result[1][1].strftime("%Y-%m-%d"), "2023-12-31")

        # Test for date range with slash delimiter
        date_result = elasticsearch._is_date_check("2023/01/01~2023/12/31")
        self.assertEqual(date_result[0], "~")
        self.assertEqual(date_result[1][0].strftime("%Y-%m-%d"), "2023-01-01")
        self.assertEqual(date_result[1][1].strftime("%Y-%m-%d"), "2023-12-31")

        # Test for date range containing whitespace
        date_result = elasticsearch._is_date_check("2023-01-01 ~ 2023-12-31")
        self.assertEqual(date_result[0], "~")
        self.assertEqual(date_result[1][0].strftime("%Y-%m-%d"), "2023-01-01")
        self.assertEqual(date_result[1][1].strftime("%Y-%m-%d"), "2023-12-31")

        # Test for invalid date range (end date before start date)
        date_result = elasticsearch._is_date_check("2023-12-31~2023-01-01")
        self.assertIsNone(date_result)

        # Test for invalid date range (different formats)
        date_result = elasticsearch._is_date_check("2023-01-01~2023/01/01")
        self.assertIsNone(date_result)

        # Test Elasticsearch query generation with date range in _make_an_attribute_filter
        hint = elasticsearch.AttrHint(name="test_date")
        filter_query = elasticsearch._make_an_attribute_filter(hint, "2023-01-01~2023-12-31")

        # Verify expected query structure
        self.assertEqual(filter_query["nested"]["path"], "attr")

        # Check range condition in should clause
        range_query = None
        for condition in filter_query["nested"]["query"]["bool"]["filter"][1]["bool"]["should"]:
            if "range" in condition:
                range_query = condition["range"]
                break

        self.assertIsNotNone(range_query)
        self.assertEqual(range_query["attr.date_value"]["format"], "yyyy-MM-dd")
        self.assertEqual(range_query["attr.date_value"]["gte"], "2023-01-01")
        self.assertEqual(range_query["attr.date_value"]["lte"], "2023-12-31")

    def test_is_date_check(self):
        """Test the _is_date_check function with legacy date formats and ISO8601 datetime formats"""
        from datetime import datetime, timezone

        from airone.lib.elasticsearch import _is_date_check

        # Valid single date (YYYY-MM-DD)
        result = _is_date_check("2023-01-01")
        self.assertEqual(result[0], "")
        self.assertEqual(result[1], datetime(2023, 1, 1))

        # Dates with comparison operators
        result = _is_date_check(">2023-12-31")
        self.assertEqual(result[0], ">")
        self.assertEqual(result[1], datetime(2023, 12, 31))

        result = _is_date_check("<2023-05-15")
        self.assertEqual(result[0], "<")
        self.assertEqual(result[1], datetime(2023, 5, 15))

        # Valid date range (YYYY-MM-DD~YYYY-MM-DD)
        result = _is_date_check("2023-01-01~2023-01-31")
        self.assertEqual(result[0], "~")
        self.assertEqual(result[1][0], datetime(2023, 1, 1))
        self.assertEqual(result[1][1], datetime(2023, 1, 31))

        # Different delimiters (YYYY/MM/DD)
        result = _is_date_check("2023/01/01")
        self.assertEqual(result[0], "")
        self.assertEqual(result[1], datetime(2023, 1, 1))

        result = _is_date_check("2023/12/31~2024/01/01")
        self.assertEqual(result[0], "~")
        self.assertEqual(result[1][0], datetime(2023, 12, 31))
        self.assertEqual(result[1][1], datetime(2024, 1, 1))

        # Invalid formats
        self.assertIsNone(_is_date_check("2023-13-01"))  # Invalid month
        self.assertIsNone(_is_date_check("2023/02/30"))  # Non-existent date
        self.assertIsNone(_is_date_check("2023-01"))  # Incomplete format
        self.assertIsNone(_is_date_check("text"))  # Not a date
        self.assertIsNone(_is_date_check("2023-01-01~"))  # Incomplete range

        # Date range order check
        self.assertIsNone(_is_date_check("2023-01-31~2023-01-01"))  # End date before start date

        # ISO8601 format tests
        # Valid single ISO8601 timestamp
        result = _is_date_check("2023-01-01T12:34:56")
        self.assertEqual(result[0], "")
        self.assertEqual(result[1], datetime(2023, 1, 1, 12, 34, 56))

        # ISO8601 with timezone
        result = _is_date_check("2023-01-01T12:34:56Z")
        self.assertEqual(result[0], "")
        self.assertEqual(result[1], datetime(2023, 1, 1, 12, 34, 56, tzinfo=timezone.utc))

        result = _is_date_check("2023-01-01T12:34:56+09:00")
        self.assertEqual(result[0], "")
        # Expect UTC normalized time (12:34:56+09:00 -> 03:34:56Z)
        self.assertEqual(result[1], datetime(2023, 1, 1, 3, 34, 56, tzinfo=timezone.utc))

        # ISO8601 with milliseconds
        result = _is_date_check("2023-01-01T12:34:56.789")
        self.assertEqual(result[0], "")
        self.assertEqual(result[1], datetime(2023, 1, 1, 12, 34, 56, 789000))

        # ISO8601 with comparison operators
        result = _is_date_check(">2023-01-01T00:00:00")
        self.assertEqual(result[0], ">")
        self.assertEqual(result[1], datetime(2023, 1, 1, 0, 0, 0))

        result = _is_date_check("<2023-12-31T23:59:59")
        self.assertEqual(result[0], "<")
        self.assertEqual(result[1], datetime(2023, 12, 31, 23, 59, 59))

        # ISO8601 timestamp range
        result = _is_date_check("2023-01-01T00:00:00~2023-01-01T23:59:59")
        self.assertEqual(result[0], "~")
        self.assertEqual(result[1][0], datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(result[1][1], datetime(2023, 1, 1, 23, 59, 59))

        # ISO8601 with 'T' delimiter
        result = _is_date_check("2023-01-01T12:34:56")
        self.assertEqual(result[0], "")
        self.assertEqual(result[1], datetime(2023, 1, 1, 12, 34, 56))

        # ISO8601 timestamp range with timezones
        result = _is_date_check("2023-01-01T00:00:00Z~2023-01-01T23:59:59+09:00")
        self.assertEqual(result[0], "~")
        self.assertEqual(result[1][0], datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(
            result[1][1], datetime(2023, 1, 1, 14, 59, 59, tzinfo=timezone.utc)
        )  # 23:59:59+09:00 -> 14:59:59Z

        # 秒なしの形式も有効とする
        self.assertEqual(
            _is_date_check("2023-01-01T12:34"), ("", datetime(2023, 1, 1, 12, 34))
        )  # Incomplete time format is valid
        self.assertIsNone(_is_date_check("2023-01-01T"))  # Missing time part

        # Invalid ISO8601 formats
        self.assertIsNone(_is_date_check("2023-01-01T25:00:00"))  # Invalid hour
        self.assertIsNone(_is_date_check("2023-01-01T12:61:00"))  # Invalid minute
        self.assertIsNone(_is_date_check("2023-01-01T12:00:61"))  # Invalid second
        self.assertIsNone(_is_date_check("2023-01-01T12:34:56~"))  # Incomplete range

        # Mixed date and datetime in range (now considered valid)
        self.assertEqual(
            _is_date_check("2023-01-01~2023-01-31T23:59:59"),
            ("~", (datetime(2023, 1, 1, 0, 0), datetime(2023, 1, 31, 23, 59, 59))),
        )  # Date ~ DateTime
        self.assertEqual(
            _is_date_check("2023-01-01T00:00:00~2023-01-31"),
            ("~", (datetime(2023, 1, 1, 0, 0, 0), datetime(2023, 1, 31, 0, 0))),
        )  # DateTime ~ Date
