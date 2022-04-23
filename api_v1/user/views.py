from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User as DjangoUser

from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from user.models import User as AironeUser


class AccessTokenAPI(APIView):
    def get(self, request, format=None):
        # Getting user by "models.objects.get" is safe, because the "IsAuthenticated" which
        # is specified in the permission_classes parameter guarantees that "request.user" is
        # registered at the Database and authenticated.
        # (c.f. https://www.django-rest-framework.org/api-guide/permissions/#isauthenticated)
        return Response(
            {
                "results": str(
                    AironeUser.objects.get(id=request.user.id, is_active=True).token
                )
            }
        )

    @method_decorator(csrf_protect)
    def put(self, request, format=None):
        """
        This refresh access_token to another one
        """

        user = DjangoUser.objects.get(id=request.user.id)
        token, created = Token.objects.get_or_create(user=user)

        # If the token is not created, this returns it.
        if created:
            return Response({"results": str(token)})

        # This recreates another Token when it has been already existed.
        token.delete()
        return Response({"results": str(Token.objects.create(user=user))})
