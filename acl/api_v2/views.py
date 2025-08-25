from collections import defaultdict

from django.db.models import Q
from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from acl.api_v2.serializers import ACLHistorySerializer, ACLSerializer
from acl.models import ACLBase
from airone.lib.acl import ACLObjType, ACLType
from entity.models import Entity, EntityAttr
from entry.models import Attribute, Entry
from role.models import HistoricalPermission
from user.models import User


class ACLPermission(BasePermission):
    def has_object_permission(self, request: Request, view, obj) -> bool:
        user: User = request.user
        permisson = {
            "retrieve": ACLType.Readable,
            "update": ACLType.Full,
        }
        if not isinstance(obj, ACLBase):
            return False
        if not user.has_permission(obj, permisson.get(view.action)):
            return False
        return True


class ACLAPI(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = ACLBase.objects.all()
    serializer_class = ACLSerializer

    permission_classes = [IsAuthenticated & ACLPermission]


@extend_schema(
    parameters=[
        OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH),
    ]
)
class ACLHistoryAPI(generics.ListAPIView):
    serializer_class = ACLHistorySerializer

    def get_queryset(self):
        """Unnecessary in this serializer"""
        pass

    def get(self, request: Request, pk: int) -> Response:
        """
        ACL History API - Performance Optimization Strategy:

        This method implements significant query reduction optimizations:
        1. select_related: Bulk fetch of related data (history_user, content_type)
        2. Bulk fetch: ACLBase name information bulk retrieval and caching
        3. prev_record cache: Pre-build history relationships to solve N+1 problem

        This minimizes DB access within serializers,
        reducing queries from 30+ to around 10.
        """
        acl = ACLBase.objects.filter(id=pk).first()
        if not acl:
            raise Http404

        instance: Entity | EntityAttr | Entry | Attribute = acl.get_subclass_object()

        # 1. Bulk fetch ACL history data (including history_user information)
        acl_history = list(instance.history.select_related("history_user").all())
        codename_query = (
            Q(codename="%s.%s" % (instance.id, ACLType.Full.id))  # type: ignore
            | Q(codename="%s.%s" % (instance.id, ACLType.Writable.id))  # type: ignore
            | Q(codename="%s.%s" % (instance.id, ACLType.Readable.id))  # type: ignore
        )
        # Also fetch Entity attribute history with same optimization
        if instance.objtype == ACLObjType.Entity:
            attrs = instance.attrs.filter(is_active=True)
            acl_history = acl_history + list(
                EntityAttr.history.filter(aclbase_ptr_id__in=[a.id for a in attrs])
                .select_related("history_user")
                .order_by("-history_date", "-history_id")
            )
            for attr in attrs:
                codename_query |= (
                    Q(codename="%s.%s" % (attr.id, ACLType.Full.id))  # type: ignore
                    | Q(codename="%s.%s" % (attr.id, ACLType.Writable.id))  # type: ignore
                    | Q(codename="%s.%s" % (attr.id, ACLType.Readable.id))  # type: ignore
                )

        # 2. Bulk fetch Permission history data (including related information)
        permissions = HistoricalPermission.objects.filter(codename_query)
        permission_history = list(
            HistoricalPermission.history.filter(permission_ptr_id__in=[p.id for p in permissions])
            .select_related("history_user", "content_type")
            .order_by("-history_date", "-history_id")
        )

        # 3. Bulk fetch and cache ACLBase name information (reduce duplicate queries in serializer)
        acl_ids = set()
        for ph in permission_history:
            if hasattr(ph, "codename") and ph.codename:
                acl_ids.add(ph.codename.split(".")[0])

        acl_base_cache = {}
        if acl_ids:
            acl_objects = ACLBase.objects.filter(id__in=acl_ids).only("id", "name")
            acl_base_cache = {str(obj.id): obj.name for obj in acl_objects}

        # 4. Build prev_record cache (fundamental solution to N+1 problem)
        # Completely eliminate DB queries when accessing history.prev_record in serializer
        prev_record_cache = {}

        # Build prev_record relationships for Permission history
        grouped_histories = defaultdict(list)
        for ph in permission_history:
            grouped_histories[ph.permission_ptr_id].append(ph)

        for permission_id, histories in grouped_histories.items():
            # Sort in chronological order (same as queryset order)
            histories.sort(key=lambda x: (x.history_date, x.history_id), reverse=True)
            for i in range(len(histories)):
                current = histories[i]
                if i + 1 < len(histories):
                    # Prevent key conflicts by including type information
                    cache_key = f"permission_{current.history_id}"
                    prev_record_cache[cache_key] = histories[i + 1]

        # Build prev_record relationships for ACL history
        acl_grouped_histories = defaultdict(list)
        for ah in acl_history:
            acl_grouped_histories[ah.aclbase_ptr_id].append(ah)

        for acl_id, histories in acl_grouped_histories.items():
            # Sort in chronological order (same as queryset order)
            histories.sort(key=lambda x: (x.history_date, x.history_id), reverse=True)
            for i in range(len(histories)):
                current = histories[i]
                if i + 1 < len(histories):
                    # Prevent key conflicts by including type information
                    cache_key = f"acl_{current.history_id}"
                    prev_record_cache[cache_key] = histories[i + 1]

        # 5. Pass optimized cache data to serializer for processing
        serializer = ACLHistorySerializer(
            data=acl_history + permission_history,
            many=True,
            context={
                "acl_base_cache": acl_base_cache,  # ACLBase name cache
                "prev_record_cache": prev_record_cache,  # prev_record relationship cache
            },
        )
        serializer.is_valid()

        # order by time desc
        sorted_history = sorted(serializer.data, reverse=True, key=lambda x: x["time"])
        results = []
        for i, history in enumerate(sorted_history):
            # filter histories have empty changes
            if history["changes"] == []:
                continue

            # oldest history is unchanged
            if i + 1 == len(sorted_history):
                results.append(history)
                continue

            # history of different target is unchanged
            prev_history = sorted_history[i + 1]
            if history["name"] != prev_history["name"]:
                results.append(history)
                continue

            # processing to combine two role changes into one
            for change in history["changes"]:
                for j, prev_change in enumerate(prev_history["changes"]):
                    if change["target"] == prev_change["target"] and change["action"] == "create":
                        change["action"] = "update"
                        change["before"] = prev_change["before"]
                        del prev_history["changes"][j]
                    elif change["target"] == prev_change["target"] and change["action"] == "delete":
                        change["action"] = "update"
                        change["after"] = prev_change["after"]
                        del prev_history["changes"][j]

            results.append(history)

        return Response(results)
