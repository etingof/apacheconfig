#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import sys

from apacheconfig import *

try:
    import unittest2 as unittest

except ImportError:
    import unittest


class LoaderTestCase(unittest.TestCase):

    def testWholeConfig(self):
        text = """\

# a
a = b

<a block>
  a = b
</a>
a b
<a a block>
c "d d"
</a>
# a
"""
        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()))

        config = loader.loads(text)

        self.assertEqual(config, {'a': 'b',
                                  'a a block': {
                                      'c': 'd d'
                                  },
                                  'a block': {
                                      'a': 'b'
                                  }})


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
