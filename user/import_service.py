from typing import Any

from airone.exceptions import ImportDataError
from group.models import Group
from user.models import User


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
