#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import os
import sys

from apacheconfig import *

try:
    import unittest2 as unittest

except ImportError:
    import unittest

try:
    from unittest import mock

except ImportError:

    import mock

class WLoaderTestCaseWrite(unittest.TestCase):
    def testChangeItemValue(self):
        cases = [
            ('option value', 'value2', 'option value2'),
            ('\noption value', 'value2', '\noption value2'),
            ('\noption =\\\n  value', 'value2', '\noption =\\\n  value2'),
            ('option value', 'long  value', 'option long  value'),
            ('option value', '"long  value"', 'option "long  value"'),
            ('option', 'option2', 'option option2'),
            ('include old/path/to/file', 'new/path/to/file', 'include new/path/to/file'),
        ]
        for raw, new_value, expected in cases:
            node = parse_item(raw)
            node.value = new_value
            self.assertEqual(expected, str(node))

    def testChangeBlockValue(self):
        cases = [
            ("<block name>\n</block>", "name2", "<block name2>\n</block>"),
            ("<block>\n</block>", "name2", "<block name2>\n</block>"),
        ]
        for raw, new_value, expected in cases:
            node = parse_block(raw)
            node.arguments = new_value
            self.assertEqual(expected, str(node))

    def testAddToContents(self):
        cases = [
            # Inserting statement middle or end
            ("a b\nc d", 1, "\n1 2", "a b\n1 2\nc d"),
            ("a b\nc d", 2, "\n1 2", "a b\nc d\n1 2"),
            ("a b\n", 1, " ###", "a b ###\n"),
            ("a b # comment\n", 1, "\n1 2", "a b\n1 2\n # comment\n"),
            # Inserting option/value statement at beginning
            ("a", 0, "\n1 2", "\n1 2\na"),
            ("a\n", 0, "###", "###\na\n"),
            ("  a b", 0, "\n1 2", "\n1 2\n  a b"),
            ("\n", 0, "\n1 2", "\n1 2\n"),
            ("# comment\n", 0, "\n1 2", "\n1 2\n# comment\n"),
        ]
        for raw, index, to_add, expected in cases:
            node = parse_contents(raw)
            node.add(index, to_add)
            self.assertEqual(expected, str(node))

    def testRemoveFromContents(self):
        cases = [
            ("a b\nc d", 1, "a b"),
            ("a b\nc d", 0, "\nc d"),
            ("\na\n", 0, "\n"),
            ("a # comment", 1, "a"),
            ("a # comment", 0, " # comment")
        ]
        for raw, index, expected in cases:
            node = parse_contents(raw)
            node.remove(index)
            self.assertEqual(expected, str(node))

class WLoaderTestCaseRead(unittest.TestCase):
    def _test_item_cases(self, cases, expected_type, options={}):
        for raw, expected_name, expected_value in cases:
            node = parse_item(raw, options)
            self.assertEqual(expected_name, node.name,
                "Expected node('%s').name to be %s, got %s" %
                    (repr(raw), expected_name, node.name))
            self.assertEqual(expected_value, node.value,
                "Expected node('%s').value to be %s, got %s" %
                    (repr(raw), expected_value, node.value))
            self.assertEqual(raw, str(node),
                "Expected str(node('%s')) to be the same, but got '%s'" %
                    (repr(raw), str(node)))
            self.assertEqual(expected_type, node.type,
                "Expected node('%s').type to be '%s', but got '%s'" %
                    (repr(raw), expected_type, str(node.type)))

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
            options={'useapacheinclude': True})

    def testLoadContents(self):
        cases = [
            ('a b\nc d', ('a b', '\nc d')),
            ('  \n', tuple()),
            ('a b  \n', ('a b',)),
            ('a b # comment', ('a b', ' # comment')),
            ('a b\n<b>\n</b>  \n', ('a b', '\n<b>\n</b>')),
        ]
        for raw, expected in cases:
            node = parse_contents(raw)
            self.assertEqual(len(node), len(expected))
            for got, expected in zip(node, expected):
                self.assertEqual(str(got), expected)
            self.assertEqual(raw, str(node))

    def testLoadBlocks(self):
        cases = [
            ('<b>\nhello there\nit me\n</b>', None),
            ('<b name/>\n</b>', 'name/'),
            ('<b>\n</b>', None),
            ('<b  name>\n</b name>', 'name'),
            ('<b>\n</b>', None),
            ('\n<b>\n</b>', None),
        ]
        for (raw, value) in cases:
            node = parse_block(raw)
            self.assertEqual("b", node.tag)
            self.assertEqual(value, node.arguments)
            self.assertEqual(raw, str(node))

    def testLoadWholeConfig(self):
        text = """\

# a
a = b

<a block>
  a = b
</a>
a b
<a a block>
c "d d"
</a>
# a
"""
        node = parse_contents(text)
        self.assertEqual(text, str(node))
