"""
WSGI config for airone project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import importlib
from django.conf import settings
from configurations.wsgi import get_wsgi_application
from airone.lib.log import Logger

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airone.settings')
os.environ.setdefault('DJANGO_CONFIGURATION', 'Dev')

for extension in settings.AIRONE['EXTENSIONS']:
    try:
        importlib.import_module('%s.settings' % extension)
    except ImportError:
        Logger.warning('Failed to load settings %s' % extension)

application = get_wsgi_application()
