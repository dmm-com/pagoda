import pytz

from api_v1.auth import AironeTokenAuth
from airone.lib.profile import airone_profile
from airone.lib.db import get_slave_db
from django.conf import settings
from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from entity.models import Entity
from entry.models import Entry
from entry.settings import CONFIG as CONFIG_ENTRY

from datetime import datetime

from user.models import User


class EntrySearchAPI(APIView):
    authentication_classes = (AironeTokenAuth, BasicAuthentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

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
    permission_classes = (IsAuthenticated,)

    @airone_profile
    def get(self, request):
        # set each request parameters to description variables
        param_entity = request.query_params.get('entity')
        param_entry = request.query_params.get('entry')
        param_target_entity = request.query_params.get('target_entity')
        param_quiet = request.query_params.get('quiet')

        # validate input parameter
        if not param_entry:
            return Response({'result': 'Parameter "entry" is mandatory'},
                            status=status.HTTP_400_BAD_REQUEST)

        # declare query to send DB according to input parameters
        query = Q(name=param_entry, is_active=True)
        if param_entity:
            query &= Q(schema__name=param_entity)

        ret_data = []
        slave_db = get_slave_db()
        for entry in Entry.objects.using(slave_db).filter(query):
            ret_data.append({
                'id': entry.id,
                'entity': {'id': entry.schema.id, 'name': entry.schema.name},
                'referral': [{
                    'id': x.id,
                    'name': x.name,
                    'entity': {} if param_quiet else {'id': x.schema.id, 'name': x.schema.name},
                } for x in entry.get_referred_objects(entity_name=param_target_entity)]
            })

        return Response({'result': ret_data}, content_type='application/json; charset=UTF-8')


class UpdateHistory(APIView):
    authentication_classes = (AironeTokenAuth, BasicAuthentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    @airone_profile
    def get(self, request):
        # validate whether mandatory parameters are specified
        p_attr = request.GET.get('attribute')
        if not p_attr:
            return Response("'attribute' parameter is required",
                            status=status.HTTP_400_BAD_REQUEST)

        # both entry and entry_id parameters accept str and connma separated array
        p_entry = request.GET.get('entry', '')
        p_entry_id = request.GET.get('entry_id', '')
        if not (p_entry or p_entry_id):
            return Response("Either 'entries' or 'entry_ids' parameter is required",
                            status=status.HTTP_400_BAD_REQUEST)

        # Set variables that describe timerange to filter the result of AttributeValue with them.
        older_than = datetime.now(pytz.timezone(settings.TIME_ZONE))
        p_older_than = request.GET.get('older_than')
        if p_older_than:
            try:
                older_than = (datetime
                              .strptime(p_older_than, CONFIG_ENTRY.TIME_FORMAT)
                              .replace(tzinfo=pytz.timezone(settings.TIME_ZONE)))
            except ValueError:
                return Response((
                    "The older_than parameter accepts for following format "
                    "'YYYY-MM-DDTHH:MM:SS'"), status=status.HTTP_400_BAD_REQUEST)

        # The initial datetime(1900/01/01 00:00:00) represents good enough past time to compare
        # with the created time of AttributeValue. We could handle minimum time by using
        # 'datetime.MIN', but some library and service couldn't deal with this time.
        # (c.f. https://dev.mysql.com/doc/refman/5.7/en/datetime.html)
        newer_than = datetime(1900, 1, 1, tzinfo=pytz.timezone(settings.TIME_ZONE))
        p_newer_than = request.GET.get('newer_than')
        if p_newer_than:
            try:
                newer_than = (datetime
                              .strptime(p_newer_than, CONFIG_ENTRY.TIME_FORMAT)
                              .replace(tzinfo=pytz.timezone(settings.TIME_ZONE)))
            except ValueError:
                return Response((
                    "The newer_than parameter accepts for following format "
                    "'YYYY-MM-DDTHH:MM:SS'"), status=status.HTTP_400_BAD_REQUEST)

        # get target entries to get update history
        q_base = Q(is_active=True)
        p_entity = request.GET.get('entity')
        if p_entity:
            q_base &= Q(schema__name=p_entity)

        target_entries = Entry.objects.filter(q_base, (
            Q(name__in=p_entry.split(',')) | Q(id__in=[int(x) for x in p_entry_id.split(',') if x])
        ))
        if not target_entries.exists():
            return Response('There is no entry with which matches specified parameters',
                            status=status.HTTP_400_BAD_REQUEST)

        results = []
        for entry in target_entries:
            attr = entry.attrs.filter(schema__name=p_attr, is_active=True).first()
            if not attr:
                return Response('There is no attribute(%s) in entry(%s)' % (p_attr, entry.name),
                                status=status.HTTP_400_BAD_REQUEST)

            result = {
                'entity': {'id': entry.schema.id, 'name': entry.schema.name},
                'entry': {'id': entry.id, 'name': entry.name},
                'attribute': {'id': attr.id, 'name': attr.schema.name, 'history': []},
            }
            for attrv in (attr.values
                          .filter(created_time__gt=newer_than, created_time__lt=older_than)
                          .order_by('-created_time')[:CONFIG_ENTRY.MAX_HISTORY_COUNT]):
                result['attribute']['history'].append({
                    'value': attrv.get_value(with_metainfo=True)['value'],
                    'updated_at': attrv.created_time,
                    'updated_username': attrv.created_user.username,
                    'updated_userid': attrv.created_user.id,
                })

            results.append(result)

        return Response(results)
