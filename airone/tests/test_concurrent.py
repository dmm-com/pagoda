from airone.lib.concurrent import ConcurrentExec
from airone.lib.test import AironeTestCase


class ModelTest(AironeTestCase):
    def test_concurrent_processing(self):
        data = range(10)

        ce = ConcurrentExec()

        def worker(ret_dict, lock, data):
            ret_dict[data] = data + 1

        ret = ce.run(data, worker)
        self.assertEqual(sum(ret.keys()), sum(data))
        self.assertEqual(sum(ret.values()), sum([x + 1 for x in data]))
