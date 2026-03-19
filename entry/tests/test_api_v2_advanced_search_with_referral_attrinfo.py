import json
from unicodedata import name

from airone.lib.elasticsearch import FilterKey
from airone.lib.types import AttrType
from entry.tests.test_api_v2 import BaseViewTest


class ViewTest(BaseViewTest):
    def setUp(self):
        super().setUp()

        # Create an entity for IP addresses as search targets
        self.ip_address_entity = self.create_entity(self.user, "IPAddress", attrs=[])

        # Create IP address entries
        self.ip_addresses = [
            self.add_entry(self.user, ip, self.ip_address_entity)
            for ip in ["192.168.0.1", "192.168.0.2", "192.168.0.3"]
        ]

        # Create referrer entities: Server and VM
        # Both have "status" and "ip_address" attrs, referencing the IPAddress entity
        self.server_entity = self.create_entity(
            self.user,
            "Server",
            attrs=[
                {"name": "status", "type": AttrType.STRING},
                {"name": "ip_address", "type": AttrType.OBJECT, "ref": self.ip_address_entity},
            ],
        )
        self.vm_entity = self.create_entity(
            self.user,
            "VM",
            attrs=[
                {"name": "status", "type": AttrType.STRING},
                {"name": "ip_address", "type": AttrType.OBJECT, "ref": self.ip_address_entity},
            ],
        )

        # Server entries:
        # Server-1: status="active",   ip_address -> 192.168.0.1
        # Server-2: status="inactive", ip_address -> 192.168.0.1
        self.servers = [
            self.add_entry(
                self.user,
                name,
                self.server_entity,
                values={"status": status, "ip_address": ip},
            )
        for name, status, ip in [
            ("Server-1", "active", self.ip_addresses[0].id),
            ("Server-2", "inactive", self.ip_addresses[0].id),
        ]
            
        ]

        # VM entries:
        # VM-1: status="active", ip_address -> 192.168.0.2
        # VM-2: status="",       ip_address -> 192.168.0.3 (no status)
        self.vms = [
            self.add_entry(
                self.user,
                name,
                self.vm_entity,
                values={"status": status, "ip_address": ip},
            )
        for name, status, ip in [
            ("VM-1", "active", self.ip_addresses[1].id),
            ("VM-2", "", self.ip_addresses[2].id),
        ]
            
        ]

    def test_filter_by_referral_attrinfo_with_keyword(self):
        # Only IP addresses referenced by active Servers or VMs should be returned
        params = {
            "entities": [self.ip_address_entity.id],
            "attrinfo": [],
            "referral_attrinfo": [{"name": "status", "keyword": "active"}],
        }
        resp = self.client.post(
            "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        resp_data = resp.json()

        self.assertEqual(resp_data["count"], 2)
        self.assertEqual(resp_data["total_count"], 2)

        result_names = [x["entry"]["name"] for x in resp_data["values"]]
        self.assertIn("192.168.0.1", result_names)
        self.assertIn("192.168.0.2", result_names)
        self.assertNotIn("192.168.0.3", result_names)

        self.assertEqual(resp_data["values"][0]["referrals"], [{
            "id": self.servers[0].id,
            "name": self.servers[0].name,
            "schema": {
                "id": self.server_entity.id,
                "name": self.server_entity.name,
            },
            "attrs": {
                "status": {
                    "type": AttrType.STRING,
                    "value": {
                        "as_string": "active",
                    },
                    "is_readable": True,
                },
            },
        }])

    def test_filter_by_referral_attrinfo_filter_key_empty(self):
        # Only IP addresses referenced by Servers/VMs with empty status should be returned
        params = {
            "entities": [self.ip_address_entity.id],
            "attrinfo": [],
            "referral_attrinfo": [{"name": "status", "filter_key": FilterKey.EMPTY}],
        }
        resp = self.client.post(
            "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        result_names = [x["entry"]["name"] for x in resp.json()["values"]]
        self.assertEqual(result_names, ["192.168.0.3"])

    def test_filter_by_referral_attrinfo_filter_key_non_empty(self):
        # Only IP addresses referenced by Servers/VMs with non-empty status should be returned
        params = {
            "entities": [self.ip_address_entity.id],
            "attrinfo": [],
            "referral_attrinfo": [{"name": "status", "filter_key": FilterKey.NON_EMPTY}],
        }
        resp = self.client.post(
            "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        result_names = [x["entry"]["name"] for x in resp.json()["values"]]
        self.assertIn("192.168.0.1", result_names)
        self.assertIn("192.168.0.2", result_names)
        self.assertNotIn("192.168.0.3", result_names)
