from datetime import datetime, timedelta
from typing import Any

from airone.lib.acl import ACLType
from airone.lib.drf import FrequentImportError
from entity.models import Entity
from job.models import Job, JobOperation, JobStatus
from user.models import User


def start_entry_import_jobs(
    user: User,
    import_datas: list[dict[str, Any]],
    *,
    force: bool = False,
    preview_job_id: int | None = None,
) -> tuple[list[int], list[str]]:
    """Start one import job per model in an already validated item import file.

    Returns the ids of the started jobs and the per-model errors (unknown model,
    or no write permission on it) that kept a model from being imported.
    """
    entities = Entity.objects.filter(name__in=[d["entity"] for d in import_datas], is_active=True)

    # limit import job to deny accidental frequent import for same entity
    if not force:
        valid_statuses: list[JobStatus] = [
            JobStatus.PREPARING,
            JobStatus.PROCESSING,
            JobStatus.DONE,
        ]
        yesterday = datetime.now() - timedelta(days=1)
        if Job.objects.filter(
            status__in=valid_statuses,
            operation=JobOperation.IMPORT_ENTRY_V2,
            target__in=entities,
            created_at__gte=yesterday,
        ).exists():
            raise FrequentImportError("Import job for each entity can apply once a day.")

    job_ids: list[int] = []
    error_list: list[str] = []
    for import_data in import_datas:
        entity: Entity | None = next((e for e in entities if e.name == import_data["entity"]), None)
        if not entity:
            error_list.append("%s: Entity does not exists." % import_data["entity"])
            continue

        if not user.has_permission(entity, ACLType.Writable):
            error_list.append("%s: Entity is permission denied." % import_data["entity"])
            continue

        job = Job.new_import_v2(
            user,
            entity,
            text="Preparing to import data",
            params=(
                {**import_data, "preview_job_id": preview_job_id}
                if preview_job_id is not None
                else import_data
            ),
        )
        job.run()
        job_ids.append(job.id)

    return job_ids, error_list
