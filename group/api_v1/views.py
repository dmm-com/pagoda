from typing import Any, cast

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from group.models import Group


class GroupTreeSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    name = serializers.CharField()
    children = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_children(self, obj: dict[str, Any]) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], obj.get("children", []))


class GroupTreeAPI(APIView):
    serializer_class = GroupTreeSerializer

    def get(self, request: Request, format: str | None = None) -> Response:
        def _make_hierarchical_group(groups: QuerySet[Group]) -> list[dict[str, Any]]:
            return [
                {
                    "id": g.id,
                    "name": g.name,
                    "children": _make_hierarchical_group(g.subordinates.filter(is_active=True)),
                }
                for g in groups
            ]

        return Response(
            _make_hierarchical_group(
                cast(
                    QuerySet[Group],
                    Group.objects.filter(parent_group__isnull=True, is_active=True),  # type: ignore[misc]
                )
            )
        )
