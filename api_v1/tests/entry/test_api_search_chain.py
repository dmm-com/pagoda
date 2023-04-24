import copy
import json
from unittest import mock

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue
from api_v1.entry import serializer
from entry.models import Entry
from entry.settings import CONFIG as ENTRY_CONFIG


class APITest(AironeViewTest):
    def tearDown(self):
        super(APITest, self).tearDown()

        # restore originl configuration data and method
        ENTRY_CONFIG.conf = self._orig_entry_config
        Entry.search_entries = self._entry_search_entries

    def setUp(self):
        super(APITest, self).setUp()

        self.user = self.guest_login()

        # dump originl configuration data and emthod
        self._orig_entry_config = copy.copy(ENTRY_CONFIG.conf)
        self._entry_search_entries = Entry.search_entries

        # create Entities that have all referral Attribute types
        self.entity_vlan = self.create_entity(
            self.user,
            "VLAN",
            attrs=[
                {"name": "note", "type": AttrTypeValue["string"]},
            ],
        )
        self.entity_network = self.create_entity(
            self.user,
            "Network",
            attrs=[
                {"name": "vlan", "type": AttrTypeValue["object"], "ref": self.entity_vlan},
            ],
        )
        self.entity_ipv4 = self.create_entity(
            self.user,
            "IPv4 Address",
            attrs=[
                {
                    "name": "network",
                    "type": AttrTypeValue["named_object"],
                    "ref": self.entity_network,
                },
            ],
        )
        self.entity_nic = self.create_entity(
            self.user,
            "NIC",
            attrs=[
                {
                    "name": "IP address",
                    "type": AttrTypeValue["array_object"],
                    "ref": self.entity_ipv4,
                },
            ],
        )
        self.entity_status = self.create_entity(self.user, "Status")
        self.entity_vm = self.create_entity(
            self.user,
            "VM",
            attrs=[
                {
                    "name": "Ports",
                    "type": AttrTypeValue["array_named_object"],
                    "ref": self.entity_nic,
                },
                {"name": "Status", "type": AttrTypeValue["object"], "ref": self.entity_status},
            ],
        )

        # create Entries, that will be used in this test case
        self.entry_vlan1 = self.add_entry(
            self.user,
            "vlan100",
            self.entity_vlan,
            values={
                "note": "test network",
            },
        )
        self.entry_vlan2 = self.add_entry(
            self.user,
            "vlan200",
            self.entity_vlan,
            values={
                "note": "another test network",
            },
        )
        self.entry_network = self.add_entry(
            self.user,
            "10.0.0.0/8",
            self.entity_network,
            values={
                "vlan": self.entry_vlan1,
            },
        )
        self.entry_network2 = self.add_entry(
            self.user,
            "110.0.0.0/8",
            self.entity_network,
            values={
                "vlan": self.entry_vlan1,
            },
        )
        self.entry_ipv4 = self.add_entry(
            self.user,
            "10.0.0.1",
            self.entity_ipv4,
            values={
                "network": {"id": self.entry_network, "name": ""},
            },
        )
        self.entry_ipv4_2 = self.add_entry(
            self.user,
            "110.0.0.1",
            self.entity_ipv4,
            values={
                "network": {"id": self.entry_network2, "name": ""},
            },
        )
        self.entry_nic = self.add_entry(
            self.user,
            "ens0",
            self.entity_nic,
            values={
                "IP address": [self.entry_ipv4],
            },
        )
        self.entry_service_in = self.add_entry(self.user, "Service-In", self.entity_status)
        self.entry_service_out = self.add_entry(self.user, "Service-Out", self.entity_status)
        self.entry_vm1 = self.add_entry(
            self.user,
            "test-vm1",
            self.entity_vm,
            values={
                "Ports": [{"id": self.entry_nic, "name": "ens0"}],
                "Status": self.entry_service_in,
            },
        )
        self.entry_vm2 = self.add_entry(
            self.user,
            "test-vm2",
            self.entity_vm,
            values={
                "Status": self.entry_service_out,
            },
        )

    def test_search_chain_with_full_chained_query(self):
        # create query to search chained query that follows all attribute chain
        params = {
            "entities": ["VM"],
            "attrs": [
                {
                    "name": "Ports",
                    "value": "ens0",
                    "attrs": [
                        {
                            "name": "IP address",
                            "value": "10.0.0.1",
                            "attrs": [
                                {
                                    "name": "network",
                                    "value": "10.0.0.0/8",
                                    "attrs": [
                                        {
                                            "name": "vlan",
                                            "value": "100",
                                            "attrs": [
                                                {
                                                    "name": "note",
                                                    "value": "test",
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted([{"id": x.id, "name": x.name} for x in [self.entry_vm1]], key=lambda x: x["id"]),
        )

    def test_search_chain_with_partial_chained_query(self):
        # create query to search chained query that doesn't have last attr chain
        params = {
            "entities": ["VM"],
            "attrs": [
                {
                    "name": "Ports",
                    "value": "ens0",
                    "attrs": [
                        {
                            "name": "IP address",
                            "value": "10.0.0.1",
                            "attrs": [
                                {
                                    "name": "network",
                                    "value": "10.0.0.0/8",
                                    "attrs": [
                                        {
                                            "name": "vlan",
                                            "value": "100",
                                            # NOTE: This doesn't have attr chain
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                },
                {"name": "Status", "value": "Service-In"},
            ],
        }

        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted([{"id": x.id, "name": x.name} for x in [self.entry_vm1]], key=lambda x: x["id"]),
        )

    def test_search_chain_with_wrong_keyword_value(self):
        # create query to search chained query that has wrong value
        params = {
            "entities": ["VM"],
            "attrs": [
                {
                    "name": "Ports",
                    "value": "ens0",
                    "attrs": [
                        {
                            "name": "IP address",
                            "value": "wrong VALUE",  # This specifies wrong value
                            "attrs": [
                                {
                                    "name": "network",
                                    "value": "10.0.0.0/8",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 0)
        self.assertEqual(resp.json()["ret_values"], [])

    def test_search_chain_using_OR_condition(self):
        # create query to search chained query
        params = {
            "entities": ["VM"],
            "is_any": True,
            "attrs": [
                # This condition will match only test-vm1
                {"name": "Status", "value": "Service-In"},
                # This condition will match only test-vm2
                {"name": "Status", "value": "Service-Out"},
            ],
        }

        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 2)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted(
                [{"id": x.id, "name": x.name} for x in [self.entry_vm1, self.entry_vm2]],
                key=lambda x: x["id"],
            ),
        )

        # case with only one filtering hit
        params = {
            "entities": ["VM"],
            "is_any": True,
            "attrs": [
                # This condition not match entry
                {
                    "name": "Ports",
                    "value": "ens0",
                    "attrs": [
                        {
                            "name": "IP address",
                            "value": "wrong VALUE",  # This specifies wrong value
                        }
                    ],
                },
                # This condition will match only test-vm2
                {"name": "Status", "value": "Service-Out"},
            ],
        }

        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted(
                [{"id": x.id, "name": x.name} for x in [self.entry_vm2]],
                key=lambda x: x["id"],
            ),
        )

    def test_search_chain_using_AND_condition(self):
        # create query to search chained query
        params = {
            "entities": ["VM"],
            "is_any": False,
            "attrs": [
                # This condition will match only test-vm1
                {"name": "Status", "value": "Service-In"},
                # This condition will match only test-vm2
                {"name": "Status", "value": "Service-Out"},
            ],
        }

        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 0)
        self.assertEqual(resp.json()["ret_values"], [])

    def test_search_chain_to_get_entry_that_refers_nothing(self):
        # Prepare NIC Entry that doens't refer any IP address Entries.
        entry_another_nic = self.add_entry(
            self.user,
            "ens1",
            self.entity_nic,
            values={
                "IP address": [],
            },
        )
        entry_another_vm = self.add_entry(
            self.user,
            "test-vm3",
            self.entity_vm,
            values={
                "Ports": [{"id": entry_another_nic, "name": ""}],
            },
        )
        # create query to search chained query
        params = {
            "entities": ["VM"],
            "attrs": [
                {
                    "name": "Ports",
                    "attrs": [{"name": "IP address", "value": ""}],
                },
            ],
        }
        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted(
                [{"id": x.id, "name": x.name} for x in [entry_another_vm]], key=lambda x: x["id"]
            ),
        )

    def test_search_chain_do_not_care_intermediate_entry_name(self):
        """
        There are multiple Entries that refers network (10.0.0.0/8)
        """
        entry_another_ipv4 = self.add_entry(
            self.user,
            "10.0.0.2",
            self.entity_ipv4,
            values={
                "network": {"id": self.entry_network, "name": ""},
            },
        )
        entry_another_nic = self.add_entry(
            self.user,
            "ens1",
            self.entity_nic,
            values={
                "IP address": [entry_another_ipv4],
            },
        )
        entry_another_vm = self.add_entry(
            self.user,
            "test-vm3",
            self.entity_vm,
            values={
                "Ports": [{"id": entry_another_nic, "name": ""}],
            },
        )

        # create query to search chained query that it only cares about
        # termination Entry "10.0.0.0/8".
        params = {
            "entities": ["VM"],
            "attrs": [
                {
                    "name": "Ports",
                    "attrs": [
                        {
                            "name": "IP address",
                            "attrs": [
                                {
                                    "name": "network",
                                    "value": "10.0.0.0/8",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 2)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted(
                [{"id": x.id, "name": x.name} for x in [self.entry_vm1, entry_another_vm]],
                key=lambda x: x["id"],
            ),
        )

    def test_search_chain_with_complex_is_any_condition(self):
        """This test send query that has AND and OR match conditions at different layers."""
        entry_ipaddrs = [
            self.add_entry(
                self.user,
                x,
                self.entity_ipv4,
                values={
                    "network": {"id": self.entry_network, "name": ""},
                },
            )
            for x in ["10.0.100.1", "10.0.100.2"]
        ]
        entry_nic = self.add_entry(
            self.user,
            "ens1",
            self.entity_nic,
            values={
                "IP address": entry_ipaddrs,
            },
        )
        entry_another_vm = self.add_entry(
            self.user,
            "test-another-vm",
            self.entity_vm,
            values={
                "Ports": [{"id": entry_nic, "name": ""}],
            },
        )

        # create query to get Entries that is service-out or
        # that refers 10.0.0.0/8 network when it is service-in.
        params = {
            "entities": ["VM"],
            "is_any": True,
            "attrs": [
                {
                    "name": "Ports",
                    "is_any": False,
                    "attrs": [
                        {
                            "name": "IP address",
                            "value": "10.0.100.1",
                        },
                        {
                            "name": "IP address",
                            "value": "10.0.100.2",
                        },
                    ],
                },
                {"name": "Status", "value": "Service-Out"},
            ],
        }

        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 2)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted(
                [{"id": x.id, "name": x.name} for x in [self.entry_vm2, entry_another_vm]],
                key=lambda x: x["id"],
            ),
        )

    def test_search_chain_when_object_attrvalue_is_empty(self):
        entry_network = self.add_entry(
            self.user,
            "192.168.0.1/8",
            self.entity_network,
            values={
                "vlan": None,
            },
        )
        entry_ipv4 = self.add_entry(
            self.user,
            "192.168.0.100",
            self.entity_ipv4,
            values={
                "network": {"id": entry_network, "name": ""},
            },
        )
        entry_nic = self.add_entry(
            self.user,
            "ens1",
            self.entity_nic,
            values={
                "IP address": [entry_ipv4],
            },
        )
        self.add_entry(
            self.user,
            "test-another-vm",
            self.entity_vm,
            values={
                "Ports": [{"id": entry_nic, "name": "ens1"}],
            },
        )

        # create query to search chained query that follows all attribute chain
        params = {
            "entities": ["VM"],
            "attrs": [
                {
                    "name": "Ports",
                    "attrs": [
                        {
                            "name": "IP address",
                            "attrs": [
                                {
                                    "name": "network",
                                    "attrs": [
                                        {
                                            "name": "vlan",
                                            "attrs": [
                                                {
                                                    "name": "note",
                                                    "value": "test",
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted([{"id": x.id, "name": x.name} for x in [self.entry_vm1]], key=lambda x: x["id"]),
        )

    def test_search_chain_when_named_object_attrvalue_is_empty(self):
        entry_ipv4 = self.add_entry(
            self.user,
            "192.168.0.100",
            self.entity_ipv4,
            values={
                "network": {"id": None, "name": "hoge"},
            },
        )
        entry_nic = self.add_entry(
            self.user,
            "ens1",
            self.entity_nic,
            values={
                "IP address": [entry_ipv4],
            },
        )
        self.add_entry(
            self.user,
            "test-another-vm",
            self.entity_vm,
            values={
                "Ports": [{"id": entry_nic, "name": "ens1"}],
                "Status": self.entry_service_in,
            },
        )

        # create query to search chained query that follows all attribute chain
        params = {
            "entities": ["VM"],
            "attrs": [
                {
                    "name": "Ports",
                    "attrs": [
                        {
                            "name": "IP address",
                            "attrs": [
                                {
                                    "name": "network",
                                    "attrs": [
                                        {
                                            "name": "vlan",
                                            "attrs": [
                                                {
                                                    "name": "note",
                                                    "value": "test",
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted([{"id": x.id, "name": x.name} for x in [self.entry_vm1]], key=lambda x: x["id"]),
        )

    def test_search_chain_when_array_object_attrvalue_is_empty(self):
        entry_nic = self.add_entry(
            self.user,
            "ens1",
            self.entity_nic,
            values={
                "IP address": [],
            },
        )
        self.add_entry(
            self.user,
            "test-another-vm",
            self.entity_vm,
            values={
                "Ports": [{"id": entry_nic, "name": "ens1"}],
                "Status": self.entry_service_in,
            },
        )

        # create query to search chained query that follows all attribute chain
        params = {
            "entities": ["VM"],
            "attrs": [
                {
                    "name": "Ports",
                    "attrs": [
                        {
                            "name": "IP address",
                            "attrs": [
                                {
                                    "name": "network",
                                    "attrs": [
                                        {
                                            "name": "vlan",
                                            "attrs": [
                                                {
                                                    "name": "note",
                                                    "value": "test",
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted([{"id": x.id, "name": x.name} for x in [self.entry_vm1]], key=lambda x: x["id"]),
        )

    def test_search_chain_when_array_named_object_attrvalue_is_empty(self):
        self.add_entry(
            self.user,
            "test-another-vm",
            self.entity_vm,
            values={
                "Ports": [{"id": None, "name": "ens1"}],
                "Status": self.entry_service_in,
            },
        )

        # create query to search chained query that follows all attribute chain
        params = {
            "entities": ["VM"],
            "attrs": [
                {
                    "name": "Ports",
                    "attrs": [
                        {
                            "name": "IP address",
                            "attrs": [
                                {
                                    "name": "network",
                                    "attrs": [
                                        {
                                            "name": "vlan",
                                            "attrs": [
                                                {
                                                    "name": "note",
                                                    "value": "test",
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted([{"id": x.id, "name": x.name} for x in [self.entry_vm1]], key=lambda x: x["id"]),
        )

    def test_complex_entity_structure(self):
        # create Entities that have all referral Attribute types
        entity_ipv6_network = self.create_entity(
            self.user,
            "IPv6 Network",
            attrs=[
                {"name": "vlan", "type": AttrTypeValue["object"], "ref": self.entity_vlan},
            ],
        )
        entity_ipv6_address = self.create_entity(
            self.user,
            "IPv6 Address",
            attrs=[
                {
                    "name": "network",
                    "type": AttrTypeValue["named_object"],
                    "ref": entity_ipv6_network,
                },
            ],
        )
        entity_server = self.create_entity(
            self.user,
            "Server",
            attrs=[
                {
                    "name": "IP addresses",
                    "type": AttrTypeValue["array_object"],
                    "ref": [
                        self.entity_ipv4,
                        entity_ipv6_address,
                    ],
                },
            ],
        )

        # create Entries, that will be used in this test case
        entry_ipv6_network = self.add_entry(
            self.user,
            "2001:0DB8:0:CD30:123:4567:89AB:CDEF/60",
            entity_ipv6_network,
            values={
                "vlan": self.entry_vlan1,
            },
        )
        entry_ipv6_address = self.add_entry(
            self.user,
            "2001:0DB8:0:CD30:123:4567:89AB:CDEF",
            entity_ipv6_address,
            values={
                "network": {"id": entry_ipv6_network, "name": ""},
            },
        )
        entry_server = self.add_entry(
            self.user,
            "srv001",
            entity_server,
            values={
                "IP addresses": [entry_ipv6_address],
            },
        )

        # create query to search chained query that follows all attribute chain
        params = {
            "entities": ["Server"],
            "attrs": [
                {
                    "name": "IP addresses",
                    "attrs": [
                        {
                            "name": "network",
                            "attrs": [
                                {
                                    "name": "vlan",
                                    "attrs": [
                                        {
                                            "name": "note",
                                            "value": "test",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted([{"id": x.id, "name": x.name} for x in [entry_server]], key=lambda x: x["id"]),
        )

    def test_basic_backward_reference(self):
        # create query to search chained query
        params = {
            "entities": ["NIC"],
            "refers": [{"entity": "VM", "entry": "test-vm1"}],
        }

        # check results of backward search Entries
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted([{"id": x.id, "name": x.name} for x in [self.entry_nic]], key=lambda x: x["id"]),
        )

    def test_basic_backward_reference_with_blank_entry(self):
        # create query to search chained query with blank "entry" parameter
        params = {
            "entities": ["NIC"],
            "refers": [{"entity": "VM", "entry": ""}],
        }

        # check results of backward search Entries
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted([{"id": x.id, "name": x.name} for x in [self.entry_nic]], key=lambda x: x["id"]),
        )

    def test_basic_backward_and_forward_reference(self):
        # create query to search chained query
        params = {
            "entities": ["NIC"],
            "refers": [
                {
                    "entity": "VM",
                    "attrs": [
                        {
                            "name": "Status",
                            "value": "Service-In",
                        }
                    ],
                }
            ],
        }

        # check results of backward and forward search Entries
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted([{"id": x.id, "name": x.name} for x in [self.entry_nic]], key=lambda x: x["id"]),
        )

    def test_nested_backward_reference(self):
        self.add_entry(
            self.user,
            "192.168.10.0/24",
            self.entity_network,
            values={
                "vlan": self.entry_vlan2,
            },
        )

        # create query to search chained query
        params = {
            "entities": ["VLAN"],
            "refers": [
                {
                    "entity": "Network",
                    "refers": [
                        {
                            "entity": "IPv4 Address",
                            "entry": "10.0.0.1",
                        }
                    ],
                }
            ],
        }
        # check results of nested backward search Entries
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted(
                [{"id": x.id, "name": x.name} for x in [self.entry_vlan1]], key=lambda x: x["id"]
            ),
        )

    def test_basic_forward_and_backward_reference(self):
        # create query to search chained query
        params = {
            "entities": ["IPv4 Address"],
            "attrs": [
                {
                    "name": "network",
                    "refers": [
                        {
                            "entity": "IPv4 Address",
                            "entry": "^10.0.0.1$",
                        }
                    ],
                }
            ],
        }

        # check results of forward and backward search Entries
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted(
                [{"id": x.id, "name": x.name} for x in [self.entry_ipv4]], key=lambda x: x["id"]
            ),
        )

    def test_specify_both_attrs_and_refers_at_the_same_time_using_OR_condition(self):
        # create Entries that are used for this test
        another_nic = self.add_entry(self.user, "ens1", self.entity_nic, values={})
        another_vm = self.add_entry(
            self.user,
            "test-another-vm",
            self.entity_vm,
            values={
                "Ports": [{"id": another_nic, "name": ""}],
            },
        )

        # create query to search chained query
        params = {
            "entities": ["NIC"],
            "is_any": True,
            "attrs": [{"name": "IP address", "value": self.entry_ipv4.name}],
            "refers": [{"entity": "VM", "entry": another_vm.name}],
        }

        # check results of forward and backward search Entries
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 2)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted(
                [{"id": x.id, "name": x.name} for x in [self.entry_nic, another_nic]],
                key=lambda x: x["id"],
            ),
        )

    def test_specify_both_attrs_and_refers_at_the_same_time_using_AND_condition(self):
        # create another Entry that refers self.entry_ipv4, but this is not referred by anyone
        self.add_entry(
            self.user,
            "ens1",
            self.entity_nic,
            values={
                "IP address": [self.entry_ipv4],
            },
        )

        # create query to search Entry that
        # - refers to Entry (self.entry_ipv4)
        # - referred by Entry (self.entry_vm1)
        params = {
            "entities": ["NIC"],
            "is_any": False,
            "attrs": [{"name": "IP address", "value": self.entry_ipv4.name}],
            "refers": [{"entity": "VM", "entry": self.entry_vm1.name}],
        }

        # check results of forward and backward search Entries
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted([{"id": x.id, "name": x.name} for x in [self.entry_nic]], key=lambda x: x["id"]),
        )

    def test_refers_with_entry_hint_at_intermediate_query(self):
        # This test specify "entry" parameter as hint at intermediate query of "refers" condition
        # to narrow down candidates of intermediate search process.
        entry_nw = self.add_entry(
            self.user,
            "192.168.10.0/24",
            self.entity_network,
            values={
                "vlan": self.entry_vlan2,
            },
        )
        entry_ipaddr = self.add_entry(
            self.user,
            "192.168.10.10",
            self.entity_ipv4,
            values={
                "network": {"id": entry_nw, "name": ""},
            },
        )
        entry_nic = self.add_entry(
            self.user,
            "ens0",
            self.entity_nic,
            values={
                "IP address": [entry_ipaddr],
            },
        )
        self.add_entry(
            self.user,
            "vm1000",
            self.entity_vm,
            values={
                "Ports": [{"id": entry_nic, "name": "ens0"}],
                "Status": self.entry_service_in,
            },
        )

        # Send a search_chain request without any intermediate "entry" hint,
        # then it's expected to return all Network Entries that are associated with
        # Service-IN VM
        resp = self.client.post(
            "/api/v1/entry/search_chain",
            json.dumps(
                {
                    "entities": [self.entity_network.name],
                    "refers": [
                        {
                            "entity": self.entity_ipv4.name,
                            "refers": [
                                {
                                    "entity": self.entity_nic.name,
                                    "refers": [
                                        {
                                            "entity": self.entity_vm.name,
                                            "attrs": [
                                                {
                                                    "name": "Status",
                                                    "value": self.entry_service_in.name,
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 2)
        self.assertEqual(
            sorted([x["entry"]["name"] for x in resp.json()["ret_values"]]),
            sorted(["10.0.0.0/8", "192.168.10.0/24"]),
        )

        # Send a search_chain request with "entry" parameter at intermediate query,
        # then it's expected to return Network Entry that isassociated with
        # Service-IN VM and IP address has "192.168.xxx.xxx".
        resp = self.client.post(
            "/api/v1/entry/search_chain",
            json.dumps(
                {
                    "entities": [self.entity_network.name],
                    "refers": [
                        {
                            "entity": self.entity_ipv4.name,
                            "entry": "192.168.",  # This is the point of this test
                            "refers": [
                                {
                                    "entity": self.entity_nic.name,
                                    "refers": [
                                        {
                                            "entity": self.entity_vm.name,
                                            "attrs": [
                                                {
                                                    "name": "Status",
                                                    "value": self.entry_service_in.name,
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            [x["entry"]["name"] for x in resp.json()["ret_values"]], ["192.168.10.0/24"]
        )
        self.assertEqual(resp.status_code, 200)

    def test_search_chain_with_empty_conditions(self):
        # create query to search chained query
        params = {
            "entities": ["VM"],
            "attrs": [],
            "refers": [],
        }

        # This checks to get Entries that meets chaining conditions
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 0)
        self.assertEqual(resp.json()["ret_values"], [])

    def test_search_forward_chain_exceeding_search_limit(self):
        # check the case that the number of Entries of Entry.search_results() exceeds
        # expected limit.
        serializer.SEARCH_ENTRY_LIMIT = 2

        # create number of Entries exceeding SEARCH_ENTRY_LIMIT
        another_ipaddrs = [
            self.add_entry(
                self.user,
                "10.0.10.%d" % i,
                self.entity_ipv4,
                values={
                    "network": {"id": self.entry_network, "name": ""},
                },
            )
            for i in range(1, 5)
        ]
        another_nic = self.add_entry(
            self.user,
            "ensX",
            self.entity_nic,
            values={
                "IP address": another_ipaddrs,
            },
        )
        another_vm = self.add_entry(
            self.user,
            "test-another-vm",
            self.entity_vm,
            values={
                "Ports": [{"id": another_nic, "name": "ens-X"}],
            },
        )

        # create query to search above Entries
        params = {
            "entities": [self.entity_vm.name],
            "attrs": [
                {
                    "name": "Ports",
                    "attrs": [
                        {
                            "name": "IP address",
                            "attrs": [{"name": "network", "value": self.entry_network.name}],
                        }
                    ],
                }
            ],
        }

        # check results of forward and backward search Entries
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 2)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted(
                [{"id": x.id, "name": x.name} for x in [self.entry_vm1, another_vm]],
                key=lambda x: x["id"],
            ),
        )

    def test_search_backward_chain_exceeding_search_limit(self):
        # check the case that the number of Entries of Entry.search_results() exceeds
        # expected limit.
        serializer.SEARCH_ENTRY_LIMIT = 2

        # create number of Entries exceeding SEARCH_ENTRY_LIMIT
        another_ipaddrs = [
            self.add_entry(
                self.user,
                "10.0.10.%d" % i,
                self.entity_ipv4,
                values={
                    "network": {"id": self.entry_network, "name": ""},
                },
            )
            for i in range(1, 5)
        ]
        self.add_entry(
            self.user,
            "ensX",
            self.entity_nic,
            values={
                "IP address": another_ipaddrs,
            },
        )

        # create query to search above Entries
        params = {
            "entities": ["Network"],
            "refers": [{"entity": "IPv4 Address", "refers": [{"entity": "NIC", "entry": "ens"}]}],
        }
        # check results of forward and backward search Entries
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ret_count"], 1)
        self.assertEqual(
            sorted([x["entry"] for x in resp.json()["ret_values"]], key=lambda x: x["id"]),
            sorted(
                [{"id": x.id, "name": x.name} for x in [self.entry_network]], key=lambda x: x["id"]
            ),
        )

    def test_search_chain_when_result_exceeds_acceptable_count(self):
        # Change configuration to test processing for acceptable result from elasticsearch
        ENTRY_CONFIG.conf["SEARCH_CHAIN_ACCEPTABLE_RESULT_COUNT"] = 2

        # Create Entries that exceeds above changing configuration
        [
            self.add_entry(
                self.user,
                "test-%s" % x,
                self.entity_vm,
                values={
                    "Status": self.entry_service_in,
                },
            )
            for x in range(2)
        ]

        # create query to search chained query
        params = {"entities": ["VM"], "attrs": [{"name": "Status", "value": "Service-In"}]}

        # check results of backward and forward search Entries
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"reason": "Data overflow was happened. Please narrow down intermediate conditions"},
        )

    # @mock.patch('entry.models.Entry')
    def test_search_chain_when_elasticsearch_raise_an_exception(self):
        def side_effect(*args, **kwargs):
            raise RuntimeError("Dummy Exception of Elasticsearch")

        mock_method = mock.Mock(side_effect=side_effect)
        Entry.search_entries = mock_method

        # create query to search chained query
        params = {"entities": ["VM"], "attrs": [{"name": "Status", "value": "Service-In"}]}

        # check results of backward and forward search Entries
        resp = self.client.post(
            "/api/v1/entry/search_chain", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(),
            {"reason": "Data overflow was happened. Please narrow down intermediate conditions"},
        )
