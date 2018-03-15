#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import sys

from apacheconfig import parser

try:
    import unittest2 as unittest

except ImportError:
    import unittest


class GrammarTestCase(unittest.TestCase):
    def testWhitespace(self):
        text = '   \t\t  \t \r  \n\n'
        tokens = parser.WHITE.parseString(text)
        self.assertFalse(tokens[0].strip())

        text = '\n\r'
        self.assertRaises(parser.ParseException, parser.WHITE.parseString, text)

    def testOptionAndValue(self):
        tokens = parser.OPTION_AND_VALUE.parseString('a b\n')
        self.assertEqual(tokens.asList(), [['a', 'b']])

        tokens = parser.OPTION_AND_VALUE.parseString('a=b\n')
        self.assertEqual(tokens.asList(), [['a', 'b']])

        tokens = parser.OPTION_AND_VALUE.parseString('a "b"\n')
        self.assertEqual(tokens.asList(), [['a', 'b']])

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
        tokens = parser.OPTION_AND_VALUE_SET.parseString(text)
        self.assertEqual(tokens.asList(), [['a', 'b']] * 8)

    def testLiteralTag(self):
        tokens = parser.LITERAL_TAG.parseString('a')
        self.assertEqual(tokens.asList(), ['a'])

        tokens = parser.LITERAL_TAG.parseString(' a')
        self.assertEqual(tokens.asList(), ['a'])

        tokens = parser.LITERAL_TAG.parseString(' a b ')
        self.assertEqual(tokens.asList(), ['a', 'b'])

        tokens = parser.LITERAL_TAG.parseString(' a < b ')
        self.assertEqual(tokens.asList(), ['a'])

    def testOpenLiteralTag(self):
        tokens = parser.OPEN_TAG.parseString('<a>')
        self.assertEqual(tokens.asList(), ['a'])

        tokens = parser.OPEN_TAG.parseString('<  a>')
        self.assertEqual(tokens.asList(), ['a'])

        tokens = parser.OPEN_TAG.parseString('<  a b  >')
        self.assertEqual(tokens.asList(), ['a', 'b'])

    def testCloseLiteralTag(self):
        tokens = parser.CLOSE_TAG.parseString('</a>')
        self.assertEqual(tokens.asList(), ['a'])

        tokens = parser.CLOSE_TAG.parseString('</  a>')
        self.assertEqual(tokens.asList(), ['a'])

        tokens = parser.CLOSE_TAG.parseString('</  a b  >')
        self.assertEqual(tokens.asList(), ['a', 'b'])

    def testComments(self):
        text = """\
#
# a
#a
# a b
"""
        tokens = parser.COMMENTS.parseString(text)
        self.assertEqual(tokens.asList(), [[], ['a'], ['a'], ['a', 'b']])

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
        tokens = parser.TAGGED_BLOCK.parseString(text)
        self.assertEqual(tokens.asList(), ['a'] + [['a', 'b']] * 5 + ['a'])

    def testBlockComments(self):
        text = """\
<a>
#
# a
# a b
</a>
"""
        tokens = parser.TAGGED_BLOCK.parseString(text)
        self.assertEqual(tokens.asList(), ['a', [], ['a'], ['a', 'b'], 'a'])

    def testBlockBlankLines(self):
        text = """\
<a>


</a>
"""
        tokens = parser.BLOCK.parseString(text)
        self.assertEqual(tokens.asList(), ['a', 'a'])

    def testConfiguration(self):
        text = """\
# h
a = b
<a>
  a b
</a>
"""
        tokens = parser.COMMENTS.parseString(text)
        self.assertEqual(tokens.asList(), ['a'] + [['a', 'b']] * 5 + ['a'])


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
