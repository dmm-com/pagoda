from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from airone.lib.acl import ACLType
from airone.lib.drf import ObjectNotExistsError
from category.api_v2.serializers import (
    CategoryCreateSerializer,
    CategoryListSerializer,
    CategoryUpdateSerializer,
)
from category.models import Category
from entity.api_v2.views import EntityPermission


class CategoryAPI(viewsets.ModelViewSet):
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticated & EntityPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["name"]
    ordering = ["name"]

    def get_serializer_class(self):
        serializer = {
            "create": CategoryCreateSerializer,
            "update": CategoryUpdateSerializer,
        }
        return serializer.get(self.action, CategoryListSerializer)

    def get_queryset(self):
        # get items that has permission to read
        targets = []
        for category in Category.objects.filter(is_active=True):
            if self.request.user.has_permission(category, ACLType.Readable):
                targets.append(category.id)

        return Category.objects.filter(id__in=targets).order_by("-priority")

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        category: Category = self.get_object()
        if not category.is_active:
            raise ObjectNotExistsError("specified entry has already been deleted")

        # delete specified category
        category.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
