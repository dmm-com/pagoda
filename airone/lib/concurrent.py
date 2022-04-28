import multiprocessing

from django.conf import settings
from django.db import connections


class ConcurrentExec(object):
    MPM = multiprocessing.Manager()
    DEFAULT_CONCURRENCY = 1

    def __init__(self, concurrency=None):
        self.concurrency = concurrency

        if not concurrency:
            if "CONCURRENCY" in settings.AIRONE and settings.AIRONE["CONCURRENCY"]:
                self.concurrency = settings.AIRONE["CONCURRENCY"]
            else:
                self.concurrency = self.DEFAULT_CONCURRENCY

    def run(self, data_all, worker, **kwargs):
        jobs = []
        ret_container = {}
        lock = multiprocessing.Lock()
        ccount = 0

        # write new-linke
        for data in data_all:
            proc_info = {"process": None, "ret": self.MPM.dict()}

            while len(jobs) >= self.concurrency:
                for pinfo in jobs:
                    if not pinfo["process"].is_alive():
                        jobs.remove(pinfo)
                        ret_container = dict(ret_container)
                        ret_container.update(pinfo["ret"])
                        ccount += 1

            # reset db connection
            connections.close_all()

            if isinstance(data, tuple):
                args = (proc_info["ret"], lock) + data
            else:
                args = (proc_info["ret"], lock, data)

            proc_info["process"] = multiprocessing.Process(target=worker, args=args, kwargs=kwargs)
            proc_info["process"].start()
            jobs.append(proc_info)

        for pinfo in jobs:
            pinfo["process"].join()
            ret_container = dict(ret_container)
            ret_container.update(pinfo["ret"])
            ccount += 1

        return ret_container
