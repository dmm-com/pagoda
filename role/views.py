import json

from airone.lib.http import HttpResponseSeeOther
from airone.lib.http import http_get, http_post, http_file_upload
from airone.lib.http import render
from airone.lib.http import get_download_response
from airone.lib.http import check_superuser
from django.http.response import JsonResponse
from django.shortcuts import redirect

from group.models import Group
from user.models import User
from role.models import Role
from role.settings import CONFIG


@http_get
def index(request):
    context = {}
    context['roles'] = [{
        'id': x.id,
        'name': x.name,
        'users': x.users.all().order_by('username'),
        'groups': x.groups.all().order_by('name'),
        'admin_users': x.administrative_users.all().order_by('username'),
        'admin_groups': x.administrative_groups.all().order_by('name'),
    } for x in Role.objects.filter(is_active=True)]

    return render(request, 'list_role.html', context)


@http_get
def create(request):
    context = {}

    # set group members for each groups
    context["users"] = [{
            "id": u.id,
            "name": u.username,
        } for u in User.objects.filter(is_active=True).order_by("username")]
    context["groups"] = [{
            "id": g.id,
            "name": g.name,
        } for g in Group.objects.filter(is_active=True).order_by("name")]
    context['submit_ref'] = '/role/do_create'

    return render(request, 'role/create.html', context)


@http_post([
    {'name': 'name', 'type': str, 'checker': lambda x: (
        x['name'] and not Role.objects.filter(name=x['name'], is_active=True).exists()
    )},
    {'name': 'users', 'type': list, 'meta': [{'name': 'id', 'type': int}]},
    {'name': 'groups', 'type': list, 'meta': [{'name': 'id', 'type': int}]},
    {'name': 'admin_users', 'type': list, 'meta': [{'name': 'id', 'type': int}]},
    {'name': 'admin_groups', 'type': list, 'meta': [{'name': 'id', 'type': int}]},
])
def do_create(request, recv_data):
    role = Role.objects.create(name=recv_data['name'])
    for (model, member, key) in [(User, 'users', 'users'), (Group, 'groups', 'groups'),
                         (User, 'administrative_users', 'admin_users'),
                         (Group, 'administrative_groups', 'admin_groups')]:
        for obj in recv_data[key]:
            instance = model.objects.filter(id=obj['id'], is_active=True).first()
            if instance:
                getattr(role, member).add(instance)

    return JsonResponse({
        'msg': 'Succeeded in creating new Role "%s"' % recv_data['name']
    })


@http_get
def edit(request):
    context = {}

    # set group members for each groups
    context["users"] = [{
            "id": u.id,
            "name": u.username,
        } for u in User.objects.filter(is_active=True).order_by("username")]
    context["groups"] = [{
            "id": g.id,
            "name": g.name,
        } for g in Group.objects.filter(is_active=True).order_by("name")]
    context['submit_ref'] = '/role/do_edit'

    return render(request, 'role/create.html', context)


@http_post([
    {'name': 'name', 'type': str, 'checker': lambda x: (
        x['name'] and Role.objects.filter(name=x['name'], is_active=True).exists()
    )},
])
def do_edit(request, recv_data):
    print('[onix/do_edit(00)] recv_data: %s' % str(recv_data))

    return redirect('/role')
