from airone.lib.profile import airone_profile
from airone.lib.http import HttpResponseSeeOther
from airone.lib.http import http_get

from django.http.response import JsonResponse

from user.models import User


@airone_profile
@http_get
def get_user(request, user_id):
    if not request.user.is_authenticated:
        return HttpResponseSeeOther('/auth/login')

    user = User.objects.get(id=user_id)

    return JsonResponse({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_superuser': user.is_superuser,
        'date_joined': user.date_joined,
    })


@airone_profile
@http_get
def list_users(request):
    if not request.user.is_authenticated:
        return HttpResponseSeeOther('/auth/login')

    users = User.objects.filter(is_active=True)

    return JsonResponse([
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined,
        } for user in users
    ], safe=False)
