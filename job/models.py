import json
import pickle
import time
from datetime import date, datetime, timedelta
from enum import Enum
from importlib import import_module

import pytz
from django.conf import settings
from django.db import models

from acl.models import ACLBase
from airone.lib.log import Logger
from entity.models import Entity
from entry.models import Entry
from job.settings import CONFIG as JOB_CONFIG
from user.models import User


def _support_time_default(o):
    if isinstance(o, date):
        return o.isoformat()
    raise TypeError(repr(o) + " is not JSON serializable")


class JobOperation(Enum):
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
    _TASK_MODULE = {}

    # This hash table describes operation status value and operation processing
    _METHOD_TABLE = {}

    # TODO: these constants should be changed as dict value like STATUS for maintainability
    TARGET_UNKNOWN = 0
    TARGET_ENTRY = 1
    TARGET_ENTITY = 2

    STATUS = {
        "PREPARING": 1,
        "DONE": 2,
        "ERROR": 3,
        "TIMEOUT": 4,
        "PROCESSING": 5,
        "CANCELED": 6,
        "WARNING": 7,
    }

    # In some jobs sholdn't make user aware of existence because of user experience
    # (e.g. re-registrating elasticsearch data of entries which refer to changed name entry).
    # These are the jobs that should be proceeded transparently.
    HIDDEN_OPERATIONS = [
        JobOperation.REGISTER_REFERRALS.value,
        JobOperation.NOTIFY_CREATE_ENTRY.value,
        JobOperation.NOTIFY_UPDATE_ENTRY.value,
        JobOperation.NOTIFY_DELETE_ENTRY.value,
    ]

    CANCELABLE_OPERATIONS = [
        JobOperation.CREATE_ENTRY.value,
        JobOperation.COPY_ENTRY.value,
        JobOperation.IMPORT_ENTRY.value,
        JobOperation.IMPORT_ENTRY_V2.value,
        JobOperation.EXPORT_ENTRY.value,
        JobOperation.REGISTER_REFERRALS.value,
        JobOperation.EXPORT_SEARCH_RESULT.value,
    ]

    PARALLELIZABLE_OPERATIONS = [
        JobOperation.NOTIFY_CREATE_ENTRY.value,
        JobOperation.NOTIFY_UPDATE_ENTRY.value,
        JobOperation.NOTIFY_DELETE_ENTRY.value,
        JobOperation.COPY_ENTRY.value,
        JobOperation.DO_COPY_ENTRY.value,
        JobOperation.IMPORT_ENTRY.value,
        JobOperation.EXPORT_ENTRY.value,
    ]

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

    def may_schedule(self):
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

    def is_timeout(self):
        # Sync updated_at time information with the data which is stored in database
        self.refresh_from_db(fields=["updated_at"])

        task_expiry = self.updated_at + timedelta(seconds=self._get_job_timeout())

        return datetime.now(pytz.timezone(settings.TIME_ZONE)) > task_expiry

    def is_finished(self):
        # Sync status flag information with the data which is stored in database
        self.refresh_from_db(fields=["status"])

        # This value indicates that there is no more processing for a job
        finished_status = [
            Job.STATUS["DONE"],
            Job.STATUS["ERROR"],
            Job.STATUS["TIMEOUT"],
            Job.STATUS["CANCELED"],
            Job.STATUS["WARNING"],
        ]

        return self.status in finished_status or self.is_timeout()

    def is_canceled(self):
        # Sync status flag information with the data which is stored in database
        self.refresh_from_db(fields=["status"])

        return self.status == Job.STATUS["CANCELED"]

    def proceed_if_ready(self):
        # In this case, job is finished (might be canceled or proceeded same job by other process)
        if self.is_finished() or self.status == Job.STATUS["PROCESSING"]:
            return False

        # This checks whether dependent job is and it hasn't finished yet.
        if self.may_schedule():
            return False

        return True

    def update(self, status=None, text=None, target=None, operation=None):
        update_fields = ["updated_at"]

        if status is not None and status in Job.STATUS.values():
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

    def to_json(self):
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
    def _create_new_job(kls, user, target, operation, text, params) -> "Job":
        t_type = kls.TARGET_UNKNOWN
        if isinstance(target, Entry):
            t_type = kls.TARGET_ENTRY
        elif isinstance(target, Entity):
            t_type = kls.TARGET_ENTITY

        # set dependent job to prevent running tasks simultaneously which set to target same one.
        dependent_job = None
        if target:
            threshold = datetime.now(pytz.timezone(settings.TIME_ZONE)) - timedelta(
                seconds=kls._get_job_timeout()
            )
            dependent_job = (
                Job.objects.filter(target=target, operation=operation, updated_at__gt=threshold)
                .order_by("updated_at")
                .last()
            )

        params = {
            "user": user,
            "target": target,
            "target_type": t_type,
            "status": kls.STATUS["PREPARING"],
            "operation": operation,
            "text": text,
            "params": params,
            "dependent_job": dependent_job,
        }

        return kls.objects.create(**params)

    @classmethod
    def get_task_module(kls, component):
        if component not in kls._TASK_MODULE:
            kls._TASK_MODULE[component] = import_module(component)

        return kls._TASK_MODULE[component]

    @classmethod
    def method_table(kls):
        if not kls._METHOD_TABLE:
            entry_task = kls.get_task_module("entry.tasks")
            dashboard_task = kls.get_task_module("dashboard.tasks")
            entity_task = kls.get_task_module("entity.tasks")

            kls._METHOD_TABLE = {
                JobOperation.CREATE_ENTRY.value: entry_task.create_entry_attrs,
                JobOperation.EDIT_ENTRY.value: entry_task.edit_entry_attrs,
                JobOperation.DELETE_ENTRY.value: entry_task.delete_entry,
                JobOperation.COPY_ENTRY.value: entry_task.copy_entry,
                JobOperation.DO_COPY_ENTRY.value: entry_task.do_copy_entry,
                JobOperation.IMPORT_ENTRY.value: entry_task.import_entries,
                JobOperation.IMPORT_ENTRY_V2.value: entry_task.import_entries_v2,
                JobOperation.EXPORT_ENTRY.value: entry_task.export_entries,
                JobOperation.RESTORE_ENTRY.value: entry_task.restore_entry,
                JobOperation.EXPORT_SEARCH_RESULT.value: dashboard_task.export_search_result,
                JobOperation.REGISTER_REFERRALS.value: entry_task.register_referrals,
                JobOperation.CREATE_ENTITY.value: entity_task.create_entity,
                JobOperation.EDIT_ENTITY.value: entity_task.edit_entity,
                JobOperation.DELETE_ENTITY.value: entity_task.delete_entity,
                JobOperation.NOTIFY_CREATE_ENTRY.value: entry_task.notify_create_entry,
                JobOperation.NOTIFY_UPDATE_ENTRY.value: entry_task.notify_update_entry,
                JobOperation.NOTIFY_DELETE_ENTRY.value: entry_task.notify_delete_entry,
            }

        return kls._METHOD_TABLE

    @classmethod
    def register_method_table(kls, operation, method):
        if operation not in kls.method_table():
            kls._METHOD_TABLE[operation] = method

    @classmethod
    def get_job_with_params(kls, user, params):
        return kls.objects.filter(
            user=user,
            params=json.dumps(params, default=_support_time_default, sort_keys=True),
        )

    @classmethod
    def new_create(kls, user, target, text="", params={}):
        return kls._create_new_job(
            user,
            target,
            JobOperation.CREATE_ENTRY.value,
            text,
            json.dumps(params, default=_support_time_default, sort_keys=True),
        )

    @classmethod
    def new_edit(kls, user, target, text="", params={}):
        return kls._create_new_job(
            user,
            target,
            JobOperation.EDIT_ENTRY.value,
            text,
            json.dumps(params, default=_support_time_default, sort_keys=True),
        )

    @classmethod
    def new_delete(kls, user, target, text="", params={}):
        return kls._create_new_job(user, target, JobOperation.DELETE_ENTRY.value, text, params)

    @classmethod
    def new_copy(kls, user, target, text="", params={}):
        return kls._create_new_job(
            user,
            target,
            JobOperation.COPY_ENTRY.value,
            text,
            json.dumps(params, sort_keys=True),
        )

    @classmethod
    def new_do_copy(kls, user, target, text="", params={}):
        return kls._create_new_job(
            user,
            target,
            JobOperation.DO_COPY_ENTRY.value,
            text,
            json.dumps(params, sort_keys=True),
        )

    @classmethod
    def new_import(kls, user, entity, text="", params={}):
        return kls._create_new_job(
            user,
            entity,
            JobOperation.IMPORT_ENTRY.value,
            text,
            json.dumps(params, default=_support_time_default, sort_keys=True),
        )

    @classmethod
    def new_import_v2(kls, user, entity, text="", params={}):
        return kls._create_new_job(
            user,
            entity,
            JobOperation.IMPORT_ENTRY_V2.value,
            text,
            json.dumps(params, default=_support_time_default, sort_keys=True),
        )

    @classmethod
    def new_export(kls, user, target=None, text="", params={}):
        return kls._create_new_job(
            user,
            target,
            JobOperation.EXPORT_ENTRY.value,
            text,
            json.dumps(params, default=_support_time_default, sort_keys=True),
        )

    @classmethod
    def new_restore(kls, user, target, text="", params={}):
        return kls._create_new_job(user, target, JobOperation.RESTORE_ENTRY.value, text, params)

    @classmethod
    def new_export_search_result(kls, user, target=None, text="", params={}):
        return kls._create_new_job(
            user,
            target,
            JobOperation.EXPORT_SEARCH_RESULT.value,
            text,
            json.dumps(params, default=_support_time_default, sort_keys=True),
        )

    @classmethod
    def new_register_referrals(kls, user, target):
        return kls._create_new_job(
            user,
            target,
            JobOperation.REGISTER_REFERRALS.value,
            "",
            json.dumps({}, default=_support_time_default, sort_keys=True),
        )

    @classmethod
    def new_create_entity(kls, user, target, text="", params={}):
        return kls._create_new_job(
            user,
            target,
            JobOperation.CREATE_ENTITY.value,
            text,
            json.dumps(params, default=_support_time_default, sort_keys=True),
        )

    @classmethod
    def new_edit_entity(kls, user, target, text="", params={}):
        return kls._create_new_job(
            user,
            target,
            JobOperation.EDIT_ENTITY.value,
            text,
            json.dumps(params, default=_support_time_default, sort_keys=True),
        )

    @classmethod
    def new_delete_entity(kls, user, target, text="", params={}):
        return kls._create_new_job(user, target, JobOperation.DELETE_ENTITY.value, text, params)

    @classmethod
    def new_notify_create_entry(kls, user, target, text="", params={}):
        return kls._create_new_job(
            user, target, JobOperation.NOTIFY_CREATE_ENTRY.value, text, params
        )

    @classmethod
    def new_notify_update_entry(kls, user, target, text="", params={}):
        return kls._create_new_job(
            user, target, JobOperation.NOTIFY_UPDATE_ENTRY.value, text, params
        )

    @classmethod
    def new_notify_delete_entry(kls, user, target, text="", params={}):
        return kls._create_new_job(
            user, target, JobOperation.NOTIFY_DELETE_ENTRY.value, text, params
        )

    def set_cache(self, value):
        with open("%s/job_%d" % (settings.AIRONE["FILE_STORE_PATH"], self.id), "wb") as fp:
            pickle.dump(value, fp)

    def get_cache(self):
        value = ""
        with open("%s/job_%d" % (settings.AIRONE["FILE_STORE_PATH"], self.id), "rb") as fp:
            value = pickle.load(fp)

        return value

    @classmethod
    def _get_job_timeout(kls):
        if "JOB_TIMEOUT" in settings.AIRONE and settings.AIRONE["JOB_TIMEOUT"]:
            return settings.AIRONE["JOB_TIMEOUT"]
        else:
            return kls.DEFAULT_JOB_TIMEOUT
