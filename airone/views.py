from django.shortcuts import render
from social_django.models import UserSocialAuth

def index(request):
    social_user = UserSocialAuth.objects.get(user_id=request.user.id)
    return render(request, 'index.html')
