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


class LexerTestCase(unittest.TestCase):
    def setUp(self):
        ApacheConfigLexer = make_lexer()
        self.lexer = ApacheConfigLexer()

    def test_whitespace(self):
        tokens = self.lexer.tokenize('   \t\t  \t \r  \n\n')
        self.assertFalse(tokens)

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
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, [('a', 'b'), ('a', 'b'), ('a', 'b'),
                                  ('a', 'b'), ('a', 'b'), ('a', 'b'),
                                  ('a', 'b'), ('a', 'b')])

    def testLiteralTags(self):
        text = """\
<a>
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['a', 'a'])

    def testExpressionTags(self):
        text = """\
    <if a == 1>
    </if>
    """
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['if a == 1', 'if'])

    def testComments(self):
        text = """\
#
# a
#a
# a b
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['', ' a', 'a', ' a b'])

    def testBlockOptionsAndValues(self):
        text = """\
<a>
a b
a=b
a =  b
a = "b"
a "b"
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['a', ('a', 'b'), ('a', 'b'), ('a', 'b'), ('a', 'b'), ('a', 'b'), 'a'])

    def testBlockComments(self):
        text = """\
<a>
#
# a
# a b
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['a', '', ' a', ' a b', 'a'])

    def testBlockBlankLines(self):
        text = """\
<a>


</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['a', 'a'])

    def testIncludesConfigGeneral(self):
        text = """\
<<include first.conf>>
<a>
<<include second.conf>>
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['first.conf', 'a', 'second.conf', 'a'])

    def testIncludesApache(self):
        text = """\
include first.conf
<a>
include second.conf
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['first.conf', 'a', 'second.conf', 'a'])

    def testConfiguration(self):
        text = """\
# h
a = b
<a>
  a b
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, [' h', ('a', 'b'), 'a', ('a', 'b'), 'a'])


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
