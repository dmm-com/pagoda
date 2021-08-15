from datetime import timedelta

from airone.lib.profile import airone_profile
from airone.lib.http import http_get

from django.http.response import JsonResponse, HttpResponse

from rest_framework.authtoken.models import Token

from user.models import User


@airone_profile
@http_get
def get_user(request, user_id):
    current_user = User.objects.get(id=request.user.id)
    user = User.objects.get(id=user_id)
    if not current_user.is_superuser and current_user != user:
        return HttpResponse("You don't have permission to access", status=400)

    (token, _) = Token.objects.get_or_create(user=user)
    return JsonResponse({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_superuser': user.is_superuser,
        'date_joined': user.date_joined.isoformat(),
        'token': str(token) if request.user.id == user.id else '',
        'token_lifetime': user.token_lifetime,
        'token_expire': token.created + timedelta(seconds=user.token_lifetime),
    })


@airone_profile
@http_get
def list_users(request):
    users = User.objects.filter(is_active=True)

    return JsonResponse([
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined.isoformat(),
        } for user in users
    ], safe=False)
