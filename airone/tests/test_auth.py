from airone.lib.test import AironeViewTest


class ViewTest(AironeViewTest):
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
