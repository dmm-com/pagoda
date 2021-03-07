import unittest

from airone.lib import elasticsearch


class ElasticSearchTest(unittest.TestCase):

    def test_get_regex_pattern(self):
        pattern = elasticsearch._get_regex_pattern('keyword')
        self.assertEqual(pattern, '.*[kK][eE][yY][wW][oO][rR][dD].*')

        # Empty
        pattern = elasticsearch._get_regex_pattern('')
        self.assertEqual(pattern, '.*.*')

        # A keyword with meta characters should be escaped
        pattern = elasticsearch._get_regex_pattern('key...word')
        self.assertEqual(pattern, '.*[kK][eE][yY]\\.\\.\\.[wW][oO][rR][dD].*')

        # A keyword with meta characters with '^' and/or '$'
        pattern = elasticsearch._get_regex_pattern('^keyword')
        self.assertEqual(pattern, '^[kK][eE][yY][wW][oO][rR][dD].*')
        pattern = elasticsearch._get_regex_pattern('keyword$')
        self.assertEqual(pattern, '.*[kK][eE][yY][wW][oO][rR][dD]$')
        pattern = elasticsearch._get_regex_pattern('^keyword$')
        self.assertEqual(pattern, '^[kK][eE][yY][wW][oO][rR][dD]$')
