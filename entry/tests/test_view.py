import errno
import json
import logging
from datetime import date
from unittest import skip
from unittest.mock import Mock, patch

import yaml
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.urls import reverse

from airone.lib.acl import ACLType
from airone.lib.elasticsearch import AttrHint
from airone.lib.log import Logger
from airone.lib.test import AironeViewTest, DisableStderr
from airone.lib.types import (
    AttrType,
)
from entity.models import Entity, EntityAttr
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


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        # clear data which is used in individual tests
        self._test_data = {}

    # override 'admin_login' method to create initial Entity/EntityAttr objects
    def admin_login(self):
        user = super(ViewTest, self).admin_login()

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

    def make_attr(
        self,
        name,
        attrtype=AttrType.STRING,
        created_user=None,
        parent_entity=None,
        parent_entry=None,
    ):
        schema = EntityAttr.objects.create(
            name=name,
            type=attrtype,
            created_user=(created_user and created_user or self._user),
            parent_entity=(parent_entity and parent_entity or self._entity),
        )

        return Attribute.objects.create(
            name=name,
            schema=schema,
            created_user=(created_user and created_user or self._user),
            parent_entry=(parent_entry and parent_entry or self._entry),
        )

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

    def test_get_edit_without_login(self):
        resp = self.client.get(reverse("entry:edit", args=[0]))
        self.assertEqual(resp.status_code, 303)

    def test_get_edit_with_invalid_entry_id(self):
        user = self.admin_login()

        Entry(name="fuga", schema=self._entity, created_user=user).save()

        # with invalid entry-id
        resp = self.client.get(reverse("entry:edit", args=[0]))
        self.assertEqual(resp.status_code, 400)

    def test_get_edit_with_valid_entry_id(self):
        user = self.admin_login()

        # making test Entry set
        entry = Entry(name="fuga", schema=self._entity, created_user=user)
        entry.save()

        for attr_name in ["foo", "bar"]:
            attr = self.make_attr(name=attr_name, parent_entry=entry, created_user=user)

            for value in ["hoge", "fuga"]:
                attr_value = AttributeValue(value=value, created_user=user, parent_attr=attr)
                attr_value.save()

                attr.values.add(attr_value)

        # with invalid entry-id
        resp = self.client.get(reverse("entry:edit", args=[entry.id]))
        self.assertEqual(resp.status_code, 200)

    def test_get_edit_with_optional_attr(self):
        user = self.admin_login()

        # making test Entry set
        entry = Entry(name="fuga", schema=self._entity, created_user=user)
        entry.save()

        self.make_attr(name="attr", created_user=user, parent_entry=entry)

        # with invalid entry-id
        resp = self.client.get(reverse("entry:edit", args=[entry.id]))
        self.assertEqual(resp.status_code, 200)

    def test_post_edit_without_login(self):
        params = {"attrs": [{"entity_attr_id": "", "id": "0", "value": [], "referral_key": []}]}
        resp = self.client.post(
            reverse("entry:do_edit", args=[0]), json.dumps(params), "application/json"
        )

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(AttributeValue.objects.count(), 0)

    def test_post_edit_with_invalid_param(self):
        user = self.admin_login()

        params = {"attrs": [{"entity_attr_id": "", "id": "0", "value": [], "referral_key": []}]}
        resp = self.client.post(
            reverse("entry:do_edit", args=[0]), json.dumps(params), "application/json"
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(AttributeValue.objects.count(), 0)

        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=user)
        params = {
            "entry_name": "changed_name",
            "attrs": [{"entity_attr_id": "", "id": "", "value": [], "referral_key": []}],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(AttributeValue.objects.count(), 0)

        params = {
            "entry_name": "hoge\thoge",
            "attrs": [],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)

    def test_post_edit_creating_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=user)
        entry.set_status(Entry.STATUS_CREATING)

        params = {"entry_name": "changed-entry"}
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.get(id=entry.id).name, "entry")

    def test_get_show_and_edit_creating_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=user)
        entry.set_status(Entry.STATUS_CREATING)

        resp = self.client.get(reverse("entry:show", args=[entry.id]))
        self.assertEqual(resp.status_code, 400)

        resp = self.client.get(reverse("entry:edit", args=[entry.id]))
        self.assertEqual(resp.status_code, 400)

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    @patch(
        "entry.tasks.notify_update_entry.delay",
        Mock(side_effect=tasks.notify_update_entry),
    )
    @patch("entry.tasks.notify_entry_update", Mock(return_value=Mock()))
    def test_post_edit_with_valid_param(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        for attr_name in ["foo", "bar"]:
            EntityAttr.objects.create(
                name=attr_name,
                type=AttrType.STRING,
                created_user=user,
                parent_entity=entity,
            )

        # making test Entry set
        entry = Entry.objects.create(name="fuga", schema=entity, created_user=user)
        entry.complement_attrs(user)

        # save time parameters to check that
        # - entry.created_time won't be changed
        # - entry.updated_time would be changed
        init_created_time = entry.created_time
        init_updated_time = entry.updated_time

        for attr in entry.attrs.all():
            attr.add_value(user, "hoge")

        # Save count of HistoricalRecord for Entry before sending request
        self._test_data["entry_history_count"] = {
            "before": entry.history.count(),
        }
        self.assertEqual(entry.history.count(), 1)

        params = {
            "entry_name": "hoge",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(Attribute.objects.get(name="foo").id),
                    "type": str(AttrType.ARRAY_STRING),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
                {
                    "entity_attr_id": "",
                    "id": str(Attribute.objects.get(name="bar").id),
                    "type": str(AttrType.ARRAY_STRING),
                    "value": [{"data": "fuga", "index": 0}],
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
        self.assertEqual(AttributeValue.objects.count(), 3)
        self.assertEqual(Attribute.objects.get(name="foo").values.count(), 1)
        self.assertEqual(Attribute.objects.get(name="bar").values.count(), 2)
        self.assertEqual(Attribute.objects.get(name="foo").values.last().value, "hoge")
        self.assertEqual(Attribute.objects.get(name="bar").values.last().value, "fuga")

        entry.refresh_from_db()
        self.assertEqual(entry.name, "hoge")
        self.assertEqual(entry.created_time, init_created_time)
        self.assertNotEqual(entry.updated_time, init_updated_time)

        # tests for historical records for Entry,
        self.assertEqual(
            entry.history.count(), self._test_data["entry_history_count"]["before"] + 1
        )

        # checks to set corrected status-flag
        foo_value_first = Attribute.objects.get(name="foo").values.first()
        bar_value_first = Attribute.objects.get(name="bar").values.first()
        bar_value_last = Attribute.objects.get(name="bar").values.last()

        self.assertTrue(foo_value_first.is_latest)
        self.assertFalse(bar_value_first.is_latest)
        self.assertTrue(bar_value_last.is_latest)

        # checks that we can search updated entry using updated value
        resp = AdvancedSearchService.search_entries(
            user, [entity.id], [AttrHint(name="bar", keyword="fuga")]
        )
        self.assertEqual(resp.ret_count, 1)
        self.assertEqual(resp.ret_values[0].entity["id"], entity.id)
        self.assertEqual(resp.ret_values[0].entry["id"], entry.id)

        # checks created jobs and its params are as expected
        jobs = Job.objects.filter(user=user, target=entry)
        job_expectations = [
            {
                "operation": JobOperation.EDIT_ENTRY,
                "status": JobStatus.DONE,
                "dependent_job": None,
            },
            {
                "operation": JobOperation.REGISTER_REFERRALS,
                "status": JobStatus.PREPARING,
                "dependent_job": None,
            },
            {
                "operation": JobOperation.NOTIFY_UPDATE_ENTRY,
                "status": JobStatus.DONE,
                "dependent_job": None,
            },
            {
                "operation": JobOperation.MAY_INVOKE_TRIGGER,
                "status": JobStatus.PREPARING,
                "dependent_job": jobs.get(operation=JobOperation.EDIT_ENTRY),
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
        params = {
            "entry_name": "foo",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(Attribute.objects.get(name="foo").id),
                    "value": [{"data": "puyo", "index": 0}],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        entry.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(entry.attrs.get(name="foo").get_latest_value().value, "puyo")
        self.assertEqual(entry.attrs.get(name="bar").get_latest_value().value, "fuga")

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_with_optional_params(self):
        user = self.admin_login()

        # making test Entry set
        entry = Entry(name="fuga", schema=self._entity, created_user=user)
        entry.save()

        for attr_name in ["foo", "bar", "baz"]:
            self.make_attr(name=attr_name, created_user=user, parent_entry=entry)

        params = {
            "entry_name": entry.name,
            "attrs": [
                # include blank value
                {
                    "entity_attr_id": "",
                    "id": str(Attribute.objects.get(name="foo").id),
                    "type": str(AttrType.ARRAY_STRING),
                    "value": [{"data": "", "index": 0}],
                    "referral_key": [],
                },
                {
                    "entity_attr_id": "",
                    "id": str(Attribute.objects.get(name="bar").id),
                    "type": str(AttrType.ARRAY_STRING),
                    "value": [{"data": "fuga", "index": 0}],
                    "referral_key": [],
                },
                {
                    "entity_attr_id": "",
                    "id": str(Attribute.objects.get(name="baz").id),
                    "type": str(AttrType.ARRAY_STRING),
                    "value": [{"data": "0", "index": 0}],
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
        self.assertEqual(Attribute.objects.get(name="foo").values.filter(is_latest=True).count(), 1)
        self.assertEqual(Attribute.objects.get(name="foo").values.last().value, "")
        self.assertEqual(Attribute.objects.get(name="bar").values.filter(is_latest=True).count(), 1)
        self.assertEqual(Attribute.objects.get(name="bar").values.last().value, "fuga")
        self.assertEqual(Attribute.objects.get(name="baz").values.filter(is_latest=True).count(), 1)
        self.assertEqual(Attribute.objects.get(name="baz").values.last().value, "0")
        self.assertEqual(Entry.objects.get(id=entry.id).name, entry.name)

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_with_array_string_value(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        EntityAttr.objects.create(
            **{
                "name": "attr",
                "type": AttrType.ARRAY_STRING,
                "created_user": user,
                "parent_entity": entity,
            }
        )

        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        entry.complement_attrs(user)
        attr = entry.attrs.first()
        attr.add_value(
            user,
            [
                {"name": "hoge", "id": ""},
                {"name": "fuga", "id": ""},
            ],
        )

        parent_values_count = AttributeValue.objects.extra(
            **{"where": ["status & %s = 1" % AttributeValue.STATUS_DATA_ARRAY_PARENT]}
        ).count()

        params = {
            "entry_name": entry.name,
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(attr.id),
                    "type": str(attr.schema.type),
                    "value": [
                        {"data": "hoge", "index": 0},
                        {"data": "puyo", "index": 1},
                    ],
                    "referral_key": [],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)

        # checks to set correct status flags
        leaf_values = [
            x
            for x in AttributeValue.objects.all()
            if not x.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
        ]

        parent_values = [
            x
            for x in AttributeValue.objects.all()
            if x.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
        ]
        self.assertEqual(len(leaf_values), 4)
        self.assertEqual(len(parent_values), parent_values_count + 1)

        self.assertEqual(attr.values.count(), parent_values_count + 1)
        self.assertTrue(attr.values.last().status & AttributeValue.STATUS_DATA_ARRAY_PARENT)

        self.assertEqual(attr.values.last().data_array.count(), 2)
        self.assertTrue(
            all([x.value in ["hoge", "puyo"] for x in attr.values.last().data_array.all()])
        )

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_show_and_post_edit_with_array_object_value(self):
        user = self.admin_login()

        # This create referral Entries (e0, e1 and e2).
        # Initially the e0 and e1 are registered at the "attr" of "entry" out of those.
        # Then, this test send a request to edit the "entry" to change referral Entries
        # at the "attr" to e1 and e2.
        ref_entity = self.create_entity(user, "RefEntity")
        ref_entries = [self.add_entry(user, "e%s" % i, ref_entity) for i in range(4)]

        entity = self.create_entity(
            user,
            "Entity",
            attrs=[{"name": "attr", "type": AttrType.ARRAY_NAMED_OBJECT, "ref": ref_entity}],
        )
        entry = self.add_entry(
            user,
            "entry",
            entity,
            values={
                "attr": [
                    {"name": "hoge", "id": ref_entries[0]},
                    {"name": "fuga", "id": ref_entries[3]},
                ]
            },
        )
        attr = entry.attrs.last()

        # This represents to prevent showing AttributeValue that refers deleted Entry
        ref_entries[3].delete()
        resp = self.client.get(reverse("entry:edit", args=[entry.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            [x["last_value"] for x in resp.context["attributes"] if x["id"] == attr.id][0],
            [{"value": "hoge", "id": ref_entries[0].id, "name": ref_entries[0].name}],
        )

        parent_values_count = AttributeValue.objects.extra(
            **{"where": ["status & %s = 1" % AttributeValue.STATUS_DATA_ARRAY_PARENT]}
        ).count()

        params = {
            "entry_name": entry.name,
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(attr.id),
                    "type": str(AttrType.ARRAY_OBJECT),
                    "value": [
                        {"data": ref_entries[1].id, "index": 0},
                        {"data": ref_entries[2].id, "index": 1},
                    ],
                    "referral_key": [],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # check es-documents of both e0 (was referred before) and e2 (is referred now)
        ret = AdvancedSearchService.search_entries(
            user,
            [ref_entity.id],
            hint_referral="",
        )
        self.assertEqual(ret.ret_count, 3)
        for info in ret.ret_values:
            if info.entry["id"] == ref_entries[0].id:
                self.assertEqual(info.referrals, [])
            elif info.entry["id"] == ref_entries[1].id or info.entry["id"] == ref_entries[2].id:
                self.assertEqual(
                    info.referrals,
                    [
                        {
                            "id": entry.id,
                            "name": entry.name,
                            "schema": {"id": entity.id, "name": entity.name},
                        }
                    ],
                )
            else:
                raise RuntimeError("Unexpected es-document was returned")

        # checks to set correct status flags
        leaf_values = [
            x
            for x in AttributeValue.objects.all()
            if not x.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
        ]

        parent_values = [
            x
            for x in AttributeValue.objects.all()
            if x.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
        ]
        self.assertEqual(len(leaf_values), 4)
        self.assertEqual(len(parent_values), parent_values_count + 1)
        self.assertEqual(attr.values.count(), parent_values_count + 1)
        self.assertTrue(attr.values.last().status & AttributeValue.STATUS_DATA_ARRAY_PARENT)

        self.assertEqual(attr.values.last().data_array.count(), 2)
        self.assertTrue(
            all(
                [
                    x.referral.id in [ref_entries[1].id, ref_entries[2].id]
                    for x in attr.values.last().data_array.all()
                ]
            )
        )

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
            attr = self.make_attr(name=attr_name, created_user=user, parent_entry=entry)

            for value in ["hoge", "fuga"]:
                attr_value = AttributeValue(value=value, created_user=user, parent_attr=attr)
                attr_value.save()

                attr.values.add(attr_value)

        resp = self.client.get(reverse("entry:show", args=[entry.id]))
        self.assertEqual(resp.status_code, 200)

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_with_referral(self):
        user = self.admin_login()

        attr_base = EntityAttr.objects.create(
            name="attr_with_referral",
            created_user=user,
            type=AttrType.OBJECT,
            parent_entity=self._entity,
            is_mandatory=False,
        )
        attr_base.referral.add(self._entity)

        entry = Entry.objects.create(name="old_entry", schema=self._entity, created_user=user)

        attr = entry.add_attribute_from_base(attr_base, user)
        attr_value = AttributeValue.objects.create(
            referral=entry, created_user=user, parent_attr=attr
        )
        attr.values.add(attr_value)

        new_entry = Entry.objects.create(name="new_entry", schema=self._entity, created_user=user)

        params = {
            "entry_name": "old_entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(attr.id),
                    "type": str(AttrType.OBJECT),
                    "value": [{"data": str(new_entry.id), "index": 0}],
                    "referral_key": [],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(entry.attrs.last().values.count(), 2)
        self.assertEqual(entry.attrs.last().values.first().value, "")
        self.assertEqual(entry.attrs.last().values.first().referral.id, entry.id)
        self.assertEqual(entry.attrs.last().values.last().value, "")
        self.assertEqual(entry.attrs.last().values.last().referral.id, new_entry.id)

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_without_referral_value(self):
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

        attr = entry.add_attribute_from_base(attr_base, user)
        attr_value = AttributeValue.objects.create(
            referral=entry, created_user=user, parent_attr=attr
        )
        attr.values.add(attr_value)

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(attr.id),
                    "type": str(AttrType.OBJECT),
                    "value": [{"data": "0", "index": 0}],
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
        self.assertEqual(attr.values.count(), 2)
        self.assertEqual(attr.values.last().value, "")

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_to_no_referral(self):
        user = self.admin_login()

        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=user)

        attr = self.make_attr(
            name="attr", attrtype=AttrType.OBJECT, created_user=user, parent_entry=entry
        )

        attr_value = AttributeValue.objects.create(
            referral=entry, created_user=user, parent_attr=attr
        )
        attr.values.add(attr_value)

        params = {
            "entry_name": entry.name,
            "attrs": [
                # include blank value
                {
                    "entity_attr_id": "",
                    "id": str(attr.id),
                    "type": str(AttrType.OBJECT),
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
        self.assertEqual(attr.values.count(), 2)
        self.assertEqual(attr.values.first(), attr_value)
        self.assertIsNone(attr.values.last().referral)

    @patch("entry.tasks.export_entries.delay", Mock(side_effect=tasks.export_entries))
    def test_post_export(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="ほげ", created_user=user)
        for name in ["foo", "bar"]:
            EntityAttr.objects.create(
                **{
                    "name": name,
                    "type": AttrType.STRING,
                    "created_user": user,
                    "parent_entity": entity,
                }
            )

        entry = Entry.objects.create(name="fuga", schema=entity, created_user=user)
        entry.complement_attrs(user)
        for attr in entry.attrs.all():
            [attr.add_value(user, x) for x in ["hoge", "fuga"]]

        resp = self.client.post(
            reverse("entry:export", args=[entity.id]),
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {"result": "Succeed in registering export processing. Please check Job list."},
        )

        job = Job.objects.last()
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY)
        self.assertEqual(job.status, JobStatus.DONE)
        self.assertEqual(job.text, "entry_ほげ.yaml")

        obj = yaml.load(job.get_cache(), Loader=yaml.SafeLoader)
        self.assertTrue(entity.name in obj)

        self.assertEqual(len(obj[entity.name]), 1)
        entry_data = obj[entity.name][0]
        self.assertTrue(all(["name" in entry_data and "attrs" in entry_data]))

        self.assertEqual(entry_data["name"], entry.name)
        self.assertEqual(len(entry_data["attrs"]), entry.attrs.count())
        self.assertEqual(entry_data["attrs"]["foo"], "fuga")
        self.assertEqual(entry_data["attrs"]["bar"], "fuga")

        resp = self.client.post(
            reverse("entry:export", args=[entity.id]),
            json.dumps({"format": "CSV"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # append an unpermitted Attribute
        EntityAttr.objects.create(
            **{
                "name": "new_attr",
                "type": AttrType.STRING,
                "created_user": user,
                "parent_entity": entity,
                "is_public": False,
            }
        )

        # re-login with guest user
        user = self.guest_login()

        resp = self.client.post(
            reverse("entry:export", args=[entity.id]),
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        obj = yaml.load(Job.objects.last().get_cache(), Loader=yaml.SafeLoader)

        # check permitted attributes exist in the result
        self.assertTrue(all([x in obj["ほげ"][0]["attrs"] for x in ["foo", "bar"]]))

        # check unpermitted attribute doesn't exist in the result
        self.assertFalse("new_attr" in obj["ほげ"][0]["attrs"])

        ###
        # Check the case of canceling job
        ###
        with patch.object(Job, "is_canceled", return_value=True):
            resp = self.client.post(
                reverse("entry:export", args=[entity.id]),
                json.dumps({}),
                "application/json",
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {"result": "Succeed in registering export processing. Please check Job list."},
        )

        job = Job.objects.last()
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY)
        self.assertEqual(job.text, "entry_ほげ.yaml")
        with self.assertRaises(OSError) as e:
            raise OSError

        if e.exception.errno == errno.ENOENT:
            job.get_cache()

    @patch("entry.tasks.export_entries.delay", Mock(side_effect=tasks.export_entries))
    def test_get_export_csv_escape(self):
        user = self.admin_login()

        dummy_entity = Entity.objects.create(name="Dummy", created_user=user)
        dummy_entry = Entry(name='D,U"MM"Y', schema=dummy_entity, created_user=user)
        dummy_entry.save()

        CASES = [
            [AttrType.STRING, 'raison,de"tre', '"raison,de""tre"'],
            [AttrType.OBJECT, dummy_entry, '"D,U""MM""Y"'],
            [AttrType.TEXT, "1st line\r\n2nd line", '"1st line' + "\r\n" + '2nd line"'],
            [AttrType.NAMED_OBJECT, {"key": dummy_entry}, '"{\'key\': \'D,U""MM""Y\'}"'],
            [AttrType.ARRAY_STRING, ["one", "two", "three"], "\"['one', 'two', 'three']\""],
            [AttrType.ARRAY_OBJECT, [dummy_entry], '"[\'D,U""MM""Y\']"'],
            [
                AttrType.ARRAY_NAMED_OBJECT,
                [{"key1": dummy_entry}],
                '"[{\'key1\': \'D,U""MM""Y\'}]"',
            ],
        ]

        for type, value, expected in CASES:
            type_name = type.name
            attr_name = type_name + ',"ATTR"'

            test_entity = Entity.objects.create(name="TestEntity_" + type_name, created_user=user)

            test_entity_attr = EntityAttr.objects.create(
                name=attr_name,
                type=type,
                created_user=user,
                parent_entity=test_entity,
            )

            test_entry = Entry.objects.create(
                name=type_name + ',"ENTRY"', schema=test_entity, created_user=user
            )
            test_entry.save()

            test_attr = Attribute.objects.create(
                name=attr_name,
                schema=test_entity_attr,
                created_user=user,
                parent_entry=test_entry,
            )

            test_val = None

            if type & AttrType._ARRAY == 0:
                match type:
                    case AttrType.STRING:
                        test_val = AttributeValue.create(user=user, attr=test_attr, value=value)
                    case AttrType.OBJECT:
                        test_val = AttributeValue.create(user=user, attr=test_attr, referral=value)
                    case AttrType.TEXT:
                        test_val = AttributeValue.create(user=user, attr=test_attr, value=value)
                    case AttrType.NAMED_OBJECT:
                        [(k, v)] = value.items()
                        test_val = AttributeValue.create(
                            user=user, attr=test_attr, value=k, referral=v
                        )
            else:
                test_val = AttributeValue.create(user=user, attr=test_attr)
                test_val.set_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
                for child in value:
                    match type:
                        case AttrType.ARRAY_STRING:
                            AttributeValue.create(
                                user=user, attr=test_attr, value=child, parent_attrv=test_val
                            )
                        case AttrType.ARRAY_OBJECT:
                            AttributeValue.create(
                                user=user, attr=test_attr, referral=child, parent_attrv=test_val
                            )
                        case AttrType.ARRAY_NAMED_OBJECT:
                            [(k, v)] = child.items()
                            AttributeValue.create(
                                user=user,
                                attr=test_attr,
                                value=k,
                                referral=v,
                                parent_attrv=test_val,
                            )

            test_val.save()
            test_attr.values.add(test_val)
            test_attr.save()

            resp = self.client.post(
                reverse("entry:export", args=[test_entity.id]),
                json.dumps({"format": "CSV"}),
                "application/json",
            )
            self.assertEqual(resp.status_code, 200)

            content = Job.objects.last().get_cache()
            header = content.splitlines()[0]
            self.assertEqual(header, 'Name,"%s,""ATTR"""' % type_name)

            data = content.replace(header, "", 1).strip()
            self.assertEqual(data, '"%s,""ENTRY""",' % type_name + expected)

    @patch("entry.tasks.delete_entry.delay", Mock(side_effect=tasks.delete_entry))
    @patch(
        "entry.tasks.notify_delete_entry.delay",
        Mock(side_effect=tasks.notify_delete_entry),
    )
    @patch("entry.tasks.notify_entry_delete", Mock(return_value=Mock()))
    def test_post_delete_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name="fuga", schema=self._entity, created_user=user)
        self.make_attr(name="attr-test", parent_entry=entry, created_user=user)

        entry_count = Entry.objects.count()

        # Save count of HistoricalRecord for EntityAttr before sending request
        self._test_data["entry_history_count"] = {
            "before": entry.history.count(),
        }
        self.assertEqual(entry.history.count(), 1)

        resp = self.client.post(
            reverse("entry:do_delete", args=[entry.id]),
            json.dumps({}),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Entry.objects.count(), entry_count)

        # tests for historical records for Entry
        self.assertEqual(
            entry.history.count(),
            self._test_data["entry_history_count"]["before"] + 1,
        )

        # checks created jobs and its params are as expected
        jobs = Job.objects.filter(user=user, target=entry)
        job_expectations = [
            {
                "operation": JobOperation.DELETE_ENTRY,
                "status": JobStatus.DONE,
                "dependent_job": jobs.get(operation=JobOperation.NOTIFY_DELETE_ENTRY),
            },
            {
                "operation": JobOperation.NOTIFY_DELETE_ENTRY,
                "status": JobStatus.DONE,
                "dependent_job": None,
            },
        ]
        self.assertEqual(jobs.count(), len(job_expectations))
        for expectation in job_expectations:
            obj = jobs.get(operation=expectation["operation"].value)
            self.assertEqual(obj.target.id, entry.id)
            self.assertEqual(obj.target_type, JobTarget.ENTRY)
            self.assertEqual(obj.status, expectation["status"])
            self.assertEqual(obj.dependent_job, expectation["dependent_job"])

        entry = Entry.objects.last()
        self.assertFalse(entry.is_active)
        self.assertFalse(Attribute.objects.get(name__icontains="attr-test_deleted_").is_active)

        # Checks Elasticsearch also removes document of removed entry
        res = self._es.get(
            index=settings.ES_CONFIG["INDEX_NAME"],
            id=entry.id,
            ignore=[404],
        )
        self.assertFalse(res["found"])

    @patch("entry.tasks.delete_entry.delay", Mock(return_value=None))
    def test_post_delete_entry_with_long_delay(self):
        # This is the case when background processing never be started
        user = self.guest_login()

        # Create an entry to be deleted
        entity = Entity.objects.create(name="Entity", created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        # Send a request to delete an entry
        resp = self.client.post(
            reverse("entry:do_delete", args=[entry.id]),
            json.dumps({}),
            "application/json",
        )

        # Check that deleted entry's active flag is down
        entry.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(entry.is_active)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_permission_check_for_delete_request(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="test-entity", created_user=user)

        TEST_PARAMS_SET = [
            {"permission": ACLType.Nothing.id, "expected_response_code": 400, "is_active": True},
            {"permission": ACLType.Readable.id, "expected_response_code": 400, "is_active": True},
            {"permission": ACLType.Writable.id, "expected_response_code": 200, "is_active": False},
            {"permission": ACLType.Full.id, "expected_response_code": 200, "is_active": False},
        ]
        for index, test_params in enumerate(TEST_PARAMS_SET):
            entry = Entry.objects.create(
                name="test-entry-%d" % index,
                schema=entity,
                created_user=user,
                is_public=False,
                default_permission=test_params["permission"],
            )
            resp = self.client.post(
                reverse("entry:do_delete", args=[entry.id]),
                json.dumps({}),
                "application/json",
            )

            entry.refresh_from_db()
            self.assertEqual(resp.status_code, test_params["expected_response_code"])
            self.assertEqual(entry.is_active, test_params["is_active"])

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

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_edit_entry_with_role_attributes(self):
        user = self.guest_login()
        role = Role.objects.create(name="TestRole")

        # initialize Entity which has Role related Attributes
        # and create Entry which is associated with that Entity
        entity = self.create_entity(
            user,
            "Entity",
            attrs=[
                {"name": "Role", "type": AttrType.ROLE},
                {"name": "RoleArray", "type": AttrType.ARRAY_ROLE},
            ],
        )
        entry = self.add_entry(user, "TestEntry", entity)

        # initialize parameters that will be sent to AirOne to edit Entry
        sending_params = {"entry_name": "entry", "attrs": []}
        for attrname, value in [
            ("Role", [{"data": str(role.id), "index": 0}]),
            ("RoleArray", [{"data": str(role.id), "index": 0}]),
        ]:
            attr = entry.attrs.get(schema__name=attrname, is_active=True)
            sending_params["attrs"].append(
                {
                    "entity_attr_id": str(attr.schema.id),
                    "id": str(attr.id),
                    "value": value,
                    "referral_key": [],
                }
            )

        # sending a request to edit specified Entry and
        # confirme updated Entry has expected Attribute values
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(sending_params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        updatedEntry = Entry.objects.get(id=resp.json().get("entry_id"))
        self.assertFalse(updatedEntry.attrs.get(schema__name="Role").is_updated(role))
        self.assertFalse(updatedEntry.attrs.get(schema__name="RoleArray").is_updated([role]))

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    @patch(
        "trigger.tasks.may_invoke_trigger.delay",
        Mock(side_effect=trigger_tasks.may_invoke_trigger),
    )
    def test_edit_entry_with_trigger_configuration(self):
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
        entry = self.add_entry(user, "Jhon Doe", entity)

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

        # send request for editing Entry to invoke TriggerAction
        sending_params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": str(entity.attrs.get(name="address").id),
                    "id": str(entry.attrs.get(schema__name="address").id),
                    "value": [{"data": "", "index": 0}],
                    "referral_key": [{"data": "unknown", "index": 0}],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(sending_params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # check trigger action was worked properly
        job_query = Job.objects.filter(operation=JobOperation.MAY_INVOKE_TRIGGER)
        self.assertEqual(job_query.count(), 1)
        self.assertEqual(job_query.first().status, JobStatus.DONE.value)

        # check updated Entry's attributes are set properly by TriggerAction
        self.assertEqual(resp.json().get("entry_id"), entry.id)
        self.assertEqual(entry.get_attrv("age").value, "0")
        self.assertEqual(entry.get_attrv("address").value, "Chiyoda ward")
        self.assertEqual(entry.get_attrv("address").referral.id, pref_info["tokyo"].id)

    def test_edit_when_another_same_named_alias_exists(self):
        user = self.guest_login()

        # create Model, Item and Alias that is same name with updating Item in this test
        model = self.create_entity(user, "Mountain")
        item = self.add_entry(user, "Everest", model)
        item.add_alias("Chomolungma")

        resp = self.client.post(
            reverse("entry:do_edit", args=[item.id]),
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

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_just_limit_of_value(self):
        user = self.admin_login()

        entry = Entry.objects.create(name="entry", created_user=user, schema=self._entity)
        attr = entry.add_attribute_from_base(self._entity_attr, user)

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(attr.id),
                    "type": str(AttrType.STRING),
                    "value": [{"data": "A" * AttributeValue.MAXIMUM_VALUE_SIZE, "index": 0}],
                    "referral_key": [],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AttributeValue.objects.filter(parent_attr=attr, is_latest=True).count(), 1)
        self.assertEqual(len(attr.values.last().value), AttributeValue.MAXIMUM_VALUE_SIZE)

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

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_post_edit_exceeding_limit_of_value(self):
        user = self.admin_login()

        entry = Entry.objects.create(name="entry", created_user=user, schema=self._entity)
        attr = entry.add_attribute_from_base(self._entity_attr, user)

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(attr.id),
                    "type": str(AttrType.STRING),
                    "value": [
                        {
                            "data": "A" * AttributeValue.MAXIMUM_VALUE_SIZE + "A",
                            "index": 0,
                        }
                    ],
                    "referral_key": [],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(attr.values.count(), 0)

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

    def test_try_to_edit_duplicate_name_of_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name="entry", created_user=user, schema=self._entity)
        entry.add_attribute_from_base(self._entity_attr, user)

        dup_entry = Entry.objects.create(name="dup_entry", created_user=user, schema=self._entity)
        dup_attr = Attribute.objects.create(
            name=self._entity_attr.name,
            schema=self._entity_attr,
            created_user=user,
            parent_entry=dup_entry,
        )

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(dup_attr.id),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[dup_entry.id]),
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

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_create_and_edit_entry_that_has_boolean_attr(self):
        admin = self.admin_login()

        entity = Entity.objects.create(name="entity", created_user=admin)
        entity_attr = EntityAttr.objects.create(
            name="attr_bool",
            type=AttrType.BOOLEAN,
            parent_entity=entity,
            created_user=admin,
        )

        # creates entry that has a parameter which is typed boolean
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(entity_attr.id),
                    "type": str(AttrType.BOOLEAN),
                    "value": [{"data": True, "index": 0}],
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

        # get entry which is created in here
        entry = Entry.objects.get(name="entry", schema=entity)

        self.assertEqual(entry.attrs.count(), 1)
        self.assertIsNotNone(entry.attrs.last().get_latest_value())
        self.assertTrue(entry.attrs.last().get_latest_value().boolean)

        # edit entry to update the value of attribute 'attr_bool'
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(name="attr_bool").id),
                    "type": str(AttrType.BOOLEAN),
                    "value": [{"data": False, "index": 0}],
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

        # checks AttributeValue which is specified to update
        self.assertEqual(entry.attrs.last().values.count(), 2)
        self.assertFalse(entry.attrs.last().get_latest_value().boolean)

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

    def test_post_edit_entry_without_mandatory_param(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="Entity", is_public=False, created_user=user)
        EntityAttr.objects.create(
            name="attr",
            type=AttrType.STRING,
            is_mandatory=True,
            parent_entity=entity,
            created_user=user,
        )

        entry = Entry.objects.create(name="Entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        params = {
            "entry_name": "Updated Entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(name="attr").id),
                    "type": str(AttrType.STRING),
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

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Entry.objects.get(id=entry.id).name, "Entry")

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

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_edit_entry_with_named_ref(self):
        user = self.admin_login()

        ref_entity = Entity.objects.create(name="referred_entity", created_user=user)
        ref_entry = Entry.objects.create(
            name="referred_entry", created_user=user, schema=ref_entity
        )

        entity = Entity.objects.create(name="entity", created_user=user)

        attr_base = EntityAttr.objects.create(
            **{
                "name": "named_ref",
                "type": AttrType.NAMED_OBJECT,
                "created_user": user,
                "parent_entity": entity,
            }
        )
        attr_base.referral.add(ref_entity)

        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        entry.complement_attrs(user)

        attr = entry.attrs.get(name="named_ref")
        attr.add_value(user, {"id": ref_entry, "name": "hoge"})

        # try to update with same data (expected not to be updated)
        params = {
            "entry_name": "updated_entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(name="named_ref").id),
                    "type": str(AttrType.NAMED_OBJECT),
                    "value": [{"data": str(ref_entry.id), "index": 0}],
                    "referral_key": [{"data": "hoge", "index": 0}],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        updated_entry = Entry.objects.get(id=entry.id)
        self.assertEqual(updated_entry.name, "updated_entry")
        self.assertEqual(updated_entry.attrs.get(name="named_ref").values.count(), 1)

        # try to update with different data (expected to be updated)
        ref_entry2 = Entry.objects.create(
            name="referred_entry2", created_user=user, schema=ref_entity
        )
        params = {
            "entry_name": "updated_entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(name="named_ref").id),
                    "type": str(AttrType.NAMED_OBJECT),
                    "value": [{"data": str(ref_entry2.id), "index": 0}],
                    "referral_key": [{"data": "fuga", "index": 0}],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        updated_entry = Entry.objects.get(id=entry.id)
        self.assertEqual(updated_entry.attrs.get(name="named_ref").values.count(), 2)
        self.assertEqual(updated_entry.attrs.get(name="named_ref").values.last().value, "fuga")
        self.assertEqual(
            updated_entry.attrs.get(name="named_ref").values.last().referral.id,
            ref_entry2.id,
        )

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_edit_entry_with_array_named_ref(self):
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

        # create an Entry associated to the 'entity'
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        entry.complement_attrs(user)

        attr = entry.attrs.get(name="arr_named_ref")
        self.assertTrue(attr.is_updated([{"id": ref_entry.id}]))

        attrv = attr.add_value(
            user,
            [
                {
                    "name": "key_%d" % i,
                    "id": Entry.objects.create(
                        name="r_%d" % i, created_user=user, schema=ref_entity
                    ),
                }
                for i in range(3)
            ],
        )

        # try to update with same data (expected not to be updated)
        old_attrv_count = attr.values.count()
        r_entries = [x.referral.id for x in attrv.data_array.all()]
        params = {
            "entry_name": "updated_entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(name="arr_named_ref").id),
                    "type": str(AttrType.ARRAY_NAMED_OBJECT),
                    "value": [{"data": str(r), "index": i} for i, r in enumerate(r_entries)],
                    "referral_key": [{"data": "key_%d" % i, "index": i} for i in range(0, 3)],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        updated_entry = Entry.objects.get(id=entry.id)
        self.assertEqual(updated_entry.name, "updated_entry")
        self.assertEqual(
            updated_entry.attrs.get(name="arr_named_ref").values.count(),
            old_attrv_count,
        )

        # try to update with different data (expected to be updated)
        params = {
            "entry_name": "updated_entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(name="arr_named_ref").id),
                    "type": str(AttrType.ARRAY_NAMED_OBJECT),
                    "value": [
                        {"data": r_entries[1], "index": 1},
                        {"data": r_entries[2], "index": 2},
                    ],
                    "referral_key": [{"data": "hoge_%d" % i, "index": i} for i in range(0, 2)],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        updated_entry = Entry.objects.get(id=entry.id)
        self.assertEqual(
            updated_entry.attrs.get(name="arr_named_ref").values.count(),
            old_attrv_count + 1,
        )

        new_attrv = updated_entry.attrs.get(name="arr_named_ref").values.last()
        self.assertEqual(new_attrv.data_array.count(), 3)

        contexts = [
            {
                "name": x.value,
                "referral": x.referral.id if x.referral else None,
            }
            for x in new_attrv.data_array.all()
        ]

        self.assertTrue({"name": "hoge_0", "referral": None} in contexts)
        self.assertTrue({"name": "hoge_1", "referral": r_entries[1]} in contexts)
        self.assertTrue({"name": "", "referral": r_entries[2]} in contexts)

        # try to update with same data but order is different (expected not to be updated)
        params = {
            "entry_name": "updated_entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(name="arr_named_ref").id),
                    "type": str(AttrType.ARRAY_NAMED_OBJECT),
                    "value": [
                        {"data": r_entries[2], "index": 2},
                        {"data": r_entries[1], "index": 1},
                    ],
                    "referral_key": [
                        {"data": "hoge_1", "index": 1},
                        {"data": "hoge_0", "index": 0},
                    ],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        updated_entry = Entry.objects.get(id=entry.id)
        self.assertEqual(
            updated_entry.attrs.get(name="arr_named_ref").values.count(),
            old_attrv_count + 1,
        )

    def test_get_copy_with_invalid_entry(self):
        self.admin_login()

        resp = self.client.get(reverse("entry:index", args=[9999]))
        self.assertEqual(resp.status_code, 400)

    def test_get_copy_with_valid_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name="entry", created_user=user, schema=self._entity)

        resp = self.client.get(reverse("entry:copy", args=[entry.id]))
        self.assertEqual(resp.status_code, 200)

    def test_post_copy_without_mandatory_parameter(self):
        user = self.admin_login()

        entry = Entry.objects.create(name="entry", created_user=user, schema=self._entity)

        resp = self.client.post(
            reverse("entry:do_copy", args=[entry.id]),
            json.dumps({}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_post_copy_with_invalid_entry(self):
        self.admin_login()

        params = {
            "entries": "foo\nbar\nbaz",
        }
        resp = self.client.post(
            reverse("entry:do_copy", args=[9999]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)

    @patch("entry.tasks.copy_entry.delay", Mock(side_effect=tasks.copy_entry))
    def test_permission_check_for_copy_request(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="test-entity", created_user=user)
        entry = Entry.objects.create(
            name="test-entry", created_user=user, schema=entity, is_public=False
        )
        entry.complement_attrs(user)

        TEST_PARAMS_SET = [
            {"set_permission": ACLType.Nothing.id, "expected_response_code": 400},
            {"set_permission": ACLType.Readable.id, "expected_response_code": 400},
            {"set_permission": ACLType.Writable.id, "expected_response_code": 200},
            {"set_permission": ACLType.Full.id, "expected_response_code": 200},
        ]
        for test_params in TEST_PARAMS_SET:
            entry.default_permission = test_params["set_permission"]
            entry.save()

            resp = self.client.post(
                reverse("entry:do_copy", args=[entry.id]),
                json.dumps({"entries": "copy-test-entry"}),
                "application/json",
            )
            self.assertEqual(resp.status_code, test_params["expected_response_code"])

            # remove copied Entry which might be created not to other loop
            copied_entry = Entry.objects.filter(name="copy-test-entry", is_active=True).last()
            if copied_entry is not None:
                copied_entry.delete()

    @patch("entry.tasks.copy_entry.delay", Mock(side_effect=tasks.copy_entry))
    def test_copy_when_duplicated_named_alias_exists(self):
        user = self.admin_login()

        model = self.create_entity(user, "Mountain")
        item_src = Entry.objects.create(name="Everest", created_user=user, schema=model)
        item_src.add_alias("Chomolungma")

        resp = self.client.post(
            reverse("entry:do_copy", args=[item_src.id]),
            json.dumps(
                {
                    # Chomolungma is duplicated with Alias of Everest
                    "entries": "Mt.Fuji\nK2\nChomolungma",
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # check Chomolungma copy job was failed
        copy_job = Job.objects.filter(user=user, operation=JobOperation.COPY_ENTRY).first()
        self.assertEqual(copy_job.text, "Copy completed [%5d/%5d]" % (3, 3))
        self.assertEqual(copy_job.target.entry, item_src)
        self.assertEqual(copy_job.status, JobStatus.DONE)

        # check Job of COPY has expected attributes
        do_copy_jobs = Job.objects.filter(user=user, operation=JobOperation.DO_COPY_ENTRY)
        self.assertEqual(do_copy_jobs.count(), 3)

        EXPECTED_PARAMS = [
            ("Mt.Fuji", JobStatus.DONE, "original entry: Everest"),
            ("K2", JobStatus.DONE, "original entry: Everest"),
            (
                "Chomolungma",
                JobStatus.ERROR,
                "Duplicated Alias(name=Chomolungma) exists in this model",
            ),
        ]
        for index, (name, status, text) in enumerate(EXPECTED_PARAMS):
            job = do_copy_jobs[index]
            self.assertEqual(json.loads(job.params)["new_name"], name)
            self.assertEqual(job.status, status)
            self.assertEqual(job.text, text)

    @patch("entry.tasks.copy_entry.delay", Mock(side_effect=tasks.copy_entry))
    def test_post_copy_with_valid_entry(self):
        user = self.admin_login()

        entry = Entry.objects.create(name="entry", created_user=user, schema=self._entity)
        entry.complement_attrs(user)

        entry_count = Entry.objects.filter(schema=self._entity).count()

        params = {
            # 'foo' is duplicated and 'entry' is already created
            "entries": "foo\nbar\nbaz\nfoo\nentry",
        }
        resp = self.client.post(
            reverse("entry:do_copy", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertTrue("results" in resp.json())

        self.assertEqual(Entry.objects.filter(schema=self._entity).count(), entry_count + 3)
        for name in ["foo", "bar", "baz"]:
            self.assertEqual(Entry.objects.filter(name=name, schema=self._entity).count(), 1)

        results = resp.json()["results"]
        self.assertEqual(len(results), 5)
        self.assertEqual(len([x for x in results if x["status"] == "fail"]), 2)
        self.assertEqual(len([x for x in results if x["status"] == "success"]), 3)

        # checks copied entries were registered to the Elasticsearch
        res = AdvancedSearchService.get_all_es_docs()
        self.assertEqual(res["hits"]["total"]["value"], 3)

        # checks jobs were created as expected
        copy_job = Job.objects.filter(user=user, operation=JobOperation.COPY_ENTRY).first()
        self.assertEqual(copy_job.text, "Copy completed [%5d/%5d]" % (3, 3))
        self.assertEqual(copy_job.target.entry, entry)
        self.assertEqual(copy_job.status, JobStatus.DONE)

        do_copy_jobs = Job.objects.filter(user=user, operation=JobOperation.DO_COPY_ENTRY)
        self.assertEqual(do_copy_jobs.count(), 3)
        for obj in do_copy_jobs.all():
            self.assertTrue(any([obj.target.name == x for x in ["foo", "bar", "baz"]]))
            self.assertEqual(obj.text, "original entry: %s" % entry.name)
            self.assertEqual(obj.target_type, JobTarget.ENTRY)
            self.assertEqual(obj.status, JobStatus.DONE)
            self.assertNotEqual(obj.created_at, obj.updated_at)
            self.assertTrue((obj.updated_at - obj.created_at).total_seconds() > 0)

        # check notification jobs were create in the copy entry's processing
        notify_jobs = Job.objects.filter(
            operation=JobOperation.NOTIFY_CREATE_ENTRY,
            status=JobStatus.PREPARING,
            user=user,
        )
        self.assertEqual(notify_jobs.count(), do_copy_jobs.count())

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

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_edit_entry_with_group_attr(self):
        admin = self.admin_login()

        for index in range(0, 10):
            group = Group.objects.create(name="group-%d" % (index))
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

        entry = Entry.objects.create(name="entry", schema=entity, created_user=admin)
        entry.complement_attrs(admin)

        attr = entry.attrs.first()
        attr.add_value(admin, str(Group.objects.get(name="group-0").id))

        # Specify a value which is same with the latest one, then AirOne do not update it.
        attrv_count = AttributeValue.objects.count()
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(attr.id),
                    "type": str(AttrType.GROUP),
                    "value": [{"index": 0, "data": str(Group.objects.get(name="group-0").id)}],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AttributeValue.objects.count(), attrv_count)

        # Specify a different value to add a new AttributeValue
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(attr.id),
                    "type": str(AttrType.GROUP),
                    "value": [{"index": 0, "data": str(Group.objects.get(name="group-1").id)}],
                }
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AttributeValue.objects.count(), attrv_count + 1)

        attrv = attr.get_latest_value()
        self.assertIsNotNone(attrv)
        self.assertEqual(attrv.group, Group.objects.get(name="group-1"))

    @patch("entry.tasks.import_entries.delay", Mock(side_effect=tasks.import_entries))
    def test_import_entry(self):
        user = self.guest_login()

        # prepare to Entity and Entries which importing data refers to
        ref_entity = Entity.objects.create(name="RefEntity", created_user=user)
        ref_entry = Entry.objects.create(name="ref", created_user=user, schema=ref_entity)
        group = Group.objects.create(name="group")
        role = Role.objects.create(name="role")

        entity = Entity.objects.create(name="Entity", created_user=user)
        attr_info = {
            "str": {"type": AttrType.STRING},
            "obj": {"type": AttrType.OBJECT},
            "grp": {"type": AttrType.GROUP},
            "role": {"type": AttrType.ROLE},
            "name": {"type": AttrType.NAMED_OBJECT},
            "bool": {"type": AttrType.BOOLEAN},
            "date": {"type": AttrType.DATE},
            "arr1": {"type": AttrType.ARRAY_STRING},
            "arr2": {"type": AttrType.ARRAY_OBJECT},
            "arr3": {"type": AttrType.ARRAY_NAMED_OBJECT},
            "arr4": {"type": AttrType.ARRAY_GROUP},
            "arr5": {"type": AttrType.ARRAY_ROLE},
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

        # try to import data which has invalid data structure
        for index in range(3):
            fp = self.open_fixture_file("invalid_import_data%d.yaml" % index)
            resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})
            fp.close()
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.content, b"Uploaded file has invalid data structure to import")

        # invalid data couldn't scan
        for index in range(2):
            fp = self.open_fixture_file("invalid_import_data_scan%d.yaml" % index)
            resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})
            fp.close()
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.content, b"Couldn't scan uploaded file")

        # invalid data date format
        fp = self.open_fixture_file("invalid_import_data_date.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"Invalid value is found: month must be in 1..12")

        # import data from test file
        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})
        fp.close()

        # check the import is success
        self.assertEqual(resp.status_code, 303)
        self.assertTrue(Entry.objects.filter(name="Entry", schema=entity))

        entry = Entry.objects.get(name="Entry", schema=entity)
        checklist = [
            {"attr": "str", "checker": lambda x: x.value == "foo"},
            {"attr": "obj", "checker": lambda x: x.referral.id == ref_entry.id},
            {"attr": "grp", "checker": lambda x: x.group == group},
            {"attr": "role", "checker": lambda x: x.role == role},
            {
                "attr": "name",
                "checker": lambda x: x.value == "foo" and x.referral.id == ref_entry.id,
            },
            {"attr": "bool", "checker": lambda x: x.boolean is False},
            {"attr": "date", "checker": lambda x: x.date == date(2018, 12, 31)},
            {"attr": "arr1", "checker": lambda x: x.data_array.count() == 3},
            {
                "attr": "arr2",
                "checker": lambda x: x.data_array.count() == 1
                and x.data_array.first().referral.id == ref_entry.id,
            },
            {
                "attr": "arr3",
                "checker": lambda x: x.data_array.count() == 1
                and x.data_array.first().referral.id == ref_entry.id,
            },
            {
                "attr": "arr4",
                "checker": lambda x: x.data_array.count() == 1
                and x.data_array.first().group == group,
            },
            {
                "attr": "arr5",
                "checker": lambda x: x.data_array.count() == 1
                and x.data_array.first().role == role,
            },
        ]
        for info in checklist:
            attr = entry.attrs.get(name=info["attr"])
            attrv = attr.get_latest_value()

            self.assertIsNotNone(attrv)
            self.assertTrue(info["checker"](attrv))

        # checks created jobs and its params are as expected
        jobs = Job.objects.filter(user=user)
        job_expectations = [
            {"operation": JobOperation.IMPORT_ENTRY, "status": JobStatus.DONE},
            {
                "operation": JobOperation.MAY_INVOKE_TRIGGER,
                "status": JobStatus.PREPARING,
            },
            {
                "operation": JobOperation.NOTIFY_CREATE_ENTRY,
                "status": JobStatus.PREPARING,
            },
        ]
        self.assertEqual(jobs.count(), len(job_expectations))
        for expectation in job_expectations:
            obj = jobs.get(operation=expectation["operation"].value)
            self.assertEqual(obj.status, expectation["status"])
            self.assertIsNone(obj.dependent_job)

        # checks that created entry was registered to the Elasticsearch
        res = self._es.get(index=settings.ES_CONFIG["INDEX_NAME"], id=entry.id)
        self.assertTrue(res["found"])

    @patch(
        "trigger.tasks.may_invoke_trigger.delay",
        Mock(side_effect=trigger_tasks.may_invoke_trigger),
    )
    @patch("entry.tasks.import_entries.delay", Mock(side_effect=tasks.import_entries))
    def test_import_when_duplicated_named_alias_exists(self):
        user = self.admin_login()

        # create Item and Alias that is duplicated with importing Item ("entry1")
        item = self.add_entry(user, "TestItem", self._entity)
        item.add_alias("entry1")

        # This import_data03 has following Items (entry1, entry2 and entry3)
        with self.open_fixture_file("import_data03.yaml") as fp:
            resp = self.client.post(
                reverse("entry:do_import", args=[self._entity.id]), {"file": fp}
            )
            self.assertEqual(resp.status_code, 303)

        # check expected values are set in the job attributes
        job = Job.objects.filter(operation=JobOperation.IMPORT_ENTRY).last()
        self.assertEqual(job.status, JobStatus.DONE)
        self.assertEqual(job.text, "")

        # check "entry1" wasn't created because same named Alias has already been registered
        whole_items = Entry.objects.filter(schema=self._entity, is_active=True)
        self.assertEqual(whole_items.count(), 3)
        self.assertEqual(
            sorted([x.name for x in whole_items.all()]), sorted(["TestItem", "entry2", "entry3"])
        )

    @patch(
        "trigger.tasks.may_invoke_trigger.delay",
        Mock(side_effect=trigger_tasks.may_invoke_trigger),
    )
    @patch("entry.tasks.import_entries.delay", Mock(side_effect=tasks.import_entries))
    def test_import_entry_when_trigger_is_set(self):
        user = self.guest_login()

        entity = self.create_entity(user, "Entity", [{"name": "str", "type": AttrType.STRING}])

        TriggerCondition.register(
            entity,
            [
                {"attr_id": entity.attrs.get(name="str").id, "cond": "foo"},
            ],
            [{"attr_id": entity.attrs.get(name="str").id, "value": "fuga"}],
        )

        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})
        fp.close()

        self.assertEqual(resp.status_code, 303)
        entry = Entry.objects.get(name="Entry", schema=entity)
        self.assertEqual(entry.get_attrv("str").value, "fuga")

    def test_import_entry_invalid_param(self):
        user: User = self.guest_login()
        role: Role = Role.objects.create(name="Role")
        role.users.add(user)
        entity: Entity = Entity.objects.create(name="Entity", created_user=user, is_active=False)

        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[9999]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"Failed to get entity of specified id")

        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"Failed to get entity of specified id")

        # nothing permisson
        entity.is_active = True
        entity.is_public = False
        entity.save()
        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"You don't have permission to access this object")

        # readable permission
        entity.readable.roles.add(role)
        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"You don't have permission to access this object")

        # writable permission
        entity.writable.roles.add(role)
        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 303)

    def test_import_entry_invalid_param_other_entity(self):
        user: User = self.guest_login()
        role: Role = Role.objects.create(name="Role")
        role.users.add(user)
        entity: Entity = Entity.objects.create(name="Entity", created_user=user, is_active=False)
        entity2: Entity = Entity.objects.create(name="Entity2", created_user=user)

        fp = self.open_fixture_file("import_data02.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity2.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"Specified entity does not exist (hoge)")

        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity2.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"Specified entity does not exist (Entity)")

        # nothing permisson
        entity.is_active = True
        entity.is_public = False
        entity.save()
        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity2.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"You don't have permission to access (Entity)")

        # readable permission
        entity.readable.roles.add(role)
        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity2.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"You don't have permission to access (Entity)")

        # writable permission
        entity.writable.roles.add(role)
        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity2.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 303)

    @patch("airone.lib.custom_view.is_custom", Mock(return_value=True))
    @patch("airone.lib.custom_view.call_custom")
    def test_import_entry_with_custom_view(self, mock_call_custom):
        user: User = self.guest_login()
        entity: Entity = Entity.objects.create(name="Entity", created_user=user)

        def side_effect(handler_name, entity_name, user, import_entity, import_data):
            # Check specified parameters are expected
            self.assertEqual(handler_name, "import_entry")
            self.assertEqual(entity_name, entity.name)
            self.assertEqual(import_entity, entity)
            data = yaml.safe_load(self.open_fixture_file("import_data01.yaml"))
            self.assertEqual(import_data, data[entity.name])

            return (import_data, None)

        mock_call_custom.side_effect = side_effect

        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 303)
        self.assertTrue(mock_call_custom.called)

        # specified other entity
        entity2: Entity = Entity.objects.create(name="Entity2", created_user=user)
        mock_call_custom.called = False
        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity2.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 303)
        self.assertTrue(mock_call_custom.called)

    @patch("airone.lib.custom_view.is_custom", Mock(return_value=True))
    @patch("airone.lib.custom_view.call_custom", Mock(return_value=(None, "error message")))
    def test_import_entry_with_custom_view_error(self):
        user: User = self.guest_login()
        entity: Entity = Entity.objects.create(name="Entity", created_user=user)

        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})
        fp.close()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"error message")

    @patch("entry.tasks.import_entries.delay", Mock(side_effect=tasks.import_entries))
    def test_import_entry_with_changing_entity_attr(self):
        user = self.admin_login()

        # prepare to Entity and Entries which importing data refers to
        ref_entity = Entity.objects.create(name="RefEntity", created_user=user)
        ref_entry = Entry.objects.create(name="ref", created_user=user, schema=ref_entity)
        Group.objects.create(name="group")

        entity = Entity.objects.create(name="Entity", created_user=user)
        attr_info = {
            "str (before changing)": {"type": AttrType.STRING},
            "obj": {"type": AttrType.OBJECT},
            "grp": {"type": AttrType.GROUP},
            "name": {"type": AttrType.NAMED_OBJECT},
            "bool": {"type": AttrType.BOOLEAN},
            "date": {"type": AttrType.DATE},
            "arr1": {"type": AttrType.ARRAY_STRING},
            "arr2": {"type": AttrType.ARRAY_OBJECT},
            "arr3": {"type": AttrType.ARRAY_NAMED_OBJECT},
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

        # Change a name of EntityAttr 'str (before changing)' to 'str'
        entity_attr = EntityAttr.objects.get(name="str (before changing)", parent_entity=entity)
        entity_attr.name = "str"
        entity_attr.save()

        # import data from test file
        fp = self.open_fixture_file("import_data01.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})

        # check the import is success
        self.assertEqual(resp.status_code, 303)

        entry = Entry.objects.get(name="Entry", schema=entity)
        self.assertEqual(entry.attrs.get(schema=entity_attr).get_latest_value().value, "foo")

        # check array_string value is set correctly
        attrv = entry.attrs.get(name="arr1").get_latest_value()
        self.assertEqual(attrv.data_type, AttrType.ARRAY_STRING)
        self.assertEqual(attrv.data_array.count(), 3)
        self.assertTrue(all([x.parent_attrv == attrv for x in attrv.data_array.all()]))

        # check imported data was registered to the ElasticSearch
        res = AdvancedSearchService.get_all_es_docs()
        self.assertEqual(res["hits"]["total"]["value"], 2)

        for e in [entry, ref_entry]:
            res = self._es.get(index=settings.ES_CONFIG["INDEX_NAME"], id=e.id)
            self.assertTrue(res["found"])

    @skip("When a file which is encodeed by non UTF-8, django-test-client fails encoding")
    def test_import_entry_by_multi_encoded_files(self):
        user = self.admin_login()

        entity = Entity.objects.create(name="Entity", created_user=user)
        EntityAttr.objects.create(
            name="str",
            type=AttrType.STRING,
            created_user=user,
            parent_entity=entity,
        )

        for encoding in ["UTF-8", "Shift-JIS", "EUC-JP"]:
            fp = self.open_fixture_file("import_data_%s.yaml" % encoding)
            resp = self.client.post(reverse("entry:do_import", args=[entity.id]), {"file": fp})

            # check the import is success
            self.assertEqual(resp.status_code, 303)

        self.assertEqual(Entry.objects.filter(name__iregex=r"えんとり*").coiunt(), 3)

    @patch("entry.tasks.import_entries.delay", Mock(side_effect=tasks.import_entries))
    def test_import_entry_with_notify_entry(self):
        user = self.admin_login()

        # create
        fp = self.open_fixture_file("import_data02.yaml")
        self.client.post(reverse("entry:do_import", args=[self._entity.id]), {"file": fp})
        fp.close()

        job = Job.objects.filter(operation=JobOperation.IMPORT_ENTRY).last()
        self.assertEqual(job.status, JobStatus.DONE)

        self.assertTrue(Job.objects.filter(operation=JobOperation.NOTIFY_CREATE_ENTRY).exists())

        ret = AdvancedSearchService.search_entries(user, [self._entity.id], [AttrHint(name="test")])
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual(ret.ret_values[0].entry["name"], "entry")
        self.assertEqual(ret.ret_values[0].attrs["test"]["value"], "fuga")

        Job.objects.all().delete()

        # no update
        fp = self.open_fixture_file("import_data02.yaml")
        self.client.post(reverse("entry:do_import", args=[self._entity.id]), {"file": fp})
        fp.close()

        job = Job.objects.filter(operation=JobOperation.IMPORT_ENTRY).last()
        self.assertEqual(job.status, JobStatus.DONE)

        self.assertFalse(Job.objects.filter(operation=JobOperation.NOTIFY_UPDATE_ENTRY).exists())

        Job.objects.all().delete()

        # update
        fp = self.open_fixture_file("import_data02_change.yaml")
        self.client.post(reverse("entry:do_import", args=[self._entity.id]), {"file": fp})
        fp.close()

        job = Job.objects.filter(operation=JobOperation.IMPORT_ENTRY).last()
        self.assertEqual(job.status, JobStatus.DONE)

        self.assertTrue(Job.objects.filter(operation=JobOperation.NOTIFY_UPDATE_ENTRY).exists())

        ret = AdvancedSearchService.search_entries(user, [self._entity.id], [AttrHint(name="test")])
        self.assertEqual(ret.ret_count, 1)
        self.assertEqual(ret.ret_values[0].entry["name"], "entry")
        self.assertEqual(ret.ret_values[0].attrs["test"]["value"], "piyo")

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_create_and_edit_entry_that_has_date_attr(self):
        admin = self.admin_login()

        entity = Entity.objects.create(name="entity", created_user=admin)
        entity_attr = EntityAttr.objects.create(
            name="attr_date",
            type=AttrType.DATE,
            parent_entity=entity,
            created_user=admin,
        )

        # creates entry that has a parameter which is typed date
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "id": str(entity_attr.id),
                    "type": str(AttrType.DATE),
                    "value": [{"data": "2018-12-31", "index": 0}],
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

        # get entry which is created in here
        entry = Entry.objects.get(name="entry", schema=entity)

        self.assertEqual(entry.attrs.count(), 1)
        self.assertIsNotNone(entry.attrs.last().get_latest_value())
        self.assertEqual(entry.attrs.last().get_latest_value().date, date(2018, 12, 31))

        # edit entry to update the value of attribute 'attr_date'
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(name="attr_date").id),
                    "type": str(AttrType.DATE),
                    "value": [{"data": "2019-1-1", "index": 0}],
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

        # checks AttributeValue which is specified to update
        self.assertEqual(entry.attrs.last().values.count(), 2)
        self.assertEqual(entry.attrs.last().get_latest_value().date, date(2019, 1, 1))

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

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_edit_invalid_date_param(self):
        INITIAL_DATE = date.today()
        admin = self.admin_login()

        entity = Entity.objects.create(name="entity", created_user=admin)
        EntityAttr.objects.create(
            name="attr_date",
            type=AttrType.DATE,
            parent_entity=entity,
            created_user=admin,
        )

        entry = Entry.objects.create(name="entry", schema=entity, created_user=admin)
        entry.complement_attrs(admin)

        attr = entry.attrs.last()
        attr.add_value(admin, INITIAL_DATE)

        # updates entry that has a invalid parameter which is typed date
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(attr.id),
                    "type": str(AttrType.DATE),
                    "value": [{"data": "hoge", "index": 0}],
                    "referral_key": [],
                },
            ],
        }

        # check that invalied parameter raises error with self.assertRaises(ValueError) as ar:
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)

        # check that backend processing will not update with invalid value
        self.assertEqual(entry.attrs.last().values.count(), 1)
        self.assertEqual(attr.get_latest_value().date, INITIAL_DATE)

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

    @patch("entry.tasks.edit_entry_attrs.delay", Mock(side_effect=tasks.edit_entry_attrs))
    def test_edit_entry_for_each_typed_attributes_repeatedly(self):
        user = self.admin_login()

        # prepare to Entity and Entries which importing data refers to
        ref_entity = Entity.objects.create(name="RefEntity", created_user=user)
        ref_entry = Entry.objects.create(name="ref", created_user=user, schema=ref_entity)
        group = Group.objects.create(name="group")

        entity = Entity.objects.create(name="Entity", created_user=user)
        attr_info = {
            "str": {
                "type": AttrType.STRING,
                "value": [{"data": "data", "index": 0}],
                "expect_value": "data",
                "expect_blank_value": "",
                "referral_key": [],
            },
            "obj": {
                "type": AttrType.OBJECT,
                "value": [{"data": str(ref_entry.id), "index": 0}],
                "expect_value": "ref",
                "expect_blank_value": None,
                "referral_key": [],
            },
            "grp": {
                "type": AttrType.GROUP,
                "value": [{"data": str(group.id), "index": 0}],
                "expect_value": "group",
                "expect_blank_value": None,
                "referral_key": [],
            },
            "name": {
                "type": AttrType.NAMED_OBJECT,
                "value": [{"data": str(ref_entry.id), "index": 0}],
                "expect_value": {"key": "ref"},
                "expect_blank_value": {"": None},
                "referral_key": [{"data": "key", "index": 0}],
            },
            "bool": {
                "type": AttrType.BOOLEAN,
                "value": [{"data": True, "index": 0}],
                "expect_value": True,
                "expect_blank_value": False,
                "referral_key": [],
            },
            "date": {
                "type": AttrType.DATE,
                "value": [{"data": "2018-01-01", "index": 0}],
                "expect_value": date(2018, 1, 1),
                "expect_blank_value": None,
                "referral_key": [],
            },
            "arr1": {
                "type": AttrType.ARRAY_STRING,
                "value": [{"data": "foo", "index": 0}, {"data": "bar", "index": 1}],
                "expect_value": ["bar", "foo"],
                "expect_blank_value": [],
                "referral_key": [],
            },
            "arr2": {
                "type": AttrType.ARRAY_OBJECT,
                "value": [{"data": str(ref_entry.id), "index": 0}],
                "expect_value": ["ref"],
                "expect_blank_value": [],
                "referral_key": [],
            },
            "arr3": {
                "type": AttrType.ARRAY_NAMED_OBJECT,
                "value": [{"data": str(ref_entry.id), "index": 0}],
                "expect_value": [{"foo": "ref"}, {"bar": None}],
                "expect_blank_value": [],
                "referral_key": [
                    {"data": "foo", "index": 0},
                    {"data": "bar", "index": 1},
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

            info["schema"] = attr
            if info["type"] & AttrType.OBJECT:
                attr.referral.add(ref_entity)

        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        entry.complement_attrs(user)

        ###
        # set valid values for each attrs
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(schema=x["schema"]).id),
                    "type": str(x["type"]),
                    "value": x["value"],
                    "referral_key": x["referral_key"],
                }
                for x in attr_info.values()
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        # checks that expected values are set for each Attributes
        self.assertEqual(resp.status_code, 200)
        for info in attr_info.values():
            value = entry.attrs.get(schema=info["schema"]).get_latest_value().get_value()

            if isinstance(value, list):
                self.assertTrue(any(x in info["expect_value"] for x in value))
            else:
                self.assertEqual(value, info["expect_value"])

        ###
        # checks that value histories for each Attributes will be same when same values are set
        # before_vh = [x.get_value() for x in entry.get_value_history(user)]
        before_vh = entry.get_value_history(user)

        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(schema=x["schema"]).id),
                    "type": str(x["type"]),
                    "value": x["value"],
                    "referral_key": x["referral_key"],
                }
                for x in attr_info.values()
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )

        self.assertEqual(entry.get_value_history(user), before_vh)

        ###
        # checks that expected values are set for each Attributes
        self.assertEqual(resp.status_code, 200)

        # set all parameters to be empty
        params = {
            "entry_name": "entry",
            "attrs": [
                {
                    "entity_attr_id": "",
                    "id": str(entry.attrs.get(schema=x["schema"]).id),
                    "type": str(x["type"]),
                    "value": [],
                    "referral_key": [],
                }
                for x in attr_info.values()
            ],
        }
        resp = self.client.post(
            reverse("entry:do_edit", args=[entry.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        for name, info in attr_info.items():
            self.assertEqual(
                entry.attrs.get(schema=info["schema"]).get_latest_value().get_value(),
                info["expect_blank_value"],
            )

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

    @patch("entry.tasks.import_entries.delay", Mock(side_effect=tasks.import_entries))
    def test_import_entry_with_abnormal_entry_which_has_multiple_attrs_of_same_name(
        self,
    ):
        user = self.admin_login()

        # Create a test entry
        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=user)
        entry.complement_attrs(user)

        # Added another Attribute to entry to test to be able to detect this abnormal situation
        self.make_attr("test", parent_entry=entry, created_user=user)

        # Send a request to import entry
        with self.assertLogs(logger=Logger, level=logging.ERROR) as cm:
            fp = self.open_fixture_file("import_data02.yaml")
            self.client.post(reverse("entry:do_import", args=[self._entity.id]), {"file": fp})
            fp.close()

        # Check expected log was dispatched
        self.assertEqual(
            cm.output[0],
            (
                "ERROR:airone:[task.import_entry] "
                "Abnormal entry was detected(entry:%d)" % entry.id
            ),
        )

        # Check Job processing was ended successfully
        job = Job.objects.filter(user=user, operation=JobOperation.IMPORT_ENTRY).last()
        self.assertEqual(job.status, JobStatus.DONE)

    @patch("entry.tasks.import_entries.delay", Mock(side_effect=tasks.import_entries))
    @patch("entry.tasks._do_import_entries")
    def test_import_entry_with_unexpected_situation(self, mock_do_import_entry):
        def side_effect(*args, **kwargs):
            raise RuntimeError("Unexpected situation was happened")

        mock_do_import_entry.side_effect = side_effect

        user = self.admin_login()

        # Create a test entry
        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=user)
        entry.complement_attrs(user)

        # Send a request to import entry
        fp = self.open_fixture_file("import_data02.yaml")
        self.client.post(reverse("entry:do_import", args=[self._entity.id]), {"file": fp})
        fp.close()

        # Check Job processing was failed
        job = Job.objects.filter(user=user, operation=JobOperation.IMPORT_ENTRY).last()
        self.assertEqual(job.status, JobStatus.ERROR)
        self.assertEqual(
            job.text,
            "[task.import] [job:%d] Unexpected situation was happened" % job.id,
        )

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

    @patch("entry.tasks.import_entries.delay", Mock(side_effect=tasks.import_entries))
    def test_importing_entries_on_multiple_entities(self):
        user = self.admin_login()

        Entity.objects.create(name="fuga", created_user=user)

        fp = self.open_fixture_file("import_data04.yaml")
        resp = self.client.post(reverse("entry:do_import", args=[self._entity.id]), {"file": fp})
        fp.close()

        # check the import is success
        self.assertEqual(resp.status_code, 303)
        for entity_name in ["hoge", "fuga"]:
            self.assertTrue(
                Job.objects.filter(
                    target__name=entity_name, operation=JobOperation.IMPORT_ENTRY
                ).exists()
            )
            self.assertTrue(
                Entry.objects.filter(
                    name="entry1", schema__name=entity_name, is_active=True
                ).exists()
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
