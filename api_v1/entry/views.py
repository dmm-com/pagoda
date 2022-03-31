import pytz
from datetime import datetime

from airone.lib.acl import ACLType
from django.conf import settings
from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from entity.models import Entity
from entry.models import Entry
from entry.settings import CONFIG as CONFIG_ENTRY


class EntrySearchAPI(APIView):

    def post(self, request, format=None):
        hint_entities = request.data.get('entities')
        hint_entry_name = request.data.get('entry_name', '')
        hint_attrs = request.data.get('attrinfo')
        hint_referral = request.data.get('referral', False)
        is_output_all = request.data.get('is_output_all', True)
        entry_limit = request.data.get('entry_limit', CONFIG_ENTRY.MAX_LIST_ENTRIES)

        if (not isinstance(hint_entities, list) or
                not isinstance(hint_entry_name, str) or
                not isinstance(hint_attrs, list) or
                not isinstance(is_output_all, bool) or
                not isinstance(hint_referral, (str, bool)) or
                not isinstance(entry_limit, int)):
            return Response('The type of parameter is incorrect',
                            status=status.HTTP_400_BAD_REQUEST)

        # forbid to input large size request
        if len(hint_entry_name) > CONFIG_ENTRY.MAX_QUERY_SIZE:
            return Response("Sending parameter is too large", status=400)

        # check attribute params
        for hint_attr in hint_attrs:
            if 'name' not in hint_attr:
                return Response("The name key is required for attrinfo parameter", status=400)
            if not isinstance(hint_attr['name'], str):
                return Response("Invalid value for attrinfo parameter", status=400)
            if hint_attr.get('keyword'):
                if not isinstance(hint_attr['keyword'], str):
                    return Response("Invalid value for attrinfo parameter", status=400)
                # forbid to input large size request
                if len(hint_attr['keyword']) > CONFIG_ENTRY.MAX_QUERY_SIZE:
                    return Response("Sending parameter is too large", status=400)

        # check entities params
        if not hint_entities:
            return Response("The entities parameters are required", status=400)
        hint_entity_ids = []
        for hint_entity in hint_entities:
            entity = None
            if isinstance(hint_entity, int):
                entity = Entity.objects.filter(id=hint_entity, is_active=True).first()
            elif isinstance(hint_entity, str):
                if hint_entity.isnumeric():
                    entity = Entity.objects.filter(Q(id=hint_entity) | Q(name=hint_entity),
                                                   Q(is_active=True)).first()
                else:
                    entity = Entity.objects.filter(name=hint_entity, is_active=True).first()

            if entity and request.user.has_permission(entity, ACLType.Readable):
                hint_entity_ids.append(entity.id)

        resp = Entry.search_entries(request.user,
                                    hint_entity_ids,
                                    hint_attrs,
                                    entry_limit,
                                    hint_entry_name,
                                    hint_referral,
                                    is_output_all)

        return Response({'result': resp})


class EntryReferredAPI(APIView):

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
        for entry in Entry.objects.filter(query):
            ret_data.append({
                'id': entry.id,
                'entity': {'id': entry.schema.id, 'name': entry.schema.name},
                'referral': [{
                    'id': x.id,
                    'name': x.name,
                    'entity': {} if param_quiet else {'id': x.schema.id, 'name': x.schema.name},
                } for x in entry.get_referred_objects(entity_name=param_target_entity)]
            })

        return Response({'result': ret_data})


class UpdateHistory(APIView):

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
