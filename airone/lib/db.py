import logging

from django_replicated.middleware import ReplicationMiddleware
from django_replicated.utils import routers

log = logging.getLogger('django_replicated.middleware')


class AirOneReplicationMiddleware(ReplicationMiddleware):
    def handle_redirect_after_write(self, request, response):
        '''
        Sets a flag using cookies to redirect requests happening after
        successful write operations to ensure that corresponding read
        request will use master database. This avoids situation when
        replicas lagging behind on updates a little.

        (AirOne)
        The original deletes the cookie on the second GET request.
        Changed to retain cookies as replication may be delayed.
        Also, I changed to set a cookie after connecting to MasterDB
        even if it is not a redirect. After the number of seconds specified
        by MAX_AGE has elapsed, it will be deleted on the browser side.
        '''

        if routers.state() == 'master':
            log.debug('set force master cookie for %s', request.path)
            self.set_force_master_cookie(response)
