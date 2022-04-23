from airone.lib.http import http_get, http_post
from airone.lib.http import render
from django.http import HttpResponse
from django.http.response import JsonResponse

from group.models import Group
from user.models import User
from role.models import Role


def set_role_members(role, recv_data):
    for (model, member, key) in [
        (User, "users", "users"),
        (Group, "groups", "groups"),
        (User, "admin_users", "admin_users"),
        (Group, "admin_groups", "admin_groups"),
    ]:
        for obj in recv_data[key]:
            instance = model.objects.filter(id=obj["id"], is_active=True).first()
            if instance:
                getattr(role, member).add(instance)


def is_role_editable(role, recv_data):
    admin_users = [
        User.objects.get(id=u["id"])
        for u in recv_data["admin_users"]
        if User.objects.filter(id=u["id"], is_active=True).exists()
    ]
    admin_groups = [
        Group.objects.get(id=g["id"])
        for g in recv_data["admin_groups"]
        if Group.objects.filter(id=g["id"]).exists()
    ]

    return Role.editable(role, admin_users, admin_groups)


def initialize_role_context():
    context = {}
    for k in ["user_info", "admin_user_info"]:
        context[k] = {
            u.id: {
                "name": u.username,
                "type": "user",
            }
            for u in User.objects.filter(is_active=True).order_by("username")
        }

    for k in ["group_info", "admin_group_info"]:
        context[k] = {
            g.id: {
                "name": g.name,
                "type": "group",
            }
            for g in Group.objects.filter(is_active=True).order_by("name")
        }

    return context


@http_get
def index(request):
    context = {}
    context["roles"] = [
        {
            "id": x.id,
            "name": x.name,
            "description": x.description,
            "users": x.users.all().order_by("username"),
            "groups": x.groups.all().order_by("name"),
            "admin_users": x.admin_users.all().order_by("username"),
            "admin_groups": x.admin_groups.all().order_by("name"),
        }
        for x in Role.objects.filter(is_active=True)
    ]

    return render(request, "role/list.html", context)


@http_get
def create(request):
    # get user and group members that are selectable as role members
    context = initialize_role_context()
    context["submit_ref"] = "/role/do_create/"

    return render(request, "role/create.html", context)


@http_post(
    [
        {"name": "name", "type": str, "checker": lambda x: x["name"]},
        {"name": "description", "type": str},
        {"name": "users", "type": list, "meta": [{"name": "id", "type": int}]},
        {"name": "groups", "type": list, "meta": [{"name": "id", "type": int}]},
        {"name": "admin_users", "type": list, "meta": [{"name": "id", "type": int}]},
        {"name": "admin_groups", "type": list, "meta": [{"name": "id", "type": int}]},
    ]
)
def do_create(request, recv_data):
    if Role.objects.filter(name=recv_data["name"], is_active=True).exists():
        return HttpResponse("Duplicate named role has already been registered", status=400)

    # This checks whether specified parameter might make this role not to be able to
    # delete this role by this user.
    if not is_role_editable(request.user, recv_data):
        return HttpResponse(
            "You can't edit this role. Please set administrative members", status=400
        )

    # create role instance that has specified name and description parameters
    role = Role.objects.create(
        **{
            "name": recv_data["name"],
            "description": recv_data["description"] if recv_data["description"] else "",
        }
    )

    # set users and groups, which include administrative ones, to role instance
    set_role_members(role, recv_data)

    return JsonResponse({"msg": 'Succeeded in creating new Role "%s"' % recv_data["name"]})


@http_get
def edit(request, role_id):
    user = request.user
    role = Role.objects.filter(id=role_id, is_active=True).first()
    if not role:
        return HttpResponse("Specified Role(id:%d) does not exist" % role_id, status=400)

    if not role.is_editable(user):
        return HttpResponse("You do not have permission to change this role", status=400)

    # get user and group members that are selectable as role members
    context = initialize_role_context()
    context["submit_ref"] = "/role/do_edit/%d/" % role.id

    # update users/groups context to set what users and groups are registered on role
    context["name"] = role.name
    context["description"] = role.description
    for (key, nameattr, model) in [
        ("user_info", "username", role.users),
        ("group_info", "name", role.groups),
        ("admin_user_info", "username", role.admin_users),
        ("admin_group_info", "name", role.admin_groups),
    ]:

        for instance in model.filter(is_active=True):
            context[key][instance.id].update(
                {
                    "name": getattr(instance, nameattr),
                    "is_checked": "true",
                }
            )

    return render(request, "role/create.html", context)


@http_post(
    [
        {"name": "name", "type": str, "checker": lambda x: x["name"]},
        {"name": "description", "type": str},
        {"name": "users", "type": list, "meta": [{"name": "id", "type": int}]},
        {"name": "groups", "type": list, "meta": [{"name": "id", "type": int}]},
        {"name": "admin_users", "type": list, "meta": [{"name": "id", "type": int}]},
        {"name": "admin_groups", "type": list, "meta": [{"name": "id", "type": int}]},
    ]
)
def do_edit(request, role_id, recv_data):
    user = request.user
    role = Role.objects.filter(id=role_id, is_active=True).first()
    if not role:
        return HttpResponse("Specified Role(id:%d) does not exist" % role_id, status=400)

    dup_role = Role.objects.filter(name=recv_data["name"], is_active=True).first()
    if dup_role and dup_role.id != int(role_id):
        return HttpResponse("Other duplicate named role has already been registered", status=400)

    if not role.is_editable(user):
        return HttpResponse("You do not have permission to change this role", status=400)

    # This checks whether specified parameter might make this role not to be able to
    # delete this role by this user.
    if not is_role_editable(user, recv_data):
        return HttpResponse(
            "You can't edit this role. Please set administrative members", status=400
        )

    # clear registered members (users, groups and administrative ones) to that role
    for key in ["users", "groups", "admin_users", "admin_groups"]:
        getattr(role, key).clear()

    # set users and groups, which include administrative ones, to role instance
    set_role_members(role, recv_data)

    # update attributes of role instance
    update_fields = []
    for key in ["name", "description"]:
        if getattr(role, key) != recv_data.get(key):
            setattr(role, key, recv_data.get(key))
            update_fields.append(key)

    role.save(update_fields=update_fields)

    return JsonResponse({"msg": 'Succeeded in creating new Role "%s"' % recv_data["name"]})
