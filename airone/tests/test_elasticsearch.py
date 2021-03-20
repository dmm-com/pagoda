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

    def test_make_key_for_each_block_of_keywords(self):
        key1 = elasticsearch._make_key_for_each_block_of_keywords(
            {'name': 'name'}, 'keyword', True)
        self.assertEqual(key1, 'keyword')

        key2 = elasticsearch._make_key_for_each_block_of_keywords(
            {'name': 'name'}, 'keyword', False)
        self.assertEqual(key2, 'keyword_name')

    def test_is_matched_keyword(self):
        # if it has the same value with a hint
        self.assertTrue(elasticsearch._is_matched_keyword(
            attrname='attr',
            attrvalue='keyword',
            hint_attrs=[{'name': 'attr', 'keyword': 'keyword'}]
        ))

        # TODO if it matches with a regexp hint

        # if a hint is blank
        self.assertTrue(elasticsearch._is_matched_keyword(
            attrname='attr',
            attrvalue='keyword',
            hint_attrs=[{'name': 'attr', 'keyword': ''}]
        ))

    def test_make_query(self):
        query = elasticsearch.make_query(
            hint_entity_ids=['1'],
            hint_attrs=[{'name': 'a1', 'keyword': 'a'}, {'name': 'a2', 'keyword': ''}],
            entry_name='entry1',
            or_match=False,
        )

        self.assertEqual(query, {
            'query': {
                'bool': {
                    'filter': [
                        {
                            'nested': {
                                'path': 'entity',
                                'query': {
                                    'bool': {
                                        'should': [
                                            {'term': {'entity.id': 1}}
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            'bool': {
                                'should': [
                                    {
                                        'bool': {
                                            'filter': [
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
                            'nested': {
                                'path': 'attr',
                                'query': {
                                    'bool': {
                                        'filter': [
                                            {'term': {'attr.name': 'a1'}},
                                            {
                                                'bool': {
                                                    'should': [
                                                        {'match': {'attr.value': 'a'}},
                                                        {'regexp': {'attr.value': '.*[aA].*'}}
                                                    ]
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    ],
                    'should': []
                }
            }
        })

    def test_make_search_results(self):
        entry = Entry.objects.create(name='test_entry', schema=self._entity, created_user=self._user)
        attr = Attribute.objects.create(name='test_attr',
                                        schema=self._entity_attr,
                                        created_user=self._user,
                                        parent_entry=entry)
        attr_value = AttributeValue.objects.create(value='test_attr_value', created_user=self._user,
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
                                    'referral_id': ''
                                }
                            ]
                        },
                        'sort': [entry.name]
                    }
                ]
            }
        }

        results = elasticsearch.make_search_results(res, None, 100, False)

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
                        }
                },
            }
        ])
