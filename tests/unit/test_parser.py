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


class ParserTestCase(unittest.TestCase):

    def testOptionAndValue(self):
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(ApacheConfigLexer(), start='statement')

        ast = parser.parse('a b\n')
        self.assertEqual(ast, ['statement', 'a', 'b'])

        ast = parser.parse('a=b\n')
        self.assertEqual(ast, ['statement', 'a', 'b'])

        ast = parser.parse('a "b c"\n')
        self.assertEqual(ast, ['statement', 'a', 'b c'])

    def testHashComments(self):
            text = """\
#a
# b
"""
            ApacheConfigLexer = make_lexer()
            ApacheConfigParser = make_parser()

            parser = ApacheConfigParser(ApacheConfigLexer(), start='contents')

            ast = parser.parse(text)
            self.assertEqual(ast, ['contents', ['comment', 'a'], ['comment', ' b']])

    def testCStyleComments(self):
        text = """\
/*a*/
/*
# b
*/
    """
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(ast, ['contents', ['comment', 'a'], ['comment', '\n# b\n']])

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

            parser = ApacheConfigParser(ApacheConfigLexer(), start='contents')

            self.assertRaises(ApacheConfigError, parser.parse, text)

    def testIncludes(self):
        text = """\
include first.conf
<<include second.conf>>
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(ast, ['contents', ['include', 'first.conf'], ['include', 'second.conf']])

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

        parser = ApacheConfigParser(ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(ast, ['contents', ['include', 'first.conf'], ['include', 'second.conf']])

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
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

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

    def testBlockWithOptions(self):
        text = """\
<a>
  #a
  a = "b b"
  # a b
  a = "b b"
</a>
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(ApacheConfigLexer(), start='block')

        ast = parser.parse(text)
        self.assertEqual(ast, ['block', 'a',
                               ['contents',
                                ['comment', 'a'],
                                ['statements',
                                 ['statement', 'a', 'b b']],
                                ['comment', ' a b'],
                                ['statements',
                                 ['statement', 'a', 'b b']]], 'a'])

    def testNestedBlock(self):
            text = """\
<a>
  <b>
     <c>
     </c>
  </b>
</a>
"""
            ApacheConfigLexer = make_lexer()
            ApacheConfigParser = make_parser()

            parser = ApacheConfigParser(ApacheConfigLexer(), start='block')

            ast = parser.parse(text)
            self.assertEqual(ast, ['block', 'a',
                                   ['contents',
                                    ['block', 'b',
                                     ['contents',
                                      ['block', 'c', [], 'c']], 'b']], 'a'])

    def testEmptyBlocks(self):
        text = """\
<a/>
<b/>
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(ApacheConfigLexer(), start='contents')

        ast = parser.parse(text)
        self.assertEqual(ast, ['contents',
                               ['block', 'a', [], 'a'],
                               ['block', 'b', [], 'b']])

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
        self.assertEqual(ast, ['contents',
                               ['block', 'a', [], 'a'],
                               ['block', 'aa',
                                ['contents',
                                 ['statements', ['statement', 'bb', 'Cc']]],
                                'aa']])

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
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        parser = ApacheConfigParser(ApacheConfigLexer(), start='config')

        ast = parser.parse(text)
        self.assertEqual(ast, ['config',
                               ['contents',
                                ['comment', ' a'],
                                ['statements',
                                 ['statement', 'a', 'b']],
                                ['block', 'a',
                                 ['contents',
                                  ['statements',
                                   ['statement', 'a', 'b']]], 'a'],
                                ['statements',
                                 ['statement', 'a', 'b']],
                                ['block', 'a a',
                                 ['contents',
                                  ['statements',
                                   ['statement', 'a', 'b']]], 'a a'],
                                ['comment', ' a']]])


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
