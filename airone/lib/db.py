import random
from django.conf import settings


def get_slave_db():
    '''Change the DB query request to Slave.
    The slave DB has a replication delay compared to the master DB.
    There is a problem if change all read query requests to slaves.
    Use this function only for query requests that can afford replication delays.

    Usage:
    Entry.objects.using(get_slave_db()).filter(...)
    '''
    return random.choice(settings.AIRONE['DB_SLAVES'])
