import json
import pickle
import pytz
import time

from acl.models import ACLBase
from datetime import date
from entity.models import Entity
from entry.models import Entry

from datetime import datetime, timedelta
from django.conf import settings
from django.db import models
from user.models import User


def _support_time_default(o):
    if isinstance(o, date):
        return o.isoformat()
    raise TypeError(repr(o) + " is not JSON serializable")


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

    # Constant to describes status of each jobs
    # TODO: these constants should be changed as dict value like STATUS for maintainability
    OP_CREATE = 1
    OP_EDIT = 2
    OP_DELETE = 3
    OP_COPY = 4
    OP_IMPORT = 5
    OP_EXPORT = 6
    OP_RESTORE = 7

    # TODO: these constants should be changed as dict value like STATUS for maintainability
    TARGET_UNKNOWN = 0
    TARGET_ENTRY = 1
    TARGET_ENTITY = 2

    STATUS = {
        'PREPARING': 1,
        'DONE': 2,
        'ERROR': 3,
        'TIMEOUT': 4,
        'PROCESSING': 5,
        'CANCELED': 6,
    }

    user = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    target = models.ForeignKey(ACLBase, null=True)
    target_type = models.IntegerField(default=0)
    status = models.IntegerField(default=0)
    operation = models.IntegerField(default=0)

    # This parameter will be used for supplementing this job
    text = models.TextField()

    # This has serialized parameters to which user sent
    params = models.TextField()

    # This describes dependent jobs. Before executing a job processing, this must check this value.
    # When this has another job, this job have to wait until it would be finished.
    dependent_job = models.ForeignKey('Job', null=True)

    def wait_dependent_job(self):
        # When there is dependent job, this waits until that would be finished.
        if self.dependent_job:
            while not self.dependent_job.is_finished():
                time.sleep(.5)

    def is_timeout(self):
        # Sync updated_at time information with the data which is stored in database
        self.refresh_from_db(fields=['updated_at'])

        task_expiry = self.updated_at + timedelta(seconds=self._get_job_timeout())

        return datetime.now(pytz.timezone(settings.TIME_ZONE)) > task_expiry

    def is_finished(self):
        # Sync status flag information with the data which is stored in database
        self.refresh_from_db(fields=['status'])

        # This value indicates that there is no more processing for a job
        finished_status = [
            Job.STATUS['DONE'],
            Job.STATUS['ERROR'],
            Job.STATUS['TIMEOUT'],
            Job.STATUS['CANCELED'],
        ]

        return (self.status in finished_status or self.is_timeout())

    def is_canceled(self):
        # Sync status flag information with the data which is stored in database
        self.refresh_from_db(fields=['status'])

        return self.status == Job.STATUS['CANCELED']

    def is_ready_to_process(self):
        return (not self.is_finished() and self.status != Job.STATUS['PROCESSING'])

    def set_status(self, new_status):
        if new_status in Job.STATUS.values():
            self.status = new_status
            self.save(update_fields=['status', 'updated_at'])

            return True
        else:
            return False

    def to_json(self):
        return {
            'id': self.id,
            'user': self.user.username,
            'target_type': self.target_type,
            'target': {
                'id': self.target.id,
                'name': self.target.name,
            } if self.target else {},
            'text': self.text,
            'status': self.status,
            'operation': self.operation,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    @classmethod
    def _create_new_job(kls, user, target, operation, text, params):
        t_type = kls.TARGET_UNKNOWN
        if isinstance(target, Entry):
            t_type = kls.TARGET_ENTRY
        elif isinstance(target, Entity):
            t_type = kls.TARGET_ENTITY

        # set dependent job to prevent running tasks simultaneously which set to target same one.
        dependent_job = None
        if target:
            threshold = (datetime.now(pytz.timezone(settings.TIME_ZONE)) -
                         timedelta(seconds=kls._get_job_timeout()))
            dependent_job = (
                Job.objects.filter(target=target, operation=operation, updated_at__gt=threshold)
                .order_by('updated_at').last()
            )

        params = {
            'user': user,
            'target': target,
            'target_type': t_type,
            'status': kls.STATUS['PREPARING'],
            'operation': operation,
            'text': text,
            'params': params,
            'dependent_job': dependent_job,
        }

        return kls.objects.create(**params)

    @classmethod
    def get_job_with_params(kls, user, params):
        return kls.objects.filter(
            user=user, params=json.dumps(params, default=_support_time_default, sort_keys=True))

    @classmethod
    def new_create(kls, user, target, text='', params={}):
        return kls._create_new_job(user, target, kls.OP_CREATE, text,
                                   json.dumps(params, default=_support_time_default,
                                              sort_keys=True))

    @classmethod
    def new_edit(kls, user, target, text='', params={}):
        return kls._create_new_job(user, target, kls.OP_EDIT, text,
                                   json.dumps(params, default=_support_time_default,
                                              sort_keys=True))

    @classmethod
    def new_delete(kls, user, target, text='', params={}):
        return kls._create_new_job(user, target, kls.OP_DELETE, text, params)

    @classmethod
    def new_copy(kls, user, target, text='', params={}):
        return kls._create_new_job(user, target, kls.OP_COPY, text,
                                   json.dumps(params, sort_keys=True))

    @classmethod
    def new_import(kls, user, entity, text='', params={}):
        return kls._create_new_job(user, entity, kls.OP_IMPORT, text,
                                   json.dumps(params, default=_support_time_default,
                                              sort_keys=True))

    @classmethod
    def new_export(kls, user, target=None, text='', params={}):
        return kls._create_new_job(user, target, kls.OP_EXPORT, text,
                                   json.dumps(params, default=_support_time_default,
                                              sort_keys=True))

    @classmethod
    def new_restore(kls, user, target, text='', params={}):
        return kls._create_new_job(user, target, kls.OP_RESTORE, text, params)

    def set_cache(self, value):
        with open('%s/job_%d' % (settings.AIRONE['FILE_STORE_PATH'], self.id), 'wb') as fp:
            pickle.dump(value, fp)

    def get_cache(self):
        value = ''
        with open('%s/job_%d' % (settings.AIRONE['FILE_STORE_PATH'], self.id), 'rb') as fp:
            value = pickle.load(fp)

        return value

    @classmethod
    def _get_job_timeout(kls):
        if 'JOB_TIMEOUT' in settings.AIRONE and settings.AIRONE['JOB_TIMEOUT']:
            return settings.AIRONE['JOB_TIMEOUT']
        else:
            return kls.DEFAULT_JOB_TIMEOUT
