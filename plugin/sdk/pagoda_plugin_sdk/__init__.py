"""
Pagoda Core - Plugin Development Framework

This package provides the core foundation for developing plugins in the Pagoda ecosystem.
It offers base classes, interfaces, and utilities that enable plugins to be completely
independent from the host application.
"""

from .exceptions import (
    PagodaError,
    PluginError,
    PluginLoadError,
    PluginSecurityError,
    PluginValidationError,
)
from .plugin import Plugin
from .utils import get_pagoda_version


# Lazy import for Django-dependent components
def _lazy_import_mixins():
    """Lazy import of Django-dependent mixins"""
    try:
        from .mixins import PluginAPIViewMixin

        return PluginAPIViewMixin
    except ImportError as e:
        if "django" in str(e).lower() or "rest_framework" in str(e).lower():
            raise ImportError(
                "Django and Django REST Framework are required "
                "to use PluginAPIViewMixin. "
                "Please install Django and djangorestframework, "
                "or import this mixin directly when Django is configured."
            )
        raise


def _lazy_import_api():
    """Lazy import of Django REST Framework dependent API components"""
    try:
        from .api import (
            PluginAPIView,
            PluginPagination,
            PluginPermission,
            PluginSerializerMixin,
            PluginViewSet,
        )

        return (
            PluginViewSet,
            PluginAPIView,
            PluginPagination,
            PluginPermission,
            PluginSerializerMixin,
        )
    except ImportError as e:
        if "django" in str(e).lower() or "rest_framework" in str(e).lower():
            raise ImportError(
                "Django and Django REST Framework are required to use API components. "
                "Please install Django and djangorestframework, "
                "or import these components directly when Django is configured."
            )
        raise


def _lazy_import_tasks():
    """Lazy import of task-related components"""
    try:
        from .tasks import (
            Job,
            JobOperation,
            JobStatus,
            JobTarget,
            PluginTaskConfig,
            PluginTaskRegistry,
            celery_app,
            register_plugin_job_task,
        )

        return (
            celery_app,
            PluginTaskRegistry,
            PluginTaskConfig,
            register_plugin_job_task,
            Job,
            JobStatus,
            JobOperation,
            JobTarget,
        )
    except ImportError as e:
        if "airone" in str(e).lower() or "celery" in str(e).lower() or "job" in str(e).lower():
            raise ImportError(
                "Task components require the host application to be installed. "
                "These components are only available when the plugin is running "
                "within the AirOne environment."
            )
        raise


def _lazy_import_override():
    """Lazy import of entry operation override components"""
    try:
        from .override import (
            OverrideContext,
            OverrideMeta,
            accepted_response,
            created_response,
            error_response,
            no_content_response,
            not_found_response,
            override_operation,
            permission_denied_response,
            success_response,
            validation_error_response,
        )

        return {
            "override_operation": override_operation,
            "OverrideMeta": OverrideMeta,
            "OverrideContext": OverrideContext,
            "success_response": success_response,
            "created_response": created_response,
            "accepted_response": accepted_response,
            "no_content_response": no_content_response,
            "error_response": error_response,
            "not_found_response": not_found_response,
            "permission_denied_response": permission_denied_response,
            "validation_error_response": validation_error_response,
        }
    except ImportError as e:
        if "rest_framework" in str(e).lower():
            raise ImportError(
                "Override components require Django REST Framework. "
                "Please install djangorestframework or import directly when configured."
            )
        raise


_OVERRIDE_NAMES = [
    "override_operation",
    "OverrideMeta",
    "OverrideContext",
    "success_response",
    "created_response",
    "accepted_response",
    "no_content_response",
    "error_response",
    "not_found_response",
    "permission_denied_response",
    "validation_error_response",
]


# Define lazy properties for mixins, API components, and task components
def __getattr__(name):
    if name == "PluginAPIViewMixin":
        return _lazy_import_mixins()
    elif name in (
        "PluginViewSet",
        "PluginAPIView",
        "PluginPagination",
        "PluginPermission",
        "PluginSerializerMixin",
    ):
        api_classes = _lazy_import_api()
        api_names = [
            "PluginViewSet",
            "PluginAPIView",
            "PluginPagination",
            "PluginPermission",
            "PluginSerializerMixin",
        ]
        if name in api_names:
            return api_classes[api_names.index(name)]
    elif name in (
        "celery_app",
        "PluginTaskRegistry",
        "PluginTaskConfig",
        "register_plugin_job_task",
        "Job",
        "JobStatus",
        "JobOperation",
        "JobTarget",
    ):
        task_classes = _lazy_import_tasks()
        task_names = [
            "celery_app",
            "PluginTaskRegistry",
            "PluginTaskConfig",
            "register_plugin_job_task",
            "Job",
            "JobStatus",
            "JobOperation",
            "JobTarget",
        ]
        if name in task_names:
            return task_classes[task_names.index(name)]
    elif name in _OVERRIDE_NAMES:
        override_components = _lazy_import_override()
        return override_components[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__version__ = "1.0.0"

__all__ = [
    # Core classes
    "Plugin",
    # Exceptions
    "PagodaError",
    "PluginError",
    "PluginLoadError",
    "PluginValidationError",
    "PluginSecurityError",
    # Mixins for plugin development
    "PluginAPIViewMixin",
    # API components (Django REST Framework dependent)
    "PluginViewSet",
    "PluginAPIView",
    "PluginPagination",
    "PluginPermission",
    "PluginSerializerMixin",
    # Task components (host application dependent)
    "celery_app",
    "PluginTaskRegistry",
    "PluginTaskConfig",
    "register_plugin_job_task",
    "Job",
    "JobStatus",
    "JobOperation",
    "JobTarget",
    # Entry operation override components
    "override_operation",
    "OverrideMeta",
    "OverrideContext",
    "success_response",
    "created_response",
    "accepted_response",
    "no_content_response",
    "error_response",
    "not_found_response",
    "permission_denied_response",
    "validation_error_response",
    # Utilities
    "get_pagoda_version",
]
