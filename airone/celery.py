import importlib
import os

import configurations
from celery import Celery
from django.conf import settings

from airone.lib.log import Logger

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airone.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")

configurations.setup()

for extension in settings.AIRONE["EXTENSIONS"]:
    try:
        importlib.import_module("%s.settings" % extension)
    except ImportError:
        Logger.warning("Failed to load settings %s" % extension)

app = Celery("airone")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
