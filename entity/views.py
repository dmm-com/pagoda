import collections
import io
import re

import yaml
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.http.response import JsonResponse

from airone.lib import custom_view
from airone.lib.acl import ACLType, get_permitted_objects
from airone.lib.http import (
    get_download_response,
    get_obj_with_check_perm,
    http_get,
    http_post,
    render,
)
from airone.lib.types import AttrType, AttrTypes
from entry.models import AttributeValue, Entry
from job.models import Job
from user.models import History

from .models import Entity, EntityAttr
from .settings import CONFIG


@http_get
def index(request):
    param_page_index = request.GET.get("page", 0)
    param_keyword = request.GET.get("keyword")

    # Get entities under the conditions of specified parameters
    query = Q(is_active=True)
    if param_keyword:
        query &= Q(name__icontains=param_keyword)

    overall_entities = Entity.objects.filter(query).order_by("name")

    p = Paginator(overall_entities, CONFIG.MAX_LIST_ENTITIES)
    try:
        page = int(param_page_index)
        # Page numbers on the entity index page start at 0, wheres Paginator start at 1.
        page_obj = p.page(page + 1)

    except (ValueError, PageNotAnInteger):
        return HttpResponse("Invalid page number. It must be unsigned integer", status=400)
    except EmptyPage:
        return HttpResponse("Invalid page number. The page doesn't have anything", status=400)

    return_entities = page_obj.object_list
    index_start = (page_obj.number - 1) * CONFIG.MAX_LIST_ENTITIES

    context = {
        "entities": return_entities,
        "entity_count": return_entities.count(),
        "total_count": overall_entities.count(),
        "page_index_start": index_start,
        "page_index_end": index_start + return_entities.count(),
    }
    return render(request, "list_entities.html", context)


@http_get
def create(request):
    context = {
        "entities": [
            x
            for x in Entity.objects.filter(is_active=True)
            if request.user.has_permission(x, ACLType.Readable)
        ],
        "attr_types": AttrTypes,
    }
    return render(request, "create_entity.html", context)


@http_get
def edit(request, entity_id):
    entity, error = get_obj_with_check_perm(request.user, Entity, entity_id, ACLType.Writable)
    if error:
        return error

    # when an entity in referral attribute is deleted
    # user should be able to select new entity or keep it unchanged
    # candidate entites for referral are:
    # - active(not deleted) entity
    # - current value of any attributes even if the entity has been deleted
    context = {
        "entity": entity,
        "attr_types": AttrTypes,
        "attributes": [
            {
                "id": x.id,
                "name": x.name,
                "type": x.type,
                "is_mandatory": x.is_mandatory,
                "is_delete_in_chain": x.is_delete_in_chain,
                "referrals": x.referral.all(),
            }
            for x in entity.attrs.filter(is_active=True).order_by("index")
            if request.user.has_permission(x, ACLType.Writable)
        ],
    }
    return render(request, "edit_entity.html", context)


@http_post(
    [
        {
            "name": "name",
            "type": str,
            "checker": lambda x: (
                x["name"] and len(x["name"]) <= Entity._meta.get_field("name").max_length
            ),
        },
        {"name": "note", "type": str},
        {"name": "is_toplevel", "type": bool},
        {
            "name": "attrs",
            "type": list,
            "meta": [
                {
                    "name": "name",
                    "type": str,
                    "checker": lambda x: (
                        x["name"]
                        and not re.match(r"^\s*$", x["name"])
                        and len(x["name"]) <= EntityAttr._meta.get_field("name").max_length
                    ),
                },
                {
                    "name": "type",
                    "type": str,
                    "checker": lambda x: (any([y == int(x["type"]) for y in AttrTypes])),
                },
                {"name": "is_mandatory", "type": bool},
                {"name": "is_delete_in_chain", "type": bool},
                {
                    "name": "row_index",
                    "type": str,
                    "checker": lambda x: (re.match(r"^[0-9]*$", x["row_index"])),
                },
            ],
        },
    ]
)
def do_edit(request, entity_id, recv_data):
    entity, error = get_obj_with_check_perm(request.user, Entity, entity_id, ACLType.Writable)
    if error:
        return error

    # validation checks
    for attr in recv_data["attrs"]:
        # formalize recv_data format
        if "ref_ids" not in attr:
            attr["ref_ids"] = []

        if int(attr["type"]) & AttrType.OBJECT and not attr["ref_ids"]:
            return HttpResponse("Need to specify enabled referral ids", status=400)

        if any([not Entity.objects.filter(id=x).exists() for x in attr["ref_ids"]]):
            return HttpResponse("Specified referral is invalid", status=400)

    # duplication checks
    counter = collections.Counter(
        [
            attr["name"]
            for attr in recv_data["attrs"]
            if "deleted" not in attr or not attr["deleted"]
        ]
    )
    if len([v for v, count in counter.items() if count > 1]):
        return HttpResponse("Duplicated attribute names are not allowed", status=400)

    # prevent to show edit page under the processing
    if entity.get_status(Entity.STATUS_EDITING):
        return HttpResponse("Target entity is now under processing", status=400)

    if custom_view.is_custom("edit_entity"):
        resp = custom_view.call_custom(
            "edit_entity", None, entity, recv_data["name"], recv_data["attrs"]
        )
        if resp:
            return resp

    # update status parameters
    if recv_data["is_toplevel"]:
        entity.set_status(Entity.STATUS_TOP_LEVEL)
    else:
        entity.del_status(Entity.STATUS_TOP_LEVEL)

    # update entity metatada informations to new ones
    entity.set_status(Entity.STATUS_EDITING)

    # Create a new job to edit entity and run it
    job = Job.new_edit_entity(request.user, entity, params=recv_data)
    job.run()

    new_name = recv_data["name"]
    return JsonResponse(
        {
            "entity_id": entity.id,
            "entity_name": new_name,
            "msg": 'Success to schedule to update Entity "%s"' % new_name,
        }
    )


@http_post(
    [
        {
            "name": "name",
            "type": str,
            "checker": lambda x: (
                x["name"]
                and not Entity.objects.filter(name=x["name"]).exists()
                and len(x["name"]) <= Entity._meta.get_field("name").max_length
            ),
        },
        {"name": "note", "type": str},
        {"name": "is_toplevel", "type": bool},
        {
            "name": "attrs",
            "type": list,
            "meta": [
                {
                    "name": "name",
                    "type": str,
                    "checker": lambda x: (
                        x["name"]
                        and not re.match(r"^\s*$", x["name"])
                        and len(x["name"]) <= EntityAttr._meta.get_field("name").max_length
                    ),
                },
                {
                    "name": "type",
                    "type": str,
                    "checker": lambda x: (any([y == int(x["type"]) for y in AttrTypes])),
                },
                {"name": "is_mandatory", "type": bool},
                {"name": "is_delete_in_chain", "type": bool},
                {
                    "name": "row_index",
                    "type": str,
                    "checker": lambda x: (re.match(r"^[0-9]*$", x["row_index"])),
                },
            ],
        },
    ]
)
def do_create(request, recv_data):
    # validation checks
    for attr in recv_data["attrs"]:
        # formalize recv_data format
        if "ref_ids" not in attr:
            attr["ref_ids"] = []

        if int(attr["type"]) & AttrType.OBJECT and not attr["ref_ids"]:
            return HttpResponse("Need to specify enabled referral ids", status=400)

        if any([not Entity.objects.filter(id=x).exists() for x in attr["ref_ids"]]):
            return HttpResponse("Specified referral is invalid", status=400)

    # duplication checks
    counter = collections.Counter(
        [
            attr["name"]
            for attr in recv_data["attrs"]
            if "deleted" not in attr or not attr["deleted"]
        ]
    )
    if len([v for v, count in counter.items() if count > 1]):
        return HttpResponse("Duplicated attribute names are not allowed", status=400)

    if custom_view.is_custom("create_entity"):
        resp = custom_view.call_custom("create_entity", None, recv_data["name"], recv_data["attrs"])
        if resp:
            return resp

    # create EntityAttr objects
    entity = Entity(
        name=recv_data["name"],
        note=recv_data["note"],
        created_user=request.user,
        status=Entity.STATUS_CREATING,
    )

    # set status parameters
    if recv_data["is_toplevel"]:
        entity.status = Entity.STATUS_TOP_LEVEL

    entity.save()

    # Create a new job to edit entity and run it
    job = Job.new_create_entity(request.user, entity, params=recv_data)
    job.run()

    return JsonResponse(
        {
            "entity_id": entity.id,
            "entity_name": entity.name,
            "msg": 'Success to create Entity "%s"' % entity.name,
        }
    )


@http_get
def export(request):
    output = io.StringIO()

    data = {"Entity": [], "EntityAttr": []}

    entities = get_permitted_objects(request.user, Entity, ACLType.Readable)
    for entity in entities:
        data["Entity"].append(
            {
                "created_user": entity.created_user.username,
                "id": entity.id,
                "name": entity.name,
                "note": entity.note,
                "status": entity.status,
            }
        )

    attrs = get_permitted_objects(request.user, EntityAttr, ACLType.Readable)
    for attr in attrs:
        data["EntityAttr"].append(
            {
                "created_user": attr.created_user.username,
                "entity": attr.parent_entity.name,
                "id": attr.id,
                "is_mandatory": attr.is_mandatory,
                "name": attr.name,
                "refer": ",".join(
                    list(map(lambda x: x.name, attr.referral.filter(is_active=True)))
                ),
                "type": attr.type,
            }
        )

    output.write(yaml.dump(data, default_flow_style=False, allow_unicode=True))
    return get_download_response(output, "entity.yaml")


@http_post([])
def do_delete(request, entity_id, recv_data):
    entity, error = get_obj_with_check_perm(request.user, Entity, entity_id, ACLType.Full)
    if error:
        return error

    if not entity.is_active:
        return HttpResponse("Target entity is now under processing", status=400)

    if Entry.objects.filter(schema=entity, is_active=True).exists():
        return HttpResponse(
            "cannot delete Entity because one or more Entries are not deleted",
            status=400,
        )

    if custom_view.is_custom("delete_entity"):
        resp = custom_view.call_custom("delete_entity", None, entity)
        if resp:
            return resp

    ret = {}
    # save deleting target name before do it
    ret["name"] = entity.name

    # set deleted flag in advance because deleting processing takes long time
    entity.is_active = False
    entity.save_without_historical_record(update_fields=["is_active"])

    # Create a new job to delete entry and run it
    job = Job.new_delete_entity(request.user, entity)
    job.run()

    return JsonResponse(ret)


@http_get
def history(request, entity_id):
    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse("Failed to get entity of specified id", status=400)

    # entity to be editted is given by url
    entity = Entity.objects.get(id=entity_id)

    context = {
        "entity": entity,
        "history": History.objects.filter(target_obj=entity, is_detail=False).order_by("-time"),
    }

    return render(request, "history_entity.html", context)


@http_get
def dashboard(request, entity_id):
    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse("Failed to get entity of specified id", status=400)

    # entity to be editted is given by url
    entity = Entity.objects.get(id=entity_id)
    total_entry_count = Entry.objects.filter(schema=entity, is_active=True).count()

    summarized_data = {}
    for attr in EntityAttr.objects.filter(parent_entity=entity, is_active=True, is_summarized=True):
        summarized_data[attr] = {
            "referral_count": [
                {
                    "referral": r.name,
                    "count": AttributeValue.objects.filter(
                        **{
                            "parent_attr__parent_entry__is_active": True,
                            "parent_attr__is_active": True,
                            "parent_attr__schema": attr,
                            "is_latest": True,
                            "referral": r,
                        }
                    ).count(),
                }
                for r in Entry.objects.filter(schema=attr.referral.first(), is_active=True)
            ],
        }

        # filter elements which count is 0
        summarized_data[attr]["referral_count"] = [
            x for x in summarized_data[attr]["referral_count"] if x["count"] > 0
        ]

        # set count of entries which doesn't have referral
        summarized_data[attr]["no_referral_count"] = Entry.objects.filter(
            schema=entity, is_active=True
        ).count() - sum([x["count"] for x in summarized_data[attr]["referral_count"]])

        summarized_data[attr]["no_referral_ratio"] = "%2.1f" % (
            (100 * summarized_data[attr]["no_referral_count"]) / total_entry_count
        )

        # sort by referral counts
        summarized_data[attr]["referral_count"] = sorted(
            summarized_data[attr]["referral_count"],
            key=lambda x: x["count"],
            reverse=True,
        )

        # summarize results to prevent overflowing results by a lot of tiny elements
        if len(summarized_data[attr]["referral_count"]) > CONFIG.DASHBOARD_NUM_ITEMS:
            rest_counts = sum(
                [
                    x["count"]
                    for x in summarized_data[attr]["referral_count"][CONFIG.DASHBOARD_NUM_ITEMS :]
                ]
            )

            summarized_data[attr]["referral_count"] = summarized_data[attr]["referral_count"][
                : CONFIG.DASHBOARD_NUM_ITEMS
            ]
            summarized_data[attr]["referral_count"].append(
                {
                    "referral": "(Others)",
                    "count": rest_counts,
                    "ratio": "%2.1f" % ((rest_counts * 100) / total_entry_count),
                }
            )

        # set ratio for each elements
        for info in summarized_data[attr]["referral_count"]:
            info["ratio"] = "%2.1f" % ((info["count"] * 100) / total_entry_count)

    context = {
        "entity": entity,
        "total_entry_count": total_entry_count,
        "summarized_data": summarized_data,
    }
    return render(request, "dashboard_entity.html", context)


@http_get
def conf_dashboard(request, entity_id):
    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse("Failed to get entity of specified id", status=400)

    # entity to be editted is given by url
    entity = Entity.objects.get(id=entity_id)

    context = {
        "entity": entity,
        "ref_attrs": EntityAttr.objects.filter(
            parent_entity=entity, type=AttrType.OBJECT, is_active=True
        ),
        "redirect_url": "/entity/dashboard/config/register/%s" % entity_id,
    }
    return render(request, "conf_dashboard_entity.html", context)


@http_post(
    [
        {
            "name": "attrs",
            "type": list,
            "checker": lambda x: all(
                [EntityAttr.objects.filter(id=v).exists() for v in x["attrs"]]
            ),
        }
    ]
)
def do_conf_dashboard(request, entity_id, recv_data):
    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse("Failed to get entity of specified id", status=400)

    # clear is_summarized flag for each EntityAttrs corresponding to the entity
    EntityAttr.objects.filter(parent_entity=entity_id).update(is_summarized=False)

    # set is_summarized flag for each specified EntityAttrs
    for attr in [EntityAttr.objects.get(id=x) for x in recv_data["attrs"]]:
        attr.is_summarized = True
        attr.save(update_fields=["is_summarized"])

    return JsonResponse({"msg": "Success to update dashboard"})
