from django.apps import AppConfig


class AclConfig(AppConfig):
    name = "acl"

    def ready(self) -> None:
        from . import signals  # noqa
