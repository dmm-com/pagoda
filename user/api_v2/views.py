from rest_framework import filters, status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from user.api_v2.serializers import UserListSerializer, UserRetrieveSerializer
from user.models import User


class UserRetrievePermission(BasePermission):
    def has_object_permission(self, request, view, obj: User):
        current_user = request.user
        return current_user.is_superuser or current_user == obj


class UserAPI(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserRetrieveSerializer
    permission_classes = [IsAuthenticated & UserRetrievePermission]

    def destroy(self, request, pk):
        user: User = self.get_object()
        user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserListAPI(ListAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ["username"]
    search_fields = ["username"]
