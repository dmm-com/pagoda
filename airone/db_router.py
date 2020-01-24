import random

from django.conf import settings


class DBRouter:
    def db_for_read(self, model, **hints):
        return random.choice(settings.AIRONE['DB_SLAVES'])

    def db_for_write(self, model, **hints):
        return settings.AIRONE['DB_MASTER']

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model=None, **hints):
        return True
