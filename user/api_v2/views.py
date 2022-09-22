from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from user.api_v2.serializers import UserRetrieveSerializer
from user.models import User


class UserPermission(BasePermission):
    def has_object_permission(self, request, view, obj: User):
        current_user: User = request.user
        permisson = {
            "retrieve": current_user.is_superuser or current_user == obj,
            "destroy": current_user.is_superuser,
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
            #            "get": UserRetrieveSerializer,
            "list": UserListSerializer,
            #            "delete": UserRetrieveSerializer,
        }
        return serializer.get(self.action, UserRetrieveSerializer)

    def destroy(self, request, pk):
        user: User = self.get_object()
        user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# class UserListAPI(ListAPIView):
#    queryset = User.objects.filter(is_active=True)
#    serializer_class = UserListSerializer
#    permission_classes = [IsAuthenticated]
#    pagination_class = PageNumberPagination
#    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
#    ordering = ["username"]
#    search_fields = ["username"]
