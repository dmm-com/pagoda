from datetime import timedelta
from typing import Optional, TypedDict

from rest_framework import serializers

from user.models import User


class UserToken(TypedDict):
    value: str
    lifetime: int
    expire: str
    created: str


class UserBaseSerializer(serializers.ModelSerializer):
    date_joined = serializers.SerializerMethodField(method_name="get_date_joined")

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_superuser", "date_joined"]

    def get_date_joined(self, obj: User) -> str:
        return obj.date_joined.isoformat()


class UserRetrieveSerializer(UserBaseSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_superuser", "date_joined", "token"]

    def get_token(self, obj: User) -> Optional[UserToken]:
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
