import errno
import json
import logging
from datetime import date
from unittest import skip
from unittest.mock import Mock, patch

import yaml
from django.conf import settings
from django.urls import reverse
from elasticsearch import NotFoundError

from airone.lib.acl import ACLType
from airone.lib.elasticsearch import AttrHint
from airone.lib.log import Logger
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
from user.models import User


class ViewImportExportTest(BaseViewTest):
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
        self.make_attr(name="attr-test", entry=entry, user=user)

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
        with self.assertRaises(NotFoundError):
            self._es.get(index=settings.ES_CONFIG["INDEX_NAME"], id=entry.id)

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

    @patch("entry.tasks.import_entries.delay", Mock(side_effect=tasks.import_entries))
    def test_import_entry_with_abnormal_entry_which_has_multiple_attrs_of_same_name(
        self,
    ):
        user = self.admin_login()

        # Create a test entry
        entry = Entry.objects.create(name="entry", schema=self._entity, created_user=user)
        entry.complement_attrs(user)

        # Added another Attribute to entry to test to be able to detect this abnormal situation
        self.make_attr("test", entry=entry, user=user)

        # Send a request to import entry
        with self.assertLogs(logger=Logger, level=logging.ERROR) as cm:
            fp = self.open_fixture_file("import_data02.yaml")
            self.client.post(reverse("entry:do_import", args=[self._entity.id]), {"file": fp})
            fp.close()

        # Check expected log was dispatched
        self.assertEqual(
            cm.output[0],
            ("ERROR:airone:[task.import_entry] Abnormal entry was detected(entry:%d)" % entry.id),
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
