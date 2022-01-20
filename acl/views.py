from django.http import HttpResponse
from django.http.response import JsonResponse

from airone.lib.acl import ACLType, ACLObjType
from airone.lib.http import http_get, http_post, render
from airone.lib.http import get_object_with_check_permission
from airone.lib.profile import airone_profile
from airone.lib.log import Logger

from entity.models import Entity, EntityAttr
from entry.models import Entry, Attribute
from group.models import Group
from user.models import User
from .models import ACLBase


@airone_profile
@http_get
def index(request, obj_id):
    user = User.objects.get(id=request.user.id)
    aclbase_obj, error = get_object_with_check_permission(user, ACLBase, obj_id, ACLType.Full)
    if error:
        return error
    target_obj = aclbase_obj.get_subclass_object()

    # get ACLTypeID of target_obj if a permission is set
    def get_current_permission(member):
        permissions = [x for x in member.permissions.all() if x.get_objid() == target_obj.id]
        if permissions:
            return permissions[0].get_aclid()
        else:
            return 0

    # Some type of objects needs object that refers target_obj (e.g. Attribute)
    # for showing breadcrumb navigation.
    parent_obj = None
    try:
        if isinstance(target_obj, Attribute):
            parent_obj = target_obj.parent_entry
        elif isinstance(target_obj, EntityAttr):
            parent_obj = target_obj.parent_entity
    except StopIteration:
        Logger.warning('failed to get related parent object')

    context = {
        'object': target_obj,
        'parent': parent_obj,
        'acltypes': [{'id': x.id, 'name': x.label} for x in ACLType.all()],
        'members': [{'id': x.id,
                     'name': x.username,
                     'current_permission': get_current_permission(x),
                     'type': 'user'} for x in User.objects.filter(is_active=True)] +
                   [{'id': x.id,
                     'name': x.name,
                     'current_permission': get_current_permission(x),
                     'type': 'group'} for x in Group.objects.filter(is_active=True)]
    }
    return render(request, 'edit_acl.html', context)


@airone_profile
@http_post([
    {'name': 'object_id', 'type': str,
     'checker': lambda x: ACLBase.objects.filter(id=x['object_id']).exists()},
    {'name': 'object_type', 'type': str,
     'checker': lambda x: x['object_type']},
    {'name': 'acl', 'type': list, 'meta': [
        {'name': 'member_type', 'type': str,
         'checker': lambda x: x['member_type'] == 'user' or x['member_type'] == 'group'},
        {'name': 'member_id', 'type': str,
         'checker': lambda x: any(
             [k.objects.filter(id=x['member_id']).exists() for k in [User, Group]]
          )},
        {'name': 'value', 'type': (str, type(None)),
         'checker': lambda x: [y for y in ACLType.all() if int(x['value']) == y]},
    ]},
    {'name': 'default_permission', 'type': str, 'checker': lambda x: any(
        [y == int(x['default_permission']) for y in ACLType.all()]
    )},
])
def set(request, recv_data):
    user = User.objects.get(id=request.user.id)
    acl_obj = getattr(_get_acl_model(recv_data['object_type']),
                      'objects').get(id=recv_data['object_id'])

    if not user.has_permission(acl_obj, ACLType.Full):
        return HttpResponse(
            "User(%s) doesn't have permission to change this ACL" % user.username, status=400)

    if not user.may_permitted(acl_obj, ACLType.Full, **{
            'is_public': True if 'is_public' in recv_data else False,
            'default_permission': int(recv_data['default_permission']),
            'acl_settings': recv_data['acl']}):
        return HttpResponse(
            "Inadmissible setting. By this change you will never change this ACL", status=400)

    acl_obj.is_public = False
    if 'is_public' in recv_data:
        acl_obj.is_public = True

    acl_obj.default_permission = int(recv_data['default_permission'])

    # update the Public/Private flag parameter
    acl_obj.save()

    for acl_data in [x for x in recv_data['acl'] if x['value']]:
        if acl_data['member_type'] == 'user':
            member = User.objects.get(id=acl_data['member_id'])
        else:
            member = Group.objects.get(id=acl_data['member_id'])

        acl_type = [x for x in ACLType.all() if x == int(acl_data['value'])][0]

        # update permissios for the target ACLBased object
        _set_permission(member, acl_obj, acl_type)

    redirect_url = '/'
    if isinstance(acl_obj, Entity):
        redirect_url = '/entity/'
    elif isinstance(acl_obj, EntityAttr):
        redirect_url = '/entity/edit/%s' % acl_obj.parent_entity.id
    elif isinstance(acl_obj, Entry):
        redirect_url = '/entry/show/%s' % acl_obj.id
    elif isinstance(acl_obj, Attribute):
        redirect_url = '/entry/edit/%s' % acl_obj.parent_entry.id

    if isinstance(acl_obj, Attribute):
        acl_obj = acl_obj.parent_entry

    if isinstance(acl_obj, Entry):
        acl_obj.register_es()

    return JsonResponse({
        'redirect_url': redirect_url,
        'msg': 'Success to update ACL of "%s"' % acl_obj.name,
    })


def _get_acl_model(object_id):
    if int(object_id) == ACLObjType.Entity:
        return Entity
    if int(object_id) == ACLObjType.Entry:
        return Entry
    elif int(object_id) == ACLObjType.EntityAttr:
        return EntityAttr
    elif int(object_id) == ACLObjType.EntryAttr:
        return Attribute
    else:
        return ACLBase


def _set_permission(member, acl_obj, acl_type):
    # clear unset permissions of target ACLbased object
    for _acltype in ACLType.all():
        if _acltype != acl_type and _acltype != ACLType.Nothing:
            member.permissions.remove(getattr(acl_obj, _acltype.name))

    # set new permissoin to be specified except for 'Nothing' permission
    if acl_type != ACLType.Nothing:
        member.permissions.add(getattr(acl_obj, acl_type.name))
