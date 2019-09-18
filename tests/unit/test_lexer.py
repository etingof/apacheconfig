#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
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
        space = '   \t\t  \t \r  \n\n'
        tokens = self.lexer.tokenize(space)
        self.assertEqual(tokens, [space])

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
        self.assertEqual(tokens, [('a', ' ',  'b'), '\n', ('a', ' = ', 'b'), '\n', ('a','    ', 'b'), '\n',
                                  ('a', '= ', 'b'), '\n', ('a',' =', 'b'),'\n', ('a','   ', 'b'),'\n',
                                  ('a', ' ', 'b'), '\n', ('a', ' = ','b'), '\n'])

    def testLiteralTags(self):
        text = """\
<a>
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['a', '\n', 'a', '\n'])

    def testExpressionTags(self):
        text = """\
    <if a == 1>
    </if>
    """
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['    ', 'if a == 1', '\n    ', 'if', '\n    '])

    def testComments(self):
        text = """\
#
# a
#a
# a b
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['#', '\n', '# a', '\n', '#a', '\n', '# a b', '\n'])

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
        self.assertEqual(tokens, ['a', '\n', ('a', ' ', 'b'), '\n', ('a', '=', 'b'), '\n', ('a', ' =  ', 'b'), '\n', ('a', ' = ', 'b'), '\n', ('a',' ', 'b'), '\n', 'a', '\n'])

    def testBlockComments(self):
        text = """\
<a>
#
# a
# a b
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['a', '\n', '#', '\n', '# a', '\n', '# a b', '\n', 'a', '\n'])

    def testBlockBlankLines(self):
        text = """\
<a>


</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['a', '\n\n\n', 'a', '\n'])

    def testIncludesConfigGeneral(self):
        text = """\
<<include first.conf>>
<a>
<<Include second.conf>>
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, [('<<', 'include', ' ', 'first.conf', '>>'), '\n', 'a', '\n',
                                ('<<', 'Include', ' ', 'second.conf', '>>'), '\n', 'a', '\n'])

    def testIncludesApache(self):
        text = """\
include first.conf
<a>
Include second.conf
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, [('include', ' ', 'first.conf'), '\n', 'a', '\n',
                            ('Include', ' ', 'second.conf'), '\n', 'a', '\n'])

    def testMultilineOption(self):
        text = """\
a \\
c b  \\
  """
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, [('a', ' ', 'c b'), '  \\\n  '])

    def testNoStripValues(self):
        text = """  a b    """
        options = { 'nostripvalues': True }
        ApacheConfigLexer = make_lexer(**options)
        tokens = ApacheConfigLexer().tokenize(text)
        self.assertEqual(tokens, ['  ', ('a', ' ', 'b    ')])

    def testNoStripValuesMultiline(self):
        text = """\
  Bb Cc\
 \
 """
        options = { 'nostripvalues': True }
        ApacheConfigLexer = make_lexer(**options)
        tokens = ApacheConfigLexer().tokenize(text)
        self.assertEqual(tokens, ['  ', ('Bb', ' ', 'Cc  ')])

    def testConfiguration(self):
        text = """\
# h
a = b
<a>
  a b
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['# h', '\n', ('a', ' = ', 'b'), '\n', 'a', '\n  ', ('a', ' ', 'b'), '\n', 'a', '\n'])


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
