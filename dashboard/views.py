import json
import yaml

from airone.lib.acl import ACLType
from airone.lib.http import render
from airone.lib.http import http_get, http_post
from airone.lib.http import http_file_upload
from airone.lib.http import HttpResponseSeeOther
from airone.lib.profile import airone_profile
from airone.lib.log import Logger
from django.http import HttpResponse
from django.http.response import JsonResponse
from entity.admin import EntityResource, EntityAttrResource
from entry.admin import EntryResource, AttrResource, AttrValueResource
from entity.models import Entity, EntityAttr
from entry.models import Entry, AttributeValue
from job.models import Job
from user.models import User
from .settings import CONFIG

IMPORT_INFOS = [
    {'model': 'Entity', 'resource': EntityResource},
    {'model': 'EntityAttr', 'resource': EntityAttrResource},
    {'model': 'Entry', 'resource': EntryResource},
    {'model': 'Attribute', 'resource': AttrResource},
    {'model': 'AttributeValue', 'resource': AttrValueResource},
]


def _search_entries(user, hint_entity_ids, hint_attrs, entry_name, hint_referral,
                    entry_limit=CONFIG.MAXIMUM_SEARCH_RESULTS):
    attr_names = [x['name'] for x in hint_attrs]
    results = {'ret_count': 0, 'ret_values': []}
    for hint_entity_id in hint_entity_ids:
        entity = Entity.objects.filter(id=hint_entity_id, is_active=True).first()

        # Check EntityAttr for which user does not have readable permission
        non_permission_entityattrs = [
            x.name for x in entity.attrs.filter(name__in=attr_names, is_active=True)
            if not user.has_permission(x, ACLType.Readable)]

        search_results = Entry.search_entries(
            user,
            [hint_entity_id],
            hint_attrs,
            entry_limit if len(results['ret_values']) < entry_limit else 0,
            entry_name,
            hint_referral=hint_referral),

        results['ret_count'] += search_results[0]['ret_count']
        for entryinfo in search_results[0]['ret_values']:

            # Check number of result values
            if len(results['ret_values']) >= CONFIG.MAXIMUM_SEARCH_RESULTS:
                continue
            # Check Entry for which user does not have readable permission
            if (not entryinfo['permission']['is_public'] and
                    entryinfo['permission']['default_permission'] < ACLType.Readable.id):
                entry = Entry.objects.filter(id=entryinfo['entry']['id'], is_active=True).first()
                if not entry:
                    Logger.warning('Non exist entry (id:%s) is registered in ESS.' %
                                   entryinfo['entry']['id'])
                    continue
                if not user.has_permission(entry, ACLType.Readable):
                    ret_value = {
                        'entity': entryinfo['entity'],
                        'entry': entryinfo['entry'],
                        'attrs': {},
                        'permission': False,
                    }
                    if 'referrals' in entryinfo:
                        ret_value['referrals'] = entryinfo['referrals']

                    results['ret_values'].append(ret_value)
                    continue

            ret_value = {
                'entity': entryinfo['entity'],
                'entry': entryinfo['entry'],
                'attrs': {},
                'permission': True,
            }
            if 'referrals' in entryinfo:
                ret_value['referrals'] = entryinfo['referrals']

            # Check Attribute for which user does not have readable permission
            for attr_name in attr_names:
                if attr_name in non_permission_entityattrs:
                    ret_value['attrs'][attr_name] = {'permission': False}
                    continue

                if attr_name not in entryinfo['attrs'].keys():
                    continue

                if (not entryinfo['attrs'][attr_name]['permission']['is_public'] and
                        entryinfo['attrs'][attr_name]['permission']['default_permission'] <
                        ACLType.Readable.id):
                    entry = Entry.objects.filter(id=entryinfo['entry']['id'],
                                                 is_active=True).first()
                    if not entry:
                        Logger.warning('Non exist entry (id:%s) is registered in ESS.' %
                                       entryinfo['entry']['id'])
                        continue
                    attr = entry.attrs.filter(schema__name=attr_name, is_active=True).first()
                    if not attr:
                        continue
                    if not user.has_permission(attr, ACLType.Readable):
                        ret_value['attrs'][attr_name] = {'permission': False}
                        continue

                ret_value['attrs'][attr_name] = entryinfo['attrs'][attr_name]
                ret_value['attrs'][attr_name]['permission'] = True

            results['ret_values'].append(ret_value)

    return results


@airone_profile
def index(request):
    context = {}
    if request.user.is_authenticated and User.objects.filter(id=request.user.id).exists():
        history = []
        # Sort by newest attribute update date (id is auto increment)
        for attr_value in AttributeValue.objects.order_by(
                'id').reverse()[:CONFIG.LAST_ENTRY_HISTORY]:
            parent_attr = attr_value.parent_attr
            parent_entry = parent_attr.parent_entry
            parent_entity = parent_entry.schema

            history.append({
                'entity': parent_entity,
                'entry': parent_entry,
                'attr_type': parent_attr,
                'attr_value': attr_value,
            })

        context['last_entries'] = history

    return render(request, 'dashboard_user_top.html', context)


@airone_profile
@http_get
def import_data(request):
    return render(request, 'import.html', {})


@airone_profile
@http_file_upload
def do_import_data(request, context):
    user = User.objects.get(id=request.user.id)

    if request.FILES['file'].size >= CONFIG.LIMIT_FILE_SIZE:
        return HttpResponse("File size over", status=400)

    try:
        data = yaml.load(context, Loader=yaml.FullLoader)
    except yaml.parser.ParserError:
        return HttpResponse("Couldn't parse uploaded file", status=400)

    def _do_import(resource, iter_data):
        results = []
        for data in iter_data:
            try:
                result = resource.import_data_from_request(data, user)

                results.append({'result': result, 'data': data})
            except RuntimeError as e:
                Logger.warning(('(%s) %s ' % (resource, data)) + str(e))

        if results:
            resource.after_import_completion(results)

    for info in IMPORT_INFOS:
        if info['model'] in data:
            _do_import(info['resource'], data[info['model']])

    return HttpResponseSeeOther('/dashboard/')


@airone_profile
@http_get
def search(request):
    query = request.GET.get('query')
    if not query:
        return HttpResponse("Invalid query parameter is specified", status=400)

    if len(query.encode('utf-8')) > CONFIG.MAX_QUERY_SIZE:
        return HttpResponse("Sending parameter is too large", status=400)

    target_models = [Entry, AttributeValue]

    modified_query = query.strip()
    search_results = sum([x.search(modified_query) for x in target_models], [])
    dic = {}

    for result in search_results:
        eid = result['object'].id
        if eid not in dic:
            dic[eid] = {
                'types': [],
                'object': result['object'],
                'hints': []
            }

        dic[eid]['types'].append(result['type'])
        if result['hint'] != '':
            dic[eid]['hints'].append(result['hint'])

    results = []
    for result in dic.values():
        results.append({
            'type': ', '.join(result['types']),
            'object': result['object'],
            'hint': ', '.join(result['hints'])
        })

    results.sort(key=lambda x: x['object'].name)

    return render(request, 'show_search_results.html', {
        'search_query': modified_query,
        'results': results,
    })


@airone_profile
@http_get
def advanced_search(request):
    entities = [x for x in Entity.objects.filter(is_active=True).order_by('name')
                if x.attrs.filter(is_active=True).exists()]

    return render(request, 'advanced_search.html', {
        'entities': entities,
    })


@http_get
@airone_profile
def advanced_search_result(request):
    user = User.objects.get(id=request.user.id)

    recv_entity = request.GET.getlist('entity[]')
    is_all_entities = request.GET.get('is_all_entities') == 'true'
    has_referral = request.GET.get('has_referral', False)
    attrinfo = request.GET.get('attrinfo')
    entry_name = request.GET.get('entry_name')

    # check attribute params
    if not attrinfo:
        return HttpResponse("The attrinfo parameters is required", status=400)
    try:
        hint_attrs = json.loads(attrinfo)
    except json.JSONDecodeError:
        return HttpResponse("The attrinfo parameter is not JSON", status=400)
    attr_names = [x['name'] for x in hint_attrs]

    # check entity params
    hint_entity_ids = []
    if is_all_entities:
        attrs = sum(
            [list(EntityAttr.objects.filter(name=x, is_active=True)) for x in attr_names], [])
        hint_entity_ids = list(set([x.parent_entity.id for x in attrs if x and
                                   user.has_permission(x.parent_entity, ACLType.Readable)]))
    else:
        if not recv_entity:
            return HttpResponse("The entity[] parameters are required", status=400)

        for entity_id in recv_entity:
            entity = Entity.objects.filter(id=entity_id, is_active=True).first()
            if not entity:
                return HttpResponse("Invalid entity ID is specified", status=400)

            if user.has_permission(entity, ACLType.Readable):
                hint_entity_ids.append(entity.id)

    return render(request, 'advanced_search_result.html', {
        'hint_attrs': hint_attrs,
        'results': _search_entries(user, hint_entity_ids, hint_attrs, entry_name, has_referral),
        'max_num': CONFIG.MAXIMUM_SEARCH_RESULTS,
        'entities': ','.join([str(x) for x in hint_entity_ids]),
        'has_referral': has_referral,
        'is_all_entities': is_all_entities,
        'entry_name': entry_name,
    })


@airone_profile
@http_post([
    {'name': 'entities', 'type': list,
     'checker': lambda x: all([Entity.objects.filter(id=y) for y in x['entities']])},
    {'name': 'attrinfo', 'type': list},
    {'name': 'has_referral', 'type': str, 'omittable': True},
    {'name': 'entry_name', 'type': str, 'omittable': True},
    {'name': 'export_style', 'type': str},
])
def export_search_result(request, recv_data):
    # additional validation
    if recv_data['export_style'] != 'yaml' and recv_data['export_style'] != 'csv':
        return HttpResponse('Invalid "export_type" is specified', status=400)

    user = User.objects.get(id=request.user.id)

    # check whether same job is sent
    job_status_not_finished = [Job.STATUS['PREPARING'], Job.STATUS['PROCESSING']]
    if Job.get_job_with_params(user, recv_data).filter(status__in=job_status_not_finished).exists():
        return HttpResponse('Same export processing is under execution', status=400)

    # create a job to export search result and run it
    job = Job.new_export_search_result(user, **{
        'text': 'search_results.%s' % recv_data['export_style'],
        'params': recv_data,
    })
    job.run()

    return JsonResponse({
        'result': 'Succeed in registering export processing. ' +
                  'Please check Job list.'
    })
