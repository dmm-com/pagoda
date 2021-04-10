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

        self._entry = Entry.objects.create(name='test_entry',
                                           schema=self._entity,
                                           created_user=self._user)
        self._attr = Attribute.objects.create(name='test_attr',
                                              schema=self._entity_attr,
                                              created_user=self._user,
                                              parent_entry=self._entry)
        self._attr_value = AttributeValue.objects.create(value='test_attr_value',
                                                         created_user=self._user,
                                                         parent_attr=self._attr)
        self._attr.values.add(self._attr_value)
        self._attr.save()

    def test_get_regex_pattern(self):
        # without escape character
        p1 = elasticsearch._get_regex_pattern('keyword')
        self.assertEqual(p1, '.*[kK][eE][yY][wW][oO][rR][dD].*')

        # with escape character
        p2 = elasticsearch._get_regex_pattern('key@@@word')
        self.assertEqual(p2, '.*[kK][eE][yY]\\@\\@\\@[wW][oO][rR][dD].*')

        # with anchor operators
        p2 = elasticsearch._get_regex_pattern('^keyword$')
        self.assertEqual(p2, '.*^?[kK][eE][yY][wW][oO][rR][dD]$?.*')

    def test_make_key_for_each_block_of_keywords(self):
        key1 = elasticsearch._make_key_for_each_block_of_keywords(
            {'name': 'name'}, 'keyword', True)
        self.assertEqual(key1, 'keyword')

        key2 = elasticsearch._make_key_for_each_block_of_keywords(
            {'name': 'name'}, 'keyword', False)
        self.assertEqual(key2, 'keyword_name')

    def test_is_matched_keyword(self):
        # if it has the same value with a hint
        self.assertTrue(elasticsearch._is_matched_entry(
            attrs=[{'name': 'attr', 'value': 'keyword', 'type': AttrTypeStr.TYPE}],
            hint_attrs=[{'name': 'attr', 'keyword': 'keyword'}]
        ))

        # if a hint has ^ and/or $, it matches with the keyword as a regexp
        self.assertTrue(elasticsearch._is_matched_entry(
            attrs=[{'name': 'attr', 'value': 'keyword', 'type': AttrTypeStr.TYPE}],
            hint_attrs=[{'name': 'attr', 'keyword': '^keyword'}]
        ))
        self.assertFalse(elasticsearch._is_matched_entry(
            attrs=[{'name': 'attr', 'value': '111keyword', 'type': AttrTypeStr.TYPE}],
            hint_attrs=[{'name': 'attr', 'keyword': '^keyword'}]
        ))
        self.assertTrue(elasticsearch._is_matched_entry(
            attrs=[{'name': 'attr', 'value': 'keyword', 'type': AttrTypeStr.TYPE}],
            hint_attrs=[{'name': 'attr', 'keyword': 'keyword$'}]
        ))
        self.assertFalse(elasticsearch._is_matched_entry(
            attrs=[{'name': 'attr', 'value': 'keyword111', 'type': AttrTypeStr.TYPE}],
            hint_attrs=[{'name': 'attr', 'keyword': 'keyword$'}]
        ))

        # if a hint is blank
        self.assertTrue(elasticsearch._is_matched_entry(
            attrs=[{'name': 'attr', 'value': 'keyword', 'type': AttrTypeStr.TYPE}],
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
        res = {
            'hits': {
                'total': 1,
                'hits': [
                    {
                        '_type': 'entry',
                        '_id': self._entry.id,
                        '_source': {
                            'entity': {
                                'id': self._entry.id,
                                'name': self._entry.name
                            },
                            'name': self._entry.name,
                            'attr': [
                                {
                                    'name': self._attr.name,
                                    'type': self._attr.schema.type,
                                    'key': '',
                                    'value': self._attr_value.value,
                                    'referral_id': ''
                                }
                            ]
                        },
                        'sort': [self._entry.name]
                    }
                ]
            }
        }

        # Empty keyword should be handled as wildcard
        results_with_empty_keyword = elasticsearch.make_search_results(
            res, [{'name': self._attr.name, 'keyword': ''}], 100, False)
        self.assertEqual(results_with_empty_keyword['ret_count'], 1)
        self.assertEqual(results_with_empty_keyword['ret_values'], [
            {
                'entity': {
                    'id': self._entity.id,
                    'name': self._entity.name,
                },
                'entry': {
                    'id': self._entry.id,
                    'name': self._entry.name
                },
                'attrs': {
                    self._attr.name:
                        {
                            'type': self._attr.schema.type,
                            'value': self._attr_value.value,
                        }
                },
            }
        ])

        # With a matched keyword
        results_with_matched_keyword = elasticsearch.make_search_results(
            res, [{'name': self._attr.name, 'keyword': self._attr_value.value}], 100, False)
        self.assertEqual(results_with_matched_keyword['ret_count'], 1)
        self.assertEqual(results_with_matched_keyword['ret_values'], [
            {
                'entity': {
                    'id': self._entity.id,
                    'name': self._entity.name,
                },
                'entry': {
                    'id': self._entry.id,
                    'name': self._entry.name
                },
                'attrs': {
                    self._attr.name:
                        {
                            'type': self._attr.schema.type,
                            'value': self._attr_value.value,
                        }
                },
            }
        ])

        # With a mismatched keyword
        results_with_mismatched_keyword = elasticsearch.make_search_results(
            res, [{'name': self._attr.name, 'keyword': '^mismatched$'}], 100, False)
        self.assertEqual(results_with_mismatched_keyword['ret_count'], 0)
        self.assertEqual(results_with_mismatched_keyword['ret_values'], [])
