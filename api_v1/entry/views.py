from api_v1.auth import AironeTokenAuth
from airone.lib.profile import airone_profile

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication
from rest_framework.authentication import SessionAuthentication

from entity.models import Entity
from entry.models import Entry
from entry.settings import CONFIG as CONFIG_ENTRY
from user.models import User


class EntrySearchAPI(APIView):
    authentication_classes = (AironeTokenAuth, BasicAuthentication, SessionAuthentication,)

    @airone_profile
    def post(self, request, format=None):
        user = User.objects.get(id=request.user.id)

        hint_entity = request.data.get('entities')
        hint_entry_name = request.data.get('entry_name', '')
        hint_attr = request.data.get('attrinfo')
        hint_referral = request.data.get('referral')
        entry_limit = request.data.get('entry_limit', CONFIG_ENTRY.MAX_LIST_ENTRIES)

        if (not isinstance(hint_entity, list) or
                not isinstance(hint_attr, list) or
                not isinstance(entry_limit, int)):
            return Response('The type of parameter is incorrect',
                            status=status.HTTP_400_BAD_REQUEST)

        # forbid to input large size request
        if any([len(str(x)) > CONFIG_ENTRY.MAX_QUERY_SIZE * 2 for x in hint_attr]):
            return Response("Sending parameter is too large", status=400)

        # convert hint_referral type to be eligible for search_entries method
        if hint_referral is None:
            hint_referral = False

        hint_entity_ids = []
        for hint in hint_entity:
            try:
                if Entity.objects.filter(id=hint).exists():
                    hint_entity_ids.append(hint)

            except ValueError:
                # This may happen when a string value is specified in the entities parameter
                entity = Entity.objects.filter(name=hint).first()
                if entity:
                    hint_entity_ids.append(entity.id)

        resp = Entry.search_entries(user, hint_entity_ids, hint_attr, entry_limit, **{
            'hint_referral': hint_referral,
            'entry_name': hint_entry_name,
        })

        return Response({'result': resp}, content_type='application/json; charset=UTF-8')


class EntryReferredAPI(APIView):
    authentication_classes = (AironeTokenAuth, BasicAuthentication, SessionAuthentication,)

    @airone_profile
    def get(self, request):
        param_entry = request.query_params.get('entry')
        if not param_entry:
            return Response({'result': 'Parameter "entry" is mandatory'},
                            status=status.HTTP_400_BAD_REQUEST)

        ret_data = []
        for entry in Entry.objects.filter(name=param_entry, is_active=True):
            ret_data.append({
                'id': entry.id,
                'entity': {'id': entry.schema.id, 'name': entry.schema.name},
                'referral': [{
                    'id': x.id,
                    'name': x.name,
                    'entity': {'id': x.schema.id, 'name': x.schema.name},
                } for x in entry.get_referred_objects()]
            })

        return Response({'result': ret_data}, content_type='application/json; charset=UTF-8')
