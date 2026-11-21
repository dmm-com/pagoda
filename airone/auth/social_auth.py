from typing import Any

from user.models import User


def create_user(
    details: dict[str, str], user: User | None = None, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    # When first time login, UserSocialAuth model's object is created.
    # If UserSocialAuth exists, user already exists.
    if user:
        return {"is_new": False}

    # Returns User if the AirOne user already exists.
    user = User.objects.filter(username=details["username"], is_active=True).first()
    if not user:
        # Create a User if the AirOne user does not exist. SSO users are
        # authenticated by the identity provider, so they get no local password.
        user = User(username=details["username"], email=details["email"])
        user.set_unusable_password()
        user.save()

    return {"user": user}
