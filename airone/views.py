from django.shortcuts import render
from user.models import User
from social_django.models import UserSocialAuth

def index(request):
    if User.objects.filter(id=request.user.id).exists():
        user = User.objects.get(id=request.user.id)

    if UserSocialAuth.objects.filter(user_id=request.user.id).exists():
        social_user = UserSocialAuth.objects.get(user_id=request.user.id)

    return render(request, 'index.html')
