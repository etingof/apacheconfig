# -*- coding: utf-8 -*-
#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
from __future__ import unicode_literals

import os
import sys

from apacheconfig import ApacheConfigError
from apacheconfig import make_loader

try:
    import unittest2 as unittest

except ImportError:
    import unittest


TEST_CONFIGS = {
    "nested-block-test.conf": {
        "cops": {
            "age": "25",
            "appearance": {
                "color": "#000000"
            },
            "name": "stein"
        }
    },
    "array-content-test.conf": {
        "domain": [
            "b0fh.org",
            "l0pht.com",
            "infonexus.com"
        ]
    },
    "unquoted-values-with-whitespaces.conf": {
        "option": "value with whitespaces"
    },
    "multiline-option-test.conf": {
        "command": "ssh -f -g orpheus.0x49.org -l azrael -L:34777samir.okir.da"
                   ".ru:22 -L:31773:shane.sol1.rocket.de:22 'exec sleep "
                   "99999990'"
    },
    "here-document-test.conf": {
        "header": "  <table border=\"0\">\n  </table>"
    },
    "c-style-comment-test.conf": {
        "passwd": "sakkra",
        "foo": {
            "bar": "baz"
        },
        "db": {
            "host": "blah.blubber"
        },
        "user": "tom"
    },
    "combination-of-constructs.conf": {
        "cops": {
            "officer": [
                {
                    "randall": {
                        "name": "stein",
                        "age": "25"
                    }
                },
                {
                    "gordon": {
                        "name": "bird",
                        "age": "31"
                    }
                }
            ]
        },
        "domain": [
            "nix.to",
            "b0fh.org",
            "foo.bar",
        ],
        "域名": "unicode.example.com",
        "message": "  yes. we are not here. you\n  can reach us somewhere in\n"
                   "  outerspace.",
        "nocomment": "Comments in a here-doc should not be treated as "
                     "comments.\n/* So this should appear in the output */",
        "command": "ssh -f -g orpheus.0x49.org -l azrael -L:34777samir.okir."
                   "da.ru:22 -L:31773:shane.sol1.rocket.de:22 'exec sleep "
                   "99999990'",
        "user": "tom",
        "passwd": "sakkra",
        "db": {
            "host": "blah.blubber"
        },
        "beta": [
            {
                "user1": "hans"
            },
            {
                "user2": "max"
            }
        ],
        "quoted": "this one contains whitespace at the end    ",
        "quotedwithquotes": " holy crap, it contains \"masked quotes\" and "
                            "'single quotes'  "
    },
    "include-file-test.conf": {
        "seen_first_config": "true",
        "seen_second_config": "true",
        "inner": {
            "final_include": "true",
            "seen_third_config": "true"
        }
    },
    "second-test.conf": {
        "seen_second_config": "true",
        "inner": {
            "final_include": "true",
            "seen_third_config": "true"
        }
    },
    "third-test.conf": {
        "final_include": "true",
        "seen_third_config": "true"
    }
}


class PerlConfigGeneralTestCase(unittest.TestCase):
    def testParseFiles(self):
        samples_dir = os.path.join(
            os.path.dirname(__file__),
            'samples', 'perl-config-general'
        )

        errors = []

        with make_loader() as loader:

            for filename in os.listdir(samples_dir):

                filepath = os.path.join(samples_dir, filename)

                if os.path.isdir(filepath):
                    continue

                try:
                    config = loader.load(filepath)

                except ApacheConfigError as ex:
                    errors.append('failed to parse %s: %s' % (filepath, ex))
                    continue

                if filename in TEST_CONFIGS:
                    self.assertEqual(config, TEST_CONFIGS[filename])

        self.assertEqual(len(errors), 2)

    def testIncludeDirectories(self):
        samples_file = os.path.join(
            os.path.dirname(__file__),
            'samples', 'perl-config-general', 'include-directory-test.conf'
        )

        options = {
            'includedirectories': True
        }

        with make_loader(**options) as loader:
            config = loader.load(samples_file)

        self.assertTrue(config)

    def testIncludeGlob(self):
        samples_file = os.path.join(
            os.path.dirname(__file__),
            'samples', 'perl-config-general', 'include-glob-test.conf'
        )

        options = {
            'includeglob': True
        }

        with make_loader(**options) as loader:
            config = loader.load(samples_file)

        self.assertTrue(config)

    def testIncludeOptional(self):
        samples_file = os.path.join(
            os.path.dirname(__file__),
            'samples', 'perl-config-general', 'include-optional-test.conf'
        )

        with make_loader() as loader:
            config = loader.load(samples_file)

        self.assertFalse(config)

    def testIncludeAgainDisabled(self):
        samples_file = os.path.join(
            os.path.dirname(__file__),
            'samples', 'perl-config-general', 'include-again-test.conf'
        )

        options = {
            'includeagain': False
        }

        with make_loader(**options) as loader:
            config = loader.load(samples_file)

        self.assertEqual(config, {'seen_second_config': 'true',
                                  'inner': {'final_include': 'true',
                                            'seen_third_config': 'true'}})

    def testIncludeAgainEnabled(self):
        samples_file = os.path.join(
            os.path.dirname(__file__),
            'samples', 'perl-config-general', 'include-again-test.conf'
        )

        options = {
            'includeagain': True
        }

        with make_loader(**options) as loader:
            config = loader.load(samples_file)

        self.assertEqual(
            config, {
                'seen_second_config': ['true', 'true'],
                'inner': [
                    {'final_include': 'true', 'seen_third_config': 'true'},
                    {'final_include': 'true', 'seen_third_config': 'true'}
                ]
            }
        )


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
