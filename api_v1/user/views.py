from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView


class AccessTokenAPI(APIView):

    def get(self, request, format=None):
        return Response(
            {'results': str(request.user.token)}
        )

    @method_decorator(csrf_protect)
    def put(self, request, format=None):
        """
        This refresh access_token to another one
        """

        token, created = Token.objects.get_or_create(user=request.user)

        # If the token is not created, this returns it.
        if created:
            return Response({'results': str(token)})

        # This recreates another Token when it has been already existed.
        token.delete()
        return Response({'results': str(Token.objects.create(user=request.user))})
