import json
from datetime import date
from unittest.mock import Mock, patch

from django.urls import reverse

from airone.lib.elasticsearch import AttrHint
from airone.lib.types import (
    AttrType,
)
from entity.models import Entity, EntityAttr
from entry import tasks
from entry.models import Attribute, AttributeValue, Entry
from entry.services import AdvancedSearchService
from entry.tests.test_view import BaseViewTest
from group.models import Group
from job.models import Job, JobOperation, JobStatus, JobTarget
from role.models import Role
from trigger import tasks as trigger_tasks
from trigger.models import TriggerCondition


class ViewEditTest(BaseViewTest):
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
            attr = self.make_attr(name=attr_name, entry=entry, user=user)

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

        self.make_attr(name="attr", user=user, entry=entry)

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
            self.make_attr(name=attr_name, user=user, entry=entry)

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

        attr = self.make_attr(name="attr", attrtype=AttrType.OBJECT, user=user, entry=entry)

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
