# -*- coding: utf-8 -*-
#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
from __future__ import unicode_literals

import six

try:
    import unittest2 as unittest

except ImportError:
    import unittest

import os
import shutil
import tempfile

from apacheconfig import flavors
from apacheconfig import make_loader
from apacheconfig.error import ApacheConfigError


class WLoaderTestCaseWrite(unittest.TestCase):

    def setUp(self):
        context = make_loader(writable=True, **flavors.NATIVE_APACHE)
        self.loader = context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)

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
            node = next(iter(self.loader.loads(raw)))
            node.value = new_value
            self.assertEqual(expected, node.dump())

    def testChangeBlockValue(self):
        cases = [
            ("<block name>\n</block>", "name2", "<block name2>\n</block>"),
            ("<block>\n</block>", "name2", "<block name2>\n</block>"),
        ]
        for raw, new_value, expected in cases:
            node = next(iter(self.loader.loads(raw)))
            node.arguments = new_value
            self.assertEqual(expected, node.dump())

    def testAddToContents(self):
        cases = [
            # Inserting statement middle or end
            ("a b\nc d", 1, "\n1 2", "a b\n1 2\nc d"),
            ("a b\nc d", 2, "\n1 2", "a b\nc d\n1 2"),
            ("a b\n", 1, " ###", "a b ###\n"),
            ("a b # comment\n", 1, "\n1 2", "a b\n1 2 # comment\n"),
            # Inserting option/value statement at beginning
            ("a", 0, "\n1 2", "\n1 2\na"),
            ("a\n", 0, "###", "###\na\n"),
            ("  a b", 0, "\n1 2", "\n1 2\n  a b"),
            ("\n", 0, "\n1 2", "\n1 2\n"),
            ("# comment\n", 0, "\n1 2", "\n1 2\n# comment\n"),
        ]
        for raw, index, to_add, expected in cases:
            node = self.loader.loads(raw)
            node.add(index, to_add)
            self.assertEqual(expected, node.dump())

    def testRemoveFromContents(self):
        cases = [
            ("a b\nc d", 1, "a b"),
            ("a b\nc d", 0, "\nc d"),
            ("\na\n", 0, "\n"),
            ("a # comment", 1, "a"),
            ("a # comment", 0, " # comment")
        ]
        for raw, index, expected in cases:
            node = self.loader.loads(raw)
            node.remove(index)
            self.assertEqual(expected, node.dump())


class WLoaderTestCaseRead(unittest.TestCase):

    def setUp(self):
        context = make_loader(writable=True, **flavors.NATIVE_APACHE)
        self.loader = context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)

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
            node = next(iter(self.loader.loads(raw)))
            node.value = new_value
            self.assertEqual(expected, node.dump())

    def _test_item_cases(self, cases, expected_type):
        for raw, expected_name, expected_value in cases:
            node = next(iter(self.loader.loads(raw)))
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
                              "but got '%s'" %
                              (repr(raw), expected_type,
                               six.text_type(node.typestring))))

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
        self._test_item_cases(cases, 'include')

    def testDumpUnicodeSupport(self):
        text = "\n value is 三"
        node = next(iter(self.loader.loads(text)))
        dump = node.dump()
        self.assertTrue(isinstance(dump, six.text_type))
        self.assertEqual(dump, text)

    def testStrUnicodeBuiltIns(self):
        node = next(iter(self.loader.loads("\n option value")))
        self.assertTrue(isinstance(str(node), str))
        self.assertTrue(isinstance(node.__unicode__(), six.text_type))
        if six.PY2:
            # Make test compatible with both u'string' and 'string'
            node_str = six.text_type(node).replace("u'", "'")
        self.assertEqual(
            "LeafNode(['statement', 'option', ' ', 'value'])", node_str)

    def testLoadContents(self):
        cases = [
            ('a b\nc d', ('a b', '\nc d')),
            ('  \n', tuple()),
            ('a b  \n', ('a b',)),
            ('a b # comment', ('a b', ' # comment')),
            ('a b\n<b>\n</b>  \n', ('a b', '\n<b>\n</b>')),
        ]
        for raw, expected in cases:
            node = self.loader.loads(raw)
            self.assertEqual(len(node), len(expected))
            for got, expected in zip(node, expected):
                self.assertEqual(got.dump(), expected)
            self.assertEqual(raw, node.dump())

    def testMalformedContents(self):
        from apacheconfig.wloader import ListNode
        cases = [
            (["block", ("b",), [], "b"], "Wrong typestring."),
            (["statement", "option", " ", "value"], "Wrong typestring."),
            (["contents", ["contents", []]], "Malformed contents."),
            (["contents", ["block", ("b",), []]], "Malformed contents."),
        ]
        for case in cases:
            self.assertRaises(ApacheConfigError, ListNode, case[0],
                              None)

    def testModifyListIndexError(self):
        cases = [
            ('a b\nc d', "add", 4),
            ('a b\nc d', "add", -1),
            ('a b\nc d', "remove", 3),
            ('a b\nc d', "remove", -1),
            ('\n', "remove", 0),
            ('\n', "add", 1),
        ]
        for raw, fn, index in cases:
            node = self.loader.loads(raw)
            self.assertEqual(raw, node.dump())
            if fn == "add":
                self.assertRaises(IndexError, node.add, index, " # comment")
            else:
                self.assertRaises(IndexError, node.remove, index)

    def testListAddParsingError(self):
        node = self.loader.loads("a b\nc d")
        cases = ["a b\nc d", ""]
        for case in cases:
            self.assertRaises(ApacheConfigError, node.add, 0, case)

    def testMalformedBlocks(self):
        from apacheconfig.wloader import BlockNode
        cases = [
            (["contents", []], "Wrong typestring."),
            (["statement", "option", " ", "value"], "Wrong typestring."),
            (["block", ("b",), []], "Raw data too short."),
            (["block", ("b",), ["contents"], "b"], "Malformed contents."),
        ]
        for case in cases:
            self.assertRaises(ApacheConfigError, BlockNode, case[0],
                              None)

    def testMalformedItem(self):
        from apacheconfig.wloader import LeafNode
        cases = [
            (["contents", []], "Wrong typestring."),
            (["block", ("b",), [], "b"], "Wrong typestring."),
            (["statement"], "Too short."),
        ]
        for case in cases:
            self.assertRaises(ApacheConfigError, LeafNode, case[0])

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
            node = next(iter(self.loader.loads(raw)))
            self.assertEqual("b", node.tag)
            self.assertEqual(value, node.arguments)
            self.assertEqual(raw, node.dump())

    def testLoadWholeConfigFromFile(self):
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
        t = tempfile.mkdtemp()
        filepath = os.path.join(t, "config")
        with open(filepath, "w") as f:
            f.write(text)
        node = self.loader.load(filepath)
        self.assertEqual(text, node.dump())
        shutil.rmtree(t)
