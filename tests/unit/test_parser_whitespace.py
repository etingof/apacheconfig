#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
from apacheconfig import make_lexer
from apacheconfig import make_parser

try:
    import unittest2 as unittest

except ImportError:
    import unittest


def _create_parser(options={}, start='contents'):
    ApacheConfigLexer = make_lexer(**options)
    ApacheConfigParser = make_parser(**options)

    return ApacheConfigParser(ApacheConfigLexer(), start=start)


class WhitespaceParserTestCase(unittest.TestCase):
    def _test_cases(self, cases, tag='contents', options={}):
        options['preservewhitespace'] = True
        parser = _create_parser(start=tag, options=options)

        for x, expected in cases:
            got = parser.parse(x)

            self.assertEqual(
                got, expected,
                "When parsing '%s' we got %s, but "
                "expected %s" % (repr(x), got, expected))

    def testOptionAndValue(self):
        tests = [
            ('a', ['statement', 'a']),
            ('a  b', ['statement', 'a', '  ', 'b']),
            ('a = b', ['statement', 'a', ' = ', 'b']),
            ('a "b c"', ['statement', 'a', ' ', 'b c']),
        ]
        self._test_cases(tests, tag='statement')

    def testInclude(self):
        tests = [
            ('include   file.conf', [
                'include', 'include', '   ', 'file.conf']),
            ('<<include   file.conf>>', [
                'include', '<<', 'include', '   ', 'file.conf', '>>']),
        ]
        self._test_cases(tests, tag='include')

    def testIncludeOptional(self):
        tests = [
            ('includeoptional   file.conf', [
                'includeoptional', 'includeoptional', '   ', 'file.conf'
            ])
        ]
        self._test_cases(tests, tag='includeoptional')

    def testHashComment(self):
        comment = '# hello there !!! yep'
        tests = [(comment, ['comment', comment])]
        self._test_cases(tests, tag='comment')

    def testContentsWhitespaces(self):
        tests = [
            ('\n', ['contents', '\n']),
            ('\na', ['contents', ['statement', '\n', 'a']]),
            ('a b', ['contents', ['statement', 'a', ' ', 'b']]),
            ('a b\n ', ['contents', ['statement', 'a', ' ', 'b'], '\n ']),
            ('\n a b', ['contents', ['statement', '\n ', 'a', ' ', 'b']]),
            ('\n a b\n',
             ['contents', ['statement', '\n ', 'a', ' ', 'b'], '\n']),
            (' \n a b\nb c\n', ['contents',
                                ['statement', ' \n ', 'a', ' ', 'b'],
                                ['statement', '\n', 'b', ' ', 'c'], '\n']),
        ]
        self._test_cases(tests, tag='contents')

    def testContentsWithComments(self):
        tests = [
            ('# a b', ['contents', ['comment', '# a b']]),
            ('\n # a b', ['contents', ['comment', '\n ', '# a b']]),
            ('   # a b', ['contents', ['comment', '   ', '# a b']]),
            ('a b #comment\n  ', ['contents',
                                  ['statement', 'a', ' ', 'b'],
                                  ['comment', ' ', '#comment'], '\n  ']),
            ('a b \n #comment\n  ', ['contents',
                                     ['statement', 'a', ' ', 'b'],
                                     ['comment', ' \n ', '#comment'], '\n  ']),
            ('a b #comment\n  #comment2\n c d\n', [
                'contents',
                ['statement', 'a', ' ', 'b'],
                ['comment', ' ', '#comment'],
                ['comment', '\n  ', '#comment2'],
                ['statement', '\n ', 'c', ' ', 'd'], '\n'
            ]),
        ]
        self._test_cases(tests, tag='contents')

    def testNamedBlocks(self):
        tests = [
            ('<a name/>', [
                'block', ('a', ' ', 'name'), [], 'a name'
            ]),
            ('<a name>\n</a>', [
                'block', ('a', ' ', 'name'), ['contents', '\n'], 'a']),
        ]
        self._test_cases(tests, tag='block')

    def testBlocks(self):
        tests = [
            ('<a/>', ['block', ('a',), [], 'a']),
            ('<a>\n</a>', ['block', ('a',), ['contents', '\n'], 'a']),
            ('<a> #comment\n</a>', [
                'block', ('a',), ['contents', [
                    'comment', ' ', '#comment'], '\n'], 'a']),
            ('<a> #comment\n a b #comment2\n</a>', [
                'block', ('a',), ['contents', [
                    'comment', ' ', '#comment'],
                                  ['statement', '\n ', 'a', ' ', 'b'],
                                  ['comment', ' ', '#comment2'], '\n'], 'a'])
        ]

        self._test_cases(tests, tag='block')

    def testEmptyConfig(self):
        tests = [(" \n", ['config', ['contents', ' \n']])]
        self._test_cases(tests, tag='config')
