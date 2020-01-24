import ldap3

from django.conf import settings
from ldap3.core import exceptions as ldap_exceptions

from airone.lib.log import Logger
from user.models import User

CONF_LDAP = settings.AUTH_CONFIG['LDAP']


class LDAPBackend(object):
    def authenticate(self, username=None, password=None):
        # check authentication with local database at first.
        user = User.objects.filter(username=username,
                                   authenticate_type=User.AUTH_TYPE_LOCAL,
                                   is_active=True).first()
        if user and user.check_password(password):
            return user
        elif user:
            # This is necessary not to send a request to check authentication even though
            # the specified user is in the local database.
            Logger.info('Failed to authenticate user(%s) in local' % username)
            return None

        if not hasattr(settings, 'AUTH_CONFIG'):
            Logger.warn('"AUTH_CONFIG" parameter is necessary in airone/settings.py')
            return None

        # If local authentication fails, check it with LDAP server.
        try:
            user_dn = None
            with ldap3.Connection(CONF_LDAP['SERVER_ADDRESS'], auto_bind=True) as conn:
                if conn.search(search_base=CONF_LDAP['BASE_DN'],
                               search_scope=ldap3.SUBTREE,
                               search_filter=CONF_LDAP['SEARCH_FILTER'].format(username=username)):

                    user_dn = conn.entries[0].entry_dn

            if user_dn:
                with ldap3.Connection(CONF_LDAP['SERVER_ADDRESS'],
                                      user=user_dn, password=password, auto_bind=True) as conn:

                    # This creates LDAP-authenticated user if necessary. Those of them who
                    # authenticated by LDAP are distinguished by 'authenticate_type' parameter
                    # of User object.
                    (user, _) = User.objects.update_or_create(**{
                        'username': username,
                        'authenticate_type': User.AUTH_TYPE_LDAP,
                    })
                    return user

        except ldap_exceptions.LDAPException as e:
            Logger.warn('Failed to authenticate user(%s) in LDAP server(%s)' % (username, e))

    def get_user(self, user_id):
        return User.objects.filter(pk=user_id).first()
