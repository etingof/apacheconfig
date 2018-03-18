#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import sys

from apacheconfig.lexer import ApacheConfigLexer
from apacheconfig.parser import ApacheConfigParser

try:
    import unittest2 as unittest

except ImportError:
    import unittest


class ParserTestCase(unittest.TestCase):

    def testOptionAndValue(self):
        parser = ApacheConfigParser(ApacheConfigLexer(), start='statement')

        ast = parser.parse('a b\n')
        self.assertEqual(ast, ['statement', 'a', 'b'])

        ast = parser.parse('a=b\n')
        self.assertEqual(ast, ['statement', 'a', 'b'])

        ast = parser.parse('a "b c"\n')
        self.assertEqual(ast, ['statement', 'a', 'b c'])

    def testOptionAndValueSet(self):
        text = """\
a b
a = b
a    b
a= b
a =b
a   b
a "b"
a = "b"
"""
        parser = ApacheConfigParser(ApacheConfigLexer(), start='statements')

        ast = parser.parse(text)
        self.assertEqual(ast, ['statements',
                               ['statement', 'a', 'b'],
                               ['statement', 'a', 'b'],
                               ['statement', 'a', 'b'],
                               ['statement', 'a', 'b'],
                               ['statement', 'a', 'b'],
                               ['statement', 'a', 'b'],
                               ['statement', 'a', 'b'],
                               ['statement', 'a', 'b']])

    def testCommentsAndOptions(self):
        text = """\
#
# a
#a
a = "b b"
# a b
a = "b b"
"""
        parser = ApacheConfigParser(ApacheConfigLexer(), start='statements')

        ast = parser.parse(text)
        self.assertEqual(ast, ['statements',
                               ['comment', ''],
                               ['comment', ' a'],
                               ['comment', 'a'],
                               ['statement', 'a', 'b b'],
                               ['comment', ' a b'],
                               ['statement', 'a', 'b b']])

    def testBlockWithOptions(self):
        text = """\
<a>
  #a
  a = "b b"
  # a b
  a = "b b"
</a>
"""
        parser = ApacheConfigParser(ApacheConfigLexer(), start='block')

        ast = parser.parse(text)
        self.assertEqual(ast, ['block', 'a',
                               ['statements', ['comment', 'a'],
                                ['statement', 'a', 'b b'], ['comment', ' a b'],
                                ['statement', 'a', 'b b']], 'a'])

    def testWholeConfig(self):
        text = """\
# a
a = b

<a>
  a = b
</a>
a b
<a a>
a b
</a a>
# a
"""
        parser = ApacheConfigParser(ApacheConfigLexer(), start='config')

        ast = parser.parse(text)
        self.assertEqual(ast, ['config',
                               ['statements', ['comment', ' a'],
                                ['statement', 'a', 'b']],
                                ['block', 'a',
                                 ['statements',
                                  ['statement', 'a', 'b']], 'a'],
                                ['statements',
                                 ['statement', 'a', 'b']],
                               ['block', 'a a',
                                ['statements',
                                 ['statement', 'a', 'b']], 'a a'],
                               ['statements', ['comment', ' a']]])


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
