from typing import Any

from group.models import Group
from user.models import User


class ImportDataError(Exception):
    """The content of an import file cannot be applied (e.g. it names a missing record)."""


def validate_user_import_data(import_datas: list[dict[str, Any]]) -> None:
    """Check the keys a user import record must carry, before anything is written."""
    for user_data in import_datas:
        for param in ["username", "groups", "email"]:
            if param not in user_data:
                raise ImportDataError("'%s' is required" % param)


def import_users(import_datas: list[dict[str, Any]]) -> None:
    validate_user_import_data(import_datas)

    for user_data in import_datas:
        user: User | None = None
        if "id" in user_data:
            # update user by id when id is specified
            user = User.objects.filter(id=user_data["id"]).first()
            if not user:
                raise ImportDataError(
                    "Specified id user does not exist(id:%s, user:%s)"
                    % (user_data["id"], user_data["username"])
                )
            if (user.username != user_data["username"]) and (
                User.objects.filter(username=user_data["username"]).count() > 0
            ):
                raise ImportDataError(
                    "New username is already used(id:%s, user:%s->%s)"
                    % (user_data["id"], user.username, user_data["username"])
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

        new_groups: list[Group] = []
        for group_name in user_data["groups"].split(","):
            if group_name == "":
                continue
            new_group: Group | None = Group.objects.filter(name=group_name).first()
            if not new_group:
                raise ImportDataError(
                    "Specified group does not exist(user:%s, group:%s)"
                    % (user_data["username"], group_name)
                )
            new_groups.append(new_group)

        user.groups.set(new_groups)
        user.save()


def import_groups(import_datas: list[dict[str, Any]]) -> None:
    for group_data in import_datas:
        if "id" in group_data:
            # update group by id
            group = Group.objects.filter(id=group_data["id"]).first()
            if not group:
                raise ImportDataError(
                    "Specified id group does not exist(id:%s, group:%s)"
                    % (group_data["id"], group_data["name"])
                )

            # check new name is not used
            if (group.name != group_data["name"]) and (
                Group.objects.filter(name=group_data["name"]).count() > 0
            ):
                raise ImportDataError(
                    "New group name is already used(id:%s, group:%s->%s)"
                    % (group_data["id"], group.name, group_data["name"])
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
