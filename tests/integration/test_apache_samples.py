#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import sys
import os

from apacheconfig import *

try:
    import unittest2 as unittest

except ImportError:
    import unittest

class PerlConfigGeneralTestCase(unittest.TestCase):

    def setUp(self):
        options = {'preservewhitespace': True}
        ApacheConfigLexer = make_lexer(**options)
        self.lexer = ApacheConfigLexer()
        ApacheConfigParser = make_parser(**options)
        self.parser = ApacheConfigParser(self.lexer, start='contents')

    def _test_files(self, directory, perform_test, expected_errors=0):
        errors = []
        for filename in os.listdir(directory):
            text = ""
            filepath = os.path.join(directory, filename)
            if os.path.isdir(filepath):
                continue
            with open(filepath) as f:
                text = f.read()
            perform_test(text)
        self.assertEqual(len(errors), expected_errors)

    def testLexFiles(self):
        samples_dir = os.path.join(
            os.path.dirname(__file__),
            'samples', 'apache-conf-files',
        )
        self._test_files(samples_dir, self.lexer.tokenize)

    def testParseFiles(self):
        samples_dir = os.path.join(
            os.path.dirname(__file__),
            'samples', 'apache-conf-files',
        )
        self._test_files(samples_dir, self.parser.parse)

    def _parse_and_write(self, text):
        node = parse_contents(text)
        self.assertEquals(str(node), text)

    def testParseAndWriteFiles(self):
        samples_dir = os.path.join(
            os.path.dirname(__file__),
            'samples', 'apache-conf-files',
        )
        self._test_files(samples_dir, self._parse_and_write)

suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
