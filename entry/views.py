import yaml
import json
import re

import custom_view

from django.http import HttpResponse
from django.http.response import JsonResponse
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import urlencode
from datetime import datetime

from airone.lib.elasticsearch import prepend_escape_character
from airone.lib.http import http_get, http_post, check_permission, render
from airone.lib.http import http_file_upload
from airone.lib.http import HttpResponseSeeOther
from airone.lib.types import AttrTypeValue
from airone.lib.acl import ACLType
from airone.lib.profile import airone_profile

from entity.models import Entity
from entry.models import Entry, Attribute, AttributeValue
from job.models import Job, JobOperation
from user.models import User
from group.models import Group
from .settings import CONFIG


def _validate_input(recv_data, obj):
    def _has_data(value):
        return 'data' in value and value['data'] != '' and value['data'] is not None

    def _has_referral(value):
        if isinstance(value['data'], int):
            return value['data'] > 0
        elif isinstance(value['data'], str):
            try:
                return value['data'].isnumeric() and int(value['data']) > 0
            except ValueError:
                return False
        else:
            return False

    for attr_data in recv_data['attrs']:
        attr = obj.attrs.filter(id=attr_data['id']).first()
        if not attr:
            return HttpResponse('Specified attribute is invalid', status=400)

        if isinstance(obj, Entry):
            attr = attr.schema

        if attr.is_mandatory:
            # This checks whether valid data is passed
            is_valid = (attr_data['value'] and
                        all([_has_data(x) for x in attr_data['value']]))

            # This checks whether valid referral parameter is passed
            if is_valid and attr.type & AttrTypeValue['object']:
                is_valid &= all([_has_referral(x) for x in attr_data['value']])

            # This checks whether valid referral_key parameter is passed
            if attr.type & AttrTypeValue['named']:
                is_valid |= (attr_data['referral_key'] and
                             all([_has_data(x) for x in attr_data['referral_key']]))

            if not is_valid:
                return HttpResponse('You have to specify value at mandatory parameters', status=400)

        # Checks specified value exceeds the limit of AttributeValue
        if any([len(str(y['data']).encode('utf-8')) > AttributeValue.MAXIMUM_VALUE_SIZE
                for y in attr_data['value']]):
            return HttpResponse('Passed value is exceeded the limit', status=400)

        # Check date value format
        if (attr.type & AttrTypeValue['date']):
            try:
                [datetime.strptime(str(i['data']), '%Y-%m-%d')
                    for i in attr_data['value'] if i['data']]
            except ValueError:
                return HttpResponse('Incorrect data format in date', status=400)


@airone_profile
@http_get
@check_permission(Entity, ACLType.Readable)
def index(request, entity_id):
    page = request.GET.get('page', 1)
    keyword = request.GET.get('keyword', None)

    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    entity = Entity.objects.get(id=entity_id)
    if custom_view.is_custom("list_entry_without_context", entity.name):
        # show custom view without context
        resp = custom_view.call_custom("list_entry_without_context", entity.name, request, entity)
        if resp:
            return resp

    if keyword:
        name_pattern = prepend_escape_character(CONFIG.ESCAPE_CHARACTERS_ENTRY_LIST, keyword)
        entries = Entry.objects.order_by('name').filter(schema=entity, is_active=True,
                                                        name__iregex=name_pattern)
    else:
        entries = Entry.objects.order_by('name').filter(schema=entity, is_active=True)

    p = Paginator(entries, CONFIG.MAX_LIST_ENTRIES)
    try:
        page_obj = p.page(page)
    except PageNotAnInteger:
        return HttpResponse('Invalid page number. It must be unsigned integer', status=400)
    except EmptyPage:
        return HttpResponse('Invalid page number. The page doesn\'t have anything', status=400)

    context = {
        'entity': entity,
        'keyword': keyword,
        'page_obj': page_obj,
    }

    if custom_view.is_custom("list_entry", entity.name):
        # list custom view
        return custom_view.call_custom("list_entry", entity.name, request, entity, context)
    else:
        # list ordinal view
        return render(request, 'list_entry.html', context)


@airone_profile
@http_get
@check_permission(Entity, ACLType.Writable)
def create(request, entity_id):
    user = User.objects.get(id=request.user.id)

    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    entity = Entity.objects.get(id=entity_id)
    if custom_view.is_custom("create_entry_without_context", entity.name):
        # show custom view
        return custom_view.call_custom("create_entry_without_context", entity.name, request, user,
                                       entity)

    context = {
        'entity': entity,
        'form_url': '/entry/do_create/%s/' % entity.id,
        'redirect_url': '/entry/%s' % entity.id,
        'groups': Group.objects.filter(is_active=True),
        'attributes': [{
            'id': x.id,
            'type': x.type,
            'name': x.name,
            'is_mandatory': x.is_mandatory,
        } for x in entity.attrs.filter(is_active=True).order_by('index')
            if user.has_permission(x, ACLType.Writable)]
    }

    if custom_view.is_custom("create_entry", entity.name):
        # show custom view
        return custom_view.call_custom("create_entry", entity.name, request, user, entity, context)
    else:
        return render(request, 'create_entry.html', context)


@airone_profile
@http_post([
    {'name': 'entry_name', 'type': str, 'checker': lambda x: x['entry_name']},
    {'name': 'attrs', 'type': list, 'meta': [
        {'name': 'id', 'type': str},
        {'name': 'value', 'type': list},
    ]}
])
@check_permission(Entity, ACLType.Writable)
def do_create(request, entity_id, recv_data):
    # get objects to be referred in the following processing
    user = User.objects.get(id=request.user.id)
    entity = Entity.objects.get(id=entity_id)

    # checks that a same name entry corresponding to the entity is existed, or not.
    if Entry.objects.filter(schema=entity_id, name=recv_data['entry_name']).exists():
        return HttpResponse('Duplicate name entry is existed', status=400)

    # validate contexts of each attributes
    err = _validate_input(recv_data, entity)
    if err:
        return err

    if custom_view.is_custom("do_create_entry", entity.name):
        # resp is HttpReponse instance or its subclass (e.g. JsonResponse)
        resp = custom_view.call_custom(
            "do_create_entry", entity.name, request, recv_data, user, entity)
        if resp:
            return resp

    # Create a new Entry object
    entry = Entry.objects.create(name=recv_data['entry_name'],
                                 created_user=user,
                                 schema=entity,
                                 status=Entry.STATUS_CREATING)

    # Create a new job to create entry and run it
    job = Job.new_create(user, entry, params=recv_data)
    job.run()

    return JsonResponse({
        'entry_id': entry.id,
        'entry_name': entry.name,
    })


@airone_profile
@http_get
@check_permission(Entry, ACLType.Writable)
def edit(request, entry_id):
    user = User.objects.get(id=request.user.id)

    if not Entry.objects.filter(id=entry_id).exists():
        return HttpResponse('Failed to get an Entry object of specified id', status=400)

    entry = Entry.objects.get(id=entry_id)

    # prevent to show edit page under the creating processing
    if entry.get_status(Entry.STATUS_CREATING):
        return HttpResponse('Target entry is now under processing', status=400)

    if not entry.is_active:
        return _redirect_restore_entry(entry)

    entry.complement_attrs(user)

    context = {
        'entry': entry,
        'groups': Group.objects.filter(is_active=True),
        'attributes': entry.get_available_attrs(user, ACLType.Writable, get_referral_entries=True),
        'form_url': '/entry/do_edit/%s' % entry.id,
        'redirect_url': '/entry/show/%s' % entry.id,
    }

    if custom_view.is_custom("edit_entry", entry.schema.name):
        # show custom view
        return custom_view.call_custom("edit_entry", entry.schema.name, request, user, entry,
                                       context)
    else:
        return render(request, 'edit_entry.html', context)


@airone_profile
@http_post([
    {'name': 'entry_name', 'type': str, 'checker': lambda x: (
        x['entry_name']
    )},
    {'name': 'attrs', 'type': list, 'meta': [
        {'name': 'id', 'type': str},
        {'name': 'value', 'type': list},
    ]},
])
@check_permission(Entry, ACLType.Writable)
def do_edit(request, entry_id, recv_data):
    user = User.objects.get(id=request.user.id)
    entry = Entry.objects.get(id=entry_id)
    tasks = []

    # checks that a same name entry corresponding to the entity is existed.
    query = Q(schema=entry.schema, name=recv_data['entry_name']) & ~Q(id=entry.id)
    if Entry.objects.filter(query).exists():
        return HttpResponse('Duplicate name entry is existed', status=400)

    # validate contexts of each attributes
    err = _validate_input(recv_data, entry)
    if err:
        return err

    if entry.get_status(Entry.STATUS_CREATING):
        return HttpResponse('Target entry is now under processing', status=400)

    if custom_view.is_custom("do_edit_entry", entry.schema.name):
        # resp is HttpReponse instance or its subclass (e.g. JsonResponse)
        resp = custom_view.call_custom(
            "do_edit_entry", entry.schema.name, request, recv_data, user, entry
        )
        if resp:
            return resp

    # update name of Entry object. If name would be updated, the elasticsearch data of entries that
    # refers this entry also be updated by creating REGISTERED_REFERRALS task.
    if entry.name != recv_data['entry_name']:
        tasks.append(Job.new_register_referrals(user, entry))

    entry.name = recv_data['entry_name']

    # set flags that indicates target entry is under processing
    entry.set_status(Entry.STATUS_EDITING)

    entry.save()

    # Create a new job to edit entry
    tasks.append(Job.new_edit(user, entry, params=recv_data))

    # Run all tasks which are created in this request
    [t.run() for t in tasks]

    return JsonResponse({
        'entry_id': entry.id,
        'entry_name': entry.name,
    })


@airone_profile
@http_get
@check_permission(Entry, ACLType.Readable)
def show(request, entry_id):
    user = User.objects.get(id=request.user.id)

    try:
        entry = Entry.objects.extra(
            where=['status & %d = 0' % Entry.STATUS_CREATING]).get(id=entry_id)
    except ObjectDoesNotExist:
        return HttpResponse('Failed to get an Entry object of specified id', status=400)

    if entry.get_status(Entry.STATUS_CREATING):
        return HttpResponse('Target entry is now under processing', status=400)

    if not entry.is_active:
        return _redirect_restore_entry(entry)

    # create new attributes which are appended after creation of Entity
    entry.complement_attrs(user)

    context = {
        'entry': entry,
        'attributes': entry.get_available_attrs(user),
    }

    if custom_view.is_custom("show_entry", entry.schema.name):
        # show custom view
        return custom_view.call_custom("show_entry", entry.schema.name, request, user, entry,
                                       context)
    else:
        # show ordinal view
        return render(request, 'show_entry.html', context)


@airone_profile
@http_get
@check_permission(Entry, ACLType.Readable)
def history(request, entry_id):
    user = User.objects.get(id=request.user.id)

    try:
        entry = Entry.objects.extra(
            where=['status & %d = 0' % Entry.STATUS_CREATING]).get(id=entry_id)
    except ObjectDoesNotExist:
        return HttpResponse('Failed to get an Entry object of specified id', status=400)

    if entry.get_status(Entry.STATUS_CREATING):
        return HttpResponse('Target entry is now under processing', status=400)

    if not entry.is_active:
        return _redirect_restore_entry(entry)

    context = {
        'entry': entry,
        'value_history': entry.get_value_history(user),
        'history_count': CONFIG.MAX_HISTORY_COUNT,
    }

    return render(request, 'show_entry_history.html', context)


@airone_profile
@http_get
@check_permission(Entry, ACLType.Readable)
def refer(request, entry_id):
    try:
        entry = Entry.objects.extra(
            where=['status & %d = 0' % Entry.STATUS_CREATING]).get(id=entry_id)
    except ObjectDoesNotExist:
        return HttpResponse('Failed to get an Entry object of specified id', status=400)

    if entry.get_status(Entry.STATUS_CREATING):
        return HttpResponse('Target entry is now under processing', status=400)

    if not entry.is_active:
        return _redirect_restore_entry(entry)

    # get referred entries and count of them
    referred_objects = entry.get_referred_objects()

    context = {
        'entry': entry,
        'referred_objects': referred_objects[0:CONFIG.MAX_LIST_REFERRALS],
        'referred_total': referred_objects.count(),
    }
    return render(request, 'show_entry_refer.html', context)


@http_get
def export(request, entity_id):
    user = User.objects.get(id=request.user.id)

    job_params = {
        'export_format': 'yaml',
        'target_id': entity_id,
    }

    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    if 'format' in request.GET and request.GET.get('format') == 'CSV':
        job_params['export_format'] = 'csv'

    # check whether same job is sent
    job_status_not_finished = [Job.STATUS['PREPARING'], Job.STATUS['PROCESSING']]
    if Job.get_job_with_params(
            user, job_params).filter(status__in=job_status_not_finished).exists():
        return HttpResponse('Same export processing is under execution', status=400)

    entity = Entity.objects.get(id=entity_id)
    if not user.has_permission(entity, ACLType.Readable):
        return HttpResponse('Permission denied to export "%s"' % entity.name, status=400)

    # create a job to export search result and run it
    job = Job.new_export(user, **{
        'text': 'entry_%s.%s' % (entity.name, job_params['export_format']),
        'target': entity,
        'params': job_params,
    })
    job.run()

    return JsonResponse({
        'result': 'Succeed in registering export processing. ' +
                  'Please check Job list.'
    })


@http_get
def import_data(request, entity_id):
    if not Entity.objects.filter(id=entity_id, is_active=True).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    return render(request, 'import_entry.html', {'entity': Entity.objects.get(id=entity_id)})


@http_file_upload
def do_import_data(request, entity_id, context):
    user = User.objects.get(id=request.user.id)
    entity = Entity.objects.filter(id=entity_id, is_active=True).first()
    if not entity:
        return HttpResponse("Couldn't parse uploaded file", status=400)

    try:
        data = yaml.load(context, Loader=yaml.FullLoader)
    except yaml.parser.ParserError:
        return HttpResponse("Couldn't parse uploaded file", status=400)

    if not Entry.is_importable_data(data):
        return HttpResponse("Uploaded file has invalid data structure to import", status=400)

    if custom_view.is_custom("import_entry", entity.name):
        # import custom view
        resp = custom_view.call_custom("import_entry", entity.name, user, entity, data)

        # If custom_view returns available response this returns it to user,
        # or continues default processing.
        if resp:
            return resp

    # create job to import data to create or update entries and run it
    job = Job.new_import(user, entity, text='Preparing to import data', params=data)
    job.run()

    return HttpResponseSeeOther('/entry/%s/' % entity_id)


@http_post([])  # check only that request is POST, id will be given by url
@check_permission(Entry, ACLType.Full)
def do_delete(request, entry_id, recv_data):
    user = User.objects.get(id=request.user.id)
    ret = {}

    if not Entry.objects.filter(id=entry_id).exists():
        return HttpResponse('Failed to get an Entry object of specified id', status=400)

    # update name of Entry object
    entry = Entry.objects.filter(id=entry_id).get()

    if custom_view.is_custom("do_delete_entry", entry.schema.name):
        # do_delete custom view
        resp = custom_view.call_custom("do_delete_entry", entry.schema.name, request, user, entry)

        # If custom_view returns available response this returns it to user,
        # or continues default processing.
        if resp:
            return resp

    # set deleted flag in advance because deleting processing taks long time
    entry.is_active = False
    entry.save(update_fields=['is_active'])

    # save deleting Entry name before do it
    ret['name'] = entry.name

    # register operation History for deleting entry
    user.seth_entry_del(entry)

    # Create a new job to delete entry and run it
    job = Job.new_delete(user, entry)
    job.run()

    return JsonResponse(ret)


@airone_profile
@http_get
@check_permission(Entry, ACLType.Writable)
def copy(request, entry_id):
    user = User.objects.get(id=request.user.id)

    if not Entry.objects.filter(id=entry_id).exists():
        return HttpResponse('Failed to get an Entry object of specified id', status=400)

    entry = Entry.objects.get(id=entry_id)

    # prevent to show edit page under the creating processing
    if entry.get_status(Entry.STATUS_CREATING) or entry.get_status(Entry.STATUS_EDITING):
        return HttpResponse('Target entry is now under processing', status=400)

    if not entry.is_active:
        return _redirect_restore_entry(entry)

    context = {
        'form_url': '/entry/do_copy/%s' % entry.id,
        'redirect_url': '/entry/%s' % entry.schema.id,
        'entry': entry,
    }

    if custom_view.is_custom("copy_entry", entry.schema.name):
        return custom_view.call_custom("copy_entry", entry.schema.name, request, user, entry,
                                       context)

    return render(request, 'copy_entry.html', context)


@airone_profile
@http_post([
    {'name': 'entries', 'type': str},
])
@check_permission(Entry, ACLType.Writable)
def do_copy(request, entry_id, recv_data):
    user = User.objects.get(id=request.user.id)

    # validation check
    if 'entries' not in recv_data:
        return HttpResponse('Malformed data is specified (%s)' % recv_data, status=400)

    if not Entry.objects.filter(id=entry_id).exists():
        return HttpResponse('Failed to get an Entry object of specified id', status=400)

    ret = []
    entry = Entry.objects.get(id=entry_id)
    for new_name in [x for x in recv_data['entries'].split('\n') if x]:
        if Entry.objects.filter(schema=entry.schema, name=new_name).exists():
            ret.append({
                'status': 'fail',
                'msg': 'A same named entry (%s) already exists' % new_name,
            })
            continue

        if custom_view.is_custom("do_copy_entry", entry.schema.name):
            (is_continue, status, msg) = custom_view.call_custom(
                "do_copy_entry", entry.schema.name, request, entry, recv_data, user, new_name)
            if not is_continue:
                ret.append({
                    'status': 'success' if status else 'fail',
                    'msg': msg,
                })
                continue

        params = {
            'new_name': new_name,
            'post_data': recv_data,
        }

        # Check another COPY job that targets same name entry is under processing
        if Job.objects.filter(
                operation=JobOperation.COPY_ENTRY.value,
                target=entry,
                status__in=[Job.STATUS['PREPARING'], Job.STATUS['PROCESSING']],
                params=json.dumps(params, sort_keys=True)):
            ret.append({
                'status': 'fail',
                'msg': 'There is another job that targets same name(%s) is existed' % new_name,
            })
            continue

        # make a new job to copy entry and run it
        job = Job.new_copy(user, entry, text=new_name, params=params)
        job.run()

        ret.append({
            'status': 'success',
            'msg': "Success to create new entry '%s'" % new_name,
        })

    return JsonResponse({'results': ret})


@airone_profile
@http_get
@check_permission(Entity, ACLType.Full)
def restore(request, entity_id):
    page = request.GET.get('page', 1)
    keyword = request.GET.get('keyword', None)

    entity = Entity.objects.filter(id=entity_id, is_active=True).first()
    if not entity:
        return HttpResponse('Failed to get entity of specified id', status=400)

    # get all deleted entries that correspond to the entity, the specififcation of
    # 'status=0' is necessary to prevent getting entries that were under processing.
    if keyword:
        name_pattern = prepend_escape_character(CONFIG.ESCAPE_CHARACTERS_ENTRY_LIST, keyword)
        entries = Entry.objects.filter(schema=entity, status=0, is_active=False,
                                       name__iregex=name_pattern).order_by('-updated_time')
    else:
        entries = Entry.objects.filter(schema=entity, status=0,
                                       is_active=False).order_by('-updated_time')

    p = Paginator(entries, CONFIG.MAX_LIST_ENTRIES)
    try:
        page_obj = p.page(page)
    except PageNotAnInteger:
        return HttpResponse('Invalid page number. It must be unsigned integer', status=400)
    except EmptyPage:
        return HttpResponse('Invalid page number. The page doesn\'t have anything', status=400)

    return render(request, 'list_deleted_entry.html', {
        'entity': entity,
        'keyword': keyword,
        'page_obj': page_obj,
    })


@airone_profile
@http_post([])
@check_permission(Entry, ACLType.Full)
def do_restore(request, entry_id, recv_data):
    user = User.objects.get(id=request.user.id)
    entry = Entry.objects.filter(id=entry_id, is_active=False).first()
    if not entry:
        return JsonResponse(
            data={'msg': 'Failed to get entry from specified parameter'}, status=400)

    # checks that a same name entry corresponding to the entity is existed, or not.
    dup_entry = Entry.objects.filter(
            schema=entry.schema.id, name=re.sub(r'_deleted_[0-9_]*$', '', entry.name),
            is_active=True).first()
    if dup_entry:
        return JsonResponse(
            data={'msg': '', 'entry_id': dup_entry.id, 'entry_name': dup_entry.name}, status=400)

    entry.set_status(Entry.STATUS_CREATING)

    # Create a new job to restore deleted entry and run it
    job = Job.new_restore(user, entry)
    job.run()

    return HttpResponse('Success to queue a request to restore an entry')


@airone_profile
@http_post([
    {'type': str, 'name': 'attr_id'},
    {'type': str, 'name': 'attrv_id'}
])
def revert_attrv(request, recv_data):
    user = User.objects.get(id=request.user.id)

    attr = Attribute.objects.filter(id=recv_data['attr_id']).first()
    if not attr:
        return HttpResponse('Specified Attribute-id is invalid', status=400)

    if not user.has_permission(attr, ACLType.Writable):
        return HttpResponse("You don't have permission to update this Attribute", status=400)

    attrv = AttributeValue.objects.filter(id=recv_data['attrv_id']).first()
    if not attrv or attrv.parent_attr.id != attr.id:
        return HttpResponse('Specified AttributeValue-id is invalid', status=400)

    # When the AttributeType was changed after settting value, this operation is aborted
    if attrv.data_type != attr.schema.type:
        return HttpResponse('Attribute-type was changed after this value was registered.',
                            status=400)

    latest_value = attr.get_latest_value()
    if latest_value.get_value() != attrv.get_value():
        # clear all exsts latest flag
        attr.unset_latest_flag()

        # copy specified AttributeValue
        new_attrv = AttributeValue.objects.create(**{
            'value': attrv.value,
            'referral': attrv.referral,
            'status': attrv.status,
            'boolean': attrv.boolean,
            'date': attrv.date,
            'data_type': attrv.data_type,
            'created_user': user,
            'parent_attr': attr,
            'is_latest': True,
        })

        # This also copies child attribute values and append new one
        new_attrv.data_array.add(*[AttributeValue.objects.create(**{
                'value': v.value,
                'referral': v.referral,
                'created_user': user,
                'parent_attr': attr,
                'status': v.status,
                'boolean': v.boolean,
                'date': v.date,
                'data_type': v.data_type,
                'is_latest': False,
                'parent_attrv': new_attrv,
        }) for v in attrv.data_array.all()])

        # append cloned value to Attribute
        attr.values.add(new_attrv)

        # register update to the Elasticsearch
        attr.parent_entry.register_es()

        # call custom-view if it exists
        if custom_view.is_custom("revert_attrv", attr.parent_entry.schema.name):
            return custom_view.call_custom(*[
                "revert_attrv", attr.parent_entry.schema.name, request, user, attr, latest_value,
                new_attrv
            ])

    return HttpResponse('Succeed in updating Attribute "%s"' % attr.schema.name)


def _redirect_restore_entry(entry):
    return redirect('{}?{}'.format(reverse('entry:restore', args=[entry.schema.id]),
                                   urlencode({'keyword': entry.name})))
