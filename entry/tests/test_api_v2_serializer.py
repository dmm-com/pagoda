from airone.lib.acl import ACLType
from airone.lib.http import DRFRequest
from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from entry.api_v2.serializers import (
    PrivilegedEntryCreateSerializer,
    PrivilegedEntryUpdateSerializer,
)
from user.models import User


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        user: User = User.objects.create(username="userA")

        # create Entity that has "secret" Attribute user couldn't update
        self.schema = self.create_entity(
            user,
            "Entity",
            attrs=[
                {"name": "secret", "type": AttrType.STRING},
            ],
        )
        attr = self.schema.attrs.last()
        attr.is_public = False
        attr.default_permission = ACLType.Nothing.id
        attr.save()

    def test_create_entry_without_permission_leagally(self):
        login_user: User = self.guest_login()

        # create Entry using Serializer by user who doesn't have permission to
        # update "secret" Attribute.
        setting_data = {
            "schema": self.schema,
            "name": "Entry0",
            "attrs": [
                {
                    "id": self.schema.attrs.get(name="secret").id,
                    "value": "caput draconis",
                }
            ],
            "created_user": login_user,
        }
        serializer = PrivilegedEntryCreateSerializer(
            data=setting_data, context={"request": DRFRequest(login_user)}
        )
        self.assertIsNotNone(serializer)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()

        # check created Entry has proper Attribute value
        self.assertEqual(entry.name, "Entry0")
        self.assertEqual(entry.get_attrv("secret").value, "caput draconis")

    def test_update_entry_without_permission_leagally(self):
        # create Entry to update in this test
        another_user: User = User.objects.create(username="userB")
        entry = self.add_entry(another_user, "e0", self.schema)

        login_user: User = self.guest_login()

        # update Entry using Serializer by user who doesn't have permission to
        # update "secret" Attribute.
        setting_data = {
            "id": entry.id,
            "name": "e0 changed",
            "attrs": [
                {
                    "id": self.schema.attrs.get(name="secret").id,
                    "value": "caput draconis",
                }
            ],
        }
        serializer = PrivilegedEntryUpdateSerializer(
            instance=entry, data=setting_data, context={"request": DRFRequest(login_user)}
        )

        self.assertIsNotNone(serializer)
        serializer.is_valid(raise_exception=True)
        changed_entry = serializer.save()

        # check created Entry has proper Attribute value
        self.assertEqual(changed_entry.name, "e0 changed")
        self.assertEqual(changed_entry.get_attrv("secret").value, "caput draconis")
