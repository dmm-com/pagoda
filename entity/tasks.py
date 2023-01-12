import json

from airone.celery import app
from airone.lib.types import AttrTypeValue
from entity.models import Entity, EntityAttr
from job.models import Job
from user.models import User


@app.task(bind=True)
def create_entity(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        # At the first time, update job status to prevent executing this job duplicately
        job.update(Job.STATUS["PROCESSING"])

        user = User.objects.filter(id=job.user.id).first()
        entity = Entity.objects.filter(id=job.target.id, is_active=True).first()

        # for history record
        entity._history_user = user

        if not entity or not user:
            # Abort when specified entity doesn't exist
            job.update(Job.STATUS["CANCELED"])
            return

        recv_data = json.loads(job.params)

        # register history to modify Entity
        history = user.seth_entity_add(entity)

        adding_attrs = []
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

            if int(attr["type"]) & AttrTypeValue["object"]:
                [attr_base.referral.add(Entity.objects.get(id=x)) for x in attr["ref_ids"]]

            # This is neccesary to summarize adding attribute history to one time
            adding_attrs.append(attr_base)

            # register history to modify Entity
            history.add_attr(attr_base)

        if adding_attrs:
            # save history for adding attributes if it's necessary
            entity.attrs.add(*adding_attrs)

        # clear flag to specify this entity has been completed to create
        entity.del_status(Entity.STATUS_CREATING)

        # update job status and save it
        job.update(Job.STATUS["DONE"])


@app.task(bind=True)
def edit_entity(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        # At the first time, update job status to prevent executing this job duplicately
        job.update(Job.STATUS["PROCESSING"])

        user = User.objects.filter(id=job.user.id).first()
        entity = Entity.objects.filter(id=job.target.id, is_active=True).first()

        # for history record
        entity._history_user = user

        if not entity or not user:
            # Abort when specified entity doesn't exist
            job.update(Job.STATUS["CANCELED"])
            return

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

        # This describes job pamraeters of Job.update_es_docuemnt()
        jp_update_es_document = {
            "is_updated": True,
        }

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

                params = {
                    "name": attr["name"],
                    "refs": [int(x) for x in attr["ref_ids"]],
                    "index": attr["row_index"],
                    "is_mandatory": attr["is_mandatory"],
                    "is_delete_in_chain": attr["is_delete_in_chain"],
                }
                if attr_obj.is_updated(**params):
                    attr_obj.name = attr["name"]
                    attr_obj.is_mandatory = attr["is_mandatory"]
                    attr_obj.is_delete_in_chain = attr["is_delete_in_chain"]
                    attr_obj.index = int(attr["row_index"])

                    if attr_obj.type & AttrTypeValue["object"]:
                        # the case of an attribute that has referral entry
                        attr_obj.referral.clear()
                        attr_obj.referral.add(*[Entity.objects.get(id=x) for x in attr["ref_ids"]])

                    attr_obj.save()

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
                if int(attr["type"]) & AttrTypeValue["object"]:
                    [attr_obj.referral.add(Entity.objects.get(id=x)) for x in attr["ref_ids"]]

                # add a new attribute on the existed Entries
                entity.attrs.add(attr_obj)

                # register History to register adding EntityAttr
                history.add_attr(attr_obj)

        Job.new_update_documents(entity, "", jp_update_es_document).run()

        # This job updates elasticsearch not only Entries that are belonged to
        # the edited Entity, but also Entrie that are refered by Entry, which is
        # belonged to this Entity.
        associated_entity_ids = set()
        for attr in entity.attrs.filter(is_active=True):
            associated_entity_ids |= set([x.id for x in attr.referral.filter(is_active=True)])

        # This also update es-documents of Entries that are referred by AttributeValues
        # that are associated with deleted EntityAttrs.
        for attr_id in deleted_attr_ids:
            attr = EntityAttr.objects.filter(id=attr_id).last()
            if attr:
                associated_entity_ids |= set([x.id for x in attr.referral.filter(is_active=True)])

        # create job to update es-document that is related with edited Entity
        for related_entity_id in associated_entity_ids:
            related_entity = Entity.objects.get(id=related_entity_id)
            Job.new_update_documents(related_entity, "", jp_update_es_document).run()

        # clear flag to specify this entity has been completed to edit
        entity.del_status(Entity.STATUS_EDITING)

        # update job status and save it
        job.update(Job.STATUS["DONE"])


@app.task(bind=True)
def delete_entity(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        # At the first time, update job status to prevent executing this job duplicately
        job.update(Job.STATUS["PROCESSING"])

        user = User.objects.filter(id=job.user.id).first()
        entity = Entity.objects.filter(id=job.target.id, is_active=False).first()

        # for history record
        entity._history_user = user

        if not entity or not user:
            # Abort when specified entity doesn't exist
            job.update(Job.STATUS["CANCELED"])
            return

        entity.delete()
        history = user.seth_entity_del(entity)

        # Delete all attributes which target Entity have
        for attr in entity.attrs.all():
            attr.delete()
            history.del_attr(attr)

        # update job status and save it
        job.update(Job.STATUS["DONE"])
