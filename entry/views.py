import re
from datetime import datetime
from urllib.parse import urlencode

import yaml
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

import custom_view
from airone.lib.acl import ACLType
from airone.lib.elasticsearch import prepend_escape_character
from airone.lib.http import (
    HttpResponseSeeOther,
    get_obj_with_check_perm,
    http_file_upload,
    http_get,
    http_post,
    render,
)
from airone.lib.types import AttrTypeValue
from entity.models import Entity
from entry.models import Attribute, AttributeValue, Entry
from group.models import Group
from job.models import Job
from user.models import User

from .settings import CONFIG


def _validate_input(recv_data, obj):
    def _has_data(value):
        return "data" in value and value["data"] != "" and value["data"] is not None

    def _has_referral(value):
        if isinstance(value["data"], int):
            return value["data"] > 0
        elif isinstance(value["data"], str):
            try:
                return value["data"].isnumeric() and int(value["data"]) > 0
            except ValueError:
                return False
        else:
            return False

    for attr_data in recv_data["attrs"]:
        if isinstance(obj, Entry):
            attr = None
            if attr_data["id"]:
                attr = obj.attrs.filter(id=attr_data["id"]).first()

            if attr:
                attr = attr.schema
            elif attr_data["entity_attr_id"]:
                attr = obj.schema.attrs.filter(id=attr_data["entity_attr_id"]).first()

        if isinstance(obj, Entity):
            attr = obj.attrs.filter(id=attr_data["id"]).first()

        if not attr:
            return HttpResponse("Specified attribute is invalid", status=400)

        if attr.is_mandatory:
            # This checks whether valid data is passed
            is_valid = attr_data["value"] and all([_has_data(x) for x in attr_data["value"]])

            # This checks whether valid referral parameter is passed
            if is_valid and attr.type & AttrTypeValue["object"]:
                is_valid &= all([_has_referral(x) for x in attr_data["value"]])

            # This checks whether valid referral_key parameter is passed
            if attr.type & AttrTypeValue["named"]:
                is_valid |= attr_data["referral_key"] and all(
                    [_has_data(x) for x in attr_data["referral_key"]]
                )

            if not is_valid:
                return HttpResponse("You have to specify value at mandatory parameters", status=400)

        # Checks specified value exceeds the limit of AttributeValue
        if any(
            [
                len(str(y["data"]).encode("utf-8")) > AttributeValue.MAXIMUM_VALUE_SIZE
                for y in attr_data["value"]
            ]
        ):
            return HttpResponse("Passed value is exceeded the limit", status=400)

        # Check date value format
        if attr.type & AttrTypeValue["date"]:
            try:
                [
                    datetime.strptime(str(i["data"]), "%Y-%m-%d")
                    for i in attr_data["value"]
                    if i["data"]
                ]
            except ValueError:
                return HttpResponse("Incorrect data format in date", status=400)


@http_get
def index(request, entity_id):
    entity, error = get_obj_with_check_perm(request.user, Entity, entity_id, ACLType.Readable)
    if error:
        return error

    page = request.GET.get("page", 1)
    keyword = request.GET.get("keyword", None)

    if custom_view.is_custom("list_entry_without_context", entity.name):
        # show custom view without context
        resp = custom_view.call_custom("list_entry_without_context", entity.name, request, entity)
        if resp:
            return resp

    if keyword:
        name_pattern = prepend_escape_character(CONFIG.ESCAPE_CHARACTERS_ENTRY_LIST, keyword)
        entries = Entry.objects.order_by("name").filter(
            schema=entity, is_active=True, name__iregex=name_pattern
        )
    else:
        entries = Entry.objects.order_by("name").filter(schema=entity, is_active=True)

    p = Paginator(entries, CONFIG.MAX_LIST_ENTRIES)
    try:
        page_obj = p.page(page)
    except PageNotAnInteger:
        return HttpResponse("Invalid page number. It must be unsigned integer", status=400)
    except EmptyPage:
        return HttpResponse("Invalid page number. The page doesn't have anything", status=400)

    context = {
        "entity": entity,
        "keyword": keyword,
        "page_obj": page_obj,
    }

    if custom_view.is_custom("list_entry", entity.name):
        # list custom view
        return custom_view.call_custom("list_entry", entity.name, request, entity, context)
    else:
        # list ordinal view
        return render(request, "list_entry.html", context)


@http_get
def create(request, entity_id):
    entity, error = get_obj_with_check_perm(request.user, Entity, entity_id, ACLType.Writable)
    if error:
        return error

    if custom_view.is_custom("create_entry_without_context", entity.name):
        # show custom view
        return custom_view.call_custom(
            "create_entry_without_context", entity.name, request, request.user, entity
        )

    context = {
        "entity": entity,
        "form_url": "/entry/do_create/%s/" % entity.id,
        "redirect_url": "/entry/%s" % entity.id,
        "groups": Group.objects.filter(is_active=True),
        "attributes": [
            {
                "entity_attr_id": x.id,
                "id": x.id,
                "type": x.type,
                "name": x.name,
                "is_mandatory": x.is_mandatory,
                "is_readble": True if request.user.has_permission(x, ACLType.Writable) else False,
            }
            for x in entity.attrs.filter(is_active=True).order_by("index")
        ],
    }

    if custom_view.is_custom("create_entry", entity.name):
        # show custom view
        return custom_view.call_custom(
            "create_entry", entity.name, request, request.user, entity, context
        )
    else:
        return render(request, "create_entry.html", context)


@http_post(
    [
        {"name": "entry_name", "type": str, "checker": lambda x: x["entry_name"]},
        {
            "name": "attrs",
            "type": list,
            "meta": [
                {"name": "id", "type": str},
                {"name": "value", "type": list},
            ],
        },
    ]
)
def do_create(request, entity_id, recv_data):
    # get objects to be referred in the following processing
    entity, error = get_obj_with_check_perm(request.user, Entity, entity_id, ACLType.Writable)
    if error:
        return error

    # checks that a same name entry corresponding to the entity is existed, or not.
    if Entry.objects.filter(schema=entity_id, name=recv_data["entry_name"]).exists():
        return HttpResponse("Duplicate name entry is existed", status=400)

    # validate contexts of each attributes
    err = _validate_input(recv_data, entity)
    if err:
        return err

    if custom_view.is_custom("do_create_entry", entity.name):
        # resp is HttpReponse instance or its subclass (e.g. JsonResponse)
        resp = custom_view.call_custom(
            "do_create_entry", entity.name, request, recv_data, request.user, entity
        )
        if resp:
            return resp

    # Create a new Entry object
    entry = Entry.objects.create(
        name=recv_data["entry_name"],
        created_user=request.user,
        schema=entity,
        status=Entry.STATUS_CREATING,
    )

    # Create a new job to create entry and run it
    job_create_entry = Job.new_create(request.user, entry, params=recv_data)
    job_create_entry.run()

    return JsonResponse(
        {
            "entry_id": entry.id,
            "entry_name": entry.name,
        }
    )


@http_get
def edit(request, entry_id):
    entry, error = get_obj_with_check_perm(request.user, Entry, entry_id, ACLType.Writable)
    if error:
        return error

    # prevent to show edit page under the creating processing
    if entry.get_status(Entry.STATUS_CREATING):
        return HttpResponse("Target entry is now under processing", status=400)

    if not entry.is_active:
        return _redirect_restore_entry(entry)

    context = {
        "entry": entry,
        "groups": Group.objects.filter(is_active=True),
        "attributes": entry.get_available_attrs(request.user, ACLType.Writable),
        "form_url": "/entry/do_edit/%s" % entry.id,
        "redirect_url": "/entry/show/%s" % entry.id,
    }

    if custom_view.is_custom("edit_entry", entry.schema.name):
        # show custom view
        return custom_view.call_custom(
            "edit_entry", entry.schema.name, request, request.user, entry, context
        )
    else:
        return render(request, "edit_entry.html", context)


@http_post(
    [
        {"name": "entry_name", "type": str, "checker": lambda x: (x["entry_name"])},
        {
            "name": "attrs",
            "type": list,
            "meta": [
                {"name": "entity_attr_id", "type": str},
                {"name": "id", "type": str},
                {"name": "value", "type": list},
            ],
        },
    ]
)
def do_edit(request, entry_id, recv_data):
    entry, error = get_obj_with_check_perm(request.user, Entry, entry_id, ACLType.Writable)
    if error:
        return error

    # checks that a same name entry corresponding to the entity is existed.
    query = Q(schema=entry.schema, name=recv_data["entry_name"]) & ~Q(id=entry.id)
    if Entry.objects.filter(query).exists():
        return HttpResponse("Duplicate name entry is existed", status=400)

    # validate contexts of each attributes
    err = _validate_input(recv_data, entry)
    if err:
        return err

    if entry.get_status(Entry.STATUS_CREATING):
        return HttpResponse("Target entry is now under processing", status=400)

    if custom_view.is_custom("do_edit_entry", entry.schema.name):
        # resp is HttpReponse instance or its subclass (e.g. JsonResponse)
        resp = custom_view.call_custom(
            "do_edit_entry", entry.schema.name, request, recv_data, request.user, entry
        )
        if resp:
            return resp

    # update name of Entry object. If name would be updated, the elasticsearch data of entries that
    # refers this entry also be updated by creating REGISTERED_REFERRALS task.
    job_register_referrals = None
    if entry.name != recv_data["entry_name"]:
        job_register_referrals = Job.new_register_referrals(request.user, entry)

    entry.name = recv_data["entry_name"]
    entry.save(update_fields=["name"])

    # set flags that indicates target entry is under processing
    entry.set_status(Entry.STATUS_EDITING)

    # Create new jobs to edit entry and notify it to registered webhook endpoint if it's necessary
    job_edit_entry = Job.new_edit(request.user, entry, params=recv_data)
    job_edit_entry.run()

    # running job of re-register referrals because of chaning entry's name
    if job_register_referrals:
        job_register_referrals.dependent_job = job_edit_entry
        job_register_referrals.run()

    return JsonResponse(
        {
            "entry_id": entry.id,
            "entry_name": entry.name,
        }
    )


@http_get
def show(request, entry_id):
    entry, error = get_obj_with_check_perm(request.user, Entry, entry_id, ACLType.Readable)
    if error:
        return error

    if entry.get_status(Entry.STATUS_CREATING):
        return HttpResponse("Target entry is now under processing", status=400)

    if not entry.is_active:
        return _redirect_restore_entry(entry)

    context = {
        "entry": entry,
        "attributes": entry.get_available_attrs(request.user),
    }

    if custom_view.is_custom("show_entry", entry.schema.name):
        # show custom view
        return custom_view.call_custom(
            "show_entry", entry.schema.name, request, request.user, entry, context
        )
    else:
        # show ordinal view
        return render(request, "show_entry.html", context)


@http_get
def history(request, entry_id):
    entry, error = get_obj_with_check_perm(request.user, Entry, entry_id, ACLType.Readable)
    if error:
        return error

    if entry.get_status(Entry.STATUS_CREATING):
        return HttpResponse("Target entry is now under processing", status=400)

    if not entry.is_active:
        return _redirect_restore_entry(entry)

    context = {
        "entry": entry,
        "value_history": entry.get_value_history(request.user),
        "history_count": CONFIG.MAX_HISTORY_COUNT,
    }

    return render(request, "show_entry_history.html", context)


@http_get
def refer(request, entry_id):
    entry, error = get_obj_with_check_perm(request.user, Entry, entry_id, ACLType.Readable)
    if error:
        return error

    if entry.get_status(Entry.STATUS_CREATING):
        return HttpResponse("Target entry is now under processing", status=400)

    if not entry.is_active:
        return _redirect_restore_entry(entry)

    # get referred entries and count of them
    referred_objects = entry.get_referred_objects()

    context = {
        "entry": entry,
        "referred_objects": referred_objects[0 : CONFIG.MAX_LIST_REFERRALS],
        "referred_total": referred_objects.count(),
    }
    return render(request, "show_entry_refer.html", context)


@http_post([])
def export(request, entity_id, recv_data):
    job_params = {
        "export_format": "yaml",
        "target_id": entity_id,
    }

    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse("Failed to get entity of specified id", status=400)

    if "format" in recv_data and recv_data["format"] == "CSV":
        job_params["export_format"] = "csv"

    # check whether same job is sent
    job_status_not_finished = [Job.STATUS["PREPARING"], Job.STATUS["PROCESSING"]]
    if (
        Job.get_job_with_params(request.user, job_params)
        .filter(status__in=job_status_not_finished)
        .exists()
    ):
        return HttpResponse("Same export processing is under execution", status=400)

    entity = Entity.objects.get(id=entity_id)
    if not request.user.has_permission(entity, ACLType.Readable):
        return HttpResponse('Permission denied to export "%s"' % entity.name, status=400)

    # create a job to export search result and run it
    job = Job.new_export(
        request.user,
        **{
            "text": "entry_%s.%s" % (entity.name, job_params["export_format"]),
            "target": entity,
            "params": job_params,
        }
    )
    job.run()

    return JsonResponse(
        {"result": "Succeed in registering export processing. " + "Please check Job list."}
    )


@http_get
def import_data(request, entity_id):
    if not Entity.objects.filter(id=entity_id, is_active=True).exists():
        return HttpResponse("Failed to get entity of specified id", status=400)

    return render(request, "import_entry.html", {"entity": Entity.objects.get(id=entity_id)})


@http_file_upload
def do_import_data(request, entity_id, context):
    user: User = request.user
    entity: Entity
    entity, error = get_obj_with_check_perm(user, Entity, entity_id, ACLType.Writable)
    if error:
        return error
    if not entity.is_active:
        return HttpResponse("Failed to get entity of specified id", status=400)

    try:
        data = yaml.load(context, Loader=yaml.FullLoader)
    except yaml.parser.ParserError:
        return HttpResponse("Couldn't parse uploaded file", status=400)
    except ValueError as e:
        return HttpResponse("Invalid value is found: %s" % e, status=400)
    except yaml.scanner.ScannerError:
        return HttpResponse("Couldn't scan uploaded file", status=400)
    except Exception as e:
        return HttpResponse("Unknown exception: %s" % e, status=500)

    if not Entry.is_importable_data(data):
        return HttpResponse("Uploaded file has invalid data structure to import", status=400)

    for entity_name in data.keys():
        import_entity: Entity = Entity.objects.filter(name=entity_name, is_active=True).first()
        if not import_entity:
            return HttpResponse("Specified entity does not exist (%s)" % entity_name, status=400)
        if not user.has_permission(import_entity, ACLType.Writable):
            return HttpResponse(
                "You don't have permission to access (%s)" % entity_name, status=400
            )

        import_data = data[entity_name]

        if custom_view.is_custom("import_entry", entity_name):
            # import custom view
            import_data, err_msg = custom_view.call_custom(
                "import_entry", entity_name, user, import_entity, import_data
            )

            # If custom_view returns available response this returns it to user,
            # or continues default processing.
            if err_msg:
                return HttpResponse(err_msg, status=400)

        # create job to import data to create or update entries and run it
        job = Job.new_import(
            user, import_entity, text="Preparing to import data", params=import_data
        )
        job.run()

    return HttpResponseSeeOther("/entry/%s/" % entity_id)


@http_post([])  # check only that request is POST, id will be given by url
def do_delete(request, entry_id, recv_data):
    entry, error = get_obj_with_check_perm(request.user, Entry, entry_id, ACLType.Full)
    if error:
        return error

    if custom_view.is_custom("do_delete_entry", entry.schema.name):
        # do_delete custom view
        resp = custom_view.call_custom(
            "do_delete_entry", entry.schema.name, request, request.user, entry
        )

        # If custom_view returns available response this returns it to user,
        # or continues default processing.
        if resp:
            return resp

    # set deleted flag in advance because deleting processing taks long time
    entry.is_active = False
    entry.save(update_fields=["is_active"])

    ret = {}
    # save deleting Entry name before do it
    ret["name"] = entry.name

    # register operation History for deleting entry
    request.user.seth_entry_del(entry)

    # Create a new job to delete entry and run it
    job_delete_entry = Job.new_delete(request.user, entry)
    job_notify_event = Job.new_notify_delete_entry(request.user, entry)

    # This prioritizes notifying job rather than deleting entry
    if job_delete_entry.dependent_job:
        job_notify_event.dependent_job = job_delete_entry.dependent_job

    job_notify_event.save(update_fields=["dependent_job"])
    job_notify_event.run()

    # This update dependent job of deleting entry job
    job_delete_entry.dependent_job = job_notify_event
    job_delete_entry.save(update_fields=["dependent_job"])

    job_delete_entry.run()

    return JsonResponse(ret)


@http_get
def copy(request, entry_id):
    entry, error = get_obj_with_check_perm(request.user, Entry, entry_id, ACLType.Writable)
    if error:
        return error

    # prevent to show edit page under the creating processing
    if entry.get_status(Entry.STATUS_CREATING) or entry.get_status(Entry.STATUS_EDITING):
        return HttpResponse("Target entry is now under processing", status=400)

    if not entry.is_active:
        return _redirect_restore_entry(entry)

    context = {
        "form_url": "/entry/do_copy/%s" % entry.id,
        "redirect_url": "/entry/%s" % entry.schema.id,
        "entry": entry,
    }

    if custom_view.is_custom("copy_entry", entry.schema.name):
        return custom_view.call_custom(
            "copy_entry", entry.schema.name, request, request.user, entry, context
        )

    return render(request, "copy_entry.html", context)


@http_post(
    [
        {"name": "entries", "type": str},
    ]
)
def do_copy(request, entry_id, recv_data):
    entry, error = get_obj_with_check_perm(request.user, Entry, entry_id, ACLType.Full)
    if error:
        return error

    ret = []
    params = {
        "new_name_list": [],
        "post_data": recv_data,
    }
    for new_name in [x for x in recv_data["entries"].split("\n") if x]:
        if (
            new_name in params["new_name_list"]
            or Entry.objects.filter(schema=entry.schema, name=new_name).exists()
        ):
            ret.append(
                {
                    "status": "fail",
                    "msg": "A same named entry (%s) already exists" % new_name,
                }
            )
            continue

        if custom_view.is_custom("do_copy_entry", entry.schema.name):
            (is_continue, status, msg) = custom_view.call_custom(
                "do_copy_entry",
                entry.schema.name,
                request,
                entry,
                recv_data,
                request.user,
                new_name,
            )
            if not is_continue:
                ret.append(
                    {
                        "status": "success" if status else "fail",
                        "msg": msg,
                    }
                )
                continue

        params["new_name_list"].append(new_name)
        ret.append(
            {
                "status": "success",
                "msg": "Success to create new entry '%s'" % new_name,
            }
        )

    # if there is no entry to copy, do not create a job.
    if params["new_name_list"]:
        # make a new job to copy entry and run it
        job = Job.new_copy(request.user, entry, text="Preparing to copy entry", params=params)
        job.run()

    return JsonResponse({"results": ret})


@http_get
def restore(request, entity_id):
    entity, error = get_obj_with_check_perm(request.user, Entity, entity_id, ACLType.Full)
    if error:
        return error

    page = request.GET.get("page", 1)
    keyword = request.GET.get("keyword", None)

    # get all deleted entries that correspond to the entity, the specififcation of
    # 'status=0' is necessary to prevent getting entries that were under processing.
    if keyword:
        name_pattern = prepend_escape_character(CONFIG.ESCAPE_CHARACTERS_ENTRY_LIST, keyword)
        entries = Entry.objects.filter(
            schema=entity, status=0, is_active=False, name__iregex=name_pattern
        ).order_by("-updated_time")
    else:
        entries = Entry.objects.filter(schema=entity, status=0, is_active=False).order_by(
            "-updated_time"
        )

    p = Paginator(entries, CONFIG.MAX_LIST_ENTRIES)
    try:
        page_obj = p.page(page)
    except PageNotAnInteger:
        return HttpResponse("Invalid page number. It must be unsigned integer", status=400)
    except EmptyPage:
        return HttpResponse("Invalid page number. The page doesn't have anything", status=400)

    return render(
        request,
        "list_deleted_entry.html",
        {
            "entity": entity,
            "keyword": keyword,
            "page_obj": page_obj,
        },
    )


@http_post([])
def do_restore(request, entry_id, recv_data):
    entry, error = get_obj_with_check_perm(request.user, Entry, entry_id, ACLType.Full)
    if error:
        return error

    if entry.is_active:
        return JsonResponse(
            data={"msg": "Failed to get entry from specified parameter"}, status=400
        )

    # checks that a same name entry corresponding to the entity is existed, or not.
    dup_entry = Entry.objects.filter(
        schema=entry.schema.id,
        name=re.sub(r"_deleted_[0-9_]*$", "", entry.name),
        is_active=True,
    ).first()
    if dup_entry:
        return JsonResponse(
            data={"msg": "", "entry_id": dup_entry.id, "entry_name": dup_entry.name},
            status=400,
        )

    entry.set_status(Entry.STATUS_CREATING)

    # Create a new job to restore deleted entry and run it
    job = Job.new_restore(request.user, entry)
    job.run()

    return HttpResponse("Success to queue a request to restore an entry")


@http_post([{"type": str, "name": "attr_id"}, {"type": str, "name": "attrv_id"}])
def revert_attrv(request, recv_data):
    attr = Attribute.objects.filter(id=recv_data["attr_id"]).first()
    if not attr:
        return HttpResponse("Specified Attribute-id is invalid", status=400)

    if not request.user.has_permission(attr, ACLType.Writable):
        return HttpResponse("You don't have permission to update this Attribute", status=400)

    attrv = AttributeValue.objects.filter(id=recv_data["attrv_id"]).first()
    if not attrv or attrv.parent_attr.id != attr.id:
        return HttpResponse("Specified AttributeValue-id is invalid", status=400)

    # When the AttributeType was changed after settting value, this operation is aborted
    if attrv.data_type != attr.schema.type:
        return HttpResponse(
            "Attribute-type was changed after this value was registered.", status=400
        )

    latest_value = attr.get_latest_value()
    if latest_value.get_value() != attrv.get_value():
        # copy specified AttributeValue
        new_attrv = AttributeValue.objects.create(
            **{
                "value": attrv.value,
                "referral": attrv.referral,
                "status": attrv.status,
                "boolean": attrv.boolean,
                "date": attrv.date,
                "data_type": attrv.data_type,
                "created_user": request.user,
                "parent_attr": attr,
                "is_latest": True,
            }
        )

        # This also copies child attribute values and append new one
        new_attrv.data_array.add(
            *[
                AttributeValue.objects.create(
                    **{
                        "value": v.value,
                        "referral": v.referral,
                        "created_user": request.user,
                        "parent_attr": attr,
                        "status": v.status,
                        "boolean": v.boolean,
                        "date": v.date,
                        "data_type": v.data_type,
                        "is_latest": False,
                        "parent_attrv": new_attrv,
                    }
                )
                for v in attrv.data_array.all()
            ]
        )

        # append cloned value to Attribute
        attr.values.add(new_attrv)

        # clear all exsts latest flag
        attr.unset_latest_flag(exclude_id=new_attrv.id)

        # register update to the Elasticsearch
        attr.parent_entry.register_es()

        # Send notification to the webhook URL
        job_notify = Job.new_notify_update_entry(request.user, attr.parent_entry)
        job_notify.run()

        # call custom-view if it exists
        if custom_view.is_custom("revert_attrv", attr.parent_entry.schema.name):
            return custom_view.call_custom(
                *[
                    "revert_attrv",
                    attr.parent_entry.schema.name,
                    request,
                    request.user,
                    attr,
                    latest_value,
                    new_attrv,
                ]
            )

    return HttpResponse('Succeed in updating Attribute "%s"' % attr.schema.name)


def _redirect_restore_entry(entry):
    return redirect(
        "{}?{}".format(
            reverse("entry:restore", args=[entry.schema.id]),
            urlencode({"keyword": entry.name}),
        )
    )
