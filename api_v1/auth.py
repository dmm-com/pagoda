import pytz

from datetime import datetime, timedelta
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from user.models import User


class AironeTokenAuth(TokenAuthentication):
    def authenticate_credentials(self, key):
        (django_user, token) = super(AironeTokenAuth, self).authenticate_credentials(key)

        # get Airone user object from django_user id
        user = User.objects.get(id=django_user.id)

        if (user.token_lifetime > 0 and
                datetime.now(tz=pytz.UTC) > token.created + timedelta(seconds=user.token_lifetime)):
            raise AuthenticationFailed('Token lifetime is expired')

        return (user, token)
