import csv
import io
import json
from datetime import date, datetime
from typing import Any, Callable, List, TypeAlias

import yaml
from celery import Task
from django.conf import settings
from rest_framework.exceptions import ValidationError

from acl.models import ACLBase
from airone.celery import app
from airone.lib import custom_view
from airone.lib.acl import ACLType
from airone.lib.elasticsearch import (
    AdvancedSearchResultRecord,
    AdvancedSearchResultRecordAttr,
    AttrHint,
    EntryHint,
)
from airone.lib.event_notification import (
    notify_entry_create,
    notify_entry_delete,
    notify_entry_update,
)
from airone.lib.http import DRFRequest
from airone.lib.import_preview import PreviewCollector
from airone.lib.job import (
    may_schedule_until_job_is_ready,
    may_schedule_until_job_is_ready_with_handlers,
    register_job_task,
)
from airone.lib.log import Logger
from airone.lib.types import AttrType
from dashboard.tasks import _csv_export
from entity.models import Entity, EntityAttr
from entry.api_v2.serializers import (
    AdvancedSearchJoinAttrInfoList,
    AdvancedSearchResultExportSerializer,
    EntryCreateSerializer,
    EntryImportEntitySerializer,
    EntryUpdateSerializer,
    ExportedEntityEntries,
    ExportedEntry,
    ExportedEntryAttribute,
    ExportedEntryAttributePrimitiveValue,
    ExportedEntryAttributeValue,
    ExportedEntryAttributeValueObject,
    ExportTaskParams,
    ReferralEntry,
)
from entry.models import Attribute, Entry
from entry.services import AdvancedSearchService
from group.models import Group
from job.models import Job, JobOperation, JobStatus, JobTarget
from role.models import Role
from trigger.models import TriggerCondition
from user.models import User

# A single pre-serialization attribute value handed to the YAML exporter: an
# object/named-object dict, a scalar, or None. Array values are unwrapped one
# level up (in _get_attr_value) before reaching the primitive helper.
ExportPrimitiveInput: TypeAlias = dict[str, Any] | str | int | float | date | datetime | bool | None


def _merge_referrals_by_index(
    ref_list: list[dict[str, Any]], name_list: list[dict[str, Any]]
) -> dict[int, dict[str, Any]]:
    """This is a helper function to set array_named_object value.
    This re-formats data construction with index parameter of argument.
    """

    # pad None to align the length of each lists
    def be_aligned(list1: list[Any], list2: list[Any]) -> None:
        padding_length = len(list2) - len(list1)
        if padding_length > 0:
            list1.extend([None] * padding_length)

    for args in [(ref_list, name_list), (name_list, ref_list)]:
        be_aligned(*args)

    result: dict[int, dict[str, Any]] = {}
    for ref_info, name_info in zip(ref_list, name_list):
        if ref_info:
            index = ref_info["index"]
            if index not in result:
                result[index] = {}
            result[index]["id"] = ref_info["data"]

        if name_info:
            index = name_info["index"]
            if index not in result:
                result[index] = {}
            result[index]["name"] = name_info["data"]

    return result


def _convert_data_value(attr: Attribute, info: dict[str, Any]) -> Any:
    if attr.is_array():
        recv_value: Any = []
        if "value" in info and info["value"]:
            recv_value = [x["data"] for x in info["value"] if "data" in x]

        if attr.schema.type & AttrType._NAMED:
            return _merge_referrals_by_index(info["value"], info["referral_key"]).values()
        else:
            return recv_value

    else:
        recv_value = recv_ref_key = ""

        if "value" in info and info["value"] and "data" in info["value"][0]:
            recv_value = info["value"][0]["data"]
        if "referral_key" in info and info["referral_key"] and "data" in info["referral_key"][0]:
            recv_ref_key = info["referral_key"][0]["data"]

        match attr.schema.type:
            case AttrType.NAMED_OBJECT | AttrType.ARRAY_NAMED_OBJECT:
                return {
                    "name": recv_ref_key,
                    "id": recv_value,
                }
            case AttrType.DATE:
                if recv_value is None or recv_value == "":
                    return None
                else:
                    return datetime.strptime(recv_value, "%Y-%m-%d").date()
            case AttrType.BOOLEAN:
                if recv_value is None or recv_value == "":
                    return False
                else:
                    return recv_value
            case AttrType.DATETIME:
                if recv_value is None or recv_value == "":
                    return None
                else:
                    return datetime.fromisoformat(recv_value)
            case AttrType.NUMBER:
                if recv_value is None or recv_value == "":
                    return None
                else:
                    try:
                        return float(recv_value)
                    except (ValueError, TypeError):
                        return None
            case _:
                return recv_value


def _do_import_entries(job: Job) -> None:
    user: User = job.user
    entity: Entity = Entity.objects.get(id=job.target.id)
    import_data = json.loads(job.params)

    # get custom_view method to prevent executing check method in every loop processing
    custom_view_handler = None
    if custom_view.is_custom("after_import_entry", entity.name):
        custom_view_handler = "after_import_entry"

    total_count = len(import_data)

    # create or update entry
    for index, entry_data in enumerate(import_data):
        job_notify: Job | None = None
        job.text = "Now importing... (progress: [%5d/%5d] for %s)" % (
            index + 1,
            total_count,
            entity.name,
        )
        job.save(update_fields=["text"])

        # abort processing when job is canceled
        if job.is_canceled():
            return

        entry: Entry = Entry.objects.filter(name=entry_data["name"], schema=entity).first()
        if not entry:
            # skip to create Item when another duplicated Alias exists
            if not entity.is_available(entry_data["name"]):
                continue

            entry = Entry(name=entry_data["name"], schema=entity, created_user=user)

            # for history record
            entry._history_user = user

            entry.save()

            # create job to notify create event to the WebHook URL
            job_notify = Job.new_notify_create_entry(user, entry)

        else:
            # for history record
            entry._history_user = user

        if not user.has_permission(entry, ACLType.Writable):
            continue

        entry.complement_attrs(user)
        is_update: bool = False
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

            attr: Attribute = attr_query.last()
            if not user.has_permission(attr.schema, ACLType.Writable) or not user.has_permission(
                attr, ACLType.Writable
            ):
                continue

            input_value = attr.convert_value_to_register(value)
            if user.has_permission(attr.schema, ACLType.Writable) and attr.is_updated(input_value):
                try:
                    attr.add_value(user, input_value)
                except TypeError as e:
                    # add_value raises TypeError when the value fails attr-specific
                    # validation (e.g. SELECT choice not in EntityAttr.choices).
                    # Skip this single attribute and continue importing the rest of
                    # the row / file instead of aborting the whole job.
                    Logger.warning(
                        "[task.import_entry] Skipped attr '%s' on entry '%s': %s"
                        % (attr_name, entry.name, e)
                    )
                    continue
                is_update = True

            # call custom-view processing corresponding to import entry
            if custom_view_handler:
                custom_view.call_custom(custom_view_handler, entity.name, user, entry, attr, value)

        # Create job for TriggerAction
        Job.new_invoke_trigger(
            user, entry, entry.get_trigger_params(user, entry_data["attrs"].keys())
        ).run()

        if not job_notify and is_update:
            job_notify = Job.new_notify_update_entry(user, entry)

        if job_notify:
            # register entry to the Elasticsearch
            entry.register_es()

            # run notification job
            job_notify.run()

    job.update(status=JobStatus.DONE, text="")


def _yaml_export_v2(
    job: Job,
    values: list[AdvancedSearchResultRecord],
    recv_data: dict[str, Any],
    has_referral: bool,
) -> io.StringIO | None:
    def _get_attr_primitive_value(
        atype: int, value: ExportPrimitiveInput
    ) -> ExportedEntryAttributePrimitiveValue:
        match atype:
            case AttrType.NAMED_OBJECT | AttrType.NAMED_OBJECT_BOOLEAN:
                assert isinstance(value, dict)
                [(key, val)] = value.items()
                # NAMED_OBJECT_BOOLEAN carries its boolean flag beside the referral
                # info, so export it too in order to keep the value round-trippable.
                boolean_info = (
                    {"boolean": val["boolean"]}
                    if atype == AttrType.NAMED_OBJECT_BOOLEAN
                    and isinstance(val, dict)
                    and "boolean" in val
                    else {}
                )
                entry: Entry | None = (
                    Entry.objects.filter(id=val["id"]).first()
                    if isinstance(val, dict) and isinstance(val.get("id"), int)
                    else None
                )
                if entry:
                    return {
                        key: ExportedEntryAttributeValueObject(
                            entity=entry.schema.name,
                            name=val["name"],
                            **boolean_info,
                        )
                    }
                elif len(key) > 0:
                    return {
                        key: None,
                    }
                else:
                    return {}

            case AttrType.OBJECT:
                assert isinstance(value, dict)
                entry = (
                    Entry.objects.filter(id=value["id"]).first()
                    if isinstance(value.get("id"), int)
                    else None
                )
                if entry:
                    return ExportedEntryAttributeValueObject(
                        entity=entry.schema.name,
                        name=value["name"],
                    )
                else:
                    return None

            case AttrType.GROUP:
                assert isinstance(value, dict)
                if (
                    isinstance(value.get("id"), int)
                    and Group.objects.filter(id=value["id"]).exists()
                ):
                    return value["name"]
                else:
                    return None

            case AttrType.ROLE:
                assert isinstance(value, dict)
                if (
                    isinstance(value.get("id"), int)
                    and Role.objects.filter(id=value["id"]).exists()
                ):
                    return value["name"]
                else:
                    return None

            case AttrType.SELECT:
                # SELECT value comes as {"value": ..., "label": ...}.
                # Export the immutable `value` (not the label) so re-import is
                # safe across schema label edits.
                if isinstance(value, dict):
                    return value.get("value")
                return value

            case _:
                assert not isinstance(value, dict)
                return value

    def _get_attr_value(
        atype: int, value: ExportPrimitiveInput | list[Any]
    ) -> ExportedEntryAttributeValue:
        match atype:
            case _ if atype & AttrType._ARRAY:
                assert isinstance(value, list)
                return [_get_attr_primitive_value(atype ^ AttrType._ARRAY, x) for x in value]
            case _:
                assert not isinstance(value, list)
                return _get_attr_primitive_value(atype, value)

    resp_data: List[ExportedEntityEntries] = []
    for index, entry_info in enumerate(values):
        data = ExportedEntry(
            id=entry_info.entry["id"],
            name=entry_info.entry["name"],
            attrs=[],
        )

        # Abort processing when job is canceled
        if index % Job.STATUS_CHECK_FREQUENCY == 0 and job.is_canceled():
            return None

        for attrinfo in recv_data["attrinfo"]:
            if attrinfo["name"] in entry_info.attrs:
                _adata = entry_info.attrs[attrinfo["name"]]
                if "value" not in _adata:
                    continue

                data.attrs.append(
                    ExportedEntryAttribute(
                        name=attrinfo["name"],
                        value=_get_attr_value(_adata["type"], _adata["value"]),
                    )
                )

        if has_referral is not False:
            data.referrals = [
                ReferralEntry(
                    entity=x["schema"]["name"],
                    entry=x["name"],
                )
                for x in entry_info.referrals or []
            ]

        found = next(filter(lambda x: x.entity == entry_info.entity["name"], resp_data), None)
        if found:
            found.entries.append(data)
        else:
            resp_data.append(
                ExportedEntityEntries(
                    entity=entry_info.entity["name"],
                    entries=[data],
                )
            )

    output = io.StringIO()
    output.write(
        yaml.dump(
            [x.dict(exclude_unset=True) for x in resp_data],
            default_flow_style=False,
            allow_unicode=True,
        )
    )

    return output


@register_job_task(JobOperation.CREATE_ENTRY)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready_with_handlers(
    on_cancelled=lambda job: (
        Entry.objects.filter(id=job.target.id, is_active=True).first().delete()
        if Entry.objects.filter(id=job.target.id, is_active=True).exists()
        else None
    )
)
def create_entry_attrs(self: Task, job: Job) -> JobStatus | None:
    user = User.objects.filter(id=job.user.id).first()
    entry = Entry.objects.filter(id=job.target.id, is_active=True).first()

    # for history record
    entry._history_user = user

    if not entry or not user:
        # Abort when specified entry doesn't exist
        return JobStatus.CANCELED

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
            return None

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
        # Send notification to the webhook URL
        job_notify_event = Job.new_notify_create_entry(user, entry)
        job_notify_event.run()

    return JobStatus.DONE


@register_job_task(JobOperation.EDIT_ENTRY)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def edit_entry_attrs(self: Task, job: Job) -> JobStatus:
    user = User.objects.get(id=job.user.id)
    entry = Entry.objects.get(id=job.target.id)

    # for history record
    entry._history_user = user

    recv_data = json.loads(job.params)

    for info in recv_data["attrs"]:
        if info["id"]:
            attr = Attribute.objects.get(id=info["id"])
        else:
            entity_attr = EntityAttr.objects.get(id=info["entity_attr_id"])
            attr = entry.attrs.filter(schema=entity_attr, is_active=True).first()
            if not attr:
                attr = entry.add_attribute_from_base(entity_attr, user)

        # check permission of EntityAttr
        if not user.has_permission(attr, ACLType.Writable):
            continue

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

    # running job to notify changing entry event
    job_notify_event = Job.new_notify_update_entry(user, entry)
    job_notify_event.run()

    return JobStatus.DONE


@register_job_task(JobOperation.DELETE_ENTRY)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def delete_entry(self: Task, job: Job) -> JobStatus:
    entry = Entry.objects.get(id=job.target.id)

    # for history record
    entry._history_user = job.user

    entry.delete(deleted_user=job.user)

    for ref_entry, actions in TriggerCondition.get_invoked_actions_on_delete(entry):
        for action in actions:
            action.run(job.user, ref_entry)

    if custom_view.is_custom("after_delete_entry", entry.schema.name):
        custom_view.call_custom("after_delete_entry", entry.schema.name, job.user, entry)

    return JobStatus.DONE


@register_job_task(JobOperation.RESTORE_ENTRY)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def restore_entry(self: Task, job: Job) -> JobStatus:
    entry = Entry.objects.get(id=job.target.id)

    # for history record
    entry._history_user = job.user

    entry.restore()

    # remove status flag which is set before calling this
    entry.del_status(Entry.STATUS_CREATING)

    # Send notification to the webhook URL
    job_notify = Job.new_notify_create_entry(job.user, entry)
    job_notify.run()

    # calling custom view processing if necessary
    if custom_view.is_custom("after_restore_entry", entry.schema.name):
        custom_view.call_custom("after_restore_entry", entry.schema.name, job.user, entry)

    return JobStatus.DONE


@register_job_task(JobOperation.COPY_ENTRY)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def copy_entry(self: Task, job: Job) -> tuple[JobStatus, str, None] | None:
    src_entry = Entry.objects.get(id=job.target.id)

    params = json.loads(job.params)
    total_count = len(params["new_name_list"])
    for index, new_name in enumerate(params["new_name_list"]):
        # abort processing when job is canceled
        if job.is_canceled():
            job.text = "Copy completed [%5d/%5d]" % (index, total_count)
            job.save(update_fields=["text"])
            return None

        job.text = "Now copying... (progress: [%5d/%5d])" % (index + 1, total_count)
        job.save(update_fields=["text"])

        params["new_name"] = new_name
        job_do_copy_entry = Job.new_do_copy(job.user, src_entry, new_name, params)
        job_do_copy_entry.run(will_delay=False)

    # update job status and save it
    return JobStatus.DONE, "Copy completed [%5d/%5d]" % (total_count, total_count), None


@register_job_task(JobOperation.DO_COPY_ENTRY)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def do_copy_entry(self: Task, job: Job) -> tuple[JobStatus, str, None]:
    src_entry = Entry.objects.get(id=job.target.id)
    params = json.loads(job.params)

    # abort this job when there is duplicated Alias exists
    if not src_entry.schema.is_available(params["new_name"]):
        return (
            JobStatus.ERROR,
            "Duplicated Alias(name=%s) exists in this model" % params["new_name"],
            src_entry,
        )

    dest_entry = Entry.objects.filter(schema=src_entry.schema, name=params["new_name"]).first()
    if not dest_entry:
        dest_entry = src_entry.clone(job.user, name=params["new_name"])

        # for updating its name from attribute values
        dest_entry.save_autoname()

        # update item name pj
        dest_entry.register_es()

    if custom_view.is_custom("after_copy_entry", src_entry.schema.name):
        custom_view.call_custom(
            "after_copy_entry",
            src_entry.schema.name,
            job.user,
            src_entry,
            dest_entry,
            params["post_data"],
        )

    # create and run event notification job
    job_notify_event = Job.new_notify_create_entry(job.user, dest_entry)
    job_notify_event.run()

    return JobStatus.DONE, "original entry: %s" % src_entry.name, dest_entry


@register_job_task(JobOperation.IMPORT_ENTRY)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def import_entries(self: Task, job: Job) -> tuple[JobStatus, str, None] | None:
    try:
        _do_import_entries(job)
    except Exception as e:
        return JobStatus.ERROR, "[task.import] [job:%d] %s" % (job.id, str(e)), None

    return None


@register_job_task(JobOperation.IMPORT_ENTRY_V2)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def import_entries_v2(self: Task, job: Job) -> tuple[JobStatus, str, None] | None:
    user: User = job.user
    entity = Entity.objects.get(id=job.target.id)
    import_serializer = EntryImportEntitySerializer(data=json.loads(job.params))
    import_serializer.is_valid()
    context = {"request": DRFRequest(user)}

    total_count = len(import_serializer.validated_data["entries"])
    err_msg: list[str] = []
    stale: list[str] = []
    baselines = _load_preview_baselines(job)
    for index, entry_data in enumerate(import_serializer.validated_data["entries"]):
        job.text = "Now importing... (progress: [%5d/%5d])" % (index + 1, total_count)
        job.save(update_fields=["text"])

        # abort processing when job is canceled
        if job.is_canceled():
            job.status = JobStatus.CANCELED
            job.save(update_fields=["status"])
            return None

        entry_data["schema"] = entity

        # Identify the Item to be updated
        entry: Entry | None = None
        if entry_data.get("id") is not None:
            entry = Entry.objects.filter(id=entry_data["id"], schema=entity, is_active=True).first()

        if not entry:
            entry = Entry.objects.filter(
                name=entry_data["name"], schema=entity, is_active=True
            ).first()

        if entry and _is_stale(entry, entry_data, baselines):
            # Someone changed this item after the preview was built, so the
            # preview the user approved no longer describes what would happen.
            stale.append(entry_data["name"])
            continue

        if entry:
            serializer = EntryUpdateSerializer(instance=entry, data=entry_data, context=context)
        else:
            serializer = EntryCreateSerializer(data=entry_data, context=context)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ValidationError as e:
            err_msg.append(entry_data["name"])
            Logger.warning(
                "failed to validate on entry import v2: entry=%s, error=%s"
                % (entry_data["name"], e)
            )

    if err_msg or stale:
        text = "Imported Entry count: %d" % total_count
        if err_msg:
            text += ", Failed import Entry: %s" % err_msg
        if stale:
            text += ", Changed by someone else since the preview: %s" % stale
        return (JobStatus.WARNING, text, None)
    else:
        return JobStatus.DONE, "Imported Entry count: %d" % total_count, None


def _load_preview_baselines(job: Job) -> dict[str, dict[str, Any]] | None:
    """Read the values a preview recorded, when the import was started from one.

    Without a preview job there is nothing to compare against and the import
    behaves exactly as it always has.
    """
    preview_job_id = json.loads(job.params).get("preview_job_id")
    if not preview_job_id:
        return None

    preview_job = Job.objects.filter(
        id=preview_job_id, user=job.user, operation=JobOperation.IMPORT_ENTRY_PREVIEW
    ).first()
    if preview_job is None or preview_job.status != JobStatus.DONE:
        return None

    try:
        payload = preview_job.get_cache()
    except OSError:
        return None

    return {row["name"]: row["baseline"] for row in payload["rows"] if row.get("baseline")}


def _is_stale(
    entry: Entry, entry_data: dict[str, Any], baselines: dict[str, dict[str, Any]] | None
) -> bool:
    if baselines is None:
        return False

    baseline = baselines.get(entry_data["name"])
    if baseline is None or baseline["entry_id"] != entry.id:
        return False

    current = _latest_value_ids(entry, [int(x["id"]) for x in entry_data.get("attrs", [])])
    return current != baseline["values"]


@register_job_task(JobOperation.EXPORT_ENTRY)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def export_entries(self: Task, job: Job) -> None:
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
        # Use LF as the row terminator to match the LF used when joining array
        # values; mixing CRLF terminators with bare-LF cell separators makes
        # editors render the row-terminating CR as a stray ^M control character.
        writer = csv.writer(output, lineterminator="\n")

        attrs = [x.name for x in entity.attrs.filter(is_active=True)]
        writer.writerow(["Name"] + attrs)

        def data2str(data: Any | None) -> str:
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


@register_job_task(JobOperation.EXPORT_ENTRY_V2)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def export_entries_v2(self: Task, job: Job) -> None:
    user = job.user
    entity = Entity.objects.get(id=job.target.id)
    params = ExportTaskParams.model_validate_json(job.params)
    with_entity = params.export_format != "csv"

    exported_entity: list[ExportedEntityEntries] = []
    exported_entries: list[ExportedEntry] = []

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
            exported_entries.append(entry.export_v2(user, with_entity=with_entity))

        # increment loop counter
        export_item_counter += 1

    exported_entity.append(ExportedEntityEntries(entity=entity.name, entries=exported_entries))

    output = None
    if params.export_format == "csv":
        # newline is blank because csv module performs universal newlines
        # https://docs.python.org/ja/3/library/csv.html#id3
        output = io.StringIO(newline="")
        # Use LF as the row terminator to match the LF used when joining array
        # values; mixing CRLF terminators with bare-LF cell separators makes
        # editors render the row-terminating CR as a stray ^M control character.
        writer = csv.writer(output, lineterminator="\n")

        attrs = [x.name for x in entity.attrs.filter(is_active=True).order_by("index")]
        writer.writerow(["Name"] + attrs)

        def data2str(data: ExportedEntryAttributeValue | None) -> str:
            if not data:
                return ""
            return str(data)

        for data in exported_entity[0].entries:
            writer.writerow(
                [data.name] + [data2str(x.value) for x in data.attrs if x.name in attrs]
            )
    else:
        output = io.StringIO()
        output.write(
            yaml.dump(
                [x.dict(exclude_unset=True) for x in exported_entity],
                default_flow_style=False,
                allow_unicode=True,
            )
        )

    if output:
        job.set_cache(output.getvalue())


def _csv_export_v2(
    job: Job,
    values: list[AdvancedSearchResultRecord],
    recv_data: dict[str, Any],
    has_referral: bool,
) -> io.StringIO | None:
    """CSV export for v2. No Entity column; adds sub-attribute columns from join_attrs."""
    output = io.StringIO(newline="")
    # Use LF as the row terminator to match the LF used when joining array
    # values; mixing CRLF terminators with bare-LF cell separators makes
    # editors render the row-terminating CR as a stray ^M control character.
    writer = csv.writer(output, lineterminator="\n")

    join_attrs = recv_data.get("join_attrs", [])
    join_attr_col_names = [attr["name"] for jattr in join_attrs for attr in jattr["attrinfo"]]

    writer.writerow(["Name"] + [x["name"] for x in recv_data["attrinfo"]] + join_attr_col_names)

    def _format_value(value: AdvancedSearchResultRecordAttr) -> str:
        if not value or "value" not in value or value["value"] is None:
            return ""
        vtype = value.get("type")
        vval = value["value"]
        match vtype:
            case (
                AttrType.STRING
                | AttrType.TEXT
                | AttrType.BOOLEAN
                | AttrType.DATE
                | AttrType.DATETIME
                | AttrType.NUMBER
            ):
                return str(vval)
            case AttrType.OBJECT | AttrType.GROUP | AttrType.ROLE:
                return str(vval["name"])
            case AttrType.NAMED_OBJECT | AttrType.NAMED_OBJECT_BOOLEAN:
                [(k, v)] = vval.items()
                return f"{k}: {v['name']}" if isinstance(v, dict) else f"{k}: "
            case AttrType.SELECT:
                if isinstance(vval, dict):
                    return str(vval.get("label", ""))
                return ""
            case AttrType.ARRAY_STRING:
                from natsort import natsorted

                return "\n".join(natsorted(vval))
            case AttrType.ARRAY_NUMBER:
                from natsort import natsorted

                return "\n".join(natsorted([str(x) if x is not None else "" for x in vval]))
            case AttrType.MULTI_SELECT:
                from natsort import natsorted

                labels = [str(x.get("label", "")) for x in vval if isinstance(x, dict)]
                return "\n".join(natsorted(labels))
            case AttrType.ARRAY_OBJECT | AttrType.ARRAY_GROUP | AttrType.ARRAY_ROLE:
                from natsort import natsorted

                return "\n".join(natsorted([x["name"] for x in vval]))
            case AttrType.ARRAY_NAMED_OBJECT | AttrType.ARRAY_NAMED_OBJECT_BOOLEAN:
                from natsort import natsorted

                items = []
                for vset in vval:
                    [(k, v)] = vset.items()
                    items.append(f"{k}: {v['name']}" if isinstance(v, dict) else f"{k}: ")
                return "\n".join(natsorted(items))
        return ""

    for index, entry_info in enumerate(values):
        if index % Job.STATUS_CHECK_FREQUENCY == 0 and job.is_canceled():
            return None

        line_data = [entry_info.entry["name"]]

        for attrinfo in recv_data["attrinfo"]:
            value = entry_info.attrs.get(attrinfo["name"])
            line_data.append(_format_value(value) if value else "")

        for jattr in join_attrs:
            for attr in jattr["attrinfo"]:
                col_key = f"{jattr['name']}.{attr['name']}"
                value = entry_info.attrs.get(col_key)
                line_data.append(_format_value(value) if value else "")

        writer.writerow(line_data)

    return output


@register_job_task(JobOperation.EXPORT_SEARCH_RESULT_V2)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def export_search_result_v2(self: Any, job: Job) -> tuple[JobStatus, str, ACLBase | None] | None:
    user = job.user
    serializer = AdvancedSearchResultExportSerializer(data=json.loads(job.params))
    serializer.is_valid(raise_exception=True)
    params: dict[str, Any] = serializer.validated_data
    join_attrs = params.get("join_attrs", [])

    has_referral: bool = params.get("has_referral", False)
    referral_name: str | None = params.get("referral_name")

    if has_referral and referral_name is None:
        referral_name = ""

    if not isinstance(params["attrinfo"], list):
        return JobStatus.ERROR, "Invalid attrinfo", None

    try:
        hint_attrs = [AttrHint.model_validate(x) for x in params["attrinfo"]]
    except ValidationError:
        return JobStatus.ERROR, "Invalid attrinfo", None

    hint_entry_raw = serializer.validated_data.get("hint_entry")
    hint_entry: EntryHint | None = None
    if hint_entry_raw and (
        hint_entry_raw.get("filter_key") is not None or hint_entry_raw.get("keyword")
    ):
        hint_entry = EntryHint(
            keyword=hint_entry_raw.get("keyword"),
            filter_key=hint_entry_raw.get("filter_key"),
        )

    resp = AdvancedSearchService.search_entries(
        user,
        params["entities"],
        hint_attrs,
        settings.ES_CONFIG["MAXIMUM_RESULTS_NUM"],
        entry_name=None,
        hint_referral=referral_name,
        is_output_all=False,
        hint_referral_entity_id=None,
        offset=0,
        hint_entry=hint_entry,
    )

    # Apply join_attrs in the same way as AdvancedSearchAPI.post() in views.py
    join_attr_objects = AdvancedSearchJoinAttrInfoList.model_validate(join_attrs).root
    resp = AdvancedSearchService.apply_join_attrs(
        user,
        resp,
        join_attr_objects,
    )

    output: io.StringIO | None = None
    match params["export_style"]:
        case "yaml":
            output = _yaml_export_v2(job, resp.ret_values, params, has_referral)
        case "csv":
            # Use v2 format (no Entity column, with sub-attribute columns)
            # when join_attrs is specified.
            if join_attrs:
                output = _csv_export_v2(job, resp.ret_values, params, has_referral)
            else:
                output = _csv_export(job, resp.ret_values, params, has_referral)

    if output:
        job.set_cache(output.getvalue())

    return None


@register_job_task(JobOperation.REGISTER_REFERRALS)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def register_referrals(self: Task, job: Job) -> None:
    # register entries data which refer target entry to elasticsearch
    entry = Entry.objects.filter(id=job.target.id, is_active=True).first()
    if entry:
        [r.register_es() for r in entry.get_referred_objects()]


def _notify_event(
    notification_method: Callable[[Entry, User], None], object_id: int, user: User
) -> tuple[JobStatus, str, None] | None:
    entry = Entry.objects.filter(id=object_id).first()
    if not entry:
        return JobStatus.ERROR, "Failed to get job.target (%s)" % object_id, None

    try:
        notification_method(entry, user)
        return None
    except Exception as e:
        return JobStatus.ERROR, str(e), None


@register_job_task(JobOperation.UPDATE_DOCUMENT)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def update_es_documents(self: Task, job: Job) -> JobStatus:
    params = json.loads(job.params)

    entity = Entity.objects.get(id=job.target.id)
    AdvancedSearchService.update_documents(entity, params.get("is_update", False))

    return JobStatus.DONE


@register_job_task(JobOperation.NOTIFY_CREATE_ENTRY)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def notify_create_entry(self: Task, job: Job) -> tuple[JobStatus, str, None] | None:
    return _notify_event(notify_entry_create, job.target.id, job.user)


@register_job_task(JobOperation.NOTIFY_UPDATE_ENTRY)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def notify_update_entry(self: Task, job: Job) -> tuple[JobStatus, str, None] | None:
    return _notify_event(notify_entry_update, job.target.id, job.user)


@register_job_task(JobOperation.NOTIFY_DELETE_ENTRY)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def notify_delete_entry(self: Task, job: Job) -> tuple[JobStatus, str, None] | None:
    return _notify_event(notify_entry_delete, job.target.id, job.user)


@register_job_task(JobOperation.CREATE_ENTRY_V2)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def create_entry_v2(self: Task, job: Job) -> JobStatus:
    serializer = EntryCreateSerializer(data=json.loads(job.params), context={"_user": job.user})
    if not serializer.is_valid():
        return JobStatus.ERROR

    entry = serializer.create(serializer.validated_data)

    # Associate the created entry with this job. The job is created with
    # target=None (the entry does not exist yet at request time), so without
    # this the create operation would be hidden from the job list, which
    # filters out non-export/non-delete jobs that have no active target.
    job.target = entry
    job.target_type = JobTarget.ENTRY
    job.save(update_fields=["target", "target_type"])

    return JobStatus.DONE


@register_job_task(JobOperation.EDIT_ENTRY_V2)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def edit_entry_v2(self: Task, job: Job) -> JobStatus:
    entry: Entry | None = Entry.objects.filter(id=job.target.id, is_active=True).first()
    if not entry:
        return JobStatus.ERROR

    serializer = EntryUpdateSerializer(
        instance=entry, data=json.loads(job.params), context={"_user": job.user}
    )
    if not serializer.is_valid():
        return JobStatus.ERROR

    serializer.update(entry, serializer.validated_data)

    return JobStatus.DONE


@register_job_task(JobOperation.DELETE_ENTRY_V2)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def delete_entry_v2(self: Task, job: Job) -> JobStatus:
    entry: Entry | None = Entry.objects.filter(id=job.target.id, is_active=True).first()
    if not entry:
        return JobStatus.ERROR

    # register operation History for deleting entry
    job.user.seth_entry_del(entry)
    entry.delete(deleted_user=job.user)

    for ref_entry, actions in TriggerCondition.get_invoked_actions_on_delete(entry):
        for action in actions:
            action.run(job.user, ref_entry)

    # Send notification to the webhook URL
    job_notify: Job = Job.new_notify_delete_entry(job.user, entry)
    job_notify.run()

    if custom_view.is_custom("after_delete_entry_v2", entry.schema.name):
        custom_view.call_custom("after_delete_entry_v2", entry.schema.name, job.user, entry)

    return JobStatus.DONE


@register_job_task(JobOperation.BULK_EDIT_ENTRY)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def bulk_update_entries(
    self: Any, job: Job
) -> JobStatus | tuple[JobStatus, str, ACLBase | None] | None:
    job_params = json.loads(job.params)

    # get target items from ES by job_params.attr_info parameter
    resp = AdvancedSearchService.search_entries(
        user=job.user,
        hint_entity_ids=[job_params["modelid"]],
        hint_attrs=[AttrHint(**x) for x in job_params.get("attrinfo", [])],
        hint_entry=EntryHint(**job_params.get("hint_entry"))
        if job_params.get("hint_entry")
        else None,
        hint_referral=job_params.get("referral_name"),
        retrieve_all=True,
    )

    # update each items in accordance with job_params.value parameter
    context = {"request": DRFRequest(job.user)}
    total_count = resp.ret_count
    for index, record in enumerate(resp.ret_values):
        job.text = "Now updating... (progress: [%5d/%5d])" % (index + 1, total_count)
        job.save(update_fields=["text"])

        # abort processing when job is canceled
        if job.is_canceled():
            job.status = JobStatus.CANCELED
            job.save(update_fields=["status"])
            return None

        entry = Entry.objects.get(id=record.entry["id"])
        updating_data: dict[str, list[Any]] = {"attrs": []}
        if job_params.get("value"):
            updating_data["attrs"].append(
                {
                    "id": job_params.get("value")["id"],
                    "value": job_params.get("value")["value"],
                }
            )

        serializer = EntryUpdateSerializer(instance=entry, data=updating_data, context=context)
        if serializer.is_valid():
            serializer.save()
        else:
            return (
                JobStatus.ERROR,
                "Validation error during bulk update (%s)" % serializer.error_messages,
                None,
            )

    job.text = "Bulk update completed [%5d/%5d]" % (total_count, total_count)
    job.save(update_fields=["text"])
    return JobStatus.DONE


def _render_import_value(value: Any) -> str:
    """Render a value as the user wrote it in the import file."""
    match value:
        case None:
            return ""
        case bool():
            return "true" if value else "false"
        case list():
            return ", ".join(_render_import_value(x) for x in value)
        case dict():
            return ", ".join("%s: %s" % (k, _render_import_value(v)) for k, v in value.items())
        case _:
            return str(value)


def _render_stored_value(attr: Attribute) -> str:
    """Render an attribute's current value.

    Attribute.get_latest_value() creates an empty AttributeValue when there is
    none, which a preview must never do, so the latest value is read directly.
    """
    attrv = attr.values.filter(is_latest=True).last()
    if attrv is None:
        return ""
    return _render_import_value(attrv.get_value())


def _unresolved_referrals(raw_value: Any, converted_value: Any) -> list[str]:
    """Names the importer could not resolve, reported as 0 by the serializer.

    A reference that cannot be resolved is silently stored as an empty value, so
    a preview that did not surface it would hide the import's most damaging
    failure mode.
    """
    match (raw_value, converted_value):
        case (list(), list()) if len(raw_value) == len(converted_value):
            return [
                name
                for raw, converted in zip(raw_value, converted_value)
                for name in _unresolved_referrals(raw, converted)
            ]
        case (dict(), dict()):
            # named object: {"name": ..., "id": <resolved>} against {"<name>": "<referral>"}
            if converted_value.get("id") == 0:
                return [_render_import_value(list(raw_value.values())[0])]
            return []
        case (_, 0) if raw_value:
            return [_render_import_value(raw_value)]
        case _:
            return []


@register_job_task(JobOperation.IMPORT_ENTRY_PREVIEW)
@app.task(bind=True)  # type: ignore[misc]
@may_schedule_until_job_is_ready
def import_entries_preview_v2(self: Task, job: Job) -> JobStatus:
    """Report what importing this file would do to the items of one model.

    Unlike the model import preview, this never writes: applying an item import
    also reindexes Elasticsearch and queues webhook and trigger jobs, none of
    which a transaction could take back. What it does instead is run the same
    decisions the import runs -- the same serializers for validation, the same
    Attribute.is_updated() for change detection -- and stop before the write.
    """
    user: User = job.user
    entity = Entity.objects.get(id=job.target.id)
    raw_data = json.loads(job.params)

    import_serializer = EntryImportEntitySerializer(data=raw_data)
    if not import_serializer.is_valid():
        return JobStatus.ERROR

    context = {"request": DRFRequest(user)}
    collector = PreviewCollector()

    raw_entries = raw_data.get("entries", [])
    entries = import_serializer.validated_data["entries"]
    total_count = len(entries)

    for index, entry_data in enumerate(entries):
        job.text = "Now previewing... (progress: [%5d/%5d])" % (index + 1, total_count)
        job.save(update_fields=["text"])

        if job.is_canceled():
            return JobStatus.CANCELED

        raw_entry = raw_entries[index] if index < len(raw_entries) else {}
        _preview_one_entry(user, entity, entry_data, raw_entry, context, collector)

    job.set_cache(collector.payload())

    return JobStatus.DONE


def _preview_one_entry(
    user: User,
    entity: Entity,
    entry_data: dict[str, Any],
    raw_entry: dict[str, Any],
    context: dict[str, Any],
    collector: PreviewCollector,
) -> None:
    entry_data = dict(entry_data, schema=entity)
    name = entry_data["name"]

    # Identify the Item the import would touch, exactly as import_entries_v2 does.
    entry: Entry | None = None
    if entry_data.get("id") is not None:
        entry = Entry.objects.filter(id=entry_data["id"], schema=entity, is_active=True).first()
    if not entry:
        entry = Entry.objects.filter(name=name, schema=entity, is_active=True).first()

    # Run the very serializer the import runs, but stop before save(): validation
    # errors are reported here instead of being logged and counted as a failure.
    serializer: EntryUpdateSerializer | EntryCreateSerializer = (
        EntryUpdateSerializer(instance=entry, data=entry_data, context=context)
        if entry
        else EntryCreateSerializer(data=entry_data, context=context)
    )
    if not serializer.is_valid():
        collector.add(
            kind="Item",
            name=name,
            action="error",
            reason="; ".join(
                "%s: %s" % (field, ", ".join(str(x) for x in messages))
                for field, messages in serializer.errors.items()
            ),
        )
        return

    warnings = _collect_unresolved(entry_data, raw_entry)
    changes = _collect_attr_changes(user, entity, entry, entry_data, raw_entry)

    # Importing fires triggers, which change values the file never mentions.
    # Read-only: this asks which actions would match, it does not run them.
    will_invoke_trigger = bool(
        TriggerCondition.get_invoked_actions(entity, entry_data.get("attrs", []))
    )

    if entry is None:
        collector.add(
            kind="Item",
            name=name,
            action="create",
            reason="; ".join(warnings) or None,
            changes=changes,
            will_invoke_trigger=will_invoke_trigger,
        )
        return

    if entry.name != name:
        changes.insert(0, {"field": "name", "before": entry.name, "after": name})

    collector.add(
        kind="Item",
        name=name,
        action="update" if changes else "unchanged",
        reason="; ".join(warnings) or None,
        changes=changes,
        will_invoke_trigger=will_invoke_trigger,
        baseline=_entry_baseline(entry, entry_data),
    )


def _entry_baseline(entry: Entry, entry_data: dict[str, Any]) -> dict[str, Any]:
    """Fingerprint the values this row would overwrite.

    The import compares it against the values it finds, so that a row someone
    else changed in the meantime is not overwritten on the strength of a preview
    that no longer describes it.
    """
    return {
        "entry_id": entry.id,
        "values": _latest_value_ids(entry, [int(x["id"]) for x in entry_data.get("attrs", [])]),
    }


def _latest_value_ids(entry: Entry, entity_attr_ids: list[int]) -> dict[str, int]:
    latest: dict[str, int] = {}
    for attr in entry.attrs.filter(schema__id__in=entity_attr_ids, is_active=True):
        attrv = attr.values.filter(is_latest=True).last()
        latest[str(attr.schema_id)] = attrv.id if attrv else 0
    return latest


def _collect_unresolved(entry_data: dict[str, Any], raw_entry: dict[str, Any]) -> list[str]:
    raw_by_name = {x["name"]: x.get("value") for x in raw_entry.get("attrs", [])}
    warnings: list[str] = []
    for attr_data in entry_data.get("attrs", []):
        unresolved = _unresolved_referrals(raw_by_name.get(attr_data["name"]), attr_data["value"])
        if unresolved:
            warnings.append(
                "%s: 参照先が見つかりません (%s)" % (attr_data["name"], ", ".join(unresolved))
            )
    return warnings


def _collect_attr_changes(
    user: User,
    entity: Entity,
    entry: Entry | None,
    entry_data: dict[str, Any],
    raw_entry: dict[str, Any],
) -> list[dict[str, str | None]]:
    raw_by_name = {x["name"]: x.get("value") for x in raw_entry.get("attrs", [])}
    attrs_data = entry_data.get("attrs", [])
    changes: list[dict[str, str | None]] = []

    for entity_attr in entity.attrs.filter(is_active=True):
        attr_data = next((x for x in attrs_data if int(x["id"]) == entity_attr.id), None)
        if attr_data is None:
            continue

        after = _render_import_value(raw_by_name.get(attr_data["name"]))

        attr: Attribute | None = (
            entry.attrs.filter(schema=entity_attr, is_active=True).first() if entry else None
        )
        if attr is None:
            # The import would create the attribute; anything non-empty is a change.
            if after:
                changes.append({"field": entity_attr.name, "before": None, "after": after})
            continue

        if not user.has_permission(attr, ACLType.Writable):
            continue

        if attr.is_updated(attr_data["value"]):
            changes.append(
                {
                    "field": entity_attr.name,
                    "before": _render_stored_value(attr),
                    "after": after,
                }
            )

    return changes
