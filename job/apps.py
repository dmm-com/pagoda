from django.apps import AppConfig

from airone.lib.plugin_task import PluginTaskRegistry


class JobConfig(AppConfig):
    name = "job"

    def ready(self):
        PluginTaskRegistry.validate_all()
