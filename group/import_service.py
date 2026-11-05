from typing import Any

from airone.exceptions import ImportDataError
from group.models import Group


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
