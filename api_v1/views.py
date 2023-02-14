from copy import deepcopy

from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from airone.lib.acl import ACLType
from entity.models import Entity
from entry.models import Entry
from entry.settings import CONFIG as ENTRY_CONFIG
from job.models import Job

from .serializers import PostEntrySerializer


class EntryAPI(APIView):
    def post(self, request, format=None):
        sel = PostEntrySerializer(data=request.data)

        # This is necessary because request.data might be changed by the processing of serializer
        raw_request_data = deepcopy(request.data)

        if not sel.is_valid():
            ret = {
                "result": "Validation Error",
                "details": ["(%s) %s" % (k, ",".join(e)) for k, e in sel._errors.items()],
            }
            return Response(ret, status=status.HTTP_400_BAD_REQUEST)

        # checking that target user has permission to create an entry
        if not request.user.has_permission(sel.validated_data["entity"], ACLType.Writable):
            return Response(
                {"result": "Permission denied to create(or update) entry"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # set target entry information to response data
        resp_data = {
            "updated_attrs": {},  # This describes updated attribute values
            "is_created": False,  # This sets true when target entry will be created in this
            # processing
        }

        # This variable indicates whether NOTIFY_UPDATE_ENTRY Job will be created.
        # This is necessary to create minimum necessary NOTIFY_UPDATE_ENTRY Job.
        will_notify_update_entry = False

        # Common processing to update Entry's name and set will_notify_update_entry variable
        def _update_entry_name(entry):
            # Set Entry status that indicates target Entry is under editing processing
            # to prevent to updating this entry from others.
            entry.set_status(Entry.STATUS_EDITING)

            # Set will_notify_update_entry when name parameter is different with target Entry's name
            _will_notify_update_entry = False
            if entry.name != sel.validated_data["name"]:
                entry.name = sel.validated_data["name"]
                entry.save(update_fields=["name"])
                _will_notify_update_entry = True

            return _will_notify_update_entry

        entry_condition = {
            "schema": sel.validated_data["entity"],
            "name": sel.validated_data["name"],
            "is_active": True,
        }
        if "id" in sel.validated_data:
            # prevent to register duplicate entry-name with other entry
            if Entry.objects.filter(
                Q(**entry_condition) & ~Q(id=sel.validated_data["id"])
            ).exists():
                return Response(
                    {"result": '"%s" is duplicate name with other Entry' % entry_condition["name"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            entry = Entry.objects.get(id=sel.validated_data["id"])
            if not request.user.has_permission(entry, ACLType.Writable):
                return Response(
                    {"result": "Permission denied to update entry"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            will_notify_update_entry = _update_entry_name(entry)

        elif Entry.objects.filter(**entry_condition).exists():
            entry = Entry.objects.get(**entry_condition)
            if not request.user.has_permission(entry, ACLType.Writable):
                return Response(
                    {"result": "Permission denied to update entry"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            will_notify_update_entry = _update_entry_name(entry)

        else:
            # This is the processing just in case for safety not to create duplicate Entries
            # when multiple requests passed through existance check. Even through multiple
            # requests coming here, Django prevents from creating multiple Entries.
            entry, is_created = Entry.objects.update_or_create(
                created_user=request.user, status=Entry.STATUS_CREATING, **entry_condition
            )
            resp_data["is_created"] = True

            if is_created:
                # create job to notify entry event to the registered WebHook
                Job.new_notify_create_entry(request.user, entry).run()
            else:
                # set flag to create a Job of NOTIFY_UPDATE_ENTRY in later
                # (Note: This code is rarely run!)
                will_notify_update_entry = True

        entry.complement_attrs(request.user)
        for name, value in sel.validated_data["attrs"].items():
            # If user doesn't have readable permission for target Attribute, it won't be created.
            if not entry.attrs.filter(name=name).exists():
                continue

            attr = entry.attrs.get(schema__name=name, is_active=True)
            if request.user.has_permission(attr.schema, ACLType.Writable) and attr.is_updated(
                value
            ):
                attr.add_value(request.user, value)
                will_notify_update_entry = True

                # This enables to let user know what attributes are changed in this request
                resp_data["updated_attrs"][name] = raw_request_data["attrs"][name]

        if will_notify_update_entry:
            # Create job to notify event, which indicates target entry is updated,
            # to the registered WebHook.
            Job.new_notify_update_entry(request.user, entry).run()

        # register target Entry to the Elasticsearch
        entry.register_es()

        entry.del_status(Entry.STATUS_CREATING | Entry.STATUS_EDITING)

        return Response(dict({"result": entry.id}, **resp_data))

    def get(self, request, *args, **kwargs):
        # The parameter for entry is acceptable both id and name.
        param_entry_id = request.GET.get("entry_id")
        param_entry_name = request.GET.get("entry")
        param_entity = request.GET.get("entity")
        param_offset = request.GET.get("offset", "0")
        if not (param_entry_name or param_entry_id or param_entity):
            return Response(
                {"result": 'Parameter any of "entry", "entry_id" or "entity" is mandatory'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if param_entry_id and not param_entry_id.isdigit():
            return Response(
                {"result": 'Parameter "entry_id" is numerically'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not param_offset.isdigit():
            return Response(
                {"result": 'Parameter "offset" is numerically'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entity = None
        if param_entity:
            entity = Entity.objects.filter(name=param_entity).first()
            if not entity:
                return Response(
                    {"result": "Failed to find specified Entity (%s)" % param_entity},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # This enables to return deleted values
        is_active = request.GET.get("is_active", True)

        # make a query based on GET parameters
        query = Q(is_active=is_active)
        if entity:
            query = Q(query, schema=entity)

        if param_entry_id:
            query = Q(query, id=param_entry_id)
        elif param_entry_name:
            query = Q(query, name=param_entry_name)

        retinfo = [
            x.to_dict(request.user)
            for x in Entry.objects.filter(query)[
                int(param_offset) : int(param_offset) + ENTRY_CONFIG.MAX_LIST_ENTRIES
            ]
        ]
        if not any(retinfo):
            return Response({"result": "Failed to find entry"}, status=status.HTTP_404_NOT_FOUND)

        return Response([x for x in retinfo if x])

    def delete(self, request, *args, **kwargs):
        # checks mandatory parameters are specified
        if not all([x in request.data for x in ["entity", "entry"]]):
            return Response(
                'Parameter "entity" and "entry" are mandatory',
                status=status.HTTP_400_BAD_REQUEST,
            )

        entity = Entity.objects.filter(name=request.data["entity"]).first()
        if not entity:
            return Response(
                "Failed to find specified Entity (%s)" % request.data["entity"],
                status=status.HTTP_404_NOT_FOUND,
            )

        entry = Entry.objects.filter(name=request.data["entry"], schema=entity).first()
        if not entry:
            return Response(
                "Failed to find specified Entry (%s)" % request.data["entry"],
                status=status.HTTP_404_NOT_FOUND,
            )

        # permission check
        if not request.user.has_permission(entry, ACLType.Writable):
            return Response("Permission denied to operate", status=status.HTTP_400_BAD_REQUEST)

        # Delete the specified entry then return its id, if is active
        if entry.is_active:
            # create a new Job to delete entry and run it
            job = Job.new_delete(request.user, entry)

            # create and run notify delete entry task
            job_notify = Job.new_notify_delete_entry(request.user, entry)
            job_notify.run()

            job.dependent_job = job_notify
            job.save(update_fields=["dependent_job"])

            job.run()

        return Response({"id": entry.id})
