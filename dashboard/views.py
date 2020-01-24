import logging
import yaml

from airone.lib.http import render
from airone.lib.http import http_get, http_post
from airone.lib.http import http_file_upload
from airone.lib.http import HttpResponseSeeOther
from airone.lib.profile import airone_profile
from django.http import HttpResponse
from django.http.response import JsonResponse
from entity.admin import EntityResource, EntityAttrResource
from entry.admin import EntryResource, AttrResource, AttrValueResource
from entity.models import Entity, EntityAttr
from entry.models import Entry, AttributeValue
from job.models import Job
from user.models import User
from .settings import CONFIG
from .tasks import export_search_result as task_export_search_result

IMPORT_INFOS = [
    {'model': 'Entity', 'resource': EntityResource},
    {'model': 'EntityAttr', 'resource': EntityAttrResource},
    {'model': 'Entry', 'resource': EntryResource},
    {'model': 'Attribute', 'resource': AttrResource},
    {'model': 'AttributeValue', 'resource': AttrValueResource},
]

Logger = logging.getLogger(__name__)


@airone_profile
def index(request):
    context = {}
    if request.user.is_authenticated() and User.objects.filter(id=request.user.id).exists():
        history = []
        for attr_value in AttributeValue.objects.order_by(
                'created_time').reverse()[:CONFIG.LAST_ENTRY_HISTORY]:
            parent_attr = attr_value.parent_attr
            parent_entry = parent_attr.parent_entry

            if parent_attr.is_active and parent_entry.is_active:
                history.append({
                    'entry': parent_entry,
                    'attr_type': parent_attr,
                    'attr_value': attr_value,
                    'attr_value_array': attr_value.data_array.all(),
                })

        context['last_entries'] = history

    return render(request, 'dashboard_user_top.html', context)


@http_get
def import_data(request):
    return render(request, 'import.html', {})


@http_file_upload
def do_import_data(request, context):
    user = User.objects.get(id=request.user.id)

    if request.FILES['file'].size >= CONFIG.LIMIT_FILE_SIZE:
        return HttpResponse("File size over", status=400)

    try:
        data = yaml.load(context)
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


@http_get
def search(request):
    query = request.GET.get('query')
    if not query:
        return HttpResponse("Invalid query parameter is specified", status=400)

    if len(query.encode('utf-8')) > CONFIG.MAX_QUERY_SIZE:
        return HttpResponse("Sending parameter is too large", status=400)

    target_models = [Entry, AttributeValue]

    search_results = sum([x.search(query) for x in target_models], [])
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
        'results': results
    })


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
    recv_attr = request.GET.getlist('attr[]')
    is_all_entities = request.GET.get('is_all_entities') == 'true'
    has_referral = request.GET.get('has_referral') == 'true'

    if not is_all_entities and (not recv_entity or not recv_attr):
        return HttpResponse("The attr[] and entity[] parameters are required", status=400)
    elif is_all_entities and not recv_attr:
        return HttpResponse("The attr[] parameters are required", status=400)

    if not is_all_entities and not all(
            [Entity.objects.filter(id=x, is_active=True).exists() for x in recv_entity]):
        return HttpResponse("Invalid entity ID is specified", status=400)

    if is_all_entities:
        attrs = sum(
            [list(EntityAttr.objects.filter(name=x, is_active=True)) for x in recv_attr], [])
        entities = list(set([x.parent_entity.id for x in attrs if x]))
    else:
        entities = recv_entity

    return render(request, 'advanced_search_result.html', {
        'attrs': recv_attr,
        'results': Entry.search_entries(user,
                                        entities,
                                        [{'name': x} for x in recv_attr],
                                        CONFIG.MAXIMUM_SEARCH_RESULTS,
                                        hint_referral=has_referral),
        'max_num': CONFIG.MAXIMUM_SEARCH_RESULTS,
        'entities': ','.join([str(x) for x in entities]),
        'has_referral': has_referral,
        'is_all_entities': is_all_entities,
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

    # create a job to export search result
    job = Job.new_export(user, **{
        'text': 'search_results.%s' % recv_data['export_style'],
        'params': recv_data,
    })

    # register task to make export data and cache it
    task_export_search_result.delay(job.id)

    return JsonResponse({
        'result': 'Succeed in registering export processing. ' +
                  'Please check Job list.'
    })
