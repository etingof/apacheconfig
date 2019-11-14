# -*- coding: utf-8 -*-
#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
from __future__ import unicode_literals

import sys

from apacheconfig import make_lexer
from apacheconfig import make_parser

try:
    import unittest2 as unittest

except ImportError:
    import unittest


class ParserTestCase(unittest.TestCase):

    def _make_parser(self, start='contents', **options):
        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)
        return ApacheConfigParser(ApacheConfigLexer(), start=start)

    def testUnicodeSupport(self):
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()
        parser = ApacheConfigParser(ApacheConfigLexer(), start='statement')

        ast = parser.parse('a = 三')
        self.assertEqual(ast, ['statement', 'a', '三'])

    def testOptionAndValue(self):
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(ApacheConfigLexer(), start='statement')

        ast = parser.parse('a')
        self.assertEqual(ast, ['statement', 'a'])

        ast = parser.parse('a b')
        self.assertEqual(ast, ['statement', 'a', 'b'])

        ast = parser.parse('a=b')
        self.assertEqual(ast, ['statement', 'a', 'b'])

        ast = parser.parse('a "b c"')
        self.assertEqual(ast, ['statement', 'a', 'b c'])

    def testContentsWhitespace(self):
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(ApacheConfigLexer(), start='contents')

        tests = ['a b', 'a b\n', '\n a b', '\n a b  \n', '\n a \\\n b  \n']
        for test in tests:
            ast = parser.parse(test)
            self.assertEqual(ast, ['contents', ['statement', 'a', 'b']])

    def testHashComments(self):
        text = """\
#a
# b
c c# c
c \\# # c
key value\\#123
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'contents',
                ['comment', '#a'],
                ['comment', '# b'],
                ['statement', 'c', 'c'],
                ['comment', '# c'],
                ['statement', 'c', '\\#'],
                ['comment', '# c'],
                ['statement', 'key', 'value\\#123']
            ]
        )

    def testCStyleComments(self):
        text = """\
/*a*/
/*
# b
*/
    """
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'contents', ['comment', 'a'],
                ['comment', '\n# b\n']
            ]
        )

    def testCStyleCommentsDisabled(self):
        text = """\
/*a*/
/*
# b
*/
        """
        options = {
            'ccomments': False
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='contents')
        self.assertEqual(
            parser.parse(text), [
                'contents',
                ['statement', '/*a*/'],
                ['statement', '/*'],
                ['comment', '# b'],
                ['statement', '*/']
            ]
        )

    def testIncludes(self):
        text = """\
include first.conf
<<include second.conf>>
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'contents', ['include', 'first.conf'],
                ['include', 'second.conf']
            ]
        )

    def testApacheIncludesDisabled(self):
        text = """\
include first.conf
<<include second.conf>>
"""
        options = {
            'useapacheincludes': False
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'contents', ['include', 'first.conf'],
                ['include', 'second.conf']
            ]
        )

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
   a =        'b'
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'contents',
                ['statement', 'a', 'b'],
                ['statement', 'a', 'b'],
                ['statement', 'a', 'b'],
                ['statement', 'a', 'b'],
                ['statement', 'a', 'b'],
                ['statement', 'a', 'b'],
                ['statement', 'a', 'b'],
                ['statement', 'a', 'b'],
                ['statement', 'a', 'b']
            ]
        )

    def testBlockWithOptions(self):
        text = """\
<a>
  #a
  a = "b b"
  # a b
  a = "b b"
</a>"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='block')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'block', ('a',),
                ['contents',
                 ['comment', '#a'],
                 ['statement', 'a', 'b b'],
                 ['comment', '# a b'],
                 ['statement', 'a', 'b b']], 'a'
            ]
        )

    def testNestedBlock(self):
        text = """\
<a>
  <b>
     <c>
     </c>
  </b>
</a>"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='block')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'block', ('a',),
                ['contents',
                 ['block', ('b',),
                  ['contents',
                   ['block', ('c',), [], 'c']], 'b']], 'a'
            ]
        )

    def testEmptyBlocks(self):
        text = """\
<a/>
<b/>
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'contents',
                ['block', ('a',), [], 'a'],
                ['block', ('b',), [], 'b']
            ]
        )

    def testNamedEmptyBlocks(self):
        text = """\
<a A/>
<b B />
</b B />
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'contents',
                ['block', ('a', ' ', 'A'), [], 'a A'],
                ['block', ('b', ' ', 'B /'), [], 'b B /']
            ]
        )

    def testMultilineBlocks(self):
        text = "<long \\\n bloc \\\n name\\\n>\n</long>"
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'contents', ['block', ('long', ' \\\n ',
                                       'bloc name '),
                             [], 'long']
            ]
        )

    def testNamedBlocksEmptyBlocksDisabled(self):
        text = """\
<hello/>
</hello/>
<a A/>
</a A/>
<b B />
</b B />
"""

        options = {
            'disableemptyelementtags': True
        }
        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'contents', ['block', ('hello/',), [], 'hello/'],
                ['block', ('a', ' ', 'A/',), [], 'a A/'],
                ['block', ('b', ' ', 'B /',), [], 'b B /']])

    def testLowerCaseNames(self):
        text = """\
<A/>
<aA>
  Bb Cc
</aA>
"""
        options = {
            'lowercasenames': True
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        parser = ApacheConfigParser(ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'contents',
                ['block', ('a',), [], 'a'],
                ['block', ('aa',),
                 ['contents', ['statement', 'bb', 'Cc']], 'aa']
            ]
        )

    def testNoStripValues(self):
        text = """\
<aA>
  Bb Cc   \

  key value \\# 123 \t  \

</aA>
"""
        options = {
            'nostripvalues': True
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'contents', [
                    'block', ('aA',), [
                        'contents', ['statement', 'Bb', 'Cc   '],
                        ['statement', 'key', 'value \\# 123 \t  ']], 'aA'
                ]
            ]
        )

    def testHereDoc(self):
        text = """\
<main>
    PYTHON <<MYPYTHON
        def a():
            x = y
            return
    MYPYTHON
</main>
"""
        ast = self._make_parser().parse(text)

        self.assertEqual(
            ast, [
                'contents', ['block', ('main',), [
                    'contents', [
                        'statement', 'PYTHON', '        def a():\n            '
                                               'x = y\n            return'
                    ]
                ], 'main']
            ]
        )

    def testHereDocEscapedNewlinePreservesWhitespace(self):
        text = """\
PYTHON <<MYPYTHON
    def a():
        x = \\
        y
        return
MYPYTHON
"""
        ast = self._make_parser().parse(text)
        self.assertEqual(
            ast, ['contents', ['statement', 'PYTHON', '    def a():\n        '
                               'x = \\\n        y\n        return']])

    def testEmptyConfig(self):
        text = " \n "
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='config')

        ast = parser.parse(text)
        self.assertEqual(ast, ['config', []])

    def testWholeConfig(self):
        text = """\
# a
a = b

<a>
  a = b

</a>
a b
 <a a>
  a b \

  c = d
  # c
 </a a>
# a
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(
            ApacheConfigLexer(), start='config')

        ast = parser.parse(text)
        self.assertEqual(
            ast, [
                'config', [
                    'contents', ['comment', '# a'],
                    ['statement', 'a', 'b'],
                    ['block', ('a',), ['contents',
                                       ['statement', 'a', 'b']], 'a'],
                    ['statement', 'a', 'b'],
                    ['block', ('a', ' ', 'a'), ['contents', ['statement',
                                                             'a', 'b'],
                                                ['statement', 'c', 'd'],
                                                ['comment', '# c']],
                     'a a'],
                    ['comment', '# a']
                ]
            ]
        )


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
