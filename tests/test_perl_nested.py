#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import sys
import os

from apacheconfig.lexer import ApacheConfigLexer
from apacheconfig.parser import ApacheConfigParser

try:
    import unittest2 as unittest

except ImportError:
    import unittest


class PerlNestedBlocksTestCase(unittest.TestCase):
    def testParseFile(self):
        sample = os.path.join(
            os.path.dirname(__file__),
            'samples', 'perl-config-general', 'nested-block-test.conf'
        )

        parser = ApacheConfigParser(ApacheConfigLexer())
        with open(sample) as f:
            ast = parser.parse(f.read())

        self.assertEqual(ast, [[('comment', ' Nested block test')],
                               ('block', 'cops',
                                    [('option', 'name', 'stein'),
                                     ('option', 'age', '25'),
                                     ('option', 'color', '\\#000000')],
                                'cops')])


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
