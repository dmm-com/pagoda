import base64
from airone.lib.test import AironeViewTest

from rest_framework import status
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.authtoken.models import Token

from user.models import User
from django.contrib.auth.models import User as DjangoUser


class APITest(AironeViewTest):
    def test_create_token(self):
        admin = self.admin_login()

        resp = self.client.put("/api/v1/user/access_token")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue("results" in resp.json())
        self.assertTrue(isinstance(resp.json()["results"], str))
        self.assertEqual(resp.json()["results"], str(Token.objects.get(user=admin)))

    def test_refresh_token(self):
        admin = self.admin_login()
        token = Token.objects.create(user=admin)

        resp = self.client.put("/api/v1/user/access_token")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertNotEqual(resp.json()["results"], str(token))

    def test_get_token(self):
        admin = self.admin_login()
        token = Token.objects.create(user=admin)

        resp = self.client.get("/api/v1/user/access_token")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["results"], str(token))

    def test_refresh_token_using_token(self):
        # This processing doesn't login but just only create an User 'guest'
        user = User.objects.create(username="guest")
        token = Token.objects.create(user=DjangoUser.objects.get(id=user.id))

        resp = self.client.get(
            "/api/v1/user/access_token",
            **{
                "HTTP_AUTHORIZATION": "Token %s" % str(token),
            }
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["results"], str(token))

    def test_refresh_token_using_invalid_token(self):
        resp = self.client.get(
            "/api/v1/user/access_token",
            **{
                "HTTP_AUTHORIZATION": "Token %s" % "invlaid-token",
            }
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_token_with_password(self):
        user = User.objects.create(username="test-user")
        user.set_password("password")
        user.save()

        auth_byte = ("%s:%s" % ("test-user", "password")).encode(HTTP_HEADER_ENCODING)
        auth_info = base64.b64encode(auth_byte).decode(HTTP_HEADER_ENCODING)

        resp = self.client.get(
            "/api/v1/user/access_token",
            **{
                "HTTP_AUTHORIZATION": "Basic %s" % auth_info,
            }
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_get_token_with_invalid_password(self):
        user = User.objects.create(username="test-user")
        user.set_password("password")
        user.save()

        auth_byte = ("%s:%s" % ("test-user", "invalid-password")).encode(
            HTTP_HEADER_ENCODING
        )
        auth_info = base64.b64encode(auth_byte).decode(HTTP_HEADER_ENCODING)

        resp = self.client.get(
            "/api/v1/user/access_token",
            **{
                "HTTP_AUTHORIZATION": "Basic %s" % auth_info,
            }
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
