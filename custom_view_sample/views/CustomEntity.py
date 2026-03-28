from airone.lib.http import render
from custom_view.lib.task import JobOperationCustom
from job.models import Job


def list_entry(request, entity, context):
    return render(request, "custom_view/list_custom_entry.html", context)


def after_create_entry(recv_data, user, entry):
    job = Job.new_create(
        **{
            "user": user,
            "target": entry,
        }
    )

    operation = JobOperationCustom.UPDATE_CUSTOM_ATTRIBUTE
    job.update(
        operation=operation,
    )
    job.run()
