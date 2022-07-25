import importlib.util
import os
from pathlib import Path

from django.http import HttpResponse

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

# to cache custom view
CUSTOM_VIEW = {}


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


def is_custom(handler_name, entity_name=None):
    # When 'entity_name' is specified, this tries to load custom_view of Entry.
    # But it tries to load Entity's custom_view when 'entity_name' parameter doesn't specified.
    if entity_name:
        spec_name = entity_name
        filepath = "%s/views/%s.py" % (BASE_DIR, entity_name)
        if not Path(filepath).is_file():
            return False
    else:
        spec_name = "entity"
        filepath = "%s/entity.py" % BASE_DIR
        if not Path(filepath).is_file():
            return False

    return _does_custom_method_defined(handler_name, spec_name, filepath)


def call_custom(handler_name, spec_name=None, *args, **kwargs):
    if not spec_name:
        filepath = "%s/entity.py" % BASE_DIR
    else:
        filepath = "%s/views/%s.py" % (BASE_DIR, spec_name)

    if _isin_cache(filepath, handler_name):
        return CUSTOM_VIEW[filepath][handler_name](*args, **kwargs)
    else:
        return HttpResponse("Custom view of %s doesn't exist" % handler_name, status=500)
