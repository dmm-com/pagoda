from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from trigger.api_v2.serializers import (
    TriggerParentCreateSerializer,
    TriggerParentSerializer,
    TriggerParentUpdateSerializer,
)
from trigger.models import TriggerParent


class TriggerAPI(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filterset_fields = ["entity__is_active"]

    def get_serializer_class(self):
        serializer = {
            "update": TriggerParentUpdateSerializer,
            "create": TriggerParentCreateSerializer,
        }
        return serializer.get(self.action, TriggerParentSerializer)

    def get_queryset(self):
        query = {
            "entity__is_active": True,
        }

        # add parameter to filter specified entity
        filter_entity_id = self.request.query_params.get("entity_id")
        if filter_entity_id:
            query["entity__id"] = filter_entity_id

        query = TriggerParent.objects.filter(**query)
        if not query.exists():
            raise Http404

        return query

    def destroy(self, request, pk):
        trigger_parent = TriggerParent.objects.filter(pk=pk).last()
        if trigger_parent:
            # delete TriggerConditions, TriggerActions and TriggerActionValues that
            # are related with this TriggerParent
            trigger_parent.clear()

            # delete this TriggerParent
            trigger_parent.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
