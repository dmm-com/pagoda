from airone.lib.test import AironeViewTest
from airone.auth.social_auth import create_user
from django.conf import settings
from user.models import User

settings.AIRONE["TITLE"] = "TITLE"
settings.AIRONE["SUBTITLE"] = "SUBTITLE"
settings.AIRONE["NOTE_DESC"] = "NOTE_DESC"
settings.AIRONE["NOTE_LINK"] = "NOTE_LINK"
settings.AIRONE["SSO_DESC"] = "SSO_DESC"


class ViewTest(AironeViewTest):
    def test_login_extra_context(self):
        resp = self.client.get("/auth/login/")
        self.assertEqual(resp.context["title"], "TITLE")
        self.assertEqual(resp.context["subtitle"], "SUBTITLE")
        self.assertEqual(resp.context["note_desc"], "NOTE_DESC")
        self.assertEqual(resp.context["note_link"], "NOTE_LINK")
        self.assertEqual(resp.context["sso_desc"], "SSO_DESC")

    def test_logout_with_get(self):
        self.guest_login()
        resp = self.client.get("/auth/logout/")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"Invalid HTTP method is specified")

    def test_logout_with_post(self):
        self.guest_login()
        resp = self.client.post("/auth/logout/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(template_name="registration/logged_out.html")

    def test_social_auth_create_user(self):
        user = User.objects.create(username="hogefuga")

        result = create_user({}, user)
        self.assertEqual(result["is_new"], False)

        result = create_user({"username": "hogefuga", "email": "hogefuga@example.com"})
        self.assertEqual(result["user"], user)

        user.delete()
        result = create_user({"username": "hogefuga", "email": "hogefuga@example.com"})
        new_user = User.objects.filter(username="hogefuga").first()
        self.assertEqual(result["user"], new_user)
