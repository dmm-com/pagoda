from __future__ import annotations

from typing import Any

from celery import Task

from airone.celery import app
from airone.lib import custom_view
from airone.lib.job import may_schedule_until_job_is_ready, register_job_task
from airone.lib.types import AttrType
from entity.api_v2.serializers import EntityCreateSerializer, EntityUpdateSerializer
from entity.models import Entity, EntityAttr
from job.models import Job, JobOperation, JobStatus
from job.params import (
    CreateEntityParams,
    CreateEntityV2Params,
    EditEntityAttrV2Params,
    EditEntityParams,
    EditEntityV2Params,
    EditWebhookParams,
    EmptyParams,
    EntityAttrParams,
    EntityAttrV2Params,
    ImportEntityPreviewParams,
    IsolationActionParams,
    IsolationConditionParams,
    IsolationRuleParams,
    WebhookHeaderParams,
    WebhookParams,
)
from user.models import History, User

CreateEntityAttr = EntityAttrParams
EditEntityAttr = EntityAttrParams
CreateEntityV2Attr = EntityAttrV2Params
EditEntityV2Attr = EditEntityAttrV2Params
CreateEntityV2Webhook = WebhookParams
EditEntityV2Webhook = EditWebhookParams
IsolationActionParam = IsolationActionParams
IsolationConditionParam = IsolationConditionParams
IsolationRuleParam = IsolationRuleParams
WebhookHeader = WebhookHeaderParams

__all__ = [
    "CreateEntityAttr",
    "CreateEntityParams",
    "CreateEntityV2Attr",
    "CreateEntityV2Params",
    "CreateEntityV2Webhook",
    "EditEntityAttr",
    "EditEntityParams",
    "EditEntityV2Attr",
    "EditEntityV2Params",
    "EditEntityV2Webhook",
    "IsolationActionParam",
    "IsolationConditionParam",
    "IsolationRuleParam",
    "WebhookHeader",
]

# ============================================================================
# Task Functions
# ============================================================================


@register_job_task(JobOperation.CREATE_ENTITY)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def create_entity(self: Task[Any, Any], job: Job) -> JobStatus:
    if job.target is None:
        return JobStatus.CANCELED
    user = User.objects.filter(id=job.user.id).first()
    entity = Entity.objects.filter(id=job.target.id, is_active=True).first()

    if not entity or not user:
        # Abort when specified entity doesn't exist
        return JobStatus.CANCELED

    # for history record
    entity._history_user = user

    params = job.get_typed_params(CreateEntityParams)

    # register history to modify Entity
    history = user.seth_entity_add(entity)

    for attr in params.attrs:
        attr_base = EntityAttr.objects.create(
            name=attr.name,
            type=attr.type,
            is_mandatory=attr.is_mandatory,
            is_delete_in_chain=attr.is_delete_in_chain,
            created_user=user,
            parent_entity=entity,
            index=int(attr.row_index),
        )

        if attr.type & AttrType.OBJECT:
            for x in attr.ref_ids:
                attr_base.referral.add(Entity.objects.get(id=x))

        # register history to modify Entity
        history.add_attr(attr_base)

    # clear flag to specify this entity has been completed to create
    entity.del_status(Entity.STATUS_CREATING)

    # update job status and save it
    return JobStatus.DONE


@register_job_task(JobOperation.EDIT_ENTITY)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def edit_entity(self: Task[Any, Any], job: Job) -> JobStatus:
    if job.target is None:
        return JobStatus.CANCELED
    user = User.objects.filter(id=job.user.id).first()
    entity = Entity.objects.filter(id=job.target.id, is_active=True).first()

    if not entity or not user:
        # Abort when specified entity doesn't exist
        return JobStatus.CANCELED

    # for history record
    entity._history_user = user

    params = job.get_typed_params(EditEntityParams)

    # register history to modify Entity
    history = user.seth_entity_mod(entity)
    if entity.name != params.name:
        history.mod_entity(entity, 'old name: "%s"' % (entity.name))

    if entity.name != params.name:
        entity.name = params.name
        entity.save(update_fields=["name"])

    if entity.note != params.note:
        entity.note = params.note
        entity.save(update_fields=["note"])

    # update processing for each attrs
    deleted_attr_ids: list[int] = []
    for attr in params.attrs:
        if attr.deleted:
            # In case of deleting attribute which has been already existed
            if attr.id is None:
                continue
            attr_obj = EntityAttr.objects.get(id=attr.id)
            attr_obj.delete()

            # Save deleted EntityAttr id to update es_document of Entries
            # that are refered by associated AttributeValues.
            deleted_attr_ids.append(attr_obj.id)

            # register History to register deleting EntityAttr
            history.del_attr(attr_obj)

        elif attr.id is not None and EntityAttr.objects.filter(id=attr.id).exists():
            # In case of updating attribute which has been already existed
            attr_id = attr.id
            attr_obj = EntityAttr.objects.get(id=attr_id)

            # register operaion history if the parameters are changed
            if attr_obj.name != attr.name:
                history.mod_attr(attr_obj, 'old name: "%s"' % (attr_obj.name))

            if attr_obj.is_mandatory != attr.is_mandatory:
                if attr.is_mandatory:
                    history.mod_attr(attr_obj, "set mandatory flag")
                else:
                    history.mod_attr(attr_obj, "unset mandatory flag")

            # EntityAttr.is_referral_updated() is separated from EntityAttr.is_updated()
            # to reduce unnecessary creation of HistoricalRecord.
            if attr_obj.is_updated(
                name=attr.name,
                is_mandatory=attr.is_mandatory,
                is_delete_in_chain=attr.is_delete_in_chain,
                index=int(attr.row_index),
            ):
                attr_obj.name = attr.name
                attr_obj.is_mandatory = attr.is_mandatory
                attr_obj.is_delete_in_chain = attr.is_delete_in_chain
                attr_obj.index = int(attr.row_index)

                attr_obj.save()

            if (attr_obj.type & AttrType.OBJECT) and (attr_obj.is_referral_updated(attr.ref_ids)):
                # the case of an attribute that has referral entry
                attr_obj.referral_clear()
                attr_obj.referral.add(*[Entity.objects.get(id=x) for x in attr.ref_ids])

        else:
            # In case of creating new attribute
            attr_obj = EntityAttr.objects.create(
                name=attr.name,
                type=attr.type,
                is_mandatory=attr.is_mandatory,
                is_delete_in_chain=attr.is_delete_in_chain,
                index=int(attr.row_index),
                created_user=user,
                parent_entity=entity,
            )

            # append referral objects
            if attr.type & AttrType.OBJECT:
                for x in attr.ref_ids:
                    attr_obj.referral.add(Entity.objects.get(id=x))

            # register History to register adding EntityAttr
            history.add_attr(attr_obj)

    # clear flag to specify this entity has been completed to edit
    entity.del_status(Entity.STATUS_EDITING)

    # update job status and save it
    return JobStatus.DONE


@register_job_task(JobOperation.DELETE_ENTITY)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def delete_entity(self: Task[Any, Any], job: Job) -> JobStatus:
    job.get_typed_params(EmptyParams)
    if job.target is None:
        return JobStatus.CANCELED
    user = User.objects.filter(id=job.user.id).first()
    entity = Entity.objects.filter(id=job.target.id, is_active=False).first()

    if not entity or not user:
        # Abort when specified entity doesn't exist
        return JobStatus.CANCELED

    # for history record
    entity._history_user = user

    entity.delete()

    history = user.seth_entity_del(entity)

    # Delete all attributes which target Entity have
    for attr in entity.attrs.all():
        attr.delete()
        history.del_attr(attr)

    return JobStatus.DONE


@register_job_task(JobOperation.CREATE_ENTITY_V2)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def create_entity_v2(self: Task[Any, Any], job: Job) -> JobStatus:
    if job.target is None:
        return JobStatus.ERROR
    entity: Entity | None = Entity.objects.filter(id=job.target.id, is_active=True).first()
    if not entity:
        return JobStatus.ERROR

    params = job.get_typed_params(CreateEntityV2Params)

    params_dict = params.model_dump(mode="json", by_alias=True, exclude_unset=True)

    # The request path has already created the Entity, so validating its name again
    # would report that very instance as a duplicate. Validate the remaining payload
    # as a partial update while retaining the create-specific nested validators.
    remaining_data = {key: value for key, value in params_dict.items() if key != "name"}
    serializer = EntityCreateSerializer(
        instance=entity,
        data=remaining_data,
        partial=True,
        context={"_user": job.user},
    )
    if not serializer.is_valid():
        return JobStatus.ERROR
    serializer.create_remaining(entity, serializer.validated_data)

    # update job status and save it
    return JobStatus.DONE


@register_job_task(JobOperation.EDIT_ENTITY_V2)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def edit_entity_v2(self: Task[Any, Any], job: Job) -> JobStatus:
    if job.target is None:
        return JobStatus.ERROR
    entity: Entity | None = Entity.objects.filter(id=job.target.id, is_active=True).first()
    if not entity:
        return JobStatus.ERROR

    params = job.get_typed_params(EditEntityV2Params)

    # Convert Pydantic model to dict for serializer
    # (EntityUpdateSerializer expects dict input)
    #
    # Use exclude_unset (NOT exclude_none) so that explicitly specified nulls
    # keep their "clear this field" semantics. E.g. the UI sends
    # default_value: null to remove an EntityAttr's default value; dropping
    # that null made it impossible to clear a default once set, because
    # update_or_create keeps the stored value for absent fields.
    params_dict = params.model_dump(mode="json", by_alias=True, exclude_unset=True)

    serializer = EntityUpdateSerializer(
        instance=entity, data=params_dict, context={"_user": job.user}
    )
    if not serializer.is_valid():
        return JobStatus.ERROR

    serializer.update_remaining(entity, serializer.validated_data)

    return JobStatus.DONE


@register_job_task(JobOperation.DELETE_ENTITY_V2)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def delete_entity_v2(self: Task[Any, Any], job: Job) -> JobStatus:
    job.get_typed_params(EmptyParams)
    if job.target is None:
        return JobStatus.ERROR
    entity: Entity | None = Entity.objects.filter(id=job.target.id, is_active=True).first()
    if not entity:
        return JobStatus.ERROR

    if custom_view.is_custom("before_delete_entity_v2"):
        custom_view.call_custom("before_delete_entity_v2", None, job.user, entity)

    # register operation History for deleting entity
    history: History = job.user.seth_entity_del(entity)
    entity.delete()

    # Delete all attributes which target Entity have
    entity_attr: EntityAttr
    for entity_attr in entity.attrs.filter(is_active=True):
        history.del_attr(entity_attr)
        entity_attr.delete()

    if custom_view.is_custom("after_delete_entity_v2"):
        custom_view.call_custom("after_delete_entity_v2", None, job.user, entity)

    return JobStatus.DONE


@register_job_task(JobOperation.IMPORT_ENTITY_PREVIEW)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def import_entities_preview_v2(self: Task[Any, Any], job: Job) -> JobStatus:
    """Build the preview of a model import file and store it on the job.

    Previewing costs as much as the import it previews, so it runs here rather
    than in the request that asked for it. It writes nothing.
    """
    from entity.api_v2.serializers import EntityImportExportRootSerializer

    params = job.get_typed_params(ImportEntityPreviewParams)
    serializer = EntityImportExportRootSerializer(
        data=params.model_dump(mode="json", by_alias=True, exclude_unset=True),
        context={"request": _JobRequest(job.user)},
    )
    if not serializer.is_valid():
        return JobStatus.ERROR

    payload = serializer.build_preview(job=job)
    if payload is None:
        return JobStatus.CANCELED

    job.set_cache(payload)

    return JobStatus.DONE


class _JobRequest:
    """The minimum a serializer needs from a request when it runs on a worker."""

    def __init__(self, user: User) -> None:
        self.user = user
