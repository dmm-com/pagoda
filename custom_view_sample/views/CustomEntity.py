from typing import Any

from django.http import HttpRequest, HttpResponse

from airone.lib.http import render
from custom_view.lib.task import JobOperationCustom
from entity.models import Entity
from entry.models import Entry
from job.models import Job
from user.models import User


def list_entry(request: HttpRequest, entity: Entity, context: dict[str, Any]) -> HttpResponse:
    return render(request, "custom_view/list_custom_entry.html", context)


def after_create_entry(recv_data: dict[str, Any], user: User, entry: Entry) -> None:
    job = Job.new_create(
        user=user,
        target=entry,
    )

    operation = JobOperationCustom.UPDATE_CUSTOM_ATTRIBUTE
    job.update(
        operation=operation,
    )
    job.run()
