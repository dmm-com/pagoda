import inspect
import os
import sys

from django.conf import settings
from django.test import Client, TestCase, override_settings
from pytz import timezone

from airone.lib.types import AttrTypeValue
from entity.models import Entity, EntityAttr
from entry.models import Entry
from user.models import User
from webhook.models import Webhook

from .elasticsearch import ESS


class AironeTestCase(TestCase):
    ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY = [
        {"name": "val", "type": AttrTypeValue["string"]},
        {"name": "vals", "type": AttrTypeValue["array_string"]},
        {"name": "ref", "type": AttrTypeValue["object"]},
        {"name": "refs", "type": AttrTypeValue["array_object"]},
        {"name": "name", "type": AttrTypeValue["named_object"]},
        {"name": "names", "type": AttrTypeValue["array_named_object"]},
        {"name": "group", "type": AttrTypeValue["group"]},
        {"name": "groups", "type": AttrTypeValue["array_group"]},
        {"name": "bool", "type": AttrTypeValue["boolean"]},
        {"name": "text", "type": AttrTypeValue["text"]},
        {"name": "date", "type": AttrTypeValue["date"]},
        {"name": "role", "type": AttrTypeValue["role"]},
        {"name": "roles", "type": AttrTypeValue["array_role"]},
    ]

    TZ_INFO = timezone(settings.TIME_ZONE)

    def setUp(self):
        OVERRIDE_ES_CONFIG = settings.ES_CONFIG.copy()
        OVERRIDE_ES_CONFIG["INDEX"] = "test-" + settings.ES_CONFIG["INDEX"]
        OVERRIDE_AIRONE = settings.AIRONE.copy()
        OVERRIDE_AIRONE["FILE_STORE_PATH"] = "/tmp/airone_app_test"

        if not os.path.exists("/tmp/airone_app_test"):
            os.makedirs("/tmp/airone_app_test")

        # update django settings
        self._settings: override_settings = self.settings(
            ES_CONFIG=OVERRIDE_ES_CONFIG, AIRONE=OVERRIDE_AIRONE
        )
        self._settings.enable()
        self.modify_settings(
            MIDDLEWARE={"remove": "airone.lib.log.LoggingRequestMiddleware"}
        ).enable()

        # Before starting test, clear all documents in the Elasticsearch of test index
        self._es = ESS()
        self._es.recreate_index()

    def tearDown(self):
        # shutil.rmtree(settings.AIRONE['FILE_STORE_PATH'])
        for fname in os.listdir(settings.AIRONE["FILE_STORE_PATH"]):
            os.unlink(os.path.join(settings.AIRONE["FILE_STORE_PATH"], fname))

        self._settings.disable()

    def create_entity(self, user, name, attrs=[], webhooks=[], is_public=True):
        """
        This is a helper method to create Entity for test. This method has following parameters.
        * user      : describes user instance which will be registered on creating Entity
        * name      : describes name of Entity to be created
        * is_public : same parameter of creating Entity [True by default]
        * attrs     : describes EntityAttrs to attach creating Entity
                      and expects to have following information
          - name : indicates name of creating EntityAttr
          - type : indicates type of creating EntityAttr [string by default]
          - is_mandatory : same parameter of EntityAttr [False by default]
          - ref : Entity that Entry can refer to
        """

        entity: Entity = Entity.objects.create(name=name, created_user=user, is_public=is_public)
        for index, attr_info in enumerate(attrs):
            entity_attr: EntityAttr = EntityAttr.objects.create(
                **{
                    "index": index,
                    "name": attr_info["name"],
                    "type": attr_info.get("type", AttrTypeValue["string"]),
                    "is_mandatory": attr_info.get("is_mandatory", False),
                    "parent_entity": entity,
                    "created_user": user,
                }
            )

            if "ref" in attr_info:
                if isinstance(attr_info["ref"], list):
                    for ref in attr_info["ref"]:
                        entity_attr.referral.add(ref)
                else:
                    entity_attr.referral.add(attr_info["ref"])

            entity.attrs.add(entity_attr)

        for webhook_info in webhooks:
            webhook: Webhook = Webhook.objects.create(
                **{
                    "url": webhook_info.get("url", "http://arione.com/"),
                    "label": webhook_info.get("label", "hoge"),
                    "is_enabled": webhook_info.get("is_enabled", True),
                    "is_verified": webhook_info.get("is_verified", True),
                    "headers": webhook_info.get("headers", []),
                }
            )
            entity.webhooks.add(webhook)

        return entity

    def add_entry(self, user, name, schema, values={}, is_public=True):
        entry = Entry.objects.create(
            name=name, schema=schema, created_user=user, is_public=is_public
        )
        entry.complement_attrs(user)

        for attrname, value in values.items():
            attr = entry.attrs.get(schema__name=attrname)
            attr.add_value(user, value)

        # register it to the elasticsearch
        entry.register_es()

        return entry


class AironeViewTest(AironeTestCase):
    def setUp(self):
        super(AironeViewTest, self).setUp()

        self.client = Client()

    def _do_login(self, uname, is_superuser=False):
        # create test user to authenticate
        user = User(username=uname, is_superuser=is_superuser)
        user.set_password(uname)
        user.save()

        self.client.login(username=uname, password=uname)

        return user

    def admin_login(self):
        return self._do_login("admin", True)

    def guest_login(self, uname="guest"):
        return self._do_login(uname)

    def open_fixture_file(self, fname):
        test_file_path = inspect.getfile(self.__class__)
        test_base_path = os.path.dirname(test_file_path)

        return open("%s/fixtures/%s" % (test_base_path, fname), "r")


class DisableStderr(object):
    def __enter__(self):
        self.tmp_stderr = sys.stderr
        self.f = open(os.devnull, "w")
        sys.stderr = self.f

    def __exit__(self, *arg, **kwargs):
        sys.stderr = self.tmp_stderr
        self.f.close()
