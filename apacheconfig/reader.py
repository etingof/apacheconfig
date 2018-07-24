import os
import io


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


class TestInfraHostReader(object):
    """TestInfraHostReader for ApacheConfigLoader"""

    def __init__(self, host):
        self._host = host
        self._env = host.env()

    @property
    def env(self):
        return self._env

    def exists(self, filepath):
        return self._host.run_test("test -f %s", filepath).rc == 0

    def isdir(self, filepath):
        return self._host.run_test("test -d %s" % filepath).rc == 0

    def listdir(self, filepath):
        out = self._host.run_test("ls -A %s" % filepath)
        if out.rc != 0:
            raise OSError
        else:
            return out.stdout.split()

    def open(self, filepath):
        out = self.run_test("cat -- %s", filepath)
        if out.rc != 0:
            raise IOError
        return io.StringIO(out.stdout)
