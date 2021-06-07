import unittest

from airone.lib.db import get_slave_db
from django.conf import settings


class AirOneDBTest(unittest.TestCase):

    def setUp(self):
        # this saves original configurations to be able to retrieve them
        self.orig_conf_db_slaves = settings.AIRONE['DB_SLAVES']

        # this enables do profiling
        settings.AIRONE['DB_SLAVES'] = ['slave1', 'slave2']

    def tearDown(self):
        # this retrieves original configurations
        settings.AIRONE['ENABLE_PROFILE'] = self.orig_conf_db_slaves

    def test_get_slave_db(self):
        self.assertIn(get_slave_db(), settings.AIRONE['DB_SLAVES'])
