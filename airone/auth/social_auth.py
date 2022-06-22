from user.models import User


def create_user(details, user=None, *args, **kwargs):

    # When first time login, UserSocialAuth model's object is created.
    # If UserSocialAuth exists, user already exists.
    if user:
        return {"is_new": False}

    # Returns User if the AirOne user already exists.
    user = User.objects.filter(username=details["username"], is_active=True).first()
    if not user:
        # Create a User if the AirOne user does not exist.
        user = User.objects.create(username=details["username"], email=details["email"])

    return {"user": user}
