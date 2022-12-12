from django.contrib.auth.forms import UserModel
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from airone.lib.drf import YAMLParser, YAMLRenderer
from group.models import Group
from user.api_v2.serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    UserCreateSerializer,
    UserExportSerializer,
    UserImportSerializer,
    UserListSerializer,
    UserRetrieveSerializer,
    UserTokenSerializer,
    UserUpdateSerializer,
)
from user.models import User


class UserPermission(BasePermission):
    def has_object_permission(self, request, view, obj: User):
        current_user: User = request.user
        permisson = {
            "retrieve": current_user.is_superuser or current_user == obj,
            "destroy": current_user.is_superuser,
            "update": current_user.is_superuser or current_user == obj,
        }
        return permisson.get(view.action)


class UserAPI(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated & UserPermission]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering = ["username"]
    search_fields = ["username"]

    def get_serializer_class(self):
        serializer = {
            "create": UserCreateSerializer,
            "update": UserUpdateSerializer,
            "list": UserListSerializer,
        }
        return serializer.get(self.action, UserRetrieveSerializer)

    def destroy(self, request, pk):
        user: User = self.get_object()
        user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserTokenAPI(viewsets.ModelViewSet):
    serializer_class = UserTokenSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request):
        instance = get_object_or_404(Token.objects.filter(user=request.user))
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def refresh(self, request):
        Token.objects.filter(user=request.user).delete()
        instance = Token.objects.create(user=request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UserImportAPI(generics.GenericAPIView):
    parser_classes = [YAMLParser]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer

    def post(self, request):
        import_datas = request.data
        serializer = UserImportSerializer(data=import_datas)
        serializer.is_valid(raise_exception=True)

        # TODO better to move the saving logic into the serializer
        for user_data in import_datas:
            for param in ["username", "groups", "email"]:
                if param not in user_data:
                    return Response("'%s' is required" % param, status=400)

            user = None
            if "id" in user_data:
                # update user by id when id is specified
                user = User.objects.filter(id=user_data["id"]).first()
                if not user:
                    return Response(
                        "Specified id user does not exist(id:%s, user:%s)"
                        % (user_data["id"], user_data["username"]),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if (user.username != user_data["username"]) and (
                    User.objects.filter(username=user_data["username"]).count() > 0
                ):
                    return Response(
                        "New username is already used(id:%s, user:%s->%s)"
                        % (user_data["id"], user.username, user_data["username"]),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                # update user by username
                user = User.objects.filter(username=user_data["username"]).first()
                if not user:
                    # create user
                    user = User(username=user_data["username"])
                    user.save()

            user.username = user_data["username"]
            user.email = user_data["email"]

            new_groups = []
            for group_name in user_data["groups"].split(","):
                if group_name == "":
                    continue
                new_group = Group.objects.filter(name=group_name).first()
                if not new_group:
                    return Response(
                        "Specified group does not exist(user:%s, group:%s)"
                        % (user_data["username"], group_name),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                new_groups.append(new_group)

            user.groups.set(new_groups)
            user.save()

        return Response()


class UserExportAPI(generics.ListAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserExportSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [YAMLRenderer]


class PasswordResetAPI(viewsets.GenericViewSet):
    serializer_class = PasswordResetSerializer
    permission_classes = []

    def reset(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO may be better to implement it in serializer
        username = serializer.validated_data.get("username")
        user = self._get_user(username)
        if not user:
            return Response("user %s not found" % username, status=status.HTTP_400_BAD_REQUEST)

        user_email = getattr(user, UserModel.get_email_field_name())
        use_https = request.is_secure()
        token_generator = default_token_generator
        current_site = get_current_site(request)
        site_name = current_site.name
        domain = current_site.domain
        context = {
            "email": user_email,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "user": user,
            "domain": domain,
            "site_name": site_name,
            "token": token_generator.make_token(user),
            "protocol": "https" if use_https else "http",
        }
        self._send_mail(
            subject_template_name="registration/password_reset_subject.txt",
            email_template_name="registration/ui/password_reset_email.html",
            context=context,
            from_email=None,
            to_email=user_email,
            html_email_template_name=None,
        )

        return Response(serializer.validated_data)

    def _get_user(self, username):
        """
        Given a username, return matching user who should receive a reset or None.
        """
        active_users = UserModel._default_manager.filter(
            **{
                "%s__iexact" % UserModel.USERNAME_FIELD: username,
                "is_active": True,
            }
        )
        if len(active_users) == 1 and active_users[0].has_usable_password():
            return active_users[0]
        else:
            return None

    def _send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, "text/html")

        email_message.send()


class PasswordResetConfirmAPI(viewsets.GenericViewSet):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = []

    def confirm(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.validated_data)
