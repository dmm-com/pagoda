import json
from unittest.mock import Mock, patch

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.urls import reverse

from airone.lib.acl import ACLType
from airone.lib.elasticsearch import AttrHint
from airone.lib.test import AironeViewTest, DisableStderr
from airone.lib.types import (
    AttrType,
)
from entity.models import Entity, EntityAttr, ItemNameType
from entry import tasks
from entry.models import Attribute, AttributeValue, Entry
from entry.services import AdvancedSearchService
from entry.settings import CONFIG as ENTRY_CONFIG
from group.models import Group
from job.models import Job, JobOperation, JobStatus, JobTarget
from role.models import Role
from trigger import tasks as trigger_tasks
from trigger.models import TriggerCondition
from user.models import User


class BaseViewTest(AironeViewTest):
    def setUp(self):
        super(BaseViewTest, self).setUp()

        # clear data which is used in individual tests
        self._test_data = {}

    # override 'admin_login' method to create initial Entity/EntityAttr objects
    def admin_login(self):
        user = super(BaseViewTest, self).admin_login()

        # create test entity which is a base of creating entry
        self._entity = Entity.objects.create(name="hoge", created_user=user)

        # set EntityAttr for the test Entity object
        self._entity_attr = EntityAttr(
            name="test",
            type=AttrType.STRING,
            is_mandatory=True,
            created_user=user,
            parent_entity=self._entity,
        )
        self._entity_attr.save()

        return user


class ViewTest(BaseViewTest):
    def test_get_index_without_login(self):
        resp = self.client.get(reverse("entry:index", args=[0]))
        self.assertEqual(resp.status_code, 303)

    def test_get_index_with_entries(self):
        user = self.admin_login()

        # create Entries (e1, e2 and e3) for using this test
        entries = [
            Entry.objects.create(name="e%d" % n, schema=self._entity, created_user=user)
            for n in range(1, 4)
        ]

        # create Entry e0 with a different time for checking sort-order
        Entry.objects.create(name="e0", schema=self._entity, created_user=user)

        # update Entry e1 after creating Entry e0
        resp = self.client.post(
            reverse("entry:do_edit", args=[entries[0].id]),
            json.dumps({"entry_name": "e1-changed", "attrs": []}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        TEST_PARAMS = [
            {
                "sort_order": ENTRY_CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["name"],
                "expected_order": ["e0", "e1-changed", "e2", "e3"],
            },
            {
                "sort_order": ENTRY_CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["name_reverse"],
                "expected_order": ["e3", "e2", "e1-changed", "e0"],
            },
            {
                "sort_order": ENTRY_CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["updated_time"],
                "expected_order": ["e2", "e3", "e0", "e1-changed"],
            },
            {
                "sort_order": ENTRY_CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["updated_time_reverse"],
                "expected_order": ["e1-changed", "e0", "e3", "e2"],
            },
            {
                "sort_order": ENTRY_CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["created_time"],
                "expected_order": ["e1-changed", "e2", "e3", "e0"],
            },
            {
                "sort_order": ENTRY_CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["created_time_reverse"],
                "expected_order": ["e0", "e3", "e2", "e1-changed"],
            },
        ]
        for param in TEST_PARAMS:
            resp = self.client.get(
                reverse("entry:index", args=[self._entity.id]), {"sort_order": param["sort_order"]}
            )
            self.assertEqual(resp.status_code, 200)

            # check listed Entries is sorted by created time order
            self.assertEqual(resp.context["sort_order"], param["sort_order"])
            self.assertEqual([x.name for x in resp.context["page_obj"]], param["expected_order"])

    def test_get_permitted_entries(self):
        self.guest_login()

        another_user = User.objects.create(username="hoge")
        entity = Entity(name="hoge", created_user=another_user, is_public=False)
        entity.save()

        resp = self.client.get(reverse("entry:index", args=[entity.id]))
        self.assertEqual(resp.status_code, 400)

    def test_get_self_created_entries(self):
        self.admin_login()

        self._entity.is_public = False

        resp = self.client.get(reverse("entry:index", args=[self._entity.id]))
        self.assertEqual(resp.status_code, 200)

        # check default sort_order value
        self.assertEqual(resp.context["sort_order"], ENTRY_CONFIG.DEFAULT_LIST_SORT_ORDER)

    def test_get_entries_with_user_permission(self):
        user = self.admin_login()

        entity = Entity.objects.create(
            name="hoge",
            is_public=False,
            created_user=User.objects.create(username="hoge"),
        )

        # set permission to the logged-in user
        user.permissions.add(entity.readable)

        resp = self.client.get(reverse("entry:index", args=[entity.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_entries_with_superior_user_permission(self):
        user = self.admin_login()

        entity = Entity.objects.create(
            name="hoge",
            is_public=False,
            created_user=User.objects.create(username="hoge"),
        )

        # set superior permission to the logged-in user
        user.permissions.add(entity.writable)

        resp = self.client.get(reverse("entry:index", args=[entity.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_index_with_page(self):
        self.admin_login()

        resp = self.client.get(reverse("entry:index", args=[self._entity.id]), {"page": 1})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse("entry:index", args=[self._entity.id]), {"page": 100})
        self.assertEqual(resp.status_code, 400)
        resp = self.client.get(reverse("entry:index", args=[self._entity.id]), {"page": "invalid"})
        self.assertEqual(resp.status_code, 400)

    def test_get_index_with_keyword(self):
        self.admin_login()

        resp = self.client.get(reverse("entry:index", args=[self._entity.id]), {"keyword": "test"})
        self.assertEqual(resp.status_code, 200)

    def test_get_with_inferior_user_permission(self):
        user = self.guest_login()

        entity = Entity.objects.create(
            name="hoge",
            is_public=False,
            created_user=User.objects.create(username="hoge"),
        )

        # set superior permission to the logged-in user
        user.permissions.add(entity.readable)

        resp = self.client.get(reverse("entry:create", args=[entity.id]))
        self.assertEqual(resp.status_code, 400)

    def test_get_entries_with_group_permission(self):
        user = self.admin_login()

        entity = Entity.objects.create(
            name="hoge",
            is_public=False,
            created_user=User.objects.create(username="hoge"),
        )

        # create test group
        group = Group.objects.create(name="test-group")
        user.groups.add(group)

        # set permission to the group which logged-in user belonged to
        group.permissions.add(entity.readable)

        resp = self.client.get(reverse("entry:index", args=[entity.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_entries_with_superior_group_permission(self):
        user = self.admin_login()

        entity = Entity.objects.create(
            name="hoge",
            is_public=False,
            created_user=User.objects.create(username="hoge"),
        )

        # create test group
        group = Group.objects.create(name="test-group")
        user.groups.add(group)

        # set superior permission to the group which logged-in user belonged to
        group.permissions.add(entity.full)

        resp = self.client.get(reverse("entry:index", args=[entity.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_create_page_without_login(self):
        resp = self.client.get(reverse("entry:create", args=[0]))
        self.assertEqual(resp.status_code, 303)

    def test_get_create_page_with_login(self):
        self.admin_login()

        resp = self.client.get(reverse("entry:create", args=[self._entity.id]))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["entity"], self._entity)

    def test_post_without_login(self):
        params = {
            "entry_name": "hoge",
            "attrs": [
                {
                    "id": "0",
                    "value": [{"data": "fuga", "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[0]), json.dumps(params), "application/json"
        )

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Attribute.objects.count(), 0)
        self.assertEqual(AttributeValue.objects.count(), 0)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    @patch(
        "entry.tasks.notify_create_entry.delay",
        Mock(side_effect=tasks.notify_create_entry),
    )
    @patch("entry.tasks.notify_entry_create", Mock(return_value=Mock()))
    def test_post_create_entry(self):
        user = self.admin_login()

        params = {
            "entry_name": "hoge",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "type": str(AttrType.ARRAY_STRING),
                    "value": [{"data": "hoge", "index": "0"}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(Attribute.objects.count(), 1)
        self.assertEqual(AttributeValue.objects.count(), 1)

        entry = Entry.objects.last()
        self.assertEqual(entry.attrs.count(), 1)
        self.assertEqual(entry.attrs.last(), Attribute.objects.last())
        self.assertEqual(entry.attrs.last().values.count(), 1)
        self.assertIsNotNone(entry.created_time)

        # tests for historical-record
        self.assertEqual(entry.history.count(), 1)

        attrvalue = AttributeValue.objects.last()
        self.assertEqual(entry.attrs.last().values.last(), attrvalue)
        self.assertTrue(attrvalue.is_latest)

        # checks that created entry is also registered in the Elasticsearch
        res = self._es.get(index=settings.ES_CONFIG["INDEX_NAME"], id=entry.id)
        self.assertTrue(res["found"])
        self.assertEqual(res["_source"]["entity"]["id"], self._entity.id)
        self.assertEqual(res["_source"]["name"], entry.name)
        self.assertEqual(len(res["_source"]["attr"]), entry.attrs.count())
        for attrinfo in res["_source"]["attr"]:
            attrv = AttributeValue.objects.get(parent_attr__name=attrinfo["name"], is_latest=True)
            self.assertEqual(attrinfo["value"], attrv.value)

        # checks created jobs and its params are as expected
        jobs = Job.objects.filter(user=user, target=entry)
        job_expectations = [
            {
                "operation": JobOperation.CREATE_ENTRY,
                "status": JobStatus.DONE,
                "dependent_job": None,
            },
            {
                "operation": JobOperation.NOTIFY_CREATE_ENTRY,
                "status": JobStatus.DONE,
                "dependent_job": None,
            },
            {
                "operation": JobOperation.MAY_INVOKE_TRIGGER,
                "status": JobStatus.PREPARING,
                "dependent_job": jobs.get(operation=JobOperation.CREATE_ENTRY),
            },
        ]
        self.assertEqual(jobs.count(), len(job_expectations))
        for expectation in job_expectations:
            obj = jobs.get(operation=expectation["operation"].value)
            self.assertEqual(obj.target.id, entry.id)
            self.assertEqual(obj.target_type, JobTarget.ENTRY)
            self.assertEqual(obj.status, expectation["status"])
            self.assertEqual(obj.dependent_job, expectation["dependent_job"])

        # checks specify part of attribute parameter then set AttributeValue
        # which is only specified one
        new_attr = EntityAttr.objects.create(
            name="new_attr",
            created_user=user,
            type=AttrType.STRING,
            parent_entity=self._entity,
            is_mandatory=False,
        )
        params["entry_name"] = "new_entry"
        params["attrs"] = [{"id": str(new_attr.id), "value": [{"data": "foo", "index": "0"}]}]

        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        entry = Entry.objects.last()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(entry.name, params["entry_name"])
        self.assertEqual(entry.attrs.count(), 2)

        attr_info = entry.get_available_attrs(user)
        self.assertEqual(len(attr_info), 2)
        self.assertEqual(
            sorted([x["name"] for x in attr_info]),
            sorted([x.schema.name for x in entry.attrs.all()]),
        )

        self.assertEqual([x["last_value"] for x in attr_info if x["name"] == "test"], [""])
        self.assertEqual([x["last_value"] for x in attr_info if x["name"] == "new_attr"], ["foo"])

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_post_create_entry_without_permission(self):
        self.guest_login()

        another_user = User.objects.create(username="hoge")
        entity = Entity.objects.create(name="hoge", is_public=False, created_user=another_user)
        attr_base = EntityAttr.objects.create(
            name="test",
            type=AttrType.STRING,
            is_mandatory=True,
            parent_entity=entity,
            created_user=another_user,
        )

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(attr_base.id),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Attribute.objects.count(), 0)
        self.assertEqual(AttributeValue.objects.count(), 0)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_post_with_optional_parameter(self):
        user = self.admin_login()

        # add an optional EntityAttr to the test Entity object
        self._entity_attr_optional = EntityAttr(
            name="test-optional",
            type=AttrType.STRING,
            is_mandatory=False,
            created_user=user,
            parent_entity=self._entity,
        )
        self._entity_attr_optional.save()

        params = {
            "entry_name": "hoge",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "type": str(AttrType.STRING),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
                {
                    "id": str(self._entity_attr_optional.id),
                    "type": str(AttrType.STRING),
                    "value": [],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(Attribute.objects.count(), 2)

        # Even if an empty value is specified, an AttributeValue will be create for creating.
        self.assertEqual(AttributeValue.objects.count(), 2)

        entry = Entry.objects.last()
        self.assertEqual(entry.attrs.count(), 2)
        self.assertEqual(entry.attrs.get(name="test").values.count(), 1)
        self.assertEqual(entry.attrs.get(name="test-optional").values.count(), 1)
        self.assertEqual(entry.attrs.get(name="test").values.last().value, "hoge")

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_post_with_lack_of_params(self):
        self.admin_login()

        params = {
            "entry_name": "",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Attribute.objects.count(), 0)
        self.assertEqual(AttributeValue.objects.count(), 0)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_post_create_with_referral(self):
        user = self.admin_login()

        attr_base = EntityAttr.objects.create(
            name="attr_with_referral",
            created_user=user,
            type=AttrType.OBJECT,
            parent_entity=self._entity,
            is_mandatory=False,
        )
        attr_base.referral.add(self._entity)

        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=user)

        params = {
            "entry_name": "new_entry",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "type": str(AttrType.OBJECT),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
                {
                    "id": str(attr_base.id),
                    "type": str(AttrType.OBJECT),
                    "value": [{"data": str(entry.id), "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), 2)
        self.assertEqual(Entry.objects.last().name, "new_entry")
        self.assertEqual(Entry.objects.last().attrs.last().schema.type, AttrType.OBJECT)
        self.assertEqual(Entry.objects.last().attrs.last().values.count(), 1)
        self.assertEqual(Entry.objects.last().attrs.last().values.last().value, "")
        self.assertEqual(Entry.objects.last().attrs.last().values.last().referral.id, entry.id)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_post_with_invalid_param(self):
        self.admin_login()

        params = {
            "entry_name": "hoge",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
                {"id": "9999", "value": ["invalid value"], "referral_key": []},
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Attribute.objects.count(), 0)
        self.assertEqual(AttributeValue.objects.count(), 0)

        params = {
            "entry_name": "hoge\thoge",
            "attrs": [],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_post_without_entry(self):
        user = self.admin_login()

        attr_base = EntityAttr.objects.create(
            name="ref_attr",
            created_user=user,
            type=AttrType.OBJECT,
            parent_entity=self._entity,
            is_mandatory=False,
        )
        attr_base.referral.add(self._entity)

        params = {
            "entry_name": "new_entry",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "type": str(AttrType.OBJECT),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
                {
                    "id": str(attr_base.id),
                    "type": str(AttrType.OBJECT),
                    "value": [{"data": "0", "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)

        new_entry = Entry.objects.get(name="new_entry")
        self.assertEqual(new_entry.attrs.get(schema=self._entity_attr).values.count(), 1)
        self.assertEqual(new_entry.attrs.get(schema=self._entity_attr).values.last().value, "hoge")
        # Even if an empty value is specified, an AttributeValue will be create for creating.
        self.assertEqual(new_entry.attrs.get(schema=attr_base).values.count(), 1)

    def test_get_detail_with_invalid_param(self):
        self.admin_login()

        resp = self.client.get(reverse("entry:show", args=[0]))
        self.assertEqual(resp.status_code, 400)

    def test_get_detail_with_valid_param(self):
        user = self.admin_login()

        # making test Entry set
        entry = Entry(name="fuga", schema=self._entity, created_user=user)
        entry.save()

        for attr_name in ["foo", "bar"]:
            attr = self.make_attr(name=attr_name, user=user, entry=entry)

            for value in ["hoge", "fuga"]:
                attr_value = AttributeValue(value=value, created_user=user, parent_attr=attr)
                attr_value.save()

                attr.values.add(attr_value)

        resp = self.client.get(reverse("entry:show", args=[entry.id]))
        self.assertEqual(resp.status_code, 200)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_post_create_array_string_attribute(self):
        user = self.admin_login()

        # create a test data set
        entity = Entity.objects.create(name="entity-test", created_user=user)

        attr_base = EntityAttr.objects.create(
            name="attr-test",
            type=AttrType.ARRAY_STRING,
            is_mandatory=False,
            created_user=user,
            parent_entity=entity,
        )

        params = {
            "entry_name": "entry-test",
            "attrs": [
                {
                    "id": str(attr_base.id),
                    "type": str(AttrType.ARRAY_STRING),
                    "value": [
                        {"data": "hoge", "index": 0},
                        {"data": "fuga", "index": 1},
                        {"data": "puyo", "index": 2},
                    ],
                    "referral_key": [],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(AttributeValue.objects.count(), 4)

        entry = Entry.objects.last()
        self.assertEqual(entry.name, "entry-test")
        self.assertEqual(entry.attrs.count(), 1)

        attr = entry.attrs.last()
        self.assertEqual(attr.name, "attr-test")
        self.assertEqual(attr.values.count(), 1)

        attr_value = attr.values.last()
        self.assertTrue(attr_value.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT))
        self.assertEqual(attr_value.value, "")
        self.assertIsNone(attr_value.referral)
        self.assertEqual(attr_value.data_array.count(), 3)
        self.assertTrue(
            [
                x.value == "hoge" or x.value == "fuga" or x.value == "puyo"
                for x in attr_value.data_array.all()
            ]
        )

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_post_create_array_object_attribute(self):
        user = self.admin_login()

        # create a test data set
        entity = Entity.objects.create(name="entity-test", created_user=user)

        attr_base = EntityAttr.objects.create(
            name="attr-ref-test",
            created_user=user,
            type=AttrType.ARRAY_OBJECT,
            parent_entity=entity,
            is_mandatory=False,
        )
        attr_base.referral.add(self._entity)

        referral = Entry.objects.create(name="entry0", schema=self._entity, created_user=user)

        params = {
            "entry_name": "entry-test",
            "attrs": [
                {
                    "id": str(attr_base.id),
                    "type": str(AttrType.ARRAY_OBJECT),
                    "value": [
                        {"data": str(referral.id), "index": 0},
                        {"data": str(referral.id), "index": 1},
                    ],
                    "referral_key": [],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(AttributeValue.objects.count(), 3)

        entry = Entry.objects.last()
        self.assertEqual(entry.name, "entry-test")
        self.assertEqual(entry.attrs.count(), 1)

        attr = entry.attrs.last()
        self.assertEqual(attr.name, "attr-ref-test")
        self.assertEqual(attr.values.count(), 1)

        attr_value = attr.values.last()
        self.assertTrue(attr_value.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT))
        self.assertEqual(attr_value.value, "")
        self.assertIsNone(attr_value.referral)
        self.assertEqual(attr_value.data_array.count(), 2)
        self.assertTrue(all([x.referral.id == referral.id for x in attr_value.data_array.all()]))

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_post_text_area_value(self):
        user = self.admin_login()

        textattr = EntityAttr.objects.create(
            name="attr-text",
            type=AttrType.TEXT,
            created_user=user,
            parent_entity=self._entity,
        )

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "type": str(AttrType.TEXT),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
                {
                    "id": str(textattr.id),
                    "type": str(AttrType.TEXT),
                    "value": [{"data": "fuga", "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(Attribute.objects.count(), 2)
        self.assertEqual(AttributeValue.objects.count(), 2)

        entry = Entry.objects.last()
        self.assertEqual(entry.attrs.count(), 2)
        self.assertTrue(
            any(
                [
                    (x.values.last().value == "hoge" or x.values.last().value == "fuga")
                    for x in entry.attrs.all()
                ]
            )
        )

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_create_entry_with_role_attributes(self):
        user = self.guest_login()
        role = Role.objects.create(name="TestRole")

        # initialize Entity which has Role related Attributes
        entity = self.create_entity(
            user,
            "Entity",
            attrs=[
                {"name": "Role", "type": AttrType.ROLE},
                {"name": "RoleArray", "type": AttrType.ARRAY_ROLE},
            ],
        )

        # initialize parameters that will be sent to AirOne to create Entry
        sending_params = {"entry_name": "entry", "attrs": []}
        for attrname, value in [
            ("Role", [{"data": str(role.id), "index": 0}]),
            ("RoleArray", [{"data": str(role.id), "index": 0}]),
        ]:
            attr = entity.attrs.get(name=attrname, is_active=True)
            sending_params["attrs"].append(
                {
                    "id": str(attr.id),
                    "type": str(attr.type),
                    "value": value,
                    "referral_key": [],
                }
            )

        # create Entry with valid role attributes and confirm that
        # created Entry has specified Attribute values.
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(sending_params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(id=resp.json().get("entry_id"))
        self.assertFalse(entry.attrs.get(schema__name="Role").is_updated(role))
        self.assertFalse(entry.attrs.get(schema__name="RoleArray").is_updated([role]))

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    @patch(
        "trigger.tasks.may_invoke_trigger.delay",
        Mock(side_effect=trigger_tasks.may_invoke_trigger),
    )
    def test_create_entry_with_trigger_configuration(self):
        user = self.guest_login()

        # initialize Entity which has Role related Attributes
        entity_pref = self.create_entity(user, "Prefecture")
        self.add_entry(user, "Tokyo", entity_pref)
        pref_info = {"tokyo": self.add_entry(user, "Tokyo", entity_pref)}

        entity = self.create_entity(
            user,
            "Personal Information",
            attrs=[
                {"name": "address", "type": AttrType.NAMED_OBJECT, "ref": entity_pref},
                {"name": "age", "type": AttrType.STRING},
            ],
        )

        # register TriggerAction configuration before creating an Entry
        TriggerCondition.register(
            entity,
            [
                {
                    "attr_id": entity.attrs.get(name="address").id,
                    "hint": "json",
                    "cond": json.dumps(
                        {
                            "name": "unknown",
                            "id": None,
                        }
                    ),
                }
            ],
            [
                {"attr_id": entity.attrs.get(name="age").id, "value": "0"},
                {
                    "attr_id": entity.attrs.get(name="address").id,
                    "value": {
                        "name": "Chiyoda ward",
                        "id": pref_info["tokyo"],
                    },
                },
            ],
        )

        # create an Entry to invoke TriggerAction
        params = {
            "entry_name": "Jhon Doe",
            "attrs": [
                {
                    "entity_attr_id": str(entity.attrs.get(name="address").id),
                    "id": str(entity.attrs.get(name="address").id),
                    "type": str(AttrType.STRING),
                    "value": [{"data": "", "index": 0}],
                    "referral_key": [{"data": "unknown", "index": 0}],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        # check trigger action was worked properly
        job_query = Job.objects.filter(operation=JobOperation.MAY_INVOKE_TRIGGER)
        self.assertEqual(job_query.count(), 1)
        self.assertEqual(job_query.first().status, JobStatus.DONE.value)

        # check created Entry's attributes are set properly by TriggerAction
        entry = Entry.objects.get(id=resp.json().get("entry_id"))
        self.assertEqual(entry.get_attrv("age").value, "0")
        self.assertEqual(entry.get_attrv("address").value, "Chiyoda ward")
        self.assertEqual(entry.get_attrv("address").referral.id, pref_info["tokyo"].id)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_create_entry_with_group_attr(self):
        admin = self.admin_login()

        group = Group.objects.create(name="group")
        admin.groups.add(group)

        entity = Entity.objects.create(name="entity", created_user=admin)
        EntityAttr.objects.create(
            **{
                "name": "attr_group",
                "type": AttrType.GROUP,
                "created_user": admin,
                "parent_entity": entity,
            }
        )

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(entity.attrs.first().id),
                    "type": str(AttrType.GROUP),
                    "value": [{"index": 0, "data": str(group.id)}],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(name="entry", schema=entity)
        self.assertEqual(entry.attrs.count(), 1)

        attrv = entry.attrs.first().get_latest_value()
        self.assertIsNotNone(attrv)
        self.assertEqual(attrv.group, group)
        self.assertEqual(attrv.data_type, AttrType.GROUP)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_post_create_just_limit_of_value(self):
        self.admin_login()

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "type": str(AttrType.STRING),
                    "value": [{"data": "A" * AttributeValue.MAXIMUM_VALUE_SIZE, "index": 0}],
                    "referral_key": [],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), 1)

        entry = Entry.objects.last()
        self.assertEqual(entry.attrs.count(), 1)
        self.assertEqual(entry.attrs.last().values.count(), 1)
        self.assertEqual(
            len(entry.attrs.last().values.last().value),
            AttributeValue.MAXIMUM_VALUE_SIZE,
        )

    def test_create_when_another_same_named_alias_exists(self):
        user = self.guest_login()

        # create Model, Item and Alias that is same name with creating Item in this test
        model = self.create_entity(user, "Mountain")
        item = self.add_entry(user, "Everest", model)
        item.add_alias("Chomolungma")

        resp = self.client.post(
            reverse("entry:do_create", args=[model.id]),
            json.dumps(
                {
                    "entry_name": "Chomolungma",
                    "attrs": [],
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode("utf-8"), "Duplicate named Alias is existed")

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_post_create_exceeding_limit_of_value(self):
        self.admin_login()

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "type": str(AttrType.STRING),
                    "value": {
                        "data": ["A" * AttributeValue.MAXIMUM_VALUE_SIZE + "A"],
                        "index": 0,
                    },
                    "referral_key": [],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.count(), 0)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_try_to_create_duplicate_name_of_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name="entry", created_user=user, schema=self._entity)
        entry.add_attribute_from_base(self._entity_attr, user)

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "type": str(AttrType.STRING),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_make_entry_with_unpermitted_params(self):
        user = self.admin_login()

        # update ACL of EntityAttr
        attr = EntityAttr.objects.create(
            name="newattr",
            type=AttrType.STRING,
            created_user=user,
            parent_entity=self._entity,
        )

        self._entity_attr.is_mandatory = False
        self._entity_attr.is_public = False
        self._entity_attr.default_permission = ACLType.Nothing.id
        self._entity_attr.save()

        self.guest_login()

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "type": str(AttrType.STRING),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
                {
                    "id": str(attr.id),
                    "type": str(AttrType.STRING),
                    "value": [{"data": "fuga", "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)

        # checks that Entry object is created with only permitted Attributes
        entry = Entry.objects.last()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.name, "entry")
        self.assertEqual(
            [attr.get_latest_value().get_value() for attr in entry.attrs.all()],
            ["", "fuga"],
        )

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_get_available_attrs(self):
        admin = self.admin_login()

        entity = Entity.objects.create(name="entity", created_user=admin)

        attrs = []
        for index, permission in enumerate([ACLType.Readable, ACLType.Writable]):
            attr = EntityAttr.objects.create(
                name="attr%d" % index,
                type=AttrType.STRING,
                created_user=admin,
                parent_entity=entity,
                is_public=False,
                index=index,
                default_permission=permission.id,
            )
            attrs.append(attr)

        params = {
            "entry_name": "entry1",
            "attrs": [
                {
                    "id": str(attrs[0].id),
                    "type": str(AttrType.STRING),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
                {
                    "id": str(attrs[1].id),
                    "type": str(AttrType.STRING),
                    "value": [{"data": "fuga", "index": 1}],
                    "referral_key": [],
                },
            ],
        }

        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)

        # switch to guest user
        user = self.guest_login()

        entry = Entry.objects.get(name="entry1")
        test_params = [
            {
                "user": admin,
                "is_readable": ACLType.Writable,
                "attrs": [
                    {"name": "attr0", "is_readable": True, "last_value": "hoge"},
                    {"name": "attr1", "is_readable": True, "last_value": "fuga"},
                ],
            },
            {
                "user": user,
                "is_readable": ACLType.Readable,
                "attrs": [
                    {"name": "attr0", "is_readable": True, "last_value": "hoge"},
                    {"name": "attr1", "is_readable": True, "last_value": "fuga"},
                ],
            },
            {
                "user": user,
                "is_readable": ACLType.Writable,
                "attrs": [
                    {"name": "attr0", "is_readable": False, "last_value": ""},
                    {"name": "attr1", "is_readable": True, "last_value": "fuga"},
                ],
            },
        ]
        for test_param in test_params:
            context = entry.get_available_attrs(test_param["user"], test_param["is_readable"])
            for index, test_param_attr in enumerate(test_param["attrs"]):
                self.assertEqual(context[index]["name"], test_param_attr["name"])
                self.assertEqual(context[index]["is_readable"], test_param_attr["is_readable"])
                self.assertEqual(context[index]["last_value"], test_param_attr["last_value"])

    def test_post_create_entry_without_mandatory_param(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="Entity", is_public=False, created_user=user)
        attr_base = EntityAttr.objects.create(
            name="attr",
            type=AttrType.STRING,
            is_mandatory=True,
            parent_entity=entity,
            created_user=user,
        )

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(attr_base.id),
                    "type": str(AttrType.STRING),
                    "value": [],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Attribute.objects.count(), 0)
        self.assertEqual(AttributeValue.objects.count(), 0)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    @patch("entry.tasks.delete_entry.delay", Mock(side_effect=tasks.delete_entry))
    @patch(
        "entry.tasks.notify_delete_entry.delay",
        Mock(side_effect=tasks.notify_delete_entry),
    )
    def test_referred_entry_cache(self):
        user = self.admin_login()

        ref_entity = Entity.objects.create(name="referred_entity", created_user=user)

        ref_entry1 = Entry.objects.create(name="referred1", schema=ref_entity, created_user=user)
        ref_entry2 = Entry.objects.create(name="referred2", schema=ref_entity, created_user=user)
        ref_entry3 = Entry.objects.create(name="referred3", schema=ref_entity, created_user=user)

        entity = Entity.objects.create(name="entity", created_user=user)
        entity_attr_ref = EntityAttr.objects.create(
            name="ref",
            type=AttrType.OBJECT,
            parent_entity=entity,
            created_user=user,
        )
        entity_attr_arr_ref = EntityAttr.objects.create(
            name="arr_ref",
            type=AttrType.ARRAY_OBJECT,
            parent_entity=entity,
            created_user=user,
        )

        # set entity that target each attributes refer to
        [x.referral.add(ref_entity) for x in entity.attrs.all()]

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(entity_attr_ref.id),
                    "type": str(AttrType.OBJECT),
                    "value": [
                        {"data": str(ref_entry1.id), "index": 0},
                    ],
                    "referral_key": [],
                },
                {
                    "id": str(entity_attr_arr_ref.id),
                    "type": str(AttrType.ARRAY_OBJECT),
                    "value": [
                        {"data": str(ref_entry1.id), "index": 0},
                        {"data": str(ref_entry2.id), "index": 1},
                    ],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)

        # checks referred_object cache is set
        entry = Entry.objects.get(name="entry")

        self.assertEqual(list(ref_entry1.get_referred_objects()), [entry])
        self.assertEqual(list(ref_entry2.get_referred_objects()), [entry])
        self.assertEqual(list(ref_entry3.get_referred_objects()), [])
        self.assertEqual(ref_entry1.get_referred_objects().count(), 1)
        self.assertEqual(ref_entry2.get_referred_objects().count(), 1)

        # checks referred_object cache will be updated by unrefering
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(name="ref").id),
                    "type": str(AttrType.OBJECT),
                    "value": [],
                    "referral_key": [],
                },
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(name="arr_ref").id),
                    "type": str(AttrType.ARRAY_OBJECT),
                    "value": [],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(list(ref_entry1.get_referred_objects()), [])
        self.assertEqual(list(ref_entry2.get_referred_objects()), [])
        self.assertEqual(list(ref_entry3.get_referred_objects()), [])

        # checks referred_object cache will be updated by the edit processing
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(name="ref").id),
                    "type": str(AttrType.OBJECT),
                    "value": [
                        {"data": str(ref_entry2.id), "index": 0},
                    ],
                    "referral_key": [],
                },
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(name="arr_ref").id),
                    "type": str(AttrType.ARRAY_OBJECT),
                    "value": [
                        {"data": str(ref_entry2.id), "index": 0},
                        {"data": str(ref_entry3.id), "index": 1},
                    ],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)

        # checks referred_object cache is updated by changing referring
        self.assertEqual(list(ref_entry1.get_referred_objects()), [])
        self.assertEqual(list(ref_entry2.get_referred_objects()), [entry])
        self.assertEqual(list(ref_entry3.get_referred_objects()), [entry])
        self.assertEqual(ref_entry2.get_referred_objects().count(), 1)
        self.assertEqual(ref_entry3.get_referred_objects().count(), 1)

        # delete referring entry and make sure that
        # the cahce of referred_entry of ref_entry is reset
        resp = self.client.post(
            reverse("entry:do_delete", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(ref_entry1.get_referred_objects()), [])
        self.assertEqual(list(ref_entry2.get_referred_objects()), [])
        self.assertEqual(list(ref_entry3.get_referred_objects()), [])

        # checks jobs were created as expected
        expected_job_infos = [
            {"op": JobOperation.CREATE_ENTRY, "count": 1},
            {"op": JobOperation.EDIT_ENTRY, "count": 2},
            {"op": JobOperation.DELETE_ENTRY, "count": 1},
            {"op": JobOperation.NOTIFY_CREATE_ENTRY, "count": 1},
            {"op": JobOperation.NOTIFY_UPDATE_ENTRY, "count": 2},
            {"op": JobOperation.NOTIFY_DELETE_ENTRY, "count": 1},
        ]
        for info in expected_job_infos:
            self.assertEqual(
                Job.objects.filter(user=user, operation=info["op"].value).count(),
                info["count"],
            )

        # checking for the cases of sending invalid referral parameters
        requests = [
            {"name": "entry_with_zero1", "value": "0"},
            {"name": "entry_with_zero2", "value": ""},
        ]

        for req in requests:
            params = {
                "entry_name": req["name"],
                "attrs": [
                    {
                        "id": str(entity.attrs.get(name="ref").id),
                        "type": str(AttrType.OBJECT),
                        "value": [
                            {"data": req["value"], "index": 0},
                        ],
                        "referral_key": [],
                    },
                    {
                        "id": str(entity.attrs.get(name="arr_ref").id),
                        "type": str(AttrType.ARRAY_OBJECT),
                        "value": [
                            {"data": req["value"], "index": 0},
                        ],
                        "referral_key": [],
                    },
                ],
            }

            with DisableStderr():
                resp = self.client.post(
                    reverse("entry:do_create", args=[entity.id]),
                    json.dumps(params),
                    "application/json",
                )

            self.assertEqual(resp.status_code, 200)

            entry = Entry.objects.get(name=req["name"])
            attr_ref = entry.attrs.get(schema__name="ref")
            entry.attrs.get(schema__name="arr_ref")

            self.assertIsNone(attr_ref.get_latest_value().referral)
            self.assertEqual(attr_ref.get_latest_value().data_array.count(), 0)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_create_entry_with_named_ref(self):
        user = self.admin_login()

        ref_entity = Entity.objects.create(name="referred_entity", created_user=user)
        ref_entry = Entry.objects.create(
            name="referred_entry", created_user=user, schema=ref_entity
        )

        entity = Entity.objects.create(name="entity", created_user=user)
        new_attr_params = {
            "name": "named_ref",
            "type": AttrType.NAMED_OBJECT,
            "created_user": user,
            "parent_entity": entity,
        }
        attr_base = EntityAttr.objects.create(**new_attr_params)
        attr_base.referral.add(ref_entity)

        # try to create with empty params
        params = {
            "entry_name": "new_entry1",
            "attrs": [
                {
                    "id": str(attr_base.id),
                    "type": str(AttrType.NAMED_OBJECT),
                    "referral_key": [],
                    "value": [],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(name="new_entry1")

        # An AttributeValue will be created at the creating processing even though
        # the value is empty, but except for invalid one.
        self.assertEqual(entry.attrs.get(name="named_ref").values.count(), 1)
        self.assertIsNone(entry.attrs.get(name="named_ref").values.first().referral)

        # try to create only with value which is a reference for other entry
        params = {
            "entry_name": "new_entry2",
            "attrs": [
                {
                    "id": str(attr_base.id),
                    "type": str(AttrType.NAMED_OBJECT),
                    "value": [{"data": str(ref_entry.id), "index": 0}],
                    "referral_key": [],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(name="new_entry2")
        self.assertEqual(entry.attrs.get(name="named_ref").values.count(), 1)
        self.assertEqual(entry.attrs.get(name="named_ref").values.last().value, "")
        self.assertEqual(entry.attrs.get(name="named_ref").values.last().referral.id, ref_entry.id)

        # try to create only with referral_key
        params = {
            "entry_name": "new_entry3",
            "attrs": [
                {
                    "id": str(attr_base.id),
                    "type": str(AttrType.NAMED_OBJECT),
                    "value": [],
                    "referral_key": [{"data": "hoge", "index": 0}],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(name="new_entry3")
        self.assertEqual(entry.attrs.get(name="named_ref").values.count(), 1)
        self.assertEqual(entry.attrs.get(name="named_ref").values.last().value, "hoge")
        self.assertEqual(entry.attrs.get(name="named_ref").values.last().referral, None)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_create_entry_with_array_named_ref(self):
        user = self.admin_login()

        ref_entity = Entity.objects.create(name="referred_entity", created_user=user)
        ref_entry = Entry.objects.create(
            name="referred_entry", created_user=user, schema=ref_entity
        )

        entity = Entity.objects.create(name="entity", created_user=user)
        new_attr_params = {
            "name": "arr_named_ref",
            "type": AttrType.ARRAY_NAMED_OBJECT,
            "created_user": user,
            "parent_entity": entity,
        }
        attr_base = EntityAttr.objects.create(**new_attr_params)
        attr_base.referral.add(ref_entity)

        params = {
            "entry_name": "new_entry",
            "attrs": [
                {
                    "id": str(attr_base.id),
                    "type": str(AttrType.ARRAY_NAMED_OBJECT),
                    "value": [
                        {"data": str(ref_entry.id), "index": 0},
                        {"data": str(ref_entry.id), "index": 1},
                    ],
                    "referral_key": [
                        {"data": "hoge", "index": 1},
                        {"data": "fuga", "index": 2},
                    ],
                }
            ],
        }

        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(name="new_entry")
        self.assertEqual(entry.attrs.get(name="arr_named_ref").values.count(), 1)

        attrv = entry.attrs.get(name="arr_named_ref").values.last()
        self.assertTrue(attrv.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT))
        self.assertEqual(attrv.data_array.count(), 3)

        self.assertEqual(attrv.data_array.all()[0].value, "")
        self.assertEqual(attrv.data_array.all()[0].referral.id, ref_entry.id)

        self.assertEqual(attrv.data_array.all()[1].value, "hoge")
        self.assertEqual(attrv.data_array.all()[1].referral.id, ref_entry.id)

        self.assertEqual(attrv.data_array.all()[2].value, "fuga")
        self.assertEqual(attrv.data_array.all()[2].referral, None)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_create_invalid_date_param(self):
        admin = self.admin_login()

        entity = Entity.objects.create(name="entity", created_user=admin)
        entity_attr = EntityAttr.objects.create(
            name="attr_date",
            type=AttrType.DATE,
            parent_entity=entity,
            created_user=admin,
        )

        # creates entry that has a invalid format parameter which is typed date
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(entity_attr.id),
                    "type": str(AttrType.DATE),
                    "value": [{"data": "2018-13-30", "index": 0}],
                    "referral_key": [],
                },
            ],
        }

        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_create_empty_date_param(self):
        admin = self.admin_login()

        entity = Entity.objects.create(name="entity", created_user=admin)
        entity_attr = EntityAttr.objects.create(
            name="attr_date",
            type=AttrType.DATE,
            parent_entity=entity,
            created_user=admin,
        )

        # creates entry that has a empty parameter which is typed date
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(entity_attr.id),
                    "type": str(AttrType.DATE),
                    "value": [{"data": "", "index": 0}],
                    "referral_key": [],
                },
            ],
        }

        # check that created a new entry with an empty date parameter
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)

        # get entry which is created in here
        entry = Entry.objects.get(name="entry", schema=entity)

        self.assertEqual(entry.attrs.count(), 1)
        self.assertIsNone(entry.attrs.last().get_latest_value().date)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_create_with_invalid_referral_params(self):
        user = self.admin_login()

        def checker_obj(attrv):
            self.assertIsNone(attrv.referral)

        def checker_name(attrv):
            self.assertEqual(attrv.value, "foo")
            self.assertIsNone(attrv.referral)

        def checker_arr_obj(attrv):
            self.assertEqual(attrv.data_array.count(), 0)

        def checker_arr_name(attrv):
            self.assertEqual(attrv.data_array.count(), 1)
            self.assertEqual(attrv.data_array.first().value, "foo")
            self.assertIsNone(attrv.data_array.first().referral)

        entity = Entity.objects.create(name="Entity", created_user=user)
        attr_info = {
            "obj": {"type": AttrType.OBJECT, "checker": checker_obj},
            "name": {"type": AttrType.NAMED_OBJECT, "checker": checker_name},
            "arr_obj": {
                "type": AttrType.ARRAY_OBJECT,
                "checker": checker_arr_obj,
            },
            "arr_name": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "checker": checker_arr_name,
            },
        }
        for attr_name, info in attr_info.items():
            EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )

        for i, value in enumerate(["", "0", 0, "9999", None]):
            entry_name = "entry-%d" % i
            params = {
                "entry_name": entry_name,
                "attrs": [
                    {
                        "id": str(x.id),
                        "type": str(x.type),
                        "value": [{"data": value, "index": 0}],
                        "referral_key": [{"data": "foo", "index": 0}]
                        if x.type & AttrType._NAMED
                        else [],
                    }
                    for x in entity.attrs.all()
                ],
            }

            with DisableStderr():
                resp = self.client.post(
                    reverse("entry:do_create", args=[entity.id]),
                    json.dumps(params),
                    "application/json",
                )

            self.assertEqual(resp.status_code, 200)
            entry = Entry.objects.get(name=entry_name, schema=entity)

            for name, info in attr_info.items():
                info["checker"](entry.attrs.get(schema__name=name).get_latest_value())

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_attribute_of_mandatory_params(self):
        """
        This tests the processing of creating entry would return error, or not,
        when non-value was specified in a mandatory parameter for each attribute type.
        """
        user = self.admin_login()

        # prepare to Entity and Entries which importing data refers to
        entity_info = {
            "str": {"type": AttrType.STRING},
            "obj": {"type": AttrType.OBJECT},
            "grp": {"type": AttrType.GROUP},
            "name": {"type": AttrType.NAMED_OBJECT},
            "bool": {"type": AttrType.BOOLEAN},
            "date": {"type": AttrType.DATE},
            "arr1": {"type": AttrType.ARRAY_STRING},
            "arr2": {"type": AttrType.ARRAY_OBJECT},
            "arr3": {"type": AttrType.ARRAY_NAMED_OBJECT},
        }
        for name, info in entity_info.items():
            # create entity that only has one attribute of specified type
            entity = Entity.objects.create(name=name, created_user=user)
            attr = EntityAttr.objects.create(
                name=name,
                type=info["type"],
                created_user=user,
                is_mandatory=True,
                parent_entity=entity,
            )

            # send a request to create entry and expect to be error
            referral_key = []
            if info["type"] & AttrType._NAMED:
                referral_key = [{"data": "", "index": 0}]
            params = {
                "entry_name": "entry",
                "attrs": [
                    {
                        "id": str(attr.id),
                        "type": str(info["type"]),
                        "value": [{"data": "", "index": 0}],
                        "referral_key": referral_key,
                    }
                ],
            }
            resp = self.client.post(
                reverse("entry:do_create", args=[entity.id]),
                json.dumps(params),
                "application/json",
            )
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(Entry.objects.filter(schema=entity).count(), 0)

            # when a referral_key is specified, named type will be successful to create
            if info["type"] & AttrType._NAMED:
                referral_key[0]["data"] = "hoge"
                resp = self.client.post(
                    reverse("entry:do_create", args=[entity.id]),
                    json.dumps(params),
                    "application/json",
                )

                self.assertEqual(resp.status_code, 200)
                self.assertEqual(Entry.objects.filter(schema=entity).count(), 1)

    def test_set_mandatory_attrs_with_empty_referral(self):
        """
        This tests whether an entry could be created with empty referral value.
        In this test case, this creates entities which have each different attribute
        that refers entry. And this confirms whether an entry could be created with
        empty value which is equivalent of '- NOT SET -'.
        """

        user = self.guest_login()

        ref_entity = Entity.objects.create(name="ref", created_user=user)
        for index, attr_type in enumerate(
            [
                AttrType.OBJECT,
                AttrType.NAMED_OBJECT,
                AttrType.ARRAY_OBJECT,
                AttrType.ARRAY_NAMED_OBJECT,
            ]
        ):
            # create Entity and Entry which test to create
            entity = Entity.objects.create(name="E%d" % index, created_user=user)
            attr = EntityAttr.objects.create(
                name="attr",
                type=attr_type,
                created_user=user,
                is_mandatory=True,
                parent_entity=entity,
            )
            attr.referral.add(ref_entity)

            referral_key = []
            if attr_type & AttrType._NAMED:
                referral_key = [{"data": "", "index": 0}]

            # This checks error response would be returned by sending a request
            # to create entry by specifying 0('- NOT SET -') parameter that indicates
            # there is no matched entry to the mandatroy attribute.
            params = {
                "entry_name": "entry",
                "attrs": [
                    {
                        "id": str(attr.id),
                        "value": [{"data": "0", "index": 0}],
                        "referral_key": referral_key,
                    }
                ],
            }
            resp = self.client.post(
                reverse("entry:do_create", args=[entity.id]),
                json.dumps(params),
                "application/json",
            )

            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.content, b"You have to specify value at mandatory parameters")
            self.assertEqual(Entry.objects.filter(schema=entity).count(), 0)

    def test_update_entry_without_backend(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)

        params = {
            "entry_name": "hoge",
            "attrs": [],
        }

        def side_effect(job_id):
            job = Job.objects.get(id=job_id)

            self.assertEqual(job.user.id, user.id)
            self.assertEqual(job.target.id, entry.id)
            self.assertEqual(job.target_type, JobTarget.ENTRY)
            self.assertEqual(job.status, JobStatus.PREPARING)
            self.assertEqual(job.operation, JobOperation.EDIT_ENTRY)

        with patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=side_effect)):
            resp = self.client.post(
                reverse("entry:do_edit", args=[entry.id]),
                json.dumps(params),
                "application/json",
            )

            self.assertEqual(resp.status_code, 200)

    @patch("entry.tasks.delete_entry.delay", Mock(side_effect=tasks.delete_entry))
    def test_not_to_show_deleted_entry(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)

        # delete entry and check each page couldn't be shown
        entry.delete()

        # Check status code and transition destination url
        test_suites = [
            "entry:show",
            "entry:edit",
            "entry:copy",
            "entry:refer",
            "entry:history",
        ]
        for test_suite in test_suites:
            resp = self.client.get(reverse(test_suite, args=[entry.id]))
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp.url, "/entry/restore/{}/?keyword={}".format(entity.id, entry.name)
            )

    def test_not_to_show_under_processing_entry(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)

        # update status of entry and check each page couldn't be shown
        entry.set_status(Entry.STATUS_EDITING)
        self.assertEqual(self.client.get(reverse("entry:copy", args=[entry.id])).status_code, 400)

        entry.set_status(Entry.STATUS_CREATING)
        self.assertEqual(self.client.get(reverse("entry:show", args=[entry.id])).status_code, 400)
        self.assertEqual(self.client.get(reverse("entry:edit", args=[entry.id])).status_code, 400)
        self.assertEqual(self.client.get(reverse("entry:copy", args=[entry.id])).status_code, 400)
        self.assertEqual(self.client.get(reverse("entry:refer", args=[entry.id])).status_code, 400)
        self.assertEqual(
            self.client.get(reverse("entry:history", args=[entry.id])).status_code, 400
        )

    def test_show_entry_history(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)
        EntityAttr.objects.create(
            **{
                "name": "attr",
                "created_user": user,
                "parent_entity": entity,
                "type": AttrType.STRING,
            }
        )

        # create and add values
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        [entry.attrs.first().add_value(user, str(x)) for x in range(3)]

        resp = self.client.get(reverse("entry:history", args=[entry.id]))
        self.assertEqual(resp.status_code, 200)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_create_and_edit_without_type_parameter(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)
        attr = EntityAttr.objects.create(
            name="attr",
            created_user=user,
            parent_entity=entity,
            type=AttrType.STRING,
        )

        # create without type parameter
        params = {
            "entry_name": "entry",
            "attrs": [
                {"id": str(attr.id), "value": [{"data": "hoge", "index": "0"}]},
            ],
        }
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.get(name="entry", schema=entity, is_active=True)
        self.assertEqual(entry.attrs.first().get_latest_value().value, "hoge")

        # edit without type parameter
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.first().id),
                    "value": [{"data": "fuga", "index": "0"}],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        entry.refresh_from_db()
        self.assertEqual(entry.attrs.first().get_latest_value().value, "fuga")

    def test_index_deleting_entries(self):
        # initialize entries to test
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)

        # to check the view of deleted entries, all entries would be deleted just after creating
        entries = []
        for index in range(3):
            entry = Entry.objects.create(name="e-%d" % index, schema=entity, created_user=user)
            entry.delete()

            entries.append(entry)

        # to check that entries that are set status would not be listed at restore page
        entries[1].set_status(Entry.STATUS_CREATING)

        resp = self.client.get(reverse("entry:restore", args=[entity.id]), {"page": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["entity"].id, entity.id)
        self.assertEqual(len(resp.context["page_obj"]), 2)

        # check listing entries are ordered by desc
        self.assertEqual(resp.context["page_obj"][0].name.find("e-2"), 0)
        self.assertEqual(resp.context["page_obj"][1].name.find("e-0"), 0)

        # If called from other than the job list,
        # confirm that the search keyword has not been entered
        self.assertIsNone(resp.context["keyword"])

        # If called from the job list, make sure that the search keyword has been entered
        resp = self.client.get("/entry/restore/%d/?keyword=%s" % (entity.id, entries[0].name))
        self.assertEqual(resp.context["keyword"], entries[0].name)

        # If the page is invalid
        resp = self.client.get(reverse("entry:restore", args=[entity.id]), {"page": 100})
        self.assertEqual(resp.status_code, 400)
        resp = self.client.get(reverse("entry:restore", args=[entity.id]), {"page": "invalid"})
        self.assertEqual(resp.status_code, 400)

    @patch("entry.tasks.restore_entry.delay", Mock(side_effect=tasks.restore_entry))
    @patch("entry.tasks.notify_create_entry.delay")
    def test_restore_entry(self, mock_task):
        # initialize entries to test
        user = self.guest_login()
        role: Role = Role.objects.create(name="Role")
        role.users.add(user)
        entity = Entity.objects.create(name="entity", created_user=user)
        EntityAttr.objects.create(
            **{
                "name": "attr",
                "type": AttrType.STRING,
                "created_user": user,
                "parent_entity": entity,
            }
        )

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        # send request with invalid entry-id
        resp = self.client.post(
            reverse("entry:do_restore", args=[9999]), json.dumps({}), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

        # send request with entry-id which is active
        resp = self.client.post(
            reverse("entry:do_restore", args=[entry.id]),
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        obj = json.loads(resp.content.decode("UTF-8"))
        self.assertEqual(obj["msg"], "Failed to get entry from specified parameter")

        # delete target entry to run restore processing
        entry.delete()

        entry.refresh_from_db()
        self.assertTrue(entry.name.find("_deleted_") > 0)
        self.assertFalse(any([x.is_active for x in entry.attrs.all()]))

        # nothing permisson
        entry.is_public = False
        entry.save()
        resp = self.client.post(
            reverse("entry:do_restore", args=[entry.id]),
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"You don't have permission to access this object")
        entry.refresh_from_db()
        self.assertFalse(entry.is_active)

        # readable permission
        entry.readable.roles.add(role)
        resp = self.client.post(
            reverse("entry:do_restore", args=[entry.id]),
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"You don't have permission to access this object")
        entry.refresh_from_db()
        self.assertFalse(entry.is_active)

        # writable permission
        entry.writable.roles.add(role)
        resp = self.client.post(
            reverse("entry:do_restore", args=[entry.id]),
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        entry.refresh_from_db()
        self.assertEqual(entry.name, "entry")
        self.assertTrue(entry.is_active)
        self.assertTrue(all([x.is_active for x in entry.attrs.all()]))

        # check that index information of restored entry in Elasticsearch is also restored
        resp = AdvancedSearchService.search_entries(user, [entity.id])
        self.assertEqual(resp.ret_count, 1)
        self.assertEqual(resp.ret_values[0].entry["id"], entry.id)
        self.assertEqual(resp.ret_values[0].entry["name"], entry.name)

        self.assertTrue(mock_task.called)

    def test_restore_when_duplicate_entry_exist(self):
        # initialize entries to test
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        # delete target entry to run restore processing
        entry.delete()

        # After deleting, create an entry with the same name
        dup_entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        resp = self.client.post(
            reverse("entry:do_restore", args=[entry.id]),
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        obj = json.loads(resp.content.decode("UTF-8"))
        self.assertEqual(obj["msg"], "")
        self.assertEqual(obj["entry_id"], dup_entry.id)
        self.assertEqual(obj["entry_name"], dup_entry.name)

    def test_restore_when_another_same_named_alias_exists(self):
        user = self.guest_login()

        # create Model, Item and Alias that is same name with updating Item in this test
        model = self.create_entity(user, "Mountain")
        other_item = self.add_entry(user, "Chomolungma", model)
        other_item.delete()
        item = self.add_entry(user, "Everest", model)
        item.add_alias("Chomolungma")

        resp = self.client.post(
            reverse("entry:do_restore", args=[other_item.id]),
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode("utf-8"), "Duplicate named Alias is existed")

    @patch("entry.tasks.notify_update_entry.delay")
    def test_revert_attrv(self, mock_task):
        user = self.guest_login()

        # initialize referred objects
        ref_entity = Entity.objects.create(name="RefEntity", created_user=user)
        ref_entries = [
            Entry.objects.create(name="r%d" % i, created_user=user, schema=ref_entity)
            for i in range(3)
        ]
        groups = [Group.objects.create(name="g%d" % i) for i in range(2)]

        # initialize Entity and Entry
        entity = Entity.objects.create(name="Entity", created_user=user)

        # First of all, this test set values which is in 'values' of attr_info to each attributes
        # in order of first and second (e.g. in the case of 'str', this test sets 'foo' at first,
        # then sets 'bar') manually. After that, this test retrieve first value by calling the
        # 'revert_attrv' handler. So finnaly, this test expects first value is stored
        # in Database and Elasticsearch.
        attr_info = {
            "str": {"type": AttrType.STRING, "values": ["foo", "bar"]},
            "obj": {
                "type": AttrType.OBJECT,
                "values": [ref_entries[0], ref_entries[1]],
            },
            "grp": {"type": AttrType.GROUP, "values": [groups[0], groups[1]]},
            "name": {
                "type": AttrType.NAMED_OBJECT,
                "values": [
                    {"name": "foo", "id": ref_entries[0]},
                    {"name": "bar", "id": ref_entries[1]},
                ],
            },
            "bool": {"type": AttrType.BOOLEAN, "values": [False, True]},
            "date": {
                "type": AttrType.DATE,
                "values": ["2018-01-01", "2018-02-01"],
            },
            "arr1": {
                "type": AttrType.ARRAY_STRING,
                "values": [["foo", "bar", "baz"], ["hoge", "fuga", "puyo"]],
            },
            "arr2": {
                "type": AttrType.ARRAY_OBJECT,
                "values": [[ref_entries[0], ref_entries[1]], [ref_entries[2]]],
            },
            "arr3": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "values": [
                    [
                        {"name": "foo", "id": ref_entries[0]},
                        {"name": "bar", "id": ref_entries[1]},
                    ],
                    [
                        {"name": "", "id": ref_entries[1]},
                        {"name": "fuga", "id": ref_entries[2]},
                    ],
                ],
            },
        }
        for attr_name, info in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name,
                type=info["type"],
                created_user=user,
                parent_entity=entity,
            )

            if info["type"] & AttrType.OBJECT:
                attr.referral.add(ref_entity)

        # initialize each AttributeValues
        entry = Entry.objects.create(name="Entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        for attr_name, info in attr_info.items():
            attr = entry.attrs.get(schema__name=attr_name)
            attrv1 = attr.add_value(user, info["values"][0])

            # store first value's attrv
            info["expected_value"] = attrv1.get_value()

            # update value to second value
            attrv2 = attr.add_value(user, info["values"][1])

            # check value is actually updated
            self.assertNotEqual(attrv1.get_value(), attrv2.get_value())

            # reset AttributeValue and latest_value equals with attrv1
            params = {"attr_id": str(attr.id), "attrv_id": str(attrv1.id)}
            resp = self.client.post(
                reverse("entry:revert_attrv"), json.dumps(params), "application/json"
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(attrv1.get_value(), attr.get_latest_value().get_value())

        resp = AdvancedSearchService.search_entries(user, [entity.id], [], is_output_all=True)
        self.assertEqual(resp.ret_count, 1)
        for attr_name, data in resp.ret_values[0].attrs.items():
            self.assertEqual(data["type"], attr_info[attr_name]["type"])

            value = attr_info[attr_name]["values"][0]
            if data["type"] == AttrType.BOOLEAN:
                self.assertEqual(data["value"], value)

            elif data["type"] == AttrType.GROUP:
                self.assertEqual(data["value"], {"name": value.name, "id": value.id})

            elif data["type"] == AttrType.OBJECT:
                self.assertEqual(data["value"], {"name": value.name, "id": value.id})

            elif data["type"] == AttrType.ARRAY_OBJECT:
                self.assertEqual(data["value"], [{"name": x.name, "id": x.id} for x in value])

            elif data["type"] == AttrType.NAMED_OBJECT:
                self.assertEqual(
                    data["value"],
                    {value["name"]: {"name": value["id"].name, "id": value["id"].id}},
                )

            elif data["type"] == AttrType.ARRAY_NAMED_OBJECT:
                self.assertEqual(
                    data["value"],
                    [{x["name"]: {"name": x["id"].name, "id": x["id"].id}} for x in value],
                )

            else:
                self.assertEqual(data["value"], value)

        self.assertEqual(mock_task.call_count, len(attr_info))

    def test_revert_attrv_for_autoname(self):
        user = self.guest_login()
        model_lb = self.create_entity(user, "LB")
        model_sg = self.create_entity(
            user,
            "LBServiceGroup",
            attrs=[
                {
                    "name": "LB",
                    "type": AttrType.OBJECT,
                    "ref": model_lb,
                    "name_order": 1,
                    "name_prefix": "[",
                    "name_postfix": "]",
                },
                {"name": "domain", "type": AttrType.STRING, "name_order": 2, "name_prefix": " "},
                {"name": "port", "type": AttrType.STRING, "name_order": 3, "name_prefix": ":"},
            ],
            item_name_type=ItemNameType.ATTR,
        )

        item_lb = self.add_entry(user, "LB0001", model_lb)
        item_sg = self.add_entry(
            user,
            "ChangingName",
            model_sg,
            values={
                "lb": item_lb.id,
                "domain": "test.example.com",
                "port": "10000",
            },
        )
        item_sg.save_autoname()

        # update its attribute values
        attr_domain = item_sg.attrs.get(schema__name="domain")
        v1 = attr_domain.add_value(user, "hoge.example.com")
        v2 = attr_domain.add_value(user, "fuga.example.com")

        # revert attribute value of 'domain' and check its name is followed by its change
        params = {"attr_id": str(attr_domain.id), "attrv_id": str(v1.id)}
        resp = self.client.post(
            reverse("entry:revert_attrv"), json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(attr_domain.get_latest_value().get_value(), "hoge.example.com")
        item_sg.refresh_from_db()
        self.assertEqual(item_sg.name, "[LB0001] hoge.example.com:10000")
        # ---
        params = {"attr_id": str(attr_domain.id), "attrv_id": str(v2.id)}
        resp = self.client.post(
            reverse("entry:revert_attrv"), json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(attr_domain.get_latest_value().get_value(), "fuga.example.com")
        item_sg.refresh_from_db()
        self.assertEqual(item_sg.name, "[LB0001] fuga.example.com:10000")

    @patch(
        "trigger.tasks.may_invoke_trigger.delay",
        Mock(side_effect=trigger_tasks.may_invoke_trigger),
    )
    def test_invoke_trigger_by_revert_attrv(self):
        user = self.guest_login()

        # initialize Entity and Entry that are used in this test
        entity = self.create_entity(
            user,
            "Entity",
            [
                {"name": "cond_str", "type": AttrType.STRING},
                {"name": "cond_name", "type": AttrType.NAMED_OBJECT},
                {"name": "action", "type": AttrType.STRING},
            ],
        )

        # register TriggerAction configuration before creating an Entry
        TriggerCondition.register(
            entity,
            [{"attr_id": entity.attrs.get(name="cond_str").id, "cond": "hoge"}],
            [{"attr_id": entity.attrs.get(name="action").id, "value": "fuga"}],
        )
        TriggerCondition.register(
            entity,
            [{"attr_id": entity.attrs.get(name="cond_name").id, "cond": "foo"}],
            [{"attr_id": entity.attrs.get(name="action").id, "value": "fuga"}],
        )

        # changed value to retrieve
        testing_params = [
            ("cond_str", "hoge", "changed", Q(value="hoge")),
            (
                "cond_name",
                {"name": "foo", "id": None},
                {"name": "changed", "id": None},
                Q(value="foo"),
            ),
        ]
        for index, (attrname, initial_value, changed_value, query) in enumerate(testing_params):
            entry = self.add_entry(
                user,
                "TestEntry-%d" % index,
                entity,
                values={
                    attrname: initial_value,
                },
            )
            changing_attr = entry.attrs.get(name=attrname)
            changing_attr.add_value(user, changed_value)

            # send request to revert attribute value of "cond"
            revert_attrv = changing_attr.values.filter(query).last()
            params = {"attr_id": str(changing_attr.id), "attrv_id": str(revert_attrv.id)}
            resp = self.client.post(
                reverse("entry:revert_attrv"), json.dumps(params), "application/json"
            )
            self.assertEqual(resp.status_code, 200)

            # This check that Attribute value of "action" would be updated by TriggerAction
            self.assertEqual(entry.get_attrv("action").value, "fuga")

            # check trigger action was worked properly
            job_query = Job.objects.filter(operation=JobOperation.MAY_INVOKE_TRIGGER)
            self.assertEqual(job_query.count(), 1 + index)
            self.assertEqual(job_query.last().status, JobStatus.DONE)

    def test_revert_attrv_with_invalid_value(self):
        user = self.guest_login()

        # initialize Entity and Entry
        entity = Entity.objects.create(name="Entity", created_user=user)
        [
            EntityAttr.objects.create(
                **{
                    "name": attr_name,
                    "type": AttrType.STRING,
                    "created_user": user,
                    "parent_entity": entity,
                }
            )
            for attr_name in ["attr1", "attr2"]
        ]

        entry = Entry.objects.create(name="Entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        attr1 = entry.attrs.first()

        # send request with invalid arguments
        params = {"attr_id": "0", "attrv_id": "0"}
        resp = self.client.post(
            reverse("entry:revert_attrv"), json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"Specified Attribute-id is invalid")

        params = {"attr_id": str(attr1.id), "attrv_id": "0"}
        resp = self.client.post(
            reverse("entry:revert_attrv"), json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"Specified AttributeValue-id is invalid")

        attrvs = [attr1.add_value(user, str(x)) for x in range(2)]
        self.assertEqual(attr1.get_latest_value(), attrvs[-1])

        # change Attribute type of attr then get latest AttributeValue
        attr1.schema.type = AttrType.OBJECT
        attr1.schema.save(update_fields=["type"])

        self.assertGreater(attr1.get_latest_value().id, attrvs[-1].id)

        # specify attrv_id which refers different parent_attr
        params = {"attr_id": str(entry.attrs.last().id), "attrv_id": str(attrvs[0].id)}
        resp = self.client.post(
            reverse("entry:revert_attrv"), json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"Specified AttributeValue-id is invalid")

    @patch("airone.lib.custom_view.is_custom", Mock(return_value=True))
    @patch("airone.lib.custom_view.call_custom", Mock(return_value=HttpResponse("success")))
    def test_revert_attrv_with_custom_view(self):
        user = self.guest_login()

        # initialize Entity and Entry
        entity = Entity.objects.create(name="Entity", created_user=user)
        EntityAttr.objects.create(
            **{
                "name": "attr",
                "type": AttrType.STRING,
                "created_user": user,
                "parent_entity": entity,
            }
        )

        entry = Entry.objects.create(name="Entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        attr = entry.attrs.first()

        # set AttributeValues to the Attribute object
        attrv1 = attr.add_value(user, "hoge")
        attr.add_value(user, "fuga")
        number_of_attrvalue = attr.values.count()

        # send request to revert AttributeValue which is set before
        params = {"attr_id": str(attr.id), "attrv_id": str(attrv1.id)}
        resp = self.client.post(
            reverse("entry:revert_attrv"), json.dumps(params), "application/json"
        )

        # the latest AttributeValue object is reverted from "fuga" to "hoge"
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(attr.values.count(), number_of_attrvalue + 1)
        self.assertEqual(attr.get_latest_value().value, attrv1.value)
        self.assertNotEqual(attr.get_latest_value().id, attrv1.id)

    @patch("airone.lib.custom_view.is_custom", Mock(return_value=True))
    @patch("airone.lib.custom_view.call_custom", Mock(return_value=HttpResponse("success")))
    def test_revert_attrv_with_custom_view_by_latest_value(self):
        user = self.guest_login()

        # initialize Entity and Entry
        entity = Entity.objects.create(name="Entity", created_user=user)
        EntityAttr.objects.create(
            **{
                "name": "attr",
                "type": AttrType.STRING,
                "created_user": user,
                "parent_entity": entity,
            }
        )

        entry = Entry.objects.create(name="Entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        attr = entry.attrs.first()

        # set AttributeValue to Attribute
        attrv = attr.add_value(user, "hoge")
        number_of_attrvalue = attr.values.count()

        # try to revert AttributeValue which is the latest one
        params = {"attr_id": str(attr.id), "attrv_id": str(attrv.id)}
        resp = self.client.post(
            reverse("entry:revert_attrv"), json.dumps(params), "application/json"
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(attr.values.count(), number_of_attrvalue)
        self.assertEqual(attr.get_latest_value(), attrv)

    @patch("airone.lib.custom_view.is_custom", Mock(return_value=True))
    @patch(
        "airone.lib.custom_view.call_custom", Mock(return_value=HttpResponse("test", status=400))
    )
    def test_call_custom_do_create_entry_return_int(self):
        self.admin_login()

        params = {
            "entry_name": "hoge",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "type": str(AttrType.ARRAY_STRING),
                    "value": [{"data": "hoge", "index": "0"}],
                    "referral_key": [],
                },
            ],
        }

        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)

    @patch("airone.lib.custom_view.is_custom", Mock(return_value=True))
    @patch(
        "airone.lib.custom_view.call_custom",
        Mock(
            return_value=JsonResponse(
                {
                    "entry_id": 1,
                    "entry_name": "fuga",
                }
            )
        ),
    )
    def test_call_custom_do_create_entry_return_json(self):
        self.admin_login()

        params = {
            "entry_name": "hoge",
            "attrs": [
                {
                    "id": str(self._entity_attr.id),
                    "type": str(AttrType.ARRAY_STRING),
                    "value": [{"data": "hoge", "index": "0"}],
                    "referral_key": [],
                },
            ],
        }

        resp = self.client.post(
            reverse("entry:do_create", args=[self._entity.id]),
            json.dumps(params),
            "application/json",
        )

        data = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data["entry_id"], 1)
        self.assertEqual(data["entry_name"], "fuga")

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    @patch.object(Job, "is_canceled", Mock(return_value=True))
    def test_cancel_creating_entry(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entity_attr = EntityAttr.objects.create(
            name="attr",
            type=AttrType.STRING,
            parent_entity=entity,
            created_user=user,
        )

        # creates entry that has a parameter which is typed boolean
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(entity_attr.id),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
            ],
        }

        # This task would be canceled because is_canceled method of creating job object
        # returns True.
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.last()
        self.assertFalse(entry.is_active)
        self.assertIn("entry_deleted_", entry.name)

    @patch.object(Job, "is_canceled", Mock(return_value=True))
    @patch.object(Job, "proceed_if_ready", Mock(return_value=False))
    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_cancel_creating_entry_before_starting_background_processing(self):
        user = self.admin_login()
        entity = Entity.objects.create(name="entity", created_user=user)

        # The case that job is canceled before staring background processing
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps({"entry_name": "entry", "attrs": []}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        entry = Entry.objects.last()
        self.assertFalse(entry.is_active)
        self.assertIn("entry_deleted_", entry.name)

    @patch.object(Job, "is_canceled", Mock(return_value=True))
    @patch("entry.tasks.import_entries.delay", Mock(side_effect=tasks.import_entries))
    def test_cancel_importing_entries(self):
        self.admin_login()

        fp = self.open_fixture_file("import_data03.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[self._entity.id]), {"file": fp})
        fp.close()

        # check the import is success
        self.assertEqual(resp.status_code, 303)
        self.assertEqual(Entry.objects.filter(schema=self._entity).count(), 0)
        self.assertEqual(
            Job.objects.last().text, "Now importing... (progress: [    1/    3] for hoge)"
        )

    @patch(
        "entry.tasks.register_referrals.delay",
        Mock(side_effect=tasks.register_referrals),
    )
    def test_change_name_of_referral_entry(self):
        """This creates an Entry instance that refers ref_entry. After that,
        this changes name of ref_entry, then getting search result of
        elasticsearch to check changing wether entry name would be reflected.
        """

        # Create an entry that refers ref_entry through attribute 'ref'
        user = self.guest_login()
        ref_entity = Entity.objects.create(name="ref_entity", created_user=user)
        ref_entry = Entry.objects.create(name="before_change", created_user=user, schema=ref_entity)

        entity = Entity.objects.create(name="entity", created_user=user)
        EntityAttr.objects.create(
            **{
                "name": "ref",
                "created_user": user,
                "type": AttrType.OBJECT,
                "parent_entity": entity,
            }
        )
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)
        entry.attrs.first().add_value(user, ref_entry)
        entry.register_es()

        # Change name of entry
        params = {
            "entry_name": "changed_name",
            "attrs": [],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[ref_entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        ref_entry.refresh_from_db()
        self.assertEqual(ref_entry.name, "changed_name")

        # check entry changing reflects to the ElasticSearch
        ret = AdvancedSearchService.search_entries(user, [entity.id], [AttrHint(name="ref")])
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual(ret.ret_values[0].entry["name"], "entry")
        self.assertEqual(ret.ret_values[0].attrs["ref"]["value"]["name"], "changed_name")

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_run_create_entry_task_duplicately(self):
        user = self.guest_login()

        # initialize data for test
        entity = self.create_entity(user, "Entity", [{"name": "hoge"}])

        # sending a request to create Entry
        params = {"entry_name": "entry", "attrs": []}
        for entity_attr in entity.attrs.all():
            params["attrs"].append(
                {
                    "id": str(entity_attr.id),
                    "type": entity_attr.type,
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                }
            )
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # This confirms above sending request create expected Job and Entry instances
        entry = Entry.objects.get(name="entry", schema=entity, is_active=True)
        # checks created jobs and its params are as expected
        jobs = Job.objects.filter(user=user, target=entry)
        job_expectations = [
            {
                "operation": JobOperation.CREATE_ENTRY,
                "status": JobStatus.DONE,
                "dependent_job": None,
            },
            {
                "operation": JobOperation.NOTIFY_CREATE_ENTRY,
                "status": JobStatus.PREPARING,
                "dependent_job": None,
            },
            {
                "operation": JobOperation.MAY_INVOKE_TRIGGER,
                "status": JobStatus.PREPARING,
                "dependent_job": jobs.get(operation=JobOperation.CREATE_ENTRY),
            },
        ]
        self.assertEqual(jobs.count(), len(job_expectations))
        for expectation in job_expectations:
            obj = jobs.get(operation=expectation["operation"].value)
            self.assertEqual(obj.target.id, entry.id)
            self.assertEqual(obj.target_type, JobTarget.ENTRY)
            self.assertEqual(obj.status, expectation["status"])
            self.assertEqual(obj.dependent_job, expectation["dependent_job"])

        # Rerun creating that entry job (This is core processing of this test)
        job_create = Job.objects.get(user=user, operation=JobOperation.CREATE_ENTRY)
        job_create.status = JobStatus.PREPARING
        job_create.save()
        job_create.run(will_delay=False)

        # This confirms unexpected Attribute instances were not created
        # when creating job was run duplicately.
        self.assertEqual(
            Entry.objects.get(id=entry.id).attrs.count(),
            Entity.objects.get(id=entity.id).attrs.count(),
        )

    def test_acl_is_not_editable_when_superiors_has_not_full_permission(self):
        # This tests Entry, EntityAttr and Attribute couldn't be editable when
        # superior Entity doesn't have full permission.

        user = self.guest_login()
        for index, acltype in enumerate([ACLType.Readable, ACLType.Writable]):
            entity = self.create_entity(
                user,
                "Test Another Entity %d" % index,
                attrs=[{"name": "attr", "type": AttrType.STRING}],
                is_public=False,
                default_permission=acltype.id,
            )
            # check Entry's ACL can NOT be editable
            entry = self.add_entry(user, "TestEntry", entity)
            resp = self.client.get(reverse("entry:acl", args=[entry.id]))
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.content.decode("utf-8"), "You don't have permission to access this object"
            )

            # check Attribute's and EntityAttr's ACL can NOT be editable
            attr = entry.attrs.last()
            self.assertEqual(attr.schema.name, "attr")
            for instance in [attr, attr.schema]:
                resp = self.client.get(reverse("acl:index", args=[instance.id]))
                self.assertEqual(resp.status_code, 400)
                self.assertEqual(
                    resp.content.decode("utf-8"), "You don't have permission to access this object"
                )

    def test_acl_of_attribute_is_not_editable_when_entityattr_has_not_full_permission(self):
        # This tests Attribute ACL couldn't be editable when
        # superior EntityAttr doesn't have full permission.

        user = self.guest_login()
        for index, acltype in enumerate([ACLType.Readable, ACLType.Writable]):
            entity = self.create_entity(
                user,
                "Test Another Entity %d" % index,
                attrs=[
                    {
                        "name": "attr",
                        "type": AttrType.STRING,
                        "is_public": False,
                        "default_permission": acltype.id,
                    }
                ],
                is_public=True,
                default_permission=acltype.id,
            )
            # check Entry's ACL CAN be editable
            entry = self.add_entry(user, "TestEntry", entity)
            resp = self.client.get(reverse("entry:acl", args=[entry.id]))
            self.assertEqual(resp.status_code, 200)

            # check Attribute's and EntityAttr's ACL can NOT be editable
            attr = entry.attrs.last()
            self.assertEqual(attr.schema.name, "attr")
            for instance in [attr, attr.schema]:
                resp = self.client.get(reverse("acl:index", args=[instance.id]))
                self.assertEqual(resp.status_code, 400)
                self.assertEqual(
                    resp.content.decode("utf-8"), "You don't have permission to access this object"
                )

    def test_acl_of_attribute_is_not_editable_when_entry_has_not_full_permission(self):
        # This tests Attribute ACL couldn't be editable when
        # superior Entry doesn't have full permission.

        user = self.guest_login()
        for index, acltype in enumerate([ACLType.Readable, ACLType.Writable]):
            entity = self.create_entity(
                user,
                "Test Another Entity %d" % index,
                attrs=[{"name": "attr", "type": AttrType.STRING, "is_public": True}],
                is_public=True,
                default_permission=acltype.id,
            )
            entry = self.add_entry(user, "TestEntry", entity, is_public=False)
            attr = entry.attrs.last()

            # check EntityAttr's ACL CAN be editable
            resp = self.client.get(reverse("acl:index", args=[attr.schema.id]))
            self.assertEqual(resp.status_code, 200)

            # check Attribute's ACL can NOT be editable
            resp = self.client.get(reverse("acl:index", args=[attr.id]))
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(
                resp.content.decode("utf-8"), "You don't have permission to access this object"
            )

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_update_entry_has_prohibited_attribute(self):
        admin = User.objects.create(username="Admin", is_superuser=True)
        user = self.guest_login()

        # Create Entity and Entry that user can't update it
        entity = self.create_entity(
            user,
            "Entity",
            attrs=[
                {"name": "Attr", "type": AttrType.STRING},
            ],
        )
        entity_attr = entity.attrs.last()
        entity_attr.is_public = False
        entity_attr.default_permissoin = ACLType.Nothing.id
        entity_attr.save()

        entry = self.add_entry(
            admin,
            "entry",
            entity,
            values={"Attr": "hogefuga"},
        )

        # This request try to update Attr's value, which is prohibited to update
        # by requested user.
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.last().id),
                    "type": str(AttrType.STRING),
                    "value": [{"data": "", "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]), json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(entry.get_attrv("Attr").value, "hogefuga")

    def test_create_entry_over_201_characters(self):
        user = self.guest_login()

        # initialize data for test
        entity = self.create_entity(user, "Entity", [{"name": "hoge"}])

        # sending a request to create Entry
        params = {"entry_name": "a" * 201, "attrs": []}
        resp = self.client.post(
            reverse("entry:do_create", args=[entity.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
