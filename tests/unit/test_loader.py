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

try:
    mock = unittest.mock

except AttributeError:

    import mock


class LoaderTestCase(unittest.TestCase):

    def testWholeConfig(self):
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
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()))

        config = loader.loads(text)

        self.assertEqual(config, {'a': ['b', {'block': {'a': 'b'}},
                                        'b', {'a block': {'c': 'd d'}}]})

    def testDuplicateBlocksUnmerged(self):
        text = """\
<a>
b = 1
</a>
<a>
b = 2
</a>
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()))

        config = loader.loads(text)

        self.assertEqual(config, {'a': [{'b': '1'}, {'b': '2'}]})

    def testDuplicateBlocksMerged(self):
        text = """\
<a>
b = 1
</a>
<a>
b = 2
</a>
"""
        options = {
            'mergeduplicateblocks': True
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'a': {'b': ['1', '2']}})

    def testDuplicateOptionsAllowed(self):
        text = """\
a = 1
a = 2
"""
        options = {
            'allowmultioptions': True
        }

        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'a': ['1', '2']})

    def testDuplicateOptionsDenied(self):
        text = """\
a = 1
a = 2
"""
        options = {
            'allowmultioptions': False
        }

        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        self.assertRaises(ApacheConfigError, loader.loads, text)

    def testDuplicateOptionsOverriden(self):
        text = """\
a = 1
a = 2
"""
        options = {
            'mergeduplicateoptions': True
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'a': '2'})

    def testNamedBlocks(self):
        text = """\
<a b>
c = 1
</a b>
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()))

        config = loader.loads(text)

        self.assertEqual(config, {'a': {'b': {'c': '1'}}})

    def testAutoTrue(self):
        text = """\
a 1
a on
a true
b 0
b off
b false
"""
        options = {
            'autotrue': True
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'a': ['1', '1', '1'], 'b': ['0', '0', '0']})

    @mock.patch('os.path.exists')
    def testConfigPath(self, path_exists_mock):
        text = """\
<<include t.conf>>
"""

        options = {
            'configpath': ['a', 'b']
        }

        path_exists_mock.return_value = False

        with make_loader(**options) as loader:
            self.assertRaises(ApacheConfigError, loader.loads, text)

        expected_probes = ['a/t.conf', 'b/t.conf', './t.conf']
        actual_probes = [x[1][0] for x in path_exists_mock.mock_calls
                         if len(x[1]) and x[1][0] in expected_probes]

        self.assertEqual(expected_probes, actual_probes)

    @mock.patch('os.path.exists')
    def testProgramPath(self, path_exists_mock):
        text = """\
<<include t.conf>>
"""

        options = {
            'programpath': 'a/b'
        }

        path_exists_mock.return_value = False

        with make_loader(**options) as loader:
            self.assertRaises(ApacheConfigError, loader.loads, text)

        expected_probes = ['a/b/t.conf']
        actual_probes = [x[1][0] for x in path_exists_mock.mock_calls
                         if len(x[1]) and x[1][0] in expected_probes]

        self.assertEqual(expected_probes, actual_probes)

    @mock.patch('os.path.exists')
    def testIncludeRelative(self, path_exists_mock):
        text = """\
<<include t.conf>>
"""

        options = {
            'includerelative': True,
            'configroot': 'a'
        }

        path_exists_mock.return_value = False

        with make_loader(**options) as loader:
            self.assertRaises(ApacheConfigError, loader.loads, text)

        expected_probes = ['a/t.conf']
        actual_probes = [x[1][0] for x in path_exists_mock.mock_calls
                         if len(x[1]) and x[1][0] in expected_probes]

        self.assertEqual(expected_probes, actual_probes)

    def testIncludeDirectories(self):
        text = """\
<<include xxx>>
"""

        options = {
            'includedirectories': True
        }

        with make_loader(**options) as loader:
            with mock.patch('os.path.exists') as path_exists_mock:
                with mock.patch('os.path.isdir') as path_isdir_mock:
                    with mock.patch('os.listdir') as listdir_mock:
                        path_exists_mock.side_effect = lambda x: [True, False]
                        path_isdir_mock.side_effect = lambda x: [True, False]
                        listdir_mock.return_value = []

                        config = loader.loads(text)

                        self.assertEqual(config, {})


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
