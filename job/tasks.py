from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any

from celery import Task
from django.core.files.storage import default_storage

from airone.celery import app
from airone.exceptions import ImportDataError
from airone.lib.acl import ACLObjType, ACLType, get_permitted_objects
from airone.lib.drf import YAMLRenderer
from airone.lib.job import may_schedule_until_job_is_ready, register_job_task
from common.lib.import_detector import ImportType, wrap_envelope
from entity.api_v2.serializers import EntityImportExportRootSerializer
from entity.models import Entity, EntityAttr
from entity.tasks import _JobRequest
from entry.models import Entry
from group.api_v2.serializers import GroupExportSerializer
from group.import_service import import_groups
from group.models import Group
from job.models import Job, JobOperation, JobStatus
from job.params import ConfigurationExportParams, GeneralImportParams, JobHistoryExportParams
from role.api_v2.serializers import RoleImportExportChildSerializer
from role.api_v2.views import get_permitted_roles
from role.models import Role
from user.api_v2.serializers import UserExportSerializer
from user.import_service import import_users
from user.models import User


@register_job_task(JobOperation.EXPORT_JOB_HISTORY)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def export_job_history(self: Task[Any, Any], job: Job) -> None:
    from job.api_v2.views import filter_jobs

    params = job.get_typed_params(JobHistoryExportParams)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "job_id",
            "user",
            "target_entity",
            "target_entry",
            "status",
            "operation",
            "execution_time_seconds",
            "created_at",
            "message",
        ]
    )
    # Exclude this export and jobs created after it was requested.
    queryset = filter_jobs(job.user, params.filters).filter(id__lt=job.id)
    entry_schema_names = dict(
        Entry.objects.filter(id__in=queryset.values_list("target_id", flat=True)).values_list(
            "id", "schema__name"
        )
    )
    for index, item in enumerate(queryset.iterator(chunk_size=500)):
        if index % 500 == 0 and job.is_canceled():
            return
        target_entity = ""
        target_entry = ""
        if item.target is not None:
            if item.target.objtype == ACLObjType.Entry:
                target_entry = item.target.name
                target_entity = (
                    entry_schema_names.get(item.target_id, "") if item.target_id is not None else ""
                )
            else:
                target_entity = item.target.name
        try:
            status_name = (
                JobStatus.TIMEOUT.name
                if item.status in (JobStatus.PREPARING, JobStatus.PROCESSING)
                and item.is_timeout(with_refresh=False)
                else JobStatus(item.status).name
            )
        except ValueError:
            status_name = str(item.status)
        try:
            operation_name = (
                JobOperation.EXPORT_JOB_HISTORY.name
                if item.is_legacy_history_export()
                else JobOperation(item.operation).name
            )
        except ValueError:
            operation_name = str(item.operation)
        elapsed = (
            (
                item.updated_at
                if item.is_finished(with_refresh=False)
                else datetime.now(timezone.utc)
            )
            - item.created_at
        ).total_seconds()
        writer.writerow(
            [
                item.id,
                item.user.username,
                target_entity,
                target_entry,
                status_name,
                operation_name,
                int(elapsed),
                item.created_at.isoformat(),
                item.text,
            ]
        )
    if not job.is_canceled():
        with default_storage.open(job.text, "wb") as file:
            file.write(output.getvalue().encode("utf-8-sig"))


@register_job_task(JobOperation.EXPORT_CONFIGURATION_V2)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def export_configuration(self: Task[Any, Any], job: Job) -> None:
    params = job.get_typed_params(ConfigurationExportParams)
    user = job.user
    data: object
    if params.kind == "entity":
        if params.entity_id is not None:
            entity = Entity.objects.filter(id=params.entity_id, is_active=True).first()
            entities = (
                [entity]
                if entity is not None and user.has_permission(entity, ACLType.Readable)
                else []
            )
            attrs = [
                attr
                for attr in EntityAttr.objects.filter(
                    parent_entity_id=params.entity_id, is_active=True
                )
                if user.has_permission(attr, ACLType.Readable)
            ]
        else:
            entities = get_permitted_objects(user, Entity, ACLType.Readable)
            attrs = get_permitted_objects(user, EntityAttr, ACLType.Readable)
        data = EntityImportExportRootSerializer(
            {
                "Entity": entities,
                "EntityAttr": attrs,
            }
        ).data
    elif params.kind == "user":
        data = UserExportSerializer(User.objects.filter(is_active=True), many=True).data
    elif params.kind == "group":
        data = GroupExportSerializer(Group.objects.filter(is_active=True), many=True).data
    else:
        data = RoleImportExportChildSerializer(
            get_permitted_roles(user, Role.objects.filter(is_active=True)), many=True
        ).data

    if not job.is_canceled():
        job.set_cache(YAMLRenderer().render(wrap_envelope(ImportType(params.kind), data)))


@register_job_task(JobOperation.IMPORT_GENERAL_V2)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def import_general(self: Task[Any, Any], job: Job) -> tuple[JobStatus, str, None]:
    params = job.get_typed_params(GeneralImportParams)

    try:
        if params.kind == "entity":
            serializer = EntityImportExportRootSerializer(
                data=params.data, context={"request": _JobRequest(job.user)}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        elif params.kind == "user":
            import_users(params.data)
        else:
            import_groups(params.data)
    except ImportDataError as e:
        return JobStatus.ERROR, str(e), None

    return JobStatus.DONE, "Imported %s data" % params.kind, None
