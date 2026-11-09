from urllib.parse import quote

from django.conf import settings
from django.test import override_settings

from airone.auth.social_auth import create_user
from airone.lib.test import AironeViewTest, extract_json_script
from user.models import User


class ViewTest(AironeViewTest):
    def setUp(self):
        # AironeTestCase.setUp swaps settings.AIRONE for a per-test copy, so
        # mutating it here (instead of at import time) cannot leak into tests
        # of other modules that run in the same process
        super().setUp()
        settings.AIRONE["TITLE"] = "TITLE"
        settings.AIRONE["SUBTITLE"] = "SUBTITLE"
        settings.AIRONE["NOTE_DESC"] = "NOTE_DESC"
        settings.AIRONE["NOTE_LINK"] = "NOTE_LINK"
        settings.AIRONE["SSO_DESC"] = "SSO_DESC"
        settings.AIRONE["PASSWORD_RESET_DISABLED"] = True

    def test_login_extra_context(self):
        resp = self.client.get("/auth/login/")
        self.assertEqual(resp.context["title"], "TITLE")
        self.assertEqual(resp.context["subtitle"], "SUBTITLE")
        self.assertEqual(resp.context["note_desc"], "NOTE_DESC")
        self.assertEqual(resp.context["note_link"], "NOTE_LINK")
        self.assertEqual(resp.context["sso_desc"], "SSO_DESC")
        self.assertEqual(resp.context["password_reset_disabled"], True)

    def test_login_context_payload(self):
        resp = self.client.get("/auth/login/", {"next": "/ui/entries/"})
        self.assertEqual(resp.status_code, 200)

        payload = extract_json_script(resp.content.decode("utf-8"), "django-context")
        self.assertEqual(payload["next"], "/ui/entries/")
        self.assertEqual(payload["title"], "TITLE")
        self.assertEqual(payload["subtitle"], "SUBTITLE")
        self.assertEqual(payload["note_desc"], "NOTE_DESC")
        self.assertEqual(payload["note_link"], "NOTE_LINK")
        self.assertEqual(payload["password_reset_disabled"], True)
        self.assertNotIn("singleSignOnLoginUrl", payload)

    def test_login_page_does_not_emit_raw_next_value(self):
        # A next value that contains a script closing tag must not be emitted
        # verbatim into the page.
        payload = "</script><script>alert(1)</script>/ui/"

        resp = self.client.get("/auth/login/", {"next": payload})
        self.assertEqual(resp.status_code, 200)

        content = resp.content.decode("utf-8")
        self.assertNotIn(payload, content)
        self.assertNotIn("</script><script>alert(1)</script>", content)

        # The value is still delivered to the client as JSON data
        self.assertEqual(extract_json_script(content, "django-context")["next"], payload)

    @override_settings(SOCIAL_AUTH_SAML_ENABLED_IDPS={"idp1": {}})
    def test_legacy_login_page_sso_url_is_encoded(self):
        # A next value without '/ui/' renders the legacy (non-SPA) form, which
        # must use the same URL-encoded SSO link.
        resp = self.client.get("/auth/login/", {"next": "/dashboard/?a=1&b=2"})
        self.assertEqual(resp.status_code, 200)

        content = resp.content.decode("utf-8")
        self.assertIn("idp=idp1", content)
        self.assertIn("next=%2Fdashboard%2F%3Fa%3D1%26b%3D2", content)

    @override_settings(SOCIAL_AUTH_SAML_ENABLED_IDPS={"idp1": {}})
    def test_login_page_does_not_emit_raw_next_value_in_sso_url(self):
        payload = '</script><script>alert(1)</script>/ui/"'

        resp = self.client.get("/auth/login/", {"next": payload})
        self.assertEqual(resp.status_code, 200)

        content = resp.content.decode("utf-8")
        self.assertNotIn("</script><script>alert(1)</script>", content)

        sso_url = extract_json_script(content, "django-context")["singleSignOnLoginUrl"]
        self.assertIsNotNone(sso_url)
        self.assertIn("idp=idp1", sso_url)
        self.assertIn("next=" + quote(payload, safe=""), sso_url)

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
