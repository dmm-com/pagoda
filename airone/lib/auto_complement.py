from django.conf import settings

from user.models import User


def get_auto_complement_user(user: User | None) -> User | None:
    if "AUTO_COMPLEMENT_USER" in settings.AIRONE and settings.AIRONE["AUTO_COMPLEMENT_USER"]:
        res_user = User.objects.filter(username=settings.AIRONE["AUTO_COMPLEMENT_USER"]).first()
        user = res_user if res_user else user

    return user


def get_or_create_auto_complement_user() -> User:
    """Return the auto-complement service user, creating it when missing.

    The service user only stands in as the actor of background jobs and never
    logs in, so it is created without a usable password.
    """
    user = get_auto_complement_user(None)
    if user:
        return user

    user = User(username=settings.AIRONE["AUTO_COMPLEMENT_USER"])
    user.set_unusable_password()
    user.save()
    return user
