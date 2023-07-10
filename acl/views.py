from django.http import HttpResponse
from django.http.response import JsonResponse

from airone.lib.acl import ACLObjType, ACLType
from airone.lib.http import get_obj_with_check_perm, http_get, http_post, render
from airone.lib.log import Logger
from entity.models import Entity, EntityAttr
from entry.models import Attribute, Entry
from role.models import Role

from .models import ACLBase


@http_get
def index(request, obj_id):
    aclbase_obj, error = get_obj_with_check_perm(request.user, ACLBase, obj_id, ACLType.Full)
    if error:
        return error
    target_obj = aclbase_obj.get_subclass_object()

    # Some type of objects needs object that refers target_obj (e.g. Attribute)
    # for showing breadcrumb navigation.
    parent_obj = None
    try:
        if isinstance(target_obj, Attribute):
            parent_obj = target_obj.parent_entry
        elif isinstance(target_obj, EntityAttr):
            parent_obj = target_obj.parent_entity
    except StopIteration:
        Logger.warning("failed to get related parent object")

    context = {
        "object": target_obj,
        "parent": parent_obj,
        "acltypes": [{"id": x.id, "name": x.label} for x in ACLType.all()],
        "roles": [
            {
                "id": x.id,
                "name": x.name,
                "description": x.description,
                "current_permission": x.get_current_permission(target_obj),
            }
            for x in Role.objects.filter(is_active=True)
            if request.user.is_superuser or x.is_belonged_to(request.user)
        ],
    }
    return render(request, "edit_acl.html", context)


@http_post(
    [
        {
            "name": "object_id",
            "type": str,
            "checker": lambda x: ACLBase.objects.filter(id=x["object_id"]).exists(),
        },
        {"name": "object_type", "type": str, "checker": lambda x: x["object_type"]},
        {
            "name": "acl",
            "type": list,
            "meta": [
                {
                    "name": "role_id",
                    "type": str,
                    "checker": lambda x: Role.objects.filter(
                        id=x["role_id"], is_active=True
                    ).exists(),
                },
                {
                    "name": "value",
                    "type": (str, type(None)),
                    "checker": lambda x: [y for y in ACLType.all() if int(x["value"]) == y],
                },
            ],
        },
        {
            "name": "default_permission",
            "type": str,
            "checker": lambda x: any([y == int(x["default_permission"]) for y in ACLType.all()]),
        },
    ]
)
def set(request, recv_data):
    acl_obj = getattr(_get_acl_model(recv_data["object_type"]), "objects").get(
        id=recv_data["object_id"]
    )

    # This checks that user currently has permission to change it
    if not request.user.has_permission(acl_obj, ACLType.Full):
        return HttpResponse(
            "User(%s) doesn't have permission to change this ACL" % request.user.username,
            status=400,
        )

    # This checks that user will have permission as user specifies by this change
    # (NOTE: this processing is completely different from above permission check)
    if not request.user.is_permitted_to_change(
        **{
            "target_obj": acl_obj,
            "expected_permission": ACLType.Full,
            "will_be_public": recv_data.get("is_public", False),
            "default_permission": int(recv_data["default_permission"]),
            "acl_settings": [
                {
                    "role": Role.objects.filter(id=x["role_id"], is_active=True).first(),
                    "value": int(x["value"]),
                }
                for x in recv_data["acl"]
            ],
        }
    ):
        return HttpResponse(
            "Inadmissible setting. By this change you will never change this ACL", status=400
        )

    if acl_obj.is_acl_updated(
        bool(recv_data.get("is_public", False)), int(recv_data["default_permission"])
    ):
        acl_obj.is_public = bool(recv_data.get("is_public", False))
        acl_obj.default_permission = int(recv_data["default_permission"])

        # update the Public/Private flag parameter
        acl_obj.save()

    for acl_data in [x for x in recv_data["acl"] if x["value"]]:
        role = Role.objects.get(id=acl_data["role_id"])
        acl_type = [x for x in ACLType.all() if x == int(acl_data["value"])][0]

        # update permissios for the target ACLBased object
        _set_permission(role, acl_obj, acl_type)

    redirect_url = "/"
    if isinstance(acl_obj, Entity):
        redirect_url = "/entity/"
    elif isinstance(acl_obj, EntityAttr):
        redirect_url = "/entity/edit/%s" % acl_obj.parent_entity.id
    elif isinstance(acl_obj, Entry):
        redirect_url = "/entry/show/%s" % acl_obj.id
    elif isinstance(acl_obj, Attribute):
        redirect_url = "/entry/edit/%s" % acl_obj.parent_entry.id

    if isinstance(acl_obj, Attribute):
        acl_obj = acl_obj.parent_entry

    if isinstance(acl_obj, Entry):
        acl_obj.register_es()

    return JsonResponse(
        {
            "redirect_url": redirect_url,
            "msg": 'Success to update ACL of "%s"' % acl_obj.name,
        }
    )


def _get_acl_model(object_id):
    if int(object_id) == ACLObjType.Entity.value:
        return Entity
    if int(object_id) == ACLObjType.Entry.value:
        return Entry
    elif int(object_id) == ACLObjType.EntityAttr.value:
        return EntityAttr
    elif int(object_id) == ACLObjType.EntryAttr.value:
        return Attribute
    else:
        return ACLBase


def _set_permission(role, acl_obj, acl_type):
    # clear unset permissions of target ACLbased object
    for _acltype in ACLType.all():
        if _acltype != acl_type and _acltype != ACLType.Nothing:
            permission = getattr(acl_obj, _acltype.name)
            # Delete only if the target role exists in the permission
            if permission.roles.filter(id=role.id):
                permission.roles.remove(role)

    # set new permission to be specified except for 'Nothing' permission
    if acl_type != ACLType.Nothing:
        permission = getattr(acl_obj, acl_type.name)
        # Add only if the target role doesn't exist in the permission
        if not permission.roles.filter(id=role.id):
            permission.roles.add(role)
