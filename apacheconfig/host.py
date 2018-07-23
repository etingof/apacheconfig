import os


class LocalHost(object):

    def __init__(self):
        self._environ = os.environ
        self._path = os.path

    @property
    def environ(self):
        return self._environ

    @property
    def path(self):
        return self._path

    def listdir(self, filepath):
        return os.listdir(filepath)

    def open(self, filename, mode='r', bufsize=-1):
        return open(filename, mode, bufsize)
