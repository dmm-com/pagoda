from django.apps import AppConfig


class AclConfig(AppConfig):
    name = 'acl'

    def ready(self):
        from . import signals # noqa
