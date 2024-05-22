import ldap
from django.conf import settings

from airone.lib.log import Logger
from user.models import User


class LDAPBackend(object):
    # This method is called by Django to authenticate user by specified username and password.
    def authenticate(self, request, username=None, password=None):
        # If the HTTP method is GET or HEAD, use the slave DB by the django_replicated.
        # Return None because session information cannot be written to SlaveDB.
        if request and request.method in ["GET", "HEAD"]:
            Logger.info("Failed to authenticate because of GET or HEAD method")
            return None

        # check authentication with local database at first.
        user = User.objects.filter(
            username=username,
            authenticate_type=User.AuthenticateType.AUTH_TYPE_LOCAL,
            is_active=True,
        ).first()
        if user and user.check_password(password):
            return user
        elif user:
            # This is necessary not to send a request to check authentication even though
            # the specified user is in the local database.
            Logger.info("Failed to authenticate user(%s) in local" % username)
            return None

        if not hasattr(settings, "AUTH_CONFIG"):
            Logger.warn('"AUTH_CONFIG" parameter is necessary in airone/settings.py')
            return None

        # If local authentication fails, check it with LDAP server.
        if self.is_authenticated(username, password):
            # This creates LDAP-authenticated user if necessary. Those of them who
            # authenticated by LDAP are distinguished by 'authenticate_type' parameter
            # of User object.
            (user, _) = User.objects.get_or_create(
                **{
                    "username": username,
                    "authenticate_type": User.AuthenticateType.AUTH_TYPE_LDAP,
                }
            )
        else:
            Logger.info("Failed to authenticate user(%s) in LDAP" % username)

        return user

    # This method is necessary because this called by Django to identify user object from id.
    def get_user(self, user_id):
        return User.objects.filter(pk=user_id).first()

    @classmethod
    def is_authenticated(kls, username, password):
        CONF_LDAP = settings.AUTH_CONFIG["LDAP"]
        try:
            o = ldap.initialize(CONF_LDAP["SERVER_ADDRESS"])
            o.protocol_version = ldap.VERSION3
            o.simple_bind_s(who=CONF_LDAP["USER_FILTER"].format(username=username), cred=password)
            o.unbind_s()
            return True
        except ldap.INVALID_CREDENTIALS:
            return False
        except ldap.LDAPError as e:
            Logger.error(str(e))

            return False
