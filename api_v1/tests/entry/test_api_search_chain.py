import json

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue


class APITest(AironeViewTest):
    def setUp(self):
        super(APITest, self).setUp()

        self.user = self.guest_login()

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
        self.entry_ipv4 = self.add_entry(
            self.user,
            "10.0.0.1",
            self.entity_ipv4,
            values={
                "network": {"id": self.entry_network, "name": ""},
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
        print("[onix-test] %s" % str(resp.json()["ret_values"]))
        self.assertEqual(
            [(k, v["value"]) for (k, v) in resp.json()["ret_values"][0]["attrs"].items()],
            [
                ("Ports", [{"ens0": {"id": self.entry_nic.id, "name": self.entry_nic.name}}]),
                ("Status", {"id": self.entry_service_in.id, "name": self.entry_service_in.name}),
            ],
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
        entry_network1 = self.add_entry(
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
                            "entry": "10.0.0.1",
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
