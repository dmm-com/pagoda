from django.conf import settings
from user.models import User


def get_auto_complement_user(user):
    if ('AUTO_COMPLEMENT_USER' in settings.AIRONE
            and settings.AIRONE['AUTO_COMPLEMENT_USER']):
        res_user = User.objects.filter(username=settings.AIRONE['AUTO_COMPLEMENT_USER']).first()
        user = res_user if res_user else user

    return user
