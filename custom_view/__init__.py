from pathlib import Path
from django.http import HttpResponse

import importlib.util
import os

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

# to cache custom view
CUSTOM_VIEW = {}


def _isin_cache(entity_name, method_name):
    return entity_name in CUSTOM_VIEW and method_name in CUSTOM_VIEW


def _is_view(entity_name, method_name):
    # return if cache is hit
    if _isin_cache(entity_name, method_name):
        return True

    filepath = '%s/views/%s.py' % (BASE_DIR, entity_name)
    if not Path(filepath).is_file():
        return False

    spec = importlib.util.spec_from_file_location(entity_name, filepath)
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)

    if entity_name not in CUSTOM_VIEW:
        CUSTOM_VIEW[entity_name] = {}

    if not hasattr(model, method_name):
        return False

    # set custom_view cache
    CUSTOM_VIEW[entity_name][method_name] = getattr(model, method_name)

    return True


# check custom_view handlerd exists
def is_custom(handler_name, entity_name):
    return _is_view(entity_name, handler_name)


def call_custom(handler_name, entity_name, *args, **kwargs):
    if(_isin_cache(entity_name, handler_name) or _is_view(entity_name, handler_name)):
        return CUSTOM_VIEW[entity_name][handler_name](*args, **kwargs)
    else:
        return HttpResponse("Custom view of %s doesn't exist" % handler_name, status=500)
