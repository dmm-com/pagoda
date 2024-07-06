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
        acl = ACLBase.objects.filter(id=pk).first()
        if not acl:
            raise Http404

        instance: Entity | EntityAttr | Entry | Attribute = acl.get_subclass_object()

        acl_history = list(instance.history.all())
        codename_query = (
            Q(codename="%s.%s" % (instance.id, ACLType.Full.id))  # type: ignore
            | Q(codename="%s.%s" % (instance.id, ACLType.Writable.id))  # type: ignore
            | Q(codename="%s.%s" % (instance.id, ACLType.Readable.id))  # type: ignore
        )
        if instance.objtype == ACLObjType.Entity:
            attrs = instance.attrs.filter(is_active=True)
            acl_history = acl_history + list(
                EntityAttr.history.filter(aclbase_ptr_id__in=[a.id for a in attrs]).order_by(
                    "-history_date", "-history_id"
                )
            )
            for attr in attrs:
                codename_query |= (
                    Q(codename="%s.%s" % (attr.id, ACLType.Full.id))  # type: ignore
                    | Q(codename="%s.%s" % (attr.id, ACLType.Writable.id))  # type: ignore
                    | Q(codename="%s.%s" % (attr.id, ACLType.Readable.id))  # type: ignore
                )

        permissions = HistoricalPermission.objects.filter(codename_query)
        permission_history = list(
            HistoricalPermission.history.filter(
                permission_ptr_id__in=[p.id for p in permissions]
            ).order_by("-history_date", "-history_id")
        )

        serializer = ACLHistorySerializer(data=acl_history + permission_history, many=True)
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
