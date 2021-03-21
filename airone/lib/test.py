import inspect
import sys
import os

from airone.lib.types import AttrTypeValue
from django.test import TestCase, Client, override_settings
from django.conf import settings
from entity.models import Entity, EntityAttr
from user.models import User
from .elasticsearch import ESS


@override_settings(ES_CONFIG={
    'NODES': settings.ES_CONFIG['NODES'],
    'INDEX': 'test-airone',
    'MAXIMUM_RESULTS_NUM': 10000,
    'TIMEOUT': 300
})
class AironeTestCase(TestCase):
    def setUp(self):
        # Before starting test, clear all documents in the Elasticsearch of test index
        self._es = ESS()
        self._es.recreate_index()

        # update airone app
        settings.AIRONE['FILE_STORE_PATH'] = '/tmp/airone_app_test'
        if not os.path.exists(settings.AIRONE['FILE_STORE_PATH']):
            os.makedirs(settings.AIRONE['FILE_STORE_PATH'])

    def tearDown(self):
        # shutil.rmtree(settings.AIRONE['FILE_STORE_PATH'])
        for fname in os.listdir(settings.AIRONE['FILE_STORE_PATH']):
            os.unlink(os.path.join(settings.AIRONE['FILE_STORE_PATH'], fname))

    def create_entity(self, user, name, attrs=[], is_public=True):
        """
        This is a helper method to create Entity for test. This method has following parameters.
        * user      : describes user instance which will be registered on creating Entity
        * name      : describes name of Entity to be created
        * is_public : same parameter of creating Entity [True by default]
        * attrs     : describes EntityAttrs to attach creating Entity
                      and expects to have following information
          - name : indicates name of creating EntityAttr
          - type : indicates type of creating EntityAttr [string by default]
          - is_mandatory : same parameter of EntityAttr [False by default]
        """
        def _get_entity_attr_params(attr_info, attr_param, default_value):
            if attr_param in attr_info and attr_info[attr_param]:
                return attr_info[attr_param]
            else:
                return default_value

        entity = Entity.objects.create(name=name, created_user=user, is_public=is_public)
        for attr_info in attrs:
            entity_attr = EntityAttr.objects.create(**{
                'name': attr_info['name'],
                'type': _get_entity_attr_params(attr_info, 'type', AttrTypeValue['string']),
                'is_mandatory': _get_entity_attr_params(attr_info, 'is_mandatory', False),
                'parent_entity': entity,
                'created_user': user,
            })
            entity.attrs.add()

        return entity

class AironeViewTest(AironeTestCase):
    def setUp(self):
        super(AironeViewTest, self).setUp()

        self.client = Client()

        if hasattr(settings, 'AIRONE') and 'ENABLE_PROFILE' in settings.AIRONE:
            settings.AIRONE['ENABLE_PROFILE'] = False

    def _do_login(self, uname, is_superuser=False):
        # create test user to authenticate
        user = User(username=uname, is_superuser=is_superuser)
        user.set_password(uname)
        user.save()

        self.client.login(username=uname, password=uname)

        return user

    def admin_login(self):
        return self._do_login('admin', True)

    def guest_login(self):
        return self._do_login('guest')

    def open_fixture_file(self, fname):
        test_file_path = inspect.getfile(self.__class__)
        test_base_path = os.path.dirname(test_file_path)

        return open("%s/fixtures/%s" % (test_base_path, fname), 'r')


class DisableStderr(object):
    def __enter__(self):
        self.tmp_stderr = sys.stderr
        self.f = open(os.devnull, 'w')
        sys.stderr = self.f

    def __exit__(self, *arg, **kwargs):
        sys.stderr = self.tmp_stderr
        self.f.close()
