"""
Plugin task support module

This module provides Celery task integration for plugins.
All task-related functionality is re-exported from the host application.

Plugin developers should import task-related components from this module
instead of directly importing from the host application modules.

Example:
    from pagoda_plugin_sdk.tasks import (
        celery_app,
        register_plugin_job_task,
        Job,
        JobStatus,
    )

    @register_plugin_job_task(0)
    @celery_app.task(bind=True)
    def my_task(self, job_id: int):
        job = Job.objects.get(id=job_id)
        # ... task implementation

Note:
    This module uses lazy imports to avoid circular import issues.
    Components are imported only when first accessed.
"""

# Cache for lazy-loaded components
_cache = {}


_EXPORTED_NAMES = [
    # Celery application
    "celery_app",
    # Plugin task registry
    "PluginTaskRegistry",
    "PluginTaskConfig",
    "register_plugin_job_task",
    # Job models
    "Job",
    "JobStatus",
    "JobOperation",
    "JobTarget",
]


def __getattr__(name):
    """Lazy import of task components to avoid circular imports"""
    if name in _cache:
        return _cache[name]

    if name == "celery_app":
        from airone.celery import app as celery_app

        _cache[name] = celery_app
        return celery_app
    elif name in ("PluginTaskConfig", "PluginTaskRegistry", "register_plugin_job_task"):
        from airone.lib.plugin_task import (
            PluginTaskConfig,
            PluginTaskRegistry,
            register_plugin_job_task,
        )

        _cache["PluginTaskConfig"] = PluginTaskConfig
        _cache["PluginTaskRegistry"] = PluginTaskRegistry
        _cache["register_plugin_job_task"] = register_plugin_job_task
        return _cache[name]
    elif name in ("Job", "JobStatus", "JobOperation", "JobTarget"):
        from job.models import Job, JobOperation, JobStatus, JobTarget

        _cache["Job"] = Job
        _cache["JobStatus"] = JobStatus
        _cache["JobOperation"] = JobOperation
        _cache["JobTarget"] = JobTarget
        return _cache[name]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__():
    """Return list of available attributes for dir() and autocomplete"""
    return _EXPORTED_NAMES
