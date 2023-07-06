from datetime import timedelta
from typing import Dict, Optional, TypedDict

from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoCoreValidationError
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError

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
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "is_superuser",
        ]

    def create(self, validate_data):
        return User.objects.create_user(request_data=validate_data)


class UserUpdateSerializer(UserBaseSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "is_superuser",
        ]


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
        ]

    @extend_schema_field(UserRetrieveTokenSerializer(required=False))
    def get_token(self, obj: User) -> Optional[UserRetrieveTokenSerializer.UserTokenTypedDict]:
        current_user = self.context["request"].user
        if (current_user.id == obj.id or current_user.is_superuser) and obj.token:
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
        fields = ["id", "username", "email", "is_superuser", "date_joined"]


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

    def validate(self, attrs: Dict):
        request = self.context["request"]
        user = self.context["user"]

        # Identification
        if int(request.user.id) != int(user.id):
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

    def save(self, **kwargs):
        user = self.context["user"]
        user.set_password(self.validated_data["new_passwd"])
        user.save(update_fields=["password"])


class UserPasswordBySuperuserSerializer(serializers.Serializer):
    new_passwd = serializers.CharField()
    chk_passwd = serializers.CharField()

    def validate(self, attrs: Dict):
        request = self.context["request"]

        if not request.user.is_superuser:
            raise ValidationError("this operation is only allowed for superusers")

        # Whether the new password matches the check password
        if attrs["new_passwd"] != attrs["chk_passwd"]:
            raise ValidationError("new and confirm password are not equal")

        return attrs

    def save(self, **kwargs):
        user = self.context["user"]
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

    def _get_user(self) -> Optional[User]:
        try:
            uidb64 = self.initial_data.get("uidb64")
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (ValueError, TypeError, OverflowError, User.DoesNotExist, ValidationError):
            return None
        return user

    def validate_token(self, value: str):
        user = self._get_user()
        if not user:
            raise ValidationError("user not found")

        if not self.token_generator.check_token(user=user, token=value):
            raise ValidationError("invalid token given")

        return value

    def validate(self, attrs: Dict):
        password1 = attrs.get("password1")
        password2 = attrs.get("password2")

        if password1 != password2:
            raise ValidationError("passwords do not match")

        try:
            password_validation.validate_password(password1)
        except DjangoCoreValidationError as e:
            raise ValidationError("invalid password given. details: %s" % e)

        return attrs

    def create(self, validated_data):
        user = self._get_user()
        if not user:
            raise ValidationError("user not found")

        password = validated_data.get("password1")
        user.set_password(password)
        user.save()

        return validated_data
