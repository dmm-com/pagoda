import mock
from ldap import LDAPError
from ldap.ldapobject import LDAPObject

from airone.lib.test import AironeTestCase
from django.test import override_settings
from user.models import User


@override_settings(AUTHENTICATION_BACKENDS=('airone.auth.ldap.LDAPBackend',))
class ViewTest(AironeTestCase):
    def test_local_authentication(self):
        # When invalid user or password were specified, login processing would be failed.
        self.assertFalse(self.client.login(username='invalid_user', password='invalid_passwd'))
        self.assertFalse(self.client.login(username='guest', password='invalid_passwd'))

    def test_success_local_authentication(self):
        # When both user and password were correct, it would be success.
        user = User(username='guest', email='guest@example.com', is_superuser=False)
        user.set_password('guest')
        user.save()

        self.assertTrue(self.client.login(username='guest', password='guest'))
        self.assertTrue(User.objects.filter(username='guest', is_active=True,
                                            authenticate_type=User.AUTH_TYPE_LOCAL).exists())

    @mock.patch('airone.auth.ldap.ldap.initialize')
    @mock.patch('airone.auth.ldap.Logger')
    def test_fail_ldap_authentication_caused_by_server_connection(self, mock_logger, mock_ldap):
        mock_obj = mock.Mock(spec=LDAPObject)
        mock_obj.simple_bind_s.side_effect = LDAPError
        mock_ldap.return_value = mock_obj

        self.assertFalse(self.client.login(username='ldap_user', password='ldap_passwd'))
        self.assertFalse(User.objects.filter(username='ldap_user', is_active=True).exists())
        mock_logger.error('some problem was happend')

    @mock.patch('airone.auth.ldap.ldap.initialize')
    def test_fail_ldap_authentication_caused_by_invalid_password(self, mock_ldap):
        mock_obj = mock.Mock(spec=LDAPObject)
        mock_obj.simple_bind_s.side_effect = LDAPError
        mock_ldap.return_value = mock_obj

        self.assertFalse(self.client.login(username='ldap_user', password='ldap_passwd'))
        self.assertFalse(User.objects.filter(username='ldap_user', is_active=True).exists())

    @mock.patch('airone.auth.ldap.ldap.initialize')
    def test_success_ldap_authentication(self, mock_ldap):
        mock_obj = mock.Mock(spec=LDAPObject)
        mock_obj.simple_bind_s.return_value = 1
        mock_ldap.return_value = mock_obj

        self.assertTrue(self.client.login(username='ldap_user', password='ldap_passwd'))
        self.assertTrue(User.objects.filter(username='ldap_user', is_active=True,
                                            authenticate_type=User.AUTH_TYPE_LDAP).exists())
