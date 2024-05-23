from datetime import datetime, timedelta

import pytz
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from airone.lib.log import Logger
from user.models import User


class AironeTokenAuth(TokenAuthentication):
    def authenticate_credentials(self, key):
        (django_user, token) = super(AironeTokenAuth, self).authenticate_credentials(key)

        # get Airone user object from django_user id
        user = User.objects.get(id=django_user.id)

        if user.token_lifetime > 0 and datetime.now(tz=pytz.UTC) > token.created + timedelta(
            seconds=user.token_lifetime
        ):
            raise AuthenticationFailed("Token lifetime is expired")

        return (user, token)


class LoggingBasicAuthentication(BasicAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, _ = result
            Logger.warn(f"User({user.username}) used BASIC authentication")
        return result
