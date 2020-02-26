import inspect
import sys
import os

from django.test import TestCase, Client, override_settings
from django.conf import settings
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


def disable_stderr(func):
    def wrapper(*args, **kwargs):
        tmp_stderr = sys.stderr
        f = open(os.devnull, 'w')
        sys.stderr = f
        r = func(*args, **kwargs)
        sys.stderr = tmp_stderr
        f.close()
        return r

    return wrapper
