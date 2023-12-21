from rest_framework import generics, serializers, status, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from trigger.models import TriggerCondition
from trigger.api_v2.serializers import (
    TriggerBaseSerializer,
)


class TriggerAPI(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        serializer = {
        }
        return serializer.get(self.action, TriggerBaseSerializer)
    
    def get_queryset(self):
        query = {
            "parent__entity__is_active": True,
        }

        # add parameter to filter specified entity
        filter_entity_id = self.request.query_params.get("entity_id")
        if filter_entity_id:
            query["parent__entity__id"] = filter_entity_id

        return TriggerCondition.objects.filter(**query)