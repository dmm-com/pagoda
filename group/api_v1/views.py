from rest_framework.response import Response
from rest_framework.views import APIView

from group.models import Group


class GroupTreeAPI(APIView):
    def get(self, request, format=None):
        def _make_hierarchical_group(groups):
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
