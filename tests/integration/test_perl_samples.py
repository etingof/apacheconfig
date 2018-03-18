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
    'nested-block-test.conf': {'cops': {'color': '#000000',
                                        'age': '25',
                                        'name': 'stein'}},
    'array-content-test.conf': {'domain':
                                    ['b0fh.org', 'l0pht.com', 'infonexus.com']},
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
