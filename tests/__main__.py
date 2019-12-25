#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
try:
    import unittest2 as unittest

except ImportError:
    import unittest

suite = unittest.TestLoader().loadTestsFromNames(
    ['tests.integration.__main__.suite',
     'tests.unit.__main__.suite']
)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    exit(not result.wasSuccessful())
