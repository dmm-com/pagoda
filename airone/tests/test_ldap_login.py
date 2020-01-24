import ldap3
import mock

from django.test import override_settings

from airone.lib.test import AironeTestCase
from user.models import User


@override_settings(AUTHENTICATION_BACKENDS=('airone.auth.ldap.LDAPBackend',))
class ViewTest(AironeTestCase):
    def test_local_authentication(self):
        # When invalid user or password were specified, login processing would be failed.
        self.assertFalse(self.client.login(username='invalid_user', password='invalid_passwd'))
        self.assertFalse(self.client.login(username='guest', password='invalid_passwd'))

        # When both user and password were correct, it would be success.
        user = User(username='guest', email='guest@example.com', is_superuser=False)
        user.set_password('guest')
        user.save()

        self.assertTrue(self.client.login(username='guest', password='guest'))
        self.assertTrue(User.objects.filter(username='guest', is_active=True,
                                            authenticate_type=User.AUTH_TYPE_LOCAL).exists())

    @mock.patch('airone.auth.ldap.ldap3')
    def test_fail_ldap_authentication_caused_by_server_connection(self, ldap_mock):
        class _ConnectionMock(object):
            def __init__(self, *args, **kwargs):
                raise ldap3.core.exceptions.LDAPSocketOpenError('test')
        ldap_mock.Connection = _ConnectionMock

        self.assertFalse(self.client.login(username='ldap_user', password='ldap_passwd'))
        self.assertFalse(User.objects.filter(username='ldap_user', is_active=True).exists())

    @mock.patch('airone.auth.ldap.ldap3')
    def test_fail_ldap_authentication_caused_by_invalid_user(self, ldap_mock):
        class _ConnectionMock(object):
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            def __enter__(self):
                mock_conn = mock.Mock()
                mock_conn.search.return_value = False
                return mock_conn

            def __exit__(self, *args, **kwargs):
                pass
        ldap_mock.Connection = _ConnectionMock

        self.assertFalse(self.client.login(username='ldap_user', password='ldap_passwd'))
        self.assertFalse(User.objects.filter(username='ldap_user', is_active=True).exists())

    @mock.patch('airone.auth.ldap.ldap3')
    def test_fail_ldap_authentication_caused_by_invalid_password(self, ldap_mock):
        class _ConnectionMock(object):
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

                # simulate credentical error
                if 'user' in kwargs:
                    raise ldap3.core.exceptions.LDAPInvalidCredentialsResult('test')

            def __enter__(self):
                mock_result = mock.Mock()
                mock_result.entry_dn = 'user'

                mock_conn = mock.Mock()
                mock_conn.search.return_value = True
                mock_conn.entries = [mock_result]
                return mock_conn

            def __exit__(self, *args, **kwargs):
                pass
        ldap_mock.Connection = _ConnectionMock

        self.assertFalse(self.client.login(username='ldap_user', password='ldap_passwd'))
        self.assertFalse(User.objects.filter(username='ldap_user', is_active=True).exists())

    @mock.patch('airone.auth.ldap.ldap3')
    def test_success_ldap_authentication(self, ldap_mock):
        class _ConnectionMock(object):
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            def __enter__(self):
                mock_result = mock.Mock()
                mock_result.entry_dn = 'user'

                mock_conn = mock.Mock()
                mock_conn.search.return_value = True
                mock_conn.entries = [mock_result]
                return mock_conn

            def __exit__(self, *args, **kwargs):
                pass
        ldap_mock.Connection = _ConnectionMock

        self.assertTrue(self.client.login(username='ldap_user', password='ldap_passwd'))
        self.assertTrue(User.objects.filter(username='ldap_user', is_active=True,
                                            authenticate_type=User.AUTH_TYPE_LDAP).exists())
