from django.test import TestCase

from airone.lib import elasticsearch
from airone.lib.types import AttrTypeStr
from entity.models import Entity, EntityAttr
from entry.models import Attribute, AttributeValue, Entry
from user.models import User


class ElasticSearchTest(TestCase):

    def setUp(self):
        self._user = User(username='test')
        self._user.save()

        self._entity = Entity(name='entity', created_user=self._user)
        self._entity.save()

        self._entity_attr = EntityAttr(name='test',
                                       type=AttrTypeStr,
                                       is_mandatory=True,
                                       created_user=self._user,
                                       parent_entity=self._entity)
        self._entity_attr.save()

    def test_get_regex_pattern(self):
        # without escape character
        p1 = elasticsearch._get_regex_pattern('keyword')
        self.assertEqual(p1, '.*[kK][eE][yY][wW][oO][rR][dD].*')

        # with escape character
        p2 = elasticsearch._get_regex_pattern('key@@@word')
        self.assertEqual(p2, '.*[kK][eE][yY]\\@\\@\\@[wW][oO][rR][dD].*')

        # with anchor operators
        p2 = elasticsearch._get_regex_pattern('^keyword$')
        self.assertEqual(p2, '[kK][eE][yY][wW][oO][rR][dD]')

    def test_make_query(self):
        query = elasticsearch.make_query(
            hint_entity=self._entity,
            hint_attrs=[{'name': 'a1', 'keyword': 'hoge|fu&ga'}, {'name': 'a2', 'keyword': ''}],
            entry_name='entry1',
        )

        self.assertEqual(query, {
            'query': {
                'bool': {
                    'filter': [
                        {
                            'nested': {
                                'path': 'entity',
                                'query': {
                                    'term': {'entity.id': self._entity.id}
                                }
                            }
                        },
                        {
                            'bool': {
                                'should': [
                                    {
                                        'bool': {
                                            'must': [
                                                {'regexp': {'name': '.*[eE][nN][tT][rR][yY]1.*'}}
                                            ]
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            'nested': {
                                'path': 'attr',
                                'query': {
                                    'bool': {
                                        'should': [
                                            {'term': {'attr.name': 'a1'}},
                                            {'term': {'attr.name': 'a2'}}
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            'bool': {'should': [{
                                'nested': {
                                    'path': 'attr',
                                    'query': {'bool': {'filter': [
                                        {'term': {'attr.name': 'a1'}},
                                        {'bool': {
                                            'should': [
                                                {'match': {'attr.value': 'hoge'}},
                                                {'regexp': {'attr.value': '.*[hH][oO][gG][eE].*'}}
                                            ]
                                        }}
                                    ]}}
                                }
                            }, {
                                'bool': {'filter': [{
                                    'nested': {
                                        'path': 'attr',
                                        'query': {'bool': {'filter': [
                                            {'term': {'attr.name': 'a1'}},
                                            {'bool': {
                                                'should': [
                                                    {'match': {'attr.value': 'fu'}},
                                                    {'regexp': {'attr.value': '.*[fF][uU].*'}}
                                                ]
                                            }}
                                        ]}}
                                    }
                                }, {
                                    'nested': {
                                        'path': 'attr',
                                        'query': {'bool': {'filter': [
                                            {'term': {'attr.name': 'a1'}},
                                            {'bool': {
                                                'should': [
                                                    {'match': {'attr.value': 'ga'}},
                                                    {'regexp': {'attr.value': '.*[gG][aA].*'}}
                                                ]
                                            }}
                                        ]}}
                                    }
                                }]}
                            }]}
                        }
                    ],
                    'should': []
                }
            }
        })

    def test_make_query_for_simple(self):
        query = elasticsearch.make_query_for_simple('hoge|fuga&1', None, 0)
        self.assertEqual(query, {
            'query': {
                'bool': {'must': [{
                    'bool': {'should': [{
                        'bool': {
                            'should': [{
                                'bool': {'must': [
                                    {'regexp': {'name': '.*[hH][oO][gG][eE].*'}}
                                ]}
                            }, {
                                'bool': {'must': [
                                    {'regexp': {'name': '.*[fF][uU][gG][aA].*'}},
                                    {'regexp': {'name': '.*1.*'}}
                                ]}
                            }]
                        }
                    }, {
                        'bool': {
                            'filter': {
                                'nested': {
                                    'path': 'attr',
                                    'query': {'bool': {'should': [{
                                        'bool': {'filter': [
                                            {'regexp': {'attr.value': '.*[hH][oO][gG][eE].*'}}
                                        ]}
                                    }, {
                                        'bool': {'filter': [
                                            {'regexp': {'attr.value': '.*[fF][uU][gG][aA].*'}},
                                            {'regexp': {'attr.value': '.*1.*'}}
                                        ]}
                                    }]}},
                                    'inner_hits': {
                                        '_source': [
                                            'attr.name'
                                        ]
                                    }
                                }
                            }
                        }
                    }]}
                }]}
            },
            '_source': [
                'name'
            ],
            'sort': [{
                '_score': {
                    'order': 'desc'
                },
                'name.keyword': {
                    'order': 'asc'
                }
            }],
            'from': 0,
        })

        # set hint_entity_name
        query = elasticsearch.make_query_for_simple('hoge', 'fuga', 0)
        self.assertEqual(query['query']['bool']['must'][1], {
            'nested': {
                'path': 'entity',
                'query': {
                    'term': {
                        'entity.name': 'fuga'
                    }
                }
            }
        })

        # set offset
        query = elasticsearch.make_query_for_simple('hoge', 'fuga', 100)
        self.assertEqual(query['from'], 100)

    def test_make_search_results(self):
        entry = Entry.objects.create(name='test_entry',
                                     schema=self._entity,
                                     created_user=self._user)
        attr = Attribute.objects.create(name='test_attr',
                                        schema=self._entity_attr,
                                        created_user=self._user,
                                        parent_entry=entry)
        attr_value = AttributeValue.objects.create(value='test_attr_value',
                                                   created_user=self._user,
                                                   parent_attr=attr)
        attr.values.add(attr_value)
        attr.save()

        res = {
            'hits': {
                'total': 1,
                'hits': [
                    {
                        '_type': 'entry',
                        '_id': entry.id,
                        '_source': {
                            'entity': {
                                'id': entry.id,
                                'name': entry.name
                            },
                            'name': entry.name,
                            'attr': [
                                {
                                    'name': attr.name,
                                    'type': attr.schema.type,
                                    'key': '',
                                    'value': attr_value.value,
                                    'referral_id': '',
                                    'is_readble': True
                                }
                            ],
                            'is_readble': True
                        },
                        'sort': [entry.name]
                    }
                ]
            }
        }

        hint_attrs = [{'name': 'test_attr', 'keyword': '', 'is_readble': True}]
        results = elasticsearch.make_search_results(self._user, res, hint_attrs, 100, False)

        self.assertEqual(results['ret_count'], 1)
        self.assertEqual(results['ret_values'], [
            {
                'entity': {
                    'id': self._entity.id,
                    'name': self._entity.name,
                },
                'entry': {
                    'id': entry.id,
                    'name': entry.name
                },
                'attrs': {
                    attr.name:
                        {
                            'type': attr.schema.type,
                            'value': attr_value.value,
                            'is_readble': True
                        }
                },
                'is_readble': True
            }
        ])

    def test_make_search_results_for_simple(self):
        entry = Entry.objects.create(name='test_entry',
                                     schema=self._entity,
                                     created_user=self._user)
        attr = Attribute.objects.create(name='test',
                                        schema=self._entity_attr,
                                        created_user=self._user,
                                        parent_entry=entry)
        attr_value = AttributeValue.objects.create(value='test_attr_value',
                                                   created_user=self._user,
                                                   parent_attr=attr)
        entry.attrs.add(attr)
        attr.values.add(attr_value)
        attr.save()

        res = {
            'hits': {
                'total': 1,
                'hits': [
                    {
                        '_type': 'entry',
                        '_id': entry.id,
                        '_source': {
                            'name': entry.name
                        },
                        'inner_hits': {
                            'attr': {
                                'hits': {
                                    'total': 1,
                                    'hits': [{
                                        '_type': 'entry',
                                        '_id': entry.id,
                                        '_source': {
                                            'name': attr.name
                                        },
                                    }]
                                }
                            }
                        }
                    }
                ]
            }
        }

        results = elasticsearch.make_search_results_for_simple(res)

        self.assertEqual(results['ret_count'], 1)
        self.assertEqual(results['ret_values'], [
            {
                'id': entry.id,
                'name': entry.name,
                'attr': attr.name,
            }
        ])
