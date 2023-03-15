import codecs
import importlib
import json
import urllib.parse
from urllib.parse import quote

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render as django_render
from django.utils.encoding import smart_str

from airone.lib.acl import ACLObjType
from airone.lib.types import AttrTypes, AttrTypeValue
from entity import models as entity_models
from entry import models as entry_models
from job.models import Job, JobOperation
from user.models import History, User


class HttpResponseSeeOther(HttpResponseRedirect):
    status_code = 303


class DRFRequest(dict):
    def __init__(self, user: User):
        self.user = user


def http_get(func):
    def wrapper(*args, **kwargs):
        request = args[0]
        if request.method != "GET":
            return HttpResponse("Invalid HTTP method is specified", status=400)

        if not request.user.is_authenticated:
            return HttpResponseSeeOther(
                "/auth/login?next=%s?%s" % (request.path, quote(request.GET.urlencode()))
            )

        return func(*args, **kwargs)

    return wrapper


def get_obj_with_check_perm(user, model, object_id, permission_level):
    target_obj = model.objects.filter(id=object_id).first()
    if not target_obj:
        return (None, HttpResponse("Failed to get entity of specified id", status=400))

    # only requests that have correct permission are executed
    if not user.has_permission(target_obj, permission_level):
        return (
            None,
            HttpResponse("You don't have permission to access this object", status=400),
        )

    # This also checks parent permission if object is Entry, Attribute or EntityAttr
    airone_instance = target_obj.get_subclass_object()
    if isinstance(airone_instance, entry_models.Entry):
        if not user.has_permission(airone_instance.schema, permission_level):
            return (
                None,
                HttpResponse("You don't have permission to access this object", status=400),
            )

    elif isinstance(airone_instance, entity_models.EntityAttr):
        if not user.has_permission(airone_instance.parent_entity, permission_level):
            return (
                None,
                HttpResponse("You don't have permission to access this object", status=400),
            )

    elif isinstance(airone_instance, entry_models.Attribute):
        if (
            not user.has_permission(airone_instance.parent_entry, permission_level)
            or not user.has_permission(airone_instance.parent_entry.schema, permission_level)
            or not user.has_permission(airone_instance.schema, permission_level)
            or not user.has_permission(airone_instance.schema.parent_entity, permission_level)
        ):
            return (
                None,
                HttpResponse("You don't have permission to access this object", status=400),
            )

    return (target_obj, None)


def check_superuser(func):
    def wrapper(*args, **kwargs):
        request = args[0]

        if not request.user.is_authenticated:
            return HttpResponseSeeOther("/auth/login")

        if not request.user.is_superuser:
            return HttpResponse("This page needs administrative permission to access", status=400)

        return func(*args, **kwargs)

    return wrapper


def http_post(validator=[]):
    def _decorator(func):
        def http_post_handler(*args, **kwargs):
            request = args[0]

            if request.method != "POST":
                return HttpResponse("Invalid HTTP method is specified", status=400)

            if not request.user.is_authenticated:
                return HttpResponse("You have to login to execute this operation", status=401)

            try:
                kwargs["recv_data"] = json.loads(request.body.decode("utf-8"))
            except json.decoder.JSONDecodeError:
                return HttpResponse("Failed to parse string to JSON", status=400)

            if not _is_valid(kwargs["recv_data"], validator):
                return HttpResponse("Invalid parameters are specified", status=400)

            return func(*args, **kwargs)

        return http_post_handler

    return _decorator


def http_file_upload(func):
    def get_uploaded_file_content(request):
        """This returns uploaded file context whatever encoding type"""

        fp = request.FILES.get("file")
        for encoding in ["UTF-8", "Shift-JIS", "ISO-2022-JP", "EUC-JP"]:
            try:
                return codecs.getreader(encoding)(fp).read()

            except UnicodeDecodeError:
                fp.seek(0)

            except Exception:
                return None

    def wrapper(*args, **kwargs):
        request = args[0]

        if request.method != "POST":
            return HttpResponse("Invalid HTTP method is specified", status=400)

        kwargs["context"] = get_uploaded_file_content(request)
        if not kwargs["context"]:
            return HttpResponse("Uploaded file is invalid", status=400)

        return func(*args, **kwargs)

    return wrapper


def render(request, template, context={}):
    # added default parameters for navigate
    entity_objects = entity_models.Entity.objects.order_by("name").filter(is_active=True)
    context["navigator"] = {
        "entities": [x for x in entity_objects],
        "acl_objtype": {
            "entity": ACLObjType.Entity,
            "entry": ACLObjType.Entry,
            "attrbase": ACLObjType.EntityAttr,
            "attr": ACLObjType.EntryAttr,
        },
    }

    # set constants for operation history
    context["OPERATION_HISTORY"] = {
        "ADD_ENTITY": History.ADD_ENTITY,
        "ADD_ATTR": History.ADD_ATTR,
        "MOD_ENTITY": History.MOD_ENTITY,
        "MOD_ATTR": History.MOD_ATTR,
        "DEL_ENTITY": History.DEL_ENTITY,
        "DEL_ATTR": History.DEL_ATTR,
        "DEL_ENTRY": History.DEL_ENTRY,
    }

    # set constracts for job
    context["JOB"] = {
        "STATUS": Job.STATUS,
        "OPERATION": {
            "CREATE": JobOperation.CREATE_ENTRY.value,
            "EDIT": JobOperation.EDIT_ENTRY.value,
            "DELETE": JobOperation.DELETE_ENTRY.value,
            "COPY": JobOperation.COPY_ENTRY.value,
            "DO_COPY": JobOperation.DO_COPY_ENTRY.value,
            "IMPORT": JobOperation.IMPORT_ENTRY.value,
            "IMPORT_V2": JobOperation.IMPORT_ENTRY_V2.value,
            "EXPORT": JobOperation.EXPORT_ENTRY.value,
            "EXPORT_V2": JobOperation.EXPORT_ENTRY_V2.value,
            "RESTORE": JobOperation.RESTORE_ENTRY.value,
            "EXPORT_SEARCH_RESULT": JobOperation.EXPORT_SEARCH_RESULT.value,
            "CREATE_ENTITY": JobOperation.CREATE_ENTITY.value,
            "EDIT_ENTITY": JobOperation.EDIT_ENTITY.value,
            "DELETE_ENTITY": JobOperation.DELETE_ENTITY.value,
        },
    }

    # set constant values which are defined in each applications
    context["config"] = {}
    for app in ["entry"]:
        config = importlib.import_module("%s.settings" % app).CONFIG
        context["config"][app] = config.TEMPLATE_CONFIG

    context["attr_type"] = {}
    for attr_type in AttrTypes:
        context["attr_type"][attr_type.NAME] = attr_type.TYPE
    context["attr_type_value"] = AttrTypeValue

    # set Construct for Entity status
    context["STATUS_ENTITY"] = {}
    context["STATUS_ENTITY"]["TOP_LEVEL"] = entity_models.Entity.STATUS_TOP_LEVEL
    context["STATUS_ENTITY"]["CREATING"] = entry_models.Entity.STATUS_CREATING
    context["STATUS_ENTITY"]["EDITING"] = entry_models.Entity.STATUS_EDITING

    # set Construct for Entry status
    context["STATUS_ENTRY"] = {}
    context["STATUS_ENTRY"]["CREATING"] = entry_models.Entry.STATUS_CREATING
    context["STATUS_ENTRY"]["EDITING"] = entry_models.Entry.STATUS_EDITING

    # set Version
    context["version"] = settings.AIRONE["VERSION"]

    return django_render(request, template, context)


def get_download_response(io_stream, fname):
    response = HttpResponse(io_stream.getvalue(), content_type="application/force-download")
    response["Content-Disposition"] = 'attachment; filename="{fn}"'.format(
        fn=urllib.parse.quote(smart_str(fname))
    )
    return response


def _is_valid(params, meta_info):
    if not isinstance(params, dict):
        return False
    # These are existance checks of each parameters except for ones which has omittable parameter
    if not all([x["name"] in params for x in meta_info if "omittable" not in x]):
        return False
    # These are type checks of each parameters
    if not all(
        [isinstance(params[x["name"]], x["type"]) for x in meta_info if x["name"] in params.keys()]
    ):
        return False
    # These are value checks of each parameters
    for _meta in meta_info:
        # Skip no value
        if "omittable" in _meta and _meta["name"] not in params:
            continue

        # The case specified value is str
        if _meta["type"] == str and "checker" in _meta and not _meta["checker"](params):
            return False

        # The case specified value is list
        if _meta["type"] == list:
            if "checker" in _meta and not _meta["checker"](params):
                return False

            if "meta" in _meta and not all(
                [_is_valid(x, _meta["meta"]) for x in params[_meta["name"]]]
            ):
                return False

    return True
