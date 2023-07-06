from unittest import skip
from django.test import TestCase
from django.db import connections, models, transaction
from django.urls import reverse
from user.models import User
from user_models.models import UserModel, DRFGenerator
from django.conf import settings
from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue
from entity.models import Entity

from rest_framework.serializers import (
    ModelSerializer,
)


class APITest(AironeViewTest):
    def setUp(self):
        super(APITest, self).setUp()

    def test_declare_serializer_class(self):
        creating_entity_info = {
            "entity_user": {
                "name": "User",
                "sql_name": "user",
                "attrs": [
                    {
                        "name": "user_age",
                        "sql_name": "user_age",
                        "type": AttrTypeValue["string"],
                    },
                ],
            },
        }
        user = User.objects.create(username="test-user")
        for attrname, kwargs in creating_entity_info.items():
            setattr(self, attrname, self.create_entity(user, **kwargs))

        # create Django model from Enttiy
        model = UserModel.create_model_from_entity(self.entity_user)

        # create Serializer Class from Django model
        serializer_class = DRFGenerator.serializer.create(model)

        self.assertTrue(issubclass(serializer_class, ModelSerializer))

    def test_advanced_search_api(self):
        creating_entity_info = {
            "entity_user": {
                "name": "User",
                "sql_name": "user",
                "attrs": [
                    {
                        "name": "user age",
                        "sql_name": "age",
                        "type": AttrTypeValue["string"],
                    },
                ],
            },
        }
        user = self.guest_login()

        for attrname, kwargs in creating_entity_info.items():
            setattr(self, attrname, self.create_entity(user, **kwargs))

        model = UserModel.create_model_from_entity(self.entity_user)

        # create DB tables from generated Django model
        self.sync_db_model(model)

        model.objects.create(name="hoge", age="20")

        resp = self.client.get("/dashboard/api/v2/advanced_search_sql/", {"entity": "User"})
        print(resp.json())
