from airone.lib.test import AironeViewTest
from django.conf import settings

settings.AIRONE['TITLE'] = 'TITLE'
settings.AIRONE['SUBTITLE'] = 'SUBTITLE'
settings.AIRONE['NOTE_DESC'] = 'NOTE_DESC'
settings.AIRONE['NOTE_LINK'] = 'NOTE_LINK'


class ViewTest(AironeViewTest):
    def test_login_extra_context(self):
        resp = self.client.get('/auth/login/')
        self.assertEqual(resp.context['title'], 'TITLE')
        self.assertEqual(resp.context['subtitle'], 'SUBTITLE')
        self.assertEqual(resp.context['note_desc'], 'NOTE_DESC')
        self.assertEqual(resp.context['note_link'], 'NOTE_LINK')

    def test_logout_with_get(self):
        self.guest_login()
        resp = self.client.get('/auth/logout/')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'Invalid HTTP method is specified')

    def test_logout_with_post(self):
        self.guest_login()
        resp = self.client.post('/auth/logout/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(template_name='registration/logged_out.html')
