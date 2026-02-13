import functools
import inspect
import logging
import os
import sys
from typing import List

from django.conf import settings
from django.test import Client, TestCase, override_settings
from pytz import timezone

from airone.lib.acl import ACLType
from airone.lib.types import AttrType
from category.models import Category
from entity.models import Entity, EntityAttr, ItemNameType
from entry.models import Attribute, Entry
from user.models import User
from webhook.models import Webhook

from .elasticsearch import ESS


class AironeTestCase(TestCase):
    ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY = [
        {"name": "val", "type": AttrType.STRING},
        {"name": "vals", "type": AttrType.ARRAY_STRING},
        {"name": "ref", "type": AttrType.OBJECT},
        {"name": "refs", "type": AttrType.ARRAY_OBJECT},
        {"name": "name", "type": AttrType.NAMED_OBJECT},
        {"name": "names", "type": AttrType.ARRAY_NAMED_OBJECT},
        {"name": "group", "type": AttrType.GROUP},
        {"name": "groups", "type": AttrType.ARRAY_GROUP},
        {"name": "bool", "type": AttrType.BOOLEAN},
        {"name": "text", "type": AttrType.TEXT},
        {"name": "date", "type": AttrType.DATE},
        {"name": "role", "type": AttrType.ROLE},
        {"name": "roles", "type": AttrType.ARRAY_ROLE},
        {"name": "datetime", "type": AttrType.DATETIME},
        {"name": "num", "type": AttrType.NUMBER},
        {"name": "nums", "type": AttrType.ARRAY_NUMBER},
    ]

    TZ_INFO = timezone(settings.TIME_ZONE)

    def setUp(self):
        OVERRIDE_ES_CONFIG = settings.ES_CONFIG.copy()
        # Attach prefix "test-" to distinguish index name for test with configured one.
        # This should be only one time.
        if settings.ES_CONFIG["INDEX_NAME"].find("test-") != 0:
            OVERRIDE_ES_CONFIG["INDEX_NAME"] = "test-" + settings.ES_CONFIG["INDEX_NAME"]
        # Append pid suffix to enable parallel test
        OVERRIDE_ES_CONFIG["INDEX_NAME"] += "-" + str(os.getpid())
        OVERRIDE_AIRONE = settings.AIRONE.copy()
        OVERRIDE_AIRONE_FLAGS = settings.AIRONE_FLAGS.copy()
        # Append pid suffix to enable parallel test
        MEDIA_ROOT = "/tmp/airone_app_test_" + str(os.getpid())

        if not os.path.exists(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

        # update django settings
        self._settings: override_settings = self.settings(
            ES_CONFIG=OVERRIDE_ES_CONFIG,
            AIRONE=OVERRIDE_AIRONE,
            AIRONE_FLAGS=OVERRIDE_AIRONE_FLAGS,
            MEDIA_ROOT=MEDIA_ROOT,
        )
        self._settings.enable()
        self.modify_settings(
            MIDDLEWARE={"remove": "airone.lib.log.LoggingRequestMiddleware"}
        ).enable()

        # Before starting test, clear all documents in the Elasticsearch of test index
        self._es = ESS()
        self._es.recreate_index()

    def tearDown(self):
        # Clean up Elasticsearch test index
        if hasattr(self, "_es") and self._es:
            try:
                self._es.indices.delete(index=self._es._index, ignore=[400, 404])
            except Exception as e:
                # Don't fail the test due to cleanup errors
                logging.warning(f"Failed to cleanup ES index {self._es._index}: {e}")

        for fname in os.listdir(settings.MEDIA_ROOT):
            os.unlink(os.path.join(settings.MEDIA_ROOT, fname))

        self._settings.disable()

    def _do_update_entity(
        self,
        user,
        entity,
        attrs=[],
        webhooks=[],
    ):
        for index, attr_info in enumerate(attrs):
            entity_attr: EntityAttr = EntityAttr.objects.create(
                **{
                    "index": index,
                    "name": attr_info["name"],
                    "type": attr_info.get("type", AttrType.STRING),
                    "is_mandatory": attr_info.get("is_mandatory", False),
                    "is_public": attr_info.get("is_public", True),
                    "default_permission": attr_info.get("default_permission", ACLType.Nothing.id),
                    "parent_entity": entity,
                    "created_user": user,
                    "name_order": attr_info.get("name_order", 0),
                    "name_prefix": attr_info.get("name_prefix", ""),
                    "name_postfix": attr_info.get("name_postfix", ""),
                }
            )

            # register referral(s) EntityAttr.add_referral() supports any kind of types
            entity_attr.add_referral(attr_info.get("ref"))

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

    def create_entity(
        self,
        user,
        name,
        attrs=[],
        is_public=True,
        item_name_pattern="",
        item_name_type=None,
        default_permission=ACLType.Nothing.id,
        *args,
        **kwargs,
    ):
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
          - is_public: same parameter of creating EntityAttr [True by default]
          - default_permission: same parameter of creating EntityAttr
                                [ACLType.Nothing.id by default]
          - ref : Entity that Entry can refer to
          - name_order: number of name order when ItemNameType.ATTR is set
          - name_prefix: prefix string when ItemNameType.ATTR is set
          - name_postfix: postfix string when ItemNameType.ATTR is set
        """
        entity: Entity = Entity.objects.create(
            name=name,
            created_user=user,
            is_public=is_public,
            default_permission=default_permission,
            item_name_pattern=item_name_pattern if item_name_pattern else "",
            item_name_type=item_name_type if item_name_type else ItemNameType.USER,
        )

        return self._do_update_entity(user, entity, attrs, *args, **kwargs)

    def update_entity(self, user, entity, *args, **kwargs):
        return self._do_update_entity(user, entity, *args, **kwargs)

    def add_entry(self, user: User, name: str, schema: Entity, values={}, is_public=True) -> Entry:
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

    def create_category(
        self, user: User, name: str, note: str = "", models: List[Entity] = [], priority=0
    ) -> Category:
        # create target Category instance
        category = Category.objects.create(
            name=name, note=note, priority=priority, created_user=user
        )

        # attach created category to each specified Models
        for model in models:
            if model.is_active:
                model.categories.add(category)

        return category

    def create_entity_with_all_type_attributes(
        self, user: User, ref_entity: Entity | None = None
    ) -> Entity:
        """Create entity with all 16 attribute types for comprehensive testing."""
        entity = Entity.objects.create(name="all_attr_entity", created_user=user)
        attr_info = {
            "str": AttrType.STRING,
            "text": AttrType.TEXT,
            "obj": AttrType.OBJECT,
            "name": AttrType.NAMED_OBJECT,
            "bool": AttrType.BOOLEAN,
            "group": AttrType.GROUP,
            "date": AttrType.DATE,
            "role": AttrType.ROLE,
            "datetime": AttrType.DATETIME,
            "num": AttrType.NUMBER,
            "arr_str": AttrType.ARRAY_STRING,
            "arr_num": AttrType.ARRAY_NUMBER,
            "arr_obj": AttrType.ARRAY_OBJECT,
            "arr_name": AttrType.ARRAY_NAMED_OBJECT,
            "arr_group": AttrType.ARRAY_GROUP,
            "arr_role": AttrType.ARRAY_ROLE,
        }
        for attr_name, attr_type in attr_info.items():
            attr = EntityAttr.objects.create(
                name=attr_name, type=attr_type, created_user=user, parent_entity=entity
            )
            if attr_type & AttrType.OBJECT and ref_entity:
                attr.referral.add(ref_entity)
            entity.attrs.add(attr)
        return entity

    def make_attr(
        self,
        name: str,
        attrtype: AttrType = AttrType.STRING,
        user: User | None = None,
        entity: Entity | None = None,
        entry: Entry | None = None,
    ) -> Attribute:
        """Create EntityAttr and Attribute for testing."""
        entity_attr = EntityAttr.objects.create(
            name=name,
            type=attrtype,
            created_user=user or getattr(self, "_user", None),
            parent_entity=entity or getattr(self, "_entity", None),
        )
        return Attribute.objects.create(
            name=name,
            schema=entity_attr,
            created_user=user or getattr(self, "_user", None),
            parent_entry=entry or getattr(self, "_entry", None),
        )

    def _do_login(self, uname, is_superuser=False) -> User:
        # create test user to authenticate
        user = User(username=uname, is_superuser=is_superuser)
        user.set_password(uname)
        user.save()

        self.client.login(username=uname, password=uname)

        return user

    def admin_login(self) -> User:
        return self._do_login("admin", True)

    def guest_login(self, uname="guest") -> User:
        return self._do_login(uname)


class AironeViewTest(AironeTestCase):
    def setUp(self):
        super(AironeViewTest, self).setUp()

        self.client = Client()

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


def with_airone_settings(info={}):
    """
    This update AIRONE.settings parameter duing running test and retrieve it
    after running test.
    """

    def _with_settings(method):
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            # This evacuates original values in settings.AIRONE and set specified one
            evacuation_place = {}
            for k, v in info.items():
                evacuation_place[k] = settings.AIRONE.get(k)
                settings.AIRONE[k] = v

            # Run test case
            method(*args, **kwargs)

            # Revert original configuration that were set in the settings.AIRONE
            for k, v in evacuation_place.items():
                if v:
                    settings.AIRONE[k] = v

        return wrapper

    return _with_settings
