import enum
import json
import os
import pickle
import time
from datetime import date, datetime, timedelta
from importlib import import_module
from typing import Any, Callable, Optional, TypeAlias, Union

import pytz
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models

from acl.models import ACLBase
from airone.lib import auto_complement
from airone.lib.log import Logger
from airone.lib.types import BaseIntEnum
from entity.models import Entity
from entry.models import Entry
from job.settings import CONFIG as JOB_CONFIG
from user.models import User

TaskReturnType: TypeAlias = Union["JobStatus", tuple["JobStatus", str, Optional[ACLBase]], None]

TaskHandler: TypeAlias = Callable[[Any, "Job"], TaskReturnType]

if os.path.exists(settings.BASE_DIR + "/custom_view"):
    from custom_view.lib.task import (
        CUSTOM_CANCELABLE_OPERATIONS,
        CUSTOM_DOWNLOADABLE_OPERATIONS,
        CUSTOM_HIDDEN_OPERATIONS,
        CUSTOM_PARALLELIZABLE_OPERATIONS,
        CUSTOM_TASKS,
        JobOperationCustom,
    )
else:
    CUSTOM_CANCELABLE_OPERATIONS = []
    CUSTOM_DOWNLOADABLE_OPERATIONS = []
    CUSTOM_HIDDEN_OPERATIONS = []
    CUSTOM_PARALLELIZABLE_OPERATIONS = []
    CUSTOM_TASKS = {}

    class JobOperationCustom(BaseIntEnum):  # type: ignore
        pass


def _support_time_default(o):
    if isinstance(o, date):
        return o.isoformat()
    raise TypeError(repr(o) + " is not JSON serializable")


@enum.unique
class JobOperation(BaseIntEnum):
    # Constant to describes status of each jobs
    CREATE_ENTRY = 1
    EDIT_ENTRY = 2
    DELETE_ENTRY = 3
    COPY_ENTRY = 4
    IMPORT_ENTRY = 5
    EXPORT_ENTRY = 6
    RESTORE_ENTRY = 7
    EXPORT_SEARCH_RESULT = 8
    REGISTER_REFERRALS = 9
    CREATE_ENTITY = 10
    EDIT_ENTITY = 11
    DELETE_ENTITY = 12
    NOTIFY_CREATE_ENTRY = 13
    NOTIFY_UPDATE_ENTRY = 14
    NOTIFY_DELETE_ENTRY = 15
    DO_COPY_ENTRY = 16
    IMPORT_ENTRY_V2 = 17
    GROUP_REGISTER_REFERRAL = 18
    ROLE_REGISTER_REFERRAL = 19
    EXPORT_ENTRY_V2 = 20
    UPDATE_DOCUMENT = 21
    EXPORT_SEARCH_RESULT_V2 = 22
    MAY_INVOKE_TRIGGER = 23
    CREATE_ENTITY_V2 = 24
    EDIT_ENTITY_V2 = 25
    DELETE_ENTITY_V2 = 26
    CREATE_ENTRY_V2 = 27
    EDIT_ENTRY_V2 = 28
    DELETE_ENTRY_V2 = 29
    IMPORT_ROLE_V2 = 30


@enum.unique
class JobTarget(BaseIntEnum):
    UNKNOWN = 0
    ENTRY = 1
    ENTITY = 2


@enum.unique
class JobStatus(BaseIntEnum):
    PREPARING = 1
    DONE = 2
    ERROR = 3
    TIMEOUT = 4
    PROCESSING = 5
    CANCELED = 6
    WARNING = 7


class Job(models.Model):
    """
    This manage processing which is executed on backend.

    NOTE: This is similar to the user.models.History. That focus on
          the chaning history of Schema, while this focus on managing
          the jobs that user operated.
    """

    # This constant value indicates the frequency to qeury database for job status
    STATUS_CHECK_FREQUENCY = 100

    # This is the time (seconds) of expiry for continuing job.
    # This value could be overwrite by settings
    DEFAULT_JOB_TIMEOUT = 86400

    # This caches each task module to be able to call them from Job instance
    _TASK_MODULE: dict[str, Any] = {}

    # This hash table describes operation status value and operation processing
    _METHOD_TABLE: dict[JobOperation | JobOperationCustom, TaskHandler] = {}

    # In some jobs sholdn't make user aware of existence because of user experience
    # (e.g. re-registrating elasticsearch data of entries which refer to changed name entry).
    # These are the jobs that should be proceeded transparently.
    HIDDEN_OPERATIONS: list[JobOperation | JobOperationCustom] = [
        JobOperation.REGISTER_REFERRALS,
        JobOperation.NOTIFY_CREATE_ENTRY,
        JobOperation.NOTIFY_UPDATE_ENTRY,
        JobOperation.NOTIFY_DELETE_ENTRY,
        JobOperation.UPDATE_DOCUMENT,
        JobOperation.MAY_INVOKE_TRIGGER,
        JobOperation.GROUP_REGISTER_REFERRAL,
        JobOperation.ROLE_REGISTER_REFERRAL,
    ] + CUSTOM_HIDDEN_OPERATIONS

    CANCELABLE_OPERATIONS: list[JobOperation | JobOperationCustom] = [
        JobOperation.CREATE_ENTRY,
        JobOperation.COPY_ENTRY,
        JobOperation.IMPORT_ENTRY,
        JobOperation.IMPORT_ENTRY_V2,
        JobOperation.EXPORT_ENTRY,
        JobOperation.EXPORT_ENTRY_V2,
        JobOperation.REGISTER_REFERRALS,
        JobOperation.EXPORT_SEARCH_RESULT,
        JobOperation.EXPORT_SEARCH_RESULT_V2,
    ] + CUSTOM_CANCELABLE_OPERATIONS

    PARALLELIZABLE_OPERATIONS: list[JobOperation | JobOperationCustom] = [
        JobOperation.NOTIFY_CREATE_ENTRY,
        JobOperation.NOTIFY_UPDATE_ENTRY,
        JobOperation.NOTIFY_DELETE_ENTRY,
        JobOperation.COPY_ENTRY,
        JobOperation.DO_COPY_ENTRY,
        JobOperation.IMPORT_ENTRY,
        JobOperation.EXPORT_ENTRY,
        JobOperation.UPDATE_DOCUMENT,
    ] + CUSTOM_PARALLELIZABLE_OPERATIONS

    DOWNLOADABLE_OPERATIONS: list[JobOperation | JobOperationCustom] = [
        JobOperation.EXPORT_ENTRY,
        JobOperation.EXPORT_ENTRY_V2,
        JobOperation.EXPORT_SEARCH_RESULT,
        JobOperation.EXPORT_SEARCH_RESULT_V2,
    ] + CUSTOM_DOWNLOADABLE_OPERATIONS

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    target = models.ForeignKey(ACLBase, null=True, on_delete=models.SET_NULL)
    target_type = models.IntegerField(default=0)
    status = models.IntegerField(default=0)
    operation = models.IntegerField(default=0)

    # This parameter will be used for supplementing this job
    text = models.TextField()

    # This has serialized parameters to which user sent
    params = models.TextField()

    # This describes dependent jobs. Before executing a job processing, this must check this value.
    # When this has another job, this job have to wait until it would be finished.
    dependent_job = models.ForeignKey("Job", null=True, on_delete=models.SET_NULL)

    def may_schedule(self) -> bool:
        # Operations that can run in parallel exclude checking for dependent jobs
        if self.operation in self.PARALLELIZABLE_OPERATIONS:
            return False

        # When there is dependent job, this re-send a request to run same job
        if self.dependent_job and not self.dependent_job.is_finished():
            # This delay is needed to prevent sending excessive message to MQ
            # when there are many dependent jobs.
            time.sleep(JOB_CONFIG.RESCHEDULING_DELAY_SECONDS)

            # This sends request to reschedule this job.
            self.run()

            return True
        else:
            return False

    def is_timeout(self) -> bool:
        # Sync updated_at time information with the data which is stored in database
        self.refresh_from_db(fields=["updated_at"])

        task_expiry = self.updated_at + timedelta(seconds=self._get_job_timeout())

        return datetime.now(pytz.timezone(settings.TIME_ZONE)) > task_expiry

    def is_finished(self, with_refresh: bool = True) -> bool:
        if with_refresh:
            # Sync status flag information with the data which is stored in database
            self.refresh_from_db(fields=["status"])

        # This value indicates that there is no more processing for a job
        finished_status: list[JobStatus] = [
            JobStatus.DONE,
            JobStatus.ERROR,
            JobStatus.TIMEOUT,
            JobStatus.CANCELED,
            JobStatus.WARNING,
        ]

        return self.status in finished_status or self.is_timeout()

    def is_canceled(self) -> bool:
        # Sync status flag information with the data which is stored in database
        self.refresh_from_db(fields=["status"])

        return self.status == JobStatus.CANCELED

    def proceed_if_ready(self) -> bool:
        # In this case, job is finished (might be canceled or proceeded same job by other process)
        if self.is_finished() or self.status == JobStatus.PROCESSING:
            return False

        # This checks whether dependent job is and it hasn't finished yet.
        if self.may_schedule():
            return False

        return True

    def update(
        self,
        status: int | None = None,
        text: str | None = None,
        target: ACLBase | None = None,
        operation: int | None = None,
    ):
        update_fields = ["updated_at"]

        if status is not None and status in [s.value for s in JobStatus]:
            update_fields.append("status")
            self.status = status

        if text is not None:
            update_fields.append("text")
            self.text = text

        if target is not None:
            update_fields.append("target")
            self.target = target

        if operation is not None and operation in self.method_table():
            update_fields.append("operation")
            self.operation = operation

        self.save(update_fields=update_fields)

    def to_json(self) -> dict:
        # For advanced search results export, target is assumed to be empty.
        return {
            "id": self.id,
            "user": self.user.username,
            "target_type": self.target_type,
            "target": {
                "id": self.target.id,
                "name": self.target.name,
                "is_active": self.target.is_active,
            }
            if self.target
            else {},
            "text": self.text,
            "status": self.status,
            "operation": self.operation,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def run(self, will_delay=True):
        method_table = self.method_table()
        if self.operation not in method_table:
            Logger.error("Job %s has invalid operation type" % self.id)
            return

        # initiate job processing
        method = method_table[self.operation]
        if will_delay:
            return method.delay(self.id)
        else:
            return method(self.id)

    @classmethod
    def _create_new_job(
        kls,
        user: User,
        target: Entity | Entry | Any | None,
        operation: int,
        text: str | None,
        params: dict | None = None,
        depend_on=None,
    ) -> "Job":
        t_type = JobTarget.UNKNOWN
        if target is not None:
            if isinstance(target, Entry):
                t_type = JobTarget.ENTRY
            elif isinstance(target, Entity):
                t_type = JobTarget.ENTITY

        # # set dependent job to prevent running tasks simultaneously which set to target same one.
        dependent_job: Job | None = None
        if target is not None:
            threshold = datetime.now(pytz.timezone(settings.TIME_ZONE)) - timedelta(
                seconds=kls._get_job_timeout()
            )
            dependent_job = (
                Job.objects.filter(target=target, operation=operation, updated_at__gt=threshold)
                .order_by("updated_at")
                .last()
            )

        if dependent_job is None and depend_on is not None:
            dependent_job = depend_on

        params_str = (
            json.dumps(params, default=_support_time_default, sort_keys=True)
            if params is not None
            else "{}"
        )

        job_params: dict[str, Any] = {
            "user": user,
            "target_type": t_type,
            "status": JobStatus.PREPARING,
            "operation": operation,
            "text": text,
            "params": params_str,
            "dependent_job": dependent_job,
        }

        if target is not None:
            job_params["target"] = target

        return kls.objects.create(**job_params)

    @classmethod
    def get_task_module(kls, component: str):
        if component not in kls._TASK_MODULE:
            kls._TASK_MODULE[component] = import_module(component)

        return kls._TASK_MODULE[component]

    @classmethod
    def method_table(kls) -> dict[JobOperation | JobOperationCustom, TaskHandler]:
        for operation_num, task in CUSTOM_TASKS.items():
            custom_task = kls.get_task_module("custom_view.tasks")
            kls._METHOD_TABLE |= {operation_num: getattr(custom_task, task)}

        return kls._METHOD_TABLE

    @classmethod
    def register_method_table(
        kls, operation: JobOperation | JobOperationCustom, method: TaskHandler
    ):
        # Raise error if trying to register a handler that's already registered
        if operation in kls._METHOD_TABLE:
            raise ValueError(
                f"Task handler for operation {operation} is already registered. "
                f"Duplicate registration attempt for {method.__module__}.{method.__name__}"
            )
        # For decorator registration, register directly without calling method_table()
        # This avoids potential circular imports
        kls._METHOD_TABLE[operation] = method

    @classmethod
    def get_job_with_params(kls, user: User, params):
        return kls.objects.filter(
            user=user, params=json.dumps(params, default=_support_time_default, sort_keys=True)
        )

    @classmethod
    def new_create(kls, user: User, target, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.CREATE_ENTRY,
            text=text,
            params=params,
        )

    @classmethod
    def new_edit(kls, user: User, target, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.EDIT_ENTRY,
            text=text,
            params=params,
        )

    @classmethod
    def new_delete(kls, user: User, target, text=""):
        return kls._create_new_job(
            user=user, target=target, operation=JobOperation.DELETE_ENTRY, text=text
        )

    @classmethod
    def new_copy(kls, user: User, target, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.COPY_ENTRY,
            text=text,
            params=params,
        )

    @classmethod
    def new_do_copy(kls, user: User, target, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.DO_COPY_ENTRY,
            text=text,
            params=params,
        )

    @classmethod
    def new_import(kls, user: User, entity, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=entity,
            operation=JobOperation.IMPORT_ENTRY,
            text=text,
            params=params,
        )

    @classmethod
    def new_import_v2(kls, user: User, entity, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=entity,
            operation=JobOperation.IMPORT_ENTRY_V2,
            text=text,
            params=params,
        )

    @classmethod
    def new_export(kls, user: User, target=None, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.EXPORT_ENTRY,
            text=text,
            params=params,
        )

    @classmethod
    def new_export_v2(kls, user: User, target=None, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.EXPORT_ENTRY_V2,
            text=text,
            params=params,
        )

    @classmethod
    def new_restore(kls, user: User, target, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.RESTORE_ENTRY,
            text=text,
            params=params,
        )

    @classmethod
    def new_export_search_result(kls, user: User, target=None, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.EXPORT_SEARCH_RESULT,
            text=text,
            params=params,
        )

    @classmethod
    def new_export_search_result_v2(kls, user: User, target=None, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.EXPORT_SEARCH_RESULT_V2,
            text=text,
            params=params,
        )

    @classmethod
    def new_register_referrals(
        kls, user: User, target, operation_value=JobOperation.REGISTER_REFERRALS, params={}
    ):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=operation_value,
            text="",
            params=params,
        )

    @classmethod
    def new_create_entity(kls, user: User, target, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.CREATE_ENTITY,
            text=text,
            params=params,
        )

    @classmethod
    def new_edit_entity(kls, user: User, target, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.EDIT_ENTITY,
            text=text,
            params=params,
        )

    @classmethod
    def new_delete_entity(kls, user: User, target, text=""):
        return kls._create_new_job(
            user=user, target=target, operation=JobOperation.DELETE_ENTITY, text=text
        )

    @classmethod
    def new_update_documents(kls, target, text="", params={}):
        user = auto_complement.get_auto_complement_user(None)
        if not user:
            user = User.objects.create(username=settings.AIRONE["AUTO_COMPLEMENT_USER"])
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.UPDATE_DOCUMENT,
            text=text,
            params=params,
        )

    @classmethod
    def new_notify_create_entry(kls, user: User, target, text=""):
        return kls._create_new_job(
            user=user, target=target, operation=JobOperation.NOTIFY_CREATE_ENTRY, text=text
        )

    @classmethod
    def new_notify_update_entry(kls, user: User, target, text=""):
        return kls._create_new_job(
            user=user, target=target, operation=JobOperation.NOTIFY_UPDATE_ENTRY, text=text
        )

    @classmethod
    def new_notify_delete_entry(kls, user: User, target, text=""):
        return kls._create_new_job(
            user=user, target=target, operation=JobOperation.NOTIFY_DELETE_ENTRY, text=text
        )

    @classmethod
    def new_invoke_trigger(kls, user: User, target_entry, recv_attrs={}, dependent_job=None):
        return kls._create_new_job(
            user=user,
            target=target_entry,
            operation=JobOperation.MAY_INVOKE_TRIGGER,
            text="",
            params=recv_attrs,
            depend_on=dependent_job,
        )

    @classmethod
    def new_create_entity_v2(kls, user: User, target: Entity, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.CREATE_ENTITY_V2,
            text=text,
            params=params,
        )

    @classmethod
    def new_edit_entity_v2(kls, user: User, target: Entity, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.EDIT_ENTITY_V2,
            text=text,
            params=params,
        )

    @classmethod
    def new_delete_entity_v2(kls, user: User, target: Entity, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.DELETE_ENTITY_V2,
            text=text,
            params=params,
        )

    @classmethod
    def new_create_entry_v2(kls, user: User, target, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.CREATE_ENTRY_V2,
            text=text,
            params=params,
        )

    @classmethod
    def new_edit_entry_v2(kls, user: User, target: Entry, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.EDIT_ENTRY_V2,
            text=text,
            params=params,
        )

    @classmethod
    def new_delete_entry_v2(kls, user: User, target: Entry, text="", params={}):
        return kls._create_new_job(
            user=user,
            target=target,
            operation=JobOperation.DELETE_ENTRY_V2,
            text=text,
            params=params,
        )

    def set_cache(self, value):
        with default_storage.open("job_%d" % self.id, "wb") as fp:
            pickle.dump(value, fp)

    def get_cache(self):
        value = ""
        with default_storage.open("job_%d" % self.id, "rb") as fp:
            value = pickle.load(fp)
        return value

    @classmethod
    def _get_job_timeout(kls) -> int:
        if "JOB_TIMEOUT" in settings.AIRONE and settings.AIRONE["JOB_TIMEOUT"]:
            return settings.AIRONE["JOB_TIMEOUT"]
        else:
            return kls.DEFAULT_JOB_TIMEOUT

    @classmethod
    def new_role_import_v2(kls, user: User, text="", params: dict | None = None) -> "Job":
        return kls._create_new_job(
            user=user, target=None, operation=JobOperation.IMPORT_ROLE_V2, text=text, params=params
        )
