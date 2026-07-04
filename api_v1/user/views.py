from typing import cast

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.authtoken.models import Token
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from user.models import User


class AccessTokenAPI(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        user = cast(User, request.user)
        return Response({"results": str(user.token)})

    @method_decorator(csrf_protect)
    def put(self, request: Request, format: str | None = None) -> Response:
        """
        This refresh access_token to another one
        """

        user = cast(User, request.user)
        token, created = Token.objects.get_or_create(user=user)

        # If the token is not created, this returns it.
        if created:
            return Response({"results": str(token)})

        # This recreates another Token when it has been already existed.
        token.delete()
        return Response({"results": str(Token.objects.create(user=user))})
