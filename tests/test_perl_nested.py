#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE
#
import sys
import os

from apacheconfig.parser import Parser

try:
    import unittest2 as unittest

except ImportError:
    import unittest


class PerlNestedBlocksTestCase(unittest.TestCase):
    def skip_testParseFile(self):
        sample = os.path.join(
            os.path.dirname(__file__),
            'samples', 'perl-config-general', 'nested-block-test.conf'
        )

        parser = Parser()
        config = parser.parse_file(sample)

        self.assertTrue(config)


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
