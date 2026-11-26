import json

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from airone.lib.elasticsearch import make_search_results
from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from entity.models import Entity
from entry.models import Entry
from entry.settings import CONFIG
from group.models import Group
from role.models import Role
from user.models import User


class SearchReferralACLTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="reader")
        self.entity = Entity.objects.create(name="target model", created_user=self.user)
        self.target = Entry.objects.create(
            name="target", schema=self.entity, created_user=self.user
        )
        self.source_entity = Entity.objects.create(name="current model", created_user=self.user)
        self.source = Entry.objects.create(
            name="current source", schema=self.source_entity, created_user=self.user
        )

    def response(self, sources=None):
        return {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": self.target.id,
                        "_source": {
                            "is_readable": True,
                            "attr": [],
                            "referrals": [
                                {
                                    "id": source.id,
                                    "name": "stale secret",
                                    "schema": {"id": self.source_entity.id, "name": "stale model"},
                                }
                                for source in (sources if sources is not None else [self.source])
                            ],
                        },
                    }
                ],
            }
        }

    def referrals(self, response=None, user=True, hint=""):
        return (
            make_search_results(
                self.user if user else None, response or self.response(), [], hint, 10
            )
            .ret_values[0]
            .referrals
        )

    def test_entry_and_parent_acl_are_checked_from_database(self):
        expected = [
            {
                "id": self.source.id,
                "name": self.source.name,
                "schema": {"id": self.source_entity.id, "name": self.source_entity.name},
            }
        ]
        self.assertEqual(self.referrals(), expected)
        for obj in (self.source, self.source_entity):
            with self.subTest(object=type(obj).__name__):
                obj.is_public = False
                obj.save()
                self.assertEqual(self.referrals(), [])
                obj.is_public = True
                obj.save()

    def test_unreadable_hit_does_not_include_readable_referrals(self):
        self.target.is_public = False
        self.target.save(update_fields=["is_public"])

        self.assertEqual(self.referrals(), [])

    def test_group_role_grants_and_revocation_are_current(self):
        self.source.is_public = False
        self.source.save()
        self.source_entity.is_public = False
        self.source_entity.save()
        group = Group.objects.create(name="readers")
        self.user.groups.add(group)
        role = Role.objects.create(name="reader role")
        role.groups.add(group)
        role.permissions.add(self.source.readable, self.source_entity.readable)
        self.assertEqual(len(self.referrals()), 1)
        role.permissions.remove(self.source_entity.readable)
        self.assertEqual(self.referrals(), [])

    def test_direct_role_grants_both_entry_and_parent(self):
        self.source.is_public = False
        self.source.save()
        self.source_entity.is_public = False
        self.source_entity.save()
        role = Role.objects.create(name="direct reader")
        role.users.add(self.user)
        role.permissions.add(self.source.readable)
        self.assertEqual(self.referrals(), [])
        role.permissions.add(self.source_entity.readable)
        self.assertEqual(len(self.referrals()), 1)
        role.permissions.remove(self.source.readable)
        self.assertEqual(self.referrals(), [])

    def test_referral_order_and_hit_limit_are_preserved(self):
        second = Entry.objects.create(
            name="second", schema=self.source_entity, created_user=self.user
        )
        response = self.response([second, self.source])
        self.assertEqual(
            [value["id"] for value in self.referrals(response)], [second.id, self.source.id]
        )
        response["hits"]["hits"].append(response["hits"]["hits"][0])
        results = make_search_results(self.user, response, [], "", 1)
        self.assertEqual(len(results.ret_values), 1)
        self.assertEqual(results.ret_count, 1)

    def test_missing_deleted_and_inactive_parent_are_omitted(self):
        response = self.response()
        response["hits"]["hits"][0]["_source"]["referrals"].append(
            {"id": 999999, "name": "missing", "schema": {"id": 999998, "name": "missing"}}
        )
        self.source.is_active = False
        self.source.save()
        self.assertEqual(self.referrals(response), [])
        self.source.is_active = True
        self.source.save()
        self.source_entity.is_active = False
        self.source_entity.save()
        self.assertEqual(self.referrals(response), [])

    def test_trusted_and_absent_hint_contracts(self):
        self.assertEqual(
            self.referrals(user=False), self.response()["hits"]["hits"][0]["_source"]["referrals"]
        )
        self.assertIsNone(self.referrals(hint=None))
        self.assertEqual(self.referrals(self.response([])), [])

    def test_private_referral_queries_do_not_grow_with_unique_sources(self):
        self.source.is_public = False
        self.source.save()
        role = Role.objects.create(name="batch readers")
        role.users.add(self.user)
        role.permissions.add(self.source.readable)
        with CaptureQueriesContext(connection) as small:
            self.assertEqual(len(self.referrals()), 1)
        sources = [self.source] + [
            Entry.objects.create(
                name=f"private {i}",
                schema=self.source_entity,
                created_user=self.user,
                is_public=False,
            )
            for i in range(12)
        ]
        role.permissions.add(*(source.readable for source in sources[1:]))
        with CaptureQueriesContext(connection) as large:
            self.assertEqual(len(self.referrals(self.response(sources))), len(sources))
        self.assertLessEqual(len(large), len(small) + 1)


class SearchReferralAPIACLTest(AironeViewTest):
    def test_search_apis_filter_stale_referrals_using_current_acl(self):
        user = self.guest_login()
        target_entity = self.create_entity(user, "targets")
        target = self.add_entry(user, "target", target_entity)
        source_entity = self.create_entity(
            user, "sources", attrs=[{"name": "ref", "type": AttrType.OBJECT}]
        )
        source = self.add_entry(user, "source", source_entity, values={"ref": target.pk})
        target.register_es()
        expected = [
            {
                "id": source.pk,
                "name": source.name,
                "schema": {"id": source_entity.pk, "name": source_entity.name},
            }
        ]
        endpoints = (
            ("/entry/api/v2/advanced_search/", "referral_name"),
            ("/api/v1/entry/search", "referral"),
        )
        for endpoint, referral_key in endpoints:
            with self.subTest(endpoint=endpoint):
                params = {
                    "entities": [target_entity.pk],
                    "attrinfo": [],
                    "has_referral": True,
                    referral_key: CONFIG.EXSIT_CHARACTER,
                }

                def search_referrals():
                    response = self.client.post(endpoint, json.dumps(params), "application/json")
                    self.assertEqual(response.status_code, 200)
                    result = response.json()
                    if "result" in result:
                        result = result["result"]
                        self.assertEqual(result["ret_count"], 1)
                        return result["ret_values"][0]["referrals"]
                    self.assertEqual(result["count"], 1)
                    return result["values"][0]["referrals"]

                self.assertEqual(search_referrals(), expected)
                for obj in (source, source_entity):
                    obj.is_public = False
                    obj.save()
                    self.assertEqual(search_referrals(), [])
                    obj.is_public = True
                    obj.save()
