import re
from datetime import timedelta

from django.contrib.auth import views as auth_views
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.urls import reverse_lazy

from airone.auth.ldap import LDAPBackend
from airone.lib.http import check_superuser, http_get, http_post, render
from user.forms import UsernameBasedPasswordResetForm

from .models import User


@http_get
def index(request):
    context = {"users": [request.user]}
    if request.user.is_superuser:
        context = {
            "users": User.objects.filter(is_active=True),
        }

    return render(request, "list_user.html", context)


@http_get
@check_superuser
def create(request):
    return render(request, "create_user.html")


@http_post(
    [
        {
            "name": "name",
            "type": str,
            "checker": lambda x: (
                x["name"] and not User.objects.filter(username=x["name"]).exists()
            ),
        },
        {
            "name": "email",
            "type": str,
            "checker": lambda x: (
                x["email"] and not User.objects.filter(email=x["email"]).exists()
            ),
        },
        {"name": "passwd", "type": str, "checker": lambda x: x["passwd"]},
    ]
)
@check_superuser
def do_create(request, recv_data):
    is_superuser = False
    if "is_superuser" in recv_data:
        is_superuser = True

    user = User(
        username=recv_data["name"],
        email=recv_data["email"],
        is_superuser=is_superuser,
    )

    # store encrypted password in the database
    user.set_password(recv_data["passwd"])
    user.save()

    return JsonResponse({})


@http_get
def edit(request, user_id):
    current_user = request.user
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except ObjectDoesNotExist:
        return HttpResponse("Target user is not found", status=404)
    if not current_user.is_superuser and current_user != user:
        return HttpResponse("You don't have permission to access", status=400)

    context = {
        "user_id": int(user_id),
        "user_name": user.username,
        "user_email": user.email,
        "user_is_superuser": user.is_superuser,
        "token": user.token if current_user == user else None,
        "token_lifetime": user.token_lifetime,
        "token_created": user.token.created.strftime("%Y/%m/%d %H:%M:%S") if user.token else None,
        "token_expire": (
            (user.token.created + timedelta(seconds=user.token_lifetime)).strftime(
                "%Y/%m/%d %H:%M:%S"
            )
            if user.token
            else None
        ),
        "is_authenticated_by_local": user.authenticate_type
        == User.AuthenticateType.AUTH_TYPE_LOCAL,
    }

    return render(request, "edit_user.html", context)


@http_post(
    [
        {"name": "name", "type": str, "checker": lambda x: x["name"]},
        {"name": "email", "type": str, "checker": lambda x: x["email"]},
    ]
)
def do_edit(request, user_id, recv_data):
    access_user = request.user
    try:
        target_user = User.objects.get(id=user_id, is_active=True)
    except ObjectDoesNotExist:
        return HttpResponse("Target user is not found", status=404)

    # The case token_lifetime prameter is specified to update
    if "token_lifetime" in recv_data:
        # Validate specified token_lifetime
        if (
            not re.match(r"^[0-9]+$", recv_data["token_lifetime"])
            or int(recv_data["token_lifetime"]) < 0
            or int(recv_data["token_lifetime"]) > User.MAXIMUM_TOKEN_LIFETIME
        ):
            return HttpResponse("Invalid token lifetime is specified", status=400)

        target_user.token_lifetime = int(recv_data["token_lifetime"])

    # Other parameters could be updated by only admin user
    if access_user.is_superuser:
        # validate duplication of username
        if (
            target_user.username != recv_data["name"]
            and User.objects.filter(username=recv_data["name"]).exists()
        ):
            return HttpResponse("username is duplicated", status=400)

        # validate duplication of email
        if (
            target_user.email != recv_data["email"]
            and User.objects.filter(email=recv_data["email"]).exists()
        ):
            return HttpResponse("email is duplicated", status=400)

        # update each params
        target_user.username = recv_data["name"]
        target_user.email = recv_data["email"]

        if "is_superuser" in recv_data:
            target_user.is_superuser = True
        else:
            target_user.is_superuser = False

    target_user.save(update_fields=["username", "email", "is_superuser", "token_lifetime"])

    return JsonResponse({})


@http_get
def edit_passwd(request, user_id):
    user_grade = ""
    if request.user.is_superuser:
        user_grade = "super"
    elif int(request.user.id) == int(user_id):
        user_grade = "self"
    else:
        return HttpResponse("You don't have permission to access this object", status=400)

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except ObjectDoesNotExist:
        return HttpResponse("Target user is not found", status=404)

    context = {
        "user_id": int(user_id),
        "user_name": user.username,
        "user_grade": user_grade,
        "has_password": bool(user.password),
    }

    return render(request, "edit_passwd.html", context)


@http_post(
    [
        {"name": "old_passwd", "type": str, "omittable": False},
        {
            "name": "new_passwd",
            "type": str,
            "checker": lambda x: x["new_passwd"],
        },
        {
            "name": "chk_passwd",
            "type": str,
            "checker": lambda x: x["chk_passwd"],
        },
    ]
)
def do_edit_passwd(request, user_id, recv_data):
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except ObjectDoesNotExist:
        return HttpResponse("Target user is not found", status=404)

    # Identification
    if int(request.user.id) != int(user_id):
        return HttpResponse("You don't have permission to access this object", status=400)

    # When not have a password, don't check old password.
    if user.password:
        # Whether recv_data matches the old password
        if not user.check_password(recv_data["old_passwd"]):
            return HttpResponse("old password is wrong", status=400)

        # Whether the old password and the new password duplicate
        if user.check_password(recv_data["new_passwd"]):
            return HttpResponse("old and new password are duplicated", status=400)

    # Whether the new password matches the check password
    if recv_data["new_passwd"] != recv_data["chk_passwd"]:
        return HttpResponse("new and confirm password are not equal", status=400)

    # store encrypted password in the database
    user.set_password(recv_data["new_passwd"])
    user.save(update_fields=["password"])

    return JsonResponse({})


@http_post(
    [
        {
            "name": "new_passwd",
            "type": str,
            "checker": lambda x: x["new_passwd"],
        },
        {
            "name": "chk_passwd",
            "type": str,
            "checker": lambda x: x["chk_passwd"],
        },
    ]
)
@check_superuser
def do_su_edit_passwd(request, user_id, recv_data):
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except ObjectDoesNotExist:
        return HttpResponse("Target user is not found", status=404)

    # Whether the new password matches the check password
    if recv_data["new_passwd"] != recv_data["chk_passwd"]:
        return HttpResponse("new and confirm password are not equal", status=400)

    # store encrypted password in the database
    user.set_password(recv_data["new_passwd"])
    user.save(update_fields=["password"])

    return JsonResponse({})


@http_post([])
@check_superuser
def do_delete(request, user_id, recv_data):
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except ObjectDoesNotExist:
        return HttpResponse("Target user is not found", status=404)

    ret = {}

    # save deleting target name before do it
    ret["name"] = user.username

    # inactivate user
    user.delete()

    return JsonResponse(ret)


@http_post(
    [
        {
            "name": "ldap_password",
            "type": str,
            "checker": lambda x: x["ldap_password"],
        }
    ]
)
def change_ldap_auth(request, recv_data):
    if LDAPBackend.is_authenticated(request.user.username, recv_data["ldap_password"]):
        # When LDAP authentication is passed with current username and specified password,
        # this chnages authentication type from local to LDAP.
        request.user.authenticate_type = User.AuthenticateType.AUTH_TYPE_LDAP
        request.user.save(update_fields=["authenticate_type"])

        return HttpResponse("Succeeded")
    else:
        return HttpResponse(
            "LDAP authentication was Failed of user %s" % request.user.username,
            status=400,
        )


class PasswordReset(auth_views.PasswordResetView):
    email_template_name = "password_reset_email.html"
    success_url = reverse_lazy("user:password_reset_done")
    template_name = "password_reset_form.html"
    form_class = UsernameBasedPasswordResetForm

    def form_valid(self, form):
        # additionally validate if the user can reset its password
        username = form.cleaned_data["username"]
        user = User.objects.filter(username=username).first()
        if not user:
            return HttpResponse("user does not exist", status=400)
        if user.authenticate_type != User.AuthenticateType.AUTH_TYPE_LOCAL:
            return HttpResponse(
                "This user is authenticated without AirOne local way(like LDAP)."
                "Please confirm your authenticate information.",
                status=400,
            )

        return super(PasswordReset, self).form_valid(form)


class PasswordResetDone(auth_views.PasswordResetDoneView):
    template_name = "password_reset_done.html"


class PasswordResetConfirm(auth_views.PasswordResetConfirmView):
    success_url = reverse_lazy("user:password_reset_complete")
    template_name = "password_reset_confirm.html"


class PasswordResetComplete(auth_views.PasswordResetCompleteView):
    template_name = "password_reset_complete.html"
