import os

from django.urls import reverse

from airone.lib import custom_view
from airone.lib.test import AironeViewTest
from entity.models import Entity

BASE_DIR = os.path.dirname(os.path.realpath(__file__))


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        self.custom_view_basedir = custom_view.BASE_DIR
        custom_view.BASE_DIR = "%s/custom_view" % BASE_DIR

    def tearDown(self):
        super(ViewTest, self).tearDown()
        custom_view.BASE_DIR = self.custom_view_basedir

    def test_list_entry(self):
        user = self.guest_login()

        # initialize entity for custom_view
        entity = Entity.objects.create(name="entity_has_list_without_context", created_user=user)

        # checks custum list_entry method is called correctly
        resp = self.client.get(reverse("entry:index", args=[entity.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["test_key"], "test_value")

        # checks custum list_entry without context is called correctly
        resp = self.client.get("%s?return_resp=1" % reverse("entry:index", args=[entity.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode("utf-8"), "return no data")
