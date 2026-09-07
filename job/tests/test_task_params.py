import inspect
from unittest import mock

from django.test import TestCase
from pydantic import BaseModel, ConfigDict, ValidationError

from airone.lib.job import _handle_task
from entity.models import Entity
from entry.models import Entry
from job.models import Job, JobOperation, JobStatus, JobTarget
from job.params import (
    UpdateDocumentParams,
    register_job_params,
    unregister_job_params,
)
from user.models import User


class JobParamsBoundaryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="job-params-user")

    def test_invalid_enqueue_does_not_create_row(self):
        with self.assertRaises(ValidationError):
            Job._create_new_job(
                self.user,
                None,
                JobOperation.UPDATE_DOCUMENT,
                "",
                {"is_update": "not-a-bool"},
            )

        self.assertEqual(Job.objects.count(), 0)

    def test_canonical_serialization_and_operation_aware_deduplication(self):
        job = Job._create_new_job(
            self.user,
            None,
            JobOperation.UPDATE_DOCUMENT,
            "",
            {"is_update": True},
        )

        self.assertEqual(job.params, '{"is_update":true}')
        self.assertEqual(
            Job.get_job_with_params(
                self.user, JobOperation.UPDATE_DOCUMENT, {"is_update": True}
            ).get(),
            job,
        )
        self.assertFalse(
            Job.get_job_with_params(self.user, JobOperation.NOTIFY_UPDATE_ENTRY, {}).exists()
        )

    def test_deduplication_finds_pre_deployment_json_representation(self):
        legacy_job = Job.objects.create(
            user=self.user,
            target_type=JobTarget.UNKNOWN,
            status=JobStatus.PREPARING,
            operation=JobOperation.UPDATE_DOCUMENT,
            text="",
            params='{"is_update": true}',
        )

        self.assertEqual(
            Job.get_job_with_params(
                self.user,
                JobOperation.UPDATE_DOCUMENT,
                {"is_update": True},
            ).get(),
            legacy_job,
        )

    def test_typed_params_are_cached_and_expected_contract_is_checked(self):
        job = Job._create_new_job(
            self.user,
            None,
            JobOperation.UPDATE_DOCUMENT,
            "",
            {"is_update": True},
        )

        parser = job.get_typed_params.__globals__["parse_job_params"]
        with mock.patch("job.models.parse_job_params", wraps=parser) as parse:
            first = job.get_typed_params(UpdateDocumentParams)
            second = job.get_typed_params(UpdateDocumentParams)

        self.assertIs(first, second)
        parse.assert_called_once()
        with self.assertRaises(TypeError):
            job.get_typed_params(dict)

    @mock.patch("airone.lib.job.mail_admins")
    def test_invalid_legacy_row_fails_before_processing_without_mail_or_handler(
        self, mail_admins: mock.Mock
    ):
        job = Job.objects.create(
            user=self.user,
            target_type=JobTarget.UNKNOWN,
            status=JobStatus.PREPARING,
            operation=JobOperation.UPDATE_DOCUMENT,
            text="",
            params='{"is_update":"secret-invalid-value"}',
        )
        handler = mock.Mock()

        with mock.patch("job.models.Logger.error") as logger:
            _handle_task(object(), handler, job)

        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.ERROR)
        handler.assert_not_called()
        mail_admins.assert_not_called()
        self.assertNotIn("secret-invalid-value", str(logger.call_args))

    def test_registered_custom_contract_is_checked_by_common_readiness_boundary(self):
        class CustomParams(BaseModel):
            model_config = ConfigDict(strict=True)
            count: int

        operation = 10_005
        register_job_params(operation, CustomParams)
        self.addCleanup(unregister_job_params, operation)
        job = Job.objects.create(
            user=self.user,
            target_type=JobTarget.UNKNOWN,
            status=JobStatus.PREPARING,
            operation=operation,
            text="",
            params='{"count":"invalid-secret"}',
        )

        with mock.patch("job.models.Logger.error") as logger:
            self.assertFalse(job.proceed_if_ready())

        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.ERROR)
        self.assertNotIn("invalid-secret", str(logger.call_args))

    def test_processing_transition_rejects_invalid_params_when_readiness_is_skipped(self):
        job = Job.objects.create(
            user=self.user,
            target_type=JobTarget.UNKNOWN,
            status=JobStatus.PREPARING,
            operation=JobOperation.UPDATE_DOCUMENT,
            text="",
            params='{"is_update":"invalid-secret"}',
        )

        with self.assertRaises(ValueError), mock.patch("job.models.Logger.error") as logger:
            job.update(JobStatus.PROCESSING)

        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.ERROR)
        self.assertNotIn("invalid-secret", str(logger.call_args))

    def test_operation_update_persists_canonical_params(self):
        job = Job._create_new_job(
            self.user,
            None,
            JobOperation.CREATE_ENTRY,
            "",
            {"entry_name": "entry", "attrs": []},
        )
        job.params = '{"entry_name": "entry", "attrs": []}'
        job.save(update_fields=["params"])

        job.update(operation=JobOperation.EDIT_ENTRY)

        job.refresh_from_db()
        self.assertEqual(job.operation, JobOperation.EDIT_ENTRY)
        self.assertEqual(job.params, '{"attrs":[],"entry_name":"entry"}')

    def test_legacy_custom_view_staging_pattern_remains_supported(self):
        entity = Entity.objects.create(name="entity", created_user=self.user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=self.user)
        custom_operation = 10_006
        handler = mock.Mock()

        job = Job.new_create(self.user, entry)
        with mock.patch.object(Job, "method_table", return_value={custom_operation: handler}):
            job.update(operation=custom_operation)

        job.refresh_from_db()
        self.assertEqual(job.operation, custom_operation)
        self.assertEqual(job.params, '{"attrs":[],"entry_name":"entry"}')

    def test_factories_have_no_mutable_defaults(self):
        for name, member in inspect.getmembers(Job, predicate=callable):
            if not name.startswith("new_"):
                continue
            for parameter in inspect.signature(member).parameters.values():
                self.assertNotIsInstance(parameter.default, (dict, list, set), name)
