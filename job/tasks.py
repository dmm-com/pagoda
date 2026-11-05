from __future__ import annotations

from typing import Any

from celery import Task

from airone.celery import app
from airone.exceptions import ImportDataError
from airone.lib.acl import ACLType, get_permitted_objects
from airone.lib.drf import YAMLRenderer
from airone.lib.job import may_schedule_until_job_is_ready, register_job_task
from common.lib.import_detector import ImportType, wrap_envelope
from entity.api_v2.serializers import EntityImportExportRootSerializer
from entity.models import Entity, EntityAttr
from entity.tasks import _JobRequest
from group.api_v2.serializers import GroupExportSerializer
from group.import_service import import_groups
from group.models import Group
from job.models import Job, JobOperation, JobStatus
from job.params import ConfigurationExportParams, GeneralImportParams
from role.api_v2.serializers import RoleImportExportChildSerializer
from role.api_v2.views import get_permitted_roles
from role.models import Role
from user.api_v2.serializers import UserExportSerializer
from user.import_service import import_users
from user.models import User


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
