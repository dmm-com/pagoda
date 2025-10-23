import importlib.util
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse

from airone.plugins.hook_manager import hook_manager

# to cache custom view
CUSTOM_VIEW = {}
BASE_DIR = settings.PROJECT_PATH + "/../custom_view"


def _isin_cache(filepath, method_name):
    return filepath in CUSTOM_VIEW and method_name in CUSTOM_VIEW[filepath]


def _does_custom_method_defined(method_name, spec_name, filepath):
    # return if cache is hit
    if _isin_cache(filepath, method_name):
        return True

    spec = importlib.util.spec_from_file_location(spec_name, filepath)
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)

    if filepath not in CUSTOM_VIEW:
        CUSTOM_VIEW[filepath] = {}

    if not hasattr(model, method_name):
        return False

    # set custom_view cache
    CUSTOM_VIEW[filepath][method_name] = getattr(model, method_name)

    return True


def is_custom(handler_name: str, entity_name: str | None = None) -> bool:
    # When 'entity_name' is specified, this tries to load custom_view of Entry.
    # But it tries to load Entity's custom_view when 'entity_name' parameter doesn't specified.
    if entity_name:
        spec_name = entity_name
        filepath = "%s/views/%s.py" % (BASE_DIR, entity_name)
        if Path(filepath).is_file() and _does_custom_method_defined(
            handler_name, spec_name, filepath
        ):
            return True
    else:
        spec_name = "entity"
        filepath = "%s/entity.py" % BASE_DIR
        if Path(filepath).is_file() and _does_custom_method_defined(
            handler_name, spec_name, filepath
        ):
            return True

    # Check if any plugin hooks are registered for this handler
    return hook_manager.has_hook(handler_name, entity_name)


def call_custom(handler_name: str, spec_name: str | None = None, *args, **kwargs):
    if not spec_name:
        filepath = "%s/entity.py" % BASE_DIR
    else:
        filepath = "%s/views/%s.py" % (BASE_DIR, spec_name)

    # Priority 1: Execute custom_view file-based handler if available
    if _isin_cache(filepath, handler_name):
        return CUSTOM_VIEW[filepath][handler_name](*args, **kwargs)

    # Priority 2: Execute plugin hooks if custom_view is not available
    results = hook_manager.execute_hook(handler_name, *args, entity_name=spec_name, **kwargs)
    if results:
        # Return the last result (if multiple plugins registered)
        return results[-1]

    return HttpResponse("Custom view of %s doesn't exist" % handler_name, status=500)
