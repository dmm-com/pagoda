from typing import Any

from job.models import Job
from user.models import User


def start_entity_import_preview(user: User, import_data: dict[str, Any]) -> int:
    """Start a job that reports what an entity import file would change, and return its id.

    The entity preview endpoint and the common import preview both start it this way.
    """
    job = Job.new_import_entity_preview(user, import_data)
    job.run()
    return job.id
