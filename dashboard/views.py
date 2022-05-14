import json
import yaml

from airone.lib.acl import ACLType
from airone.lib.http import render
from airone.lib.http import http_get, http_post
from airone.lib.http import http_file_upload
from airone.lib.http import HttpResponseSeeOther
from airone.lib.log import Logger

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.shortcuts import redirect

from entity.admin import EntityResource, EntityAttrResource
from entry.admin import EntryResource, AttrResource, AttrValueResource
from entity.models import Entity, EntityAttr
from entry.models import Entry, AttributeValue
from entry.settings import CONFIG as CONFIG_ENTRY
from job.models import Job
from user.models import User
from .settings import CONFIG

IMPORT_INFOS = [
    {"model": "Entity", "resource": EntityResource},
    {"model": "EntityAttr", "resource": EntityAttrResource},
    {"model": "Entry", "resource": EntryResource},
    {"model": "Attribute", "resource": AttrResource},
    {"model": "AttributeValue", "resource": AttrValueResource},
]


def index(request):
    context = {}
    if request.user.is_authenticated and User.objects.filter(id=request.user.id).exists():
        history = []
        # Sort by newest attribute update date (id is auto increment)
        for attr_value in (
            AttributeValue.objects.filter(is_latest=True)
            .order_by("id")
            .reverse()[: CONFIG.LAST_ENTRY_HISTORY]
        ):
            parent_attr = attr_value.parent_attr
            parent_entry = parent_attr.parent_entry
            parent_entity = parent_entry.schema

            history.append(
                {
                    "entity": parent_entity,
                    "entry": parent_entry,
                    "attr_type": parent_attr,
                    "attr_value": attr_value,
                }
            )

        context["last_entries"] = history

    return render(request, "dashboard_user_top.html", context)


@http_get
def import_data(request):
    return render(request, "import.html", {})


@http_file_upload
def do_import_data(request, context):
    user = User.objects.get(id=request.user.id)

    if request.FILES["file"].size >= CONFIG.LIMIT_FILE_SIZE:
        return HttpResponse("File size over", status=400)

    try:
        data = yaml.load(context, Loader=yaml.FullLoader)
    except yaml.parser.ParserError:
        return HttpResponse("Couldn't parse uploaded file", status=400)

    def _do_import(resource, iter_data):
        results = []
        for data in iter_data:
            try:
                result = resource.import_data_from_request(data, user)

                results.append({"result": result, "data": data})
            except RuntimeError as e:
                Logger.warning(("(%s) %s " % (resource, data)) + str(e))

        if results:
            resource.after_import_completion(results)

    for info in IMPORT_INFOS:
        if info["model"] in data:
            _do_import(info["resource"], data[info["model"]])

    return HttpResponseSeeOther("/dashboard/")


def _search_by_keyword(query, entity_name, per_page, page_num):
    # correct entries that contans query at EntryName or AttributeValue
    search_result = Entry.search_entries_for_simple(
        query, entity_name, per_page, (page_num - 1) * per_page
    )

    return (search_result["ret_count"], search_result["ret_values"])


@http_get
def search(request):
    user = User.objects.get(id=request.user.id)
    query = request.GET.get("query")
    entity_name = request.GET.get("entity")
    try:
        page_num = int(request.GET.get("page", 1))
        if page_num < 1:
            return HttpResponse("Invalid pege parameter is specified", status=400)
    except Exception:
        return HttpResponse("Invalid pege parameter is specified", status=400)

    if not query:
        return HttpResponse("Invalid query parameter is specified", status=400)

    if len(query.encode("utf-8")) > CONFIG.MAX_QUERY_SIZE:
        return HttpResponse("Sending parameter is too large", status=400)

    modified_query = query.strip()

    # When an available 'entity' parameter is specified and get an entry information which exactly
    # matches, this returns entry results
    if entity_name:
        entry = Entry.objects.filter(name=query, schema__name=entity_name, is_active=True).first()
        if entry and user.has_permission(entry, ACLType.Readable):
            return redirect("/entry/show/%s/" % entry.id)

    per_page = CONFIG.MAXIMUM_SEARCH_RESULTS
    (count, entries) = _search_by_keyword(modified_query, entity_name, per_page, page_num)

    if count == 1:
        return redirect("/entry/show/%s/" % entries[0]["id"])

    p = Paginator(["" for x in range(count)], per_page)
    try:
        page_obj = p.page(page_num)
    except PageNotAnInteger:
        return HttpResponse("Invalid page number. It must be unsigned integer", status=400)
    except EmptyPage:
        return HttpResponse("Invalid page number. The page doesn't have anything", status=400)

    else:
        return render(
            request,
            "show_search_results.html",
            {
                "entries": entries,
                "query": modified_query,
                "page_obj": page_obj,
            },
        )


@http_get
def advanced_search(request):
    entities = [
        x
        for x in Entity.objects.filter(is_active=True).order_by("name")
        if x.attrs.filter(is_active=True).exists()
    ]

    return render(
        request,
        "advanced_search.html",
        {
            "entities": entities,
        },
    )


@http_get
def advanced_search_result(request):
    user = User.objects.get(id=request.user.id)

    recv_entity = request.GET.getlist("entity[]")
    recv_attr = request.GET.getlist("attr[]")
    is_all_entities = request.GET.get("is_all_entities") == "true"
    has_referral = request.GET.get("has_referral") == "true"
    referral_name = request.GET.get("referral_name")
    attrinfo = request.GET.get("attrinfo")
    entry_name = request.GET.get("entry_name", "")

    # forbid to input large size request
    if len(entry_name) > CONFIG_ENTRY.MAX_QUERY_SIZE:
        return HttpResponse("Sending parameter is too large", status=400)

    # check referral params
    # # process of converting older param for backward compatibility
    hint_referral = "" if has_referral else False
    if referral_name:
        hint_referral = referral_name

    # check attribute params
    # The "attr" parameter guarantees backward compatibility.
    # The "atterinfo" is another parameter,
    # that has same purpose that indicates which attributes to search,
    # And "attrinfo" is prioritize than "attr".
    # TODO deprecate attr[]
    hint_attrs = [{"name": x} for x in recv_attr]
    if attrinfo:
        try:
            # build hint attrs from JSON encoded params
            hint_attrs = json.loads(attrinfo)
        except json.JSONDecodeError:
            return HttpResponse("The attrinfo parameter is not JSON", status=400)

        for hint_attr in hint_attrs:
            if "name" not in hint_attr:
                return HttpResponse("The name key is required for attrinfo parameter", status=400)
            if not isinstance(hint_attr["name"], str):
                return HttpResponse("Invalid value for attrinfo parameter", status=400)
            if "keyword" in hint_attr:
                if not isinstance(hint_attr["keyword"], str):
                    return HttpResponse("Invalid value for attrinfo parameter", status=400)
                if len(hint_attr["keyword"]) > CONFIG_ENTRY.MAX_QUERY_SIZE:
                    return HttpResponse("Sending parameter is too large", status=400)

    # check entity params
    if is_all_entities:
        attr_names = [x["name"] for x in hint_attrs]
        recv_entity = list(
            EntityAttr.objects.filter(
                name__in=attr_names, is_active=True, parent_entity__is_active=True
            )
            .order_by("parent_entity__name")
            .values_list("parent_entity__id", flat=True)
            .distinct()
        )
        if not recv_entity:
            return HttpResponse("Invalid value for attribute parameter", status=400)

    if not recv_entity:
        return HttpResponse("The entity[] parameters are required", status=400)

    hint_entity_ids = []
    for entity_id in recv_entity:
        if not isinstance(entity_id, int) and not entity_id.isnumeric():
            return HttpResponse("Invalid entity ID is specified", status=400)
        entity = Entity.objects.filter(id=entity_id, is_active=True).first()
        if not entity:
            return HttpResponse("Invalid entity ID is specified", status=400)

        if user.has_permission(entity, ACLType.Readable):
            hint_entity_ids.append(entity.id)

    return render(
        request,
        "advanced_search_result.html",
        {
            "hint_attrs": hint_attrs,
            "results": Entry.search_entries(
                user,
                hint_entity_ids,
                hint_attrs,
                CONFIG.MAXIMUM_SEARCH_RESULTS,
                entry_name,
                hint_referral,
            ),
            "max_num": CONFIG.MAXIMUM_SEARCH_RESULTS,
            "entities": ",".join([str(x) for x in hint_entity_ids]),
            "has_referral": has_referral,
            "referral_name": referral_name,
            "is_all_entities": is_all_entities,
            "entry_name": entry_name,
        },
    )


@http_post(
    [
        {
            "name": "entities",
            "type": list,
            "checker": lambda x: all(
                [
                    (isinstance(y, str) and y.isnumeric())
                    or isinstance(y, int)
                    and Entity.objects.filter(id=y)
                    for y in x["entities"]
                ]
            ),
        },
        {
            "name": "attrinfo",
            "type": list,
            "meta": [
                {"name": "name", "type": str},
                {
                    "name": "keyword",
                    "type": str,
                    "omittable": True,
                    "checker": lambda x: len(x["keyword"]) <= CONFIG_ENTRY.MAX_QUERY_SIZE,
                },
            ],
        },
        {"name": "has_referral", "type": bool, "omittable": True},
        {"name": "referral_name", "type": str, "omittable": True},
        {
            "name": "entry_name",
            "type": str,
            "omittable": True,
            "checker": lambda x: len(x["entry_name"]) <= CONFIG_ENTRY.MAX_QUERY_SIZE,
        },
        {
            "name": "export_style",
            "type": str,
            "checker": lambda x: x["export_style"] == "yaml" or x["export_style"] == "csv",
        },
    ]
)
def export_search_result(request, recv_data):
    user = User.objects.get(id=request.user.id)

    # check whether same job is sent
    job_status_not_finished = [Job.STATUS["PREPARING"], Job.STATUS["PROCESSING"]]
    if Job.get_job_with_params(user, recv_data).filter(status__in=job_status_not_finished).exists():
        return HttpResponse("Same export processing is under execution", status=400)

    # create a job to export search result and run it
    job = Job.new_export_search_result(
        user,
        **{
            "text": "search_results.%s" % recv_data["export_style"],
            "params": recv_data,
        }
    )
    job.run()

    return JsonResponse(
        {"result": "Succeed in registering export processing. " + "Please check Job list."}
    )
