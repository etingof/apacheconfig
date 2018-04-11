#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import glob
import logging
import re
import os

from apacheconfig.error import ApacheConfigError

log = logging.getLogger(__name__)


class ApacheConfigLoader(object):

    def __init__(self, parser, debug=False, **options):
        self._parser = parser
        self._debug = debug
        self._options = dict(options)
        self._stack = []
        self._includes = set()

    # Code generation rules

    def g_config(self, ast):
        config = {}

        for subtree in ast:
            items = self._walkast(subtree)
            if items:
                config.update(items)

        return config

    def g_block(self, ast):
        tag = ast[0]
        values = {}

        if re.match(r'.*?[ \t\r\n]+', tag):
            tag, name = re.split(r'[ \t\r\n]+', tag, maxsplit=1)

            block = {
                tag: {
                    name: values
                }
            }

        else:
            block = {
                tag: values
            }

        for subtree in ast[1:-1]:
            items = self._walkast(subtree)
            if items:
                values.update(items)

        return block

    def g_contents(self, ast):
        # TODO(etingof): remove defaulted and overriden options from productions
        contents = self._options.get('defaultconfig', {})

        for subtree in ast:
            items = self._walkast(subtree)
            self._merge_contents(contents, items)

        return contents

    def g_statements(self, ast):
        statements = {}

        for subtree in ast:
            items = self._walkast(subtree)
            for item in items:
                if item in statements:
                    if (self._options.get('allowmultioptions', True) and
                            not self._options.get('mergeduplicateoptions', False)):
                        if not isinstance(statements[item], list):
                            statements[item] = [statements[item]]
                        statements[item].append(items[item])
                    elif self._options.get('mergeduplicateoptions', False):
                        statements[item] = items[item]
                    else:
                        raise ApacheConfigError('Duplicate option "%s" prohibited' % item)
                else:
                    statements[item] = items[item]

        if (self._options.get('interpolateenv', False) or
                self._options.get('allowsinglequoteinterpolation', False)):
            self._options['interpolatevars'] = True

        if self._options.get('interpolatevars', False):

            def lookup(match):
                option = match.groups()[0]

                if option in statements:
                    return interpolate(statements[option])

                for frame in self._stack:
                    if option in frame:
                        return interpolate(frame[option])

                if self._options.get('interpolateenv', False):
                    if option in os.environ:
                        return interpolate(os.environ[option])

                if self._options.get('strictvars', True):
                    raise ApacheConfigError('Undefined variable "${%s}" referenced' % option)

                return interpolate(match.string)

            def interpolate(value):
                expanded = re.sub(r'(?<!\\)\${([^\n\r]+?)}', lookup, value)
                if expanded != value:
                    return expanded
                return re.sub(r'(?<!\\)\$([^\n\r $]+?)', lookup, value)

            for option, value in tuple(statements.items()):
                if (not getattr(value, 'is_single_quoted', False) or
                        self._options.get('allowsinglequoteinterpolation', False)):
                    if isinstance(value, list):
                        statements[option] = [interpolate(x) for x in value]
                    else:
                        statements[option] = interpolate(value)

        self._stack.insert(0, statements)

        return statements

    def g_statement(self, ast):
        option, value = ast[:2]

        flagbits = self._options.get('flagbits')
        if flagbits and option in flagbits:
            flags = dict([(key, None) for key in flagbits[option]])
            for flag in value.split('|'):
                flag = flag.strip()
                flags[flag] = flagbits[option][flag]
            value = flags

        elif self._options.get('autotrue'):
            if value.lower() in ('yes', 'on', 'true'):
                value = '1'
            elif value.lower() in ('no', 'off', 'false'):
                value = '0'

        if self._options.get('forcearray'):
            if value.startswith('[') and value.endswith(']'):
                value = [value[1:-1]]

        return {
            option: value
        }

    def g_comment(self, ast):
        return []

    def g_include(self, ast):
        filepath = ast[0]

        options = self._options

        if os.path.isabs(filepath):
            configpath = [os.path.dirname(filepath)]
            filename = os.path.basename(filepath)

        else:
            configpath = options.get('configpath', [])

            if 'configroot' in options and options.get('includerelative'):
                configpath.insert(0, options['configroot'])

            if 'programpath' in options:
                configpath.append(options['programpath'])
            else:
                configpath.append('.')

            if os.path.isdir(filepath):
                configpath.insert(0, filepath)
                filename = '.'
            else:
                filename = filepath

        for configdir in configpath:

            filepath = os.path.join(configdir, filename)

            if os.path.isdir(filepath):
                if options.get('includedirectories'):
                    contents = {}

                    for include_file in sorted(os.listdir(filepath)):
                        items = self.load(os.path.join(filepath, include_file), initialize=False)
                        self._merge_contents(contents, items)

                    return contents

            elif options.get('includeglob'):
                contents = {}

                for include_file in sorted(glob.glob(filepath)):
                    items = self.load(include_file, initialize=False)
                    self._merge_contents(contents, items)

                return contents

            elif os.path.exists(filepath):
                return self.load(filepath, initialize=False)

        else:
            raise ApacheConfigError('Config file "%s" not found in search path %s' % (filename, ':'.join(configpath)))

    def _merge_contents(self, contents, items):
        for item in items:
            if item in contents:
                # TODO(etingof): keep block/statements merging at one place
                if self._options.get('mergeduplicateblocks'):
                    for subitem in contents[item]:
                        if subitem in items[item]:
                            if not isinstance(contents[item][subitem], list):
                                contents[item][subitem] = [contents[item][subitem]]
                            contents[item][subitem].append(items[item][subitem])
                else:
                    if not isinstance(contents[item], list):
                        contents[item] = [contents[item]]
                    contents[item].append(items[item])
            else:
                contents[item] = items[item]

        return contents

    def _walkast(self, ast):
        if not ast:
            return

        node_type = ast[0]

        try:
            handler = getattr(self, 'g_' + node_type)

        except AttributeError:
            raise ApacheConfigError('Unsupported AST node type %s' % node_type)

        return handler(ast[1:])

    def loads(self, text, initialize=True, source=None):
        if initialize:
            self._stack = []

        try:
            pre_read = self._options['plug']['pre_read']

            process, source, text = pre_read(source, text)

            if not process:
                return {}

        except KeyError:
            pass

        ast = self._parser.parse(text)

        return self._walkast(ast)

    def load(self, filepath, initialize=True):
        if initialize:
            self._stack = []
            self._includes = set()

        try:
            pre_open = self._options['plug']['pre_open']

            filename, basedir = os.path.basename(filepath), os.path.dirname(filepath)

            process, filename, basedir = pre_open(filename, basedir)

            filepath = os.path.join(basedir, filename)

            if not process:
                return {}

        except KeyError:
            pass

        if filepath in self._includes and not self._options.get('includeagain'):
            return {}

        self._includes.add(filepath)

        try:
            with open(filepath) as f:
                return self.loads(f.read(), source=filepath)

        except IOError as ex:
            raise ApacheConfigError('File %s can\'t be open: %s' % (filepath, ex))

