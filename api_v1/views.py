from .serializers import PostEntrySerializer

from copy import deepcopy

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication
from rest_framework.authentication import SessionAuthentication

from api_v1.auth import AironeTokenAuth
from airone.lib.acl import ACLType
from entity.models import Entity
from entry.models import Entry
from entry.tasks import delete_entry
from job.models import Job
from user.models import User

from entry.settings import CONFIG as ENTRY_CONFIG

from django.db.models import Q


class EntryAPI(APIView):
    authentication_classes = (AironeTokenAuth, BasicAuthentication, SessionAuthentication,)

    def post(self, request, format=None):
        user = User.objects.get(id=request.user.id)
        sel = PostEntrySerializer(data=request.data)

        # This is necessary because request.data might be changed by the processing of serializer
        raw_request_data = deepcopy(request.data)

        if not sel.is_valid():
            ret = {
                'result': 'Validation Error',
                'details': ['(%s) %s' % (k, ','.join(e)) for k, e in sel._errors.items()],
            }
            return Response(ret, status=status.HTTP_400_BAD_REQUEST)

        # checking that target user has permission to create an entry
        if not user.has_permission(sel.validated_data['entity'], ACLType.Writable):
            return Response({'result': 'Permission denied to create(or update) entry'},
                            status=status.HTTP_400_BAD_REQUEST)

        # set target entry information to response data
        resp_data = {
            'updated_attrs': {},  # This describes updated attribute values
            'is_created': False,  # This sets true when target entry will be created in this
                                  # processing
        }

        entry_condition = {
            'schema': sel.validated_data['entity'],
            'name': sel.validated_data['name'],
            'is_active': True,
        }
        if 'id' in sel.validated_data:
            # prevent to register duplicate entry-name with other entry
            if Entry.objects.filter(
                    Q(**entry_condition) & ~Q(id=sel.validated_data['id'])).exists():
                return Response(
                    {'result': '"%s" is duplicate name with other Entry' % entry_condition['name']},
                    status=status.HTTP_400_BAD_REQUEST)

            entry = Entry.objects.get(id=sel.validated_data['id'])
            entry.name = sel.validated_data['name']
            entry.set_status(Entry.STATUS_EDITING)

        elif Entry.objects.filter(**entry_condition).exists():
            entry = Entry.objects.get(**entry_condition)
            entry.set_status(Entry.STATUS_EDITING)

        else:
            entry = Entry.objects.create(created_user=user,
                                         status=Entry.STATUS_CREATING,
                                         **entry_condition)
            resp_data['is_created'] = True

        entry.complement_attrs(user)
        for name, value in sel.validated_data['attrs'].items():
            # If user doesn't have readable permission for target Attribute, it won't be created.
            if not entry.attrs.filter(name=name).exists():
                continue

            attr = entry.attrs.get(name=name)
            if user.has_permission(attr.schema, ACLType.Writable) and attr.is_updated(value):
                attr.add_value(user, value)

                # This enables to let user know what attributes are changed in this request
                resp_data['updated_attrs'][name] = raw_request_data['attrs'][name]

        # register target Entry to the Elasticsearch
        entry.register_es()

        entry.del_status(Entry.STATUS_CREATING | Entry.STATUS_EDITING)

        return Response(dict({'result': entry.id}, **resp_data))

    def get(self, request, *args, **kwargs):
        user = User.objects.filter(id=request.user.id).first()
        if not user:
            return Response({'result': 'You have to login AirOne to perform this request'},
                            status=status.HTTP_400_BAD_REQUEST)

        # The parameter for entry is acceptable both id and name.
        param_entry_id = request.GET.get('entry_id')
        param_entry_name = request.GET.get('entry')
        param_entity = request.GET.get('entity')
        if not (param_entry_name or param_entry_id or param_entity):
            return Response(
                    {'result': 'Parameter any of "entry", "entry_id" or "entity" is mandatory'},
                    status=status.HTTP_400_BAD_REQUEST)

        entity = None
        if param_entity:
            entity = Entity.objects.filter(name=param_entity).first()
            if not entity:
                return Response({'result': 'Failed to find specified Entity (%s)' % param_entity},
                                status=status.HTTP_404_NOT_FOUND)

        # This enables to return deleted values
        is_active = request.GET.get('is_active', True)

        # make a query based on GET parameters
        query = Q(is_active=is_active)
        if entity:
            query = Q(query, schema=entity)

        if param_entry_id:
            query = Q(query, id=param_entry_id)
        elif param_entry_name:
            query = Q(query, name=param_entry_name)

        param_offset = request.GET.get('offset', 0)
        retinfo = [x.to_dict(user) for x in
                   Entry.objects.filter(query)[int(param_offset):ENTRY_CONFIG.MAX_LIST_ENTRIES]]
        if not any(retinfo):
            return Response({'result': 'Failed to find entry'},
                            status=status.HTTP_404_NOT_FOUND)

        return Response([x for x in retinfo if x])

    def delete(self, request, *args, **kwargs):
        if not request.user.id:
            return Response('You have to login AirOne to perform this request',
                            status=status.HTTP_400_BAD_REQUEST)

        # checks mandatory parameters are specified
        if not all([x in request.data for x in ['entity', 'entry']]):
            return Response('Parameter "entity" and "entry" are mandatory',
                            status=status.HTTP_400_BAD_REQUEST)

        entity = Entity.objects.filter(name=request.data['entity']).first()
        if not entity:
            return Response('Failed to find specified Entity (%s)' % request.data['entity'],
                            status=status.HTTP_404_NOT_FOUND)

        entry = Entry.objects.filter(name=request.data['entry'], schema=entity).first()
        if not entry:
            return Response('Failed to find specified Entry (%s)' % request.data['entry'],
                            status=status.HTTP_404_NOT_FOUND)

        # permission check
        user = User.objects.get(id=request.user.id)
        if (not user.has_permission(entry, ACLType.Full) or
                not user.has_permission(entity, ACLType.Readable)):
            return Response('Permission denied to operate', status=status.HTTP_400_BAD_REQUEST)

        # Delete the specified entry then return its id, if is active
        if entry.is_active:
            # create a new Job to delete entry
            job = Job.new_delete(user, entry)

            delete_entry.delay(entry.id, job.id)

        return Response({'id': entry.id})
