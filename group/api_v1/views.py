from django.db.models import QuerySet
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from group.models import Group


class GroupTreeAPI(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        def _make_hierarchical_group(groups: QuerySet[Group]) -> list[dict[str, object]]:
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
                Group.objects.filter(parent_group__isnull=True, is_active=True)
            )
        )
