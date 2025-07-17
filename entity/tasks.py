import json

from airone.celery import app
from airone.lib import custom_view
from airone.lib.job import may_schedule_until_job_is_ready, register_job_task
from airone.lib.types import AttrType
from entity.api_v2.serializers import EntityCreateSerializer, EntityUpdateSerializer
from entity.models import Entity, EntityAttr
from job.models import Job, JobOperation, JobStatus
from user.models import History, User


@register_job_task(JobOperation.CREATE_ENTITY)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def create_entity(self, job: Job) -> JobStatus:
    user = User.objects.filter(id=job.user.id).first()
    entity = Entity.objects.filter(id=job.target.id, is_active=True).first()

    if not entity or not user:
        # Abort when specified entity doesn't exist
        return JobStatus.CANCELED

    # for history record
    entity._history_user = user

    recv_data = json.loads(job.params)

    # register history to modify Entity
    history = user.seth_entity_add(entity)

    for attr in recv_data["attrs"]:
        attr_base = EntityAttr.objects.create(
            name=attr["name"],
            type=int(attr["type"]),
            is_mandatory=attr["is_mandatory"],
            is_delete_in_chain=attr["is_delete_in_chain"],
            created_user=user,
            parent_entity=entity,
            index=int(attr["row_index"]),
        )

        if int(attr["type"]) & AttrType.OBJECT:
            [attr_base.referral.add(Entity.objects.get(id=x)) for x in attr["ref_ids"]]

        # register history to modify Entity
        history.add_attr(attr_base)

    # clear flag to specify this entity has been completed to create
    entity.del_status(Entity.STATUS_CREATING)

    # update job status and save it
    return JobStatus.DONE


@register_job_task(JobOperation.EDIT_ENTITY)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def edit_entity(self, job: Job) -> JobStatus:
    user = User.objects.filter(id=job.user.id).first()
    entity = Entity.objects.filter(id=job.target.id, is_active=True).first()

    if not entity or not user:
        # Abort when specified entity doesn't exist
        return JobStatus.CANCELED

    # for history record
    entity._history_user = user

    recv_data = json.loads(job.params)

    # register history to modify Entity
    history = user.seth_entity_mod(entity)
    if entity.name != recv_data["name"]:
        history.mod_entity(entity, 'old name: "%s"' % (entity.name))

    if entity.name != recv_data["name"]:
        entity.name = recv_data["name"]
        entity.save(update_fields=["name"])

    if entity.note != recv_data["note"]:
        entity.note = recv_data["note"]
        entity.save(update_fields=["note"])

    # update processing for each attrs
    deleted_attr_ids = []
    for attr in recv_data["attrs"]:
        if "deleted" in attr:
            # In case of deleting attribute which has been already existed
            attr_obj = EntityAttr.objects.get(id=attr["id"])
            attr_obj.delete()

            # Save deleted EntityAttr id to update es_document of Entries
            # that are refered by associated AttributeValues.
            deleted_attr_ids.append(attr_obj.id)

            # register History to register deleting EntityAttr
            history.del_attr(attr_obj)

        elif "id" in attr and EntityAttr.objects.filter(id=attr["id"]).exists():
            # In case of updating attribute which has been already existed
            attr_obj = EntityAttr.objects.get(id=attr["id"])

            # register operaion history if the parameters are changed
            if attr_obj.name != attr["name"]:
                history.mod_attr(attr_obj, 'old name: "%s"' % (attr_obj.name))

            if attr_obj.is_mandatory != attr["is_mandatory"]:
                if attr["is_mandatory"]:
                    history.mod_attr(attr_obj, "set mandatory flag")
                else:
                    history.mod_attr(attr_obj, "unset mandatory flag")

            # EntityAttr.is_referral_updated() is separated from EntityAttr.is_updated()
            # to reduce unnecessary creation of HistoricalRecord.
            params = {
                "name": attr["name"],
                "index": attr["row_index"],
                "is_mandatory": attr["is_mandatory"],
                "is_delete_in_chain": attr["is_delete_in_chain"],
            }
            if attr_obj.is_updated(**params):
                attr_obj.name = attr["name"]
                attr_obj.is_mandatory = attr["is_mandatory"]
                attr_obj.is_delete_in_chain = attr["is_delete_in_chain"]
                attr_obj.index = int(attr["row_index"])

                attr_obj.save()

            if (attr_obj.type & AttrType.OBJECT) and (
                attr_obj.is_referral_updated([int(x) for x in attr["ref_ids"]])
            ):
                # the case of an attribute that has referral entry
                attr_obj.referral_clear()
                attr_obj.referral.add(*[Entity.objects.get(id=x) for x in attr["ref_ids"]])

        else:
            # In case of creating new attribute
            attr_obj = EntityAttr.objects.create(
                name=attr["name"],
                type=int(attr["type"]),
                is_mandatory=attr["is_mandatory"],
                is_delete_in_chain=attr["is_delete_in_chain"],
                index=int(attr["row_index"]),
                created_user=user,
                parent_entity=entity,
            )

            # append referral objects
            if int(attr["type"]) & AttrType.OBJECT:
                [attr_obj.referral.add(Entity.objects.get(id=x)) for x in attr["ref_ids"]]

            # register History to register adding EntityAttr
            history.add_attr(attr_obj)

    # clear flag to specify this entity has been completed to edit
    entity.del_status(Entity.STATUS_EDITING)

    # update job status and save it
    return JobStatus.DONE


@register_job_task(JobOperation.DELETE_ENTITY)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def delete_entity(self, job: Job) -> JobStatus:
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
def create_entity_v2(self, job: Job) -> JobStatus:
    entity: Entity | None = Entity.objects.filter(id=job.target.id, is_active=True).first()
    if not entity:
        return JobStatus.ERROR

    # pass to validate the params because the entity should be already created
    serializer = EntityCreateSerializer(data=json.loads(job.params), context={"_user": job.user})
    serializer.create_remaining(entity, serializer.initial_data)

    # update job status and save it
    return JobStatus.DONE


@register_job_task(JobOperation.EDIT_ENTITY_V2)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def edit_entity_v2(self, job: Job) -> JobStatus:
    entity: Entity | None = Entity.objects.filter(id=job.target.id, is_active=True).first()
    if not entity:
        return JobStatus.ERROR

    serializer = EntityUpdateSerializer(
        instance=entity, data=json.loads(job.params), context={"_user": job.user}
    )
    if not serializer.is_valid():
        return JobStatus.ERROR

    serializer.update_remaining(entity, serializer.validated_data)

    return JobStatus.DONE


@register_job_task(JobOperation.DELETE_ENTITY_V2)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def delete_entity_v2(self, job: Job) -> JobStatus:
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
