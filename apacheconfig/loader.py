#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
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
        contents = {}

        for subtree in ast:
            items = self._walkast(subtree)
            for item in items:
                if item in contents:
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

        return statements

    def g_statement(self, ast):
        option, value = ast[:2]

        if self._options.get('autotrue', False):
            if value.lower() in ('yes', 'on', 'true'):
                value = '1'
            elif value.lower() in ('no', 'off', 'false'):
                value = '0'

        return {
            option: value
        }

    def g_comment(self, ast):
        return []

    def g_include(self, ast):
        return self.load(ast[0])

    def _walkast(self, ast):
        if not ast:
            return

        node_type = ast[0]

        try:
            handler = getattr(self, 'g_' + node_type)

        except AttributeError:
            raise ApacheConfigError('Unsupported AST node type %s' % node_type)

        return handler(ast[1:])

    def loads(self, text):
        ast = self._parser.parse(text)

        return self._walkast(ast)

    def load(self, filepath):
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

            filename = os.path.basename(filepath)

        for configdir in configpath:

            filepath = os.path.join(configdir, filename)

            if not os.path.exists(filepath):
                continue

            with open(filepath) as f:
                ast = self._parser.parse(f.read())

            return self._walkast(ast)

        else:
            raise ApacheConfigError('Config file "%s" not found in search path %s' % (filename, ':'.join(configpath)))
