#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
try:
    import unittest2 as unittest

except ImportError:
    import unittest

from apacheconfig import LeafASTNode
from apacheconfig import native_apache_parser


class WLoaderTestCaseWrite(unittest.TestCase):

    def setUp(self):
        self.parser = native_apache_parser()

    def testChangeItemValue(self):
        cases = [
            ('option value', 'value2', 'option value2'),
            ('\noption value', 'value2', '\noption value2'),
            ('\noption =\\\n  value', 'value2', '\noption =\\\n  value2'),
            ('option value', 'long  value', 'option long  value'),
            ('option value', '"long  value"', 'option "long  value"'),
            ('option', 'option2', 'option option2'),
            ('include old/path/to/file', 'new/path/to/file',
             'include new/path/to/file'),
        ]
        for raw, new_value, expected in cases:
            node = LeafASTNode.parse(raw, self.parser)
            node.value = new_value
            self.assertEqual(expected, node.dump())


class WLoaderTestCaseRead(unittest.TestCase):

    def setUp(self):
        self.parser = native_apache_parser()

    def testChangeItemValue(self):
        cases = [
            ('option value', 'value2', 'option value2'),
            ('\noption value', 'value2', '\noption value2'),
            ('\noption =\\\n  value', 'value2', '\noption =\\\n  value2'),
            ('option value', 'long  value', 'option long  value'),
            ('option value', '"long  value"', 'option "long  value"'),
            ('option', 'option2', 'option option2'),
            ('include old/path/to/file', 'new/path/to/file',
             'include new/path/to/file'),
        ]
        for raw, new_value, expected in cases:
            node = LeafASTNode.parse(raw, self.parser)
            node.value = new_value
            self.assertEqual(expected, node.dump())

    def _test_item_cases(self, cases, expected_type, parser=None):
        if not parser:
            parser = self.parser
        for raw, expected_name, expected_value in cases:
            node = LeafASTNode.parse(raw, self.parser)
            self.assertEqual(expected_name, node.name,
                             "Expected node('%s').name to be %s, got %s" %
                             (repr(raw), expected_name, node.name))
            self.assertEqual(expected_value, node.value,
                             "Expected node('%s').value to be %s, got %s" %
                             (repr(raw), expected_value, node.value))
            self.assertEqual(raw, node.dump(),
                             ("Expected node('%s').dump() to be the same, "
                              "but got '%s'" % (repr(raw), node.dump())))
            self.assertEqual(expected_type, node.typestring,
                             ("Expected node('%s').typestring to be '%s', "
                              "but got '%s'" % (repr(raw), expected_type,
                                                str(node.typestring))))

    def testLoadStatement(self):
        cases = [
            ('option value', 'option', 'value'),
            ('option', 'option', None),
            ('  option value', 'option', 'value'),
            ('  option = value', 'option', 'value'),
            ('\noption value', 'option', 'value'),
            ('option "dblquoted value"', 'option', 'dblquoted value'),
            ("option 'sglquoted value'", "option", "sglquoted value"),
        ]
        self._test_item_cases(cases, 'statement')

    def testLoadComment(self):
        comment = '# here is a silly comment'
        cases = [
            (comment, comment, None),
            ('\n' + comment, comment, None),
            (' ' + comment, comment, None),
        ]
        self._test_item_cases(cases, 'comment')

    def testLoadApacheInclude(self):
        cases = [
            ('include path', 'include', 'path'),
            ('  include path', 'include', 'path'),
            ('\ninclude path', 'include', 'path'),
        ]
        self._test_item_cases(cases, 'include',
                              native_apache_parser(
                                  options={'useapacheinclude': True}))
