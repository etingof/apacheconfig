#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import argparse
import sys
import os
import json

from apacheconfig import *
from apacheconfig import __version__


def main():

    parser = argparse.ArgumentParser(description='Dump Apache config files into JSON')

    parser.add_argument(
        '-v', '--version', action='version', version='%(prog)s ' + __version__
    )

    parser.add_argument(
        'file', nargs='+',
        help='Path to the configuration file to dump'
    )

    options = parser.add_argument_group('parsing options')

    options.add_argument(
        '--allowmultioptions', action='store_false',
        help='Collect multiple identical options into a list'
    )

    options.add_argument(
        '--forcearray', action='store_true',
        help=('Force a single config line to get parsed into a list by turning '
              'on this option and by surrounding the value of the config entry by []')
    )

    options.add_argument(
        '--lowercasenames', action='store_true',
        help='All options found in the config will be converted to lowercase'
    )

    options.add_argument(
        '--useapacheinclude', action='store_true',
        help='Consider "include ..." as valid include statement'
    )

    options.add_argument(
        '--includeagain', action='store_true',
        help='Allow including sub-configfiles multiple times'
    )

    options.add_argument(
        '--includerelative', action='store_true',
        help=('Open included config files from within the location of the '
              'configfile instead from within the location of the script')
    )

    options.add_argument(
        '--includedirectories', action='store_true',
        help=('Include statement may point to a directory, in which case '
              'all files inside the directory will be loaded in ASCII order')
    )

    options.add_argument(
        '--includeglob', action='store_true',
        help=('Include statement may point to a glob pattern, in which case '
              'all files matching the pattern will be loaded in ASCII order')
    )

    options.add_argument(
        '--mergeduplicateblocks', action='store_true',
        help=('Duplicate blocks (blocks and named blocks), will be merged '
              'into a single one')
    )

    options.add_argument(
        '--mergeduplicateoptions', action='store_true',
        help=('If the same option occurs more than once, the last one will '
              'be used in the resulting config dictionary')
    )

    options.add_argument(
        '--autotrue', action='store_true',
        help='Turn various forms of binary values in config into "1" and "0"'
    )

    options.add_argument(
        '--interpolatevars', action='store_true',
        help='Enable variable interpolation'
    )

    options.add_argument(
        '--interpolateenv', action='store_true',
        help='Enable process environment variable interpolation'
    )

    options.add_argument(
        '--allowsinglequoteinterpolation', action='store_true',
        help='Perform variable interpolation even when being in single quotes'
    )

    options.add_argument(
        '--strictvars', action='store_false',
        help='Do not fail on an undefined variable when performing interpolation'
    )

    options.add_argument(
        '--ccomments', action='store_false',
        help='Do not parse C-style comments'
    )

    options.add_argument(
        '--configpath', action='append', default=[],
        help='Search path for the configuration files being included. Can repeat.'
    )

    options.add_argument(
        '--flagbits', metavar='<JSON>', type=str,
        help='Named bits for an option in form of a JSON object of the following structure {"OPTION": {"NAME": "VALUE"}}'
    )

    options.add_argument(
        '--defaultconfig', metavar='<JSON>', type=str,
        help='Default values for parsed configuration in form of a JSON object'
    )

    args = parser.parse_args()

    options = dict([(option, getattr(args, option)) for option in dir(args)
                    if not option.startswith('_') and getattr(args, option) is not None])

    options['programpath'] = os.path.dirname(sys.argv[0])

    if 'flagbits' in options:
        try:
            options['flagbits'] = json.loads(options['flagbits'])

        except Exception as ex:
            sys.stderr.write('Malformed flagbits %s: %s\n' % (options['flagbits'], ex))
            return 1

    if 'defaultconfig' in options:
        try:
            options['defaultconfig'] = json.loads(options['defaultconfig'])

        except Exception as ex:
            sys.stderr.write('Malformed defaultconfig %s: %s\n' % (options['defaultconfig'], ex))
            return 1

    for config_file in args.file:

        options['configroot'] = os.path.dirname(config_file)

        with make_loader(**options) as loader:

            try:
                config = loader.load(config_file)

            except ApacheConfigError as ex:
                sys.stderr.write('Failed to parse %s: %s\n' % (config_file, ex))
                return 1

            sys.stdout.write(json.dumps(config, indent=2) + '\n')


if __name__ == '__main__':
    sys.exit(main())