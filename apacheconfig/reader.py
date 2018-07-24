import os


class LocalHostReader(object):

    def __init__(self):
        self._os = os
        self._environ = self._os.environ
        self._path = self._os.path

    @property
    def environ(self):
        return self._environ

    def exists(self, filepath):
        return self._path.exists(filepath)

    def isdir(self, filepath):
        return self._path.isdir(filepath)

    def listdir(self, filepath):
        return self._os.listdir(filepath)

    def open(self, filename, mode='r', bufsize=-1):
        return open(filename, mode, bufsize)
