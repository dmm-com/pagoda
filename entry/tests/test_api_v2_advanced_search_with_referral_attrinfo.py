import json

from airone.lib.elasticsearch import FilterKey
from airone.lib.types import AttrType
from entry.tests.test_api_v2 import BaseViewTest


class ViewTest(BaseViewTest):
    def setUp(self):
        super().setUp()

        # TargetItem-0, 1, 2 を ref_model に作成（検索対象）
        self.target_items = [
            self.add_entry(self.user, "TargetItem-%d" % i, self.ref_entity)
            for i in range(3)
        ]

        # 参照する側のモデルを複数用意する（実際と同じく複数モデルから参照される状況）
        self.model_a = self.create_entity(
            self.user,
            "ModelA",
            attrs=[
                {"name": "val", "type": AttrType.STRING},
                {"name": "ref", "type": AttrType.OBJECT, "ref": self.ref_entity},
            ],
        )
        self.model_b = self.create_entity(
            self.user,
            "ModelB",
            attrs=[
                {"name": "val", "type": AttrType.STRING},
                {"name": "ref", "type": AttrType.OBJECT, "ref": self.ref_entity},
            ],
        )

        # ModelA の Item が TargetItem を参照
        # ModelA-Item-0: val="active",   ref -> TargetItem-0
        # ModelA-Item-1: val="inactive", ref -> TargetItem-0
        for i, (val, ref_id) in enumerate(
            [
                ("active", self.target_items[0].id),
                ("inactive", self.target_items[0].id),
            ]
        ):
            self.add_entry(
                self.user,
                "ModelA-Item-%d" % i,
                self.model_a,
                values={"val": val, "ref": ref_id},
            )

        # ModelB の Item が TargetItem を参照
        # ModelB-Item-0: val="active", ref -> TargetItem-1
        # ModelB-Item-1: val="",       ref -> TargetItem-2 (空値)
        for i, (val, ref_id) in enumerate(
            [
                ("active", self.target_items[1].id),
                ("", self.target_items[2].id),
            ]
        ):
            self.add_entry(
                self.user,
                "ModelB-Item-%d" % i,
                self.model_b,
                values={"val": val, "ref": ref_id},
            )

    def test_filter_by_referral_attrinfo_with_keyword(self):
        # "active" を持つ参照アイテムから参照されているアイテムのみ返る
        params = {
            "entities": [self.ref_entity.id],
            "attrinfo": [],
            "referral_attrinfo": [{"name": "val", "keyword": "active"}],
        }
        resp = self.client.post(
            "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        result_names = [x["entry"]["name"] for x in resp.json()["values"]]
        self.assertIn("TargetItem-0", result_names)
        self.assertIn("TargetItem-1", result_names)
        self.assertNotIn("TargetItem-2", result_names)

    def test_filter_by_referral_attrinfo_filter_key_empty(self):
        # val が空の参照アイテムから参照されているアイテムのみ返る
        params = {
            "entities": [self.ref_entity.id],
            "attrinfo": [],
            "referral_attrinfo": [{"name": "val", "filter_key": FilterKey.EMPTY}],
        }
        resp = self.client.post(
            "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        result_names = [x["entry"]["name"] for x in resp.json()["values"]]
        self.assertEqual(result_names, ["TargetItem-2"])

    def test_filter_by_referral_attrinfo_filter_key_non_empty(self):
        # val が非空の参照アイテムから参照されているアイテムのみ返る
        params = {
            "entities": [self.ref_entity.id],
            "attrinfo": [],
            "referral_attrinfo": [{"name": "val", "filter_key": FilterKey.NON_EMPTY}],
        }
        resp = self.client.post(
            "/entry/api/v2/advanced_search/", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        result_names = [x["entry"]["name"] for x in resp.json()["values"]]
        self.assertIn("TargetItem-0", result_names)
        self.assertIn("TargetItem-1", result_names)
        self.assertNotIn("TargetItem-2", result_names)
