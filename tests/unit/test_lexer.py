# -*- coding: utf-8 -*-
#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
from __future__ import unicode_literals

import sys

from apacheconfig import ApacheConfigError
from apacheconfig import make_lexer

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

    def testUnicodeSupport(self):
        text = 'a = 三\n'
        tokens = self.lexer.tokenize(text)
        self.assertEqual(
            tokens, [('a', ' = ', '三'), '\n'])

    def testOptionAndValueWeirdQuotes(self):
        text = """\
"a"
"a b c d e"
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(
            tokens, [('"a"',), '\n', ('"a b c d e"',), '\n'])

    def testOptionAndValueEdgeCases(self):
        text = "="
        self.assertRaises(ApacheConfigError, self.lexer.tokenize, text)

    def testOptionAndValueSet(self):
        text = """\
a
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
        self.assertEqual(
            tokens, [
                ('a',), '\n', ('a', ' ', 'b'), '\n', ('a', ' = ', 'b'),
                '\n', ('a', '    ', 'b'), '\n',
                ('a', '= ', 'b'), '\n', ('a', ' =', 'b'), '\n',
                ('a', '   ', 'b'), '\n',
                ('a', ' ', 'b'), '\n', ('a', ' = ', 'b'), '\n'
            ]
        )

    def testLiteralTags(self):
        text = """\
<a>
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, [('a',), '\n', 'a', '\n'])

    def testExpressionTags(self):
        text = """\
    <if a == 1>
    </if>
    """
        tokens = self.lexer.tokenize(text)
        self.assertEqual(
            tokens, [
                '    ', ('if', ' ', 'a == 1'), '\n    ', 'if', '\n    '
            ]
        )

    def testHashEscapes(self):
        text = "favorite_color \\#000000"
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, [('favorite_color', ' ', '\\#000000')])

    def testHashEscapesAndComments(self):
        text = "favorite_color \\#000000 # comment"
        tokens = self.lexer.tokenize(text)
        self.assertEqual(
            tokens, [
                ('favorite_color', ' ', '\\#000000'), ' ', '# comment'
            ]
        )

    def testCommentContinuationsDisabled(self):
        text = "# comment \\\ndoesnt continue"
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, ['# comment \\', '\n',
                                  ('doesnt', ' ', 'continue')])

    def testCommentContinuations(self):
        text = "# comment \\\n continues \\\n multiple lines"
        options = {'multilinehashcomments': True}
        ApacheConfigLexer = make_lexer(**options)
        tokens = ApacheConfigLexer().tokenize(text)
        self.assertEqual(tokens,
                         ['# comment \\\n continues \\\n multiple lines'])

    def testCommentContinuationsEmptyLine(self):
        text = "# comment \\\n\n# comment"
        options = {'multilinehashcomments': True}
        ApacheConfigLexer = make_lexer(**options)
        tokens = ApacheConfigLexer().tokenize(text)
        self.assertEqual(tokens, ['# comment \\\n', '\n', '# comment'])

    def testCommentContinuationsWithOtherComments(self):
        text = ("# comment \\\n continues \\\n multiple lines\n"
                "# comment stuff\n hello there")
        options = {'multilinehashcomments': True}
        ApacheConfigLexer = make_lexer(**options)
        tokens = ApacheConfigLexer().tokenize(text)
        self.assertEqual(tokens, [
                         '# comment \\\n continues \\\n multiple lines',
                         '\n', '# comment stuff', '\n ',
                         ('hello', ' ', 'there')])

    def testCommentInBlock(self):
        text = "<block>\n# comment\n</block>"
        ApacheConfigLexer = make_lexer()
        tokens = ApacheConfigLexer().tokenize(text)
        self.assertEqual(tokens, [('block',), '\n', '# comment', '\n',
                                  'block'])

    def testComments(self):
        text = """\
#
# a
#a
# a b
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(
            tokens, [
                '#', '\n', '# a', '\n', '#a', '\n', '# a b', '\n'
            ]
        )

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
        self.assertEqual(
            tokens, [
                ('a',), '\n', ('a', ' ', 'b'), '\n', ('a', '=', 'b'),
                '\n', ('a', ' =  ', 'b'), '\n',
                ('a', ' = ', 'b'), '\n', ('a', ' ', 'b'), '\n', 'a', '\n'
            ]
        )

    def testBlockComments(self):
        text = """\
<a>
#
# a
# a b
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(
            tokens, [
                ('a',), '\n', '#', '\n', '# a', '\n', '# a b', '\n', 'a', '\n'
            ]
        )

    def testEmptyBlock(self):
        text = "<im   a empty block/>"
        tokens = self.lexer.tokenize(text)
        self.assertEqual(
            tokens, [
                ('im', '   ', 'a empty block')
            ]
        )

    def testBlockBlankLines(self):
        text = """\
<a>


</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(
            tokens, [
                ('a',), '\n\n\n', 'a', '\n'
            ]
        )

    def testBlockTagWithSpaces(self):
        text = "<  \t a  >\n</a>"
        tokens = self.lexer.tokenize(text)
        self.assertEqual(
            tokens, [
                ('  \t a  ',), '\n', 'a'
            ]
        )

    def testMultilineBlockNameEmpty(self):
        text = "<long \\\n bloc\\\n name\\\n     \\\n/>"
        tokens = self.lexer.tokenize(text)
        self.assertEqual(
            tokens, [
                ('long', ' \\\n ', 'bloc name ')
            ]
        )

    def testMultilineBlockName(self):
        text = "<long \\\n bloc\\\n name\\\n     \\\n>\n</long>"
        tokens = self.lexer.tokenize(text)
        self.assertEqual(
            tokens, [
                ('long', ' \\\n ', 'bloc name '), '\n', 'long'
            ]
        )

    def testEmptyElementTags(self):
        text = "<block/>"
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, [('block',)])

    def testEmptyElementTagsDisabled(self):
        options = {'disableemptyelementtags': True}
        text = """\
<block/>
<block />
<block hello/>
"""
        ApacheConfigLexer = make_lexer(**options)
        tokens = ApacheConfigLexer().tokenize(text)
        self.assertEqual(
            tokens, [
                ('block/',), '\n', ('block', ' ', '/'), '\n',
                ('block', ' ', 'hello/'), '\n'
            ]
        )

    def testIncludesConfigGeneral(self):
        text = """\
<<include first.conf>>
<a>
<<Include second.conf>>
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(
            tokens, [
                ('<<', 'include', ' ', 'first.conf', '>>'), '\n', ('a',), '\n',
                ('<<', 'Include', ' ', 'second.conf', '>>'), '\n', 'a', '\n'
            ]
        )

    def testIncludesApache(self):
        text = """\
include first.conf
<a>
Include second.conf
</a>
"""
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, [
            ('include', ' ', 'first.conf'), '\n', ('a',), '\n',
            ('Include', ' ', 'second.conf'), '\n', 'a', '\n'
        ]
                         )

    def testMultilineOption(self):
        text = """\
a \\
c b  \\
  """
        tokens = self.lexer.tokenize(text)
        self.assertEqual(tokens, [('a', ' \\\n', 'c b'), '  \\\n  '])

    def testNoStripValues(self):
        text = """  a b    """
        options = {'nostripvalues': True}
        ApacheConfigLexer = make_lexer(**options)
        tokens = ApacheConfigLexer().tokenize(text)
        self.assertEqual(tokens, ['  ', ('a', ' ', 'b    ')])

    def testNoStripValuesMultiline(self):
        text = """\
  Bb Cc\
 \
 """
        options = {'nostripvalues': True}
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
        self.assertEqual(
            tokens, [
                '# h', '\n', ('a', ' = ', 'b'), '\n', ('a',), '\n  ',
                ('a', ' ', 'b'), '\n', 'a', '\n'
            ]
        )


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
