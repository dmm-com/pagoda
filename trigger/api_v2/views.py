from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from trigger.api_v2.serializers import (
    TriggerParentConditionSerializer,
)
from trigger.models import TriggerParentCondition


class TriggerAPI(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filterset_fields = ["entity__is_active"]

    def get_serializer_class(self):
        serializer = {}
        return serializer.get(self.action, TriggerParentConditionSerializer)

    def get_queryset(self):
        query = {
            "entity__is_active": True,
        }

        # add parameter to filter specified entity
        filter_entity_id = self.request.query_params.get("entity_id")
        if filter_entity_id:
            query["entity__id"] = filter_entity_id

        query = TriggerParentCondition.objects.filter(**query)
        if not query.exists():
            raise Http404

        return query