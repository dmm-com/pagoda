#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import importlib
from django.conf import settings

from airone.lib.log import Logger


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airone.settings')
    os.environ.setdefault('DJANGO_CONFIGURATION', 'Dev')

    try:
        from configurations.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    for extension in settings.AIRONE['EXTENSIONS']:
        try:
            importlib.import_module('%s.settings' % extension)
        except ImportError:
            Logger.warning('Failed to load settings %s' % extension)

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
