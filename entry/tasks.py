import csv
import custom_view
import io
import json
import yaml

from airone.lib.acl import ACLType
from airone.lib.event_notification import notify_entry_create
from airone.lib.event_notification import notify_entry_update
from airone.lib.event_notification import notify_entry_delete
from airone.lib.job import may_schedule_until_job_is_ready
from airone.lib.log import Logger
from airone.lib.types import AttrTypeValue
from airone.celery import app
from entity.models import Entity, EntityAttr
from entry.models import Entry, Attribute
from user.models import User
from datetime import datetime
from job.models import Job


def _merge_referrals_by_index(ref_list, name_list):
    """This is a helper function to set array_named_object value.
    This re-formats data construction with index parameter of argument.
    """

    # pad None to align the length of each lists
    def be_aligned(list1, list2):
        padding_length = len(list2) - len(list1)
        if padding_length > 0:
            for i in range(0, padding_length):
                list1.append(None)

    for args in [(ref_list, name_list), (name_list, ref_list)]:
        be_aligned(*args)

    result = {}
    for ref_info, name_info in zip(ref_list, name_list):
        if ref_info:
            if ref_info["index"] not in result:
                result[ref_info["index"]] = {}
            result[ref_info["index"]]["id"] = ref_info["data"]

        if name_info:
            if name_info["index"] not in result:
                result[name_info["index"]] = {}
            result[name_info["index"]]["name"] = name_info["data"]

    return result


def _convert_data_value(attr, info):
    if attr.schema.type & AttrTypeValue["array"]:
        recv_value = []
        if "value" in info and info["value"]:
            recv_value = [x["data"] for x in info["value"] if "data" in x]

        if attr.schema.type & AttrTypeValue["named"]:
            return _merge_referrals_by_index(info["value"], info["referral_key"]).values()
        else:
            return recv_value

    else:
        recv_value = recv_ref_key = ""

        if "value" in info and info["value"] and "data" in info["value"][0]:
            recv_value = info["value"][0]["data"]
        if "referral_key" in info and info["referral_key"] and "data" in info["referral_key"][0]:
            recv_ref_key = info["referral_key"][0]["data"]

        if attr.schema.type & AttrTypeValue["named"]:
            return {
                "name": recv_ref_key,
                "id": recv_value,
            }
        elif attr.schema.type & AttrTypeValue["date"]:
            if recv_value is None or recv_value == "":
                return None
            else:
                return datetime.strptime(recv_value, "%Y-%m-%d").date()

        elif attr.schema.type & AttrTypeValue["boolean"]:
            if recv_value is None or recv_value == "":
                return False
            else:
                return recv_value

        else:
            return recv_value


def _do_import_entries(job):
    user = job.user

    entities_data = json.loads(job.params)
    if not entities_data:
        job.update(
            **{
                "status": Job.STATUS["ERROR"],
                "text": "Uploaded file has no entry data",
            }
        )
        return

    entities = Entity.objects.filter(name__in=entities_data.keys())
    for entity in entities:
        if not user.has_permission(entity, ACLType.Writable):
            job.update(
                **{
                    "status": Job.STATUS["ERROR"],
                    "text": "Permission denied to import. "
                    'You need Writable permission for "%s"' % entity.name,
                }
            )
            return

    job.update(Job.STATUS["PROCESSING"])

    # NOTE it imports all entities other than specified by job.target.id
    for entity in entities:
        # get custom_view method to prevent executing check method in every loop processing
        custom_view_handler = None
        if custom_view.is_custom("after_import_entry", entity.name):
            custom_view_handler = "after_import_entry"

        entries_data = entities_data[entity.name]
        total_count = len(entries_data)

        # create or update entry
        for (index, entry_data) in enumerate(entries_data):
            job.text = "Now importing... (progress: [%5d/%5d] for %s)" % (
                index + 1,
                total_count,
                entity.name,
            )
            job.save(update_fields=["text"])

            # abort processing when job is canceled
            if job.is_canceled():
                return

            entry = Entry.objects.filter(name=entry_data["name"], schema=entity).first()
            if not entry:
                entry = Entry.objects.create(
                    name=entry_data["name"], schema=entity, created_user=user
                )

                # create job to notify create event to the WebHook URL
                job_notify = Job.new_notify_create_entry(user, entry)

            elif not user.has_permission(entry, ACLType.Writable):
                continue

            else:
                # create job to notify edit event to the WebHook URL
                job_notify = Job.new_notify_update_entry(user, entry)

            entry.complement_attrs(user)
            for attr_name, value in entry_data["attrs"].items():
                # If user doesn't have readable permission for target Attribute,
                # it won't be created.
                if not entry.attrs.filter(schema__name=attr_name).exists():
                    continue

                # There should be only one EntityAttr that is specified by name and Entity.
                # Once there are multiple EntityAttrs, it must be an abnormal situation.
                # In that case, this aborts import processing for this entry and reports it
                # as an error.
                attr_query = entry.attrs.filter(
                    schema__name=attr_name,
                    is_active=True,
                    schema__parent_entity=entry.schema,
                )
                if attr_query.count() > 1:
                    Logger.error(
                        "[task.import_entry] Abnormal entry was detected(%s:%d)"
                        % (entry.name, entry.id)
                    )
                    break

                attr = attr_query.last()
                if not user.has_permission(
                    attr.schema, ACLType.Writable
                ) or not user.has_permission(attr, ACLType.Writable):
                    continue

                input_value = attr.convert_value_to_register(value)
                if user.has_permission(attr.schema, ACLType.Writable) and attr.is_updated(
                    input_value
                ):
                    attr.add_value(user, input_value)

                # call custom-view processing corresponding to import entry
                if custom_view_handler:
                    custom_view.call_custom(
                        custom_view_handler, entity.name, user, entry, attr, value
                    )

            # register entry to the Elasticsearch
            entry.register_es()

            # run notification job
            job_notify.run()

    if not job.is_canceled():
        job.update(status=Job.STATUS["DONE"], text="")


@app.task(bind=True)
def create_entry_attrs(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        # At the first time, update job status to prevent executing this job duplicately
        job.update(Job.STATUS["PROCESSING"])

        user = User.objects.filter(id=job.user.id).first()
        entry = Entry.objects.filter(id=job.target.id, is_active=True).first()
        if not entry or not user:
            # Abort when specified entry doesn't exist
            job.update(Job.STATUS["CANCELED"])
            return

        recv_data = json.loads(job.params)
        # Create new Attributes objects based on the specified value
        for entity_attr in entry.schema.attrs.filter(is_active=True):
            # This creates Attibute object that contains AttributeValues.
            # But the add_attribute_from_base may return None when target Attribute instance
            # has already been created or is creating by other process. In that case, this job
            # do nothing about that Attribute instance.
            attr = entry.add_attribute_from_base(entity_attr, user)

            # skip for unpermitted attributes
            if not user.has_permission(entity_attr, ACLType.Writable):
                continue

            # When job is canceled during this processing, abort it after deleting the created entry
            if job.is_canceled():
                entry.delete()
                return

            # make an initial AttributeValue object if the initial value is specified
            attr_data = [x for x in recv_data["attrs"] if int(x["id"]) == entity_attr.id]

            if not attr or not attr_data:
                continue

            # register new AttributeValue to the "attr"
            try:
                attr.add_value(user, _convert_data_value(attr, attr_data[0]))
            except ValueError as e:
                Logger.warning("(%s) attr_data: %s" % (e, str(attr_data[0])))

        # Delete duplicate attrs because this processing may execute concurrently
        for entity_attr in entry.schema.attrs.filter(is_active=True):
            if entry.attrs.filter(schema=entity_attr, is_active=True).count() > 1:
                query = entry.attrs.filter(schema=entity_attr, is_active=True)
                query.exclude(id=query.first().id).delete()

        if custom_view.is_custom("after_create_entry", entry.schema.name):
            custom_view.call_custom("after_create_entry", entry.schema.name, recv_data, user, entry)

        # register entry information to Elasticsearch
        entry.register_es()

        # clear flag to specify this entry has been completed to ndcreate
        entry.del_status(Entry.STATUS_CREATING)

        # update job status and save it except for the case that target job is canceled.
        if not job.is_canceled():
            job.update(Job.STATUS["DONE"])

            # Send notification to the webhook URL
            job_notify_event = Job.new_notify_create_entry(user, entry)
            job_notify_event.run()

    elif job.is_canceled():
        # When job is canceled before starting, created entry should be deleted.
        entry = Entry.objects.filter(id=job.target.id, is_active=True).first()
        if entry:
            entry.delete()


@app.task(bind=True)
def edit_entry_attrs(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        # At the first time, update job status to prevent executing this job duplicately
        job.update(Job.STATUS["PROCESSING"])

        user = User.objects.get(id=job.user.id)
        entry = Entry.objects.get(id=job.target.id)

        recv_data = json.loads(job.params)

        for info in recv_data["attrs"]:
            if info["id"]:
                attr = Attribute.objects.get(id=info["id"])
            else:
                entity_attr = EntityAttr.objects.get(id=info["entity_attr_id"])
                attr = entry.attrs.filter(schema=entity_attr, is_active=True).first()
                if not attr:
                    attr = entry.add_attribute_from_base(entity_attr, user)

            try:
                converted_value = _convert_data_value(attr, info)
            except ValueError as e:
                Logger.warning("(%s) attr_data: %s" % (e, str(info)))
                continue

            # Check a new update value is specified, or not
            if not attr.is_updated(converted_value):
                continue

            # Add new AttributeValue instance to Attribute instnace
            attr.add_value(user, converted_value)

        if custom_view.is_custom("after_edit_entry", entry.schema.name):
            custom_view.call_custom("after_edit_entry", entry.schema.name, recv_data, user, entry)

        # update entry information to Elasticsearch
        entry.register_es()

        # clear flag to specify this entry has been completed to edit
        entry.del_status(Entry.STATUS_EDITING)

        # update job status and save it
        job.update(Job.STATUS["DONE"])

        # running job to notify changing entry event
        job_notify_event = Job.new_notify_update_entry(user, entry)
        job_notify_event.run()


@app.task(bind=True)
def delete_entry(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        job.update(Job.STATUS["PROCESSING"])

        entry = Entry.objects.get(id=job.target.id)
        entry.delete()

        user = User.objects.get(id=job.user.id)
        if custom_view.is_custom("after_delete_entry", entry.schema.name):
            custom_view.call_custom("after_delete_entry", entry.schema.name, user, entry)

        # update job status and save it
        job.update(Job.STATUS["DONE"])


@app.task(bind=True)
def restore_entry(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        job.update(Job.STATUS["PROCESSING"])

        entry = Entry.objects.get(id=job.target.id)
        entry.restore()

        # remove status flag which is set before calling this
        entry.del_status(Entry.STATUS_CREATING)

        # Send notification to the webhook URL
        job_notify = Job.new_notify_create_entry(job.user, entry)
        job_notify.run()

        # calling custom view processing if necessary
        if custom_view.is_custom("after_restore_entry", entry.schema.name):
            custom_view.call_custom("after_restore_entry", entry.schema.name, job.user, entry)

        # update job status and save it
        job.update(Job.STATUS["DONE"])


@app.task(bind=True)
def copy_entry(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        # update job status
        job.update(Job.STATUS["PROCESSING"])

        user = User.objects.get(id=job.user.id)
        src_entry = Entry.objects.get(id=job.target.id)

        params = json.loads(job.params)
        total_count = len(params["new_name_list"])
        for (index, new_name) in enumerate(params["new_name_list"]):
            # abort processing when job is canceled
            if job.is_canceled():
                job.text = "Copy completed [%5d/%5d]" % (index, total_count)
                job.save(update_fields=["text"])
                return

            job.text = "Now copying... (progress: [%5d/%5d])" % (index + 1, total_count)
            job.save(update_fields=["text"])

            params["new_name"] = new_name
            job_do_copy_entry = Job.new_do_copy(user, src_entry, new_name, params)
            job_do_copy_entry.run(will_delay=False)

        # update job status and save it
        job.update(
            status=Job.STATUS["DONE"],
            text="Copy completed [%5d/%5d]" % (total_count, total_count),
        )


@app.task(bind=True)
def do_copy_entry(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        # update job status
        job.update(Job.STATUS["PROCESSING"])

        user = User.objects.get(id=job.user.id)
        src_entry = Entry.objects.get(id=job.target.id)

        params = json.loads(job.params)
        dest_entry = Entry.objects.filter(schema=src_entry.schema, name=params["new_name"]).first()
        if not dest_entry:
            dest_entry = src_entry.clone(user, name=params["new_name"])
            dest_entry.register_es()

        if custom_view.is_custom("after_copy_entry", src_entry.schema.name):
            custom_view.call_custom(
                "after_copy_entry",
                src_entry.schema.name,
                user,
                src_entry,
                dest_entry,
                params["post_data"],
            )

        # update job status and save it
        job.update(Job.STATUS["DONE"], "original entry: %s" % src_entry.name, dest_entry)

        # create and run event notification job
        job_notify_event = Job.new_notify_create_entry(user, dest_entry)
        job_notify_event.run()


@app.task(bind=True)
def import_entries(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        try:
            _do_import_entries(job)
        except Exception as e:
            job.update(
                status=Job.STATUS["ERROR"],
                text="[task.import] [job:%d] %s" % (job.id, str(e)),
            )


@app.task(bind=True)
def export_entries(self, job_id):
    job = Job.objects.get(id=job_id)

    if not job.proceed_if_ready():
        return

    job.update(Job.STATUS["PROCESSING"])

    user = job.user
    entity = Entity.objects.get(id=job.target.id)
    params = json.loads(job.params)

    exported_data = []

    # This variable is used for job status check. When it's checked at every loop, this might send
    # tons of query to the database. To prevent the sort of tragedy situation, checking status of
    # this job should be skipped some times (which is specified in Job.STATUS_CHECK_FREQUENCY).
    #
    # NOTE:
    #   This doesn't use enumerate() method to count loop. Because when a QuerySet value is
    #   passed to the argument of enumerate() method, Django try to get result at once (this never
    #   do lazy evaluation).
    export_item_counter = 0
    for entry in Entry.objects.filter(schema=entity, is_active=True):
        # abort processing when job is canceled
        if export_item_counter % Job.STATUS_CHECK_FREQUENCY == 0 and job.is_canceled():
            return

        if user.has_permission(entry, ACLType.Readable):
            exported_data.append(entry.export(user))

        # increment loop counter
        export_item_counter += 1

    output = None
    if params["export_format"] == "csv":
        # newline is blank because csv module performs universal newlines
        # https://docs.python.org/ja/3/library/csv.html#id3
        output = io.StringIO(newline="")
        writer = csv.writer(output)

        attrs = [x.name for x in entity.attrs.filter(is_active=True)]
        writer.writerow(["Name"] + attrs)

        def data2str(data):
            if not data:
                return ""
            return str(data)

        for data in exported_data:
            writer.writerow(
                [data["name"]] + [data2str(data["attrs"][x]) for x in attrs if x in data["attrs"]]
            )
    else:
        output = io.StringIO()
        output.write(
            yaml.dump(
                {entity.name: exported_data},
                default_flow_style=False,
                allow_unicode=True,
            )
        )

    if output:
        job.set_cache(output.getvalue())

    # update job status and save it except for the case that target job is canceled.
    if not job.is_canceled():
        job.update(Job.STATUS["DONE"])


@app.task(bind=True)
def register_referrals(self, job_id):
    job = Job.objects.get(id=job_id)

    # The python client for elasticsearch is thread safe, so this start processing
    # without waiting any other jobs.
    job.update(Job.STATUS["PROCESSING"])

    # register entries data which refer target entry to elasticsearch
    entry = Entry.objects.filter(id=job.target.id, is_active=True).first()
    if entry:
        [r.register_es() for r in entry.get_referred_objects()]

    if not job.is_canceled():
        job.update(Job.STATUS["DONE"])


def _notify_event(notification_method, object_id, user):
    entry = Entry.objects.filter(id=object_id).first()
    if not entry:
        return (Job.STATUS["ERROR"], "Failed to get job.target (%s)" % object_id)

    try:
        notification_method(entry, user)

    except Exception as e:
        return (Job.STATUS["ERROR"], str(e))


@app.task(bind=True)
@may_schedule_until_job_is_ready
def notify_create_entry(self, job):
    return _notify_event(notify_entry_create, job.target.id, job.user)


@app.task(bind=True)
@may_schedule_until_job_is_ready
def notify_update_entry(self, job):
    return _notify_event(notify_entry_update, job.target.id, job.user)


@app.task(bind=True)
@may_schedule_until_job_is_ready
def notify_delete_entry(self, job):
    return _notify_event(notify_entry_delete, job.target.id, job.user)
