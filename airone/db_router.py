import random
import threading

from django.conf import settings

class DBRouter:
    def db_for_read(self, model, **hints):
        setting = settings.AIRONE['DB_MASTER']
        if DBSlaves.enable():
            setting = random.choice(settings.AIRONE['DB_SLAVES'])
        return setting

    def db_for_write(self, model, **hints):
        return settings.AIRONE['DB_MASTER']

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model=None, **hints):
        return True

class DBType(Enum):
    MASTER = 0
    SLAVES = 1

class DBSlaves():
    dict = dict()
    lock = threading.Lock()
    def __init__(self):
        self.dict = DBSlaves.dict
        self.lock = DBSlaves.lock

    def __enter__(self):
        self.lock.acquire()
        thread_id = threading.get_ident()
        self.dict[thread_id] = DBType.SLAVES

    def __exit__(self, *arg, **kwargs):
        thread_id = threading.get_ident()
        self.dict[thread_id] = DBType.MASTER
        self.lock.release()

    @classmethod
    def enable(cls):
        enable = False
        thread_id = threading.get_ident()
        if DBSlaves.dict[thread_id] == DBType.SLAVES:
            enable = True
        if DBSlaves.dict[thread_id] == DBType.MASTER:
            enable = False
        return enable