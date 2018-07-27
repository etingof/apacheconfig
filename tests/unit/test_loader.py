#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
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


class LoaderTestCase(unittest.TestCase):

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
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()))

        config = loader.loads(text)

        self.assertEqual(config, {'a': ['b', {'block': {'a': 'b'}},
                                        'b', {'a block': {'c': 'd d'}}]})

    def testDumpWholeConfig(self):
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

        expect_text = """\
a b
<a>
  <block>
    a b
  </block>
</a>
a b
<a>
  <a block>
    c "d d"
  </a block>
</a>
"""

        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()))

        config = loader.loads(text)

        gen_text = loader.dumps(config)

        self.assertEqual(expect_text, gen_text)


    def testForceArray(self):
        text = """\
b = [1]
"""
        options = {
            'forcearray': True
        }
        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'b': ['1']})

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

    def testDuplicateBlocksMerged_noMultiOptions_noMergeDuplicateOptions(self):
        text = """\
<a>
b = 1
</a>
<a>
b = 2
</a>
"""
        options = {
            'mergeduplicateblocks': True,
            'allowmultioptions': False
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        self.assertRaises(ApacheConfigError, loader.loads, text)

    def testDuplicateBlocksMerged_noMultiOptions_MergeDuplicateOptions(self):
        text = """\
<a>
b = 1
</a>
<a>
b = 2
</a>
"""
        options = {
            'mergeduplicateblocks': True,
            'allowmultioptions': False,
            'mergeduplicateoptions': True
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'a': {'b': '2'}})

    def testDuplicateBlocksMerged_allowMultiOptions(self):
        text = """\
<a>
b = 1
</a>
<a>
b = 2
</a>
"""
        options = {
            'mergeduplicateblocks': True,
            'allowmultioptions': True
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
# comment
a = 3
"""
        options = {
            'allowmultioptions': True
        }

        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'a': ['1', '2', '3']})

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

    def testDefaultConfig(self):
        text = """\
a = 1
b = 2
"""
        options = {
            'defaultconfig': {
                'b': '4',
                'c': '3'
            },
            'mergeduplicateoptions': True
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'a': '1', 'b': ['4', '2'], 'c': '3'})

    def testNamedBlocks(self):
        text = """\
<a />
c = 1
</a />

<a b c>
d = 1
</a b c>
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()))

        config = loader.loads(text)

        self.assertEqual(config, {'a': [{'/': {'c': '1'}}, {'b c': {'d': '1'}}]})

    def testQuotedBlockTag(self):
        text = """\
<"a b">
c = 1
</"a b">

<'d e'>
f = 1
</'d e'>

<g 'h i'>
j = 1
</g 'h i'>
    """
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()))

        config = loader.loads(text)

        self.assertEqual(config, {'a b': {'c': '1'}, 'd e': {'f': '1'}, 'g': {'h i': {'j': '1'}}})

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

    def testFlagBits(self):
        text = """\
mode = CLEAR | UNSECURE
"""
        options = {
            'flagbits': {
                'mode': {
                    'CLEAR': 1,
                    'STRONG': 1,
                    'UNSECURE': '32bit'
                }
            }
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'mode': {'CLEAR': 1, 'STRONG': None, 'UNSECURE': '32bit'}})

    def testEscape(self):
        text = """\
a = \\$b
"""
        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()))

        config = loader.loads(text)

        self.assertEqual(config, {'a': '$b'})

    def testNoEscape(self):
        text = """\
a = \\$b
"""
        options = {
            'noescape': True
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'a': '\\$b'})

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

    def testInterpolateVars(self):
        text = """\
a = 1
b = $a
c = ${b}
e 1
<aa>
  d = ${c}
  e = 2
  f "${e} + 2"
  g = '${e}'
</aa>
"""
        options = {
            'interpolatevars': True
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'a': '1',
                                  'b': '1',
                                  'c': '1',
                                  'e': '1',
                                  'aa': {'d': '1',
                                         'e': '2',
                                         'f': '2 + 2',
                                         'g': '${e}'}})

    def testInterpolateVarsSingleQuote(self):
        text = """\
a = 1
b = '${a}'
"""
        options = {
            'allowsinglequoteinterpolation': True
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'a': '1',
                                  'b': '1'})

    def testInterpolateVarsFailOnUndefined(self):
        text = """\
b = ${a}
"""

        options = {
            'interpolatevars': True,
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        self.assertRaises(ApacheConfigError, loader.loads, text)

    def testInterpolateVarsIgnoreUndefined(self):
        text = """\
b = '${a}'
"""
        options = {
            'interpolatevars': True,
            'strictvars': False
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'b': '${a}'})

    def testInterpolateEnv(self):
        text = """\
b = $a
c = ${b}
e 1
<aa>
  d = ${c}
  e = 2
  f "${e} + 2"
  g = '${e}'
</aa>
"""
        options = {
            'interpolateenv': True
        }

        os.environ['a'] = '1'

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'b': '1',
                                  'c': '1',
                                  'e': '1',
                                  'aa': {'d': '1',
                                         'e': '2',
                                         'f': '2 + 2',
                                         'g': '${e}'}})

    def testHookPreOpen(self):

        def pre_open(filename, basedir):
            return 'blah' in filename, filename, basedir

        options = {
            'plug': {
                'pre_open': pre_open
            }
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.load('halb.conf')

        self.assertEqual(config, {})

        self.assertRaises(ApacheConfigError, loader.load, 'blah.conf')

    def testHookPreRead(self):
        text = """\
blah 1
"""
        def pre_read(filepath, text):
            return 'blah' in text, filepath, 'a 1\n'

        options = {
            'plug': {
                'pre_read': pre_read
            }
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'a': '1'})

    def testHookPreParse(self):
        text = """\
a 1
b = 2
"""

        def pre_parse_value(option, value):
            return option == 'a', option, value + '1'

        options = {
            'plug': {
                'pre_parse_value': pre_parse_value
            }
        }

        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        config = loader.loads(text)

        self.assertEqual(config, {'a': '11'})

    def testExpressionParse(self):
        text = """\
# Compare the host name to example.com and redirect to www.example.com if it matches
<If "%{HTTP_HOST} == 'example.com'">
    Redirect permanent "/" "http://www.example.com/"
</If>

# Force text/plain if requesting a file with the query string contains 'forcetext'
<If "%{QUERY_STRING} =~ /forcetext/">
    ForceType text/plain
</If>

# Only allow access to this content during business hours
<Directory "/foo/bar/business">
    Require expr %{TIME_HOUR} -gt 9 && %{TIME_HOUR} -lt 17
</Directory>

# Check a HTTP header for a list of values
<If "%{HTTP:X-example-header} in { 'foo', 'bar', 'baz' }">
    Header set matched true
</If>

# Check an environment variable for a regular expression, negated.
<If "! reqenv('REDIRECT_FOO') =~ /bar/">
    Header set matched true
</If>

# Check result of URI mapping by running in Directory context with -f
<Directory "/var/www">
    AddEncoding x-gzip gz
<If "-f '%{REQUEST_FILENAME}.unzipme' && ! %{HTTP:Accept-Encoding} =~ /gzip/">
      SetOutputFilter INFLATE
</If>
</Directory>

# Check against the client IP
<If "-R '192.168.1.0/24'">
    Header set matched true
</If>

# Function example in boolean context
<If "md5('foo') == 'acbd18db4cc2f85cedef654fccc4a4d8'">
  Header set checksum-matched true
</If>

# Function example in string context
Header set foo-checksum "expr=%{md5:foo}"

# This delays the evaluation of the condition clause compared to <If>
Header always set CustomHeader my-value "expr=%{REQUEST_URI} =~ m#^/special_path\.php$#"
"""

        expect_config = {
            'If': [
                {
                    "%{HTTP_HOST} == 'example.com'": {
                        'Redirect': 'permanent "/" "http://www.example.com/"'
                    }
                },
                {
                    '%{QUERY_STRING} =~ /forcetext/': {
                        'ForceType': 'text/plain'
                    }
                },
                {
                    "%{HTTP:X-example-header} in { 'foo', 'bar', 'baz' }": {
                        'Header': 'set matched true'
                    }
                },
                {
                    "! reqenv('REDIRECT_FOO') =~ /bar/": {
                        'Header': 'set matched true'
                    }
                },
                {
                    "-R '192.168.1.0/24'": {
                        'Header': 'set matched true'
                    }
                }, {
                    "md5('foo') == 'acbd18db4cc2f85cedef654fccc4a4d8'": {
                        'Header': 'set checksum-matched true'
                    }
                }
            ],
            'Directory': [
                {
                    '/foo/bar/business': {
                        'Require': 'expr %{TIME_HOUR} -gt 9 && %{TIME_HOUR} -lt 17'
                    }
                },
                {
                    '/var/www': {
                        'AddEncoding': 'x-gzip gz', 'If': {
                            "-f '%{REQUEST_FILENAME}.unzipme' && ! %{HTTP:Accept-Encoding} =~ /gzip/": {
                                'SetOutputFilter': 'INFLATE'
                            }
                        }
                    }
                }
            ],
            'Header': [
                'set foo-checksum "expr=%{md5:foo}"',
                'always set CustomHeader my-value "expr=%{REQUEST_URI} =~ m'  # TODO(etingof) escape hash
            ]
        }

        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()))

        config = loader.loads(text)

        self.assertEqual(config, expect_config)

    def testMergeEmptyLists(self):
        options = {}
        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        self.assertEqual(loader._merge_lists([],[]), [])

    def testMergeListWithEmptyList(self):
        options = {}
        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        self.assertEqual(loader._merge_lists([1],[]), [1])

    def testMergeListsWithDifferentValues(self):
        options = {}
        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        self.assertEqual(loader._merge_lists([1],[2]), [1, 2])

    def testMergeListsWithSameValues(self):
        options = {}
        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        self.assertEqual(loader._merge_lists([1],[1]), [1])

    def testMergeListsWithSameAndDifferentValues(self):
        options = {}
        ApacheConfigLexer = make_lexer(**options)
        ApacheConfigParser = make_parser(**options)

        loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)

        self.assertEqual(loader._merge_lists([1,2],[3,1]), [1,2,3])

suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
