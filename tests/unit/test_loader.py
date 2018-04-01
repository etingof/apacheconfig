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

        ApacheConfigLexer = make_lexer()
        ApacheConfigParser = make_parser()

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



suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
