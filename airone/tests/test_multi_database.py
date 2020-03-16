from airone.lib.test import AironeTestCase
from user.models import User


class AirOneMuiltiDatabaseTest(AironeTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_use_master(self):
        self.assertTrue(True)

    def test_use_slaves(self):
        self.assertTrue(True)
