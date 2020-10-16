import logging
import re
import io
import yaml

from django.http import HttpResponse
from django.http.response import JsonResponse

from .models import Entity
from .models import EntityAttr
from user.models import User, History
from entry.models import Entry, AttributeValue

from airone.lib.types import AttrTypes, AttrTypeValue
from airone.lib.http import http_get, http_post
from airone.lib.http import check_permission
from airone.lib.http import render
from airone.lib.http import get_download_response
from airone.lib.acl import get_permitted_objects
from airone.lib.acl import ACLType
from airone.lib.profile import airone_profile

from .settings import CONFIG

Logger = logging.getLogger(__name__)


@airone_profile
@http_get
def index(request):
    user = User.objects.get(id=request.user.id)

    entity_objects = Entity.objects.order_by('name').filter(is_active=True)
    context = {
        'entities': [x for x in entity_objects if user.has_permission(x, ACLType.Readable)]
    }
    return render(request, 'list_entities.html', context)


@http_get
def create(request):
    user = User.objects.get(id=request.user.id)

    context = {
        'entities': [x for x in Entity.objects.filter(is_active=True)
                     if user.has_permission(x, ACLType.Readable)],
        'attr_types': AttrTypes
    }
    return render(request, 'create_entity.html', context)


@airone_profile
@http_get
@check_permission(Entity, ACLType.Writable)
def edit(request, entity_id):
    user = User.objects.get(id=request.user.id)

    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    # entity to be editted is given by url
    entity = Entity.objects.get(id=entity_id)

    # when an entity in referral attribute is deleted
    # user should be able to select new entity or keep it unchanged
    # candidate entites for referral are:
    # - active(not deleted) entity
    # - current value of any attributes even if the entity has been deleted
    context = {
        'entity': entity,
        'attr_types': AttrTypes,
        'attributes': [{
            'id': x.id,
            'name': x.name,
            'type': x.type,
            'is_mandatory': x.is_mandatory,
            'is_delete_in_chain': x.is_delete_in_chain,
            'referrals': x.referral.all()
        } for x in entity.attrs.filter(is_active=True).order_by('index')
            if user.has_permission(x, ACLType.Writable)],
    }
    return render(request, 'edit_entity.html', context)


@airone_profile
@http_post([
    {'name': 'name', 'type': str, 'checker': lambda x: x['name']},
    {'name': 'note', 'type': str},
    {'name': 'is_toplevel', 'type': bool},
    {'name': 'attrs', 'type': list, 'meta': [
        {'name': 'name', 'type': str, 'checker': lambda x: (
            x['name'] and not re.match(r'^\s*$', x['name'])
        )},
        {'name': 'type', 'type': str, 'checker': lambda x: (
            any([y == int(x['type']) for y in AttrTypes])
        )},
        {'name': 'is_mandatory', 'type': bool},
        {'name': 'is_delete_in_chain', 'type': bool},
        {'name': 'row_index', 'type': str, 'checker': lambda x: (
            re.match(r"^[0-9]*$", x['row_index'])
        )}
    ]}
])
@check_permission(Entity, ACLType.Writable)
def do_edit(request, entity_id, recv_data):
    user = User.objects.get(id=request.user.id)

    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    # validation checks
    for attr in recv_data['attrs']:
        # formalize recv_data format
        if 'ref_ids' not in attr:
            attr['ref_ids'] = []

        if int(attr['type']) & AttrTypeValue['object'] and not attr['ref_ids']:
            return HttpResponse('Need to specify enabled referral ids', status=400)

        if any([not Entity.objects.filter(id=x).exists() for x in attr['ref_ids']]):
            return HttpResponse('Specified referral is invalid', status=400)

    entity = Entity.objects.get(id=entity_id)

    # register history to modify Entity
    history = user.seth_entity_mod(entity)

    # check operation history detail
    if entity.name != recv_data['name']:
        history.mod_entity(entity, 'old name: "%s"' % (entity.name))

    # update status parameters
    if recv_data['is_toplevel']:
        entity.set_status(Entity.STATUS_TOP_LEVEL)
    else:
        entity.del_status(Entity.STATUS_TOP_LEVEL)

    # update entity metatada informations to new ones
    entity.name = recv_data['name']
    entity.note = recv_data['note']
    entity.save()

    # update processing for each attrs
    for attr in recv_data['attrs']:
        if 'deleted' in attr:
            # In case of deleting attribute which has been already existed
            attr_obj = EntityAttr.objects.get(id=attr['id'])
            attr_obj.delete()

            # register History to register deleting EntityAttr
            history.del_attr(attr_obj)

        elif 'id' in attr and EntityAttr.objects.filter(id=attr['id']).exists():
            # In case of updating attribute which has been already existed
            attr_obj = EntityAttr.objects.get(id=attr['id'])

            # register operaion history if the parameters are changed
            if attr_obj.name != attr['name']:
                history.mod_attr(attr_obj, 'old name: "%s"' % (attr_obj.name))

            if attr_obj.is_mandatory != attr['is_mandatory']:
                if attr['is_mandatory']:
                    history.mod_attr(attr_obj, 'set mandatory flag')
                else:
                    history.mod_attr(attr_obj, 'unset mandatory flag')

            params = {
                'name': attr['name'],
                'refs': [int(x) for x in attr['ref_ids']],
                'index': attr['row_index'],
                'is_mandatory': attr['is_mandatory'],
                'is_delete_in_chain': attr['is_delete_in_chain'],
            }
            if attr_obj.is_updated(**params):
                attr_obj.name = attr['name']
                attr_obj.is_mandatory = attr['is_mandatory']
                attr_obj.is_delete_in_chain = attr['is_delete_in_chain']
                attr_obj.index = int(attr['row_index'])

                attr_obj.save()

        else:
            # In case of creating new attribute
            attr_obj = EntityAttr.objects.create(name=attr['name'],
                                                 type=int(attr['type']),
                                                 is_mandatory=attr['is_mandatory'],
                                                 is_delete_in_chain=attr['is_delete_in_chain'],
                                                 index=int(attr['row_index']),
                                                 created_user=user,
                                                 parent_entity=entity)

            # append referral objects
            if int(attr['type']) & AttrTypeValue['object']:
                [attr_obj.referral.add(Entity.objects.get(id=x)) for x in attr['ref_ids']]

            # add a new attribute on the existed Entries
            entity.attrs.add(attr_obj)

            # register History to register adding EntityAttr
            history.add_attr(attr_obj)

    return JsonResponse({
        'entity_id': entity.id,
        'entity_name': entity.name,
        'msg': 'Success to update Entity "%s"' % entity.name,
    })


@http_post([
    {'name': 'name', 'type': str, 'checker': lambda x: (
        x['name'] and not Entity.objects.filter(name=x['name']).exists()
    )},
    {'name': 'note', 'type': str},
    {'name': 'is_toplevel', 'type': bool},
    {'name': 'attrs', 'type': list, 'meta': [
        {'name': 'name', 'type': str, 'checker': lambda x: (
            x['name'] and not re.match(r'^\s*$', x['name'])
        )},
        {'name': 'type', 'type': str, 'checker': lambda x: (
            any([y == int(x['type']) for y in AttrTypes])
        )},
        {'name': 'is_mandatory', 'type': bool},
        {'name': 'is_delete_in_chain', 'type': bool},
        {'name': 'row_index', 'type': str, 'checker': lambda x: (
            re.match(r"^[0-9]*$", x['row_index'])
        )}
    ]},
])
def do_create(request, recv_data):
    # validation checks
    for attr in recv_data['attrs']:
        # formalize recv_data format
        if 'ref_ids' not in attr:
            attr['ref_ids'] = []

        if int(attr['type']) & AttrTypeValue['object'] and not attr['ref_ids']:
            return HttpResponse('Need to specify enabled referral ids', status=400)

        if any([not Entity.objects.filter(id=x).exists() for x in attr['ref_ids']]):
            return HttpResponse('Specified referral is invalid', status=400)

    # get user object that current access
    user = User.objects.get(id=request.user.id)

    # create EntityAttr objects
    entity = Entity(name=recv_data['name'],
                    note=recv_data['note'],
                    created_user=user)

    # set status parameters
    if recv_data['is_toplevel']:
        entity.set_status(Entity.STATUS_TOP_LEVEL)

    entity.save()

    # register history to modify Entity
    history = user.seth_entity_add(entity)

    for attr in recv_data['attrs']:
        attr_base = EntityAttr.objects.create(name=attr['name'],
                                              type=int(attr['type']),
                                              is_mandatory=attr['is_mandatory'],
                                              is_delete_in_chain=attr['is_delete_in_chain'],
                                              created_user=user,
                                              parent_entity=entity,
                                              index=int(attr['row_index']))

        if int(attr['type']) & AttrTypeValue['object']:
            [attr_base.referral.add(Entity.objects.get(id=x)) for x in attr['ref_ids']]

        entity.attrs.add(attr_base)

        # register history to modify Entity
        history.add_attr(attr_base)

    return JsonResponse({
        'entity_id': entity.id,
        'entity_name': entity.name,
        'msg': 'Success to create Entity "%s"' % entity.name,
    })


@http_get
def export(request):
    user = User.objects.get(id=request.user.id)

    output = io.StringIO()

    data = {
        "Entity": [],
        "EntityAttr": []
    }

    entities = get_permitted_objects(user, Entity, ACLType.Readable)
    for entity in entities:
        data["Entity"].append({
            "created_user": entity.created_user.username,
            "id": entity.id,
            "name": entity.name,
            "note": entity.note,
            "status": entity.status,
        })

    attrs = get_permitted_objects(user, EntityAttr, ACLType.Readable)
    for attr in attrs:
        data["EntityAttr"].append({
            "created_user": attr.created_user.username,
            "entity": attr.parent_entity.name,
            "id": attr.id,
            "is_mandatory": attr.is_mandatory,
            "name": attr.name,
            "refer": ",".join(list(map(lambda x: x.name, attr.referral.filter(is_active=True)))),
            "type": attr.type,
        })

    output.write(yaml.dump(data, default_flow_style=False, allow_unicode=True))
    return get_download_response(output, 'entity.yaml')


@http_post([])
@check_permission(Entity, ACLType.Full)
def do_delete(request, entity_id, recv_data):
    user = User.objects.get(id=request.user.id)
    ret = {}

    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    entity = Entity.objects.get(id=entity_id)

    # save deleting target name before do it
    ret['name'] = entity.name

    if Entry.objects.filter(schema=entity, is_active=True).exists():
        return HttpResponse('cannot delete Entity because one or more Entries are not deleted',
                            status=400)

    entity.delete()
    history = user.seth_entity_del(entity)

    # Delete all attributes which target Entity have
    for attr in entity.attrs.all():
        attr.delete()
        history.del_attr(attr)

    return JsonResponse(ret)


@http_get
def history(request, entity_id):
    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    # entity to be editted is given by url
    entity = Entity.objects.get(id=entity_id)

    context = {
        'entity': entity,
        'history': History.objects.filter(target_obj=entity, is_detail=False).order_by('-time'),
    }

    return render(request, 'history_entity.html', context)


@http_get
def dashboard(request, entity_id):
    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    # entity to be editted is given by url
    entity = Entity.objects.get(id=entity_id)
    total_entry_count = Entry.objects.filter(schema=entity, is_active=True).count()

    summarized_data = {}
    for attr in EntityAttr.objects.filter(parent_entity=entity, is_active=True, is_summarized=True):
        summarized_data[attr] = {
            'referral_count': [{
                'referral': r.name,
                'count': AttributeValue.objects.filter(**{
                    'parent_attr__is_active': True,
                    'parent_attr__schema': attr,
                    'is_latest': True,
                    'referral': r,
                }).count(),
            } for r in Entry.objects.filter(schema=attr.referral.first(), is_active=True)],
        }

        # filter elements which count is 0
        summarized_data[attr]['referral_count'] = \
            [x for x in summarized_data[attr]['referral_count'] if x['count'] > 0]

        # set count of entries which doesn't have referral
        summarized_data[attr]['no_referral_count'] = \
            Entry.objects.filter(schema=entity, is_active=True).count() - \
            sum([x['count'] for x in summarized_data[attr]['referral_count']])

        summarized_data[attr]['no_referral_ratio'] = '%2.1f' % \
            ((100 * summarized_data[attr]['no_referral_count']) / total_entry_count)

        # sort by referral counts
        summarized_data[attr]['referral_count'] = sorted(summarized_data[attr]['referral_count'],
                                                         key=lambda x: x['count'],
                                                         reverse=True)

        # summarize results to prevent overflowing results by a lot of tiny elements
        if len(summarized_data[attr]['referral_count']) > CONFIG.DASHBOARD_NUM_ITEMS:
            rest_counts = sum(
                [
                    x['count'] for x in
                    summarized_data[attr]['referral_count'][CONFIG.DASHBOARD_NUM_ITEMS:]
                ]
            )

            summarized_data[attr]['referral_count'] = \
                summarized_data[attr]['referral_count'][:CONFIG.DASHBOARD_NUM_ITEMS]
            summarized_data[attr]['referral_count'].append({
                'referral': '(Others)',
                'count': rest_counts,
                'ratio': '%2.1f' % ((rest_counts * 100) / total_entry_count),
            })

        # set ratio for each elements
        for info in summarized_data[attr]['referral_count']:
            info['ratio'] = '%2.1f' % ((info['count'] * 100) / total_entry_count)

    context = {
        'entity': entity,
        'total_entry_count': total_entry_count,
        'summarized_data': summarized_data,
    }
    return render(request, 'dashboard_entity.html', context)


@http_get
def conf_dashboard(request, entity_id):
    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    # entity to be editted is given by url
    entity = Entity.objects.get(id=entity_id)

    context = {
        'entity': entity,
        'ref_attrs': EntityAttr.objects.filter(parent_entity=entity, type=AttrTypeValue['object'],
                                               is_active=True),
        'redirect_url': '/entity/dashboard/config/register/%s' % entity_id,
    }
    return render(request, 'conf_dashboard_entity.html', context)


@http_post([
    {'name': 'attrs', 'type': list,
     'checker': lambda x: all([EntityAttr.objects.filter(id=v).exists() for v in x['attrs']])}
])
def do_conf_dashboard(request, entity_id, recv_data):
    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    # clear is_summarized flag for each EntityAttrs corresponding to the entity
    EntityAttr.objects.filter(parent_entity=entity_id).update(is_summarized=False)

    # set is_summarized flag for each specified EntityAttrs
    for attr in [EntityAttr.objects.get(id=x) for x in recv_data['attrs']]:
        attr.is_summarized = True
        attr.save(update_fields=['is_summarized'])

    return JsonResponse({'msg': 'Success to update dashboard'})
