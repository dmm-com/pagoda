from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from airone.lib.elasticsearch import ESS


@override_settings(
    ES_CONFIG={
        "BACKEND": "http",
        "URL": ["http://localhost:9200"],
        "INDEX_NAME": "airone-test",
        "TIMEOUT": 5,
        "MAXIMUM_RESULTS_NUM": 500000,
        "MAXIMUM_NESTED_OBJECT_NUM": 999999,
    }
)
class ElasticsearchReadAvailabilityTest(SimpleTestCase):
    def test_search_does_not_write_settings_when_master_is_unavailable(self):
        response = {"hits": {"total": {"value": 1}, "hits": []}}
        with ESS() as client:
            client.indices = Mock()
            client.indices.put_settings.side_effect = AssertionError("Master unavailable")
            with patch.object(client, "search", return_value=response):
                for options in ({}, {"size": 10, "offset": 0, "track_total_hits": True}):
                    self.assertEqual(client.search_entries({}, **options), response)
            self.assertEqual(client.indices.mock_calls, [])

    def test_index_creation_configures_search_result_window(self):
        with ESS() as client:
            client.indices = Mock()
            client.recreate_index()
            self.assertEqual(
                client.indices.create.call_args.kwargs["settings"]["index"]["max_result_window"],
                500000,
            )


class ElasticsearchConfigCompatibilityTest(SimpleTestCase):
    def test_explicit_config_supports_production_and_local_nodes(self):
        for urls in (
            ["http://192.0.2.10:9200", "http://192.0.2.11:9200", "http://192.0.2.12:9200"],
            ["http://localhost:9200", "http://localhost:9201", "http://localhost:9202"],
        ):
            config = {
                "URL": urls,
                "INDEX_NAME": "airone-v3-53-0",
                "MAXIMUM_RESULTS_NUM": 500000,
                "MAXIMUM_NESTED_OBJECT_NUM": 999999,
                "TIMEOUT": None,
            }
            with self.subTest(urls=urls), override_settings(ES_CONFIG=config), ESS() as client:
                endpoints = {
                    f"{node.config.scheme}://{node.config.host}:{node.config.port}"
                    for node in client.transport.node_pool.all()
                }
                self.assertEqual(endpoints, set(urls))
                with patch.object(client, "search", return_value={"hits": {"hits": []}}) as search:
                    client.search_entries({})
                self.assertEqual(search.call_args.kwargs["index"], "airone-v3-53-0")
                self.assertEqual(search.call_args.kwargs["size"], 500000)
