from datetime import timedelta

from airone.lib.http import http_get

from django.http.response import JsonResponse, HttpResponse

from user.models import User


@http_get
def get_user(request, user_id):
    current_user = User.objects.get(id=request.user.id)
    user = User.objects.get(id=user_id)
    if not current_user.is_superuser and current_user != user:
        return HttpResponse("You don't have permission to access", status=400)

    return JsonResponse(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser,
            "date_joined": user.date_joined.isoformat(),
            "token": str(user.token) if request.user.id == user.id else "",
            "token_lifetime": user.token_lifetime,
            "token_expire": (
                user.token.created + timedelta(seconds=user.token_lifetime)
                if user.token
                else ""
            ),
        }
    )


@http_get
def list_users(request):
    users = User.objects.filter(is_active=True)

    return JsonResponse(
        [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_superuser": user.is_superuser,
                "date_joined": user.date_joined.isoformat(),
            }
            for user in users
        ],
        safe=False,
    )
