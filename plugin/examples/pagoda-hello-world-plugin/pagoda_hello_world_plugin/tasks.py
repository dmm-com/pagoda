"""
Celery tasks for Hello World Plugin

This module demonstrates how to implement async tasks using Airone's
Celery integration.
"""

import logging

from airone.celery import app
from airone.lib.plugin_task import register_plugin_job_task
from job.models import Job, JobStatus
from pagoda_hello_world_plugin.config import HelloWorldPluginOperation

logger = logging.getLogger("airone.plugins.hello_world")


@register_plugin_job_task(HelloWorldPluginOperation.HELLO_WORLD_TASK)
@app.task(bind=True)
def hello_world_task(self, job_id: int):
    """Hello World task - does nothing but demonstrate task execution

    This is a simple task that demonstrates:
    - Task function definition with @app.task
    - Job lifecycle management
    - Status updates
    - Error handling

    Args:
        job_id: The Job ID to process
    """
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found")
        return

    logger.info(f"[Hello World Plugin] Starting hello_world_task for job {job_id}")

    # Check job cancellation and readiness
    if job.is_canceled():
        logger.info(f"Job {job_id} was canceled")
        return

    if not job.proceed_if_ready():
        logger.info(f"Job {job_id} is not ready yet")
        return

    job.update(JobStatus.PROCESSING)

    try:
        # This task does nothing - just a placeholder
        logger.info(f"[Hello World Plugin] Task executed successfully for job {job_id}")

        job.update(JobStatus.DONE)

    except Exception as e:
        logger.error(f"[Hello World Plugin] Task failed for job {job_id}: {e}")
        job.update(JobStatus.ERROR)
