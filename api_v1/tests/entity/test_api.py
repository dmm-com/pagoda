from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr


class APITest(AironeViewTest):
    def setUp(self):
        super(APITest, self).setUp()
        user = self.admin_login()
        entity_info = {
            "test_entity1": ["foo", "bar", "fuga"],
            "test_entity2": ["bar", "hoge", "fuga"],
        }
        for entity_name, attrnames in entity_info.items():
            entity = Entity.objects.create(name=entity_name, created_user=user)

            for attrname in attrnames:
                entity.attrs.add(
                    EntityAttr.objects.create(
                        name=attrname,
                        type=AttrType.STRING,
                        created_user=user,
                        parent_entity=entity,
                    )
                )

    def test_get_entity_attrs_with_invalid_entity_id(self):
        resp = self.client.get("/api/v1/entity/attrs/9999")
        self.assertEqual(resp.status_code, 400)

    def test_get_all_entity_attrs(self):
        resp = self.client.get("/api/v1/entity/attrs/,")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["result"], sorted(["foo", "bar", "hoge", "fuga"]))

    def test_get_partial_entity_attrs(self):
        entities = Entity.objects.filter(name__contains="test_entity")
        resp = self.client.get("/api/v1/entity/attrs/%s" % ",".join([str(x.id) for x in entities]))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["result"], sorted(["bar", "fuga"]))
