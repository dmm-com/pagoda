from typing import Any

from django.db.models import QuerySet
from django.http import Http404
from rest_framework import serializers, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from trigger.api_v2.serializers import (
    TriggerParentCreateSerializer,
    TriggerParentSerializer,
    TriggerParentUpdateSerializer,
)
from trigger.models import TriggerParent


class TriggerPermission(BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:
        if request.user.is_readonly and view.action in ["create", "update", "destroy"]:
            return False
        return True


class TriggerAPI(viewsets.ModelViewSet):
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated & TriggerPermission]
    filterset_fields = ["entity__is_active"]

    def get_serializer_class(self) -> type[serializers.Serializer[Any]]:
        serializer: dict[str, type[serializers.Serializer[Any]]] = {
            "update": TriggerParentUpdateSerializer,
            "create": TriggerParentCreateSerializer,
        }
        return serializer.get(self.action, TriggerParentSerializer)

    def get_queryset(self) -> QuerySet[TriggerParent]:
        filters: dict[str, Any] = {
            "entity__is_active": True,
        }

        # add parameter to filter specified entity
        filter_entity_id = self.request.query_params.get("entity_id")
        if filter_entity_id:
            filters["entity__id"] = filter_entity_id

        qs = TriggerParent.objects.filter(**filters)
        if not qs.exists():
            raise Http404

        return qs

    def destroy(self, request: Request, pk: int | str) -> Response:
        trigger_parent = TriggerParent.objects.filter(pk=pk).last()
        if trigger_parent:
            # delete TriggerConditions, TriggerActions and TriggerActionValues that
            # are related with this TriggerParent
            trigger_parent.clear()

            # delete this TriggerParent
            trigger_parent.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
