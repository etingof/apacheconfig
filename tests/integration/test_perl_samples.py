#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import sys
import os

from apacheconfig import *

try:
    import unittest2 as unittest

except ImportError:
    import unittest

test_configs = {
    'nested-block-test.conf': {'cops':
                                   {'age': '25',
                                    'appearance':
                                        {'color': '#000000'},
                                    'name': 'stein'}},
    'array-content-test.conf': {'domain':
                                    ['b0fh.org', 'l0pht.com', 'infonexus.com']},
    'unquoted-values-with-whitespaces.conf': {'option': 'value with whitespaces'},
    'multiline-option-test.conf': {'command': "ssh -f -g orpheus.0x49.org           "
                                              "-l azrael -L:34777samir.okir.da.ru:22           "
                                              "-L:31773:shane.sol1.rocket.de:22           "
                                              "'exec sleep 99999990'"},
    'here-document-test.conf': {'header': '  <table border="0">\n  </table>\n'},
}


class PerlConfigGeneralTestCase(unittest.TestCase):
    def testParseFile(self):
        samples_dir = os.path.join(
            os.path.dirname(__file__),
            'samples', 'perl-config-general'
        )

        errors = []

        for filename in os.listdir(samples_dir):
            loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()))

            sample_file = os.path.join(samples_dir, filename)

            with open(sample_file) as f:
                try:
                    config = loader.loads(f.read())

                except ApacheConfigError as ex:
                    errors.append('failed to parse %s: %s' % (sample_file, ex))
                    continue

            if filename in test_configs:
                self.assertEqual(config,  test_configs[filename])

        self.assertEqual(errors, [])


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
