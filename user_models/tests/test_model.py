from unittest import skip
from django.test import TestCase
from django.db import connections, models, transaction
from user_models.models import UserModel
from django.conf import settings
from airone.lib.test import AironeTestCase


class ModelTest(AironeTestCase):
    def setUp(self):
        super(ModelTest, self).setUp()

    def test_declare_simple_model(self):
        model = UserModel.declare(
            "TestModel", {"name": models.CharField(max_length=200, unique=True)}
        )

        # create DB tables from generated Django model
        self.sync_db_model(model)

        instance = model.objects.create(name="hoge")
        self.assertEqual(instance.name, "hoge")
