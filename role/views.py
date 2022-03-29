from airone.lib.http import HttpResponseSeeOther
from airone.lib.http import http_get, http_post, http_file_upload
from airone.lib.http import render
from airone.lib.http import get_download_response
from airone.lib.http import check_superuser
from django.shortcuts import redirect

from group.models import Group
from user.models import User
from role.models import Role


@http_get
def index(request):
    context = {}
    context['roles'] = [{
        'id': x.id,
        'name': x.name,
        'users': User.objects.filter(groups__name=x.name, is_active=True).order_by('username'),
    } for x in Group.objects.filter(is_active=True)]

    return render(request, 'list_role.html', context)


@http_get
def create(request):
    context = {}

    # set group members for each groups
    context['users'] = User.objects.filter(is_active=True)
    context['groups'] = Group.objects.filter(is_active=True)
    context['submit_ref'] = '/role/do_create'

    return render(request, 'role/create.html', context)


@http_post([
    {'name': 'name', 'type': str, 'checker': lambda x: (
        x['name'] and not Role.objects.filter(name=x['name']).exists()
    )},
])
def do_create(request, recv_data):
    print('[onix/do_create(00)] recv_data: %s' % str(recv_data))

    return redirect('/role')
