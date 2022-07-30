from airone.lib.test import AironeViewTest
from group.models import Group
from user.models import User


class APITest(AironeViewTest):
    # helper methods to craete User and Group
    def _create_user(self, name):
        return User.objects.create(username=name)

    def _create_group(self, name, parent=None):
        return Group.objects.create(name=name, parent_group=parent)

    def test_get_group_tree(self):
        """This test create User (user1) who belongs following hierarchical groups
        * group0
            ├──group1
            |    └──group3
            |
            └──group2
                 └──group4
        """
        self.guest_login()

        group0 = self._create_group("group0")
        group1 = self._create_group("group1", group0)
        group2 = self._create_group("group2", group0)
        group3 = self._create_group("group3", group1)
        group4 = self._create_group("group4", group2)

        resp = self.client.get("/group/api/v1/tree")
        self.assertEqual(
            resp.json(),
            [
                {
                    "id": group0.id,
                    "name": group0.name,
                    "children": [
                        {
                            "id": group1.id,
                            "name": group1.name,
                            "children": [{"id": group3.id, "name": group3.name, "children": []}],
                        },
                        {
                            "id": group2.id,
                            "name": group2.name,
                            "children": [{"id": group4.id, "name": group4.name, "children": []}],
                        },
                    ],
                }
            ],
        )
