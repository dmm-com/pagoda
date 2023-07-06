class Settings(object):
    def __init__(self, conf={}):
        self.conf = conf

    def __getattr__(self, key):
        return self.conf[key]

    def __contains__(self, key):
        return key in self.conf

    def values(self):
        return self.conf.values()
