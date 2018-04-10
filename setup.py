#!/usr/bin/env python
#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import os
import sys

classifiers = """\
Development Status :: 4 - Beta
Environment :: Console
Intended Audience :: Developers
Intended Audience :: Education
Intended Audience :: Information Technology
Intended Audience :: System Administrators
Intended Audience :: Telecommunications Industry
License :: OSI Approved :: BSD License
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.1
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Topic :: Communications
Topic :: Software Development :: Libraries :: Python Modules
"""


def howto_install_setuptools():
    print("""
   Error: You need setuptools Python package!

   It's very easy to install it, just type:

   wget https://bootstrap.pypa.io/ez_setup.py
   python ez_setup.py

   Then you could make eggs from this package.
""")


if sys.version_info[:2] < (2, 6):
    print("ERROR: this package requires Python 2.6 or later!")
    sys.exit(1)

try:
    from setuptools import setup, Command

    params = {
        'zip_safe': True
    }

except ImportError:
    for arg in sys.argv:
        if 'egg' in arg:
            howto_install_setuptools()
            sys.exit(1)
    from distutils.core import setup, Command

    params = {}

params.update(
    {
        'name': 'apacheconfig',
        'version': open(os.path.join('apacheconfig', '__init__.py')).read().split('\'')[1],
        'description': 'Apache config file parser',
        'long_description': 'Apache and Perl Config::General style configuration file parsing library',
        'maintainer': 'Ilya Etingof <etingof@gmail.com>',
        'author': 'Ilya Etingof',
        'author_email': 'etingof@gmail.com',
        'url': 'https://github.com/etingof/apacheconfig',
        'platforms': ['any'],
        'classifiers': [x for x in classifiers.split('\n') if x],
        'license': 'BSD',
        'packages': ['apacheconfig'],
        'entry_points': {
            'console_scripts': [
                'apacheconfigtool = apacheconfig.apacheconfigtool:main'
            ]
        }
    }
)

# handle unittest discovery feature
try:
    import unittest2 as unittest
except ImportError:
    import unittest


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        suite = unittest.TestLoader().loadTestsFromNames(
            ['tests.__main__.suite']
        )

        unittest.TextTestRunner(verbosity=2).run(suite)

params['cmdclass'] = {
    'test': PyTest,
    'tests': PyTest,
}

setup(**params)
