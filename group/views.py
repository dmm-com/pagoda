import io
from typing import Any, Dict

import yaml
from django.http import HttpResponse
from django.http.response import JsonResponse

from airone.lib.http import (
    HttpResponseSeeOther,
    check_superuser,
    get_download_response,
    http_file_upload,
    http_get,
    http_post,
    render,
)
from group.models import Group
from job.models import Job, JobOperation
from user.models import User


@http_get
def index(request):
    return render(request, "list_group.html", {})


@http_get
@check_superuser
def edit(request, group_id):
    if not Group.objects.filter(id=group_id).exists():
        return HttpResponse("Failed to get group of specified id", status=400)

    group = Group.objects.get(id=group_id)

    # set selected group information
    context: Dict[str, Any] = {
        "default_group_id": int(group_id),
        "current_group_name": group.name,
        "current_group_members": User.objects.filter(groups__id=group.id, is_active=True).order_by(
            "username"
        ),
        "submit_ref": "/group/do_edit/%s" % group_id,
        "parent_group_id": group.parent_group.id if group.parent_group else 0,
    }

    # set group members for each groups
    context["groups"] = [
        {
            "id": x.id,
            "name": x.name,
            "members": User.objects.filter(groups__id=x.id, is_active=True).order_by("username"),
        }
        for x in Group.objects.filter(is_active=True)
    ]

    # set all user
    context["groups"].insert(
        0,
        {
            "id": 0,
            "name": "-- ALL --",
            "members": User.objects.filter(is_active=True),
        },
    )

    return render(request, "edit_group.html", context)


@http_post(
    [
        {"name": "name", "type": str, "checker": lambda x: x["name"]},
        {
            "name": "users",
            "type": list,
            "checker": lambda x: (
                all([User.objects.filter(id=u).exists() for u in x.get("users", [])])
            ),
        },
        {"name": "parent_group", "type": str, "omittable": True},
    ]
)
@check_superuser
def do_edit(request, group_id, recv_data):
    if not Group.objects.filter(id=group_id).exists():
        return HttpResponse("Failed to get group of specified id", status=400)

    group = Group.objects.get(id=group_id)
    if Group.objects.filter(name=recv_data["name"]).exists():
        same_name_group = Group.objects.get(name=recv_data["name"])

        if group.id != same_name_group.id:
            return HttpResponse(
                "Failed to update because there is another group of same name",
                status=400,
            )

    # get users who are belonged to the selected group for updating
    old_users = [str(x.id) for x in User.objects.filter(groups__id=group_id, is_active=True)]
    job_register_referrals = None
    if group.name != recv_data["name"]:
        job_register_referrals = Job.new_register_referrals(
            request.user,
            None,
            operation_value=JobOperation.GROUP_REGISTER_REFERRAL,
            params={"group_id": group.id},
        )

    # update group_name with specified one
    group.name = recv_data["name"]
    group.parent_group = Group.objects.filter(
        id=recv_data.get("parent_group", 0), is_active=True
    ).first()
    group.save()

    if job_register_referrals:
        job_register_referrals.run()

    # the processing for deleted users
    for user in [User.objects.get(id=x) for x in set(old_users) - set(recv_data.get("users", []))]:
        user.groups.remove(group)

    # the processing for added users
    for user in [User.objects.get(id=x) for x in set(recv_data.get("users", [])) - set(old_users)]:
        user.groups.add(group)

    return JsonResponse(
        {
            "msg": 'Success to update Group "%s"' % group.name,
        }
    )


@http_get
@check_superuser
def create(request):
    context = {
        "default_group_id": 0,
        "submit_ref": "/group/do_create",
    }

    # set group members for each groups
    context["groups"] = [
        {
            "id": x.id,
            "name": x.name,
            "members": User.objects.filter(groups__id=x.id, is_active=True).order_by("username"),
        }
        for x in Group.objects.filter(is_active=True)
    ]

    # set all user
    context["groups"].insert(
        0,
        {
            "id": 0,
            "name": "-- ALL --",
            "members": User.objects.filter(is_active=True),
        },
    )
    context["parent_group_id"] = 0

    return render(request, "edit_group.html", context)


@http_post(
    [
        {
            "name": "name",
            "type": str,
            "checker": lambda x: (x["name"] and not Group.objects.filter(name=x["name"]).exists()),
        },
        {
            "name": "users",
            "type": list,
            "checker": lambda x: (
                all([User.objects.filter(id=u).exists() for u in x.get("users", [])])
            ),
        },
        {"name": "parent_group", "type": str, "omittable": True},
    ]
)
@check_superuser
def do_create(request, recv_data):
    new_group = Group(
        name=recv_data["name"],
        parent_group=Group.objects.filter(
            id=recv_data.get("parent_group", 0), is_active=True
        ).first(),
    )
    new_group.save()

    for user in [User.objects.get(id=x) for x in recv_data.get("users", [])]:
        user.groups.add(new_group)

    return JsonResponse(
        {
            "msg": 'Success to create a new Group "%s"' % new_group.name,
        }
    )


@http_post()
@check_superuser
def do_delete(request, group_id, recv_data):
    group = Group.objects.get(id=group_id)
    ret = {}

    # save deleting target name before do it
    ret["name"] = group.name

    # unregister target group from user object settings
    for user in User.objects.filter(groups__id=group.id):
        user.groups.remove(group)
        user.save()

    group.delete()

    return JsonResponse(ret)


@http_get
def export(request):
    output = io.StringIO()

    data = {
        "Group": [],
        "User": [],
    }

    for group in Group.objects.filter(is_active=True):
        data["Group"].append(
            {
                "id": group.id,
                "name": group.name,
            }
        )

    for user in User.objects.filter(is_active=True):
        data["User"].append(
            {
                "email": user.email,
                "groups": ",".join(
                    list(map(lambda x: x.name, user.groups.filter(group__is_active=True)))
                ),
                "id": user.id,
                "username": user.username,
            }
        )

    output.write(yaml.dump(data, default_flow_style=False, allow_unicode=True))
    return get_download_response(output, "user_group.yaml")


@http_get
@check_superuser
def import_user_and_group(request):
    return render(request, "import_user_and_group.html", {})


@http_file_upload
@check_superuser
def do_import_user_and_group(request, context):
    try:
        data = yaml.load(context, Loader=yaml.SafeLoader)
    except (yaml.parser.ParserError, yaml.scanner.ScannerError):
        return HttpResponse("Couldn't parse uploaded file", status=400)

    # complement if empty in request
    if "Group" not in data:
        data["Group"] = []

    if "User" not in data:
        data["User"] = []

    # update or create group
    #
    # because names of groups are needed when create or update user,
    # groups should be update or create in advance
    for group_data in data["Group"]:
        if "name" not in group_data:
            return HttpResponse("Group name is required", status=400)

        if "id" in group_data:
            # update group by id
            group = Group.objects.filter(id=group_data["id"]).first()
            if not group:
                return HttpResponse(
                    "Specified id group does not exist(id:%s, group:%s)"
                    % (group_data["id"], group_data["name"]),
                    status=400,
                )

            # check new name is not used
            if (group.name != group_data["name"]) and (
                Group.objects.filter(name=group_data["name"]).count() > 0
            ):
                return HttpResponse(
                    "New group name is already used(id:%s, group:%s->%s)"
                    % (group_data["id"], group.name, group_data["name"]),
                    status=400,
                )

            group.name = group_data["name"]
            group.save()
        else:
            # update group by name
            group = Group.objects.filter(name=group_data["name"]).first()
            if not group:
                # create group
                group = Group(name=group_data["name"])
            group.save()

    # update or create user
    for user_data in data["User"]:
        for param in ["username", "groups", "email"]:
            if param not in user_data:
                return HttpResponse("'%s' is required" % param, status=400)

        user = None
        if "id" in user_data:
            # update user by id when id is specified
            user = User.objects.filter(id=user_data["id"]).first()
            if not user:
                return HttpResponse(
                    "Specified id user does not exist(id:%s, user:%s)"
                    % (user_data["id"], user_data["username"]),
                    status=400,
                )
            if (user.username != user_data["username"]) and (
                User.objects.filter(username=user_data["username"]).count() > 0
            ):
                return HttpResponse(
                    "New username is already used(id:%s, user:%s->%s)"
                    % (user_data["id"], user.username, user_data["username"]),
                    status=400,
                )
        else:
            # update user by username
            user = User.objects.filter(username=user_data["username"]).first()
            if not user:
                # create user
                user = User(username=user_data["username"])
                user.save()

        user.username = user_data["username"]
        user.email = user_data["email"]

        new_groups = []
        for group_name in user_data["groups"].split(","):
            if group_name == "":
                continue
            new_group = Group.objects.filter(name=group_name).first()
            if not new_group:
                return HttpResponse(
                    "Specified group does not exist(user:%s, group:%s)"
                    % (user_data["username"], group_name),
                    status=400,
                )
            new_groups.append(new_group)

        user.groups.set(new_groups)
        user.save()

    return HttpResponseSeeOther("/group/")
