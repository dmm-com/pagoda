from __future__ import annotations

from typing import Any

from celery import Task

from airone.celery import app
from airone.lib.acl import ACLType, get_permitted_objects
from airone.lib.drf import YAMLRenderer
from airone.lib.job import may_schedule_until_job_is_ready, register_job_task
from entity.api_v2.serializers import EntityImportExportRootSerializer
from entity.models import Entity, EntityAttr
from group.api_v2.serializers import GroupExportSerializer
from group.models import Group
from job.models import Job, JobOperation
from job.params import ConfigurationExportParams
from role.api_v2.serializers import RoleImportExportChildSerializer
from role.api_v2.views import get_permitted_roles
from role.models import Role
from user.api_v2.serializers import UserExportSerializer
from user.models import User


@register_job_task(JobOperation.EXPORT_CONFIGURATION_V2)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def export_configuration(self: Task[Any, Any], job: Job) -> None:
    params = job.get_typed_params(ConfigurationExportParams)
    user = job.user
    data: object
    if params.kind == "entity":
        data = EntityImportExportRootSerializer(
            {
                "Entity": get_permitted_objects(user, Entity, ACLType.Readable),
                "EntityAttr": get_permitted_objects(user, EntityAttr, ACLType.Readable),
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
        job.set_cache(YAMLRenderer().render(data))
