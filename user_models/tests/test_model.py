from unittest import skip
from django.test import TestCase
from django.db import connections, models, transaction
from user_models.models import UserModel
from django.conf import settings

DEFAULT_DB = list(settings.DATABASES.keys())[-1]


class ModelTest(TestCase):
    def setUp(self):
        super(ModelTest, self).setUp()

    # @skip("test implementation is correct but it won't work correctly in Django testing framework")
    def test_declare_simple_model(self):
        model = UserModel.declare(
            "TestModel", {"name": models.CharField(max_length=200, unique=True)}
        )

        connection = connections[DEFAULT_DB]
        with connection.schema_editor() as se:
            in_atomic_block = se.connection.in_atomic_block
            se.connection.in_atomic_block = False
            try:
                se.create_model(model)
            finally:
                se.connection.in_atomic_block = in_atomic_block

        instance = model.objects.create(name="hoge")
        self.assertEqual(instance.name, "hoge")
