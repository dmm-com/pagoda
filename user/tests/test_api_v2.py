from airone.lib.test import AironeViewTest
from user.models import User


class ViewTest(AironeViewTest):

    def _create_user(self, name, email='email', is_superuser=False,
                     authenticate_type=User.AUTH_TYPE_LOCAL):
        user = User(username=name, email=email, is_superuser=is_superuser,
                    authenticate_type=authenticate_type)
        user.set_password(name)
        user.save()

        return user

    def test_get_user(self):
        login_user = self.guest_login()

        resp = self.client.get('/user/api/v2/users/%s' % login_user.id)
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertEqual(body['id'], login_user.id)
        self.assertEqual(body['username'], login_user.username)
        self.assertEqual(body['email'], login_user.email)
        self.assertEqual(body['is_superuser'], login_user.is_superuser)
        self.assertEqual(body['date_joined'], login_user.date_joined.isoformat())
        self.assertNotEqual(body['token'], '')
        self.assertEqual(body['token_lifetime'], login_user.token_lifetime)
        self.assertIsNotNone(body['token_expire'])

        other = self._create_user('test1', 'test1@example.com')
        resp = self.client.get('/user/api/v2/users/%s' % other.id)
        self.assertEqual(resp.status_code, 400)

    def test_list_user(self):
        login_user = self.guest_login()

        origins = [
            self._create_user('test1', 'test1@example.com'),
            self._create_user('test2', 'test2@example.com'),
        ]

        resp = self.client.get('/user/api/v2/users')
        self.assertEqual(resp.status_code, 200)

        body = [x for x in resp.json() if x['id'] != login_user.id]
        self.assertEqual(len(body), len(origins))

        for i, x in enumerate(body):
            self.assertEqual(x['id'], origins[i].id)
            self.assertEqual(x['username'], origins[i].username)
            self.assertEqual(x['email'], origins[i].email)
            self.assertEqual(x['is_superuser'], origins[i].is_superuser)
            self.assertEqual(x['date_joined'], origins[i].date_joined.isoformat())
