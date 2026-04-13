from datetime import timedelta
from typing import Any, TypedDict

from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoCoreValidationError
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied, ValidationError

from airone.auth.ldap import LDAPBackend
from user.models import User


class UserRetrieveTokenSerializer(serializers.Serializer):
    value = serializers.CharField()
    lifetime = serializers.IntegerField()
    expire = serializers.CharField()
    created = serializers.CharField()

    class UserTokenTypedDict(TypedDict):
        value: str
        lifetime: int
        expire: str
        created: str


class UserTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = [
            "key",
        ]
        read_only_fields = ["key"]


class UserBaseSerializer(serializers.ModelSerializer):
    date_joined = serializers.SerializerMethodField(method_name="get_date_joined")

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_superuser", "date_joined"]

    def get_date_joined(self, obj: User) -> str:
        return obj.date_joined.isoformat()


class UserCreateSerializer(UserBaseSerializer):
    username = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "is_superuser",
        ]

    def validate_username(self, username: str) -> str:
        """
        superuser can create any user, but non-superuser can only create user
        within a limited namespace of one's own name
        (e.g. (original-username)-NEW_NAME).
        """
        # check specified username has already been used at co-users of login user
        request_user = self.context["request"].user
        if not request_user.is_superuser:
            candidate_name = "%s-%s" % (request_user.username, username)

            if User.objects.filter(username=candidate_name).exists():
                raise ValidationError("A user with that username already exists.")

            return candidate_name

        return username

    def create(self, validate_data: dict[str, Any]) -> User:
        request_user = self.context["request"].user

        # set request_params to create user with validated data and additional parameters
        request_params = validate_data.copy()

        # return HTTP 403 when user trying to create super-user without super-user permissions
        if validate_data.get("is_superuser", False) and not request_user.is_superuser:
            raise PermissionDenied("You don't have permission to create superuser")

        # denied to create user when there is same username user already exists
        if User.objects.filter(username=validate_data["username"]).exists():
            raise ValidationError("User with this username already exists")

        # non-superuser can only create READ-ONLY co-user.
        if not request_user.is_superuser:
            request_params["is_superuser"] = False
            request_params["is_readonly"] = True
            request_params["parent_user"] = request_user
            request_params["email"] = request_user.email

        return User.objects.create_user(request_data=request_params)


class UserUpdateSerializer(UserBaseSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "is_superuser", "token_lifetime"]


class UserRetrieveSerializer(UserBaseSerializer):
    @extend_schema_field(
        {
            "type": "integer",
            "enum": User.AuthenticateType.values,
            "x-enum-varnames": User.AuthenticateType.names,
        }
    )
    class AuthenticateTypeField(serializers.IntegerField):
        pass

    token = serializers.SerializerMethodField()
    authenticate_type = AuthenticateTypeField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_superuser",
            "date_joined",
            "token",
            "authenticate_type",
            "parent_user",
        ]

    @extend_schema_field(UserRetrieveTokenSerializer(required=False))
    def get_token(self, obj: User) -> UserRetrieveTokenSerializer.UserTokenTypedDict | None:
        current_user = self.context["request"].user
        if (
            current_user.id == obj.id
            or current_user.is_superuser
            or current_user == obj.parent_user
        ) and obj.token:
            return {
                "value": str(obj.token),
                "lifetime": obj.token_lifetime,
                "expire": (obj.token.created + timedelta(seconds=obj.token_lifetime)).strftime(
                    "%Y/%m/%d %H:%M:%S"
                ),
                "created": obj.token.created.strftime("%Y/%m/%d %H:%M:%S"),
            }
        else:
            return None


class UserListSerializer(UserBaseSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_superuser",
            "date_joined",
            "parent_user",
            "is_readonly",
        ]


class UserImportChildSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    groups = serializers.CharField(required=True, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "groups",
            "email",
            "is_superuser",
        ]


class UserImportSerializer(serializers.ListSerializer):
    child = UserImportChildSerializer()


class UserExportSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "groups",
            "email",
        ]

    def get_groups(self, obj: User) -> str:
        return ",".join(list(map(lambda x: x.name, obj.groups.filter(group__is_active=True))))


class UserPasswordSerializer(serializers.Serializer):
    old_passwd = serializers.CharField()
    new_passwd = serializers.CharField()
    chk_passwd = serializers.CharField()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context["request"]
        user = self.context["user"]

        # When PASSWORD_RESET_DISABLED is set in the settings.AIRONE
        # request shouldn't be accepted.
        if settings.AIRONE.get("PASSWORD_RESET_DISABLED"):
            raise PermissionDenied("It is not allowed to change password")

        # Only allow to change password of own account or co-user's account for Non-superuser.
        is_couser = user.parent_user == request.user
        if int(request.user.id) != int(user.id) and not is_couser:
            raise ValidationError("You don't have permission to access this object")

        # When not have a password, don't check old password.
        if user.password:
            # Whether recv_data matches the old password
            if not user.check_password(attrs["old_passwd"]):
                raise ValidationError("old password is wrong")

            # Whether the old password and the new password duplicate
            if user.check_password(attrs["new_passwd"]):
                raise ValidationError("old and new password are duplicated")

        # Whether the new password matches the check password
        if attrs["new_passwd"] != attrs["chk_passwd"]:
            raise ValidationError("new and confirm password are not equal")

        return attrs

    def save(self, **kwargs: Any) -> None:
        user = self.context["user"]
        user.set_password(self.validated_data["new_passwd"])
        user.save(update_fields=["password"])


class UserPasswordBySuperuserSerializer(serializers.Serializer):
    new_passwd = serializers.CharField()
    chk_passwd = serializers.CharField()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context["request"]

        if not request.user.is_superuser:
            raise ValidationError("this operation is only allowed for superusers")

        # Whether the new password matches the check password
        if attrs["new_passwd"] != attrs["chk_passwd"]:
            raise ValidationError("new and confirm password are not equal")

        return attrs

    def save(self, **kwargs: Any) -> None:
        user: User = self.context["user"]
        user.set_password(self.validated_data["new_passwd"])
        user.save(update_fields=["password"])


class PasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    password1 = serializers.CharField()
    password2 = serializers.CharField()

    token_generator = default_token_generator

    def _get_user(self) -> User | None:
        try:
            uidb64 = self.initial_data.get("uidb64")
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (ValueError, TypeError, OverflowError, User.DoesNotExist, ValidationError):
            return None
        return user

    def validate_token(self, value: str) -> str:
        user = self._get_user()
        if not user:
            raise ValidationError("user not found")

        if not self.token_generator.check_token(user=user, token=value):
            raise ValidationError("invalid token given")

        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        password1 = attrs.get("password1")
        password2 = attrs.get("password2")

        if password1 != password2:
            raise ValidationError("passwords do not match")

        try:
            password_validation.validate_password(password1)
        except DjangoCoreValidationError as e:
            raise ValidationError("invalid password given. details: %s" % e)

        return attrs

    def create(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        user = self._get_user()
        if not user:
            raise ValidationError("user not found")

        password = validated_data.get("password1")
        user.set_password(password)
        user.save()

        return validated_data


class UserAuthSerializer(serializers.Serializer):
    ldap_password = serializers.CharField(required=True, allow_blank=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Only local to LDAP authentication is allowed."""
        user: User = self.context["user"]

        if user.authenticate_type == User.AuthenticateType.AUTH_TYPE_LDAP:
            raise ValidationError("already authenticated by LDAP")

        ldap_password = attrs.get("ldap_password")
        if ldap_password is None or not LDAPBackend.is_authenticated(user.username, ldap_password):
            raise ValidationError("LDAP authentication was Failed of user %s" % user.username)

        return attrs

    def save(self, **kwargs: Any) -> None:
        user = self.context["user"]
        user.authenticate_type = User.AuthenticateType.AUTH_TYPE_LDAP
        user.save(update_fields=["authenticate_type"])
